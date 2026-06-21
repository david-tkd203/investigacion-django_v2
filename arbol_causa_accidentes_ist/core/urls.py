# arbol_causa_accidentes_ist/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

from accidentes.views import InicioRapidoView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth centralizado en accounts/
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),

    # App de negocio
    path("accidentes", lambda request: redirect("accidentes:buscar")),
    path("accidentes/", include(("accidentes.urls", "accidentes"), namespace="accidentes")),

    # App del panel de administración
    path("adminpanel/", include("adminpanel.urls", namespace="adminpanel")),

    # Quick Start Wizard
    path("inicio/", InicioRapidoView.as_view(), name="inicio_rapido"),

    # Raíz → wizard
    path("", lambda request: redirect("inicio_rapido"), name="root"),
]
