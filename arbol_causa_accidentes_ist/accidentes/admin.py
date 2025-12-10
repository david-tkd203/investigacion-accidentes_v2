from django.contrib import admin
from .models import Holdings, Empresas, CentrosTrabajo
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget

class EmpresasInline(admin.StackedInline):
    model = Empresas
    extra = 1
    fieldsets = (
        ("Datos básicos", {
            "fields": ("empresa_sel", "rut_empresa", "actividad"),
        }),
        ("Contacto y ubicación", {
            "fields": ("telefono", "representante_legal", "region", "comuna", "direccion_empresa"),
        }),
    )
    show_change_link = True

class CentrosTrabajoInline(admin.StackedInline):  # o TabularInline si prefieres tabla
    model = CentrosTrabajo
    extra = 1
    fields = ("nombre_local", "direccion_centro", "region", "comuna")


@admin.register(Holdings)
class HoldingsAdmin(admin.ModelAdmin):
    list_display = ("holding_id", "nombre", "created_at")
    search_fields = ("nombre",)
    inlines = [EmpresasInline]


@admin.register(Empresas)
class EmpresasAdmin(admin.ModelAdmin):
    list_display = (
        "empresa_id",
        "empresa_sel",
        "rut_empresa",
        "holding",
        "region",
        "comuna",
        "created_at",
    )
    list_filter = ("holding", "region", "comuna")
    search_fields = ("empresa_sel", "rut_empresa", "representante_legal")
    inlines = [CentrosTrabajoInline]


class CentrosTrabajoResource(resources.ModelResource):
    empresa_rut = fields.Field(
        column_name="rut_empresa",           # nombre de la columna en el Excel
        attribute="empresa",                 # FK en el modelo
        widget=ForeignKeyWidget(Empresas, "rut_empresa"),
    )

    class Meta:
        model = CentrosTrabajo

        # 👇 IMPORTANTE: indicamos el ID correcto
        import_id_fields = ("centro_id",)   # en vez de ('id',)

        fields = (
            "centro_id",        # se puede dejar vacío al importar
            "empresa_rut",
            "nombre_local",
            "direccion_centro",
            "region",
            "comuna",
        )
        export_order = (
            "centro_id",
            "empresa_rut",
            "nombre_local",
            "direccion_centro",
            "region",
            "comuna",
        )

        skip_unchanged = True
        report_skipped = True

@admin.register(CentrosTrabajo)
class CentrosTrabajoAdmin(ImportExportModelAdmin):
    resource_class = CentrosTrabajoResource
    list_display = ("centro_id", "nombre_local", "empresa", "region", "comuna")
    list_filter = ("empresa", "region", "comuna")
    search_fields = ("nombre_local", "empresa__empresa_sel", "empresa__rut_empresa")




