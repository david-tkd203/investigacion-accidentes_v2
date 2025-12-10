#!/usr/bin/env python
import os
import sys
import django
import argparse
import json

# Configurar Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from accidentes.models import Accidentes, Trabajadores, CentrosTrabajo, Empresas, Documentos, AccidenteJsonData

User = get_user_model()


def show_field(obj, field_name):
    return getattr(obj, field_name) if hasattr(obj, field_name) else '<no_field>'


def imprimir_accidente(accidente, verbose=False):
    print('\n' + '='*60)
    print(f"Accidente (obj.pk): {accidente.pk}")
    print(f"- accidente_id (campo): {show_field(accidente, 'accidente_id')}")
    print(f"- codigo_accidente: {getattr(accidente, 'codigo_accidente', '')}")
    print(f"- Fecha / Hora: {getattr(accidente, 'fecha_accidente', None)} {getattr(accidente, 'hora_accidente', None)}")
    print(f"- Lugar: {getattr(accidente, 'lugar_accidente', '')}")

    # Centro
    centro = getattr(accidente, 'centro', None)
    if centro:
        print('\nCENTRO:')
        print(f"  - pk: {centro.pk}")
        print(f"  - centro_id (campo): {show_field(centro, 'centro_id')}")
        print(f"  - nombre_local: {getattr(centro, 'nombre_local', '')}")
        print(f"  - comuna / region: {getattr(centro, 'comuna', '')} / {getattr(centro, 'region', '')}")
        empresa = getattr(centro, 'empresa', None)
        if empresa:
            print('  - Empresa asociada:')
            print(f"     * pk: {empresa.pk}")
            print(f"     * empresa_id (campo): {show_field(empresa, 'empresa_id')}")
            print(f"     * nombre: {getattr(empresa, 'empresa_sel', getattr(empresa, 'nombre_empresa', ''))}")
    else:
        print('\nCENTRO: <no asignado>')

    # Trabajador
    trabajador = getattr(accidente, 'trabajador', None)
    if trabajador:
        print('\nTRABAJADOR:')
        print(f"  - pk: {trabajador.pk}")
        print(f"  - trabajador_id (campo): {show_field(trabajador, 'trabajador_id')}")
        print(f"  - nombre: {getattr(trabajador, 'nombre_trabajador', getattr(trabajador, 'nombre_completo', ''))}")
        print(f"  - rut: {getattr(trabajador, 'rut_trabajador', '')}")
        print(f"  - empresa (pk): {getattr(trabajador, 'empresa_id', getattr(getattr(trabajador, 'empresa', None), 'pk', None))}")
    else:
        print('\nTRABAJADOR: <no asignado>')

    # Usuario asignado
    usuario = getattr(accidente, 'usuario_asignado', None)
    if usuario:
        print('\nUSUARIO ASIGNADO:')
        print(f"  - pk: {usuario.pk}")
        print(f"  - username: {getattr(usuario, 'username', '')}")
        print(f"  - email: {getattr(usuario, 'email', '')}")
        print(f"  - usuario_id (campo): {show_field(usuario, 'usuario_id')}")
    else:
        print('\nUSUARIO ASIGNADO: <no asignado>')

    # Metadatos
    print('\nMETADATOS:')
    print(f"  - creado_en: {getattr(accidente, 'creado_en', None)}")
    print(f"  - actualizado_en: {getattr(accidente, 'actualizado_en', None)}")

    # Documentos
    docs = Documentos.objects.filter(accidente=accidente)
    print(f"\nDOCUMENTOS: {docs.count()} archivos")
    if verbose and docs.exists():
        for d in docs[:50]:
            print(f"  - {getattr(d, 'documento_id', d.pk)} | {getattr(d, 'nombre_archivo', '')} | {getattr(d, 'mime_type', '')}")

    # JSON origen si existe
    try:
        ajd = AccidenteJsonData.objects.filter(accidente=accidente).first()
        if ajd:
            print('\nJSON ORIGEN (primer registro):')
            try:
                print(json.dumps(ajd.json_data, ensure_ascii=False, indent=2)[:2000])
                if len(json.dumps(ajd.json_data)) > 2000:
                    print('  ... (salida truncada)')
            except Exception:
                print(str(ajd.json_data)[:2000])
    except Exception:
        pass

    print('\n' + '='*60 + '\n')


def main():
    parser = argparse.ArgumentParser(description='Consultar accidente por accidente_id o codigo_accidente')
    parser.add_argument('--id', '-i', type=int, help='accidente_id (campo)')
    parser.add_argument('--pk', '-p', type=int, help='pk de la tabla Accidentes')
    parser.add_argument('--codigo', '-c', type=str, help='codigo_accidente')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mostrar información detallada')
    args = parser.parse_args()

    accidente = None
    try:
        if args.pk:
            accidente = Accidentes.objects.get(pk=args.pk)
        elif args.id:
            # intentar buscar por campo accidente_id si existe
            try:
                accidente = Accidentes.objects.get(accidente_id=args.id)
            except Exception:
                accidente = Accidentes.objects.filter(accidente_id=args.id).first()
        elif args.codigo:
            accidente = Accidentes.objects.filter(codigo_accidente=args.codigo).first()
        else:
            parser.print_help()
            return

        if not accidente:
            print('Accidente no encontrado')
            return

        imprimir_accidente(accidente, verbose=args.verbose)

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")


if __name__ == '__main__':
    main()
