# accounts/management/commands/ensure_superuser.py
import os
from django.core.management import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import transaction

class Command(BaseCommand):
    help = "Crea o actualiza un superusuario usando variables de entorno (rol, team, rut incluidos)."

    def _validate_choice(self, user, field_name, value):
        if not value:
            return
        try:
            field = user._meta.get_field(field_name)
        except FieldDoesNotExist:
            return
        choices = getattr(field, "choices", None)
        if choices:
            valid = {c[0] for c in choices}
            if value not in valid:
                raise CommandError(
                    f"Valor inválido para {field_name}='{value}'. "
                    f"Choices válidos: {sorted(valid)}"
                )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        User = get_user_model()

        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email    = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
        rol      = os.getenv("DJANGO_SUPERUSER_ROLE")
        team     = os.getenv("DJANGO_SUPERUSER_TEAM")
        rut      = os.getenv("DJANGO_SUPERUSER_RUT")

        if not password:
            self.stdout.write(self.style.WARNING(
                "DJANGO_SUPERUSER_PASSWORD no está definido. Omitiendo ensure_superuser."
            ))
            return

        # crear o recuperar por username
        obj, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        changed = False

        # Asegura flags base
        if not obj.is_staff:
            obj.is_staff = True; changed = True
        if not obj.is_superuser:
            obj.is_superuser = True; changed = True
        if not obj.is_active:
            obj.is_active = True; changed = True

        # Sincroniza email
        if obj.email != email:
            obj.email = email; changed = True

        self._validate_choice(obj, "rol",  rol)
        self._validate_choice(obj, "team", team)

        # Asigna campos extra
        if rol and getattr(obj, "rol", None) != rol:
            obj.rol = rol; changed = True
        if team and getattr(obj, "team", None) != team:
            obj.team = team; changed = True
        if rut and getattr(obj, "rut", None) != rut:
            obj.rut = rut; changed = True

        obj.set_password(password); changed = True

        try:
            obj.full_clean()
        except ValidationError as e:
            raise CommandError(f"Validación del superusuario falló: {e.message_dict if hasattr(e, 'message_dict') else e}")

        if changed:
            obj.save()

        msg = "creado" if created else "actualizado"
        self.stdout.write(self.style.SUCCESS(f"Superusuario {msg}: {obj.username}"))
