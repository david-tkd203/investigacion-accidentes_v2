# accidentes/views_api/declaraciones.py

import json
import uuid
from uuid import uuid4

from django.http import Http404, HttpResponseNotAllowed, HttpResponse
from django.shortcuts import render
from django.views import View
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
import logging
from django.template.loader import render_to_string


logger = logging.getLogger(__name__)

from .prompt_utils import call_ia_json
from accidentes.models import (
    Accidentes,
    Declaraciones,   # si no lo usas, puedes eliminar este import
    PreguntasGuia,
    Documentos,
)
from accidentes.utils.mixins import AnchorRedirectMixin, AccidenteScopedByCodigoMixin


class DeclaracionesIAView(LoginRequiredMixin, AnchorRedirectMixin, AccidenteScopedByCodigoMixin, View):
    """
    Vista única GET/POST, con scoping robusto:
    - El accidente se resuelve vía AccidenteScopedByCodigoMixin (self.accidente),
      que valida alcance con get_accidente_scoped_or_404(user, codigo=...).
    - No depende de la sesión (sync_session=False).
    - Para HTMX, devuelve parciales (wrapper o OOB) como en tu patrón anterior.
    """
    login_url = "/accounts/login/"
    template_name = "accidentes/declaraciones.html"
    sync_session = False  # no tocar sesión; todo por código

    # ----------------- helpers -----------------
    @staticmethod
    def _as_str(value):
        """Convierte fechas/horas/None a string seguro para el JSON del prompt."""
        if value is None:
            return ""
        try:
            if hasattr(value, "isoformat"):
                return value.isoformat()
        except Exception:
            pass
        return str(value)

    def _build_context(self, accidente, codigo):
        """
        Un solo lugar para armar el contexto de GET y de las respuestas HTMX.
        """
        # Declaraciones (si las ocupas en el template)
        declaraciones = Declaraciones.objects.filter(accidente=accidente)

        # Todas las preguntas del caso
        all_qs = PreguntasGuia.objects.filter(accidente=accidente)

        # Categorías (mantenemos compat con variantes en BD)
        qs_accidentado = all_qs.filter(categoria__iexact="accidentado")
        qs_testigo = all_qs.filter(categoria__in=["testigo", "testigos"])
        qs_supervision = all_qs.filter(
            categoria__in=["supervision", "supervisión", "supervisor", "supervisores"]
        )

        nonempty = Q(pregunta__isnull=False) & ~Q(pregunta__exact="")
        count_accidentado = qs_accidentado.filter(nonempty).count()
        count_testigo = qs_testigo.filter(nonempty).count()
        count_supervision = qs_supervision.filter(nonempty).count()
        has_generated = all_qs.filter(nonempty).exists()

        return {
            "accidente": accidente,
            "declaraciones": declaraciones,
            "qs_accidentado": qs_accidentado,
            "qs_testigo": qs_testigo,
            "qs_supervision": qs_supervision,
            "count_accidentado": count_accidentado,
            "count_testigo": count_testigo,
            "count_supervision": count_supervision,
            "has_generated": has_generated,
            "codigo": codigo,
        }
    def _render_notifications(self, request) -> str:
        """Devuelve el HTML del área de notificaciones con soporte OOB."""
        return render_to_string("accidentes/notification.html", request=request)

    def _http_response_with_notif(self, request, html: str = "") -> HttpResponse:
        """
        Devuelve una HttpResponse concatenando (opcionalmente) HTML y SIEMPRE el
        fragmento de notificaciones OOB.
        """
        notif = self._render_notifications(request)
        return HttpResponse((html or "") + notif)
    # ----------------- GET -----------------
    def get(self, request, codigo):
        # Accidente ya viene resuelto en dispatch() del mixin → self.accidente
        ctx = self._build_context(self.accidente, codigo)
        return render(request, self.template_name, ctx)

    # ----------------- POST -----------------
    def post(self, request, codigo):
        accidente = self.accidente  # ya scoped
        action = (request.POST.get("action") or "").strip()
        anchor = (request.POST.get("anchor") or "").strip()
        is_htmx = bool(getattr(request, "htmx", False) or request.headers.get("HX-Request") == "true")

        # Helpers locales
        def get_slot_by_pk(pk_raw):
            try:
                pk = int(pk_raw)
            except (TypeError, ValueError):
                return None
            return PreguntasGuia.objects.filter(accidente=accidente, pk=pk).first()

        # 1) Generar preguntas y documentos con IA
        if action == "generate":
            trabajador = getattr(accidente, "trabajador", None)
            nombre_trabajador = getattr(trabajador, "nombre_trabajador", "") if trabajador else ""

            centro = getattr(accidente, "centro", None)
            empresa = getattr(centro, "empresa", None) if centro else None
            # Fallback por si no hay centro->empresa, intenta con trabajador->empresa
            if not empresa and trabajador:
                empresa = getattr(trabajador, "empresa", None)

            # ✅ Actividad económica (empresa.actividad)
            actividad = getattr(empresa, "actividad", "") if empresa else ""

            # ✅ Centro de trabajo (centro.nombre_local)
            nombre_local = getattr(centro, "nombre_local", "") if centro else ""

            preinitial_data = {
                "datos_generales": {
                    "nombre_accidentado": self._as_str(nombre_trabajador),
                    "fecha": self._as_str(getattr(accidente, "fecha_accidente", "")),
                    "hora": self._as_str(getattr(accidente, "hora_accidente", "")),
                    "actividad": self._as_str(actividad),
                    "local": self._as_str(nombre_local),
                    "lugar_accidente": self._as_str(getattr(accidente, "lugar_accidente", "")),
                    "lesion": self._as_str(getattr(accidente, "naturaleza_lesion", "")),
                },
                "operaciones": {
                    "nombre proceso": self._as_str(getattr(accidente, "tarea", "")),
                    "tarea u operación": self._as_str(getattr(accidente, "operacion", "")),
                },
                "contexto": {
                    "proceso habitual": self._as_str(getattr(accidente, "contexto", "")),
                    "circunstancias del accidente": self._as_str(getattr(accidente, "circunstancias", "")),
                },
            }

            payload = {"preinitial_data": preinitial_data}

            # ---- LOGGING SIMPLE A CONSOLA ----
            prompt_key = "explora"
            prompt_id = uuid4().hex  # id único para correlacionar request/response en consola

            try:
                # imprime el id del prompt, el prompt_key y el payload
                logger.info(
                    "[IA][request] prompt_id=%s prompt_key=%s codigo=%s payload=%s",
                    prompt_id, prompt_key, codigo, json.dumps(payload, ensure_ascii=False, indent=2)
                )

                raw = call_ia_json(
                    json.dumps(payload, ensure_ascii=False, indent=2),
                    prompt_key=prompt_key,
                )

                # imprime la respuesta (dict o str)
                try:
                    response_str = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False, indent=2)
                except Exception:
                    response_str = f"<<no-serializable: {type(raw)}>>"

                logger.info(
                    "[IA][response] prompt_id=%s prompt_key=%s codigo=%s response=%s",
                    prompt_id, prompt_key, codigo, response_str
                )

                # --------- tu lógica original: reset y creación ----------
                PreguntasGuia.objects.filter(accidente=accidente).delete()
                Documentos.objects.filter(accidente=accidente).delete()

                if isinstance(raw, dict):
                    for rol, items in raw.items():
                        if rol == "documentos":
                            continue
                        if not isinstance(items, (list, tuple)):
                            continue
                        for item in items:
                            PreguntasGuia.objects.create(
                                accidente=accidente,
                                uuid=str(item.get("id")) or str(uuid4()),
                                categoria=rol,
                                pregunta=item.get("pregunta", "") or "",
                                objetivo=item.get("objetivo", "") or "",
                                respuesta=""
                            )
                    documentos = raw.get("documentos", [])
                    if isinstance(documentos, list):
                        for doc in documentos:
                            Documentos.objects.create(
                                accidente=accidente,
                                documento_id=doc.get("id") or str(uuid4()),
                                documento=doc.get("documento", "") or "",
                                objetivo=doc.get("objetivo", "") or ""
                            )

                messages.success(request, "Preguntas y documentos generados correctamente.")

            except Exception as e:
                # imprime el error asociado al mismo prompt_id
                logger.exception(
                    "[IA][error] prompt_id=%s prompt_key=%s codigo=%s error=%s",
                    prompt_id, prompt_key, codigo, str(e)
                )
                messages.error(request, f"Error IA: {e}")

            if is_htmx:
                ctx = self._build_context(accidente, codigo)
                html = render_to_string("accidentes/partials/entrevistas/_declaraciones_wrapper.html", ctx, request=request)
                return self._http_response_with_notif(request, html)

            return self._build_redirect(request, "accidentes:ia_declaraciones", args=[codigo], anchor=anchor)

        # 2) Guardar respuesta (HTMX o normal)
        if action == "save_single":
            slot = get_slot_by_pk(request.POST.get("slot_pk"))
            if slot:
                slot.respuesta = (request.POST.get("respuesta") or "").strip()
                slot.save(update_fields=["respuesta"])
                messages.success(request, "Respuesta guardada.")
            else:
                messages.error(request, "Slot no encontrado.")

            if is_htmx:
                # No cambiamos HTML; solo feedback
                return self._http_response_with_notif(request)

            return self._build_redirect(request, "accidentes:ia_declaraciones", args=[codigo], anchor=anchor)

        # 3) Eliminar pregunta
        if action == "delete":
            slot = get_slot_by_pk(request.POST.get("slot_pk"))
            deleted = False
            if slot:
                slot.delete()
                deleted = True

            if is_htmx:
                nonempty = Q(pregunta__isnull=False) & ~Q(pregunta__exact="")
                all_qs = PreguntasGuia.objects.filter(accidente=accidente)

                # Si ya NO hay preguntas -> reemplazar todo el wrapper vía OOB
                has_generated = all_qs.filter(nonempty).exists()
                if not has_generated:
                    ctx_full = self._build_context(accidente, codigo)
                    ctx_full["oob"] = True  # el partial hará hx-swap-oob="outerHTML"
                    html = render_to_string(
                        "accidentes/partials/entrevistas/_declaraciones_wrapper.html",
                        ctx_full,
                        request=request,
                    )
                    return self._http_response_with_notif(request, html)

                # Aún hay preguntas: actualizamos solo los contadores por OOB
                ctx_badges = {
                    "count_accidentado": all_qs.filter(categoria__iexact="accidentado").filter(nonempty).count(),
                    "count_testigo":     all_qs.filter(categoria__in=["testigo", "testigos"]).filter(nonempty).count(),
                    "count_supervision": all_qs.filter(
                        categoria__in=["supervision", "supervisión", "supervisor", "supervisores"]
                    ).filter(nonempty).count(),
                }
                html = render_to_string("accidentes/partials/entrevistas/_badges_oob.html", ctx_badges, request=request)
                return self._http_response_with_notif(request, html)


            if deleted:
                messages.success(request, "Pregunta eliminada definitivamente.")
            else:
                messages.error(request, "No se encontró la pregunta a eliminar.")

            return self._build_redirect(request, "accidentes:ia_declaraciones", args=[codigo], anchor=anchor)

        # 4) Reemplazar contenido de un slot existente (opcional, si lo usas)
        if action == "add":
            slot = get_slot_by_pk(request.POST.get("slot_id") or request.POST.get("key"))
            q = (request.POST.get("new_pregunta") or "").strip()
            o = (request.POST.get("new_objetivo") or "").strip()
            if slot and q and o:
                slot.pregunta = q
                slot.objetivo = o
                slot.respuesta = ""
                slot.save(update_fields=["pregunta", "objetivo", "respuesta"])
                messages.success(request, "Pregunta añadida.")
            else:
                messages.warning(request, "Completa todos los campos y slot válido.")
            return self._build_redirect(request, "accidentes:ia_declaraciones", args=[codigo], anchor=anchor)

        if action == "save_bulk":
            pks = request.POST.getlist("slot_pk")
            resps = request.POST.getlist("respuesta")

            anchor = (request.POST.get("anchor") or "").strip()

            updated_count = 0
            try:
                # Normaliza a enteros válidos y conserva orden
                pk_ints = []
                for raw in pks:
                    try:
                        pk_ints.append(int(raw))
                    except (TypeError, ValueError):
                        continue

                qs = PreguntasGuia.objects.filter(accidente=accidente, pk__in=pk_ints)
                by_pk = {obj.pk: obj for obj in qs}

                to_update = []
                for pk, resp in zip(pk_ints, resps):
                    obj = by_pk.get(pk)
                    if obj is None:
                        continue
                    if (obj.respuesta or "") == (resp or ""): continue
                    obj.respuesta = (resp or "").strip()
                    to_update.append(obj)

                if to_update:
                    PreguntasGuia.objects.bulk_update(to_update, ["respuesta"])
                    updated_count = len(to_update)

                messages.success(request, f"Se guardaron {updated_count} respuesta(s).")
            except Exception as e:
                messages.error(request, f"No se pudieron guardar las respuestas: {e}")

            if is_htmx:
                return self._http_response_with_notif(request)

            return self._build_redirect(
                request,
                "accidentes:ia_declaraciones",
                args=[codigo],
                anchor=anchor
            )

        # 5) Crear NUEVA pregunta desde el modal (HTMX o no-HTMX)
        if action == "add_new":
            tab_cat = (request.POST.get("categoria") or "").strip().lower()  # accidentado|testigo|supervision
            q = (request.POST.get("new_pregunta") or "").strip()
            o = (request.POST.get("new_objetivo") or "").strip()

            CAT_MAP = {
                "accidentado": "accidentado",
                "testigo": "testigos",
                "supervision": "supervisores",
            }
            db_cat = CAT_MAP.get(tab_cat, tab_cat)

            created = None
            if tab_cat and q and o:
                created = PreguntasGuia.objects.create(
                    accidente=accidente,
                    uuid=str(uuid.uuid4()),
                    categoria=db_cat,
                    pregunta=q,
                    objetivo=o,
                    respuesta=""
                )
                messages.success(request, "Pregunta creada correctamente.")
            else:
                messages.warning(request, "Completa los campos requeridos.")

            if is_htmx:
                nonempty = Q(pregunta__isnull=False) & ~Q(pregunta__exact="")
                all_qs = PreguntasGuia.objects.filter(accidente=accidente)

                ctx_counts = {
                    "count_accidentado": all_qs.filter(categoria__iexact="accidentado").filter(nonempty).count(),
                    "count_testigo":     all_qs.filter(categoria__in=["testigo", "testigos"]).filter(nonempty).count(),
                    "count_supervision": all_qs.filter(
                        categoria__in=["supervision", "supervisión", "supervisor", "supervisores"]
                    ).filter(nonempty).count(),
                }

                if tab_cat == "accidentado":
                    slots = all_qs.filter(categoria__iexact="accidentado").order_by("-pk")
                elif tab_cat == "testigo":
                    slots = all_qs.filter(categoria__in=["testigo", "testigos"]).order_by("-pk")
                else:
                    slots = all_qs.filter(
                        categoria__in=["supervision", "supervisión", "supervisor", "supervisores"]
                    ).order_by("-pk")

                ctx_grid = {"categoria": tab_cat, "slots": slots, "codigo": codigo}

                html = render_to_string(
                    "accidentes/partials/entrevistas/_add_new_response.html",
                    {**ctx_counts, **ctx_grid},
                    request=request,
                )
                resp = self._http_response_with_notif(request, html)
                resp["HX-Trigger"] = "question-added"
                return resp

            return self._build_redirect(request, "accidentes:ia_declaraciones", args=[codigo], anchor=anchor)

        return HttpResponseNotAllowed(["GET", "POST"])
