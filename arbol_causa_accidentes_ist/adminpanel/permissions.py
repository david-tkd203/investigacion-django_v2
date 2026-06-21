# adminpanel/permissions.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from accidentes.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN_IST, ROLE_ADMIN_HOLDING, ROLE_ADMIN_EMPRESA, ROLE_COORDINADOR

ADMIN_ROLES = {ROLE_SUPER_ADMIN, ROLE_ADMIN_IST, ROLE_ADMIN_HOLDING, ROLE_ADMIN_EMPRESA, ROLE_COORDINADOR}

class AdminPanelAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return getattr(user, "rol", None) in ADMIN_ROLES
