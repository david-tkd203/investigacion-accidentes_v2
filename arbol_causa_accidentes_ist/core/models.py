"""
Modelos para Multi-Tenancy usando django-tenants
"""
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Empresa(TenantMixin):
    """
    Modelo de Tenant - Representa una empresa o holding
    Cada empresa tendrá su propio esquema en PostgreSQL
    """
    name = models.CharField(max_length=100, verbose_name="Nombre de la Empresa")
    rut = models.CharField(max_length=20, unique=True, verbose_name="RUT")
    created_on = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    # Campos adicionales
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to='tenants/logos/', blank=True, null=True)
    
    # django-tenants utilizará automáticamente el campo schema_name
    # heredado de TenantMixin
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        db_table = "empresas"
    
    def __str__(self):
        return self.name


class Domain(DomainMixin):
    """
    Modelo de Dominio - Relaciona dominios con empresas
    """
    pass
