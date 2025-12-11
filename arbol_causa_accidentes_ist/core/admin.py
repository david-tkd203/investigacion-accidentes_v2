"""
Admin para modelos de Multi-Tenancy
"""
from django.contrib import admin
from core.models import Empresa, Domain


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['name', 'rut', 'schema_name', 'is_active', 'created_on']
    list_filter = ['is_active', 'created_on']
    search_fields = ['name', 'rut', 'schema_name']
    readonly_fields = ['created_on', 'schema_name']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'rut', 'schema_name', 'is_active')
        }),
        ('Información de Contacto', {
            'fields': ('direccion', 'telefono', 'email', 'logo')
        }),
        ('Metadatos', {
            'fields': ('created_on',)
        }),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['domain', 'tenant__name']
