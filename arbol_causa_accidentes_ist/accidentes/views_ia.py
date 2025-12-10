from .views_api.prompt_utils    import call_ia_json, call_ia_text
from .views_api.fotos_documentos import FotosDocumentosView
from .views_api.declaraciones   import DeclaracionesIAView
from .views_api.relato          import RelatoIAView
from .views_api.hechos          import HechosIAView
from .views_api.arbol           import ArbolIAView
from .views_api.arbol           import GenerarArbolIACreateView
from .views_api.medidas_correctivas import MedidasCorrectivasView

from .views_api.generar_informe import GenerarInformeIAView


__all__ = [
    "call_ia_json", "call_ia_text",
    "FotosDocumentosView", "DeclaracionesIAView",
    "RelatoIAView", "HechosIAView", "ArbolIAView",
    "MedidasCorrectivasView", "GenerarArbolIACreateView",
    "GenerarInformeIAView"
]