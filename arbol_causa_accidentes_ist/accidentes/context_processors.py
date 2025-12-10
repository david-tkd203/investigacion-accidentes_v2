# accidentes/context_processors.py
from __future__ import annotations
from typing import Dict, Optional
from django.urls import resolve
from accidentes.models import Accidentes
from .utils.progress import build_case_progress


def case_progress(request) -> Dict:
    """
    Inyecta en contexto:
      - progress (dict) para la barra
      - progress_active_key (str) para resaltar el paso actual
    Solo actúa en páginas que traen <codigo> en la URL.
    """
    rm = getattr(request, "resolver_match", None)
    if not rm:
        return {}

    codigo = rm.kwargs.get("codigo")
    if not codigo:
        return {}

    try:
        acc = Accidentes.objects.get(codigo_accidente=codigo)
    except Accidentes.DoesNotExist:
        return {}

    progress = build_case_progress(acc)

    # Mapear nombre de ruta actual a la key del paso
    url_to_key = {
        "empresa": "empresa",
        "trabajador": "trabajador",
        "accidente": "accidente",
        "ia_relato": "relato",
        "ia_hechos": "hechos",
        "ia_arbol": "arbol",
        "ia_fotos": "documentos",
        "generar_informe": "informe",
        # si tienes vista específica para el centro, mapea aquí:
        # "centro": "centro",
    }
    active_key = url_to_key.get(rm.url_name)

    return {
        "progress": progress,
        "progress_active_key": active_key,
    }
