# adminpanel/utils/access.py (nuevo)
from django.db.models import Q
from accidentes.models import Holdings, Empresas, Trabajadores
from django.contrib.auth import get_user_model
from accidentes.access import scope_accidentes_q

User = get_user_model()
SUPER_ROLES = {"admin", "admin_ist"}

def holdings_permitidos(user):
    rol = getattr(user, "rol", None)
    if rol in SUPER_ROLES:
        return Holdings.objects.all().order_by("nombre")
    if rol == "admin_holding":
        return Holdings.objects.filter(pk=getattr(user, "holding_id", None))
    if rol == "admin_empresa":
        # por seguridad, limita al holding de su empresa si existe
        return Holdings.objects.filter(pk=getattr(user, "holding_id", None))
    return Holdings.objects.none()

def empresas_permitidas(user, *, holding_id=None):
    """Empresas visibles para el user (opcionalmente dentro de holding_id)."""
    qs = Empresas.objects.all()
    rol = getattr(user, "rol", None)
    if rol in SUPER_ROLES:
        if holding_id:
            qs = qs.filter(holding_id=holding_id)
        return qs.order_by("empresa_sel")

    if rol == "admin_holding":
        hid = holding_id or getattr(user, "holding_id", None)
        return qs.filter(holding_id=hid).order_by("empresa_sel")

    if rol == "admin_empresa":
        eid = getattr(user, "empresa_id", None)
        return qs.filter(pk=eid)

    return qs.none()

def usuarios_permitidos_para_asignar(
    user, *, empresa_id=None, holding_id=None, force_empresa_for_creation=False
):
    """
    Usuarios asociables a un accidente según rol.
    En creación: si force_empresa_for_creation=True -> filtra SIEMPRE por empresa_id,
    salvo super-roles.
    """
    rol = getattr(user, "rol", None)
    qs = User.objects.all()

    if rol in SUPER_ROLES:
        # Excepción: super-roles pueden ver todos (no se fuerza empresa)
        if holding_id:
            qs = qs.filter(holding_id=holding_id)
        return qs.order_by("first_name", "last_name", "username")

    if rol == "admin_holding":
        hid = holding_id or getattr(user, "holding_id", None)
        qs = qs.filter(holding_id=hid, rol__in=["admin_holding", "admin_empresa", "investigador"])
        if force_empresa_for_creation and empresa_id:
            qs = qs.filter(empresa_id=empresa_id)  # regla extra
        return qs.order_by("first_name", "last_name", "username")

    if rol == "admin_empresa":
        eid = getattr(user, "empresa_id", None)
        qs = qs.filter(empresa_id=eid, rol__in=["admin_empresa", "investigador"])
        if force_empresa_for_creation and empresa_id and empresa_id != eid:
            # si la empresa seleccionada no coincide, deja vacío
            return User.objects.none()
        return qs.order_by("first_name", "last_name", "username")

    return User.objects.none()

def trabajadores_permitidos(
    user, *, empresa_id=None, holding_id=None, force_empresa_for_creation=True
):
    """
    Trabajadores asociables a un accidente según rol.
    En creación: si force_empresa_for_creation=True -> filtra SIEMPRE por empresa_id,
    salvo super-roles.
    """
    rol = getattr(user, "rol", None)
    qs = Trabajadores.objects.select_related("empresa")

    if rol in SUPER_ROLES:
        # Excepción: super-roles pueden ver todos (no se fuerza empresa)
        if holding_id:
            qs = qs.filter(empresa__holding_id=holding_id)
        if force_empresa_for_creation and empresa_id:
            # si aún así quieres “ayudar” UX, quita esta línea; por la regla, super-roles NO se limitan
            pass
        return qs

    if rol == "admin_holding":
        hid = holding_id or getattr(user, "holding_id", None)
        qs = qs.filter(empresa__holding_id=hid)
        if force_empresa_for_creation:
            qs = qs.filter(empresa_id=empresa_id) if empresa_id else qs.none()
        return qs

    if rol == "admin_empresa":
        eid = getattr(user, "empresa_id", None)
        qs = qs.filter(empresa_id=eid)
        if force_empresa_for_creation and empresa_id and empresa_id != eid:
            return Trabajadores.objects.none()
        return qs

    return Trabajadores.objects.none()