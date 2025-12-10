# adminpanel/mixins.py
from adminpanel.utils.access import scope_accidentes_q
from accidentes.access import scope_accidentes_q

class ScopedAccidenteQuerysetMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(scope_accidentes_q(self.request.user))
