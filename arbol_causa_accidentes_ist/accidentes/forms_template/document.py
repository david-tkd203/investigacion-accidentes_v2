from django import forms

class DocumentForm(forms.Form):
    archivo = forms.FileField(label="Selecciona un archivo")
    etiqueta = forms.CharField(label="Etiqueta", max_length=100)
