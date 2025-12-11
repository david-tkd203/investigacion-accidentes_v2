#!/bin/sh
set -e

echo "🔗 Conectando a PostgreSQL (Docker healthcheck ya verificó la conexión)..."
echo "⏳ Esperando 5 segundos adicionales para asegurar que PostgreSQL esté completamente listo..."
sleep 5

echo "📋 Generando migraciones para core (tablas de tenants)..."
python manage.py makemigrations core --noinput

echo "📋 Generando migraciones para otras apps..."
python manage.py makemigrations --noinput

echo "🗄️ Migrando esquema compartido (todas las apps compartidas incluyendo core)..."
python manage.py migrate_schemas --shared --noinput

echo "🏢 Migrando esquemas de tenants..."
python manage.py migrate_schemas --tenant --noinput

echo "Estaticos..."
python manage.py collectstatic --noinput

#echo "Creando superuser"
#python manage.py ensure_superuser

if [ "${RUN_SEED_DATA:-0}" = "1" ]; then
    echo "Cargando datos semilla desde cargar_datos_completo.py..."
    python manage.py shell -c "from cargar_datos_completo import run as seed_run; seed_run()"
    echo "Datos semilla cargados."
fi

if [ "${RUN_SMU_DATA:-0}" = "1" ]; then
    echo "Cargando datos SMU..."
    python manage.py shell -c "from cargar_datos_smu_embebido import run as seed_run; seed_run()"
    echo "Datos semilla cargados."
fi

if [ "${RUN_EBCO_DATA:-0}" = "1" ]; then
    echo "Cargando datos EBCO..."
    python manage.py shell -c "from cargar_datos_ebco_embebido import run as seed_run; seed_run()"
    echo "Datos semilla cargados."
fi

if [ "${RUN_ULTRAMAR_DATA:-0}" = "1" ]; then
    echo "Cargando datos EBCO..."
    python manage.py shell -c "from cargar_datos_ultramar_embedido import run as seed_run; seed_run()"
    echo "Datos semilla cargados."
fi

if [ "${RUN_HUNTER_DATA:-0}" = "1" ]; then
    echo "Cargando datos HUNTER..."
    python manage.py shell -c "from cargar_datos_hunter_douglas_embedido import run as seed_run; seed_run()"
    echo "Datos HUNTER cargados."
fi

# Importar data.json con ORM de Django (opcional)
# RUN_IMPORT_HOLDINGS=1 habilita este bloque
# DATA_JSON_PATH puede sobreescribir la ruta por defecto
if [ "${RUN_IMPORT_HOLDINGS:-0}" = "1" ]; then
    echo "Importando data desde data.json..."
    DATA_JSON="${DATA_JSON_PATH:-/usr/src/app/arbol_causa_accidentes_ist/accidentes/setting/data/data.json}"

    # Fallback retrocompatible: usar HOLDINGS_JSON_PATH si está definido y data.json no existe
    if [ ! -f "$DATA_JSON" ] && [ -n "${HOLDINGS_JSON_PATH:-}" ]; then
        DATA_JSON="$HOLDINGS_JSON_PATH"
    fi

    # Fallback defensivo: si no existe, intenta localizarlo
    if [ ! -f "$DATA_JSON" ]; then
        FOUND="$(find /usr/src/app -maxdepth 6 -type f -name data.json 2>/dev/null | head -n1 || true)"
        [ -n "$FOUND" ] && DATA_JSON="$FOUND"
    fi

    if [ -f "$DATA_JSON" ]; then
        echo "Usando DATA_JSON_PATH=$DATA_JSON"
        export DATA_JSON_PATH="$DATA_JSON"
        python manage.py shell -c "
import os, json
from pathlib import Path
# 🔧 IMPORT CORREGIDO:
from accidentes.carga_datos_json import run as import_data, DEFAULT_JSON_PATH

json_path = Path(os.environ.get('DATA_JSON_PATH') or DEFAULT_JSON_PATH)
print(f'[import] DATA_JSON_PATH efectivo: {json_path}')
res = import_data(json_path)
print(json.dumps(res, ensure_ascii=False))
"
        echo "Importación de data terminada."
    else
        echo "AVISO: No se encontró data.json. Se omite la importación."
    fi
fi

echo "Iniciando servidor..."
exec "$@"
