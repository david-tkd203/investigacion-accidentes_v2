import json
import os
from django.conf import settings

# Apunta al JSON de demo dentro de config/
DEMO_JSON = os.path.join(settings.BASE_DIR, "config", "accidentes_demo.json")


def load_demo_cases():
    """Carga y retorna la lista completa de casos demo."""
    with open(DEMO_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def save_demo_cases(cases):
    """Guarda la lista de casos demo de vuelta al archivo."""
    with open(DEMO_JSON, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)


def find_demo_case(codigo):
    """
    Busca en el demo el caso que coincida por 'codigo' o 'accidente_id'.
    Retorna (lista_de_casos, caso) o (lista_de_casos, None).
    """
    cases = load_demo_cases()
    for case in cases:
        if case.get("codigo") == codigo or case.get("accidente_id") == codigo:
            return cases, case
    return cases, None


def update_demo_case(codigo, updates):
    """
    Abre config/accidentes_demo.json, busca el caso por 'codigo',
    aplica los 'updates' (dict clave: valor) y guarda de nuevo.
    Devuelve True si guardó, False en caso contrario.
    """
    print(f"[demo_storage] Iniciando actualización del caso '{codigo}' con: {updates}")
    if not os.path.isfile(DEMO_JSON):
        print(f"[demo_storage] ERROR: No existe el archivo {DEMO_JSON}")
        return False

    try:
        with open(DEMO_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[demo_storage] ERROR al leer {DEMO_JSON}: {e}")
        return False

    found = False
    for case in data:
        if case.get("codigo") == codigo:
            case.update(updates)
            found = True
            break

    if not found:
        print(f"[demo_storage] ERROR: Código '{codigo}' no encontrado en {DEMO_JSON}.")
        return False

    try:
        with open(DEMO_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[demo_storage] Éxito: Caso '{codigo}' actualizado.")
        return True
    except Exception as e:
        print(f"[demo_storage] ERROR al escribir {DEMO_JSON}: {e}")
        return False
