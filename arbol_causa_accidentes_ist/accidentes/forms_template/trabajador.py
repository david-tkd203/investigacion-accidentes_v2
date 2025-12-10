from django import forms
from ..models import Trabajadores
import datetime

class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajadores
        exclude = ['trabajador_id', 'empresa', 'created_at']
        widgets = {
            # Fecha con validación de edad (18-90 años)
            'fecha_nacimiento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': (datetime.date.today() - datetime.timedelta(days=90*365.25)).strftime('%Y-%m-%d'),
                'max': (datetime.date.today() - datetime.timedelta(days=18*365.25)).strftime('%Y-%m-%d')
            }),

            # Selects (Bootstrap 5 → form-select)
            'estado_civil':     forms.Select(attrs={'class': 'form-select'}),
            'contrato':         forms.Select(attrs={'class': 'form-select'}),
            'nacionalidad':     forms.Select(attrs={'class': 'form-select'}),
            'genero':           forms.Select(attrs={'class': 'form-select'}),

            # Textos
            'domicilio':        forms.TextInput(attrs={'class': 'form-control'}),
            'cargo_trabajador': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_trabajador': forms.TextInput(attrs={'class': 'form-control'}),
            'rut_trabajador':    forms.TextInput(attrs={'class': 'form-control'}),

            # Compatibilidad (si estos CharField existen en el modelo)
            'antiguedad_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'antiguedad_cargo':   forms.TextInput(attrs={'class': 'form-control'}),

            # Numéricos (si existen en el modelo con estos nombres)
            'antiguedad_empresa_anios': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Años'}),
            'antiguedad_empresa_meses': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Meses (0–11)', 'min': 0, 'max': 11}),
            'antiguedad_cargo_anios':   forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Años'}),
            'antiguedad_cargo_meses':   forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Meses (0–11)', 'min': 0, 'max': 11}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Pre-cargar fecha en formato ISO para <input type="date">
        if self.instance and self.instance.fecha_nacimiento:
            self.initial['fecha_nacimiento'] = self.instance.fecha_nacimiento.isoformat()

        # Opción vacía por defecto en selects (si el field lo soporta)
        for name in ('estado_civil', 'nacionalidad', 'contrato', 'genero'):
            if name in self.fields and hasattr(self.fields[name], "empty_label"):
                self.fields[name].empty_label = "Seleccione una opción"

    # -------- Validaciones --------
    def clean_fecha_nacimiento(self):
        fn = self.cleaned_data.get("fecha_nacimiento")
        if fn:
            today = datetime.date.today()
            edad = today.year - fn.year - ((today.month, today.day) < (fn.month, fn.day))
            if edad < 18:
                raise forms.ValidationError("El trabajador debe tener al menos 18 años.")
            if edad > 90:
                raise forms.ValidationError("El trabajador no puede tener más de 90 años.")
        return fn

    def clean_antiguedad_empresa_meses(self):
        m = self.cleaned_data.get("antiguedad_empresa_meses")
        if m is None:
            return m
        if not (0 <= m <= 11):
            raise forms.ValidationError("Meses debe estar entre 0 y 11.")
        return m

    def clean_antiguedad_cargo_meses(self):
        m = self.cleaned_data.get("antiguedad_cargo_meses")
        if m is None:
            return m
        if not (0 <= m <= 11):
            raise forms.ValidationError("Meses debe estar entre 0 y 11.")
        return m


    def clean(self):
        """
        - Revalida rangos de meses.
        - Si mantienes los CharField 'antiguedad_empresa' y 'antiguedad_cargo' en el modelo,
          compone sus valores desde los numéricos para conservar compatibilidad.
        """
        cleaned = super().clean()

        ae_y = cleaned.get("antiguedad_empresa_anios")
        ae_m = cleaned.get("antiguedad_empresa_meses")
        ac_y = cleaned.get("antiguedad_cargo_anios")
        ac_m = cleaned.get("antiguedad_cargo_meses")

        if ae_m is not None and not (0 <= ae_m <= 11):
            self.add_error("antiguedad_empresa_meses", "Meses debe estar entre 0 y 11.")
        if ac_m is not None and not (0 <= ac_m <= 11):
            self.add_error("antiguedad_cargo_meses", "Meses debe estar entre 0 y 11.")

        # Solo compone si esos fields existen en el form/modelo (compatibilidad)
        if "antiguedad_empresa" in self.fields and ae_y is not None and ae_m is not None:
            cleaned["antiguedad_empresa"] = f"{ae_y} años {ae_m} meses"
        if "antiguedad_cargo" in self.fields and ac_y is not None and ac_m is not None:
            cleaned["antiguedad_cargo"] = f"{ac_y} años {ac_m} meses"

        return cleaned
