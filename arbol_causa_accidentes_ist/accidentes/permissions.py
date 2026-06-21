# accidentes/permissions.py
from .constants import ROLE_SUPER_ADMIN, ROLE_ADMIN_IST, ROLE_ADMIN_HOLDING, ROLE_ADMIN_EMPRESA

def puede_crear_accidente(user, empresa):
    if user.rol in (ROLE_SUPER_ADMIN, ROLE_ADMIN_IST):
        return True
    if user.rol == ROLE_ADMIN_HOLDING:
        return empresa.holding_id == user.holding_id
    if user.rol == ROLE_ADMIN_EMPRESA:
        return empresa.empresa_id == user.empresa_id
    return False