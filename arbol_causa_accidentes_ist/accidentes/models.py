from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from .managers import AccidentesManager
import uuid


class Holdings(models.Model):
    holding_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'holdings'

    def __str__(self):
        return self.nombre


class Usuarios(models.Model):
    id = models.AutoField(primary_key=True)
    rut = models.CharField(max_length=10)
    nombre = models.CharField(max_length=100, null=True)
    apepat = models.CharField(max_length=100, null=True)
    apemat = models.CharField(max_length=100, null=True)
    email = models.CharField(max_length=254, unique=True)
    empresa = models.ForeignKey('Empresas', on_delete=models.CASCADE)
    pass_field = models.CharField(max_length=255, db_column='pass')
    tipo = models.IntegerField()
    Cargo = models.CharField(max_length=100, null=True)

    class Meta:
        db_table = 'usuarios'


class Empresas(models.Model):
    empresa_id = models.AutoField(primary_key=True)
    holding = models.ForeignKey(  # <--
        "accidentes.Holdings", null=True, on_delete=models.SET_NULL, related_name="empresas"
    )
    empresa_sel = models.CharField(max_length=255)
    rut_empresa = models.CharField(max_length=20, unique=True)
    actividad = models.CharField(max_length=255, null=True)
    direccion_empresa = models.CharField(max_length=255, null=True)
    telefono = models.CharField(max_length=30, null=True)
    representante_legal = models.CharField(max_length=255, null=True)
    region = models.CharField(max_length=100, null=True)
    comuna = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'empresas_legacy'  # Renombrado temporalmente para evitar conflicto con django-tenants
        indexes = [
            models.Index(fields=["rut_empresa"]),
            models.Index(fields=["holding", "empresa_sel"]),
        ]

    def __str__(self):
        return self.empresa_sel



class Trabajadores(models.Model):
    ESTADO_CIVIL_CHOICES = [
        ('Soltero/a', 'Soltero/a'),
        ('Casado/a', 'Casado/a'),
        ('Viudo/a', 'Viudo/a'),
        ('Divorciado/a', 'Divorciado/a'),
    ]

    CONTRATO_CHOICES = [
        ('Indefinido', 'Indefinido'),
        ('Plazo Fijo', 'Plazo Fijo'),
        ('Honorarios', 'Honorarios'),
        ('Contratista', 'Contratista'),
    ]

    NACIONALIDAD_CHOICES = [
        ('Chilena', 'Chilena'),
        ('Peruana', 'Peruana'),
        ('Venezolana', 'Venezolana'),
        ('Boliviana', 'Boliviana'),
        ('Argentina', 'Argentina'),
        ('Colombiana', 'Colombiana'),
        ('Ecuatoriana', 'Ecuatoriana'),
        ('Haitiana', 'Haitiana'),
        ('Paraguaya', 'Paraguaya'),
        ('Uruguaya', 'Uruguaya'),
    ]

    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]

    trabajador_id = models.AutoField(primary_key=True)
    empresa = models.ForeignKey('Empresas', null=True, on_delete=models.SET_NULL)
    nombre_trabajador = models.CharField(max_length=255, null=True)
    rut_trabajador = models.CharField(max_length=20, unique=True, null=True)
    fecha_nacimiento = models.DateField(null=True)
    nacionalidad = models.CharField(max_length=100, choices=NACIONALIDAD_CHOICES, null=True)
    estado_civil = models.CharField(max_length=50, choices=ESTADO_CIVIL_CHOICES, null=True)
    domicilio = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # >>> NUEVOS CAMPOS <<<
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, null=True, blank=True)

    antiguedad_empresa_anios = models.PositiveSmallIntegerField(null=True, blank=True)
    antiguedad_empresa_meses = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MaxValueValidator(11)]
    )

    antiguedad_cargo_anios = models.PositiveSmallIntegerField(null=True, blank=True)
    antiguedad_cargo_meses = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MaxValueValidator(11)]
    )

    # >>> ELIMINADOS (si existen en tu BD actual):
    # antiguedad_empresa = models.CharField(max_length=100, null=True)
    # antiguedad_cargo   = models.CharField(max_length=100, null=True)

    cargo_trabajador = models.CharField(max_length=100, null=True)
    contrato = models.CharField(max_length=50, choices=CONTRATO_CHOICES, null=True)

    class Meta:
        db_table = 'trabajadores'



class CentrosTrabajo(models.Model):
    centro_id = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(Empresas, on_delete=models.CASCADE)
    nombre_local = models.CharField(max_length=255)
    direccion_centro = models.CharField(max_length=255, null=True)
    region = models.CharField(max_length=100, null=True)
    comuna = models.CharField(max_length=100, null=True)

    class Meta:
        db_table = 'centros_trabajo'


# accidentes/models.py (solo la clase Accidentes)

from django.conf import settings
from django.db import models

class Accidentes(models.Model):
    objects = AccidentesManager()

    TIPO_ACCIDENTE_CHOICES = [
        ("Golpe por", "Golpe (golpeado) por"),
        ("Golpe con", "Golpe (golpeado) con"),
        ("Golpe contra", "Golpe (golpeado) contra"),
        ("Contacto con", "Contacto con"),
        ("Contacto por", "Contacto por"),
        ("Caída mismo nivel", "Caída al mismo nivel"),
        ("Caída distinto nivel", "Caída a distinto nivel"),
        ("Atrapamiento", "Atrapamiento"),
        ("Aprisionamiento", "Aprisionamiento"),
        ("Sobreesfuerzo", "Sobreesfuerzo"),
        ("Exposición a", "Exposición a"),
    ]
    OPCIONES_SI_NO = [("SI", "Sí"), ("NO", "No")]

    accidente_id = models.AutoField(primary_key=True)

    # Anclaje explícito
    holding = models.ForeignKey(
        "accidentes.Holdings", null=True, on_delete=models.SET_NULL, related_name="accidentes"
    )
    empresa = models.ForeignKey(
        "accidentes.Empresas", null=True, on_delete=models.SET_NULL, related_name="accidentes"
    )
    centro = models.ForeignKey(
        "accidentes.CentrosTrabajo", null=True, blank=True, on_delete=models.SET_NULL, related_name="accidentes"
    )
    trabajador = models.ForeignKey(
        "accidentes.Trabajadores", null=True, on_delete=models.SET_NULL, related_name="accidentes"
    )

    # Usuario asignado
    usuario_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="accidentes_asignados",
    )

    # Trazabilidad
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="accidentes_creados",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="accidentes_actualizados",
    )
    actualizado_en = models.DateTimeField(auto_now=True)

    # Datos del accidente
    fecha_accidente = models.DateField(null=True)
    hora_accidente = models.TimeField(null=True, blank=True)
    lugar_accidente = models.CharField(max_length=255, null=True, blank=True)
    tipo_accidente = models.CharField(max_length=100, choices=TIPO_ACCIDENTE_CHOICES, null=True, blank=True)
    naturaleza_lesion = models.CharField(max_length=255, null=True, blank=True)
    parte_afectada = models.CharField(max_length=255, null=True, blank=True)
    tarea = models.CharField(max_length=255, null=True, blank=True)
    operacion = models.CharField(max_length=255, null=True, blank=True)
    danos_personas = models.CharField(max_length=2, choices=OPCIONES_SI_NO, null=True, blank=True)
    danos_propiedad = models.CharField(max_length=2, choices=OPCIONES_SI_NO, null=True, blank=True)
    perdidas_proceso = models.CharField(max_length=2, choices=OPCIONES_SI_NO, null=True, blank=True)
    contexto = models.TextField(null=True, blank=True)
    circunstancias = models.TextField(null=True, blank=True)

    # NUEVA COLUMNA (hasta 1000 caracteres)
    resumen = models.CharField(
        "Resumen",
        max_length=1000,
        null=True,
        blank=True,
        help_text="Resumen breve del accidente (máx. 1000 caracteres)."
    )

    codigo_accidente = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "accidentes"
        indexes = [
            models.Index(fields=["codigo_accidente"]),
            models.Index(fields=["holding", "empresa"]),
        ]
        ordering = ["-fecha_accidente", "-hora_accidente", "-accidente_id"]


    def __str__(self):
        return f"Accidente {self.codigo_accidente}"

    # ---------- helpers ----------
    def _infer_holding_from_empresa(self):
        """Si empresa tiene holding y accidente no lo trae, propaga."""
        if self.empresa and (self.holding is None):
            self.holding = self.empresa.holding

    def can_assign(self, asignador, asignado):
        """
        Reglas de quién puede asignar a quién, considerando además
        que el accidente pertenece a un holding/empresa concretos.
        """
        if not asignador or not asignado:
            return False

        # Acceso total
        if asignador.rol in ("admin", "admin_ist"):
            return True

        if asignador.rol == "admin_holding":
            return (
                asignado.rol in ("admin_holding", "admin_empresa", "investigador")
                and getattr(asignado, "holding_id", None) == getattr(asignador, "holding_id", None)
                and (self.holding_id == getattr(asignador, "holding_id", None))
            )

        if asignador.rol == "admin_empresa":
            return (
                asignado.rol in ("investigador", "admin_empresa")
                and getattr(asignado, "empresa_id", None) == getattr(asignador, "empresa_id", None)
                and (self.empresa_id == getattr(asignador, "empresa_id", None))
            )

        # investigadores no asignan a otros
        return False

    # ---------- validaciones de negocio ----------
    def clean(self):
        """
        Reglas de negocio:
        - Empresa requerida (o se infiere según el rol del actor).
        - Holding consistente con la empresa.
        - Trabajador requerido y debe pertenecer a la empresa.
        - Fecha del accidente requerida.
        - Asignación:
            * En creación: exige usuario_asignado (auto-asigna al actor si puede).
            * En edición: valida sólo si cambió usuario_asignado.
        """
        super().clean()
        errors = {}

        # Actor actual (inyectado por el ModelForm) o fallback a trazabilidad
        actor = getattr(self, "_actor", None) or getattr(self, "actualizado_por", None) or getattr(self, "creado_por", None)
        actor_rol = getattr(actor, "rol", None)

        # (1) Empresa requerida / inferida por rol del actor
        if not self.empresa:
            if actor_rol in ("admin_empresa", "investigador"):
                empresa_actor = getattr(actor, "empresa", None)
                if empresa_actor:
                    self.empresa = empresa_actor
                else:
                    errors["empresa"] = "No se pudo inferir la empresa del usuario."
            else:
                errors["empresa"] = "La empresa es obligatoria."

        # (2) Holding consistente con empresa
        self._infer_holding_from_empresa()
        if self.empresa and self.holding and self.empresa.holding_id and self.holding_id != self.empresa.holding_id:
            errors["holding"] = "El holding del accidente no coincide con el holding de la empresa."

        # (3) Trabajador requerido y coherente con empresa
        if not self.trabajador:
            errors["trabajador"] = "El trabajador es obligatorio."
        else:
            if self.empresa and self.trabajador.empresa_id and self.trabajador.empresa_id != self.empresa_id:
                errors["trabajador"] = "El trabajador no pertenece a la empresa seleccionada."

        # (4) Fecha requerida
        if not self.fecha_accidente:
            errors["fecha_accidente"] = "La fecha del accidente es obligatoria."

        # (5) Asignación: crea vs edita (solo si cambió el asignado)
        is_create = self.pk is None
        original_assignee_id = getattr(self, "_original_usuario_asignado", None)
        assignee_changed = (self.usuario_asignado_id or None) != (original_assignee_id or None)

        if is_create:
            if not self.usuario_asignado:
                if actor and self.can_assign(actor, actor):
                    self.usuario_asignado = actor
                else:
                    errors["usuario_asignado"] = "Debe asignar un usuario al accidente."
            else:
                if actor and not self.can_assign(actor, self.usuario_asignado):
                    errors["usuario_asignado"] = "No tiene permisos para asignar a ese usuario."
        else:
            if assignee_changed:
                if not self.usuario_asignado:
                    errors["usuario_asignado"] = "Debe asignar un usuario al accidente."
                else:
                    if actor and not self.can_assign(actor, self.usuario_asignado):
                        errors["usuario_asignado"] = "No tiene permisos para asignar a ese usuario."

        # (5b) Coherencia extra de alcance del asignado (solo si corresponde)
        if self.usuario_asignado and "usuario_asignado" not in errors and (is_create or assignee_changed):
            if actor_rol == "admin_holding":
                if getattr(self.usuario_asignado, "holding_id", None) != self.holding_id:
                    errors["usuario_asignado"] = "El usuario asignado no pertenece al holding seleccionado."
            elif actor_rol == "admin_empresa":
                if getattr(self.usuario_asignado, "empresa_id", None) != self.empresa_id:
                    errors["usuario_asignado"] = "El usuario asignado no pertenece a la empresa seleccionada."

        if errors:
            raise ValidationError(errors)


    def save(self, *args, **kwargs):
        # Garantiza coherencia aún si no pasan por full_clean() en alguna ruta
        self._infer_holding_from_empresa()
        super().save(*args, **kwargs)



class ArbolCausas(models.Model):
    arbol_id = models.AutoField(primary_key=True)
    accidente = models.ForeignKey(Accidentes, on_delete=models.CASCADE)
    version = models.SmallIntegerField()
    is_current = models.BooleanField(default=False)
    arbol_json_5q = models.TextField(null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    arbol_json_dot = models.TextField(null=True)

    class Meta:
        db_table = 'arbol_causas'
        unique_together = ('accidente', 'version')


class Declaraciones(models.Model):
    TIPO_DECL_CHOICES = [
        ('accidentado', 'Accidentado'),
        ('testigo', 'Testigo'),
        ('supervisor', 'Supervisor')
    ]
    declaracion_id = models.AutoField(primary_key=True)
    accidente = models.ForeignKey(Accidentes, on_delete=models.CASCADE, related_name='declaraciones')
    tipo_decl = models.CharField(max_length=20, choices=TIPO_DECL_CHOICES, default='testigo')
    nombre = models.CharField(max_length=255, null=True)
    rut = models.CharField(max_length=20, null=True)
    cargo = models.CharField(max_length=255, null=True)
    texto = models.TextField(null=True)

    class Meta:
        db_table = 'declaraciones'


class Documentos(models.Model):
    documento_id = models.CharField(primary_key=True, max_length=36)
    accidente = models.ForeignKey('Accidentes', null=True, on_delete=models.CASCADE)
    documento = models.CharField(max_length=255, null=True)
    objetivo = models.TextField(null=True)
    nombre_archivo = models.CharField(max_length=255, null=True)
    mime_type = models.CharField(max_length=100, null=True)
    contenido = models.BinaryField(null=True, blank=True)
    subido_el = models.DateTimeField(auto_now_add=True)
    url = models.CharField(max_length=2048, null=True, help_text="Enlace externo o URL interna de descarga")

    class Meta:
        db_table = 'documentos'

    def es_enlace_externo(self):
        return self.url and self.url.startswith("http")

    @property
    def url_descarga(self):
        if self.es_enlace_externo():
            return self.url
        if self.nombre_archivo:
            return reverse("descargar_documento", args=[self.documento_id])
        return "#"


class Hechos(models.Model):
    hecho_id = models.AutoField(primary_key=True)
    accidente = models.ForeignKey(Accidentes, on_delete=models.CASCADE)
    secuencia = models.SmallIntegerField(null=True)
    descripcion = models.TextField(null=True)

    class Meta:
        db_table = 'hechos'


class Informes(models.Model):
    informe_id = models.AutoField(primary_key=True)
    accidente = models.ForeignKey(Accidentes, on_delete=models.CASCADE)
    version = models.SmallIntegerField()
    is_current = models.BooleanField(default=False)
    codigo = models.CharField(max_length=50, null=True)
    fecha_informe = models.DateField(null=True)
    investigador = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'informes'
        unique_together = ('accidente', 'version')


class PreguntasGuia(models.Model):
    CATEGORIA_CHOICES = [
        ('accidentado', 'Accidentado'),
        ('testigos', 'Testigos'),
        ('supervisores', 'Supervisores')
    ]
    pregunta_id = models.AutoField(primary_key=True)
    accidente = models.ForeignKey(Accidentes, on_delete=models.CASCADE)
    uuid = models.CharField(max_length=36)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    pregunta = models.TextField(null=True)
    objetivo = models.TextField(null=True)
    respuesta = models.TextField(null=True)

    class Meta:
        db_table = 'preguntas_guia'
        unique_together = ('accidente', 'uuid')


class Prescripciones(models.Model):
    prescripcion_id = models.AutoField(primary_key=True)
    accidente = models.ForeignKey(Accidentes, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=100, null=True)
    prioridad = models.CharField(max_length=50, null=True)
    plazo = models.DateField(null=True)
    responsable = models.CharField(max_length=255, null=True)
    descripcion = models.TextField(null=True)

    class Meta:
        db_table = 'prescripciones'


class AccidenteJsonData(models.Model):
    accidente = models.OneToOneField(Accidentes, primary_key=True, on_delete=models.CASCADE)
    preguntas_json = models.JSONField()
    otro_json_1 = models.JSONField(null=True)
    otro_json_2 = models.JSONField(null=True)

    class Meta:
        db_table = 'accidente_json_data'


class Relato(models.Model):
    relato_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accidente = models.ForeignKey('Accidentes', on_delete=models.CASCADE, related_name="relato")
    relato_inicial = models.TextField(blank=True, null=True)
    pregunta_1 = models.TextField(blank=True, null=True)
    respuesta_1 = models.TextField(blank=True, null=True)
    pregunta_2 = models.TextField(blank=True, null=True)
    respuesta_2 = models.TextField(blank=True, null=True)
    pregunta_3 = models.TextField(blank=True, null=True)
    respuesta_3 = models.TextField(blank=True, null=True)
    relato_final = models.TextField(blank=True, null=True)
    fraseQR1 = models.TextField(blank=True, null=True)
    fraseQR2 = models.TextField(blank=True, null=True)
    fraseQR3 = models.TextField(blank=True, null=True)
    is_current = models.BooleanField(default=True)
    creado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'accidentes_relato'

    def __str__(self):
        return f"Relato para accidente {self.accidente.codigo_accidente}"


#politicas de privacidad:

class UserPrivacyConsent(models.Model):
    """
    Registro de aceptación por usuario (FK al AUTH_USER_MODEL=accounts.User).
    """
    LEY_CHOICES = [
        ("21.459", "Ley 21.459 - Delitos Informáticos"),
        ("21.663", "Ley 21.663 - Ley Marco de Ciberseguridad"),
        ("21.719", "Ley 21.719 - Protección de Datos Personales"),
    ]

    id = models.AutoField(primary_key=True)

    # ⬇️ ESTA ES LA CLAVE: usar settings.AUTH_USER_MODEL
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,   # -> accounts.User (db_table "users")
        on_delete=models.CASCADE,
        related_name="privacy_consents",
    )

    ley_numero  = models.CharField(max_length=10, choices=LEY_CHOICES)
    version     = models.CharField(max_length=50, default="v1.0")
    aceptado_en = models.DateTimeField(default=timezone.now, db_index=True)

    ip         = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = "user_privacy_consents"
        unique_together = ("usuario", "ley_numero", "version")
        indexes = [
            models.Index(fields=["usuario", "ley_numero"]),
            models.Index(fields=["aceptado_en"]),
        ]

    def __str__(self):
        return f"{self.usuario_id} aceptó {self.ley_numero} ({self.version}) @ {self.aceptado_en:%Y-%m-%d %H:%M}"