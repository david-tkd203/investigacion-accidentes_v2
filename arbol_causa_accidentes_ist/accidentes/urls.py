# accidentes/urls.py
from django.urls import path
from . import views

# Importa SOLO las class-based views desde .views
from .views import (
    BuscarAccidenteView,
    CargarAccidenteView,
    DatosEmpresaView,
    DatosTrabajadorView,
    DatosAccidenteView,
    home_view,
    home_assigned_cases_partial,
    privacy_policies,
    privacy_policies_accept
)

from .views_ia import (
    DeclaracionesIAView,
    RelatoIAView,
    HechosIAView,
    ArbolIAView,
    FotosDocumentosView,
    MedidasCorrectivasView,
    GenerarArbolIACreateView,
    GenerarInformeIAView,
)

app_name = "accidentes"

urlpatterns = [
    path("home/", home_view, name="home"),
    path("home/assigned/", home_assigned_cases_partial, name="home-assigned-partial"),
    path("buscar/",     BuscarAccidenteView.as_view(),   name="buscar"),
    path("cargar/",     CargarAccidenteView.as_view(),   name="cargar_accidente"),

    path("empresa/<str:codigo>/",    DatosEmpresaView.as_view(),      name="empresa"),
    path("trabajador/<str:codigo>/", DatosTrabajadorView.as_view(),   name="trabajador"),
    path("accidente/<str:codigo>/",  DatosAccidenteView.as_view(),    name="accidente"),

    path("asistente/declaraciones/<str:codigo>/", DeclaracionesIAView.as_view(), name="ia_declaraciones"),
    path("asistente/relato/<str:codigo>/",        RelatoIAView.as_view(),        name="ia_relato"),
    path("asistente/hechos/<str:codigo>/",        HechosIAView.as_view(),        name="ia_hechos"),
    path("asistente/arbol/<str:codigo>/",         ArbolIAView.as_view(),         name="ia_arbol"),
    path("asistente/documentos/<str:codigo>/",    FotosDocumentosView.as_view(), name="ia_fotos"),
    path("asistente/medidas/<str:codigo>/",       MedidasCorrectivasView.as_view(), name="ia_medidas"),
    path("asistente/arbol/generar/<str:codigo>/", GenerarArbolIACreateView.as_view(), name="generar_arbol"),

    # Probablemente es necesario elimminar estos endpoint ajax
    path("ajax/cargar-comunas/", views.cargar_comunas, name="cargar_comunas"),
    path("ajax/cargar-centros/", views.cargar_centros, name="cargar_centros"),
    path("ajax/cargar-direccion-centro/", views.cargar_direccion, name="cargar_direccion"),
    path("ajax/obtener-centro-id/", views.obtener_centro_id, name="obtener_centro_id"),

    path("htmx/<str:codigo>/cargar-comunas-y-centros/", views.cargar_comunas_y_centros, name="cargar_comunas_y_centros"),
    path("htmx/<str:codigo>/cargar-centros-y-direccion/", views.cargar_centros_y_direccion, name="cargar_centros_y_direccion"),
    path("htmx/<str:codigo>/cargar-direccion-y-id/", views.cargar_direccion_y_id, name="cargar_direccion_y_id"),

    path("informe/generar/<str:codigo>/", GenerarInformeIAView.as_view(), name="generar_informe"),
    path("descargar/documento/<str:doc_id>/", views.descargar_documento, name="descargar_documento"),
    path("compliance/policies/", privacy_policies, name="privacy_policies"),
    path("compliance/policies/accept/", privacy_policies_accept, name="privacy_policies_accept"),
]
