# accidentes/constants.py
# Role string constants — no Django model imports, safe to import anywhere.

ROLE_SUPER_ADMIN = "admin"
ROLE_ADMIN_IST = "admin_ist"
ROLE_ADMIN_HOLDING = "admin_holding"
ROLE_ADMIN_EMPRESA = "admin_empresa"
ROLE_COORDINADOR = "coordinador"
ROLE_INVESTIGADOR = "investigador"
ROLE_INVESTIGADOR_IST = "investigador_ist"

SUPER_ROLES = {ROLE_SUPER_ADMIN, ROLE_ADMIN_IST, ROLE_INVESTIGADOR_IST}

ROL_CHOICES = [
    (ROLE_SUPER_ADMIN, "Admin Global"),
    (ROLE_ADMIN_IST, "Admin IST"),
    (ROLE_ADMIN_HOLDING, "Admin Holding"),
    (ROLE_ADMIN_EMPRESA, "Admin Empresa"),
    (ROLE_COORDINADOR, "Coordinador"),
    (ROLE_INVESTIGADOR, "Investigador"),
    (ROLE_INVESTIGADOR_IST, "Investigador IST"),
]

TEAM_CHOICES = [
    ("staff", "Staff IST"),
    ("adherente", "Adherente"),
]

ERROR_CASO_NO_DISPONIBLE = "Caso no disponible."
ERROR_ACCESO_DENEGADO = "Acceso denegado: debes estar asignado a este accidente."
