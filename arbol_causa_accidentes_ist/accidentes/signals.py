import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Accidentes  # ajusta si tu clase se llama distinto
from core.services.mailers import send_case_assigned_email

logger = logging.getLogger(__name__)

ASIGNADO_FIELD = "usuario_asignado"  # ← FK al User

@receiver(pre_save, sender=Accidentes)
def _pre_save_mark_first_assignment(sender, instance, **kwargs):
    new_user = getattr(instance, ASIGNADO_FIELD, None)
    new_id = getattr(new_user, "id", None)

    if instance.pk is None:
        instance._notify_first_assignment = bool(new_id)
    else:
        try:
            old_id = type(instance).objects.only(f"{ASIGNADO_FIELD}_id") \
                                     .values_list(f"{ASIGNADO_FIELD}_id", flat=True) \
                                     .get(pk=instance.pk)
        except type(instance).DoesNotExist:
            old_id = None
        instance._notify_first_assignment = (old_id is None and new_id is not None)

@receiver(post_save, sender=Accidentes)
def _post_save_send_assignment_email(sender, instance, created, **kwargs):
    if getattr(instance, "_notify_first_assignment", False):
        assigned_user = getattr(instance, ASIGNADO_FIELD, None)  # ya es un User
        assigned_by = getattr(instance, "_assigned_by", None)    # opcional
        try:
            send_case_assigned_email(instance, assigned_user, assigned_by=assigned_by)
        except Exception:
            logger.exception("Error enviando notificación de asignación (case_id=%s)", instance.pk)
        finally:
            if hasattr(instance, "_notify_first_assignment"):
                delattr(instance, "_notify_first_assignment")
