# adminpanel/utils/assignments.py
from django.contrib.auth import get_user_model

User = get_user_model()

__all__ = ["usuarios_permitidos_para_asignar"]

def usuarios_permitidos_para_asignar(
    asignador,
    *,
    empresa=None,
    empresa_id=None,
    holding=None,
    holding_id=None,
):
    """
    Devuelve un queryset de usuarios que el 'asignador' puede asignar, aplicando
    restricciones por rol + pertenencia a empresa/holding.
    Admite tanto objetos como IDs (empresa / empresa_id, holding / holding_id).
    """

    # Normaliza IDs
    e_id = None
    if empresa_id:
        e_id = int(empresa_id)
    elif empresa is not None:
        # soporta .pk o .empresa_id
        e_id = getattr(empresa, "pk", None) or getattr(empresa, "empresa_id", None)

    h_id = None
    if holding_id:
        h_id = int(holding_id)
    elif holding is not None:
        h_id = getattr(holding, "pk", None) or getattr(holding, "holding_id", None)

    role = getattr(asignador, "rol", None)
    qs = User.objects.all()

    # Super-roles: acceso total
    if role in ("admin", "admin_ist"):
        return qs.order_by("first_name", "last_name", "username")

    # Admin Holding: restringe por holding y roles permitidos
    if role == "admin_holding":
        if not h_id:
            h_id = getattr(asignador, "holding_id", None)
        if h_id:
            qs = qs.filter(holding_id=h_id)
        qs = qs.filter(rol__in=["admin_holding", "admin_empresa", "investigador"])
        return qs.order_by("first_name", "last_name", "username")

    # Admin Empresa: restringe por empresa y roles permitidos
    if role == "admin_empresa":
        if not e_id:
            e_id = getattr(asignador, "empresa_id", None)
        if e_id:
            qs = qs.filter(empresa_id=e_id)
        qs = qs.filter(rol__in=["admin_empresa", "investigador"])
        return qs.order_by("first_name", "last_name", "username")

    # Investigadores no asignan
    return User.objects.none()
