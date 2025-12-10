# accidentes/views_api/generar_informe.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import datetime
import logging
import json  # NEW
from pathlib import Path
from typing import Optional, List

from django.conf import settings
from django.views import View
from django.shortcuts import render
from django.http import FileResponse, Http404, HttpResponseRedirect, HttpResponse  # + HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.utils.timezone import now
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string  # NEW

from accidentes.models import Accidentes, Informes
from accidentes.utils.crear_informe_doc import InformeDocxBuilder
from accidentes.utils.mixins import AccidenteScopedByCodigoMixin

log = logging.getLogger(__name__)


class GenerarInformeIAView(LoginRequiredMixin, AccidenteScopedByCodigoMixin, View):
    """
    Seguridad / alcance:
      - El accidente se resuelve con self.accidente_from(codigo), que usa get_accidente_scoped_or_404
        (404 si no existe o está fuera de alcance) y sincroniza session['accidente_id'].
      - TODAS las operaciones de lectura/escritura filtran por accidente=...
      - No se revela existencia de recursos fuera de alcance (404 coherente).
    """
    template_name = "accidentes/generar_informe.html"

    # ----------------- helpers -----------------
    def _parse_fecha(self, value: str) -> datetime.date:
        if not value:
            return datetime.date.today()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.datetime.strptime(value, fmt).date()
            except Exception:
                pass
        return datetime.date.today()

    def _get_resumen_from_relato(self, accidente_id: int) -> str:
        """
        Busca un campo de texto 'resumen/relato' en los posibles modelos de relato.
        Es tolerante a la ausencia de modelos/campos.
        """
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
            return FileResponse(f, as_attachment=True, filename=download_name or Path(path).name)
        except FileNotFoundError:
            raise Http404("Archivo no encontrado.")
        except Exception as e:
            log.exception("No fue posible servir el archivo: %s", e)
            try:
                f.close()
            except Exception:
                pass
            raise Http404("No fue posible entregar el archivo.")

    @staticmethod
    def _report_path(codigo_accidente: str, codigo_informe: str, version: int) -> Optional[Path]:
        """
        Busca el archivo físico del informe para (codigo_informe, version),
        priorizando DOCX y luego TXT, dentro de PROTECTED_MEDIA_ROOT.
        """
        base = Path(settings.PROTECTED_MEDIA_ROOT) / "informes" / str(codigo_accidente)
        for ext in ("docx", "txt"):
            p = base / f"{codigo_informe}_v{version}.{ext}"
            if p.exists():
                return p
        return None

    @staticmethod
    def _delete_report_files(codigo_accidente: str, codigo_informe: str, version: int) -> bool:
        base = Path(settings.PROTECTED_MEDIA_ROOT) / "informes" / str(codigo_accidente)
        ok = False
        for ext in ("docx", "txt"):
            p = base / f"{codigo_informe}_v{version}.{ext}"
            if p.exists():
                try:
                    p.unlink()
                    ok = True
                except Exception:
                    pass
        return ok

    @staticmethod
    def _order_fields(model) -> List[str]:
        """
        Orden estable para el listado en pantalla:
        - NO incluir '-is_current' para que al restaurar no se mueva de lugar.
        - Usar '-version' y luego '-created_at' si existe, o '-pk' de fallback.
        """
        fields = model._meta
        order: List[str] = []
        try:
            fields.get_field("version")
            order.append("-version")
        except FieldDoesNotExist:
            pass
        try:
            fields.get_field("created_at")
            order.append("-created_at")
        except FieldDoesNotExist:
            pass
        if not order:
            order = ["-pk"]
        return order

    # ----------------- GET -----------------
    def get(self, request, codigo: str):
        # DESCARGA POR GET (usado por el flujo HTMX)
        if request.GET.get("download") == "1":
            codigo_informe = (request.GET.get("codigo_informe") or "").strip()
            try:
                version = int(request.GET.get("version") or "0")
            except ValueError:
                version = 0

            if not codigo_informe or version <= 0:
                raise Http404("Parámetros de descarga inválidos.")

            p = self._report_path(codigo, codigo_informe, version)
            if not p:
                raise Http404("Archivo no encontrado.")

            return self._safe_file_response(p.as_posix(), download_name=p.name)

        acc: Accidentes = self.accidente_from(codigo)

        # Listado estable: no dependemos de is_current para no “mover” filas al restaurar
        order = self._order_fields(Informes)
        informes_qs = Informes.objects.filter(accidente=acc).order_by(*order)

        # La versión actual sólo para el botón de descarga
        if any(f.name == "is_current" for f in Informes._meta.fields):
            current = Informes.objects.filter(accidente=acc, is_current=True).first()
        else:
            current = informes_qs.first()

        ctx = {
            "codigo": codigo,
            "default_codigo_informe": f"INF-{now().year}-{acc.accidente_id:03d}",
            "default_investigador": (getattr(request.user, "get_full_name", lambda: "")() or
                                     getattr(request.user, "username", "")),
            "default_fecha": datetime.date.today(),
            "informes": list(informes_qs),
            "current_informe": current,  # usado por el template para “Descargar versión actual”
        }
        return render(request, self.template_name, ctx)

    # ----------------- POST -----------------
    @transaction.atomic
    def post(self, request, codigo: str):
        acc: Accidentes = self.accidente_from(codigo)
        action = (request.POST.get("action") or "generate").strip().lower()

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

            if any(f.name == "is_current" for f in Informes._meta.fields):
                Informes.objects.filter(accidente=acc, is_current=True).update(is_current=False)

            inf = Informes.objects.create(
                version=next_version,
                **({"is_current": True} if any(f.name == "is_current" for f in Informes._meta.fields) else {}),
                codigo=codigo_informe,
                fecha_informe=fecha_informe,
                investigador=investigador,
                accidente=acc,
            )

            resumen = self._get_resumen_from_relato(acc.accidente_id)
            out_path = InformeDocxBuilder().build(accidente=acc, informe=inf, resumen_texto=resumen)

            messages.success(request, f"Informe generado: {inf.codigo} v{inf.version}")

            # Si se marcó "descargar al generar", devolvemos el archivo directo (no HTMX en este form)
            if descargar_flag:
                return self._safe_file_response(out_path, download_name=Path(out_path).name)

            return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))

        # --------- DOWNLOAD ---------
        if action == "download":
            codigo_informe = (request.POST.get("codigo_informe") or "").strip()
            try:
                version = int(request.POST.get("version") or "0")
            except ValueError:
                version = 0

            # Si no se envían parámetros: descargar la versión actual (o primera del orden)
            if not codigo_informe or version <= 0:
                order = self._order_fields(Informes)
                if any(f.name == "is_current" for f in Informes._meta.fields):
                    current = Informes.objects.filter(accidente=acc, is_current=True).first()
                else:
                    current = Informes.objects.filter(accidente=acc).order_by(*order).first()
                if not current:
                    messages.error(request, "No hay un informe disponible para descargar.")
                    return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))
                codigo_informe = current.codigo
                version = current.version

            p = self._report_path(codigo, codigo_informe, version)
            if not p:
                messages.error(request, f"No existe archivo para {codigo_informe} v{version}.")
                return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))

            # Si NO es HTMX: entrega el archivo como siempre
            hx_req = request.headers.get("HX-Request")
            is_htmx = (isinstance(hx_req, str) and hx_req.lower() == "true")
            if not is_htmx:
                return self._safe_file_response(p.as_posix(), download_name=p.name)

            # HTMX: mostrar toast + disparar descarga por GET
            messages.success(request, f"Descarga iniciada: {codigo_informe} v{version}")
            notif_html = render_to_string("accidentes/notification.html", request=request)

            download_url = (
                reverse("accidentes:generar_informe", args=[codigo])
                + f"?download=1&codigo_informe={codigo_informe}&version={version}"
            )

            resp = HttpResponse(notif_html)
            # 🔑 usa After-Settle (más fiable cuando hx-swap="none")
            payload = json.dumps({"file-download": {"url": download_url}})
            resp["HX-Trigger-After-Settle"] = payload
            # (Opcional) duplica en HX-Trigger por compat:
            resp["HX-Trigger"] = payload
            return resp

        # --------- RESTORE (marcar versión como actual; no crea nueva) ---------
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

            if any(f.name == "is_current" for f in Informes._meta.fields):
                Informes.objects.filter(accidente=acc, is_current=True).update(is_current=False)
                target.is_current = True
                target.save(update_fields=["is_current"])

            messages.success(
                request,
                f"Restaurado: {target.codigo} v{target.version} es ahora la versión actual para descargar."
            )
            return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))

        # --------- DELETE ---------
        if action == "delete":
            try:
                informe_id = int(request.POST.get("informe_id") or "0")
            except ValueError:
                informe_id = 0

            inf = Informes.objects.filter(accidente=acc, pk=informe_id).first()
            if not inf:
                messages.error(request, "Informe no encontrado.")
                return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))

            self._delete_report_files(codigo, inf.codigo, inf.version)

            was_current = getattr(inf, "is_current", False)
            inf.delete()

            if was_current and any(f.name == "is_current" for f in Informes._meta.fields):
                # Promover la de mayor versión como actual, pero sin reordenar por is_current
                order = self._order_fields(Informes)
                next_current = Informes.objects.filter(accidente=acc).order_by(*order).first()
                if next_current:
                    next_current.is_current = True
                    next_current.save(update_fields=["is_current"])

            messages.success(request, "Versión eliminada.")
            return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))

        messages.error(request, "Acción no reconocida.")
        return HttpResponseRedirect(reverse("accidentes:generar_informe", args=[codigo]))
