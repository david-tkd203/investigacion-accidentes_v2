# carga_datos_json.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models.signals import pre_save, post_save

from accidentes.models import (
    Holdings, Empresas, CentrosTrabajo, Trabajadores,
    Accidentes, ArbolCausas, Declaraciones, Documentos,
    Hechos, Informes, PreguntasGuia, Prescripciones, AccidenteJsonData, Relato
)

from pathlib import Path
from typing import Any, Dict, List, Union, Tuple, Optional
from datetime import datetime, date, time as dtime
import json
import re
import uuid
import os
import traceback

User = get_user_model()

# ========== MAPEO DE IDs ==========
# Diccionarios globales para mapear old_id (del JSON) -> new_pk (de la BD)
ID_MAPPING: Dict[str, Dict[Any, Any]] = {
    "holdings": {},
    "empresas": {},
    "centros": {},
    "trabajadores": {},
    "users": {},  # accounts.User (AUTH_USER_MODEL)
    "accidentes": {},
}

def _map_id(entity: str, old_id: Any, new_pk: Any) -> None:
    """Registra el mapeo de ID antiguo a nuevo PK."""
    if old_id is not None and str(old_id).strip():
        ID_MAPPING[entity][str(old_id)] = new_pk

def _get_mapped_id(entity: str, old_id: Any) -> Optional[Any]:
    """Obtiene el nuevo PK desde el ID antiguo."""
    if old_id is None or str(old_id).strip() == "":
        return None
    return ID_MAPPING[entity].get(str(old_id))

def _find_accidente(old_aid: Any, codigo_accidente: str, idx: int, logs: List[str]) -> Optional[Accidentes]:
    """Función auxiliar para encontrar un accidente por mapeo o código."""
    accidente = None
    accidente_pk = _get_mapped_id("accidentes", old_aid)
    
    if accidente_pk:
        try:
            accidente = Accidentes.objects.get(pk=accidente_pk)
        except Accidentes.DoesNotExist:
            logs.append(f"[idx:{idx}] WARN accidente pk={accidente_pk} no existe")
    
    # Si no se encontró por mapeo, buscar por código
    if not accidente and codigo_accidente:
        codigo_accidente = _safe_text(codigo_accidente, 100)
        if codigo_accidente:
            try:
                accidente = Accidentes.objects.get(codigo_accidente=codigo_accidente)
                _map_id("accidentes", old_aid, accidente.pk)
                logs.append(f"[idx:{idx}] INFO accidente encontrado por código: {codigo_accidente}")
            except Accidentes.DoesNotExist:
                pass
    
    return accidente

def _clear_mappings() -> None:
    """Limpia todos los mapeos."""
    for key in ID_MAPPING:
        ID_MAPPING[key].clear()

def _preprocess_accidentes_assign_empresa_holding(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pre-procesa accidentes con empresa_id o holding_id faltantes, asignándolos
    basándose en la empresa del trabajador. NO modifica centro_id (puede quedar null).
    
    1. Construye un mapa de trabajador_id -> (empresa_id, holding_id)
    2. Corrige accidentes asignándoles empresa_id y holding_id según su trabajador
    """
    logs: List[str] = []
    logs.append("\n🔧 PRE-PROCESAMIENTO: Asignando empresa_id y holding_id a accidentes")
    logs.append("="*70)
    
    # 1. Mapear trabajador_id -> (empresa_id, holding_id)
    trabajador_to_empresa_holding: Dict[int, Tuple[int, int]] = {}
    trabajadores = data.get("trabajadores", [])
    empresas = data.get("empresas", [])
    
    # Primero, crear mapa empresa_id -> holding_id
    empresa_to_holding: Dict[int, int] = {}
    for empresa in empresas:
        eid = empresa.get("empresa_id")
        hid = empresa.get("holding_id")
        if eid is not None and hid is not None:
            empresa_to_holding[eid] = hid
    
    # Luego, mapear trabajador_id -> (empresa_id, holding_id)
    for trab in trabajadores:
        tid = trab.get("trabajador_id")
        eid = trab.get("empresa_id")
        if tid is not None and eid is not None:
            hid = empresa_to_holding.get(eid)
            if hid is not None:
                trabajador_to_empresa_holding[tid] = (eid, hid)
    
    logs.append(f"✅ Mapeados {len(trabajador_to_empresa_holding)} trabajadores a (empresa_id, holding_id)")
    
    # 2. Corregir accidentes con empresa_id o holding_id faltantes Y centro_id null
    accidentes = data.get("accidentes", [])
    corregidos = 0
    corregidos_con_centro_null = 0
    sin_correccion = 0
    
    for acc in accidentes:
        empresa_id = acc.get("empresa_id")
        holding_id = acc.get("holding_id")
        centro_id = acc.get("centro_id")
        
        # Solo procesar si falta empresa_id o holding_id
        if empresa_id is None or holding_id is None:
            tid = acc.get("trabajador_id")
            codigo = acc.get("codigo_accidente", "SIN_CODIGO")
            accidente_id = acc.get("accidente_id", "N/A")
            
            if tid is None:
                if centro_id is None:
                    logs.append(f"   ❌ Accidente ID={accidente_id} Código='{codigo}': sin trabajador_id (no se puede corregir)")
                sin_correccion += 1
                continue
            
            # Obtener empresa_id y holding_id del trabajador
            empresa_holding = trabajador_to_empresa_holding.get(tid)
            if empresa_holding is None:
                if centro_id is None:
                    logs.append(f"   ❌ Accidente ID={accidente_id} Código='{codigo}': trabajador {tid} no tiene empresa/holding (no se puede corregir)")
                sin_correccion += 1
                continue
            
            nuevo_empresa_id, nuevo_holding_id = empresa_holding
            
            # CORREGIR: asignar empresa_id y holding_id (sin tocar centro_id)
            if empresa_id is None:
                acc["empresa_id"] = nuevo_empresa_id
            if holding_id is None:
                acc["holding_id"] = nuevo_holding_id
            
            corregidos += 1
            
            # Solo loguear si centro_id es null
            if centro_id is None:
                corregidos_con_centro_null += 1
                logs.append(f"   ✅ Accidente ID={accidente_id} Código='{codigo}' [centro_id=null]: empresa_id={nuevo_empresa_id}, holding_id={nuevo_holding_id} (trabajador {tid})")
    
    logs.append("")
    logs.append(f"📊 RESUMEN PRE-PROCESAMIENTO:")
    logs.append(f"   ✅ Total accidentes corregidos: {corregidos}")
    logs.append(f"   🔹 Con centro_id=null: {corregidos_con_centro_null}")
    logs.append(f"   ❌ Sin corrección posible: {sin_correccion}")
    logs.append(f"   📁 Total accidentes: {len(accidentes)}")
    logs.append("="*70 + "\n")
    
    # Imprimir logs
    for log in logs:
        print(log)
    
    return data

# ========== CONFIG / RUTAS ==========
DEFAULT_JSON_PATH = Path("arbol_causa_accidentes_ist") / "config" / "accidentes_demo.json"  # Cambio a archivo demo
DEFAULT_USER_PASSWORD = "ISTinvestiga@2025"
CONTAINER_DOCS_DIR = Path("/usr/src/app/protected_media/documentos")
# Ruta que se resolverá dinámicamente (local o contenedor)
# Dentro del contenedor, __file__ será /usr/src/app/accidentes/carga_datos_json.py
# Fuera del contenedor (Windows), será la ruta local completa
SRC_DOCS_DIR = None  # Se calculará dinámicamente en _resolve_src_docs_dir()

# ========== UTILIDADES DE NORMALIZACIÓN ==========
_RUT_CLEAN_RE = re.compile(r"[^0-9kK]")

def _safe_text(val: Any, maxlen: Optional[int] = None, case: Optional[str] = None) -> str:
    s = "" if val is None else str(val).strip()
    if case == "lower":
        s = s.lower()
    elif case == "upper":
        s = s.upper()
    elif case == "title":
        s = s.title()
    if maxlen is not None and maxlen > 0:
        s = s[:maxlen]
    return s

def _dv_mod11(num_str: str) -> str:
    seq = [2, 3, 4, 5, 6, 7]
    acc = 0
    mul_idx = 0
    for ch in reversed(num_str):
        acc += int(ch) * seq[mul_idx]
        mul_idx = (mul_idx + 1) % len(seq)
    rest = 11 - (acc % 11)
    if rest == 11:
        return "0"
    if rest == 10:
        return "K"
    return str(rest)

def normalize_rut(val: Any) -> str:
    if not val:
        return ""
    raw = _RUT_CLEAN_RE.sub("", str(val))
    if not raw:
        return ""
    body = raw[:-1] if len(raw) > 1 else raw
    dv = raw[-1].upper() if len(raw) > 1 else None
    if dv is None:
        if len(body) < 2:
            return ""
        dv = _dv_mod11(body)
    calc = _dv_mod11(body)
    if dv != calc:
        dv = calc
    body = body.lstrip("0") or "0"
    return f"{body}-{dv}"

def _parse_iso_dt(val: Any) -> Optional[datetime]:
    if not val:
        return None
    s = str(val).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        return None
    if timezone.is_naive(dt):
        try:
            tz = timezone.get_current_timezone() if getattr(settings, "USE_TZ", False) else None
        except Exception:
            tz = None
        if tz:
            dt = timezone.make_aware(dt, tz)
    return dt

def _parse_iso_date(val: Any) -> Optional[date]:
    if not val:
        return None
    try:
        return date.fromisoformat(str(val)[:10])
    except Exception:
        return None

def _parse_iso_time(val: Any) -> Optional[dtime]:
    if not val:
        return None
    s = str(val)
    try:
        parts = [int(p) for p in s.split(":")]
        while len(parts) < 3:
            parts.append(0)
        return dtime(parts[0], parts[1], parts[2])
    except Exception:
        return None

_AGE_TOK_RE = re.compile(r"(?P<num>\d+)\s*(?P<unit>a|años?|yrs?|y|mes(?:es)?|m|dias?|d)", re.I)

def _parse_antiguedad(text: Any) -> Tuple[int, int, int]:
    if not text:
        return 0, 0, 0
    s = str(text)
    yrs = mos = dys = 0
    for m in _AGE_TOK_RE.finditer(s):
        n = int(m.group("num"))
        u = m.group("unit").lower()
        if u.startswith(("a", "y")):
            yrs += n
        elif u.startswith("m"):
            mos += n
        elif u.startswith("d"):
            dys += n
    return yrs, mos, dys

def _model_has_field(model, field_name: str) -> bool:
    from django.core.exceptions import FieldDoesNotExist
    try:
        model._meta.get_field(field_name)
        return True
    except FieldDoesNotExist:
        return False

def _read_json(path: Union[str, Path]) -> Dict[str, Any]:
    p = Path(path)
    
    # Verificar que existe
    if not p.exists():
        raise FileNotFoundError(f"Archivo JSON no encontrado: {p}")
    
    # Verificar que NO sea un directorio (problema común con volúmenes Docker)
    if p.is_dir():
        raise IsADirectoryError(
            f"La ruta apunta a un DIRECTORIO, no a un archivo: {p}\n"
            f"Esto suele ocurrir cuando hay un volumen de Docker montado incorrectamente.\n"
            f"Usa un archivo JSON real, por ejemplo: 'arbol_causa_accidentes_ist/config/accidentes_demo.json'"
        )
    
    # Leer y parsear el JSON
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("El JSON raíz debe ser un objeto.")
    return data

def _take_list(obj: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
    recs = obj.get(key, [])
    if recs is None:
        return []
    if not isinstance(recs, list):
        raise ValueError(f"La clave '{key}' debe ser una lista.")
    return recs

# ========== HOLDINGS (CON MAPEO) ==========
def upsert_holdings(records: List[Dict[str, Any]]) -> Tuple[int, int, List[str], List[str]]:
    created = updated = 0
    errors: List[str] = []
    logs: List[str] = []

    supports_created_at = _model_has_field(Holdings, "created_at")

    for idx, r in enumerate(records, 1):
        old_hid = r.get("holding_id")
        nombre = _safe_text(r.get("nombre"), 255, case="title")

        if not nombre:
            errors.append(f"[holdings:{idx}] nombre vacío, omitido")
            continue

        defaults: Dict[str, Any] = {"nombre": nombre}
        if supports_created_at:
            dt = _parse_iso_dt(r.get("created_at"))
            if dt:
                defaults["created_at"] = dt

        try:
            # Buscar por nombre (campo único natural)
            obj, was_created = Holdings.objects.update_or_create(
                nombre=nombre,
                defaults=defaults
            )
            
            # 🔑 MAPEAR ID ANTIGUO -> NUEVO PK
            _map_id("holdings", old_hid, obj.pk)

            if was_created:
                created += 1
                logs.append(f"[holdings:{idx}] CREATED '{nombre}' (old_id={old_hid} -> new_pk={obj.pk})")
            else:
                updated += 1
                logs.append(f"[holdings:{idx}] UPDATED '{nombre}' (old_id={old_hid} -> new_pk={obj.pk})")

        except Exception as e:
            errors.append(f"[holdings:{idx}] ERROR -> {e}")

    return created, updated, logs, errors

# ========== EMPRESAS (CON MAPEO MEJORADO) ==========
def upsert_empresas(records: List[Dict[str, Any]]) -> Tuple[int, int, List[str], List[str]]:
    created = updated = 0
    errors: List[str] = []
    logs: List[str] = []

    supports_created_at = _model_has_field(Empresas, "created_at")

    for idx, r in enumerate(records, 1):
        old_eid = r.get("empresa_id")
        old_hid = r.get("holding_id")
        
        # 🔍 OBTENER HOLDING - INTENTAR MAPEO PRIMERO, LUEGO BUSCAR O CREAR
        holding = None
        holding_pk = _get_mapped_id("holdings", old_hid)
        
        if holding_pk:
            try:
                holding = Holdings.objects.get(pk=holding_pk)
            except Holdings.DoesNotExist:
                logs.append(f"[empresas:{idx}] WARN holding pk={holding_pk} no existe, intentando crear")
        
        # Si no se encontró por mapeo, buscar por nombre o crear uno por defecto
        if not holding:
            holding_nombre = _safe_text(r.get("holding_nombre"), 255, case="title") or "Holding Sin Nombre"
            holding, _ = Holdings.objects.get_or_create(
                nombre=holding_nombre,
                defaults={"nombre": holding_nombre}
            )
            # Actualizar mapeo
            _map_id("holdings", old_hid, holding.pk)
            logs.append(f"[empresas:{idx}] INFO holding creado/encontrado: '{holding_nombre}' (pk={holding.pk})")

        empresa_sel = _safe_text(r.get("empresa_sel"), 255, case="title")
        rut_empresa = _safe_text(r.get("rut_empresa"), 20)

        if not rut_empresa:
            errors.append(f"[empresas:{idx}] rut_empresa vacío")
            continue

        defaults: Dict[str, Any] = {
            "holding": holding,
            "empresa_sel": empresa_sel,
            "rut_empresa": rut_empresa,
            "actividad": _safe_text(r.get("actividad"), 255, case="title"),
            "direccion_empresa": _safe_text(r.get("direccion_empresa"), 255, case="title"),
            "telefono": _safe_text(r.get("telefono"), 30),
            "representante_legal": _safe_text(r.get("representante_legal"), 255, case="title"),
            "region": _safe_text(r.get("region"), 100, case="title"),
            "comuna": _safe_text(r.get("comuna"), 100, case="title"),
        }

        if supports_created_at:
            dt = _parse_iso_dt(r.get("created_at"))
            if dt:
                defaults["created_at"] = dt

        try:
            obj, was_created = Empresas.objects.update_or_create(
                rut_empresa=rut_empresa,
                defaults=defaults
            )
            
            # 🔑 MAPEAR ID
            _map_id("empresas", old_eid, obj.pk)

            if was_created:
                created += 1
                logs.append(f"[empresas:{idx}] CREATED '{empresa_sel}' (old_id={old_eid} -> new_pk={obj.pk})")
            else:
                updated += 1
                logs.append(f"[empresas:{idx}] UPDATED '{empresa_sel}' (old_id={old_eid} -> new_pk={obj.pk})")

        except Exception as e:
            errors.append(f"[empresas:{idx}] ERROR -> {e}")

    return created, updated, logs, errors

# ========== CENTROS (CON MAPEO MEJORADO) ==========
def upsert_centros(records: List[Dict[str, Any]]) -> Tuple[int, int, List[str], List[str]]:
    created = updated = 0
    errors: List[str] = []
    logs: List[str] = []

    for idx, r in enumerate(records, 1):
        old_cid = r.get("centro_id")
        old_eid = r.get("empresa_id")

        # 🔍 OBTENER EMPRESA - BUSCAR POR MAPEO O POR RUT
        empresa = None
        empresa_pk = _get_mapped_id("empresas", old_eid)
        
        if empresa_pk:
            try:
                empresa = Empresas.objects.get(pk=empresa_pk)
            except Empresas.DoesNotExist:
                logs.append(f"[centros:{idx}] WARN empresa pk={empresa_pk} no existe")
        
        # Si no se encontró por mapeo, buscar por RUT
        if not empresa:
            rut_empresa = _safe_text(r.get("rut_empresa"), 20)
            if rut_empresa:
                try:
                    empresa = Empresas.objects.get(rut_empresa=rut_empresa)
                    _map_id("empresas", old_eid, empresa.pk)
                    logs.append(f"[centros:{idx}] INFO empresa encontrada por RUT: {rut_empresa}")
                except Empresas.DoesNotExist:
                    logs.append(f"[centros:{idx}] WARN empresa con RUT={rut_empresa} no existe")
        
        if not empresa:
            errors.append(f"[centros:{idx}] empresa_id={old_eid} NO encontrado, omitido")
            continue

        nombre_local = _safe_text(r.get("nombre_local"), 255, case="title")
        if not nombre_local:
            errors.append(f"[centros:{idx}] nombre_local vacío")
            continue

        defaults = {
            "empresa": empresa,
            "nombre_local": nombre_local,
            "direccion_centro": _safe_text(r.get("direccion_centro"), 255, case="title"),
            "region": _safe_text(r.get("region"), 100, case="title"),
            "comuna": _safe_text(r.get("comuna"), 100, case="title"),
        }

        try:
            obj, was_created = CentrosTrabajo.objects.update_or_create(
                empresa=empresa,
                nombre_local=nombre_local,
                defaults=defaults
            )
            
            # 🔑 MAPEAR ID
            _map_id("centros", old_cid, obj.pk)

            if was_created:
                created += 1
                logs.append(f"[centros:{idx}] CREATED '{nombre_local}' (old_id={old_cid} -> new_pk={obj.pk})")
            else:
                updated += 1
                logs.append(f"[centros:{idx}] UPDATED '{nombre_local}' (old_id={old_cid} -> new_pk={obj.pk})")

        except Exception as e:
            errors.append(f"[centros:{idx}] ERROR -> {e}")

    return created, updated, logs, errors

# ========== TRABAJADORES (CON MAPEO MEJORADO) ==========
def upsert_trabajadores(records: List[Dict[str, Any]]) -> Tuple[int, int, List[str], List[str]]:
    created = updated = 0
    errors: List[str] = []
    logs: List[str] = []

    supports_created_at = _model_has_field(Trabajadores, "created_at")

    for idx, r in enumerate(records, 1):
        old_tid = r.get("trabajador_id")
        old_eid = r.get("empresa_id")

        # 🔍 OBTENER EMPRESA - BUSCAR POR MAPEO O POR RUT
        empresa = None
        empresa_pk = _get_mapped_id("empresas", old_eid)
        
        if empresa_pk:
            try:
                empresa = Empresas.objects.get(pk=empresa_pk)
            except Empresas.DoesNotExist:
                logs.append(f"[trabajadores:{idx}] WARN empresa pk={empresa_pk} no existe")
        
        # Si no se encontró por mapeo, buscar por RUT
        if not empresa:
            rut_empresa = _safe_text(r.get("rut_empresa"), 20)
            if rut_empresa:
                try:
                    empresa = Empresas.objects.get(rut_empresa=rut_empresa)
                    _map_id("empresas", old_eid, empresa.pk)
                    logs.append(f"[trabajadores:{idx}] INFO empresa encontrada por RUT: {rut_empresa}")
                except Empresas.DoesNotExist:
                    logs.append(f"[trabajadores:{idx}] WARN empresa con RUT={rut_empresa} no existe")
        
        if not empresa:
            errors.append(f"[trabajadores:{idx}] empresa_id={old_eid} NO encontrado, omitido")
            continue

        nombre = _safe_text(r.get("nombre_trabajador"), 255, case="title")
        rut_trab = normalize_rut(r.get("rut_trabajador"))

        if not rut_trab:
            errors.append(f"[trabajadores:{idx}] rut_trabajador vacío")
            continue

        ae, me, _ = _parse_antiguedad(r.get("antiguedad_empresa"))
        ac, mc, _ = _parse_antiguedad(r.get("antiguedad_cargo"))

        defaults: Dict[str, Any] = {
            "empresa": empresa,
            "nombre_trabajador": nombre,
            "rut_trabajador": rut_trab,
            "fecha_nacimiento": _parse_iso_date(r.get("fecha_nacimiento")),
            "nacionalidad": _safe_text(r.get("nacionalidad"), 100, case="title"),
            "estado_civil": _safe_text(r.get("estado_civil"), 50, case="title"),
            "domicilio": _safe_text(r.get("domicilio"), 255, case="title"),
            "cargo_trabajador": _safe_text(r.get("cargo_trabajador"), 100, case="title"),
            "antiguedad_empresa_anios": ae,
            "antiguedad_empresa_meses": me,
            "antiguedad_cargo_anios": ac,
            "antiguedad_cargo_meses": mc,
        }

        if _model_has_field(Trabajadores, "contrato"):
            defaults["contrato"] = _safe_text(r.get("contrato"), 50)
        if _model_has_field(Trabajadores, "genero"):
            defaults["genero"] = _safe_text(r.get("genero"), 1, case="upper")

        if supports_created_at:
            dt = _parse_iso_dt(r.get("created_at"))
            if dt:
                defaults["created_at"] = dt

        try:
            obj, was_created = Trabajadores.objects.update_or_create(
                rut_trabajador=rut_trab,
                defaults=defaults
            )
            
            # 🔑 MAPEAR ID
            _map_id("trabajadores", old_tid, obj.pk)

            if was_created:
                created += 1
                logs.append(f"[trabajadores:{idx}] CREATED '{nombre}' ({rut_trab}) (old_id={old_tid} -> new_pk={obj.pk})")
            else:
                updated += 1
                logs.append(f"[trabajadores:{idx}] UPDATED '{nombre}' ({rut_trab}) (old_id={old_tid} -> new_pk={obj.pk})")

        except Exception as e:
            errors.append(f"[trabajadores:{idx}] ERROR -> {e}")

    return created, updated, logs, errors

# ========== USUARIOS (accounts.User - CON MAPEO MEJORADO) ==========
def _unique_username(base: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9_.-]", "", base) or "user"
    uname = base
    i = 1
    while User.objects.filter(username=uname).exists():
        i += 1
        uname = f"{base}{i}"[:150]
    return uname

def _infer_rol(cargo: str) -> str:
    """
    Infiere el rol del usuario basándose en su cargo.
    
    Roles definidos en access.py:
    - SUPER_ROLES: admin, admin_ist, investigador_ist
    - Otros roles: admin_holding, admin_empresa, investigador, coordinador
    """
    if not cargo:
        return "investigador"
    
    c = cargo.lower().strip()
    
    # Normalizar texto: eliminar acentos, múltiples espacios, etc.
    c = c.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    c = " ".join(c.split())  # Normalizar espacios
    
    # SUPER ROLES (orden de prioridad)
    if any(x in c for x in ["admin global", "administrador global", "superadmin", "super admin"]):
        return "admin"
    
    if any(x in c for x in ["admin ist", "administrador ist", "adm ist"]):
        return "admin_ist"
    
    if any(x in c for x in ["investigador ist", "inv ist", "investigadora ist"]):
        return "investigador_ist"
    
    # ROLES JERÁRQUICOS
    if any(x in c for x in ["admin holding", "administrador holding", "adm holding", "admin grupo", "administrador grupo"]):
        return "admin_holding"
    
    if any(x in c for x in ["admin empresa", "administrador empresa", "adm empresa", "admin emp", "administrador emp"]):
        return "admin_empresa"
    
    # COORDINADORES
    if any(x in c for x in ["coordinador", "coordinadora", "coord", "jefe", "jefa", "encargado", "encargada"]):
        return "admin_empresa"
    
    # INVESTIGADORES (debe ir al final para no sobrescribir investigador_ist)
    if any(x in c for x in ["investigador", "investigadora", "analista", "especialista"]):
        # Si ya pasó por investigador_ist, no llega aquí
        return "investigador"
    
    # DEFAULT: investigador (rol más básico)
    return "investigador"

def upsert_usuarios(records: List[Dict[str, Any]]) -> Tuple[int, int, List[str], List[str]]:
    created = updated = 0
    errors: List[str] = []
    logs: List[str] = []

    for idx, r in enumerate(records, 1):
        old_uid = r.get("id") or r.get("usuario_id")
        old_eid = r.get("empresa_id")
        
        rut_norm = normalize_rut(r.get("rut"))
        nombre = _safe_text(r.get("nombre"), 150, case="title")
        apepat = _safe_text(r.get("apepat"), 150, case="title")
        apemat = _safe_text(r.get("apemat"), 150, case="title")
        email = _safe_text(r.get("email"), 254, case="lower") or None
        cargo = _safe_text(r.get("cargo") or r.get("Cargo"), 100, case="title")

        # 🔍 OBTENER EMPRESA - BUSCAR POR MAPEO O POR RUT
        empresa = None
        holding = None
        empresa_pk = _get_mapped_id("empresas", old_eid)
        
        if empresa_pk:
            try:
                empresa = Empresas.objects.get(pk=empresa_pk)
                holding = empresa.holding
            except Empresas.DoesNotExist:
                logs.append(f"[usuarios:{idx}] WARN empresa pk={empresa_pk} no existe")
        
        # Si no se encontró por mapeo, buscar por RUT
        if not empresa:
            rut_empresa = _safe_text(r.get("rut_empresa"), 20)
            if rut_empresa:
                try:
                    empresa = Empresas.objects.get(rut_empresa=rut_empresa)
                    holding = empresa.holding
                    _map_id("empresas", old_eid, empresa.pk)
                    logs.append(f"[usuarios:{idx}] INFO empresa encontrada por RUT: {rut_empresa}")
                except Empresas.DoesNotExist:
                    pass

        # Generar username
        if email:
            username_base = email.split("@")[0]
        elif rut_norm:
            username_base = f"u{rut_norm.replace('-', '')}"
        else:
            username_base = f"user{old_uid or idx}"
        
        username = _unique_username(username_base)

        first_name = nombre
        last_name = " ".join([x for x in [apepat, apemat] if x]).strip()

        rol_val = _infer_rol(cargo)
        is_staff = rol_val.startswith("admin") or rol_val in ("investigador_ist", "admin_ist")
        is_superuser = (rol_val == "admin")

        try:
            if email:
                obj, was_created = User.objects.get_or_create(
                    email=email,
                    defaults={"username": username}
                )
            else:
                obj = User(username=username)
                was_created = True

            obj.first_name = first_name
            obj.last_name = last_name
            obj.is_active = True
            obj.is_staff = is_staff
            obj.is_superuser = is_superuser

            if not getattr(obj, "date_joined", None):
                obj.date_joined = timezone.now()

            # Campos extras
            if _model_has_field(User, "rut") and rut_norm:
                obj.rut = rut_norm
            if _model_has_field(User, "rol"):
                obj.rol = rol_val
            if _model_has_field(User, "empresa") and empresa:
                obj.empresa = empresa
            if _model_has_field(User, "holding") and holding:
                obj.holding = holding
            if _model_has_field(User, "cargo"):
                obj.cargo = cargo

            if was_created or not obj.password:
                obj.set_password(DEFAULT_USER_PASSWORD)

            obj.save()

            # 🔑 MAPEAR ID
            _map_id("users", old_uid, obj.pk)

            if was_created:
                created += 1
                logs.append(f"[usuarios:{idx}] CREATED '{username}' (old_id={old_uid} -> new_pk={obj.pk})")
            else:
                updated += 1
                logs.append(f"[usuarios:{idx}] UPDATED '{username}' (old_id={old_uid} -> new_pk={obj.pk})")

        except Exception as e:
            errors.append(f"[usuarios:{idx}] ERROR -> {e}")

    # Imprimir errores en consola al finalizar
    if errors:
        print('\nUsuarios no importados y motivo:')
        for err in errors:
            print(f"ID: {err['usuario'].get('id', '-')}, Motivo: {err['motivo']}, Datos: {err['usuario']}")
    else:
        print('Todos los usuarios fueron importados correctamente.')

    return created, updated, logs, errors

# ========== ACCIDENTES (CON MAPEO) ==========
def _ensure_codigo_unique(base_code: str) -> str:
    code = base_code or uuid.uuid4().hex[:8].upper()
    i = 1
    while Accidentes.objects.filter(codigo_accidente=code).exists():
        i += 1
        code = f"{base_code or 'ACC'}-{i}"
    return code

def upsert_accidentes(records: List[Dict[str, Any]]) -> Tuple[int, int, List[str], List[str]]:
    created = updated = 0
    errors: List[str] = []
    logs: List[str] = []

    for idx, r in enumerate(records, 1):
        old_aid = r.get("accidente_id")
        old_cid = r.get("centro_id")
        old_tid = r.get("trabajador_id")
        old_uid = r.get("usuario_id")

        # 🔍 OBTENER CENTRO - BUSCAR POR MAPEO O POR NOMBRE+EMPRESA
        centro = None
        centro_pk = _get_mapped_id("centros", old_cid)
        
        if centro_pk:
            try:
                centro = CentrosTrabajo.objects.get(pk=centro_pk)
            except CentrosTrabajo.DoesNotExist:
                logs.append(f"[accidentes:{idx}] WARN centro pk={centro_pk} no existe")
        
        # Si no se encontró por mapeo, buscar por nombre
        if not centro and old_cid is not None:
            nombre_centro = _safe_text(r.get("nombre_centro"), 255, case="title")
            if nombre_centro:
                try:
                    centro = CentrosTrabajo.objects.filter(nombre_local__icontains=nombre_centro).first()
                    if centro:
                        _map_id("centros", old_cid, centro.pk)
                        logs.append(f"[accidentes:{idx}] INFO centro encontrado por nombre: {nombre_centro}")
                except Exception:
                    pass
        
        # 🆕 PERMITIR ACCIDENTES SIN CENTRO (centro_id=null)
        # En estos casos, obtener empresa y holding desde los datos preprocesados
        empresa = None
        holding = None
        
        if centro:
            # Si hay centro, obtener empresa y holding desde él
            try:
                empresa = centro.empresa
                holding = empresa.holding
            except Exception as e:
                errors.append(f"[accidentes:{idx}] ERROR obteniendo empresa/holding desde centro: {e}")
                continue
        else:
            # Si NO hay centro, obtener desde los datos preprocesados
            old_eid = r.get("empresa_id")
            old_hid = r.get("holding_id")
            
            # Buscar empresa
            if old_eid:
                empresa_pk = _get_mapped_id("empresas", old_eid)
                if empresa_pk:
                    try:
                        empresa = Empresas.objects.get(pk=empresa_pk)
                    except Empresas.DoesNotExist:
                        errors.append(f"[accidentes:{idx}] empresa pk={empresa_pk} NO encontrada")
                        continue
                else:
                    errors.append(f"[accidentes:{idx}] empresa_id={old_eid} no mapeado")
                    continue
            else:
                errors.append(f"[accidentes:{idx}] Sin centro_id ni empresa_id")
                continue
            
            # Buscar holding
            if old_hid:
                holding_pk = _get_mapped_id("holdings", old_hid)
                if holding_pk:
                    try:
                        holding = Holdings.objects.get(pk=holding_pk)
                    except Holdings.DoesNotExist:
                        errors.append(f"[accidentes:{idx}] holding pk={holding_pk} NO encontrado")
                        continue
                else:
                    errors.append(f"[accidentes:{idx}] holding_id={old_hid} no mapeado")
                    continue
            else:
                errors.append(f"[accidentes:{idx}] Sin centro_id ni holding_id")
                continue
            
            logs.append(f"[accidentes:{idx}] INFO accidente sin centro_id, usando empresa={empresa.empresa_sel} y holding={holding.nombre}")

        # 🔍 OBTENER TRABAJADOR - BUSCAR POR MAPEO O POR RUT
        trabajador = None
        trabajador_pk = _get_mapped_id("trabajadores", old_tid)
        
        if trabajador_pk:
            try:
                trabajador = Trabajadores.objects.get(pk=trabajador_pk)
            except Trabajadores.DoesNotExist:
                logs.append(f"[accidentes:{idx}] WARN trabajador pk={trabajador_pk} no existe")
        
        # Si no se encontró por mapeo, buscar por RUT
        if not trabajador:
            rut_trabajador = normalize_rut(r.get("rut_trabajador"))
            if rut_trabajador:
                try:
                    trabajador = Trabajadores.objects.get(rut_trabajador=rut_trabajador)
                    _map_id("trabajadores", old_tid, trabajador.pk)
                    logs.append(f"[accidentes:{idx}] INFO trabajador encontrado por RUT: {rut_trabajador}")
                except Trabajadores.DoesNotExist:
                    logs.append(f"[accidentes:{idx}] WARN trabajador con RUT={rut_trabajador} no existe")
        
        if not trabajador:
            errors.append(f"[accidentes:{idx}] trabajador_id={old_tid} NO encontrado")
            continue

        # 🔍 OBTENER USUARIO - BUSCAR POR MAPEO O POR EMAIL
        usuario_asignado = None
        if old_uid:
            user_pk = _get_mapped_id("users", old_uid)
            if user_pk:
                try:
                    usuario_asignado = User.objects.get(pk=user_pk)
                except User.DoesNotExist:
                    logs.append(f"[accidentes:{idx}] WARN usuario pk={user_pk} no existe")
            
            # Si no se encontró por mapeo, buscar por email
            if not usuario_asignado:
                email_usuario = _safe_text(r.get("email_usuario"), 254, case="lower")
                if email_usuario:
                    try:
                        usuario_asignado = User.objects.get(email=email_usuario)
                        _map_id("users", old_uid, usuario_asignado.pk)
                        logs.append(f"[accidentes:{idx}] INFO usuario encontrado por email: {email_usuario}")
                    except User.DoesNotExist:
                        pass

        codigo = _safe_text(r.get("codigo_accidente"), 100)

        defaults: Dict[str, Any] = {
            "holding": holding,
            "empresa": empresa,
            "centro": centro,
            "trabajador": trabajador,
            "usuario_asignado": usuario_asignado,
            "creado_por": usuario_asignado,
            "actualizado_por": usuario_asignado,
            "fecha_accidente": _parse_iso_date(r.get("fecha_accidente")),
            "hora_accidente": _parse_iso_time(r.get("hora_accidente")),
            "lugar_accidente": _safe_text(r.get("lugar_accidente"), 255, case="title"),
            "tipo_accidente": _safe_text(r.get("tipo_accidente"), 100),
            "naturaleza_lesion": _safe_text(r.get("naturaleza_lesion"), 255, case="title"),
            "parte_afectada": _safe_text(r.get("parte_afectada"), 255, case="title"),
            "tarea": _safe_text(r.get("tarea"), 255, case="title"),
            "operacion": _safe_text(r.get("operacion"), 255, case="title"),
            "danos_personas": _safe_text(r.get("danos_personas"), 2, case="upper"),
            "danos_propiedad": _safe_text(r.get("danos_propiedad"), 2, case="upper"),
            "perdidas_proceso": _safe_text(r.get("perdidas_proceso"), 2, case="upper"),
            "contexto": _safe_text(r.get("contexto")),
            "circunstancias": _safe_text(r.get("circunstancias")),
            "codigo_accidente": codigo,
            "creado_en": _parse_iso_dt(r.get("creado_en")) or timezone.now(),
            "actualizado_en": _parse_iso_dt(r.get("actualizado_en")) or timezone.now(),
        }

        if _model_has_field(Accidentes, "resumen"):
            defaults["resumen"] = _safe_text(r.get("resumen"), 1000)

        try:
            obj, was_created = Accidentes.objects.update_or_create(
                codigo_accidente=codigo,
                defaults=defaults
            )
            
            # 🔑 MAPEAR ID
            _map_id("accidentes", old_aid, obj.pk)

            if was_created:
                created += 1
                logs.append(f"[accidentes:{idx}] CREATED '{codigo}' (old_id={old_aid} -> new_pk={obj.pk})")
            else:
                updated += 1
                logs.append(f"[accidentes:{idx}] UPDATED '{codigo}' (old_id={old_aid} -> new_pk={obj.pk})")

        except Exception as e:
            errors.append(f"[accidentes:{idx}] ERROR -> {e}")

    return created, updated, logs, errors

# ========== ARBOL CAUSAS (CON MAPEO MEJORADO) ==========
def upsert_arbol_causas(records: List[Dict[str, Any]]) -> Tuple[int, int, List[str], List[str]]:
    created = updated = 0
    errors: List[str] = []
    logs: List[str] = []

    supports_fecha = _model_has_field(ArbolCausas, "fecha_registro")

    for idx, r in enumerate(records, 1):
        old_aid = r.get("accidente_id")

        # 🔍 BUSCAR ACCIDENTE - POR MAPEO O POR CÓDIGO
        accidente = None
        accidente_pk = _get_mapped_id("accidentes", old_aid)
        
        if accidente_pk:
            try:
                accidente = Accidentes.objects.get(pk=accidente_pk)
            except Accidentes.DoesNotExist:
                logs.append(f"[arbol_causas:{idx}] WARN accidente pk={accidente_pk} no existe")
        
        # Si no se encontró por mapeo, buscar por código
        if not accidente:
            codigo_accidente = _safe_text(r.get("codigo_accidente"), 100)
            if codigo_accidente:
                try:
                    accidente = Accidentes.objects.get(codigo_accidente=codigo_accidente)
                    _map_id("accidentes", old_aid, accidente.pk)
                    logs.append(f"[arbol_causas:{idx}] INFO accidente encontrado por código: {codigo_accidente}")
                except Accidentes.DoesNotExist:
                    pass
        
        if not accidente:
            errors.append(f"[arbol_causas:{idx}] accidente_id={old_aid} NO encontrado")
            continue

        version = int(r.get("version") or 1)

        defaults: Dict[str, Any] = {
            "accidente": accidente,
            "version": version,
            "is_current": bool(int(r.get("is_current") or 0)),
            "arbol_json_5q": _safe_text(r.get("arbol_json_5q")),
            "arbol_json_dot": _safe_text(r.get("arbol_json_dot")),
        }

        if supports_fecha:
            dt = _parse_iso_dt(r.get("fecha_registro"))
            if dt:
                defaults["fecha_registro"] = dt

        try:
            obj, was_created = ArbolCausas.objects.update_or_create(
                accidente=accidente,
                version=version,
                defaults=defaults
            )

            if was_created:
                created += 1
                logs.append(f"[arbol_causas:{idx}] CREATED version={version}")
            else:
                updated += 1
                logs.append(f"[arbol_causas:{idx}] UPDATED version={version}")

        except Exception as e:
            errors.append(f"[arbol_causas:{idx}] ERROR -> {e}")

    return created, updated, logs, errors

# ========== HECHOS (CON MAPEO MEJORADO) ==========
def upsert_hechos(records: List[Dict[str, Any]]) -> Tuple[int, int, List[str], List[str]]:
    created = updated = 0
    errors: List[str] = []
    logs: List[str] = []

    for idx, r in enumerate(records, 1):
        old_aid = r.get("accidente_id")
        codigo_accidente = r.get("codigo_accidente")

        # 🔍 BUSCAR ACCIDENTE
        accidente = _find_accidente(old_aid, codigo_accidente, idx, logs)
        
        if not accidente:
            errors.append(f"[hechos:{idx}] accidente_id={old_aid} NO encontrado")
            continue

        secuencia = int(r.get("secuencia") or 0)
        defaults = {
            "accidente": accidente,
            "secuencia": secuencia,
            "descripcion": _safe_text(r.get("descripcion")),
        }

        try:
            obj, was_created = Hechos.objects.update_or_create(
                accidente=accidente,
                secuencia=secuencia,
                defaults=defaults
            )

            if was_created:
                created += 1
                logs.append(f"[hechos:{idx}] CREATED sec={secuencia}")
            else:
                updated += 1
                logs.append(f"[hechos:{idx}] UPDATED sec={secuencia}")

        except Exception as e:
            errors.append(f"[hechos:{idx}] ERROR -> {e}")

    return created, updated, logs, errors

# ========== PREGUNTAS GUÍA (CON MAPEO MEJORADO) ==========
def upsert_preguntas_guia(records: List[Dict[str, Any]]) -> Tuple[int, int, List[str], List[str]]:
    created = updated = 0
    errors: List[str] = []
    logs: List[str] = []

    for idx, r in enumerate(records, 1):
        old_aid = r.get("accidente_id")
        codigo_accidente = r.get("codigo_accidente")

        # 🔍 BUSCAR ACCIDENTE
        accidente = _find_accidente(old_aid, codigo_accidente, idx, logs)
        
        if not accidente:
            errors.append(f"[preguntas_guia:{idx}] accidente_id={old_aid} NO encontrado")
            continue

        categoria = _safe_text(r.get("categoria"), 50).lower()
        if categoria not in {"accidentado", "testigos", "supervisores"}:
            categoria = "accidentado"

        defaults = {
            "accidente": accidente,
            "uuid": _safe_text(r.get("uuid") or str(uuid.uuid4()), 36),
            "categoria": categoria,
            "pregunta": _safe_text(r.get("pregunta")),
            "objetivo": _safe_text(r.get("objetivo")),
            "respuesta": _safe_text(r.get("respuesta")),
        }

        try:
            obj, was_created = PreguntasGuia.objects.update_or_create(
                accidente=accidente,
                uuid=defaults["uuid"],
                defaults=defaults
            )

            if was_created:
                created += 1
                logs.append(f"[preguntas_guia:{idx}] CREATED uuid={defaults['uuid'][:8]}")
            else:
                updated += 1
                logs.append(f"[preguntas_guia:{idx}] UPDATED uuid={defaults['uuid'][:8]}")

        except Exception as e:
            errors.append(f"[preguntas_guia:{idx}] ERROR -> {e}")

    return created, updated, logs, errors

# ========== PRESCRIPCIONES (CON MAPEO MEJORADO) ==========
def upsert_prescripciones(records: List[Dict[str, Any]]) -> Tuple[int, int, List[str], List[str]]:
    created = updated = 0
    errors: List[str] = []
    logs: List[str] = []

    for idx, r in enumerate(records, 1):
        old_aid = r.get("accidente_id")
        codigo_accidente = r.get("codigo_accidente")

        # 🔍 BUSCAR ACCIDENTE
        accidente = _find_accidente(old_aid, codigo_accidente, idx, logs)
        
        if not accidente:
            errors.append(f"[prescripciones:{idx}] accidente_id={old_aid} NO encontrado")
            continue

        defaults = {
            "accidente": accidente,
            "tipo": _safe_text(r.get("tipo"), 100, case="title"),
            "prioridad": _safe_text(r.get("prioridad"), 50, case="title"),
            "plazo": _parse_iso_date(r.get("plazo")),
            "responsable": _safe_text(r.get("responsable"), 255, case="title"),
            "descripcion": _safe_text(r.get("descripcion")),
        }

        try:
            obj, was_created = Prescripciones.objects.update_or_create(
                accidente=accidente,
                tipo=defaults["tipo"],
                descripcion=defaults["descripcion"],
                defaults=defaults
            )

            if was_created:
                created += 1
                logs.append(f"[prescripciones:{idx}] CREATED tipo={defaults['tipo']}")
            else:
                updated += 1
                logs.append(f"[prescripciones:{idx}] UPDATED tipo={defaults['tipo']}")

        except Exception as e:
            errors.append(f"[prescripciones:{idx}] ERROR -> {e}")

    return created, updated, logs, errors

# ========== DOCUMENTOS (CON IDS MAPEADOS) ==========
def _guess_ext(nombre_archivo: str, mime_type: str) -> str:
    ext = Path(nombre_archivo).suffix if nombre_archivo else ""
    if ext:
        return ext
    m = (mime_type or "").lower()
    if m == "application/pdf":
        return ".pdf"
    if m in ("image/jpeg", "image/jpg"):
        return ".jpg"
    if m == "image/png":
        return ".png"
    if m == "image/webp":
        return ".webp"
    if m == "image/heic":
        return ".heic"
    if m in ("text/plain", "text/markdown"):
        return ".txt"
    return ""

def _resolve_src_docs_dir(logs: List[str]) -> Path:
    """
    Busca la carpeta de origen de documentos en múltiples ubicaciones.
    Prioriza la carpeta local del proyecto sobre la del contenedor.
    """
    # Calcular ruta relativa desde este archivo
    current_file = Path(__file__).resolve()
    # Subir 2 niveles: carga_datos_json.py -> accidentes/ -> arbol_causa_accidentes_ist/
    project_root = current_file.parent.parent
    local_docs = project_root / "protected_media" / "documentos"
    
    candidates = [
        # 1. PRIORIDAD: Carpeta relativa al archivo actual (funciona local y en contenedor)
        local_docs,
        # 2. Carpeta desde BASE_DIR
        Path(getattr(settings, "BASE_DIR", "/usr/src/app")) / "protected_media" / "documentos",
        # 3. Carpeta del contenedor (ruta absoluta)
        CONTAINER_DOCS_DIR,
    ]
    
    for p in candidates:
        if p and p.exists() and p.is_dir():
            logs.append(f"[documentos] 📂 Origen encontrado -> {p.as_posix()} ({len(list(p.glob('*')))} archivos)")
            return p
    
    logs.append("[documentos] ⚠️  WARN ninguna carpeta de origen existe")
    return local_docs  # Devolver la calculada por defecto

def _index_source_documents(src_dir: Path, logs: List[str]) -> Dict[str, Path]:
    mapping: Dict[str, Path] = {}
    if not src_dir.exists():
        logs.append(f"[documentos] WARN carpeta no existe -> {src_dir.as_posix()}")
        return mapping

    count = 0
    for p in sorted(src_dir.glob("*")):
        if p.is_file():
            mapping[p.stem] = p
            count += 1
    logs.append(f"[documentos] total archivos: {count}")
    return mapping

def _mirror_write_local(bytes_data: bytes, filename: str, logs: List[str]) -> bool:
    """
    Escribe el archivo físicamente SOLO en la carpeta del contenedor.
    Retorna True si se escribió exitosamente, False si hubo error.
    """
    # SOLO escribir en la ruta del contenedor
    container_path = Path("/usr/src/app/protected_media/documentos")
    
    try:
        # Crear directorio si no existe
        container_path.mkdir(parents=True, exist_ok=True)
        
        # Escribir archivo
        output_file = container_path / filename
        output_file.write_bytes(bytes_data)
        
        # Verificar que se escribió correctamente
        if output_file.exists():
            file_size = output_file.stat().st_size
            logs.append(f"[documentos] ✅ Archivo copiado al contenedor -> {output_file} ({file_size:,} bytes)")
            return True
        else:
            logs.append(f"[documentos] ❌ ERROR: Archivo no se creó -> {output_file}")
            return False
            
    except Exception as e:
        logs.append(f"[documentos] ❌ ERROR escribiendo en {container_path}: {e}")
        return False

def upsert_documentos(records: List[Dict[str, Any]]) -> Tuple[int, int, List[str], List[str]]:
    created = updated = 0
    errors: List[str] = []
    logs: List[str] = []

    src_dir = _resolve_src_docs_dir(logs)
    index = _index_source_documents(src_dir, logs)

    for idx, r in enumerate(records, 1):
        old_aid = r.get("accidente_id")
        codigo_accidente = r.get("codigo_accidente")

        # 🔍 BUSCAR ACCIDENTE
        accidente = _find_accidente(old_aid, codigo_accidente, idx, logs)
        
        if not accidente:
            errors.append(f"[documentos:{idx}] accidente_id={old_aid} NO encontrado")
            continue

        doc_id_str = str(r.get("documento_id") or "").strip()
        if not doc_id_str:
            errors.append(f"[documentos:{idx}] documento_id vacío")
            continue

        nombre_archivo = _safe_text(r.get("nombre_archivo"), 255)
        mime_type = _safe_text(r.get("mime_type"), 100)

        defaults = {
            "accidente": accidente,
            "documento": _safe_text(r.get("documento")),
            "objetivo": _safe_text(r.get("objetivo")),
            "nombre_archivo": nombre_archivo,
            "mime_type": mime_type,
            "subido_el": _parse_iso_dt(r.get("subido_el")) or timezone.now(),
            "url": _safe_text(r.get("url"), 2048),
        }

        # 📁 COPIAR ARCHIVO FÍSICO AL CONTENEDOR (siempre, incluso si existe en BD)
        src_file = index.get(doc_id_str)
        archivo_copiado = False
        
        if src_file and src_file.exists():
            try:
                # Leer archivo desde origen (local o contenedor)
                bytes_data = src_file.read_bytes()
                logs.append(f"[documentos:{idx}] 📄 Archivo leído -> {src_file.name} ({len(bytes_data):,} bytes)")
                
                # ❌ NO guardar en BD (columna contenido LONGBLOB)
                # defaults["contenido"] = bytes_data  # ← COMENTADO: No subir a LONGBLOB
                
                # ✅ COPIAR archivo físico al contenedor (SIEMPRE)
                ext = src_file.suffix or _guess_ext(nombre_archivo, mime_type)
                filename_with_ext = f"{doc_id_str}{ext}"
                archivo_copiado = _mirror_write_local(bytes_data, filename_with_ext, logs)
                
                if archivo_copiado:
                    logs.append(f"[documentos:{idx}] ✅ Procesado correctamente (BD + Disco)")
                else:
                    logs.append(f"[documentos:{idx}] ⚠️  Guardado en BD, pero ERROR copiando archivo físico")
                    
            except Exception as e:
                errors.append(f"[documentos:{idx}] ❌ ERROR procesando archivo -> {e}")
                logs.append(f"[documentos:{idx}] Continuando con registro en BD sin archivo físico")
        else:
            # Archivo no encontrado en origen
            if doc_id_str in index:
                logs.append(f"[documentos:{idx}] ⚠️  Archivo en índice pero no existe -> {doc_id_str}")
            else:
                logs.append(f"[documentos:{idx}] ⚠️  Archivo no encontrado en origen -> {doc_id_str}")
            errors.append(f"[documentos:{idx}] WARN documento sin archivo físico -> {doc_id_str}")

        try:
            # 🔑 documento_id es la clave primaria, debe usarse en el lookup
            obj, was_created = Documentos.objects.update_or_create(
                documento_id=doc_id_str,
                defaults=defaults
            )

            if was_created:
                created += 1
                logs.append(f"[documentos:{idx}] CREATED '{nombre_archivo}'")
            else:
                updated += 1
                logs.append(f"[documentos:{idx}] UPDATED '{nombre_archivo}'")

        except Exception as e:
            errors.append(f"[documentos:{idx}] ERROR guardando en BD -> {e}")

    return created, updated, logs, errors

# ========== RELATOS (CON MAPEO) ==========
def upsert_relatos(accidentes_records: list) -> tuple:
    """
    Inserta relatos asociados a accidentes. Extrae los campos del JSON y crea el Relato si hay texto en 'relato' o 'preinitial_story'.
    """
    created = updated = 0
    errors = []
    logs = []
    for idx, r in enumerate(accidentes_records, 1):
        relato_text = r.get("relato")
        preinitial_story = r.get("preinitial_story")
        # Solo crear si hay relato o preinitial_story
        if not relato_text and not preinitial_story:
            continue
        old_aid = r.get("accidente_id")
        accidente_pk = _get_mapped_id("accidentes", old_aid)
        if not accidente_pk:
            errors.append(f"[relatos:{idx}] No se encontró accidente para old_id={old_aid}")
            continue
        try:
            accidente = Accidentes.objects.get(pk=accidente_pk)
        except Accidentes.DoesNotExist:
            errors.append(f"[relatos:{idx}] Accidente pk={accidente_pk} no existe")
            continue
        # Generar UUID
        relato_id = uuid.uuid4()
        # Crear o actualizar (solo uno por accidente, is_current=True)
        obj, was_created = Relato.objects.update_or_create(
            accidente=accidente,
            is_current=True,
            defaults={
                "relato_id": relato_id,
                "relato_inicial": preinitial_story,
                "relato_final": relato_text,
                # El resto de campos quedan en None
            }
        )
        if was_created:
            created += 1
            logs.append(f"[relatos:{idx}] CREATED para accidente {accidente.codigo_accidente}")
        else:
            updated += 1
            logs.append(f"[relatos:{idx}] UPDATED para accidente {accidente.codigo_accidente}")
    return created, updated, logs, errors

# ========== ORQUESTACIÓN PRINCIPAL ==========
@transaction.atomic
def run(json_path: Union[str, Path] = DEFAULT_JSON_PATH) -> Dict[str, Any]:
    print("\n" + "🚀 " * 30)
    print("INICIANDO CARGA DE DATOS CON MAPEO DE IDs")
    print("🔇 Signals desactivadas temporalmente (no se enviarán correos)")
    print("🚀 " * 30 + "\n")

    # Desactivar signals temporalmente para evitar envío de correos durante la carga
    # Importar los receivers específicos del módulo signals
    from accidentes.signals import _pre_save_mark_first_assignment, _post_save_send_assignment_email
    
    pre_save.disconnect(_pre_save_mark_first_assignment, sender=Accidentes)
    post_save.disconnect(_post_save_send_assignment_email, sender=Accidentes)

    try:
        # Limpiar mapeos anteriores
        _clear_mappings()

        data = _read_json(json_path)
        
        # 🔧 PRE-PROCESAMIENTO: Asignar empresa_id y holding_id a accidentes (sin tocar centro_id)
        data = _preprocess_accidentes_assign_empresa_holding(data)
        
        res: Dict[str, Any] = {"json_path": str(json_path)}

        def log_summary(entity: str, processed: int, created: int, updated: int, errors: List[str]) -> str:
            msg = (
                f"\n{'=' * 60}\n"
                f"📊 {entity.upper()}\n"
                f"{'=' * 60}\n"
                f"  Procesados: {processed}\n"
                f"  ✅ Creados: {created}\n"
                f"  🔄 Actualizados: {updated}\n"
                f"  ❌ Errores: {len(errors)}"
            )
            if errors:
                msg += f"\n\n  Primeros errores:\n"
                for err in errors[:3]:
                    msg += f"    • {err}\n"
                if len(errors) > 3:
                    msg += f"    ... y {len(errors) - 3} más\n"
            msg += f"{'=' * 60}\n"
            return msg

        # 1. HOLDINGS
        recs = _take_list(data, "holdings")
        c, u, logs, errs = upsert_holdings(recs)
        res.update({"holdings_processed": len(recs), "holdings_created": c, "holdings_updated": u, "holdings_errors": errs})
        print(log_summary("HOLDINGS", len(recs), c, u, errs))

        # 2. EMPRESAS
        recs = _take_list(data, "empresas")
        c, u, logs, errs = upsert_empresas(recs)
        res.update({"empresas_processed": len(recs), "empresas_created": c, "empresas_updated": u, "empresas_errors": errs})
        print(log_summary("EMPRESAS", len(recs), c, u, errs))

        # 3. CENTROS
        recs = _take_list(data, "centros_trabajo")
        c, u, logs, errs = upsert_centros(recs)
        res.update({"centros_processed": len(recs), "centros_created": c, "centros_updated": u, "centros_errors": errs})
        print(log_summary("CENTROS DE TRABAJO", len(recs), c, u, errs))

        # 4. TRABAJADORES
        recs = _take_list(data, "trabajadores")
        c, u, logs, errs = upsert_trabajadores(recs)
        res.update({"trabajadores_processed": len(recs), "trabajadores_created": c, "trabajadores_updated": u, "trabajadores_errors": errs})
        print(log_summary("TRABAJADORES", len(recs), c, u, errs))

        # 5. USUARIOS
        recs = _take_list(data, "usuarios")
        if recs:
            c, u, logs, errs = upsert_usuarios(recs)
            res.update({"usuarios_processed": len(recs), "usuarios_created": c, "usuarios_updated": u, "usuarios_errors": errs})
            print(log_summary("USUARIOS (AUTH)", len(recs), c, u, errs))

        # 6. ACCIDENTES
        recs = _take_list(data, "accidentes")
        c, u, logs, errs = upsert_accidentes(recs)
        res.update({"accidentes_processed": len(recs), "accidentes_created": c, "accidentes_updated": u, "accidentes_errors": errs})
        print(log_summary("ACCIDENTES", len(recs), c, u, errs))

        # 6b. RELATOS
        c, u, logs, errs = upsert_relatos(recs)
        res.update({"relatos_processed": len(recs), "relatos_created": c, "relatos_updated": u, "relatos_errors": errs})
        print(log_summary("RELATOS", len(recs), c, u, errs))

        # 7. ÁRBOL CAUSAS
        recs = _take_list(data, "arbol_causas")
        c, u, logs, errs = upsert_arbol_causas(recs)
        res.update({"arbol_causas_processed": len(recs), "arbol_causas_created": c, "arbol_causas_updated": u, "arbol_causas_errors": errs})
        print(log_summary("ÁRBOL DE CAUSAS", len(recs), c, u, errs))

        # 8. HECHOS
        recs = _take_list(data, "hechos")
        c, u, logs, errs = upsert_hechos(recs)
        res.update({"hechos_processed": len(recs), "hechos_created": c, "hechos_updated": u, "hechos_errors": errs})
        print(log_summary("HECHOS", len(recs), c, u, errs))

        # 9. PREGUNTAS GUÍA
        recs = _take_list(data, "preguntas_guia")
        c, u, logs, errs = upsert_preguntas_guia(recs)
        res.update({"preguntas_guia_processed": len(recs), "preguntas_guia_created": c, "preguntas_guia_updated": u, "preguntas_guia_errors": errs})
        print(log_summary("PREGUNTAS GUÍA", len(recs), c, u, errs))

        # 10. PRESCRIPCIONES
        recs = _take_list(data, "prescripciones")
        c, u, logs, errs = upsert_prescripciones(recs)
        res.update({"prescripciones_processed": len(recs), "prescripciones_created": c, "prescripciones_updated": u, "prescripciones_errors": errs})
        print(log_summary("PRESCRIPCIONES", len(recs), c, u, errs))

        # 11. DOCUMENTOS
        recs = _take_list(data, "documentos")
        c, u, logs, errs = upsert_documentos(recs)
        res.update({"documentos_processed": len(recs), "documentos_created": c, "documentos_updated": u, "documentos_errors": errs})
        print(log_summary("DOCUMENTOS", len(recs), c, u, errs))

        print("\n" + "✅ " * 30)
        print("CARGA COMPLETADA")
        print("✅ " * 30 + "\n")

        # Mostrar mapeo de IDs (primeros 5 por entidad)
        print("\n📋 MAPEO DE IDs (primeros 5 por entidad):")
        for entity, mapping in ID_MAPPING.items():
            if mapping:
                items = list(mapping.items())[:5]
                print(f"\n  {entity.upper()}:")
                for old_id, new_pk in items:
                    print(f"    {old_id} -> {new_pk}")
                if len(mapping) > 5:
                    print(f"    ... y {len(mapping) - 5} más")

        # 🔒 SEGURIDAD: Borrar archivo JSON con datos sensibles después de la carga
        try:
            import shutil
            
            json_file = Path(json_path)
            
            # Si es ruta relativa, intentar construir ruta absoluta desde diferentes bases
            if not json_file.is_absolute():
                # Intentar desde el directorio actual
                if json_file.exists():
                    pass  # Ya existe con la ruta relativa
                else:
                    # Intentar desde /usr/src/app (contenedor)
                    container_path = Path("/usr/src/app") / json_file
                    if container_path.exists():
                        json_file = container_path
                    else:
                        # Intentar desde settings.BASE_DIR
                        try:
                            base_dir = Path(settings.BASE_DIR)
                            settings_path = base_dir / json_file
                            if settings_path.exists():
                                json_file = settings_path
                        except Exception:
                            pass
            
            # Verificar existencia
            if json_file.exists():
                # Verificar que no sea un archivo de ejemplo/demo
                if "demo" not in json_file.name.lower() and "example" not in json_file.name.lower():
                    # Verificar si es archivo o directorio (bug extraño donde data.json es directorio)
                    if json_file.is_file():
                        json_file.unlink()
                        print(f"\n🔒 SEGURIDAD: Archivo JSON eliminado -> {json_file}")
                        print("   (Contiene datos sensibles y ya fue procesado)")
                    elif json_file.is_dir():
                        # Caso extraño: data.json es un directorio, eliminarlo recursivamente
                        shutil.rmtree(json_file)
                        print(f"\n🔒 SEGURIDAD: Directorio JSON eliminado -> {json_file}")
                        print("   ⚠️  ADVERTENCIA: data.json era un DIRECTORIO, no un archivo")
                        print("   (Contenía datos sensibles y ya fue procesado)")
                    else:
                        print(f"\n⚠️  Ruta existe pero no es archivo ni directorio -> {json_file}")
                else:
                    print(f"\n⚠️  Archivo demo/ejemplo no eliminado -> {json_file}")
            else:
                print(f"\n⚠️  Archivo JSON no encontrado para eliminar -> {json_file}")
                print(f"   Ruta buscada: {json_file.absolute()}")
        except Exception as e:
            print(f"\n⚠️  No se pudo eliminar el archivo JSON: {e}")
            import traceback
            print(f"   Detalle del error:\n{traceback.format_exc()}")

        return res

    finally:
        # Reactivar signals
        print("\n🔔 Reactivando signals...")
        pre_save.connect(_pre_save_mark_first_assignment, sender=Accidentes)
        post_save.connect(_post_save_send_assignment_email, sender=Accidentes)


if __name__ == "__main__":
    result = run(DEFAULT_JSON_PATH)
    print("\n" + json.dumps(result, ensure_ascii=False, indent=2))