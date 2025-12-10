# accidentes/permissions.py
def puede_crear_accidente(user, empresa):
    if user.rol in ("admin", "admin_ist"):
        return True
    if user.rol == "admin_holding":
        return empresa.holding_id == user.holding_id
    if user.rol == "admin_empresa":
        return empresa.empresa_id == user.empresa_id
    return False