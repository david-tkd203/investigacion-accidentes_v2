# -*- coding: utf-8 -*-
from django.db import transaction
from accidentes.models import Holdings, Empresas, CentrosTrabajo

CENTROS_ULTRAPORT = [
    {"nombre_local": "ARI",
     "direccion_centro": "18 DE SEPTIEMBRE 112, ARICA",
     "region": "Región de Arica y Parinacota", "comuna": "Arica"},
    {"nombre_local": "CEN",
     "direccion_centro": "RUTA 1 KILÓMETRO 105, MUELLE MINERA CENTINELA, ANTOFAGASTA",
     "region": "Región de Antofagasta", "comuna": "Antofagasta"},
    {"nombre_local": "TGN",
     "direccion_centro": "CALLE PUERTO 1 N° 7100, BARRIO INDUSTRIAL, MEJILLONES",
     "region": "Región de Antofagasta", "comuna": "Mejillones"},
    {"nombre_local": "MEJ",
     "direccion_centro": "AVDA. COSTANERA NORTE 2800, MEJILLONES",
     "region": "Región de Antofagasta", "comuna": "Mejillones"},
    {"nombre_local": "ANG",
     "direccion_centro": "AV. LONGITUDINAL 5500, MEJILLONES",
     "region": "Región de Antofagasta", "comuna": "Mejillones"},
    {"nombre_local": "COQ",
     "direccion_centro": "AV. COSTANERA 600, PISO 1, COQUIMBO",
     "region": "Región de Coquimbo", "comuna": "Coquimbo"},
    {"nombre_local": "VAP",
     "direccion_centro": "BLANCO 853, PRIMER PISO, VALPARAÍSO",
     "region": "Región de Valparaíso", "comuna": "Valparaíso"},
    {"nombre_local": "UCO",
     "direccion_centro": "EMPORCHA -1- INT. REC. PORTUARIOS, PUERTO AYSÉN",
     "region": "Región de Aysén", "comuna": "Aysén"},
    {"nombre_local": "PUQ",
     "direccion_centro": "BOLIVIANA 751, PUNTA ARENAS",
     "region": "Región de Magallanes y de la Antártica Chilena", "comuna": "Punta Arenas"},
    {"nombre_local": "ADN",
     "direccion_centro": "ERRÁZURIZ 854, SEGUNDO PISO, VALPARAÍSO",
     "region": "Región de Valparaíso", "comuna": "Valparaíso"},
    {"nombre_local": "IQQ",
     "direccion_centro": "Terminal Marítimo Teck Quebrada Blanca S.A., IQUIQUE",
     "region": "Región de Tarapacá", "comuna": "Iquique"},
]

@transaction.atomic
def run():
    holding, _ = Holdings.objects.get_or_create(nombre="Ultramar")

    ultramar, _ = Empresas.objects.update_or_create(
        holding=holding,
        empresa_sel="Servicios Maritimos Y Transportes Ltda",
        defaults={
            "rut_empresa": "88056400-5",
            "actividad": "Manipulación de la carga. Agentes de estibas y desestibas.",
            "direccion_empresa": "Errázuriz 854, Valparaiso",
            "telefono": "56322202975",
            "representante_legal": "Gabriel Tumani",
            "region": "Región de Valparaíso",
            "comuna": "Valparaíso",
        },
    )

    nombres_actuales = set()
    for row in CENTROS_ULTRAPORT:
        obj, _ = CentrosTrabajo.objects.update_or_create(
            empresa=ultramar,
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
    print(f"Empresa OK: {ultramar.empresa_sel} (id={ultramar.pk})")
