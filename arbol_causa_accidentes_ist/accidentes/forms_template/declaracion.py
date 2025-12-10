from django import forms

class DeclaracionForm(forms.Form):
    """
    Form for collecting structured user statements (used in AI interview assistant).
    """
    tipo = forms.ChoiceField(
        label="Tipo de declaración",
        choices=[
            ("accidentado", "Accidentado"),
            ("testigos", "Testigos"),
            ("supervisores", "Supervisores")
        ]
    )
    pregunta = forms.CharField(label="Pregunta", max_length=300)
    respuesta = forms.CharField(label="Respuesta", widget=forms.Textarea)
