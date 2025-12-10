# accidentes/access.py
from django.shortcuts import get_object_or_404
from typing import Optional
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Accidentes, Empresas, Holdings, Trabajadores
from django.core.exceptions import PermissionDenied
import logging
logger = logging.getLogger(__name__)


SUPER_ROLES = {"admin", "admin_ist", "investigador_ist"}

# Defino alcance común para todos los lugares donde vaya a listar un accidente, davisino, no toques esto jaja
def scope_accidentes_q(user) -> Q:
    rol = getattr(user, "rol", None)
    if rol in SUPER_ROLES:
        return Q()
    if rol == "admin_holding":
        return Q(holding_id=getattr(user, "holding_id", None))
    if rol in {"admin_empresa", "investigador"}:
        return Q(empresa_id=getattr(user, "empresa_id", None))
    # fallback: solo asignados
    return Q(usuario_asignado_id=getattr(user, "id", None))

# Helpers 

def get_accidente_scoped_or_404(user, codigo, select_related=()):
    from accidentes.models import Accidentes

    qs = Accidentes.objects.visibles_para(user)
    if select_related:
        qs = qs.select_related(*select_related)

    acc = get_object_or_404(qs, codigo_accidente=codigo)

    rol = getattr(user, "rol", None)

    if rol == "investigador_ist":
        # Única regla: debe estar asignado. No validar empresa/holding.
        asignado = (acc.usuario_asignado_id == getattr(user, "id", None))
        if not asignado:
            logger.info(
                "Acceso denegado (investigador_ist sin asignación) user=%s acc=%s cod=%s",
                getattr(user, "id", None), getattr(acc, "pk", None), codigo
            )
            raise PermissionDenied("Acceso denegado: debes estar asignado a este accidente.")
        return acc

    if rol == "investigador":
        # Para investigador normal, ya vienes acotado por empresa desde visibles_para(user);
        # además, exigimos asignación.
        asignado = (acc.usuario_asignado_id == getattr(user, "id", None))
        if not asignado:
            logger.info(
                "Acceso denegado (investigador sin asignación) user=%s acc=%s cod=%s",
                getattr(user, "id", None), getattr(acc, "pk", None), codigo
            )
            raise PermissionDenied("Acceso denegado: debes estar asignado a este accidente.")
        return acc

    # Otros roles: se mantienen como estaban (admin/admin_ist/admin_holding/admin_empresa, etc.)
    return acc


def scope_empresas_q(user) -> Q:
    rol = getattr(user, "rol", None)
    if rol in {"admin", "admin_ist", "investigador_ist"}:
        return Q()
    if rol == "admin_holding":
        return Q(holding_id=getattr(user, "holding_id", None))
    if rol in {"admin_empresa", "investigador"}:
        return Q(pk=getattr(user, "empresa_id", None))
    # investigadores sin empresa: no ven nada global
    return Q(pk__in=[])

def empresa_en_alcance(user, empresa_id, *, session_accidente_id=None) -> bool:
    try:
        eid = int(empresa_id)
    except (TypeError, ValueError):
        return False

    # si hay accidente en sesión, prioriza coherencia
    if session_accidente_id:
        try:
            acc = Accidentes.objects.get(pk=int(session_accidente_id))
            if acc.empresa_id:
                return acc.empresa_id == eid
        except Exception:
            pass

    # si no hay sesión o no tiene empresa, usa alcance general por rol
    return Empresas.objects.filter(pk=eid).filter(scope_empresas_q(user)).exists()


# ---------- utilidades internas para leer asignaciones del usuario ----------
def _safe_ids_from_attr(obj, attr_name: str):
    try:
        val = getattr(obj, attr_name, None)
        if val is None:
            return []
        if isinstance(val, int):
            return [val]
        if hasattr(val, "pk"):
            return [val.pk]
    except Exception:
        pass
    return []

def _safe_ids_from_m2m(obj, attr_name: str):
    try:
        rel = getattr(obj, attr_name, None)
        if hasattr(rel, "values_list"):
            return list(rel.values_list("pk", flat=True))
    except Exception:
        pass
    return []

def _user_empresa_ids(user):
    ids = []
    ids += _safe_ids_from_attr(user, "empresa_id")
    ids += _safe_ids_from_attr(user, "empresa")
    ids += _safe_ids_from_m2m(user, "empresas")
    if not ids:
        # Fallback consistente: empresas que aparecen en su universo de accidentes
        ids = list(
            Accidentes.objects.visibles_para(user).values_list("empresa_id", flat=True).distinct()
        )
    return [i for i in ids if i]

def _user_holding_ids(user):
    ids = []
    ids += _safe_ids_from_attr(user, "holding_id")
    ids += _safe_ids_from_attr(user, "holding")
    ids += _safe_ids_from_m2m(user, "holdings")
    if not ids:
        emp_ids = _user_empresa_ids(user)
        if emp_ids:
            ids = list(
                Empresas.objects.filter(pk__in=emp_ids)
                .values_list("holding_id", flat=True).distinct()
            )
    if not ids:
        ids = list(
            Accidentes.objects.visibles_para(user).values_list("holding_id", flat=True).distinct()
        )
    return [i for i in ids if i]

# ---------- alcance por holdings / empresas / trabajadores / usuarios ----------
def holdings_permitidos(user):
    """Holdings dentro del alcance del usuario."""
    if getattr(user, "rol", None) in SUPER_ROLES:
        return Holdings.objects.all()
    ids = _user_holding_ids(user)
    return Holdings.objects.filter(pk__in=ids) if ids else Holdings.objects.none()

def empresas_permitidas(user, holding_id: Optional[int] = None):
    """Empresas dentro del alcance del usuario. Opcionalmente filtra por holding_id."""
    if getattr(user, "rol", None) in SUPER_ROLES:
        qs = Empresas.objects.all()
    else:
        emp_ids = _user_empresa_ids(user)
        if emp_ids:
            qs = Empresas.objects.filter(pk__in=emp_ids)
        else:
            hids = _user_holding_ids(user)
            qs = Empresas.objects.filter(holding_id__in=hids) if hids else Empresas.objects.none()
    if holding_id:
        qs = qs.filter(holding_id=holding_id)
    return qs

def trabajadores_permitidos(user, empresa_id: Optional[int] = None, *, force_empresa_for_creation: bool = False):
    """
    Trabajadores dentro del alcance.
    - Si 'empresa_id' viene, valida que esa empresa esté en alcance y restringe por ella.
    - Si 'force_empresa_for_creation' es True y no se especifica empresa (pantallas de creación),
      devuelve none() para roles no-super (para no abrir demasiado el universo).
    """
    if getattr(user, "rol", None) in SUPER_ROLES:
        base = Trabajadores.objects.all()
    else:
        emp_qs = empresas_permitidas(user)
        base = Trabajadores.objects.filter(empresa_id__in=emp_qs.values("pk"))

    if empresa_id:
        if not empresas_permitidas(user).filter(pk=empresa_id).exists():
            return Trabajadores.objects.none()
        base = base.filter(empresa_id=empresa_id)
    else:
        if force_empresa_for_creation and getattr(user, "rol", None) not in SUPER_ROLES:
            return Trabajadores.objects.none()

    return base

def usuarios_permitidos_para_asignar(user, empresa_id: Optional[int] = None, *, force_empresa_for_creation: bool = False):
    """
    Usuarios que se pueden asignar como investigadores/gestores, respetando el alcance del solicitante.
    - Intenta acotar por empresa/holding si tu modelo de User tiene esos campos (empresa, empresas, holding, holdings).
    - Si 'empresa_id' viene, filtra adicionalmente a esa empresa (cuando sea posible mapear).
    """
    U = get_user_model()

    ASSIGNABLE_ROLES = {"investigador", "investigador_ist", "admin_empresa", "admin_holding", "admin", "admin_ist"}

    if getattr(user, "rol", None) in SUPER_ROLES:
        qs = U.objects.filter(is_active=True)
    else:
        qs = U.objects.filter(is_active=True)
        # Limita por roles si existe el campo 'rol'
        try:
            U._meta.get_field("rol")
            qs = qs.filter(rol__in=ASSIGNABLE_ROLES)
        except Exception:
            pass

        # Acota por universo de empresas/holdings permitidos del solicitante (si el esquema de User lo permite)
        emp_ids = set(empresas_permitidas(user).values_list("pk", flat=True))
        hold_ids = set(holdings_permitidos(user).values_list("pk", flat=True))

        q_scope = Q()
        if any(f.name == "empresa" for f in U._meta.fields):
            q_scope |= Q(empresa_id__in=emp_ids)
        if any(r.name == "empresas" for r in U._meta.many_to_many):
            q_scope |= Q(empresas__pk__in=list(emp_ids))
        if any(f.name == "holding" for f in U._meta.fields):
            q_scope |= Q(holding_id__in=hold_ids)
        if any(r.name == "holdings" for r in U._meta.many_to_many):
            q_scope |= Q(holdings__pk__in=list(hold_ids))

        if q_scope:
            qs = qs.filter(q_scope).distinct()

    # Filtro extra por empresa destino (si se proporciona)
    if empresa_id:
        # primero valida que la empresa esté en alcance del solicitante
        if not empresas_permitidas(user).filter(pk=empresa_id).exists():
            return U.objects.none()

        q_emp = Q()
        if any(f.name == "empresa" for f in U._meta.fields):
            q_emp |= Q(empresa_id=empresa_id)
        if any(r.name == "empresas" for r in U._meta.many_to_many):
            q_emp |= Q(empresas__pk=empresa_id)

        if q_emp:
            if getattr(user, "rol", None) in SUPER_ROLES:
                # ⬇️ Súper (admin/admin_ist/investigador_ist): permitir SIEMPRE investigador_ist,
                # aun sin relación empresa/holding.
                qs = qs.filter(q_emp) | qs.filter(rol="investigador_ist")
                qs = qs.distinct()
            else:
                qs = qs.filter(q_emp).distinct()
        # si tu User no tiene vínculo con empresa, dejamos qs como está
    else:
        if force_empresa_for_creation and getattr(user, "rol", None) not in SUPER_ROLES:
            return U.objects.none()


    return qs

# ---------- helper simple para vistas AJAX (usado ya en accidentes/views.py) ----------
def empresa_en_alcance(user, empresa_id, *, session_accidente_id: Optional[int] = None) -> bool:
    """
    True si la empresa está en el alcance del usuario.
    (Opcionalmente: si hay un accidente en sesión, permite la empresa del accidente aunque
    no venga en empresas_permitidas por algún edge-case de datos.)
    """
    try:
        eid = int(empresa_id) if empresa_id is not None else None
    except (TypeError, ValueError):
        return False
    if eid is None:
        return False

    if empresas_permitidas(user).filter(pk=eid).exists():
        return True

    if session_accidente_id:
        return Accidentes.objects.visibles_para(user).filter(pk=session_accidente_id, empresa_id=eid).exists()

    return False
