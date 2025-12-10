from django import forms
from ..models import CentrosTrabajo

PLACEHOLDER = [("", "---------")]

class CentroTrabajoForm(forms.ModelForm):
    region = forms.ChoiceField(
        choices=[], required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    comuna = forms.ChoiceField(
        choices=[], required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    nombre_local = forms.ChoiceField(
        choices=[], required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = CentrosTrabajo
        fields = ["region", "comuna", "nombre_local", "direccion_centro"]
        widgets = {
            "direccion_centro": forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
        }

    def __init__(self, *args, empresa_id=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Valores de referencia: primero lo que viene en POST (self.data),
        # si no hay, usamos initial.
        def _get_val(name):
            v = ""
            if hasattr(self, "data") and self.data:
                v = (self.data.get(name) or "").strip()
            if not v:
                v = (self.initial.get(name) or "").strip()
            return v

        region_val = _get_val("region")
        comuna_val = _get_val("comuna")

        base_qs = CentrosTrabajo.objects.none()
        if empresa_id:
            base_qs = CentrosTrabajo.objects.filter(empresa_id=empresa_id)

        # Regiones para la empresa (siempre)
        regiones = (
            base_qs.values_list("region", flat=True)
            .distinct().order_by("region")
        )
        regiones = [r for r in regiones if r]
        self.fields["region"].choices = PLACEHOLDER + [(r, r) for r in regiones]

        # Comunas filtradas por región_val si viene; si no, vacías (HTMX las cargará)
        if region_val:
            comunas = (
                base_qs.filter(region=region_val)
                .values_list("comuna", flat=True)
                .distinct().order_by("comuna")
            )
            comunas = [c for c in comunas if c]
            self.fields["comuna"].choices = PLACEHOLDER + [(c, c) for c in comunas]
        else:
            self.fields["comuna"].choices = PLACEHOLDER

        # Nombres filtrados por region_val + comuna_val si vienen; si no, vacías
        if region_val and comuna_val:
            nombres = (
                base_qs.filter(region=region_val, comuna=comuna_val)
                .values_list("nombre_local", flat=True)
                .distinct().order_by("nombre_local")
            )
            nombres = [n for n in nombres if n]
            self.fields["nombre_local"].choices = PLACEHOLDER + [(n, n) for n in nombres]
        else:
            self.fields["nombre_local"].choices = PLACEHOLDER

        # (Opcional) setear .initial para que el template marque seleccionados
        if region_val:
            self.fields["region"].initial = region_val
        if comuna_val:
            self.fields["comuna"].initial = comuna_val
        if hasattr(self, "data") and self.data:
            nombre_val = (self.data.get("nombre_local") or "").strip()
        else:
            nombre_val = (self.initial.get("nombre_local") or "").strip()
        if nombre_val:
            self.fields["nombre_local"].initial = nombre_val