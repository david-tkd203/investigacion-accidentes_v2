# accidentes/views_api/hechos.py
# -*- coding: utf-8 -*-
import re
from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.shortcuts import render
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from .prompt_utils import call_ia_text
from accidentes.models import Hechos, Relato, Accidentes
from accidentes.utils.mixins import AnchorRedirectMixin, AccidenteScopedByCodigoMixin


class HechosIAView(LoginRequiredMixin, AccidenteScopedByCodigoMixin, AnchorRedirectMixin, View):
    template_name = "accidentes/hechos.html"
    partial_name  = "accidentes/partials/hechos/_hechos_wrapper.html"
    anchor_id = "hechos-section"

    # ---------- Helpers ----------
    def get_hechos_from_db(self, accidente: Accidentes):
        """
        Devuelve una lista de descripciones (ordenadas por secuencia) para renderizar.
        """
        return list(
            Hechos.objects.filter(accidente=accidente)
            .order_by("secuencia", "pk")
            .values_list("descripcion", flat=True)
        )

    def _compute_ctx(self, request, codigo: str):
        """
        Resuelve el accidente con el scope unificado (404 si no existe o no está en alcance),
        y arma el contexto para GET/HTMX.
        """
        accidente = self.accidente_from(codigo)  # ⬅️ mixin con get_accidente_scoped_or_404 + sesión
        relato_q = Relato.objects.filter(accidente=accidente, is_current=True)
        relato_confirmado = relato_q.filter(relato_final__isnull=False).exists()
        relato_final = relato_q.first().relato_final if relato_confirmado else ""

        ctx = {
            "relatof": relato_final,
            "form_hechos_guardado": relato_confirmado,
            "hechos_generados": self.get_hechos_from_db(accidente),
            "codigo": codigo,
            "anchor": self.anchor_id,
        }
        return accidente, ctx

    def _render(self, request, codigo: str):
        _, ctx = self._compute_ctx(request, codigo)
        # Si viene de HTMX, devolvemos SOLO el partial para #hechos-wrapper
        if request.headers.get("HX-Request"):
            return render(request, self.partial_name, ctx)
        # Navegación normal -> página completa
        return render(request, self.template_name, ctx)

    def _debug_print(self, label: str, hechos: list[str]):
        if not settings.DEBUG:
            return
        enumerated = [f"{i}. {h}" for i, h in enumerate(hechos, start=1)]
        print(f">>> [DEBUG] {label}")
        for line in enumerated:
            print("    ", line)
        print("")

    # ---------- Handlers ----------
    def get(self, request, codigo: str):
        return self._render(request, codigo)

    @transaction.atomic
    def post(self, request, codigo: str):
        action = (request.POST.get("action") or "").strip()
        accidente = self.accidente_from(codigo)  # ⬅️ 404 si no está en alcance
        hechos_descripciones = self.get_hechos_from_db(accidente)

        # ---- IA: identificar hechos desde relato confirmado ----
        if action == "identify_hechos":
            relato = Relato.objects.filter(
                accidente=accidente,
                is_current=True,
                relato_final__isnull=False
            ).first()

            if not relato:
                messages.warning(request, "Primero confirma el relato.")
            else:
                try:
                    raw = call_ia_text(relato.relato_final, prompt_key="hechos")
                    facts = [
                        re.sub(r'^\s*\d+\.\s*', '', line).strip()
                        for line in raw.splitlines() if line.strip()
                    ]
                    Hechos.objects.filter(accidente=accidente).delete()
                    for i, desc in enumerate(facts, start=1):
                        Hechos.objects.create(accidente=accidente, secuencia=i, descripcion=desc)
                    self._debug_print("hechos_generados tras identify_hechos", facts)
                    messages.success(request, "Hechos identificados con IA.")
                except Exception as e:
                    messages.error(request, f"Error identificando hechos: {e}")

        # ---- Añadir un hecho vacío al final ----
        elif action == "add_fact":
            next_seq = (Hechos.objects.filter(accidente=accidente)
                        .aggregate(Max("secuencia"))["secuencia__max"] or 0) + 1
            Hechos.objects.create(accidente=accidente, secuencia=next_seq, descripcion="")
            messages.success(request, "Nuevo hecho añadido.")

        # ---- Modificar el texto de un hecho por índice (orden actual) ----
        elif action == "modify_fact":
            try:
                idx = int(request.POST.get("idx", -1))
                text = (request.POST.get("fact_text") or "").strip()
                hechos_qs = Hechos.objects.filter(accidente=accidente).order_by("secuencia", "pk")
                if 0 <= idx < hechos_qs.count():
                    hecho = hechos_qs[idx]
                    hecho.descripcion = text
                    hecho.save(update_fields=["descripcion"])
                    messages.success(request, "Hecho actualizado.")
                else:
                    messages.error(request, "Índice de hecho inválido.")
            except Exception as e:
                messages.error(request, f"Error actualizando hecho: {e}")

        # ---- Eliminar por índice y renumerar secuencias ----
        elif action == "delete_fact":
            try:
                idx = int(request.POST.get("idx", -1))
                hechos_qs = list(Hechos.objects.filter(accidente=accidente).order_by("secuencia", "pk"))
                if 0 <= idx < len(hechos_qs):
                    hechos_qs[idx].delete()
                    # Reordenar secuencias compactas
                    for i, hecho in enumerate(
                        Hechos.objects.filter(accidente=accidente).order_by("secuencia", "pk"),
                        start=1
                    ):
                        if hecho.secuencia != i:
                            hecho.secuencia = i
                            hecho.save(update_fields=["secuencia"])
                    messages.success(request, "Hecho eliminado.")
                else:
                    messages.error(request, "Índice de hecho inválido.")
            except Exception as e:
                messages.error(request, f"Error eliminando hecho: {e}")

        # ---- Mover arriba/abajo por índice, con swap de secuencia ----
        elif action in {"move_up", "move_down"}:
            try:
                idx = int(request.POST.get("idx", -1))
                hechos_qs = list(Hechos.objects.filter(accidente=accidente).order_by("secuencia", "pk"))

                if action == "move_up" and 1 <= idx < len(hechos_qs):
                    a, b = hechos_qs[idx - 1], hechos_qs[idx]
                    a.secuencia, b.secuencia = b.secuencia, a.secuencia
                    a.save(update_fields=["secuencia"])
                    b.save(update_fields=["secuencia"])
                    messages.success(request, "Hecho movido hacia arriba.")
                elif action == "move_down" and 0 <= idx < len(hechos_qs) - 1:
                    a, b = hechos_qs[idx], hechos_qs[idx + 1]
                    a.secuencia, b.secuencia = b.secuencia, a.secuencia
                    a.save(update_fields=["secuencia"])
                    b.save(update_fields=["secuencia"])
                    messages.success(request, "Hecho movido hacia abajo.")
                else:
                    messages.error(request, "No se puede mover en esa dirección.")
            except Exception as e:
                messages.error(request, f"Error moviendo hecho: {e}")

        # ---- Guardado global (las acciones ya persisten) ----
        elif action == "guardar_bd":
            messages.success(request, "Todos los cambios ya están guardados.")

        else:
            messages.error(request, "Acción no reconocida.")

        # Responder según sea HTMX o navegación normal
        if request.headers.get("HX-Request"):
            return self._render(request, codigo)

        return self._build_redirect(
            request, "accidentes:ia_hechos", args=[codigo], anchor=self.anchor_id
        )
# accidentes/views_api/hechos.py
# -*- coding: utf-8 -*-
import re
import json
import logging
from uuid import uuid4

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.shortcuts import render
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from .prompt_utils import call_ia_text
from accidentes.models import Hechos, Relato, Accidentes
from accidentes.utils.mixins import AnchorRedirectMixin, AccidenteScopedByCodigoMixin

logger = logging.getLogger(__name__)


class HechosIAView(LoginRequiredMixin, AccidenteScopedByCodigoMixin, AnchorRedirectMixin, View):
    template_name = "accidentes/hechos.html"
    partial_name  = "accidentes/partials/hechos/_hechos_wrapper.html"
    anchor_id = "hechos-section"

    # ---------- Helpers de LOG (una sola línea + truncado) ----------
    def _pretty(self, obj, max_len: int = 3500) -> str:
        """
        Representación de una sola línea y acotada para evitar intercalado con otros logs.
        """
        try:
            if isinstance(obj, (dict, list)):
                s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
            else:
                s = str(obj)
        except Exception:
            return "<no-repr>"
        s = " ".join(s.split())
        if len(s) > max_len:
            s = s[:max_len] + "…[truncated]"
        return s

    def _log_request(self, prompt_key: str, codigo: str, payload) -> str:
        prompt_id = uuid4().hex
        logger.info(
            "[IA][request] prompt_id=%s prompt_key=%s codigo=%s payload=%s",
            prompt_id, prompt_key, codigo, self._pretty(payload)
        )
        return prompt_id

    def _log_response(self, prompt_id: str, prompt_key: str, codigo: str, response):
        logger.info(
            "[IA][response] prompt_id=%s prompt_key=%s codigo=%s response=%s",
            prompt_id, prompt_key, codigo, self._pretty(response)
        )

    def _log_error(self, prompt_id: str, prompt_key: str, codigo: str, err: Exception):
        logger.exception(
            "[IA][error] prompt_id=%s prompt_key=%s codigo=%s error=%s",
            prompt_id, prompt_key, codigo, str(err)
        )

    # ---------- Helpers ----------
    def get_hechos_from_db(self, accidente: Accidentes):
        """
        Devuelve una lista de descripciones (ordenadas por secuencia) para renderizar.
        """
        return list(
            Hechos.objects.filter(accidente=accidente)
            .order_by("secuencia", "pk")
            .values_list("descripcion", flat=True)
        )

    def _compute_ctx(self, request, codigo: str):
        """
        Resuelve el accidente con el scope unificado (404 si no existe o no está en alcance),
        y arma el contexto para GET/HTMX.
        """
        accidente = self.accidente_from(codigo)  # ⬅️ mixin con get_accidente_scoped_or_404 + sesión
        relato_q = Relato.objects.filter(accidente=accidente, is_current=True)
        relato_confirmado = relato_q.filter(relato_final__isnull=False).exists()
        relato_final = relato_q.first().relato_final if relato_confirmado else ""

        ctx = {
            "relatof": relato_final,
            "form_hechos_guardado": relato_confirmado,
            "hechos_generados": self.get_hechos_from_db(accidente),
            "codigo": codigo,
            "anchor": self.anchor_id,
        }
        return accidente, ctx

    def _render(self, request, codigo: str):
        _, ctx = self._compute_ctx(request, codigo)
        # Si viene de HTMX, devolvemos SOLO el partial para #hechos-wrapper
        if request.headers.get("HX-Request"):
            return render(request, self.partial_name, ctx)
        # Navegación normal -> página completa
        return render(request, self.template_name, ctx)

    def _debug_print(self, label: str, hechos: list[str]):
        if not settings.DEBUG:
            return
        enumerated = [f"{i}. {h}" for i, h in enumerate(hechos, start=1)]
        print(f">>> [DEBUG] {label}")
        for line in enumerated:
            print("    ", line)
        print("")

    # ---------- Handlers ----------
    def get(self, request, codigo: str):
        return self._render(request, codigo)

    @transaction.atomic
    def post(self, request, codigo: str):
        action = (request.POST.get("action") or "").strip()
        accidente = self.accidente_from(codigo)  # ⬅️ 404 si no está en alcance
        hechos_descripciones = self.get_hechos_from_db(accidente)

        # ---- IA: identificar hechos desde relato confirmado ----
        if action == "identify_hechos":
            relato = Relato.objects.filter(
                accidente=accidente,
                is_current=True,
                relato_final__isnull=False
            ).first()

            if not relato:
                messages.warning(request, "Primero confirma el relato.")
            else:
                try:
                    prompt_key = "hechos"
                    payload = relato.relato_final
                    prompt_id = self._log_request(prompt_key, codigo, payload)

                    raw = call_ia_text(payload, prompt_key=prompt_key)

                    self._log_response(prompt_id, prompt_key, codigo, raw)

                    facts = [
                        re.sub(r'^\s*\d+\.\s*', '', line).strip()
                        for line in raw.splitlines() if line.strip()
                    ]
                    Hechos.objects.filter(accidente=accidente).delete()
                    for i, desc in enumerate(facts, start=1):
                        Hechos.objects.create(accidente=accidente, secuencia=i, descripcion=desc)
                    self._debug_print("hechos_generados tras identify_hechos", facts)
                    messages.success(request, "Hechos identificados con IA.")
                except Exception as e:
                    try:
                        self._log_error(prompt_id, prompt_key, codigo, e)  # type: ignore[name-defined]
                    except Exception:
                        pass
                    messages.error(request, f"Error identificando hechos: {e}")

        # ---- Añadir un hecho vacío al final ----
        elif action == "add_fact":
            next_seq = (Hechos.objects.filter(accidente=accidente)
                        .aggregate(Max("secuencia"))["secuencia__max"] or 0) + 1
            Hechos.objects.create(accidente=accidente, secuencia=next_seq, descripcion="")
            messages.success(request, "Nuevo hecho añadido.")

        # ---- Modificar el texto de un hecho por índice (orden actual) ----
        elif action == "modify_fact":
            try:
                idx = int(request.POST.get("idx", -1))
                text = (request.POST.get("fact_text") or "").strip()
                hechos_qs = Hechos.objects.filter(accidente=accidente).order_by("secuencia", "pk")
                if 0 <= idx < hechos_qs.count():
                    hecho = hechos_qs[idx]
                    hecho.descripcion = text
                    hecho.save(update_fields=["descripcion"])
                    messages.success(request, "Hecho actualizado.")
                else:
                    messages.error(request, "Índice de hecho inválido.")
            except Exception as e:
                messages.error(request, f"Error actualizando hecho: {e}")

        # ---- Eliminar por índice y renumerar secuencias ----
        elif action == "delete_fact":
            try:
                idx = int(request.POST.get("idx", -1))
                hechos_qs = list(Hechos.objects.filter(accidente=accidente).order_by("secuencia", "pk"))
                if 0 <= idx < len(hechos_qs):
                    hechos_qs[idx].delete()
                    # Reordenar secuencias compactas
                    for i, hecho in enumerate(
                        Hechos.objects.filter(accidente=accidente).order_by("secuencia", "pk"),
                        start=1
                    ):
                        if hecho.secuencia != i:
                            hecho.secuencia = i
                            hecho.save(update_fields=["secuencia"])
                    messages.success(request, "Hecho eliminado.")
                else:
                    messages.error(request, "Índice de hecho inválido.")
            except Exception as e:
                messages.error(request, f"Error eliminando hecho: {e}")

        # ---- Mover arriba/abajo por índice, con swap de secuencia ----
        elif action in {"move_up", "move_down"}:
            try:
                idx = int(request.POST.get("idx", -1))
                hechos_qs = list(Hechos.objects.filter(accidente=accidente).order_by("secuencia", "pk"))

                if action == "move_up" and 1 <= idx < len(hechos_qs):
                    a, b = hechos_qs[idx - 1], hechos_qs[idx]
                    a.secuencia, b.secuencia = b.secuencia, a.secuencia
                    a.save(update_fields=["secuencia"])
                    b.save(update_fields=["secuencia"])
                    messages.success(request, "Hecho movido hacia arriba.")
                elif action == "move_down" and 0 <= idx < len(hechos_qs) - 1:
                    a, b = hechos_qs[idx], hechos_qs[idx + 1]
                    a.secuencia, b.secuencia = b.secuencia, a.secuencia
                    a.save(update_fields=["secuencia"])
                    b.save(update_fields=["secuencia"])
                    messages.success(request, "Hecho movido hacia abajo.")
                else:
                    messages.error(request, "No se puede mover en esa dirección.")
            except Exception as e:
                messages.error(request, f"Error moviendo hecho: {e}")

        # ---- Guardado global (las acciones ya persisten) ----
        elif action == "guardar_bd":
            messages.success(request, "Todos los cambios ya están guardados.")

        else:
            messages.error(request, "Acción no reconocida.")

        # Responder según sea HTMX o navegación normal
        if request.headers.get("HX-Request"):
            return self._render(request, codigo)

        return self._build_redirect(
            request, "accidentes:ia_hechos", args=[codigo], anchor=self.anchor_id
        )
