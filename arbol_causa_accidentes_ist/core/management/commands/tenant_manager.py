"""
Script de utilidades para gestionar tenants (empresas)
"""
from django.core.management.base import BaseCommand
from core.models import Empresa, Domain


def crear_tenant_publico():
    """
    Crea el tenant público (obligatorio para django-tenants)
    """
    tenant, created = Empresa.objects.get_or_create(
        schema_name='public',
        defaults={
            'name': 'Administración General',
            'rut': '00.000.000-0',
            'is_active': True,
        }
    )
    
    if created:
        # Crear dominio para el tenant público
        Domain.objects.create(
            domain='localhost',  # Dominio por defecto
            tenant=tenant,
            is_primary=True
        )
        print(f"✅ Tenant público creado: {tenant.name}")
    else:
        print(f"ℹ️  Tenant público ya existe: {tenant.name}")
    
    return tenant


def crear_tenant(nombre, rut, schema_name, dominio):
    """
    Crea un nuevo tenant (empresa)
    
    Args:
        nombre: Nombre de la empresa
        rut: RUT de la empresa
        schema_name: Nombre del esquema en PostgreSQL (sin espacios, lowercase)
        dominio: Dominio para acceder a este tenant
    """
    try:
        tenant = Empresa.objects.create(
            schema_name=schema_name,
            name=nombre,
            rut=rut,
            is_active=True
        )
        
        # Crear dominio
        Domain.objects.create(
            domain=dominio,
            tenant=tenant,
            is_primary=True
        )
        
        print(f"✅ Tenant creado exitosamente:")
        print(f"   Nombre: {nombre}")
        print(f"   RUT: {rut}")
        print(f"   Schema: {schema_name}")
        print(f"   Dominio: {dominio}")
        
        return tenant
        
    except Exception as e:
        print(f"❌ Error al crear tenant: {str(e)}")
        return None


def listar_tenants():
    """
    Lista todos los tenants existentes
    """
    tenants = Empresa.objects.all()
    
    if not tenants:
        print("No hay tenants registrados")
        return
    
    print("\n" + "="*70)
    print("TENANTS REGISTRADOS")
    print("="*70)
    
    for tenant in tenants:
        dominios = Domain.objects.filter(tenant=tenant)
        dominios_str = ", ".join([d.domain for d in dominios])
        
        print(f"\nNombre: {tenant.name}")
        print(f"RUT: {tenant.rut}")
        print(f"Schema: {tenant.schema_name}")
        print(f"Dominios: {dominios_str}")
        print(f"Activo: {'Sí' if tenant.is_active else 'No'}")
        print(f"Creado: {tenant.created_on}")
        print("-" * 70)


class Command(BaseCommand):
    help = 'Gestión de tenants (empresas)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--crear-publico',
            action='store_true',
            help='Crea el tenant público (obligatorio)'
        )
        parser.add_argument(
            '--crear',
            action='store_true',
            help='Crea un nuevo tenant'
        )
        parser.add_argument(
            '--listar',
            action='store_true',
            help='Lista todos los tenants'
        )
        parser.add_argument('--nombre', type=str, help='Nombre de la empresa')
        parser.add_argument('--rut', type=str, help='RUT de la empresa')
        parser.add_argument('--schema', type=str, help='Nombre del schema')
        parser.add_argument('--dominio', type=str, help='Dominio para el tenant')

    def handle(self, *args, **options):
        if options['crear_publico']:
            crear_tenant_publico()
        
        elif options['crear']:
            if not all([options['nombre'], options['rut'], options['schema'], options['dominio']]):
                self.stdout.write(
                    self.style.ERROR(
                        'Debes proporcionar: --nombre --rut --schema --dominio'
                    )
                )
                return
            
            crear_tenant(
                options['nombre'],
                options['rut'],
                options['schema'],
                options['dominio']
            )
        
        elif options['listar']:
            listar_tenants()
        
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Usa --crear-publico, --crear o --listar'
                )
            )
