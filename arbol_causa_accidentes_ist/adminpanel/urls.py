# adminpanel/urls.py
from django.urls import path
from .views import (
    MisInvestigacionesView,
    MisInvestigacionesPartialView,
    CrearInvestigacionView,
    trabajador_lookup_htmx, 
    trabajador_modal_htmx, 
    trabajador_crear_htmx,
    usuario_lookup_htmx,
    usuario_select_htmx,
    empresas_por_holding_htmx,
    trabajador_select_htmx,
)
from adminpanel.admin_function.descargar_informe import (
    descargar_informe,
    descargar_documento,
)

from adminpanel.admin_function.report_excel import (
    ReporteExcelView,
    ReporteExcelPreviewHTMX,
    ReporteExcelTableHTMX,
    ReporteExcelFiltersHTMX
)

app_name = "adminpanel"

urlpatterns = [
    path("", MisInvestigacionesView.as_view(), name="home"),
    path("mis-investigaciones/", MisInvestigacionesView.as_view(), name="mis_investigaciones"),
    path("mis-investigaciones/partial/", MisInvestigacionesPartialView.as_view(), name="mis_investigaciones_partial"),
    path("accidentes/crear/", CrearInvestigacionView.as_view(), name="crear_investigacion"),

    # HTMX auxiliares to create accidente
    path("htmx/trabajador/lookup/", trabajador_lookup_htmx, name="trabajador_lookup"),
    path("htmx/trabajador/modal/", trabajador_modal_htmx, name="trabajador_modal"),
    path("htmx/trabajador/crear/", trabajador_crear_htmx, name="trabajador_crear"),
    path("htmx/usuario/lookup/", usuario_lookup_htmx, name="usuario_lookup"),
    path("htmx/usuario/select/", usuario_select_htmx, name="usuario_select"),
    path("htmx/empresa/options/", empresas_por_holding_htmx, name="empresas_por_holding"),
    path("htmx/trabajador/seleccionar/", trabajador_select_htmx, name="trabajador_select"),

    path("mis-investigaciones/<str:codigo>/descargar/", descargar_informe, name="descargar_informe"),
    path("documentos/<int:doc_id>/descargar/", descargar_documento, name="descargar_documento"),

    # ⬇️ NUEVO: Reporte Excel + preview HTMX
    path("reportes/excel/", ReporteExcelView.as_view(), name="report_excel"),
    path("reportes/excel/preview/", ReporteExcelPreviewHTMX.as_view(), name="report_excel_preview"),
    path("report/excel/table/", ReporteExcelTableHTMX.as_view(), name="report_excel_table"),
    path("reportes/excel/filters/", ReporteExcelFiltersHTMX.as_view(), name="report_excel_filters"),
]
