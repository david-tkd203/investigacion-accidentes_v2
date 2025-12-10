# adminpanel/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as ModelValidationError

from accidentes.models import Accidentes, Trabajadores, Empresas, Holdings
from accidentes.access import (
    holdings_permitidos,
    empresas_permitidas,
    usuarios_permitidos_para_asignar,
    trabajadores_permitidos,
    SUPER_ROLES,
)

User = get_user_model()


class AccidenteCrearForm(forms.ModelForm):
    trabajador_id = forms.CharField(widget=forms.HiddenInput, required=True)

    holding = forms.ModelChoiceField(queryset=Holdings.objects.none(), required=False)
    empresa = forms.ModelChoiceField(queryset=Empresas.objects.none(), required=False)
    usuario_asignado = forms.ModelChoiceField(queryset=User.objects.none(), required=True)
    fecha_accidente = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=True)

    class Meta:
        model = Accidentes
        fields = ("holding", "empresa", "fecha_accidente", "usuario_asignado")

    def _update_errors(self, e):
        if isinstance(e, ModelValidationError) and hasattr(e, "error_dict"):
            if "trabajador" in e.error_dict:
                e.error_dict["trabajador_id"] = e.error_dict.pop("trabajador")
        return super()._update_errors(e)

    def __init__(self, *args, user=None, actor=None, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        # guarda contexto
        self.user = user or actor
        self.actor = actor or user
        self.request = request
        # detecta acción
        self._action_asignarme = False
        if self.request and getattr(self.request, "method", "").upper() == "POST":
            self._action_asignarme = (self.request.POST.get("action") == "asignarme")
        # fallback por si entra como self.data (tests, etc.)
        if not self._action_asignarme:
            self._action_asignarme = (self.data.get("action") == "asignarme")

        # Si el modelo se instancia, propaga actor para validaciones del modelo
        if self.instance is not None:
            self.instance._actor = self.actor
            self.instance._original_usuario_asignado = getattr(self.instance, "usuario_asignado_id", None)

        rol = getattr(self.user, "rol", None)

        # ---- Holding según rol
        qs_hold = holdings_permitidos(self.user)
        holding_val = (self.data.get("holding") or self.initial.get("holding") or None)
        try:
            holding_val = int(holding_val) if holding_val else None
        except ValueError:
            holding_val = None

        if rol in SUPER_ROLES:
            self.fields["holding"].queryset = qs_hold
            self.fields["holding"].required = True
        elif rol in {"admin_holding", "admin_empresa"}:
            self.fields["holding"].queryset = qs_hold
            self.fields["holding"].widget = forms.HiddenInput()
            if qs_hold.exists():
                self.initial["holding"] = qs_hold.first().pk
                holding_val = holding_val or qs_hold.first().pk

        # --- Empresa encadenada a holding y rol
        qs_emp = empresas_permitidas(self.user, holding_id=holding_val)

        if rol in SUPER_ROLES or rol == "admin_holding":
            self.fields["empresa"].required = True
            self.fields["empresa"].widget.attrs.setdefault("class", "form-select")
            if holding_val:
                self.fields["empresa"].queryset = qs_emp
                self.fields["empresa"].widget.attrs.pop("disabled", None)
            else:
                self.fields["empresa"].queryset = Empresas.objects.none()
                self.fields["empresa"].widget.attrs["disabled"] = "disabled"
        else:
            self.fields["empresa"].queryset = qs_emp
            self.fields["empresa"].widget = forms.HiddenInput()
            if qs_emp.exists():
                self.initial["empresa"] = qs_emp.first().pk

        # ---- Usuario asignado: acotar por empresa
        empresa_val = (
            self.data.get("empresa")
            or self.initial.get("empresa")
            or getattr(self.instance, "empresa_id", None)
        ) or self.data.get("id_empresa_hidden")

        try:
            empresa_val = int(empresa_val) if empresa_val else None
        except ValueError:
            empresa_val = None

        self.fields["usuario_asignado"].queryset = usuarios_permitidos_para_asignar(
            self.user,
            empresa_id=empresa_val,
            force_empresa_for_creation=True,
        )
        self.fields["usuario_asignado"].widget = forms.HiddenInput()

        if self._action_asignarme:
            self.fields["usuario_asignado"].required = False

    def clean_usuario_asignado(self):
        # Si viene por “Asígname”, devuelve SIEMPRE el actor (y deja que el modelo valide reglas finas)
        if self._action_asignarme:
            return self.actor

        usuario = self.cleaned_data.get("usuario_asignado")
        if not usuario:
            raise forms.ValidationError("Debes seleccionar un investigador.")

        empresa = self.cleaned_data.get("empresa")
        allowed = usuarios_permitidos_para_asignar(
            self.user,
            empresa_id=getattr(empresa, "pk", None),
            force_empresa_for_creation=True,
        )

        # Si el usuario está permitido, OK
        if allowed.filter(pk=getattr(usuario, "pk", None)).exists():
            return usuario

        # Permite auto-asignación para roles “globales”
        if usuario.pk == getattr(self.user, "pk", None) and getattr(self.user, "rol", None) in ("admin", "admin_ist", "admin_holding"):
            return usuario

        raise forms.ValidationError("Usuario fuera de tu alcance para esta empresa.")

    def clean_trabajador_id(self):
        val = (self.cleaned_data.get("trabajador_id") or "").strip()
        if not val:
            raise forms.ValidationError("Debes seleccionar o crear un trabajador.")
        try:
            t = Trabajadores.objects.select_related("empresa").get(pk=val)
        except Trabajadores.DoesNotExist:
            raise forms.ValidationError("El trabajador seleccionado no existe.")

        if not trabajadores_permitidos(self.user, empresa_id=t.empresa_id).filter(pk=t.pk).exists():
            raise forms.ValidationError("El trabajador seleccionado está fuera de tu alcance.")
        return val

    def clean(self):
        cleaned = super().clean()
        rol = getattr(self.user, "rol", None)

        holding = cleaned.get("holding")
        empresa = cleaned.get("empresa")

        if rol in SUPER_ROLES:
            if not holding:
                self.add_error("holding", "Debes seleccionar un holding.")
            if not empresa:
                self.add_error("empresa", "Debes seleccionar una empresa.")
        elif rol == "admin_holding":
            if not empresa:
                self.add_error("empresa", "Debes seleccionar una empresa.")

        if empresa:
            qs_emp_ok = empresas_permitidas(self.user, holding_id=getattr(holding, "pk", None))
            if not qs_emp_ok.filter(pk=empresa.pk).exists():
                self.add_error("empresa", "Empresa fuera de tu alcance.")

        # Propaga campos al instance
        self.instance.creado_por = self.user
        if holding:
            self.instance.holding = holding
        elif empresa and getattr(empresa, "holding_id", None) and not getattr(self.instance, "holding_id", None):
            self.instance.holding_id = empresa.holding_id
        if empresa:
            self.instance.empresa = empresa

        # Trabajador
        trabajador_pk = cleaned.get("trabajador_id")
        if trabajador_pk:
            t = Trabajadores.objects.filter(pk=trabajador_pk).select_related("empresa").first()
            if t:
                if empresa and t.empresa_id and t.empresa_id != empresa.pk:
                    self.add_error("trabajador_id", "El trabajador no pertenece a la empresa seleccionada.")
                else:
                    self.instance.trabajador = t

        # Asignado (si no es “asignarme”, revalida alcance)
        asignado = cleaned.get("usuario_asignado")
        if asignado and not self._action_asignarme:
            allowed_users = usuarios_permitidos_para_asignar(
                self.user,
                empresa_id=getattr(empresa, "pk", None),
                force_empresa_for_creation=True,
            )
            if not allowed_users.filter(pk=getattr(asignado, "pk", None)).exists():
                self.add_error("usuario_asignado", "Usuario fuera de tu alcance para esta empresa.")
            else:
                self.instance.usuario_asignado = asignado
        else:
            # “asignarme”: fija el actor
            if self._action_asignarme:
                self.instance.usuario_asignado = self.actor

        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.creado_por = self.user
        if not obj.trabajador_id and self.cleaned_data.get("trabajador_id"):
            obj.trabajador_id = self.cleaned_data["trabajador_id"]
        if obj.empresa_id and not obj.holding_id:
            obj.holding_id = obj.empresa.holding_id
        if commit:
            obj.save()
        return obj


class TrabajadorCrearForm(forms.ModelForm):
    class Meta:
        model = Trabajadores
        fields = ("nombre_trabajador", "rut_trabajador", "empresa")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.holding_id = kwargs.pop("holding_id", None)
        super().__init__(*args, **kwargs)

        self.fields["rut_trabajador"].widget.attrs.update({"class": "form-control"})
        self.fields["nombre_trabajador"].widget.attrs.update({"class": "form-control"})
        self.fields["empresa"].widget.attrs.update({"class": "form-select"})

        role = getattr(self.user, "rol", None)

        try:
            hid = int(self.holding_id) if self.holding_id is not None else None
        except (TypeError, ValueError):
            hid = None

        qs_emp = empresas_permitidas(self.user, holding_id=hid)

        if role in SUPER_ROLES or role == "admin_holding":
            self.fields["empresa"].queryset = qs_emp
            self.fields["empresa"].required = True
            initial_emp = self.initial.get("empresa")
            if initial_emp and not qs_emp.filter(pk=initial_emp).exists():
                self.initial["empresa"] = None
        else:
            self.fields["empresa"].queryset = qs_emp
            self.fields["empresa"].widget = forms.HiddenInput()
            if qs_emp.exists():
                self.initial["empresa"] = qs_emp.first().pk

    def _normalize_rut(self, rut: str) -> str:
        return (rut or "").replace(".", "").strip().upper()

    def clean(self):
        cleaned = super().clean()
        role = getattr(self.user, "rol", None)
        empresa = cleaned.get("empresa")
        rut = self._normalize_rut(cleaned.get("rut_trabajador"))

        if rut:
            cleaned["rut_trabajador"] = rut

        if empresa:
            qs_emp_ok = empresas_permitidas(self.user, holding_id=getattr(empresa, "holding_id", None))
            if not qs_emp_ok.filter(pk=empresa.pk).exists():
                self.add_error("empresa", "Empresa fuera de tu alcance.")
        else:
            if role in SUPER_ROLES or role == "admin_holding":
                self.add_error("empresa", "Debes seleccionar una empresa.")
            else:
                qs_emp = empresas_permitidas(self.user)
                if qs_emp.exists():
                    cleaned["empresa"] = qs_emp.first()
                else:
                    self.add_error("empresa", "No tienes una empresa asignada.")

        if rut:
            existe_qs = Trabajadores.objects.filter(rut_trabajador__iexact=rut)
            emp = cleaned.get("empresa")
            if emp and existe_qs.filter(empresa=emp).exists():
                self.add_error("rut_trabajador", "Ya existe un trabajador con este RUT en la empresa seleccionada.")
            elif existe_qs.exclude(empresa=emp).exists():
                self.add_error("rut_trabajador", "Ya existe un trabajador con ese RUT.")

        return cleaned
