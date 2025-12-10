# -*- coding: utf-8 -*-
import json
import logging
import datetime
from uuid import uuid4

from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages

from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings  # <-- NUEVO

from .prompt_utils import call_ia_json  # usamos JSON directo para robustez
from accidentes.models import Accidentes, Relato, ArbolCausas, Prescripciones
from accidentes.utils.mixins import AccidenteScopedByCodigoMixin

logger = logging.getLogger(__name__)

# ----------------- Helpers de LOG (una sola línea + truncado) -----------------
def _pretty(obj, max_len: int = 3500) -> str:
    """Representación de una sola línea y acotada para evitar intercalado con otros logs."""
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

def _log_request(prompt_key: str, codigo: str, payload) -> str:
    prompt_id = uuid4().hex
    logger.info(
        "[IA][request] prompt_id=%s prompt_key=%s codigo=%s payload=%s",
        prompt_id, prompt_key, codigo, _pretty(payload)
    )
    return prompt_id

def _log_response(prompt_id: str, prompt_key: str, codigo: str, response):
    logger.info(
        "[IA][response] prompt_id=%s prompt_key=%s codigo=%s response=%s",
        prompt_id, prompt_key, codigo, _pretty(response)
    )

def _log_error(prompt_id: str, prompt_key: str, codigo: str, err: Exception):
    logger.exception(
        "[IA][error] prompt_id=%s prompt_key=%s codigo=%s error=%s",
        prompt_id, prompt_key, codigo, str(err)
    )


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class MedidasCorrectivasView(LoginRequiredMixin, AccidenteScopedByCodigoMixin, View):
    template_name = "accidentes/medidas_correctivas.html"
    partial_name = "accidentes/partials/medidas/_medidas_wrapper.html"
    login_url = "/accounts/login/"

    # ================== DEBUG helper (igual a hechos.py) ==================
    def _debug_print(self, label: str, lines: list[str]):
        if not settings.DEBUG:
            return
        enumerated = [f"{i}. {h}" for i, h in enumerate(lines, start=1)]
        print(f">>> [DEBUG] {label}")
        for line in enumerated:
            print("    ", line)
        print("")

    # ----------------- Helpers -----------------
    def _compute_ctx(self, request, codigo: str):
        """
        Resuelve el accidente con alcance (via mixin) y arma el contexto para render.
        """
        accidente = self.accidente_from(codigo)  # 🔐 alcance unificado
        medidas = Prescripciones.objects.filter(accidente=accidente).order_by("prioridad")

        edit_mode = request.GET.get("edit_mode") == "1"
        edit_index = request.GET.get("edit_index")
        try:
            edit_index = int(edit_index) if edit_mode else None
        except (ValueError, TypeError):
            edit_index = None

        ctx = {
            "medidas": medidas,
            "codigo": codigo,
            "edit_mode": edit_mode,
            "edit_index": edit_index,
        }
        return accidente, ctx

    def _render(self, request, codigo: str):
        """
        Renderiza partial si es HTMX; página completa si no.
        """
        _, ctx = self._compute_ctx(request, codigo)
        if request.headers.get("HX-Request"):
            return render(request, self.partial_name, ctx)
        return render(request, self.template_name, ctx)

    def _current_path(self, request):
        return request.path

    # ----------------- GET -----------------
    @method_decorator(require_GET)
    def get(self, request, codigo: str):
        return self._render(request, codigo)

    # ----------------- POST -----------------
    @method_decorator(require_POST)
    def post(self, request, codigo: str):
        """
        Todas las operaciones usan accidente resuelto por helper con alcance (mixin).
        """
        accidente = self.accidente_from(codigo)  # 🔐
        is_htmx = bool(request.headers.get("HX-Request"))

        # ---- Entrar a modo edición de una medida (por índice visual) ----
        if "edit" in request.POST:
            idx = request.POST.get("edit")
            if is_htmx:
                request.GET = request.GET.copy()
                request.GET["edit_mode"] = "1"
                request.GET["edit_index"] = idx
                return self._render(request, codigo)
            url = f"{self._current_path(request)}?edit_mode=1&edit_index={idx}"
            return redirect(url)

        # ---- Guardar cambios de una medida por índice ----
        if "save" in request.POST:
            try:
                idx = int(request.POST.get("save"))
                medidas_qs = Prescripciones.objects.filter(accidente=accidente).order_by("prioridad")
                medidas = list(medidas_qs)
                if idx < 0 or idx >= len(medidas):
                    raise IndexError("Índice fuera de rango")

                medida = medidas[idx]
                # Campos básicos
                medida.tipo = request.POST.get(f"medidas-{idx}-tipo", medida.tipo)
                medida.prioridad = request.POST.get(f"medidas-{idx}-prioridad", medida.prioridad)
                medida.descripcion = (request.POST.get(f"medidas-{idx}-descripcion", medida.descripcion) or "").strip()
                medida.responsable = (request.POST.get(f"medidas-{idx}-responsable", medida.responsable) or "").strip().title()

                # Fecha con fallback seguro
                fecha_str = (request.POST.get(f"medidas-{idx}-fecha") or "").strip()
                if fecha_str:
                    try:
                        medida.plazo = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
                    except ValueError:
                        medida.plazo = medida.plazo or datetime.date.today()
                else:
                    medida.plazo = medida.plazo or datetime.date.today()

                medida.save()
                messages.success(request, "Medida actualizada correctamente.")
            except Exception as e:
                logger.exception("Error al guardar la medida")
                messages.error(request, f"Error al guardar la medida: {e}")

            return self._render(request, codigo) if is_htmx else redirect("accidentes:ia_medidas", codigo=codigo)

        # ---- Eliminar una medida por índice ----
        if "delete" in request.POST:
            try:
                idx = int(request.POST.get("delete"))
                medidas_qs = Prescripciones.objects.filter(accidente=accidente).order_by("prioridad")
                medidas = list(medidas_qs)
                if 0 <= idx < len(medidas):
                    medidas[idx].delete()
                    messages.success(request, "Medida eliminada.")
                else:
                    messages.error(request, "Índice inválido para eliminar.")
            except Exception as e:
                logger.exception("Error al eliminar la medida")
                messages.error(request, f"Error al eliminar la medida: {e}")

            return self._render(request, codigo) if is_htmx else redirect("accidentes:ia_medidas", codigo=codigo)

        # ---- Regenerar todas las medidas (IA) ----
        if "regenerate" in request.POST:
            prompt_key = "medidas"
            prompt_id = None

            def _extract_json_block(text: str):
                if not isinstance(text, str):
                    return None
                if "```" in text:
                    try:
                        return text.split("```json", 1)[1].split("```", 1)[0].strip()
                    except Exception:
                        pass
                try:
                    start = text.find("{")
                    end = text.rfind("}")
                    if start != -1 and end != -1 and end > start:
                        return text[start:end+1]
                except Exception:
                    pass
                return None

            try:
                # === 1) Armar payload explícito: relato, hechos, arbol ===
                relato_obj = Relato.objects.filter(accidente=accidente, is_current=True).first()
                relatof = (relato_obj.relato_final or "").strip() if relato_obj else ""

                hechos_payload: list[str] = []
                try:
                    from accidentes.models import Hechos  # opcional
                    hqs = Hechos.objects.filter(accidente=accidente).order_by("secuencia", "pk")
                    hechos_payload = [
                        (h.descripcion or "").strip()
                        for h in hqs
                        if (h.descripcion or "").strip()
                    ]
                except Exception:
                    hechos_payload = []

                arbol_obj = ArbolCausas.objects.filter(accidente=accidente, is_current=True).first()
                arbol_raw = (arbol_obj.arbol_json_5q or "").strip() if arbol_obj else ""
                arbol_payload = None
                if arbol_raw:
                    try:
                        arbol_payload = json.loads(arbol_raw)
                    except Exception:
                        arbol_payload = arbol_raw  # string

                payload = {
                    "relato": relatof,
                    "hechos": hechos_payload,
                    "arbol_de_causa": arbol_payload or ""
                }

                self._debug_print("MEDIDAS payload.relato", [relatof] if relatof else ["<vacío>"])
                self._debug_print("MEDIDAS payload.hechos", hechos_payload or ["<vacío>"])
                self._debug_print(
                    "MEDIDAS payload.arbol_de_causa",
                    [json.dumps(arbol_payload, ensure_ascii=False)] if isinstance(arbol_payload, (dict, list)) else
                    [arbol_payload] if arbol_payload else ["<vacío>"]
                )

                if not (relatof or hechos_payload or arbol_payload):
                    messages.warning(request, "No hay datos suficientes (relato final / hechos / árbol 5Q) para generar medidas.")
                else:
                    prompt_id = _log_request(prompt_key, codigo, payload)
                    data = call_ia_json(json.dumps(payload, ensure_ascii=False), prompt_key=prompt_key)

                    if isinstance(data, str):
                        block = _extract_json_block(data) or data
                        try:
                            data = json.loads(block)
                        except Exception:
                            data = {}

                    _log_response(prompt_id, prompt_key, codigo, data)

                    data = data or {}
                    medidas = data.get("medidas", []) if isinstance(data, dict) else []

                    Prescripciones.objects.filter(accidente=accidente).delete()

                    for m in medidas:
                        tipo = (m.get("tipo") or "Administrativa").strip()
                        prioridad = (m.get("prioridad") or "Media").strip()
                        descripcion = (m.get("descripcion") or "").strip()
                        responsable = (m.get("responsable") or "").strip().title()
                        fecha_str = (m.get("fecha") or "").strip()

                        try:
                            plazo = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else datetime.date.today()
                        except ValueError:
                            plazo = datetime.date.today()

                        Prescripciones.objects.create(
                            accidente=accidente,
                            tipo=tipo,
                            prioridad=prioridad,
                            descripcion=descripcion,
                            responsable=responsable,
                            plazo=plazo,
                        )

                    messages.success(request, "Medidas regeneradas correctamente.")
            except Exception as e:
                try:
                    _log_error(prompt_id or "-", prompt_key, codigo, e)
                except Exception:
                    pass
                logger.exception("Error al generar medidas")
                messages.error(request, f"Error generando medidas: {e}")

            return self._render(request, codigo) if is_htmx else redirect("accidentes:ia_medidas", codigo=codigo)

        # ---- Guardar todo (informativo) ----
        if "save_all" in request.POST:
            messages.success(request, "Todos los cambios ya están guardados.")
            return self._render(request, codigo) if is_htmx else redirect("accidentes:ia_medidas", codigo=codigo)

        # ---- Agregar medida manual (desde modal HTMX) ----
        if "add_manual" in request.POST:
            try:
                tipo = (request.POST.get("tipo") or "Administrativa").strip()
                prioridad = (request.POST.get("prioridad") or "Media").strip()
                descripcion = (request.POST.get("descripcion") or "").strip()
                responsable = (request.POST.get("responsable") or "").strip().title()
                fecha_str = (request.POST.get("fecha") or "").strip()

                try:
                    plazo = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else datetime.date.today()
                except ValueError:
                    plazo = datetime.date.today()

                Prescripciones.objects.create(
                    accidente=accidente,
                    tipo=tipo,
                    prioridad=prioridad,
                    descripcion=descripcion,
                    responsable=responsable,
                    plazo=plazo,
                )
                messages.success(request, "Medida agregada correctamente.")
            except Exception as e:
                logger.exception("Error al agregar medida manual")
                messages.error(request, f"Error al agregar la medida: {e}")

            return self._render(request, codigo) if is_htmx else redirect("accidentes:ia_medidas", codigo=codigo)

        # ---- (Compat) Agregar medida vacía rápida (si usas un botón sin modal) ----
        if "add_new" in request.POST:
            try:
                Prescripciones.objects.create(
                    accidente=accidente,
                    tipo="Administrativa",
                    prioridad="Media",
                    descripcion="",
                    responsable="",
                    plazo=datetime.date.today(),
                )
                messages.success(request, "Nueva medida agregada.")
            except Exception as e:
                logger.exception("Error al agregar nueva medida")
                messages.error(request, f"Error al agregar nueva medida: {e}")

            return self._render(request, codigo) if is_htmx else redirect("accidentes:ia_medidas", codigo=codigo)

        # ---- Fallback ----
        return self._render(request, codigo) if is_htmx else redirect("accidentes:ia_medidas", codigo=codigo)
