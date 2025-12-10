# accidentes/forms.py
from django import forms
from ..models import Accidentes  # ajusta el import si tu estructura difiere

from django.utils import timezone
from datetime import date


class AccidenteForm(forms.ModelForm):
    # Campo "dummy" solo para que existan errores dirigidos a 'usuario_asignado'
    usuario_asignado = forms.IntegerField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Accidentes
        # 👇 NO incluimos 'usuario_asignado' aquí (no se modificará desde este form).
        fields = [
            "fecha_accidente", "hora_accidente", "lugar_accidente",
            "tipo_accidente", "naturaleza_lesion", "parte_afectada",
            "tarea", "operacion",
            "danos_personas", "danos_propiedad", "perdidas_proceso",
            "contexto", "circunstancias",
        ]
        widgets = {
            "fecha_accidente": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "hora_accidente":  forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "lugar_accidente": forms.TextInput(attrs={"class": "form-control"}),
            "tipo_accidente":  forms.Select(attrs={"class": "form-control"}),
            "naturaleza_lesion": forms.TextInput(attrs={"class": "form-control"}),
            "parte_afectada":    forms.TextInput(attrs={"class": "form-control"}),
            "tarea":             forms.TextInput(attrs={"class": "form-control"}),
            "operacion":         forms.TextInput(attrs={"class": "form-control"}),
            "danos_personas":    forms.RadioSelect(),
            "danos_propiedad":   forms.RadioSelect(),
            "perdidas_proceso":  forms.RadioSelect(),
            "contexto":          forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "circunstancias":    forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        actor = kwargs.pop("actor", None)
        super().__init__(*args, **kwargs)

        if self.instance is not None:
            setattr(self.instance, "_actor", actor)
            setattr(self.instance, "_original_usuario_asignado",
                    getattr(self.instance, "usuario_asignado_id", None))

        # Inicialización amigable para fecha
        if self.instance and self.instance.fecha_accidente:
            self.initial["fecha_accidente"] = self.instance.fecha_accidente.isoformat()

        # Marcamos requeridos visualmente
        for field in self.fields.values():
            if field.required:
                field.widget.attrs["required"] = "required"

        # Placeholder de select
        if "tipo_accidente" in self.fields:
            self.fields["tipo_accidente"].empty_label = "Seleccione una opción"

        # Clases para radios y sin opción vacía
        for name in ("danos_personas", "danos_propiedad", "perdidas_proceso"):
            if name in self.fields:
                self.fields[name].widget.attrs.update({"class": "form-check-input"})
                self.fields[name].choices = [
                    (k, v) for (k, v) in self.fields[name].choices if k not in ("", None)
                ]

        # ✅ Muy importante: setear el hidden con el usuario asignado actual
        if self.instance and getattr(self.instance, "usuario_asignado_id", None):
            self.fields["usuario_asignado"].initial = self.instance.usuario_asignado_id
        try:
            today = timezone.localdate()  # respeta TIME_ZONE
        except Exception:
            today = date.today()
        if "fecha_accidente" in self.fields:
            self.fields["fecha_accidente"].widget.attrs["max"] = today.isoformat()

        if self.instance and getattr(self.instance, "usuario_asignado_id", None):
            self.fields["usuario_asignado"].initial = self.instance.usuario_asignado_id
    
    def clean_fecha_accidente(self):
        f = self.cleaned_data.get("fecha_accidente")
        try:
            today = timezone.localdate()
        except Exception:
            today = date.today()
        if f and f > today:
            raise forms.ValidationError("La fecha del accidente no puede ser posterior a hoy.")
        return f