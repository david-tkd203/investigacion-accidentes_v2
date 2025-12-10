# arbol_causa_accidentes_ist/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth centralizado en accounts/
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),

    # App de negocio
    path("accidentes", lambda request: redirect("accidentes:buscar")),
    path("accidentes/", include(("accidentes.urls", "accidentes"), namespace="accidentes")),

    # App del panel de administración
    path("adminpanel/", include("adminpanel.urls", namespace="adminpanel")),

    # Raíz → login
    path("", lambda request: redirect("accounts:login"), name="root"),
]
