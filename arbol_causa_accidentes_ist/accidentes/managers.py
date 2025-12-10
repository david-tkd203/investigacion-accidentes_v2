from django.db import models

class AccidentesQuerySet(models.QuerySet):
    def visibles_para(self, user):
        # Un único punto de verdad
        from .access import scope_accidentes_q
        return self.filter(scope_accidentes_q(user))

class AccidentesManager(models.Manager.from_queryset(AccidentesQuerySet)):
    pass