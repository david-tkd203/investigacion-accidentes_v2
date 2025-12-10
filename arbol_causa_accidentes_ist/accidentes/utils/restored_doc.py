# accidentes/views_api/generar_informe.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import datetime
import logging
from typing import Optional

from django.views import View
from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.utils.timezone import now
from django.apps import apps

from accidentes.models import Accidentes, Informes
from accidentes.utils.crear_informe_doc import InformeDocxBuilder
from accidentes.utils.restored_doc import ReportRestore

log = logging.getLogger(__name__)


class GenerarInformeIAView(View):
    """
    GET  -> muestra 'generar_informe.html'
    POST -> generate | download | restore | delete
    """
    template_name = "accidentes/generar_informe.html"

    # ----------------- helpers -----------------
    def get_accidente(self, codigo: str) -> Accidentes:
        return get_object_or_404(Accidentes, codigo_accidente=codigo)

    def _parse_fecha(self, value: str) -> datetime.date:
        if not value:
            return datetime.date.today()
        try:
            return datetime.date.fromisoformat(value)
        except Exception:
            try:
                return datetime.datetime.strptime(value, "%d/%m/%Y").date()
            except Exception:
                return datetime.date.today()

    def _get_resumen_from_relato(self, accidente_id: int) -> str:
        candidatos = (
            ("accidentes", "AccidentesRelato"),
            ("accidentes", "Relato"),
            ("accidentes", "Relatos"),
        )
        for app_label, model_name in candidatos:
            try:
                Model = apps.get_model(app_label, model_name)
            except LookupError:
                continue
            try:
                rel = (Model.objects
                       .filter(accidente_id=accidente_id)
                       .order_by("-pk")
                       .first())
                if not rel:
                    continue
                for field in ("relato_final", "contenido", "texto", "resumen"):
                    if hasattr(rel, field) and getattr(rel, field):
                        return str(getattr(rel, field))[:4000]
            except Exception:
                continue
        return ""

    @staticmethod
    def _safe_file_response(path: str, download_name: Optional[str] = None) -> FileResponse:
        try:
            f = open(path, "rb")
            return FileResponse(f, as_attachment=True, filename=download_name)
        except FileNotFoundError:
            raise Http404("Archivo no encontrado.")
        except Exception as e:
            log.exception("No fue posible servir el archivo: %s", e)
            try:
                f.close()
            except Exception:
                pass
            raise Http404("No fue posible entregar el archivo.")

    # ----------------- GET -----------------
    def get(self, request, codigo: str):
        acc = self.get_accidente(codigo)

        # IMPORTANTE: ordenar poniendo primero el "actual" (is_current=True),
        # luego por versión desc y fecha de creación desc.
        informes_qs = (Informes.objects
                       .filter(accidente=acc)
                       .order_by("-is_current", "-version", "-created_at"))

        current = (Informes.objects
                   .filter(accidente=acc, is_current=True)
                   .order_by("-version")
                   .first())

        ctx = {
            "codigo": codigo,
            "default_codigo_informe": f"INF-{now().year}-{acc.accidente_id:03d}",
            "default_investigador": request.user.get_full_name() or request.user.username,
            "default_fecha": datetime.date.today(),
            "informes": list(informes_qs),   # <- el primero será SIEMPRE el "actual" (restaurado)
            "current_informe": current,       # por si luego quieres usarlo directo en el template
        }
        return render(request, self.template_name, ctx)

    # ----------------- POST -----------------
    @transaction.atomic
    def post(self, request, codigo: str):
        acc = self.get_accidente(codigo)
        action = (request.POST.get("action") or "generate").strip()

        # --------- GENERATE ---------
        if action == "generate":
            codigo_informe = (request.POST.get("codigo_informe") or "").strip()
            investigador   = (request.POST.get("investigador") or "").strip()
            fecha_raw      = request.POST.get("fecha_informe") or ""
            descargar_flag = (request.POST.get("descargar") == "1")

            if not codigo_informe or not investigador or not fecha_raw:
                messages.error(request, "Completa Informe N°, Investigador y Fecha.")
                return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))

            fecha_informe = self._parse_fecha(fecha_raw)

            last = Informes.objects.filter(accidente=acc).order_by("-version").first()
            next_version = (last.version + 1) if last else 1

            Informes.objects.filter(accidente=acc, is_current=True).update(is_current=False)

            inf = Informes.objects.create(
                version=next_version,
                is_current=True,
                codigo=codigo_informe,
                fecha_informe=fecha_informe,
                investigador=investigador,
                accidente=acc,
            )

            resumen = self._get_resumen_from_relato(acc.accidente_id)
            out_path = InformeDocxBuilder().build(accidente=acc, informe=inf, resumen_texto=resumen)

            messages.success(request, f"Informe generado: {inf.codigo} v{inf.version}")

            if descargar_flag:
                return self._safe_file_response(out_path, download_name=out_path.split("/")[-1])

            return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))

        # --------- DOWNLOAD ---------
        if action == "download":
            codigo_informe = (request.POST.get("codigo_informe") or "").strip()
            try:
                version = int(request.POST.get("version") or "0")
            except ValueError:
                version = 0

            # Si no viene nada, descarga el ACTUAL
            if not codigo_informe or version <= 0:
                current = (Informes.objects
                           .filter(accidente=acc, is_current=True)
                           .first())
                if not current:
                    messages.error(request, "No hay un informe actual para descargar.")
                    return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))
                codigo_informe = current.codigo
                version = current.version

            p = ReportRestore.best_path(
                codigo_accidente=codigo,
                codigo_informe=codigo_informe,
                version=version,
                prefer=("docx", "txt"),
            )
            if not p:
                messages.error(request, f"No existe archivo para {codigo_informe} v{version}.")
                return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))

            return self._safe_file_response(p.as_posix(), download_name=p.name)

        # --------- RESTORE (NO crea nueva versión) ---------
        if action == "restore":
            codigo_informe = (request.POST.get("codigo_informe") or "").strip()
            try:
                from_version = int(request.POST.get("from_version") or "0")
            except ValueError:
                from_version = 0

            if not codigo_informe or from_version <= 0:
                messages.error(request, "Parámetros de restauración inválidos.")
                return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))

            target = (Informes.objects
                      .filter(accidente=acc, codigo=codigo_informe, version=from_version)
                      .first())
            if not target:
                messages.error(request, f"No se encontró {codigo_informe} v{from_version}.")
                return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))

            # Marcar SOLO esa versión como actual (sin crear copia)
            Informes.objects.filter(accidente=acc, is_current=True).update(is_current=False)
            target.is_current = True
            target.save(update_fields=["is_current"])

            messages.success(
                request,
                f"Restaurado: {target.codigo} v{target.version} ahora es la versión actual para descargar."
            )
            # Al redirigir, el GET pondrá esta versión PRIMERA en 'informes',
            # por lo que tu template con |first la mostrará en el botón de descarga.
            return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))

        # --------- DELETE ---------
        if action == "delete":
            try:
                informe_id = int(request.POST.get("informe_id") or "0")
            except ValueError:
                informe_id = 0

            inf = (Informes.objects
                   .filter(accidente=acc, pk=informe_id)
                   .first())
            if not inf:
                messages.error(request, "Informe no encontrado.")
                return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))

            # Borrar archivos físicos
            ReportRestore.delete_version(
                codigo_accidente=codigo,
                codigo_informe=inf.codigo,
                version=inf.version,
            )
            was_current = inf.is_current
            inf.delete()

            if was_current:
                next_current = (Informes.objects
                                .filter(accidente=acc)
                                .order_by("-version", "-created_at")
                                .first())
                if next_current:
                    next_current.is_current = True
                    next_current.save(update_fields=["is_current"])

            messages.success(request, "Versión eliminada.")
            return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))

        messages.error(request, "Acción no reconocida.")
        return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))
