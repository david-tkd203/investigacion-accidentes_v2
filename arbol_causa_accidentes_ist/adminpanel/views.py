
# adminpanel/views.py
from datetime import datetime

from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.db.models import Q, Exists, OuterRef
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.db import IntegrityError
from django.contrib import messages
from django.db.models import Max

from accidentes.models import Accidentes, Empresas, Trabajadores, Informes

from .permissions import AdminPanelAccessMixin
from .forms import AccidenteCrearForm, TrabajadorCrearForm
from accidentes.access import (
    empresas_permitidas,
    usuarios_permitidos_para_asignar,
    trabajadores_permitidos,
    holdings_permitidos,
    SUPER_ROLES,
    scope_accidentes_q,  # si tu mixin lo necesita
)

User = get_user_model()

# ------------ utilidades ------------
MESES = [
    (1, "Enero"), (2, "Febrero"), (3, "Marzo"), (4, "Abril"),
    (5, "Mayo"), (6, "Junio"), (7, "Julio"), (8, "Agosto"),
    (9, "Septiembre"), (10, "Octubre"), (11, "Noviembre"), (12, "Diciembre"),
]


def generar_codigo_accidente(user) -> str:
    year = datetime.now().year
    last = Accidentes.objects.aggregate(max_id=Max("accidente_id"))["max_id"] or 0
    return f"ACC-{year}-{last + 1:06d}"


def _aplicar_filtros(qs, request):
    empresa_id = request.GET.get("empresa")
    mes_raw = request.GET.get("mes")
    trabajador_id = request.GET.get("trabajador")
    investigador_id = request.GET.get("investigador")
    q = request.GET.get("q", "").strip()

    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)

    # --- Mes: acepta número o nombre ---
    if mes_raw:
        MES_MAP = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
            "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
            "septiembre": 9, "setiembre": 9, "octubre": 10,
            "noviembre": 11, "diciembre": 12,
        }
        try:
            mes_val = int(mes_raw)
        except ValueError:
            mes_val = MES_MAP.get(mes_raw.strip().lower())
        if mes_val and 1 <= mes_val <= 12:
            qs = qs.filter(fecha_accidente__month=mes_val)

    if trabajador_id:
        qs = qs.filter(trabajador_id=trabajador_id)

    if investigador_id:
        qs = qs.filter(usuario_asignado_id=investigador_id)

    if q:
        qs = qs.filter(
            Q(codigo_accidente__icontains=q) |
            Q(empresa__empresa_sel__icontains=q) |
            Q(trabajador__nombre_trabajador__icontains=q) |
            Q(contexto__icontains=q) |
            Q(circunstancias__icontains=q)
        )
    return qs


def _opciones_filtros(user):
    """
    Construye opciones de selects restringidas al universo visible
    y además a "mis investigaciones" (creado_por=user).
    """
    base_qs = (
        Accidentes.objects
        .visibles_para(user)               # ⬅️ alcance central
        .filter(creado_por=user)           # ⬅️ “Mis investigaciones”
        .values("empresa_id", "trabajador_id", "usuario_asignado_id")
    )

    empresa_ids = {row["empresa_id"] for row in base_qs if row["empresa_id"]}
    trabajador_ids = {row["trabajador_id"] for row in base_qs if row["trabajador_id"]}
    investigador_ids = {row["usuario_asignado_id"] for row in base_qs if row["usuario_asignado_id"]}

    empresas = Empresas.objects.filter(empresa_id__in=empresa_ids).order_by("empresa_sel")
    trabajadores = Trabajadores.objects.filter(trabajador_id__in=trabajador_ids).order_by("nombre_trabajador")
    investigadores = User.objects.filter(id__in=investigador_ids).order_by("first_name", "last_name", "username")

    return empresas, trabajadores, investigadores


class MisInvestigacionesView(AdminPanelAccessMixin, ListView):
    model = Accidentes
    template_name = "adminpanel/mis_investigaciones.html"          # página completa
    context_object_name = "investigaciones"
    paginate_by = 10

    def get_queryset(self):
        # Base: solo accidentes dentro del alcance central del usuario
        qs = (
            Accidentes.objects
            .visibles_para(self.request.user)                       # ⬅️ alcance central
            .filter(creado_por=self.request.user)                   # ⬅️ “Mis investigaciones”
            .select_related("empresa", "centro", "trabajador", "creado_por", "usuario_asignado")
            .order_by("-creado_en")
        )

        # Filtros de pantalla
        qs = _aplicar_filtros(qs, self.request)

        # Flag de informe disponible (soporta modelos sin is_current)
        has_is_current = any(f.name == "is_current" for f in Informes._meta.fields)
        if has_is_current:
            qs = qs.annotate(
                tiene_informe=Exists(
                    Informes.objects.filter(
                        accidente_id=OuterRef("pk"),
                        is_current=True,
                    )
                )
            )
        else:
            qs = qs.annotate(
                tiene_informe=Exists(
                    Informes.objects.filter(
                        accidente_id=OuterRef("pk"),
                    )
                )
            )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        empresas, trabajadores, investigadores = _opciones_filtros(self.request.user)

        ctx["sidebar_active"] = "mis_investigaciones"
        ctx["q"] = self.request.GET.get("q", "")

        # opciones de selects
        ctx["empresas"] = empresas
        ctx["meses"] = MESES
        ctx["trabajadores"] = trabajadores
        ctx["investigadores"] = investigadores

        # seleccionados actuales (para mantener estado en la UI)
        ctx["sel_empresa"] = self.request.GET.get("empresa", "")
        ctx["sel_mes"] = self.request.GET.get("mes", "")
        ctx["sel_trabajador"] = self.request.GET.get("trabajador", "")
        ctx["sel_investigador"] = self.request.GET.get("investigador", "")
        return ctx

    def get_template_names(self):
        if self.request.headers.get("HX-Request") == "true":
            return ["adminpanel/partials/investigaciones_list/_mis_investigaciones_table.html"]
        return [self.template_name]


class MisInvestigacionesPartialView(MisInvestigacionesView):
    """
    Devuelve SIEMPRE el parcial. Reutiliza queryset y filtros de la vista padre.
    """
    template_name = "adminpanel/partials/investigaciones_list/_mis_investigaciones_table.html"

    def get_template_names(self):
        return [self.template_name]


# ---------- CreateView: pasar user al form y generar código ----------
class CrearInvestigacionView(AdminPanelAccessMixin, CreateView):
    model = Accidentes
    form_class = AccidenteCrearForm
    template_name = "adminpanel/crear_investigacion.html"
    success_url = reverse_lazy("adminpanel:mis_investigaciones")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pasa user, actor y request al form
        kwargs["user"] = self.request.user
        kwargs["actor"] = self.request.user
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        obj = form.save(commit=False)

        # trazabilidad
        obj.creado_por = self.request.user
        obj.actualizado_por = self.request.user

        # el modelo necesita conocer al actor para su clean()
        obj._actor = self.request.user
        obj._original_usuario_asignado = None

        # genera código si falta
        if not obj.codigo_accidente:
            obj.codigo_accidente = generar_codigo_accidente(self.request.user)

        # validación de negocio (centro no es requerido al crear)
        obj.full_clean(exclude=["centro"])
        obj.save()

        messages.success(self.request, f"Accidente {obj.codigo_accidente} creado correctamente.")
        self.object = obj
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["sidebar_active"] = "crear_investigacion"
        return ctx

    def form_invalid(self, form):
        # Debug opcional
        print("[DEBUG][crear] form.errors =", form.errors)
        print("[DEBUG][crear] non_field_errors =", form.non_field_errors())
        print("[DEBUG][crear] cleaned_data =", getattr(form, "cleaned_data", None))
        return super().form_invalid(form)


# ================== ENDPOINTS HTMX ==================
@require_GET
def empresas_por_holding_htmx(request):
    holding_raw = request.GET.get("holding")
    try:
        holding_id = int(holding_raw)
    except (TypeError, ValueError):
        html = render_to_string(
            "adminpanel/partials/crear/_seleccion_requerida.html",
            {"msg": "Selecciona un holding válido."},
            request=request,
        )
        return HttpResponse(html, status=200)

    if not holdings_permitidos(request.user).filter(pk=holding_id).exists():
        html = render_to_string(
            "adminpanel/partials/crear/_seleccion_requerida.html",
            {"msg": "El holding seleccionado no está dentro de tu alcance."},
            request=request,
        )
        return HttpResponse(html, status=200)

    qs_emp = empresas_permitidas(request.user, holding_id=holding_id)

    # ⬇️ NUEVO: lee empresa si viene (por hx-include) y pásala “segura” al template
    sel_empresa = request.GET.get("empresa") or request.GET.get("empresa_hidden") or ""

    html = render_to_string(
        "adminpanel/partials/crear/_empresa_select.html",
        {"empresas": qs_emp, "sel_empresa": sel_empresa},
        request=request,
    )
    return HttpResponse(html)



@require_GET
def trabajador_lookup_htmx(request):
    """Busca por RUT dentro de la empresa seleccionada. No autoselecciona; requiere confirmación."""
    rut = (request.GET.get("rut") or "").strip()
    empresa_raw = request.GET.get("empresa")

    # Parseo seguro
    try:
        empresa_id = int(empresa_raw) if empresa_raw else None
    except (TypeError, ValueError):
        empresa_id = None

    # Si no hay empresa seleccionada, muestra aviso (200 OK)
    if not empresa_id:
        html = render_to_string(
            "adminpanel/partials/crear/_seleccion_requerida.html",
            {"msg": "Selecciona primero el holding y la empresa para buscar un trabajador."},
            request=request,
        )
        return HttpResponse(html, status=200)

    # Empresa debe estar en alcance (200 con mensaje, no 403)
    if not empresas_permitidas(request.user).filter(pk=empresa_id).exists():
        html = render_to_string(
            "adminpanel/partials/crear/_seleccion_requerida.html",
            {"msg": "La empresa seleccionada no está dentro de tu alcance."},
            request=request,
        )
        return HttpResponse(html, status=200)

    # Buscar SOLO dentro de la empresa y alcance del usuario
    qs_trab = trabajadores_permitidos(
        request.user, empresa_id=empresa_id, force_empresa_for_creation=True
    )
    trabajador = (
        qs_trab.filter(rut_trabajador__iexact=rut)
        .select_related("empresa")
        .first()
    )

    if trabajador:
        # Mostramos “encontrado, pero NO seleccionado”
        html = render_to_string(
            "adminpanel/partials/crear/_trabajador_panel_encontrado.html",
            {"trabajador": trabajador},
            request=request,
        )
        return HttpResponse(html)

    # Existe en otra empresa? no revelar datos (200 + mensaje neutro)
    existe_otro = (
        Trabajadores.objects
        .filter(rut_trabajador__iexact=rut)
        .exclude(empresa_id=empresa_id)
        .first()
    )
    if existe_otro:
        html = render_to_string(
            "adminpanel/partials/crear/_alerta_fuera_alcance.html",
            {"rut": rut},
            request=request,
        )
        return HttpResponse(html, status=200)

    # No existe: ofrece crear dentro de ESTA empresa
    html = render_to_string(
        "adminpanel/partials/crear/_trabajador_panel_no_encontrado.html",
        {"rut": rut, "empresa_id": empresa_id},
        request=request,
    )
    return HttpResponse(html)


@require_GET
def trabajador_modal_htmx(request):
    rut = (request.GET.get("rut") or "").strip()
    holding_raw = request.GET.get("holding")
    empresa_raw = request.GET.get("empresa")

    try:
        holding_id = int(holding_raw) if holding_raw else None
    except (TypeError, ValueError):
        holding_id = None
    try:
        empresa_id = int(empresa_raw) if empresa_raw else None
    except (TypeError, ValueError):
        empresa_id = None

    rol = getattr(request.user, "rol", None)

    # **Regla**: super-roles y admin_holding deben elegir empresa antes de abrir modal
    if (rol in SUPER_ROLES or rol == "admin_holding") and not empresa_id:
        html = render_to_string(
            "adminpanel/partials/crear/_seleccion_requerida.html",
            {"msg": "Selecciona primero el holding y la empresa para crear un trabajador."},
            request=request,
        )
        return HttpResponse(html, status=200)

    # Si viene empresa, valida alcance
    if empresa_id and not empresas_permitidas(request.user, holding_id=holding_id).filter(pk=empresa_id).exists():
        html = render_to_string(
            "adminpanel/partials/crear/_seleccion_requerida.html",
            {"msg": "La empresa seleccionada no está dentro de tu alcance."},
            request=request,
        )
        return HttpResponse(html, status=200)

    form = TrabajadorCrearForm(
        user=request.user,
        holding_id=holding_id,
        initial={"rut_trabajador": rut, "empresa": empresa_id},
    )
    html = render_to_string(
        "adminpanel/partials/crear/_trabajador_modal.html",
        {"form": form},
        request=request,
    )
    return HttpResponse(html)


@require_POST
def trabajador_crear_htmx(request):
    """Crea trabajador desde el modal y, si es correcto, lo selecciona automáticamente."""
    form = TrabajadorCrearForm(request.POST, user=request.user)
    if not form.is_valid():
        html = render_to_string(
            "adminpanel/partials/crear/_trabajador_modal.html",
            {"form": form},
            request=request,
        )
        return HttpResponse(html, status=200)

    try:
        trabajador = form.save()
    except IntegrityError:
        form.add_error("rut_trabajador", "Ya existe un trabajador con ese RUT.")
        html = render_to_string(
            "adminpanel/partials/crear/_trabajador_modal.html",
            {"form": form},
            request=request,
        )
        return HttpResponse(html, status=200)

    # Éxito: panel OK OOB + hidden OOB + cerrar modal
    panel_html = render_to_string(
        "adminpanel/partials/crear/_trabajador_panel_ok.html",
        {"trabajador": trabajador},
        request=request,
    )
    panel_oob = f'<div id="trabajador-panel" hx-swap-oob="true">{panel_html}</div>'
    hidden_oob = (
        '<input type="hidden" name="trabajador_id" id="id_trabajador_id" '
        f'value="{trabajador.pk}" hx-swap-oob="true">'
    )
    cerrar_modal = """
    <div hx-swap-oob="true" id="close-worker-modal-hook"></div>
    <script>
      (function(){
         var m = document.getElementById('modalCrearTrabajador');
         if (m) {
            var modal = bootstrap.Modal.getInstance(m) || new bootstrap.Modal(m);
            modal.hide();
         }
      })();
    </script>
    """
    return HttpResponse(panel_oob + hidden_oob + cerrar_modal)


# ================== HTMX: USUARIO (asignación) ==================
@require_GET
def usuario_lookup_htmx(request):
    q = (request.GET.get("q") or "").strip()
    empresa_raw = request.GET.get("empresa")

    try:
        empresa_id = int(empresa_raw) if empresa_raw else None
    except (TypeError, ValueError):
        empresa_id = None

    # Empresa requerida
    if not empresa_id:
        html = render_to_string(
            "adminpanel/partials/crear/_seleccion_requerida.html",
            {"msg": "Selecciona primero el holding y la empresa para buscar usuarios."},
            request=request,
        )
        return HttpResponse(html, status=200)

    # Empresa dentro del alcance
    if not empresas_permitidas(request.user).filter(pk=empresa_id).exists():
        html = render_to_string(
            "adminpanel/partials/crear/_seleccion_requerida.html",
            {"msg": "La empresa seleccionada no está dentro de tu alcance."},
            request=request,
        )
        return HttpResponse(html, status=200)

    # Regla: en creación SIEMPRE filtrar por empresa, salvo super-roles
    users_qs = usuarios_permitidos_para_asignar(
        request.user,
        empresa_id=empresa_id,
        force_empresa_for_creation=True,
    )

    if q:
        users_qs = users_qs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(username__icontains=q) |
            Q(email__icontains=q)
        )

    users_qs = users_qs.order_by("first_name", "last_name", "username")[:20]
    html = render_to_string(
        "adminpanel/partials/crear/_usuario_resultados.html",
        {"usuarios": users_qs},
        request=request,
    )
    return HttpResponse(html)

@require_GET
def usuario_select_htmx(request):
    try:
        user_id = int(request.GET.get("id"))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("ID inválido.")

    try:
        empresa_id = int(request.GET.get("empresa")) if request.GET.get("empresa") else None
    except (TypeError, ValueError):
        empresa_id = None

    if not empresa_id:
        html = render_to_string(
            "adminpanel/partials/crear/_seleccion_requerida.html",
            {"msg": "Selecciona primero el holding y la empresa para asignar un usuario."},
            request=request,
        )
        return HttpResponse(html, status=200)

    users_qs = usuarios_permitidos_para_asignar(
        request.user, empresa_id=empresa_id, force_empresa_for_creation=True
    )
    usuario = users_qs.filter(pk=user_id).first()
    if not usuario:
        html = render_to_string(
            "adminpanel/partials/crear/_seleccion_requerida.html",
            {"msg": "El usuario seleccionado no está disponible para esta empresa."},
            request=request,
        )
        return HttpResponse(html, status=200)

    panel_html = render_to_string(
        "adminpanel/partials/crear/_usuario_panel_ok.html",
        {"usuario": usuario},
        request=request,
    )

    panel_oob = f'<div id="usuario-panel" hx-swap-oob="true">{panel_html}</div>'

    # ⬇️ Ahora swappeamos dentro del contenedor que ya está DENTRO del form
    hidden_oob = (
        '<div id="usuario-hidden-hook" hx-swap-oob="true">'
        f'  <input type="hidden" name="usuario_asignado" id="id_usuario_asignado" value="{usuario.pk}">'
        '</div>'
    )

    limpiar = '<div id="usuario-resultados" hx-swap-oob="true"></div>'
    return HttpResponse(panel_oob + hidden_oob + limpiar)




@require_GET
def trabajador_select_htmx(request):
    try:
        trabajador_id = int(request.GET.get("id"))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("ID inválido.")

    trabajador = get_object_or_404(Trabajadores, pk=trabajador_id)

    # Verifica alcance del trabajador
    if not (
        trabajadores_permitidos(request.user, empresa_id=trabajador.empresa_id)
        .filter(pk=trabajador.pk)
        .exists()
    ):
        html = render_to_string(
            "adminpanel/partials/crear/_alerta_fuera_alcance.html",
            {"rut": trabajador.rut_trabajador},
            request=request,
        )
        return HttpResponse(html, status=200)

    # 1) panel OK (reemplaza #trabajador-panel)
    panel_html = render_to_string(
        "adminpanel/partials/crear/_trabajador_panel_ok.html",
        {"trabajador": trabajador},
        request=request,
    )

    # 2) hidden OOB para setear el id real del formulario
    hidden_oob = (
        f'<input type="hidden" name="trabajador_id" id="id_trabajador_id" '
        f'value="{trabajador.pk}" hx-swap-oob="true">'
    )

    return HttpResponse(panel_html + hidden_oob)
