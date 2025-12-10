# -*- coding: utf-8 -*-
import json
import logging

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin  # ← NUEVO

from accidentes.models import Declaraciones, PreguntasGuia, Relato
from .prompt_utils import call_ia_text
from accidentes.utils.mixins import AccidenteScopedByCodigoMixin

logger = logging.getLogger(__name__)


@method_decorator(csrf_protect, name="dispatch")
class RelatoIAView(LoginRequiredMixin, AccidenteScopedByCodigoMixin, View):  # ← LoginRequiredMixin agregado
    """
    Flujo paso-a-paso (minimizando llamadas a la API):
      1) generar_relato              -> crea relato_inicial
      2) generar_pregunta_1          -> payload: relato_inicial
      3) guardar_respuesta_1         -> guarda R1 y fraseQR1
      4) generar_pregunta_2          -> payload: relato_inicial + fraseQR1 (desde BD)
      5) guardar_respuesta_2         -> guarda R2 y fraseQR2
      6) generar_pregunta_3          -> payload: relato_inicial + fraseQR1 + fraseQR2 (desde BD)
      7) guardar_respuesta_3         -> guarda R3 y fraseQR3
      8) generar_relato_final        -> payload: relato_inicial + fraseQR1 + fraseQR2 + fraseQR3 (desde BD)
    """
    login_url = "/accounts/login/"
    template_name = "accidentes/relato.html"
    partial_name = "accidentes/partials/relato/_relato_wrapper.html"

    # ---------------- helpers ----------------
    @staticmethod
    def _dbg_blob(title: str, blob, maxlen: int = 600):
        """Log compacto para payloads/respuestas extensas."""
        try:
            if isinstance(blob, (dict, list)):
                text = json.dumps(blob, ensure_ascii=False)
            elif isinstance(blob, bytes):
                text = blob.decode("utf-8", "ignore")
            else:
                text = str(blob)
        except Exception:
            text = "<no-repr>"

        compact = " ".join(text.split())
        tail = "…" if len(compact) > maxlen else ""
        logger.debug("%s (len=%d): %s%s", title, len(compact), compact[:maxlen], tail)

    def _compute_ctx(self, request, codigo: str):
        accidente = self.accidente_from(codigo)
        relato = Relato.objects.filter(accidente=accidente, is_current=True).first()
        if not relato:
            paso = 1
        elif not relato.relato_final:
            paso = 2
        else:
            paso = 4
        return {"relato": relato, "codigo": codigo, "paso": paso, "accidente": accidente}

    def _render(self, request, codigo: str):
        ctx = self._compute_ctx(request, codigo)
        if request.headers.get("HX-Request"):
            return render(request, self.partial_name, ctx)
        return render(request, self.template_name, ctx)

    def _norm_cat(self, cat: str) -> str:
        c = (cat or "").strip().lower()
        if c in ("accidentado", "accidentada", "accidentados", "accidentadas"):
            return "accidentado"
        if c in ("testigo", "testigos"):
            return "testigo"
        if c in ("supervision", "supervisión", "supervisor", "supervisores"):
            return "supervisor"
        return ""

    # --- Helpers para FRASEOS en BD (usa EXPLÍCITAMENTE fraseQR1/2/3) ---
    def _get_frase_qr(self, relato, n: int) -> str:
        field = f"fraseQR{n}"
        return (getattr(relato, field, "") or "")

    def _set_frase_qr(self, relato, n: int, text: str) -> None:
        field = f"fraseQR{n}"
        if not hasattr(relato, field):
            logger.warning("Campo %s no existe en Relato. Verifica la migración.", field)
            return
        setattr(relato, field, text or "")
        try:
            relato.save(update_fields=[field])
        except Exception:
            relato.save()

    def _gather_data(self, accidente) -> str:
        declaraciones = {
            tipo: [
                {"pregunta": d.nombre or "", "respuesta": d.texto or ""}
                for d in Declaraciones.objects.filter(accidente=accidente, tipo_decl=tipo)
                if (d.texto or "").strip()
            ]
            for tipo in ("accidentado", "testigo", "supervisor")
        }

        pg_rows = (
            PreguntasGuia.objects.filter(accidente=accidente)
            .values("categoria", "pregunta", "objetivo", "respuesta")
        )
        agregados = {"accidentado": [], "testigo": [], "supervisor": []}
        for r in pg_rows:
            if not ((r.get("pregunta") or "").strip() or (r.get("respuesta") or "").strip()):
                continue
            k = self._norm_cat(r.get("categoria"))
            if not k:
                continue
            agregados[k].append(
                {
                    "pregunta": r.get("pregunta") or "",
                    "respuesta": r.get("respuesta") or "",
                    "objetivo": r.get("objetivo") or "",
                }
            )
        for k in ("accidentado", "testigo", "supervisor"):
            if agregados[k]:
                declaraciones.setdefault(k, []).extend(agregados[k])

        trabajador = getattr(accidente, "trabajador", None)
        centro = getattr(accidente, "centro", None)
        empresa = getattr(centro, "empresa", None)

        data = {
            "datos_generales": {
                "nombre_accidentado": getattr(trabajador, "nombre_trabajador", "") or "",
                "fecha": (getattr(accidente, "fecha_accidente", None) or "") and accidente.fecha_accidente.isoformat(),
                "hora": (getattr(accidente, "hora_accidente", None) or "") and accidente.hora_accidente.isoformat(),
                "actividad": getattr(empresa, "actividad", "") or "",
                "local": getattr(centro, "nombre_local", "") or "",
                "lugar_accidente": getattr(accidente, "lugar_accidente", "") or "",
                "lesion": getattr(accidente, "naturaleza_lesion", "") or "",
            },
            "operaciones": {
                "nombre proceso": getattr(accidente, "tarea", "") or "",
                "tarea u operación": getattr(accidente, "operacion", "") or "",
            },
            "declaraciones": declaraciones,
            "contexto": {
                "proceso habitual": getattr(accidente, "contexto", "") or "",
                "circunstancias del accidente": getattr(accidente, "circunstancias", "") or "",
            },
        }
        payload = json.dumps(data, ensure_ascii=False)
        if logger.isEnabledFor(logging.DEBUG):
            self._dbg_blob("IA payload initial_story (gather_data)", payload)
        return payload

    def _phrase_qa(self, pregunta: str, respuesta: str) -> str:
        """
        Payload de 'frasear_preguntas' SIN 'relato': solo 'pregunta' y 'respuesta'.
        """
        payload = json.dumps(
            {
                "pregunta": (pregunta or "").strip(),
                "respuesta": (respuesta or "").strip(),
            },
            ensure_ascii=False,
        )
        if logger.isEnabledFor(logging.DEBUG):
            self._dbg_blob("IA payload frasear_preguntas", payload)
        try:
            out = call_ia_text(payload, prompt_key="frasear_preguntas").strip()
            if logger.isEnabledFor(logging.DEBUG):
                self._dbg_blob("IA out frasear_preguntas", out)
            return out
        except Exception:
            logger.exception("Error en frasear_preguntas")
            return f"Pregunta: {pregunta}\nRespuesta: {respuesta}"

    # ----------------- HTTP -----------------
    def get(self, request, codigo: str):
        return self._render(request, codigo)

    def post(self, request, codigo: str):
        accidente = self.accidente_from(codigo)
        action = (request.POST.get("action") or "").strip()
        logger.debug("POST action=%s accidente_id=%s", action, getattr(accidente, "pk", None))

        # == 1) Generar relato inicial ==
        if action == "generar_relato":
            Relato.objects.filter(accidente=accidente, is_current=True).update(is_current=False)
            try:
                initial_story = self._gather_data(accidente)
                if logger.isEnabledFor(logging.DEBUG):
                    self._dbg_blob("IA in relato_inicial", initial_story)

                texto_relato = call_ia_text(initial_story, prompt_key="relato_inicial").strip()

                if logger.isEnabledFor(logging.DEBUG):
                    self._dbg_blob("IA out relato_inicial", texto_relato)

                Relato.objects.create(
                    accidente=accidente,
                    relato_inicial=texto_relato,
                    is_current=True,
                )
                messages.success(request, "Relato inicial generado.")
            except Exception as e:
                logger.exception("Error generando relato inicial")
                messages.error(request, f"Error generando relato inicial: {e}")
            return self._render(request, codigo)

        # == Guardar cambios al relato inicial ==
        if action == "guardar_relato_inicial":
            relato = Relato.objects.filter(accidente=accidente, is_current=True).first()
            if not relato:
                messages.error(request, "No existe un relato activo.")
                return self._render(request, codigo)
            relato_input = (request.POST.get("relato_input") or "").strip()
            if not relato_input:
                messages.warning(request, "El relato no puede estar vacío.")
                return self._render(request, codigo)
            if logger.isEnabledFor(logging.DEBUG):
                self._dbg_blob("Save relato_inicial (user-edited)", relato_input)
            relato.relato_inicial = relato_input
            relato.save()
            messages.success(request, "Relato guardado.")
            return self._render(request, codigo)

        # == 2) Generar P1 ==
        if action == "generar_pregunta_1":
            relato = Relato.objects.filter(accidente=accidente, is_current=True).first()
            if not relato:
                messages.error(request, "No existe un relato activo.")
                return self._render(request, codigo)

            relato_input = (request.POST.get("relato_input") or "").strip()
            if relato_input:
                if logger.isEnabledFor(logging.DEBUG):
                    self._dbg_blob("Persist relato_inicial before P1", relato_input)
                relato.relato_inicial = relato_input
                relato.save()

            try:
                if logger.isEnabledFor(logging.DEBUG):
                    self._dbg_blob("IA in investiga1", relato.relato_inicial)
                p1 = call_ia_text(relato.relato_inicial, prompt_key="investiga1").strip()
                if logger.isEnabledFor(logging.DEBUG):
                    self._dbg_blob("IA out investiga1 (P1)", p1)

                relato.pregunta_1 = p1
                relato.save(update_fields=["relato_inicial", "pregunta_1"])
                messages.success(request, "Pregunta 1 generada.")
            except Exception as e:
                logger.exception("Error generando pregunta 1")
                messages.error(request, f"Error generando Pregunta 1: {e}")
            return self._render(request, codigo)

        # Guardar R1 (+ fraseQR1)
        if action == "guardar_respuesta_1":
            relato = Relato.objects.filter(accidente=accidente, is_current=True).first()
            if not relato or not relato.pregunta_1:
                messages.error(request, "Primero genera la Pregunta 1.")
                return self._render(request, codigo)
            r1 = (request.POST.get("respuesta_1") or "").strip()
            if not r1:
                messages.warning(request, "Debes escribir la respuesta 1.")
                return self._render(request, codigo)

            if logger.isEnabledFor(logging.DEBUG):
                self._dbg_blob("Save respuesta_1", r1)
            relato.respuesta_1 = r1
            try:
                frase = self._phrase_qa(relato.pregunta_1, r1)
                self._set_frase_qr(relato, 1, frase)
            except Exception:
                logger.exception("No se pudo generar/guardar fraseQR1")
            relato.save(update_fields=["respuesta_1"])
            messages.success(request, "Respuesta 1 guardada.")
            return self._render(request, codigo)

        # == 4) Generar P2 (usa fraseQR1 desde BD) ==
        if action == "generar_pregunta_2":
            relato = Relato.objects.filter(accidente=accidente, is_current=True).first()
            if not relato or not (relato.pregunta_1 and relato.respuesta_1):
                messages.error(request, "Para generar la Pregunta 2, debes tener la Pregunta 1 y su respuesta.")
                return self._render(request, codigo)

            relato_input = (request.POST.get("relato_input") or "").strip()
            if relato_input:
                if logger.isEnabledFor(logging.DEBUG):
                    self._dbg_blob("Persist relato_inicial before P2", relato_input)
                relato.relato_inicial = relato_input
                relato.save(update_fields=["relato_inicial"])

            qap1 = self._get_frase_qr(relato, 1)
            if not qap1:
                messages.warning(request, "Falta el fraseo 1 (fraseQR1). Guarda la Respuesta 1 para continuar.")
                return self._render(request, codigo)

            try:
                payload = {"relato_inicial": relato.relato_inicial, "qap": qap1}
                if logger.isEnabledFor(logging.DEBUG):
                    self._dbg_blob("IA in investiga2", payload)

                p2 = call_ia_text(json.dumps(payload, ensure_ascii=False), prompt_key="investiga2").strip()

                if logger.isEnabledFor(logging.DEBUG):
                    self._dbg_blob("IA out investiga2 (P2)", p2)

                relato.pregunta_2 = p2
                relato.save(update_fields=["pregunta_2"])
                messages.success(request, "Pregunta 2 generada.")
            except Exception as e:
                logger.exception("Error generando pregunta 2")
                messages.error(request, f"Error generando Pregunta 2: {e}")
            return self._render(request, codigo)

        # Guardar R2 (+ fraseQR2)
        if action == "guardar_respuesta_2":
            relato = Relato.objects.filter(accidente=accidente, is_current=True).first()
            if not relato or not relato.pregunta_2:
                messages.error(request, "Primero genera la Pregunta 2.")
                return self._render(request, codigo)
            r2 = (request.POST.get("respuesta_2") or "").strip()
            if not r2:
                messages.warning(request, "Debes escribir la respuesta 2.")
                return self._render(request, codigo)

            if logger.isEnabledFor(logging.DEBUG):
                self._dbg_blob("Save respuesta_2", r2)
            relato.respuesta_2 = r2
            try:
                frase = self._phrase_qa(relato.pregunta_2, r2)
                self._set_frase_qr(relato, 2, frase)
            except Exception:
                logger.exception("No se pudo generar/guardar fraseQR2")
            relato.save(update_fields=["respuesta_2"])
            messages.success(request, "Respuesta 2 guardada.")
            return self._render(request, codigo)

        # == 6) Generar P3 (usa fraseQR1 + fraseQR2 desde BD) ==
        if action == "generar_pregunta_3":
            relato = Relato.objects.filter(accidente=accidente, is_current=True).first()
            if not relato or not (relato.pregunta_1 and relato.respuesta_1 and relato.pregunta_2 and relato.respuesta_2):
                messages.error(request, "Para generar la Pregunta 3, debes tener P1+R1 y P2+R2.")
                return self._render(request, codigo)

            relato_input = (request.POST.get("relato_input") or "").strip()
            if relato_input:
                if logger.isEnabledFor(logging.DEBUG):
                    self._dbg_blob("Persist relato_inicial before P3", relato_input)
                relato.relato_inicial = relato_input
                relato.save(update_fields=["relato_inicial"])

            qap1 = self._get_frase_qr(relato, 1)
            qap2 = self._get_frase_qr(relato, 2)
            if not qap1 or not qap2:
                messages.warning(request, "Faltan fraseos previos (fraseQR1 y/o fraseQR2). Guarda las respuestas anteriores.")
                return self._render(request, codigo)

            try:
                payload = {"relato_inicial": relato.relato_inicial, "qap1": qap1, "qap2": qap2}
                if logger.isEnabledFor(logging.DEBUG):
                    self._dbg_blob("IA in investiga3", payload)

                p3 = call_ia_text(json.dumps(payload, ensure_ascii=False), prompt_key="investiga3").strip()

                if logger.isEnabledFor(logging.DEBUG):
                    self._dbg_blob("IA out investiga3 (P3)", p3)

                relato.pregunta_3 = p3
                relato.save(update_fields=["pregunta_3"])
                messages.success(request, "Pregunta 3 generada.")
            except Exception as e:
                logger.exception("Error generando pregunta 3")
                messages.error(request, f"Error generando Pregunta 3: {e}")
            return self._render(request, codigo)

        # Guardar R3 (+ fraseQR3)
        if action == "guardar_respuesta_3":
            relato = Relato.objects.filter(accidente=accidente, is_current=True).first()
            if not relato or not relato.pregunta_3:
                messages.error(request, "Primero genera la Pregunta 3.")
                return self._render(request, codigo)
            r3 = (request.POST.get("respuesta_3") or "").strip()
            if not r3:
                messages.warning(request, "Debes escribir la respuesta 3.")
                return self._render(request, codigo)

            if logger.isEnabledFor(logging.DEBUG):
                self._dbg_blob("Save respuesta_3", r3)
            relato.respuesta_3 = r3
            try:
                frase = self._phrase_qa(relato.pregunta_3, r3)
                self._set_frase_qr(relato, 3, frase)
            except Exception:
                logger.exception("No se pudo generar/guardar fraseQR3")
            relato.save(update_fields=["respuesta_3"])
            messages.success(request, "Respuesta 3 guardada.")
            return self._render(request, codigo)

        # == 8) Generar relato final (usa fraseQRn desde BD; NO re-frasea) ==
        if action == "generar_relato_final":
            relato = Relato.objects.filter(accidente=accidente, is_current=True).first()
            if not relato:
                messages.error(request, "No existe un relato activo.")
                return self._render(request, codigo)

            relato_input = (request.POST.get("relato_input") or "").strip() or (relato.relato_inicial or "")
            if not relato_input:
                messages.warning(request, "El relato base no puede estar vacío.")
                return self._render(request, codigo)

            if not (relato.pregunta_1 and relato.respuesta_1 and
                    relato.pregunta_2 and relato.respuesta_2 and
                    relato.pregunta_3 and relato.respuesta_3):
                messages.warning(request, "Debes completar las tres preguntas y sus respuestas antes de generar el final.")
                return self._render(request, codigo)

            qap1 = self._get_frase_qr(relato, 1)
            qap2 = self._get_frase_qr(relato, 2)
            qap3 = self._get_frase_qr(relato, 3)
            if not (qap1 and qap2 and qap3):
                messages.warning(request, "Faltan fraseos (fraseQR1, fraseQR2 y/o fraseQR3). Guarda todas las respuestas antes de continuar.")
                return self._render(request, codigo)

            try:
                relato.relato_inicial = relato_input

                final_payload = {"relato_inicial": relato_input, "qap1": qap1, "qap2": qap2, "qap3": qap3}
                if logger.isEnabledFor(logging.DEBUG):
                    self._dbg_blob("IA in reporte_final", final_payload)

                out_final = call_ia_text(json.dumps(final_payload, ensure_ascii=False), prompt_key="reporte_final").strip()

                if logger.isEnabledFor(logging.DEBUG):
                    self._dbg_blob("IA out reporte_final", out_final)

                relato.relato_final = out_final
                relato.save(update_fields=["relato_inicial", "relato_final"])
                messages.success(request, "Relato final generado correctamente.")
            except Exception as e:
                logger.exception("Error generando relato final")
                messages.error(request, f"Error generando relato final: {e}")
            return self._render(request, codigo)

        # == Guardar manual del relato final ==
        if action == "guardar_relato_final":
            relato = Relato.objects.filter(accidente=accidente, is_current=True).first()
            if relato:
                texto_final = (request.POST.get("relato_input") or "").strip()
                if not texto_final:
                    messages.warning(request, "El relato final no puede quedar vacío.")
                else:
                    if logger.isEnabledFor(logging.DEBUG):
                        self._dbg_blob("Save relato_final (user-edited)", texto_final)
                    relato.relato_final = texto_final
                    relato.save(update_fields=["relato_final"])
                    messages.success(request, "Relato final guardado correctamente.")
            else:
                messages.error(request, "No existe un relato activo.")
            return self._render(request, codigo)

        # == Eliminar y reiniciar ==
        if action == "eliminar_y_reiniciar":
            relato = Relato.objects.filter(accidente=accidente, is_current=True).first()
            if relato:
                relato.is_current = False
                relato.save(update_fields=["is_current"])
                messages.success(request, "Relato eliminado. Puedes generar uno nuevo.")
            else:
                messages.info(request, "No había un relato activo.")
            return self._render(request, codigo)

        messages.error(request, "Acción no reconocida.")
        return self._render(request, codigo)
