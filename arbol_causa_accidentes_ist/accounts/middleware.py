# accounts/middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and getattr(user, "must_change_password", False):
            rm = getattr(request, "resolver_match", None)
            current_name = rm.url_name if rm else None

            allowed = {
                # Cambio de contraseña (logueado) y resultado
                "password_change", "password_change_done",
                # Flujo de reset por token (por si entra por el link del correo)
                "password_reset", "password_reset_done",
                "password_reset_confirm", "password_reset_complete",
                # Permitir salir
                "logout", "admin:logout",
            }

            # Evita loop; si no está en las rutas permitidas, manda a cambiarla
            if current_name not in allowed:
                return redirect(reverse("accounts:password_change"))
        return self.get_response(request)
