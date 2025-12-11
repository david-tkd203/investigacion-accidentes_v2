"""
Script para importar datos desde datos_exportados.json a la estructura multi-tenant.
Cada empresa se convierte en un tenant independiente con su propio esquema PostgreSQL.
"""
import json
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from django_tenants.utils import schema_context, tenant_context
from core.models import Empresa, Domain
from accidentes.models import (
    Holdings, Empresas, CentrosTrabajo, Trabajadores, Accidentes,
    ArbolCausas, Declaraciones, Documentos, Hechos, Informes,
    PreguntasGuia, Prescripciones, AccidenteJsonData, Relato
)
from accounts.models import User


def limpiar_rut(rut):
    """Limpia y formatea el RUT"""
    if not rut:
        return ""
    # Eliminar espacios y puntos
    rut = str(rut).strip().replace(".", "").replace(" ", "")
    return rut


def crear_schema_name(empresa_nombre, rut):
    """Crea un nombre de schema válido para PostgreSQL"""
    import re
    # Tomar nombre de empresa y RUT
    nombre = re.sub(r'[^\w\s-]', '', empresa_nombre.lower())
    nombre = re.sub(r'[-\s]+', '_', nombre)
    # Limitar a 30 caracteres para evitar límites de PostgreSQL
    rut_limpio = limpiar_rut(rut).replace("-", "")[:8]
    schema = f"{nombre[:20]}_{rut_limpio}"
    return schema


def cargar_datos_json(ruta_json):
    """Carga el archivo JSON de datos exportados"""
    print(f"📂 Cargando datos desde {ruta_json}...")
    with open(ruta_json, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    print(f"✅ {len(datos)} registros cargados")
    return datos


def agrupar_por_modelo(datos):
    """Agrupa los datos por modelo de Django"""
    grupos = {}
    for item in datos:
        modelo = item['model']
        if modelo not in grupos:
            grupos[modelo] = []
        grupos[modelo].append(item)
    return grupos


def crear_tenants_desde_empresas(datos_agrupados):
    """Crea un tenant (Empresa) por cada empresa del sistema antiguo"""
    empresas_legacy = datos_agrupados.get('accidentes.empresas', [])
    holdings_legacy = datos_agrupados.get('accidentes.holdings', [])
    
    # Crear diccionario de holdings por ID
    holdings_map = {h['pk']: h['fields']['nombre'] for h in holdings_legacy}
    
    print(f"\n🏢 Creando {len(empresas_legacy)} tenants (uno por empresa)...")
    
    tenants_creados = {}
    
    for emp_data in empresas_legacy:
        fields = emp_data['fields']
        empresa_id = emp_data['pk']
        nombre = fields['empresa_sel']
        rut = limpiar_rut(fields['rut_empresa'])
        holding_id = fields.get('holding')
        holding_nombre = holdings_map.get(holding_id, 'Sin holding')
        
        # Crear schema name único
        schema_name = crear_schema_name(nombre, rut)
        
        # Verificar si ya existe
        if Empresa.objects.filter(schema_name=schema_name).exists():
            print(f"⚠️  Tenant {schema_name} ya existe, omitiendo...")
            tenant = Empresa.objects.get(schema_name=schema_name)
        else:
            # Crear tenant
            try:
                tenant = Empresa(
                    schema_name=schema_name,
                    name=nombre,
                    rut=rut,
                    is_active=True,
                    direccion=fields.get('direccion_empresa', ''),
                    telefono=fields.get('telefono', ''),
                    email=''  # No hay email en datos legacy
                )
                tenant.save()
                
                # Crear dominio
                dominio = f"{schema_name}.localhost"
                Domain.objects.create(
                    domain=dominio,
                    tenant=tenant,
                    is_primary=True
                )
                
                print(f"✅ Tenant creado: {nombre} ({rut}) -> schema: {schema_name}")
            except Exception as e:
                print(f"❌ Error creando tenant {nombre}: {e}")
                continue
        
        # Guardar mapeo de empresa_id legacy -> tenant
        tenants_creados[empresa_id] = {
            'tenant': tenant,
            'nombre': nombre,
            'holding_id': holding_id,
            'holding_nombre': holding_nombre
        }
    
    print(f"\n✅ {len(tenants_creados)} tenants creados/verificados")
    return tenants_creados


def importar_datos_tenant(tenant_obj, empresa_id, datos_agrupados, tenants_map):
    """Importa datos legacy al esquema del tenant"""
    
    tenant_info = tenants_map[empresa_id]
    print(f"\n📥 Importando datos para: {tenant_info['nombre']} (schema: {tenant_obj.schema_name})")
    
    with tenant_context(tenant_obj):
        # 1. Importar Holdings
        holdings_legacy = datos_agrupados.get('accidentes.holdings', [])
        holdings_map = {}
        
        for holding_data in holdings_legacy:
            holding_id = holding_data['pk']
            fields = holding_data['fields']
            
            holding, created = Holdings.objects.get_or_create(
                holding_id=holding_id,
                defaults={
                    'nombre': fields['nombre'],
                    'created_at': fields.get('created_at')
                }
            )
            holdings_map[holding_id] = holding
            if created:
                print(f"  ✓ Holding: {fields['nombre']}")
        
        # 2. Importar Empresas (legacy) - solo la empresa correspondiente a este tenant
        empresas_legacy = [e for e in datos_agrupados.get('accidentes.empresas', []) 
                          if e['pk'] == empresa_id]
        empresas_map = {}
        
        for emp_data in empresas_legacy:
            fields = emp_data['fields']
            emp_id = emp_data['pk']
            
            empresa, created = Empresas.objects.get_or_create(
                empresa_id=emp_id,
                defaults={
                    'holding': holdings_map.get(fields['holding']),
                    'empresa_sel': fields['empresa_sel'],
                    'rut_empresa': fields['rut_empresa'],
                    'actividad': fields.get('actividad', ''),
                    'direccion_empresa': fields.get('direccion_empresa', ''),
                    'telefono': fields.get('telefono', ''),
                    'representante_legal': fields.get('representante_legal', ''),
                    'region': fields.get('region', ''),
                    'comuna': fields.get('comuna', ''),
                    'created_at': fields.get('created_at')
                }
            )
            empresas_map[emp_id] = empresa
            if created:
                print(f"  ✓ Empresa legacy: {fields['empresa_sel']}")
        
        # 3. Importar Centros de Trabajo
        centros_data = [c for c in datos_agrupados.get('accidentes.centrostrabajo', [])
                       if c['fields']['empresa'] == empresa_id]
        centros_map = {}
        
        for centro_data in centros_data:
            fields = centro_data['fields']
            centro_id = centro_data['pk']
            
            centro, created = CentrosTrabajo.objects.get_or_create(
                centro_id=centro_id,
                defaults={
                    'empresa': empresas_map.get(fields['empresa']),
                    'nombre_local': fields.get('nombre_local', ''),
                    'direccion_centro': fields.get('direccion_centro', ''),
                    'region': fields.get('region', ''),
                    'comuna': fields.get('comuna', '')
                }
            )
            centros_map[centro_id] = centro
            if created:
                print(f"  ✓ Centro: {fields.get('nombre_local', 'Sin nombre')}")
        
        # 4. Importar Trabajadores
        trabajadores_data = [t for t in datos_agrupados.get('accidentes.trabajadores', [])
                            if t['fields']['empresa'] == empresa_id]
        trabajadores_map = {}
        
        print(f"  Importando {len(trabajadores_data)} trabajadores...")
        for trab_data in trabajadores_data:
            fields = trab_data['fields']
            trab_id = trab_data['pk']
            
            trabajador, created = Trabajadores.objects.get_or_create(
                trabajador_id=trab_id,
                defaults={
                    'empresa': empresas_map.get(fields['empresa']),
                    'nombre_trabajador': fields.get('nombre_trabajador', ''),
                    'rut_trabajador': fields.get('rut_trabajador', ''),
                    'fecha_nacimiento': fields.get('fecha_nacimiento'),
                    'nacionalidad': fields.get('nacionalidad', ''),
                    'estado_civil': fields.get('estado_civil', ''),
                    'domicilio': fields.get('domicilio', ''),
                    'genero': fields.get('genero', ''),
                    'antiguedad_empresa_anios': fields.get('antiguedad_empresa_anios', 0),
                    'antiguedad_empresa_meses': fields.get('antiguedad_empresa_meses', 0),
                    'antiguedad_cargo_anios': fields.get('antiguedad_cargo_anios', 0),
                    'antiguedad_cargo_meses': fields.get('antiguedad_cargo_meses', 0),
                    'cargo_trabajador': fields.get('cargo_trabajador', ''),
                    'contrato': fields.get('contrato', '')
                }
            )
            trabajadores_map[trab_id] = trabajador
        
        print(f"  ✅ {len(trabajadores_map)} trabajadores importados")
        
        # 5. Importar Accidentes
        accidentes_data = [a for a in datos_agrupados.get('accidentes.accidentes', [])
                          if a['fields']['empresa'] == empresa_id]
        accidentes_map = {}
        
        print(f"  Importando {len(accidentes_data)} accidentes...")
        for acc_data in accidentes_data:
            fields = acc_data['fields']
            acc_id = acc_data['pk']
            
            accidente, created = Accidentes.objects.get_or_create(
                accidente_id=acc_id,
                defaults={
                    'holding': holdings_map.get(fields.get('holding')),
                    'empresa': empresas_map.get(fields.get('empresa')),
                    'centro': centros_map.get(fields.get('centro')),
                    'trabajador': trabajadores_map.get(fields.get('trabajador')),
                    'fecha_accidente': fields.get('fecha_accidente'),
                    'hora_accidente': fields.get('hora_accidente'),
                    'tipo_accidente': fields.get('tipo_accidente'),
                    'naturaleza_lesion': fields.get('naturaleza_lesion'),
                    'parte_afectada': fields.get('parte_afectada'),
                    'tarea': fields.get('tarea'),
                    'operacion': fields.get('operacion'),
                    'danos_personas': fields.get('danos_personas'),
                    'danos_propiedad': fields.get('danos_propiedad'),
                    'perdidas_proceso': fields.get('perdidas_proceso'),
                    'contexto': fields.get('contexto'),
                    'circunstancias': fields.get('circunstancias'),
                    'resumen': fields.get('resumen'),
                    'codigo_accidente': fields.get('codigo_accidente'),
                    'creado_en': fields.get('creado_en'),
                    'actualizado_en': fields.get('actualizado_en')
                }
            )
            accidentes_map[acc_id] = accidente
        
        print(f"  ✅ {len(accidentes_map)} accidentes importados")
        
        # 6. Importar datos relacionados (ArbolCausas, Declaraciones, etc.)
        # Puedes agregar aquí la importación de otros modelos relacionados
        
        print(f"✅ Importación completada para {tenant_info['nombre']}")


def main():
    # Ruta al archivo JSON (en el directorio padre)
    ruta_json = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'datos_exportados.json'
    )
    
    if not os.path.exists(ruta_json):
        print(f"❌ No se encontró el archivo: {ruta_json}")
        return
    
    print("=" * 80)
    print("🚀 IMPORTACIÓN DE DATOS A ESTRUCTURA MULTI-TENANT")
    print("=" * 80)
    
    # Cargar datos
    datos = cargar_datos_json(ruta_json)
    datos_agrupados = agrupar_por_modelo(datos)
    
    # Crear tenants
    tenants_map = crear_tenants_desde_empresas(datos_agrupados)
    
    # Importar datos a cada tenant
    print("\n" + "=" * 80)
    print("📥 IMPORTANDO DATOS A CADA TENANT")
    print("=" * 80)
    
    for empresa_id, tenant_info in tenants_map.items():
        try:
            importar_datos_tenant(
                tenant_info['tenant'],
                empresa_id,
                datos_agrupados,
                tenants_map
            )
        except Exception as e:
            print(f"❌ Error importando datos para {tenant_info['nombre']}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "=" * 80)
    print("✅ IMPORTACIÓN COMPLETADA")
    print("=" * 80)
    print(f"\n📊 Resumen:")
    print(f"  - Tenants creados: {len(tenants_map)}")
    print(f"  - Holdings: {len(datos_agrupados.get('accidentes.holdings', []))}")
    print(f"  - Empresas: {len(datos_agrupados.get('accidentes.empresas', []))}")
    print(f"  - Trabajadores: {len(datos_agrupados.get('accidentes.trabajadores', []))}")
    print(f"  - Accidentes: {len(datos_agrupados.get('accidentes.accidentes', []))}")


if __name__ == '__main__':
    main()
