# accidentes/utils/progress.py
from __future__ import annotations

from django.urls import reverse
from typing import Dict, List, Optional

from accidentes.models import (
    Accidentes,
    Relato,
    Hechos,
    ArbolCausas,
    Informes,
    Documentos,
)

__all__ = ["build_case_progress"]


def _url(name: str, codigo: str) -> str:
    """Pequeño helper para reverses con <codigo>."""
    return reverse(name, args=[codigo])


def build_case_progress(accidente: Accidentes) -> Dict:
    """
    Construye el progreso general del caso en pasos.
    Devuelve:
      {
        "steps": [ {key, label, url, done}, ... ],
        "percent": int,
        "next_key": Optional[str]
      }
    """
    codigo = accidente.codigo_accidente

    # Reglas mínimas para considerar "listo" cada paso
    done_empresa     = accidente.empresa_id is not None
    done_centro      = accidente.centro_id is not None
    done_trabajador  = accidente.trabajador_id is not None
    done_accidente   = bool(accidente.fecha_accidente)  # usa lo más crítico
    done_relato      = Relato.objects.filter(accidente=accidente, is_current=True, relato_final__isnull=False).exists()
    done_hechos      = Hechos.objects.filter(accidente=accidente).exists()
    done_arbol       = ArbolCausas.objects.filter(accidente=accidente, is_current=True).exists()
    done_docs        = Documentos.objects.filter(accidente=accidente).exists()
    done_informe     = Informes.objects.filter(accidente=accidente, is_current=True).exists()

    steps: List[Dict] = [
        {
            "key": "empresa",
            "label": "Datos empresa",
            "url":  _url("accidentes:empresa", codigo),
            "done": done_empresa,
        },
        {
            "key": "centro",
            "label": "Centro de trabajo",
            "url":  _url("accidentes:cargar_accidente", codigo) if False else _url("accidentes:empresa", codigo),
            # ↑ Si tienes una vista específica del centro, cambia la URL arriba.
            "done": done_centro,
        },
        {
            "key": "trabajador",
            "label": "Datos trabajador",
            "url":  _url("accidentes:trabajador", codigo),
            "done": done_trabajador,
        },
        {
            "key": "accidente",
            "label": "Datos del accidente",
            "url":  _url("accidentes:accidente", codigo),
            "done": done_accidente,
        },
        {
            "key": "relato",
            "label": "Relato",
            "url":  _url("accidentes:ia_relato", codigo),
            "done": done_relato,
        },
        {
            "key": "hechos",
            "label": "Hechos",
            "url":  _url("accidentes:ia_hechos", codigo),
            "done": done_hechos,
        },
        {
            "key": "arbol",
            "label": "Árbol de causas",
            "url":  _url("accidentes:ia_arbol", codigo),
            "done": done_arbol,
        },
        {
            "key": "documentos",
            "label": "Fotos y documentos",
            "url":  _url("accidentes:ia_fotos", codigo),
            "done": done_docs,
        },
        {
            "key": "informe",
            "label": "Generar informe",
            "url":  _url("accidentes:generar_informe", codigo),
            "done": done_informe,
        },
    ]

    total = len(steps)
    done_count = sum(1 for s in steps if s["done"])
    percent = int(round(done_count * 100.0 / total)) if total else 0

    next_key: Optional[str] = None
    for s in steps:
        if not s["done"]:
            next_key = s["key"]
            break

    return {
        "steps": steps,
        "percent": percent,
        "next_key": next_key,
    }
