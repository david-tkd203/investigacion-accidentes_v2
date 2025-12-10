# accounts/admin.py
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import PasswordResetForm
from django.utils.crypto import get_random_string
from django.contrib.auth.models import Group

from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from .models import User
from accidentes.models import Empresas, Holdings

import logging
logger = logging.getLogger(__name__)


class UserResource(resources.ModelResource):
    empresa_rut = fields.Field(
        column_name="rut_empresa",
        attribute="empresa",
        widget=ForeignKeyWidget(Empresas, "rut_empresa"),
    )

    holding_nombre = fields.Field(
        column_name="holding_nombre",
        attribute="holding",
        widget=ForeignKeyWidget(Holdings, "nombre"),
    )

    # 👇 NUEVO: grupos desde Excel (incluye "Pendiente invitación")
    grupos = fields.Field(
        column_name="grupos",           # nombre de la columna en el Excel
        attribute="groups",             # M2M del modelo User
        widget=ManyToManyWidget(Group, field="name", separator=";"),
    )

    class Meta:
        model = User
        import_id_fields = ("username",)
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "rut",
            "nombre",
            "apepat",
            "apemat",
            "cargo",
            "team",
            "rol",
            "empresa_rut",
            "holding_nombre",
            "grupos",
            "is_active",
            "is_staff",
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = True

    def before_save_instance(self, instance, using_transactions, dry_run):
        if instance.rut:
            instance.clean()

        if instance.pk is None:
            # Contraseña aleatoria pero usable
            instance.set_password(get_random_string(12))

            # Forzar cambio en el primer login
            if not instance.must_change_password:
                instance.must_change_password = True



@admin.action(description="Enviar invitación para establecer contraseña")
def send_invitation(modeladmin, request, queryset):
    """Envía correo y luego limpia el grupo Pendiente invitación."""
    sent = 0
    skipped_no_email = 0

    # Obtener el grupo automáticamente
    from django.contrib.auth.models import Group
    try:
        g = Group.objects.get(name="Pendiente invitación")
    except Group.DoesNotExist:
        g = None

    for user in queryset:
        if not user.email:
            skipped_no_email += 1
            continue

        # Asegurar must_change_password
        if not user.must_change_password:
            user.must_change_password = True
            user.save(update_fields=["must_change_password"])

        # enviar invitación
        form = PasswordResetForm({'email': user.email})
        if form.is_valid():
            try:
                form.save(
                    request=request,
                    use_https=request.is_secure(),
                    email_template_name="registration/create_user_email.html",
                    html_email_template_name="registration/create_user_email.html",
                    subject_template_name="registration/create_user_subject.txt",
                    extra_email_context={"protocol": "http", "domain": "20.106.186.24"},
                )
                sent += 1
                logger.info("Invitación enviada a %s", user.email)
            except Exception:
                logger.exception("Error enviando invitación a %s", user.email)
        else:
            logger.error("PasswordResetForm inválido para %s: %s", user.email, form.errors)

        # 🔥 Limpieza automática del grupo
        if g:
            user.groups.remove(g)

    msg = f"Invitaciones enviadas: {sent}"
    if skipped_no_email:
        msg += f" | sin email: {skipped_no_email}"
    modeladmin.message_user(request, msg, level=messages.INFO)

@admin.action(description="Quitar marca 'Pendiente invitación'")
def clear_pending_invitation_group(modeladmin, request, queryset):
    group_name = "Pendiente invitación"
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        modeladmin.message_user(
            request,
            f"El grupo '{group_name}' no existe.",
            level=messages.WARNING,
        )
        return

    count = 0
    for user in queryset:
        if group in user.groups.all():
            user.groups.remove(group)
            count += 1

    modeladmin.message_user(
        request,
        f"Se eliminó el grupo '{group_name}' de {count} usuario(s).",
        level=messages.INFO,
    )


@admin.register(User)
class UserAdmin(ImportExportModelAdmin, DjangoUserAdmin):
    resource_class = UserResource

    list_display = (
        "username", "email", "first_name", "last_name",
        "team", "rol", "is_staff", "is_active", "must_change_password",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "team", "rol", "must_change_password", "groups")
    search_fields = ("username", "email", "first_name", "last_name", "rut", "nombre", "apepat", "apemat")
    ordering = ("username",)
    actions = [send_invitation, clear_pending_invitation_group]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Información personal"), {
            "fields": (
                "first_name", "last_name", "email",
                "rut", "nombre", "apepat", "apemat", "cargo",
            )
        }),
        (_("Organización"), {"fields": ("team", "rol", "empresa", "holding")}),
        (_("Permisos"), {
            "fields": (
                "is_active", "is_staff", "is_superuser",
                "groups", "user_permissions",
            )
        }),
        (_("Fechas importantes"), {"fields": ("last_login", "date_joined")}),
        (_("Seguridad"), {"fields": ("must_change_password",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username", "email", "password1", "password2",
                "first_name", "last_name",
                "rut", "nombre", "apepat", "apemat", "cargo",
                "team", "rol",
                "empresa", "holding",
                "is_staff", "is_active",
            ),
        }),
    )

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        if is_new:
            # Forzar cambio en primer login
            if not getattr(obj, "must_change_password", False):
                obj.must_change_password = True
                obj.save(update_fields=["must_change_password"])

            # Enviar correo solo cuando se crea manualmente (no en import)
            if obj.email:
                logger.info("Disparando PasswordResetForm para user_id=%s email=%s", obj.pk, obj.email)
                prf = PasswordResetForm({'email': obj.email})
                if prf.is_valid():
                    try:
                        prf.save(
                            request=request,
                            use_https=request.is_secure(),
                            email_template_name="registration/create_user_email.html",
                            html_email_template_name="registration/create_user_email.html",
                            subject_template_name="registration/create_user_subject.txt",
                            extra_email_context={"protocol": "http", "domain": "20.106.186.24"},  # TODO prod
                        )
                        logger.info("PasswordResetForm.save() ejecutado OK para %s", obj.email)
                    except Exception:
                        logger.exception("Fallo enviando reset/invitación a %s", obj.email)
                else:
                    logger.error("PasswordResetForm inválido para email=%s. Errors=%s", obj.email, prf.errors)
