# accidentes/utils/change_detector.py
from __future__ import annotations
from typing import Dict, Iterable
from django.core.cache import cache

# Orden lógico de pasos
STEP_ORDER: Iterable[str] = (
    "empresa", "trabajador", "accidente",
    "relato", "hechos", "arbol", "documentos", "informe"
)

# Dependencias: al cambiar una clave, todo lo posterior queda "stale"
DEPENDENCIES = {
    "empresa":     ("relato", "hechos", "arbol", "documentos", "informe"),
    "trabajador":  ("relato", "hechos", "arbol", "documentos", "informe"),
    "accidente":   ("relato", "hechos", "arbol", "documentos", "informe"),
    "relato":      ("hechos", "arbol", "documentos", "informe"),
    "hechos":      ("arbol", "documentos", "informe"),
    "arbol":       ("documentos", "informe"),
    "documentos":  ("informe",),
    "informe":     (),
}

def _key(codigo: str) -> str:
    return f"stale:{codigo}"

def get_flags(codigo: str) -> Dict[str, bool]:
    flags = cache.get(_key(codigo))
    if not isinstance(flags, dict):
        # inicializa todo en False
        flags = {k: False for k in STEP_ORDER}
        cache.set(_key(codigo), flags, timeout=None)
    # asegurar llaves nuevas
    for k in STEP_ORDER:
        flags.setdefault(k, False)
    return flags

def save_flags(codigo: str, flags: Dict[str, bool]) -> None:
    cache.set(_key(codigo), flags, timeout=None)

def mark_changed(codigo: str, step: str) -> None:
    """Marca 'step' como cambiado y todo lo dependiente como 'stale'."""
    flags = get_flags(codigo)
    step = step.lower()
    # el propio step se considera 'pendiente' (requiere revisión/regeneración)
    if step in flags:
        flags[step] = True
    for dep in DEPENDENCIES.get(step, ()):
        flags[dep] = True
    save_flags(codigo, flags)

def mark_refreshed(codigo: str, step: str) -> None:
    """Limpia el flag del paso cuando se ha actualizado/regenerado."""
    flags = get_flags(codigo)
    step = step.lower()
    if step in flags:
        flags[step] = False
    save_flags(codigo, flags)
