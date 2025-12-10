from django import forms

class BuscarAccidenteForm(forms.Form):
    """
    Form to search for an accident by its unique code.
    """
    codigo = forms.CharField(
        label="Código del accidente",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: ACC-2025-001',
            'class': 'form-control'
        })
    )
