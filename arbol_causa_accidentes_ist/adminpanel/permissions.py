# adminpanel/permissions.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

ADMIN_ROLES = {"admin", "admin_ist", "admin_holding", "admin_empresa", "coordinador"}

class AdminPanelAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return getattr(user, "rol", None) in ADMIN_ROLES
