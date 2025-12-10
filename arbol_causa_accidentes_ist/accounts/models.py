# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
import re

def normaliza_rut(rut: str) -> str:
    if rut is None:
        return rut
    rut = rut.replace(".", "").replace("-", "").strip().upper()
    return rut[:-1] + "-" + rut[-1] if len(rut) > 1 else rut

def valida_rut_chile(rut: str) -> bool:
    # Valida DV (módulo 11). Acepta K.
    rut = normaliza_rut(rut)
    if not rut or "-" not in rut:
        return False
    num, dv = rut.split("-")
    if not num.isdigit() or not re.match(r"^[0-9K]$", dv):
        return False
    suma, factor = 0, 2
    for d in reversed(num):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    dv_calc = "0" if resto == 11 else "K" if resto == 10 else str(resto)
    return dv == dv_calc

class User(AbstractUser):
    TEAM_CHOICES = [
        ("staff", "Staff IST"),
        ("adherente", "Adherente"),
    ]
    ROL_CHOICES = [
        ("admin", "Admin Global"),
        ("admin_ist", "Admin IST"),
        ("admin_holding", "Admin Holding"),
        ("admin_empresa", "Admin Empresa"),
        ("coordinador", "Coordinador"),
        ("investigador", "Investigador"),
        ("investigador_ist", "Investigador IST"),  # <-- añade esto
    ]


    # Opcional: email único (manteniendo username como identificador)
    email = models.EmailField("email address", unique=True, blank=True)

    team = models.CharField(max_length=10, choices=TEAM_CHOICES, default="adherente")
    rol  = models.CharField(max_length=35, choices=ROL_CHOICES, default="investigador")

    empresa = models.ForeignKey(
        "accidentes.Empresas",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="auth_users",          
        related_query_name="auth_user",     
    )
    holding = models.ForeignKey(
        "accidentes.Holdings",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="auth_users",          
        related_query_name="auth_user",
    )

    rut    = models.CharField(max_length=12, unique=True, null=True, blank=True,
                              help_text="Formato 12.345.678-5 o 12345678-5")
    nombre = models.CharField(max_length=100, null=True, blank=True)
    apepat = models.CharField(max_length=100, null=True, blank=True)
    apemat = models.CharField(max_length=100, null=True, blank=True)
    cargo  = models.CharField(max_length=100, null=True, blank=True)
    must_change_password = models.BooleanField(default=False)

    class Meta:
        db_table = "users"  # opcional; si lo quitas será 'accounts_user' por defecto
        indexes = [models.Index(fields=["team", "rol"])]

    def clean(self):
        super().clean()
        if self.rut:
            r = normaliza_rut(self.rut)
            if not valida_rut_chile(r):
                raise ValidationError({"rut": "RUT inválido."})
            self.rut = r

