# accidentes/forms.py

from .forms_template.buscar_accidente import BuscarAccidenteForm
from .forms_template.empresa           import EmpresaForm
from .forms_template.trabajador        import TrabajadorForm
from .forms_template.accidente         import AccidenteForm
from .forms_template.centro_trabajo    import CentroTrabajoForm
from .forms_template.declaracion       import DeclaracionForm
from .forms_template.document          import DocumentForm
from .forms_template.home              import home_view, home_assigned_cases_partial

__all__ = [
    "BuscarAccidenteForm",
    "EmpresaForm",
    "TrabajadorForm",
    "AccidenteForm",
    "CentroTrabajoForm",
    "DeclaracionForm",
    "DocumentForm",
    "home_view",
    "home_assigned_cases_partial",
]
