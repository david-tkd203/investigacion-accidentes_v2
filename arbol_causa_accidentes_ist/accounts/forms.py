# accounts/forms.py
import logging
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django import forms
from .models import normaliza_rut, valida_rut_chile
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm

logger = logging.getLogger("accounts.forms")
User = get_user_model()

class RutAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="RUT",
        widget=forms.TextInput(attrs={
            "placeholder": "12.345.678-5",
            "autocomplete": "username",
            "class": "form-input",
            "required": True,
        })
    )

    def clean_username(self):
        data = self.cleaned_data.get("username", "")
        rut = normaliza_rut(data)
        if not valida_rut_chile(rut):
            raise forms.ValidationError("RUT inválido. Usa formato 12.345.678-5.")
        return rut


class RutPasswordResetForm(PasswordResetForm):
    """
    Password reset por RUT: resuelve el usuario por RUT, y envía al email registrado.
    """
    rut = forms.CharField(
        label=_("RUT"),
        max_length=12,
        widget=forms.TextInput(attrs={
            "placeholder": "12.345.678-5",
            "autocomplete": "username",
            "class": "form-input",
            "required": True,
            "inputmode": "numeric",
            "pattern": r"^\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]$",
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El formulario base trae 'email'; lo removemos
        if "email" in self.fields:
            self.fields.pop("email")

    def clean_rut(self):
        data = (self.cleaned_data.get("rut") or "").strip()
        rut = normaliza_rut(data)
        if not valida_rut_chile(rut):
            raise forms.ValidationError(_("RUT inválido. Usa formato 12.345.678-5."))
        return rut

    def _get_users_by_rut(self, rut):
        qs = (
            User._default_manager.filter(rut__iexact=rut, is_active=True)
            .exclude(email__isnull=True)
            .exclude(email__exact="")
        )
        return qs.iterator()

    def save(
        self,
        domain_override=None,
        subject_template_name="registration/password_reset_subject_accounts.txt",
        email_template_name="registration/password_reset_email_accounts.html",
        use_https=False,
        token_generator=default_token_generator,
        from_email=None,
        request=None,
        html_email_template_name="registration/password_reset_email_accounts.html",
        extra_email_context=None,
    ):
        rut = self.cleaned_data["rut"]
        sent_count = 0

        try:
            users = list(self._get_users_by_rut(rut))
            logger.info("PasswordReset por RUT=%s → usuarios encontrados=%d", rut, len(users))

            if not users:
                return 0


            if request and not use_https:
                use_https = request.is_secure()

            for user in users:
                try:
                    if not domain_override:
                        current_site = get_current_site(request)
                        site_name = current_site.name
                        domain = current_site.domain
                    else:
                        site_name = domain_override
                        domain = domain_override

                    context = {
                        "email": user.email,
                        "domain": domain,
                        "site_name": site_name,
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        "token": token_generator.make_token(user),
                        "protocol": "https" if use_https else "http",
                        **(extra_email_context or {}),
                    }

                    logger.info(
                        "Enviando reset a user_id=%s email=%s domain=%s protocol=%s",
                        user.pk, user.email, domain, context["protocol"]
                    )


                    self.send_mail(
                        subject_template_name,
                        email_template_name,
                        context,
                        from_email,
                        user.email,
                        html_email_template_name=html_email_template_name,
                    )
                    sent_count += 1

                except Exception as e:
                    logger.exception(
                        "Excepción enviando reset a user_id=%s email=%s: %s",
                        getattr(user, "pk", None), getattr(user, "email", None), e
                    )

                    continue

            return sent_count

        except Exception as e:
            logger.exception("Excepción general en RutPasswordResetForm.save(): %s", e)
            return sent_count

class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields["old_password"].widget.attrs.update({"class": "form-input", "placeholder": "Contraseña actual"})
        self.fields["new_password1"].widget.attrs.update({"class": "form-input", "placeholder": "Nueva contraseña"})
        self.fields["new_password2"].widget.attrs.update({"class": "form-input", "placeholder": "Repite la nueva contraseña"})

    def save(self, commit=True):
        user = super().save(commit=False)
        if hasattr(user, "must_change_password") and user.must_change_password:
            user.must_change_password = False
        if commit:
            user.save()
        return user
        
class StyledSetPasswordForm(SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields["new_password1"].widget.attrs.update({"class": "form-input", "placeholder": "Nueva contraseña"})
        self.fields["new_password2"].widget.attrs.update({"class": "form-input", "placeholder": "Repite la nueva contraseña"})

    def save(self, commit=True):
        user = super().save(commit=False)
        if hasattr(user, "must_change_password") and user.must_change_password:
            user.must_change_password = False
        if commit:
            user.save()
        return user
