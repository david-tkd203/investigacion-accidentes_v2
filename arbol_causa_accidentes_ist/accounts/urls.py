# accounts/urls.py
from django.urls import path
from .views import RutLoginView
from django.contrib.auth import views as auth_views
from .forms import (
    RutPasswordResetForm,
    StyledSetPasswordForm,
    StyledPasswordChangeForm,
)
from django.urls import reverse_lazy

app_name = "accounts"

urlpatterns = [
    # Login / Logout
    path(
        "login/",
        RutLoginView.as_view(
            template_name="registration/login.html",
            redirect_authenticated_user=True
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # --- Cambio de contraseña (usuario logueado) ---
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            form_class=StyledPasswordChangeForm,
            template_name="registration/password_change_form.html",
            success_url=reverse_lazy("accounts:password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="registration/password_change_done.html",
        ),
        name="password_change_done",
    ),

    # --- Reset por token (flujo por email) ---
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            form_class=RutPasswordResetForm,
            template_name="registration/recuperar_pass.html",
            email_template_name="registration/password_reset_email_accounts.html",
            html_email_template_name="registration/password_reset_email_accounts.html",
            subject_template_name="registration/password_reset_subject.txt",  # si tienes una versión *_accounts.txt cámbiala aquí
            success_url=reverse_lazy("accounts:password_reset_done_accounts"),
            extra_email_context={
                "protocol": "http",    # TODO: fuerza http en dev
                "domain": "20.106.186.24",
            },
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done_accounts.html"
        ),
        name="password_reset_done_accounts",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm_accounts.html",
            form_class=StyledSetPasswordForm,
            success_url=reverse_lazy("accounts:password_reset_complete_accounts"),
        ),
        name="password_reset_confirm_accounts",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete_accounts.html"
        ),
        name="password_reset_complete_accounts",
    ),
]
