from django import forms
from ..models import Empresas

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresas
        fields = [
            'holding', 'empresa_sel', 'rut_empresa', 'actividad',
            'direccion_empresa', 'telefono', 'representante_legal',
        ]
        widgets = {
            'holding': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            'empresa_sel': forms.Select(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            'rut_empresa': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            'direccion_empresa': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            'representante_legal': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            'actividad': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
        }