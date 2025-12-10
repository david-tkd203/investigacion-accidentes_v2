# accounts/views.py
from django.urls import reverse
from django.contrib.auth.views import LoginView
from .forms import RutAuthenticationForm
from accidentes.models import UserPrivacyConsent

LEY_CHOICES = ("21.459", "21.663", "21.719")
CONSENT_VERSION = "v1.0"

def _needs_privacy_consent(user) -> bool:
    if not user.is_authenticated:
        return False
    existentes = (
        UserPrivacyConsent.objects
        .filter(usuario=user, version=CONSENT_VERSION, ley_numero__in=LEY_CHOICES)
        .values_list("ley_numero", flat=True)
    )
    return bool(set(LEY_CHOICES) - set(existentes))

class RutLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = RutAuthenticationForm

    def get_success_url(self):
        user = self.request.user
        next_url = self.request.POST.get("next") or self.request.GET.get("next")

        if _needs_privacy_consent(user):
            if next_url:
                self.request.session["post_consent_next"] = next_url
            return reverse("accidentes:privacy_policies")

        # si no falta nada, ir al next o al LOGIN_REDIRECT_URL / success_url
        return next_url or super().get_success_url()
