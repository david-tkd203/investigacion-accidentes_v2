# accounts/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import normaliza_rut, valida_rut_chile

class RutOnlyBackend(ModelBackend):
    """
    Autentica únicamente por RUT normalizado y válido.
    No permite username/email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if not username or not password:
            return None

        rut = normaliza_rut(username)
        if not valida_rut_chile(rut):
            return None

        try:
            user = User._default_manager.get(rut=rut)
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
