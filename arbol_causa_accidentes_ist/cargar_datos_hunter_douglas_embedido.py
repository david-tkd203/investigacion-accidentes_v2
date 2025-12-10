# -*- coding: utf-8 -*-
from django.db import transaction
from accidentes.models import Holdings, Empresas, CentrosTrabajo

CENTROS_HUNTER = [
    {"nombre_local": "CASA MATRIZ",
     "direccion_centro": "Portales Oriente  1757",
     "region": "Región Metropolitana",
     "comuna": "San Bernardo"}
]

@transaction.atomic
def run():
    holding, _ = Holdings.objects.get_or_create(nombre="HUNTER DOUGLAS CHILE")

    hunter_douglas, _ = Empresas.objects.update_or_create(
        holding=holding,
        empresa_sel="HUNTER DOUGLAS CHILE S.A",
        defaults={
             "rut_empresa": "92654000-9 ",
            "actividad": "Fabricación de productos metálicos para uso estructural",
            "direccion_empresa": "Portales Oriente  1757",
            "telefono": "988199612",
            "representante_legal": "Francisco José Uturria",
            "region": "Región Metropolitana",
            "comuna": "San Bernardo",
        },
    )

    nombres_actuales = set()
    for row in CENTROS_HUNTER:
        obj, _ = CentrosTrabajo.objects.update_or_create(
            empresa=hunter_douglas,
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
    print(f"Empresa OK: {hunter_douglas.empresa_sel} (id={hunter_douglas.pk})")
