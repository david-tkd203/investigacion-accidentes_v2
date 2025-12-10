# cargar_datos_completo.py

from django.db import transaction
from django.contrib.auth import get_user_model
from accidentes.models import (
    Holdings, Empresas, CentrosTrabajo, Trabajadores,
    Accidentes, ArbolCausas, Declaraciones, Documentos,
    Hechos, Informes, PreguntasGuia, Prescripciones, AccidenteJsonData
)
from datetime import time, date
import uuid

User = get_user_model()

@transaction.atomic
def run():
    # Borrar datos existentes (orden seguro por FKs)
    AccidenteJsonData.objects.all().delete()
    Prescripciones.objects.all().delete()
    PreguntasGuia.objects.all().delete()
    Informes.objects.all().delete()
    Hechos.objects.all().delete()
    Documentos.objects.all().delete()
    Declaraciones.objects.all().delete()
    ArbolCausas.objects.all().delete()
    Accidentes.objects.all().delete()
    CentrosTrabajo.objects.all().delete()
    Trabajadores.objects.all().delete()
    Empresas.objects.all().delete()
    Holdings.objects.all().delete()
    # OJO: NO tocamos accounts.User para no borrar el superusuario

    # Crear holding
    holding = Holdings.objects.create(nombre="Grupo IST")

    # Crear empresas
    empresa1 = Empresas.objects.create(
        holding=holding,
        empresa_sel="Maestranza S.A.",
        rut_empresa="12345678-9",
        actividad="Metalúrgica",
        direccion_empresa="Av. Siempre Viva 123",
        telefono="+56912345678",
        representante_legal="Juan Pérez",
        region="Metropolitana",
        comuna="Santiago"
    )

    empresa2 = Empresas.objects.create(
        holding=holding,
        empresa_sel="Constructora Andes Ltda.",
        rut_empresa="98765432-1",
        actividad="Construcción",
        direccion_empresa="Alameda 456",
        telefono="+56987654321",
        representante_legal="Ana Rojas",
        region="Valparaíso",
        comuna="Viña del Mar"
    )

    # Crear centros para empresa1
    CentrosTrabajo.objects.create(
        empresa=empresa1, nombre_local="Planta Santiago",
        direccion_centro="Camino Industrial 100", region="Metropolitana", comuna="Santiago"
    )
    CentrosTrabajo.objects.create(
        empresa=empresa1, nombre_local="Planta Sur",
        direccion_centro="Ruta 5 Sur km 10", region="Metropolitana", comuna="San Bernardo"
    )
    CentrosTrabajo.objects.create(
        empresa=empresa1, nombre_local="Planta Norte",
        direccion_centro="Av. Industrial Norte 222", region="Metropolitana", comuna="Quilicura"
    )

    # Crear centros para empresa2
    CentrosTrabajo.objects.create(
        empresa=empresa2, nombre_local="Obra Reñaca",
        direccion_centro="Reñaca Norte s/n", region="Valparaíso", comuna="Viña del Mar"
    )
    CentrosTrabajo.objects.create(
        empresa=empresa2, nombre_local="Obra Quilpué",
        direccion_centro="Av. Los Carrera 123", region="Valparaíso", comuna="Quilpué"
    )
    CentrosTrabajo.objects.create(
        empresa=empresa2, nombre_local="Obra San Antonio",
        direccion_centro="Puerto 321", region="Valparaíso", comuna="San Antonio"
    )

    # 👉 Usar tu usuario existente (id=1)
    usuario = User.objects.get(pk=1)

    # Crear trabajador
    trabajador = Trabajadores.objects.create(
        empresa=empresa1,
        nombre_trabajador="Luis Soto",
        rut_trabajador="22222222-2",
        fecha_nacimiento=date(1990, 5, 20),
        nacionalidad="Chilena",
        estado_civil="Soltero/a",
        domicilio="Calle Falsa 456",
        cargo_trabajador="Operario",
        contrato="Indefinido"
    )

    # Centro para accidente (empresa1)
    centro = CentrosTrabajo.objects.get(empresa=empresa1, nombre_local="Planta Sur")

    # Asegurar código único si re-ejecutas
    base_code = "IST2024-001"
    code = base_code
    i = 1
    while Accidentes.objects.filter(codigo_accidente=code).exists():
        i += 1
        code = f"{base_code}-{i}"

    # Crear accidente
    accidente = Accidentes.objects.create(
        holding=holding,
        empresa=empresa1,
        centro=centro,
        trabajador=trabajador,
        usuario_asignado=usuario,
        creado_por=usuario,
        fecha_accidente=date(2024, 6, 10),
        hora_accidente=time(14, 30),
        lugar_accidente="Zona de corte",
        tipo_accidente="Golpe por",
        naturaleza_lesion="Corte profundo",
        parte_afectada="Mano derecha",
        tarea="Cortar planchas",
        operacion="Laminado",
        danos_personas="SI",
        danos_propiedad="NO",
        perdidas_proceso="SI",
        contexto="Alta demanda de producción",
        circunstancias="Uso de máquina sin protección",
        codigo_accidente=code
    )

    # Declaraciones
    Declaraciones.objects.create(
        accidente=accidente,
        tipo_decl="accidentado",
        nombre="Luis Soto",
        rut="22222222-2",
        cargo="Operario",
        texto="Estaba utilizando la máquina sin protector cuando ocurrió el corte."
    )

    # Hechos
    Hechos.objects.create(
        accidente=accidente,
        secuencia=1,
        descripcion="El trabajador manipulaba una máquina sin protección."
    )

    # Informe
    Informes.objects.create(
        accidente=accidente,
        version=1,
        is_current=True,
        codigo="INF-2024-001",
        fecha_informe=date(2024, 6, 15),
        investigador="María González"
    )

    # Preguntas guía
    PreguntasGuia.objects.create(
        accidente=accidente,
        uuid=str(uuid.uuid4()),
        categoria="accidentado",
        pregunta="¿Qué ocurrió antes del accidente?",
        objetivo="Entender el contexto",
        respuesta="Estaba trabajando bajo presión."
    )

    # Prescripciones
    Prescripciones.objects.create(
        accidente=accidente,
        tipo="Seguridad",
        prioridad="Alta",
        plazo=date(2024, 7, 1),
        responsable="Jefe de turno",
        descripcion="Instalar protectores en todas las máquinas."
    )

    # JSON del accidente
    AccidenteJsonData.objects.create(
        accidente=accidente,
        preguntas_json={
            "0.0.0.0.0.0.0.0.0": "Corte superficial en mano",
            "1.0.0.0.0.0.0.0.0": "Disco de laminadora cortó superficie de mano"
        },
        otro_json_1={"key": "value"},
        otro_json_2={"key": "value2"}
    )

    # Árbol de causas
    ArbolCausas.objects.create(
        accidente=accidente,
        version=1,
        is_current=True,
        arbol_json_5q="""{
  "0.0.0.0.0.0.0.0.0": "Corte superficial en mano",
  "1.0.0.0.0.0.0.0.0": "Disco de laminadora cortó superficie de mano",
  "1.1.0.0.0.0.0.0.0": "Trabajador no utilizó dispositivo de seguridad sujetador",
  "1.1.1.0.0.0.0.0.0": "Trabajador detectó mal estado del sujetador sin mantención"
}""",
        arbol_json_dot="""digraph {
    node_0 [label="Corte superficial en mano"];
    node_1 [label="Disco de laminadora cortó superficie de mano"];
    node_0 -> node_1;
}"""
    )

    # --- Segundo caso vacío para rellenar ---
    # Crear trabajador vacío
    trabajador_vacio = Trabajadores.objects.create(
        empresa=empresa2,
        nombre_trabajador="",
        rut_trabajador="",
        fecha_nacimiento=None,
        nacionalidad="",
        estado_civil="",
        domicilio="",
        cargo_trabajador="",
        contrato=""
    )

    # Centro para accidente vacío (empresa2, primer centro)
    centro_vacio = CentrosTrabajo.objects.filter(empresa=empresa2).first()

    # Código único para el accidente vacío
    base_code_vacio = "IST2024-002"
    code_vacio = base_code_vacio
    j = 1
    while Accidentes.objects.filter(codigo_accidente=code_vacio).exists():
        j += 1
        code_vacio = f"{base_code_vacio}-{j}"

    # Crear accidente vacío
    accidente_vacio = Accidentes.objects.create(
        holding=holding,
        empresa=empresa2,
        centro=centro_vacio,
        trabajador=trabajador_vacio,
        usuario_asignado=usuario,
        creado_por=usuario,
        fecha_accidente=None,
        hora_accidente=None,
        lugar_accidente="",
        tipo_accidente="",
        naturaleza_lesion="",
        parte_afectada="",
        tarea="",
        operacion="",
        danos_personas="",
        danos_propiedad="",
        perdidas_proceso="",
        contexto="",
        circunstancias="",
        codigo_accidente=code_vacio
    )
    # No se crean declaraciones, hechos, informe, preguntas, prescripciones, json ni árbol de causas para este caso vacío.

# Si lo ejecutas con `manage.py shell`, llama a run():
if __name__ == "__main__":
    run()
