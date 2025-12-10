# -*- coding: utf-8 -*-
from django.db import transaction
from accidentes.models import Holdings, Empresas, CentrosTrabajo

CENTROS_EBCO = [
    {"nombre_local": "Edificio Vista Colón",
     "direccion_centro": "Cristóbal Colón Nº 7.475, Las Condes",
     "region": "Región Metropolitana", "comuna": "Las Condes"},
    {"nombre_local": "Santuario Bellavista",
     "direccion_centro": "A. Walker Martínez 505, La Florida",
     "region": "Región Metropolitana", "comuna": "La Florida"},
]

@transaction.atomic
def run():
    holding, _ = Holdings.objects.get_or_create(nombre="EBCO")

    ebco, _ = Empresas.objects.update_or_create(
        holding=holding,
        empresa_sel="EBCO S.A.",
        defaults={
            "rut_empresa": "76525290-3",
            "actividad": "Construcción y reparación de edificios",
            "direccion_empresa": "Av. Santa María 2450",
            "telefono": "56224644700",
            "representante_legal": "Hernan Besomi Tomas",
            "region": "Región Metropolitana",
            "comuna": "Providencia",
        },
    )

    nombres_actuales = set()
    for row in CENTROS_EBCO:
        obj, _ = CentrosTrabajo.objects.update_or_create(
            empresa=ebco,
            nombre_local=row["nombre_local"],
            defaults={
                "direccion_centro": row["direccion_centro"],
                "region": row["region"],
                "comuna": row["comuna"],
            },
        )
        nombres_actuales.add(obj.nombre_local)

    # (Opcional) eliminar SOLO centros de EBCO que ya no estén en la lista:
    # CentrosTrabajo.objects.filter(empresa=ebco).exclude(nombre_local__in=nombres_actuales).delete()

    print(f"Holding OK: {holding.nombre}")
    print(f"Empresa OK: {ebco.empresa_sel} (id={ebco.pk})")
