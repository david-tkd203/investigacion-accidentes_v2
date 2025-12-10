# adminpanel/templatetags/adminpanel_extras.py
from django import template
from adminpanel.permissions import ADMIN_ROLES  # usa tu set centralizado

register = template.Library()

@register.filter
def has_admin_access(user):
    """Devuelve True si el usuario puede ver/entrar al AdminPanel."""
    if not getattr(user, "is_authenticated", False):
        return False
    return getattr(user, "rol", None) in ADMIN_ROLES
