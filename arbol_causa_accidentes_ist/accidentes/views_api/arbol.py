# accidentes/views_api/arbol.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
from uuid import uuid4

from django.views import View
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseBadRequest
from django.db.models import Max
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from graphviz import Source, ExecutableNotFound

from accidentes.models import Accidentes, ArbolCausas, Hechos, Relato
from accidentes.utils.causal_tree import CausalTree
from accidentes.access import get_accidente_scoped_or_404  # helper central (404 si fuera de alcance)
from accidentes.utils.mixins import AccidenteScopedByCodigoMixin  # resuelve self.accidente (+sesión)
from .prompt_utils import call_ia_json

logger = logging.getLogger(__name__)


# ----------------- Helpers de LOG (una sola línea + truncado) -----------------
def _pretty(obj, max_len: int = 3500) -> str:
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


class ArbolIAView(LoginRequiredMixin, AccidenteScopedByCodigoMixin, View):
    """
    GET normal (sin HTMX) -> devuelve arbol.html (wrapper con #arbol-container).
    GET HTMX (hx-get)     -> devuelve el partial (SVG o botón Generar).
    POST (HTMX)           -> acciones de navegación/edición; devuelve partial.

    Seguridad:
      - Acceso a 'accidente' mediante self.accidente_from(codigo) -> get_accidente_scoped_or_404
      - Todas las consultas subsecuentes filtran por accidente=<self.accidente>
    """
    template_name = "accidentes/arbol.html"
    partial_template = "accidentes/partials/arbol/_arbol_partial.html"

    # ----------------- helpers -----------------
    def get_arbol_model(self, accidente: Accidentes):
        return ArbolCausas.objects.filter(accidente=accidente, is_current=True).first()

    def puede_generar_arbol(self, accidente: Accidentes) -> bool:
        return (
            Relato.objects.filter(
                accidente=accidente, is_current=True, relato_final__isnull=False
            ).exists()
            and Hechos.objects.filter(accidente=accidente).exists()
        )

    def _dot_neutro_para_bd(self, tree: CausalTree, base_path: str | None) -> str:
        """
        Genera un DOT sin resaltar el nodo actual (sin 'puntero'),
        usando el truco de poner current=None temporalmente.
        """
        _cur = tree.current
        try:
            tree.current = None
            return tree.generate_dot(base_path=base_path)
        finally:
            tree.current = _cur

    # ----------------- GET -----------------
    def get(self, request, codigo: str):
        """
        - Si es petición normal -> renderiza arbol.html (la página).
        - Si es HTMX -> renderiza el partial con SVG / botón.
        """
        is_htmx = (request.headers.get("HX-Request") == "true")

        # Validamos y sincronizamos sesión SIEMPRE, incluso en wrapper,
        # para homogeneizar comportamiento y evitar estados colgantes.
        accidente = self.accidente_from(codigo)  # <- 404 si no existe o fuera de alcance

        if not is_htmx:
            return render(request, self.template_name, {"codigo": codigo})

        action = request.GET.get("action")
        node_id = request.GET.get("node_id")

        arbol_model = self.get_arbol_model(accidente)
        if not arbol_model:
            return self.render_arbol(request, codigo, accidente, tree=None, partial=True)

        # Hay árbol: construir y eventualmente navegar
        try:
            tree = CausalTree(arbol_model.arbol_json_5q)
        except (ValueError, json.JSONDecodeError):
            # JSON roto -> mostrar botón generar
            return self.render_arbol(request, codigo, accidente, tree=None, partial=True)

        if action == "navigate_to" and node_id:
            # Mover puntero en memoria
            tree.set_current(node_id)

            # Guardar JSON (labels) normalmente
            arbol_model.arbol_json_5q = tree.export_to_5q_json()

            # Guardar DOT NEUTRO en BD (sin puntero)
            base = reverse('accidentes:ia_arbol', args=[codigo])
            arbol_model.arbol_json_dot = self._dot_neutro_para_bd(tree, base_path=base)
            arbol_model.save()

            return self.render_arbol(request, codigo, accidente, tree, partial=True)

        return self.render_arbol(request, codigo, accidente, tree, partial=True)

    # ----------------- POST -----------------
    def post(self, request, codigo: str):
        """
        Acciones de navegación/edición desde el formulario del partial.
        Devuelve siempre el partial actualizado.
        """
        accidente = self.accidente_from(codigo)  # <- 404 si no existe o fuera de alcance
        action = (request.POST.get("action") or "").strip()
        node_id = (request.POST.get("node_id") or "").strip()
        new_label = (request.POST.get("new_label") or "").strip()

        arbol_model = self.get_arbol_model(accidente)
        if not arbol_model:
            # No hay árbol aún -> mostrar botón generar
            return self.render_arbol(request, codigo, accidente, tree=None, partial=True)

        try:
            tree = CausalTree(arbol_model.arbol_json_5q)
        except (ValueError, json.JSONDecodeError):
            return self.render_arbol(request, codigo, accidente, tree=None, partial=True)

        if node_id:
            tree.set_current(node_id)

        if action == "navigate_to" and node_id:
            tree.set_current(node_id)
        elif action == "navigate_parent":
            tree.navigate_to_parent()
        elif action == "navigate_first":
            tree.navigate_to_first_child()
        elif action == "navigate_root":
            tree.navigate_to_root()
        elif action == "navigate_prev":
            tree.navigate_previous_cousin()
        elif action == "navigate_next":
            moved = tree.navigate_next_cousin()
            if moved:
                messages.success(request, "Nodo siguiente seleccionado.")
            else:
                messages.warning(request, "No hay más nodos a la derecha.")
        elif action == "edit_node":
            if tree.update_current_label(new_label):
                messages.success(request, "Etiqueta actualizada.")
            else:
                messages.warning(request, "Texto inválido.")
        elif action == "add_child":
            if new_label:
                attach_to = (request.POST.get("attach_to") or "").strip()
                if attach_to:
                    # Inserta entre el padre (nodo actual) y la rama existente seleccionada
                    ok = getattr(tree, "insert_between_parent_and_child", None)
                    if callable(ok):
                        ok = tree.insert_between_parent_and_child(tree.current, attach_to, new_label)
                    else:
                        ok = False
                    if ok:
                        messages.success(request, "Nodo insertado entre el padre y la rama seleccionada.")
                    else:
                        messages.warning(request, "No fue posible insertar: la rama seleccionada no es hija directa.")
                else:
                    # Comportamiento por defecto: crear hijo directo nuevo
                    tree.add_child_node(new_label)
                    messages.success(request, "Hijo añadido.")
            else:
                messages.warning(request, "Etiqueta vacía.")
        elif action == "add_sibling":
            if new_label:
                success = tree.add_sibling_node(new_label)
                if success:
                    messages.success(request, "Hermano añadido.")
                else:
                    messages.warning(request, "No se puede añadir un hermano al nodo raíz.")
            else:
                messages.warning(request, "Etiqueta vacía.")
        elif action in {"delete_node", "delete_current"}:
            tree.delete_current_node()
            messages.success(request, "Nodo eliminado correctamente.")
        else:
            messages.error(request, "Acción no reconocida.")
            return self.render_arbol(request, codigo, accidente, tree, partial=True)

        # Guardar cambios en BD:
        # - JSON 5Q normal (sin estado visual)
        # - DOT NEUTRO (sin puntero)
        arbol_model.arbol_json_5q = tree.export_to_5q_json()
        base = reverse('accidentes:ia_arbol', args=[codigo])
        arbol_model.arbol_json_dot = self._dot_neutro_para_bd(tree, base_path=base)
        arbol_model.save()

        return self.render_arbol(request, codigo, accidente, tree, partial=True)

    # ----------------- renderizador común -----------------
    def render_arbol(self, request, codigo: str, accidente: Accidentes, tree: CausalTree | None, partial: bool):
        """
        Si 'partial' es True (o HTMX), renderiza el fragmento.
        Si no, renderiza la página completa.
        """
        arbol_model = self.get_arbol_model(accidente)

        # --- requisitos para generar ---
        tiene_hechos = Hechos.objects.filter(accidente=accidente).exists()
        tiene_relato = Relato.objects.filter(
            accidente=accidente, is_current=True, relato_final__isnull=False
        ).exists()
        puede_generar = (tiene_hechos and tiene_relato)

        base_path = reverse("accidentes:ia_arbol", args=[codigo])

        # ---- NO HAY ÁRBOL ----
        if not arbol_model or not tree:
            context = {
                "codigo": codigo,
                "svg": None,
                "modo_edicion": False,
                "show_boton_generar_inicial": True,
                "show_boton_regenerar": False,
                "puede_generar": puede_generar,
                "faltan_hechos": not tiene_hechos,
                "faltan_relato": not tiene_relato,
                "child_targets": [],
            }
            tpl = self.partial_template if partial or (request.headers.get("HX-Request") == "true") else self.template_name
            return render(request, tpl, context)

        # ---- SÍ hay árbol ----
        try:
            dot_source = tree.generate_dot(base_path=base_path)  # con current resaltado SOLO UI
            svg = Source(dot_source).pipe(format="svg").decode("utf-8")
            svg = svg.replace('<?xml version="1.0" encoding="UTF-8" standalone="no"?>', "")
        except ExecutableNotFound:
            svg = None
            dot_source = tree.generate_dot(base_path=base_path)

        # Construir opciones de ramas hijas del nodo actual (para insertar "entre medio")
        child_targets: list[dict[str, str]] = []
        if tree and tree.current and tree.current in tree.nodes:
            for cid in (tree.nodes[tree.current].get("children") or []):
                if cid in tree.nodes:
                    child_targets.append({"id": cid, "label": tree.nodes[cid].get("label", "")})

        context = {
            "svg": svg,
            "current_id": tree.current,
            "dot_source": dot_source,
            "breadcrumbs": tree.get_breadcrumbs(),
            "current_label": tree.get_current_label(),
            "codigo": codigo,
            "puede_generar": puede_generar,
            "show_boton_generar_inicial": False,
            "show_boton_regenerar": puede_generar,
            "modo_edicion": True,
            "child_targets": child_targets,  # <- ahora sí definido antes
        }

        tpl = self.partial_template if partial or (request.headers.get("HX-Request") == "true") else self.template_name
        return render(request, tpl, context)


class GenerarArbolIACreateView(LoginRequiredMixin, AccidenteScopedByCodigoMixin, View):
    """
    Recibe el POST del botón “Generar árbol…”.
    Devuelve SIEMPRE el partial (para swap dentro de #arbol-container).

    Seguridad: accidente via self.accidente_from(codigo)
    """
    template_name = "accidentes/partials/arbol/_arbol_partial.html"

    def post(self, request, codigo: str):
        accidente = self.accidente_from(codigo)  # <- 404 si no existe o fuera de alcance

        hechos_qs = Hechos.objects.filter(accidente=accidente).order_by("secuencia", "hecho_id")
        relato_obj = Relato.objects.filter(
            accidente=accidente, is_current=True, relato_final__isnull=False
        ).first()

        if not hechos_qs.exists() or not relato_obj:
            return HttpResponseBadRequest("Faltan hechos o relato válido para generar el árbol")

        # Entrada para el prompt "arbol_causas"
        entrada = {
            "relato": (relato_obj.relato_final or "").strip(),
            "hechos": [
                (h.descripcion or "").strip()
                for h in hechos_qs
                if (h.descripcion or "").strip()
            ],
        }

        try:
            prompt_key = "arbol_causas"
            prompt_id = _log_request(prompt_key, codigo, entrada)

            # IA devuelve un JSON 5Q con claves del tipo "0.0.0.0.0.0.0.0.0"
            arbol_dict = call_ia_json(json.dumps(entrada, ensure_ascii=False), prompt_key=prompt_key)

            _log_response(prompt_id, prompt_key, codigo, arbol_dict)

            if not isinstance(arbol_dict, dict) or "0.0.0.0.0.0.0.0.0" not in arbol_dict:
                return HttpResponseBadRequest("La IA no devolvió un JSON 5Q válido para el árbol.")

            arbol_json_5q = json.dumps(arbol_dict, ensure_ascii=False)
            tree = CausalTree(arbol_json_5q)

            base = reverse("accidentes:ia_arbol", args=[codigo])

            # --- DOT NEUTRO para guardar en BD (sin puntero) ---
            _cur = tree.current
            tree.current = None
            dot_neutro = tree.generate_dot(base_path=base)
            tree.current = _cur
            # ---------------------------------------------------

            # Versionado
            ultima_version = (
                ArbolCausas.objects.filter(accidente=accidente).aggregate(Max("version"))["version__max"] or 0
            )
            nueva_version = ultima_version + 1

            ArbolCausas.objects.filter(accidente=accidente).update(is_current=False)

            ArbolCausas.objects.create(
                accidente=accidente,
                version=nueva_version,
                is_current=True,
                arbol_json_5q=tree.export_to_5q_json(),
                arbol_json_dot=dot_neutro,   # <- guardamos SIN puntero
            )

            # DOT con highlight SOLO para renderizar
            try:
                dot_runtime = tree.generate_dot(base_path=base)
                svg = Source(dot_runtime).pipe(format="svg").decode("utf-8")
                svg = svg.replace('<?xml version="1.0" encoding="UTF-8" standalone="no"?>', "")
            except ExecutableNotFound:
                svg = None

            # Opciones para insertar "entre medio" desde el inicio (raíz)
            child_targets: list[dict[str, str]] = []
            if tree and tree.current and tree.current in tree.nodes:
                for cid in (tree.nodes[tree.current].get("children") or []):
                    if cid in tree.nodes:
                        child_targets.append({"id": cid, "label": tree.nodes[cid].get("label", "")})

            context = {
                "svg": svg,
                "current_id": tree.current,
                "current_label": tree.get_current_label(),
                "codigo": codigo,
                "modo_edicion": True,
                "show_boton_generar_inicial": False,
                "show_boton_regenerar": True,
                "puede_generar": True,
                "child_targets": child_targets,
            }
            return render(request, self.template_name, context)

        except Exception as e:
            try:
                _log_error(prompt_id, prompt_key, codigo, e)  # type: ignore[name-defined]
            except Exception:
                pass
            return HttpResponseBadRequest(f"No fue posible generar el árbol: {e}")
