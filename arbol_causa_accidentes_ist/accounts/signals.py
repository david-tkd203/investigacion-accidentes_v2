# accounts/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group


@receiver(post_migrate)
def crear_grupo_pendiente_invitacion(sender, **kwargs):
    """
    Crea el grupo 'Pendiente invitación' después de aplicar migraciones.
    Se ejecuta una vez por app, así que filtramos por el nombre de la app.
    """
    # sender es un AppConfig; usamos .name
    if sender.name != "accounts":
        return

    Group.objects.get_or_create(name="Pendiente invitación")
