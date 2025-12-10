# accidentes/views.py

import json
from pathlib import Path
import mimetypes
from .models import Usuarios, UserPrivacyConsent
from django.utils import timezone
from django.http import HttpResponseBadRequest
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from django.middleware.csrf import get_token
from django.conf import settings

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse

from accidentes.utils.mixins import AccidenteScopedByCodigoMixin
from accidentes.decorators import require_accidente_scope
from accidentes.access import empresa_en_alcance, scope_accidentes_q

from django.db.models import Q, F
from django.core.paginator import Paginator, EmptyPage
import logging
from .models import Accidentes, CentrosTrabajo, Documentos
from .forms import (
    BuscarAccidenteForm,
    EmpresaForm,
    CentroTrabajoForm,
    TrabajadorForm,
    AccidenteForm
)

logger = logging.getLogger(__name__)
# Helpers para la vista de empresa (lógica en cascada para CT)
def _html_options(options, selected=None, include_placeholder=True):
    """
    options: iterable de strings (o de tuplas (value,label))
    selected: valor a marcar como seleccionado
    """
    html = []
    if include_placeholder:
        html.append('<option value="">---------</option>')
    for opt in options:
        if isinstance(opt, (tuple, list)) and len(opt) >= 2:
            val, lab = opt[0], opt[1]
        else:
            val = lab = opt
        sel = ' selected' if selected is not None and str(selected) == str(val) else ''
        html.append(f'<option value="{val}"{sel}>{lab}</option>')
    return ''.join(html)


def _render_oob(id_attr, inner_html, tag='select', extra_attrs=''):
    attrs = (extra_attrs + ' hx-swap-oob="outerHTML"').strip()
    return f'<{tag} id="{id_attr}" {attrs}>{inner_html}</{tag}>'


# =========================
# Views protegidas por Login
# =========================

class BuscarAccidenteView(LoginRequiredMixin, View):
    template_name = "accidentes/buscar_accidente.html"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def get(self, request):
        request.session.pop("accidente_preview", None)
        request.session.pop("accidente_id", None)
        request.session.pop("accidente_resultado", None)

        return render(request, self.template_name, {
            "form": BuscarAccidenteForm()
        })

    def post(self, request):
        form = BuscarAccidenteForm(request.POST)
        context = {"form": form}

        if form.is_valid():
            codigo = form.cleaned_data["codigo"].strip()
            qs = (Accidentes.objects
                  .visibles_para(request.user)  # ⬅️ manager con scope
                  .select_related("centro__empresa", "trabajador", "usuario_asignado"))
            accidente = qs.filter(codigo_accidente=codigo).first()

            if not accidente:
                messages.error(request, "No se encontró o no tienes permiso para verlo.")
                return render(request, self.template_name, context)

            resultado = {
                "codigo": accidente.codigo_accidente,
                "fecha_accidente": accidente.fecha_accidente.isoformat() if accidente.fecha_accidente else "",
                "trabajador": {
                    "rut": accidente.trabajador.rut_trabajador if accidente.trabajador else "",
                    "nombre": accidente.trabajador.nombre_trabajador if accidente.trabajador else "",
                },
            }
            request.session["accidente_preview"] = resultado
            context["resultado"] = resultado
            context["codigo"] = codigo

        return render(request, self.template_name, context)


class CargarAccidenteView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def post(self, request):
        codigo = request.POST.get("codigo") or request.session.get("accidente_preview", {}).get("codigo")
        if not codigo:
            messages.warning(request, "No se recibió el código del accidente.")
            return redirect("accidentes:buscar")

        accidente = (Accidentes.objects
                     .visibles_para(request.user)  # ⬅️ manager con scope
                     .select_related("centro__empresa", "trabajador", "usuario_asignado")
                     .filter(codigo_accidente=codigo)
                     .first())
        if not accidente:
            messages.error(request, "No se encontró o no tienes permiso para verlo.")
            return redirect("accidentes:buscar")

        resultado = {
            "codigo": accidente.codigo_accidente,
            "fecha_accidente": accidente.fecha_accidente.isoformat() if accidente.fecha_accidente else "",
            "trabajador": {
                "rut": accidente.trabajador.rut_trabajador if accidente.trabajador else "",
                "nombre": accidente.trabajador.nombre_trabajador if accidente.trabajador else "",
            },
        }

        request.session["accidente_id"] = accidente.pk
        request.session["accidente_resultado"] = resultado
        request.session.pop("accidente_preview", None)

        messages.success(request, f"Caso {codigo} cargado en sesión.")
        return redirect("accidentes:empresa", codigo=codigo)


# ─────────────────────────────────────────────────────────────────────────────
# CBVs con scope unificado (mixin resuelve accidente + sincroniza sesión)
# ─────────────────────────────────────────────────────────────────────────────

class DatosEmpresaView(LoginRequiredMixin, AccidenteScopedByCodigoMixin, View):
    template_name = "accidentes/datos_empresa.html"
    partial_template_name = "accidentes/partials/empresa/form_empresa.html"

    def _compute_empresa(self, accidente):
        """
        Prefiere la empresa del accidente; si no existe, usa la del centro.
        """
        empresa = getattr(accidente, "empresa", None)
        if empresa:
            return empresa
        if accidente.centro and getattr(accidente.centro, "empresa", None):
            return accidente.centro.empresa
        return None

    def get(self, request, codigo):
        accidente = self.accidente_from(codigo)
        empresa   = self._compute_empresa(accidente)
        centro    = accidente.centro

        form = CentroTrabajoForm(
            initial={
                "region": centro.region if centro else "",
                "comuna": centro.comuna if centro else "",
                "nombre_local": centro.nombre_local if centro else "",
                "direccion_centro": centro.direccion_centro if centro else "",   # ← precarga aquí
            },
            empresa_id=empresa.empresa_id if empresa else None,
        )

        context = {"empresa": empresa, "form": form, "codigo": codigo, "accidente": accidente}
        template = self.partial_template_name if getattr(request, "htmx", False) else self.template_name
        return render(request, template, context)


    def post(self, request, codigo):
        accidente = self.accidente_from(codigo)  # ⬅️ scope + sesión unificada
        empresa   = self._compute_empresa(accidente)

        form = CentroTrabajoForm(request.POST, empresa_id=empresa.empresa_id if empresa else None)
        if not form.is_valid():
            logger.error("ERRORES FORM EMPRESA: %s", form.errors.as_json())
            context = {"empresa": empresa, "form": form, "codigo": codigo, "accidente": accidente}
            template = self.partial_template_name if getattr(request, "htmx", False) else self.template_name
            return render(request, template, context)

        # Datos posteados (texto)
        region = (request.POST.get("region") or "").strip()
        comuna = (request.POST.get("comuna") or "").strip()

        # Resolver SIEMPRE por ID
        centro = None
        centro_id_raw = request.POST.get("centro_id")
        try:
            centro_id = int(centro_id_raw) if centro_id_raw not in (None, "",) else None
        except (TypeError, ValueError):
            centro_id = None

        if centro_id and empresa:
            # Validar coherencia empresa / región / comuna
            centro = (CentrosTrabajo.objects
                    .filter(pk=centro_id,
                            empresa_id=empresa.empresa_id,
                            region=region,
                            comuna=comuna)
                    .first())

        if centro:
            accidente.centro = centro
            accidente.save()
            msg_level  = "success"
            msg_text   = "Datos de centro de trabajo actualizados."
            messages.success(request, msg_text)
        else:
            msg_level  = "warning"
            msg_text   = "No se pudo determinar el centro seleccionado. Asegúrate de escoger un centro válido."
            messages.warning(request, msg_text)

        # Recalcular empresa por si depende del centro
        empresa = self._compute_empresa(accidente)

        # Re-render del form con valores visibles
        form = CentroTrabajoForm(
            initial={
                "region":            getattr(centro, "region", None) or region,
                "comuna":            getattr(centro, "comuna", None) or comuna,
                # Campo solo informativo; el select real es centro_id
                "nombre_local":      getattr(centro, "nombre_local", "") if centro else "",
                "direccion_centro":  getattr(centro, "direccion_centro", "") if centro else "",
            },
            empresa_id=empresa.empresa_id if empresa else None,
        )

        context = {"empresa": empresa, "form": form, "codigo": codigo, "accidente": accidente}

        if getattr(request, "htmx", False):
            response = render(request, self.partial_template_name, context)
            # Notificación + forzar refresco de dirección en el wrapper (ver hx-trigger en el template)
            response["HX-Trigger"] = json.dumps({
                "flash": {"level": msg_level, "message": "Centro actualizado" if centro else "No se pudo determinar el centro"},
                "refresh-direccion": True
            })
            return response

        return redirect("accidentes:trabajador", codigo=codigo)



class DatosTrabajadorView(LoginRequiredMixin, AccidenteScopedByCodigoMixin, View):
    template_name = "accidentes/datos_trabajador.html"
    partial_template_name = "accidentes/partials/trabajador/form_trabajador.html"

    def get(self, request, codigo):
        accidente = self.accidente_from(codigo)
        form = TrabajadorForm(instance=accidente.trabajador)
        context = {"form": form, "codigo": codigo}
        template = self.partial_template_name if getattr(request, "htmx", False) else self.template_name
        return render(request, template, context)

    def post(self, request, codigo):
        accidente = self.accidente_from(codigo)
        form = TrabajadorForm(request.POST, instance=accidente.trabajador)
        context = {"form": form, "codigo": codigo}

        if not form.is_valid():
            template = self.partial_template_name if getattr(request, "htmx", False) else self.template_name
            return render(request, template, context)

        if form.has_changed():
            trabajador = form.save()
            if accidente.trabajador_id != getattr(trabajador, "pk", None):
                accidente.trabajador = trabajador
                accidente.save()
            messages.success(request, "Datos del trabajador actualizados.")
        else:
            messages.info(request, "No se realizaron cambios en los datos del trabajador.")

        if getattr(request, "htmx", False):
            return render(request, self.partial_template_name, context)

        return redirect("accidentes:accidente", codigo=codigo)


class DatosAccidenteView(LoginRequiredMixin, AccidenteScopedByCodigoMixin, View):
    template_name = "accidentes/datos_accidente.html"
    partial_template_name = "accidentes/partials/accidente/form_accidente.html"

    def get(self, request, codigo):
        accidente = self.accidente_from(codigo)
        form = AccidenteForm(None, instance=accidente, actor=request.user)
        ctx = {"form": form, "codigo": codigo}
        template = self.partial_template_name if getattr(request, "htmx", False) else self.template_name
        return render(request, template, ctx)

    def post(self, request, codigo):
        accidente = self.accidente_from(codigo)
        form = AccidenteForm(request.POST or None, instance=accidente, actor=request.user)
        ctx = {"form": form, "codigo": codigo}

        if not form.is_valid():
            # Si el modelo devolvió un error en usuario_asignado, el hidden del form lo captura.
            template = self.partial_template_name if getattr(request, "htmx", False) else self.template_name
            return render(request, template, ctx)

        if form.has_changed():
            obj = form.save(commit=False)
            # trazabilidad opcional si tienes el campo:
            if hasattr(obj, "actualizado_por"):
                obj.actualizado_por = request.user
            obj.save()
            messages.success(request, "Datos del accidente guardados.")
        else:
            messages.info(request, "No se realizaron cambios.")

        if getattr(request, "htmx", False):
            # devolvemos el partial para refrescar el formulario en sitio
            return render(request, self.partial_template_name, ctx)

        return redirect("accidentes:accidente", codigo=codigo)


# =========================
# Function-Based Views (AJAX / utilidades) protegidas
# =========================

@require_GET
@login_required(login_url="/accounts/login/")
@require_accidente_scope(source="session")
def cargar_comunas(request):
    empresa_id = request.GET.get("empresa_id")
    acc = request.accidente

    # Coherencia empresa del caso <-> empresa_id del request
    if acc.empresa_id:
        if str(acc.empresa_id) != str(empresa_id or ""):
            raise Http404("No permitido.")
    else:
        if not empresa_en_alcance(request.user, empresa_id):
            raise Http404("No permitido.")

    region = request.GET.get("region")
    comunas = CentrosTrabajo.objects.filter(
        region=region, empresa_id=empresa_id
    ).values_list("comuna", flat=True).distinct()
    html = "".join([f'<option value="{c}">{c}</option>' for c in comunas if c])
    return HttpResponse(html)


@require_GET
@login_required(login_url="/accounts/login/")
@require_accidente_scope(source="session")
def cargar_centros(request):
    empresa_id = request.GET.get("empresa_id")
    acc = request.accidente
    if acc.empresa_id:
        if str(acc.empresa_id) != str(empresa_id or ""):
            raise Http404("No permitido.")
    else:
        if not empresa_en_alcance(request.user, empresa_id):
            raise Http404("No permitido.")

    region = request.GET.get("region")
    comuna = request.GET.get("comuna")
    nombres = CentrosTrabajo.objects.filter(
        region=region,
        comuna=comuna,
        empresa_id=empresa_id
    ).values_list("nombre_local", flat=True).distinct()

    return render(request, "accidentes/partials/empresa/opciones_nombres.html", {
        "nombres": nombres
    })


@require_GET
@login_required(login_url="/accounts/login/")
@require_accidente_scope(source="session")
def cargar_direccion(request):
    empresa_id = request.GET.get("empresa_id")
    acc = request.accidente
    if acc.empresa_id:
        if str(acc.empresa_id) != str(empresa_id or ""):
            raise Http404("No permitido.")
    else:
        if not empresa_en_alcance(request.user, empresa_id):
            raise Http404("No permitido.")

    nombre_local = request.GET.get("nombre_local")
    direccion = ""
    if nombre_local and empresa_id:
        centro = CentrosTrabajo.objects.filter(
            empresa_id=empresa_id,
            nombre_local=nombre_local
        ).first()
        if centro:
            direccion = centro.direccion_centro

    form = CentroTrabajoForm(initial={"direccion_centro": direccion})

    return render(request, "accidentes/partials/empresa/campo_direccion.html", {
        "form": form
    })


@require_GET
@login_required(login_url="/accounts/login/")
@require_accidente_scope(source="session")
def obtener_centro_id(request):
    empresa_id = request.GET.get("empresa_id")
    acc = request.accidente
    if acc.empresa_id:
        if str(acc.empresa_id) != str(empresa_id or ""):
            raise Http404("No permitido.")
    else:
        if not empresa_en_alcance(request.user, empresa_id):
            raise Http404("No permitido.")

    nombre_local = request.GET.get("nombre_local")
    centro_id = ""
    if nombre_local and empresa_id:
        centro = CentrosTrabajo.objects.filter(
            nombre_local=nombre_local,
            empresa_id=empresa_id
        ).first()
        if centro:
            centro_id = centro.centro_id

    return render(request, "accidentes/partials/empresa/campo_centro_id.html", {
        "centro_id": centro_id
    })


@login_required(login_url="/accounts/login/")
def descargar_documento(request, doc_id):
    doc = get_object_or_404(Documentos, pk=doc_id)

    if not Accidentes.objects.visibles_para(request.user).filter(pk=doc.accidente_id).exists():
        raise Http404("Documento no disponible.")
    # Si es un enlace externo, no hay archivo
    if doc.url and doc.url.startswith("http"):
        raise Http404("Este documento es un enlace externo.")

    if not doc.nombre_archivo:
        raise Http404("El documento no tiene archivo asociado.")

    # Verificamos existencia física
    ext = Path(doc.nombre_archivo).suffix
    protected_path = Path(settings.PROTECTED_MEDIA_ROOT) / "documentos" / f"{doc.documento_id}{ext}"
    if not protected_path.exists():
        raise Http404("Archivo no encontrado.")

    # Ruta interna (la que Nginx tiene mapeada con X-Accel-Redirect)
    internal_url = f"/protected_media_internal/documentos/{doc.documento_id}{ext}"

    mime_type = doc.mime_type or mimetypes.guess_type(protected_path)[0] or "application/octet-stream"

    response = HttpResponse()
    response["Content-Type"] = mime_type
    response["Content-Disposition"] = f'attachment; filename="{doc.nombre_archivo}"'
    response["X-Accel-Redirect"] = internal_url  # El "proxy interno"

    return response


@require_GET
@login_required(login_url="/accounts/login/")
@require_accidente_scope(source="kwarg")   # ★ ahora valida por codigo en la URL
def cargar_comunas_y_centros(request, codigo):
    empresa_id = request.GET.get("empresa_id")
    acc = request.accidente  # inyectado por el decorador

    # Coherencia empresa
    if acc.empresa_id:
        if str(acc.empresa_id) != str(empresa_id or ""):
            raise Http404("No permitido.")
    else:
        if not empresa_en_alcance(request.user, empresa_id):
            raise Http404("No permitido.")

    region = request.GET.get("region") or ""

    # 1) Comunas
    comunas_qs = (CentrosTrabajo.objects
                  .filter(region=region, empresa_id=empresa_id)
                  .values_list("comuna", flat=True).distinct())
    comunas = [c for c in comunas_qs if c]

    selected_comuna = ""
    include_placeholder_comuna = True
    if len(comunas) == 1:
        selected_comuna = comunas[0]
        include_placeholder_comuna = False

    comuna_options = _html_options(
        comunas,
        selected=selected_comuna,
        include_placeholder=include_placeholder_comuna
    )

    # Al cambiar la comuna, re-renderizar el SELECT de centros (por ID)
    url_centros_y_direccion = reverse("accidentes:cargar_centros_y_direccion", kwargs={"codigo": codigo})
    comuna_select_attrs = (
        'name="comuna" class="form-select" '
        f'hx-get="{url_centros_y_direccion}" '
        'hx-include="[name=\'region\'], [name=\'comuna\'], [name=\'empresa_id\']" '
        'hx-target="#id_centro_id_select" '
        'hx-swap="outerHTML"'
    )
    comuna_oob = _render_oob("id_comuna", comuna_options, tag="select", extra_attrs=comuna_select_attrs)

    # 2) Centros por ID (value=centro_id, label="Nombre — Dirección")
    centros = []
    if selected_comuna:
        centros_qs = (CentrosTrabajo.objects
                      .filter(region=region, comuna=selected_comuna, empresa_id=empresa_id)
                      .only("centro_id", "nombre_local", "direccion_centro"))
        for c in centros_qs:
            label = c.nombre_local or f"Centro {c.centro_id}"
            if getattr(c, "direccion_centro", ""):
                label = f"{label} — {c.direccion_centro}"
            centros.append((c.centro_id, label))

    centro_options = _html_options(centros, selected="", include_placeholder=True)

    # Select de centros por ID
    url_direccion_y_id = reverse("accidentes:cargar_direccion_y_id", kwargs={"codigo": codigo})
    centros_select_attrs = (
        'name="centro_id" class="form-select" '
        f'hx-get="{url_direccion_y_id}" '
        'hx-include="[name=\'region\'], [name=\'comuna\'], [name=\'empresa_id\'], [name=\'centro_id\']" '
        'hx-trigger="change" '
        'hx-target="#direccion-wrapper" '
        'hx-swap="outerHTML" '
        'hx-sync="closest form:drop"'
    )
    centros_oob = _render_oob("id_centro_id_select", centro_options, tag="select", extra_attrs=centros_select_attrs)

    return HttpResponse(comuna_oob + centros_oob)


@require_GET
@login_required(login_url="/accounts/login/")
@require_accidente_scope(source="kwarg")
def cargar_centros_y_direccion(request, codigo):
    empresa_id = request.GET.get("empresa_id")
    acc = request.accidente
    if acc.empresa_id:
        if str(acc.empresa_id) != str(empresa_id or ""):
            raise Http404("No permitido.")
    else:
        if not empresa_en_alcance(request.user, empresa_id):
            raise Http404("No permitido.")

    region = request.GET.get("region") or ""
    comuna = request.GET.get("comuna") or ""

    centros = []
    selected_id = ""
    include_placeholder = True

    if comuna:
        centros_qs = (CentrosTrabajo.objects
                      .filter(region=region, comuna=comuna, empresa_id=empresa_id)
                      .only("centro_id", "nombre_local", "direccion_centro"))
        for c in centros_qs:
            label = c.nombre_local or f"Centro {c.centro_id}"
            if getattr(c, "direccion_centro", ""):
                label = f"{label} — {c.direccion_centro}"
            centros.append((c.centro_id, label))

    direccion_oob = ""

    # Autoseleccionar si hay 1 sólo centro y precargar dirección via OOB
    if len(centros) == 1:
        selected_id = str(centros[0][0])
        include_placeholder = False
        centro = CentrosTrabajo.objects.filter(pk=centros[0][0], empresa_id=empresa_id).only("direccion_centro").first()
        direccion_val = centro.direccion_centro if centro else ""
        direccion_html = render_to_string(
            "accidentes/partials/empresa/campo_direccion.html",
            {"form": CentroTrabajoForm(initial={"direccion_centro": direccion_val})}
        )
        # OOB sólo aquí para que aparezca la dirección inmediatamente
        direccion_oob = direccion_html.replace('id="direccion-wrapper"', 'id="direccion-wrapper" hx-swap-oob="outerHTML"')

    options_html = _html_options(centros, selected=selected_id, include_placeholder=include_placeholder)

    url_direccion_y_id = reverse("accidentes:cargar_direccion_y_id", kwargs={"codigo": codigo})
    nombre_select_attrs = (
        'name="centro_id" class="form-select" '
        f'hx-get="{url_direccion_y_id}" '
        'hx-include="[name=\'region\'], [name=\'comuna\'], [name=\'empresa_id\'], [name=\'centro_id\']" '
        'hx-trigger="change" '
        'hx-target="#direccion-wrapper" '
        'hx-swap="outerHTML" '
        'hx-sync="closest form:drop"'
    )
    nombre_select_html = f'<select id="id_centro_id_select" {nombre_select_attrs}>{options_html}</select>'

    # Devuelve el select (normal) + dirección OOB solo si hay 1 centro
    return HttpResponse(nombre_select_html + direccion_oob)


@require_GET
@login_required(login_url="/accounts/login/")
@require_accidente_scope(source="kwarg")
def cargar_direccion_y_id(request, codigo):
    empresa_id = request.GET.get("empresa_id")
    acc = request.accidente
    if acc.empresa_id:
        if str(acc.empresa_id) != str(empresa_id or ""):
            raise Http404("No permitido.")
    else:
        if not empresa_en_alcance(request.user, empresa_id):
            raise Http404("No permitido.")

    region    = request.GET.get("region") or ""
    comuna    = request.GET.get("comuna") or ""
    centro_id = request.GET.get("centro_id") or ""

    direccion_val = ""

    if centro_id:
        try:
            c = (CentrosTrabajo.objects
                 .only("empresa_id", "region", "comuna", "direccion_centro")
                 .get(pk=int(centro_id)))
            # Validación de coherencia
            if (str(c.empresa_id) == str(empresa_id)
                and str(c.region) == str(region)
                and str(c.comuna) == str(comuna)):
                direccion_val = c.direccion_centro or ""
        except (CentrosTrabajo.DoesNotExist, ValueError, TypeError):
            direccion_val = ""

    # Renderiza solo el wrapper de dirección; HTMX lo reemplaza in place
    direccion_html = render_to_string(
        "accidentes/partials/empresa/campo_direccion.html",
        {"form": CentroTrabajoForm(initial={"direccion_centro": direccion_val})}
    )
    direccion_oob = direccion_html.replace(
        'id="direccion-wrapper"',
        'id="direccion-wrapper" hx-swap-oob="outerHTML"'
    )

    return HttpResponse(direccion_html)

PAGE_SIZE = 10

# ---------- Alcance de LISTADO con el mismo criterio que el detalle ----------
def scope_accidentes_listado_q(user) -> Q:
    """
    Misma regla que el gate de detalle para los roles críticos.
    - investigador: misma empresa AND asignado
    - investigador_ist: solo asignado (sin validar empresa/holding)
    - otros: alcance general existente (scope_accidentes_q)
    """
    rol = getattr(user, "rol", None)
    uid = getattr(user, "id", None)

    if rol == "investigador":
        return Q(empresa_id=getattr(user, "empresa_id", None)) & Q(usuario_asignado_id=uid)

    if rol == "investigador_ist":
        return Q(usuario_asignado_id=uid)

    return scope_accidentes_q(user)

# ---------- Helpers UI ----------
def _current_user_id(request) -> int:
    try:
        return int(request.user.pk or 0)
    except (TypeError, ValueError):
        return 0

def _title_or_blank(val: str) -> str:
    try:
        s = (val or "").strip()
        return s.title()
    except Exception:
        return ""

def _header_user_info(request) -> dict:
    u = request.user
    return {
        "first_name": _title_or_blank(getattr(u, "first_name", "")),
        "last_name": _title_or_blank(getattr(u, "last_name", "")),
        "rol": getattr(u, "rol", None),
        "team": getattr(u, "team", None),
    }

def _is_mobile(request) -> bool:
    ua = (request.META.get("HTTP_USER_AGENT") or "").lower()
    if not ua:
        return False
    mobile_kw = (
        "iphone", "android", "blackberry", "windows phone",
        "opera mini", "mobile", "ipad", "ipod"
    )
    return any(k in ua for k in mobile_kw)

def _pick_home_partial(request) -> str:
    """
    Prioridad:
      1) ?view=cards | ?view=table
      2) UA → móvil: cards / desktop: table
    """
    forced = (request.GET.get("view") or "").strip().lower()
    if forced in ("cards", "card"):
        return "accidentes/partials/home/cards.html"
    if forced in ("table", "tabla"):
        return "accidentes/partials/home/table.html"
    return "accidentes/partials/home/cards.html" if _is_mobile(request) \
           else "accidentes/partials/home/table.html"

# ---------- Vistas ----------
# Importar las vistas actualizadas desde forms_template/home.py
from .forms_template.home import (
    home_view,
    home_assigned_cases_partial
)

# Las funciones antiguas se comentan para mantener historial
# @login_required
# @require_GET
# def home_view(request):
#     ...

# Funciones antiguas comentadas - ahora se usan las de forms_template/home.py
# que incluyen filtros avanzados, búsqueda por columnas, etc.


#Politicas de privacidad

def _get_usuario_from_request(request):
    """
    Si usas auth de Django + tu tabla `usuarios`, normalmente tendrás
    un vínculo por email o por id en session. Aquí intentamos por email.
    Ajusta si guardas `usuario_id` en la session.
    """
    try:
        email = getattr(request.user, "email", None)
        if not email:
            return None
        return Usuarios.objects.get(email=email)
    except Usuarios.DoesNotExist:
        # Plan B: si guardas el id de tu tabla en la session:
        uid = request.session.get("usuario_id")
        if uid:
            try:
                return Usuarios.objects.get(pk=uid)
            except Usuarios.DoesNotExist:
                return None
        return None


LEYES = ("21.459", "21.663", "21.719")
CONSENT_VERSION = "v1.0"

def _faltan_consentimientos(user) -> set[str]:
    existentes = (
        UserPrivacyConsent.objects
        .filter(usuario=user, version=CONSENT_VERSION, ley_numero__in=LEYES)
        .values_list("ley_numero", flat=True)
    )
    return set(LEYES) - set(existentes)

@require_GET
@login_required(login_url="/accounts/login/")
def privacy_policies(request):
    # ⚠️ NO usar last_login para decidir; usar faltantes
    faltan = _faltan_consentimientos(request.user)

    if not faltan:
        # si nada falta, volver a donde quería ir o a home
        next_url = request.session.pop("post_consent_next", None)
        return redirect(next_url or reverse("accidentes:home"))

    context = {
        "leyes": [
            {
                "numero": "21.459",
                "titulo": "Delitos Informáticos",
                "publicacion": "2022-06-20",
                "vigencia": "Vigencia con disposiciones transitorias (p.ej., 6 meses para algunos artículos; otros vía reglamento).",
                "template": "accidentes/compliance/ley_21459.html",
            },
            {
                "numero": "21.663",
                "titulo": "Ley Marco de Ciberseguridad",
                "publicacion": "2024-04-08",
                "vigencia": "Implementación por reglamentos/DFL con al menos 6 meses desde publicación.",
                "template": "accidentes/compliance/ley_21663.html",
            },
            {
                "numero": "21.719",
                "titulo": "Protección de Datos Personales",
                "publicacion": "2024-12-13",
                "vigencia": "Diferida al 2026-12-01 con reglas transitorias.",
                "template": "accidentes/compliance/ley_21719.html",
            },
        ],
    }
    return render(request, "accidentes/compliance/policies.html", context)

@require_POST
@login_required(login_url="/accounts/login/")
def privacy_policies_accept(request):
    if request.POST.get("accept") != "on":
        return HttpResponseBadRequest("Debes aceptar las políticas para continuar.")

    leyes = request.POST.getlist("leyes[]")
    # Validación estricta: deben venir exactamente las 3
    if set(leyes) != set(LEYES):
        return HttpResponseBadRequest("Listado de leyes inválido.")

    ua = (request.META.get("HTTP_USER_AGENT") or "")[:400]
    ip = (request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip() or request.META.get("REMOTE_ADDR")

    for ley in leyes:
        UserPrivacyConsent.objects.get_or_create(
            usuario=request.user,
            ley_numero=ley,
            version=CONSENT_VERSION,
            defaults={"aceptado_en": timezone.now(), "ip": ip, "user_agent": ua},
        )

    next_url = request.session.pop("post_consent_next", None)
    return redirect(next_url or reverse("accidentes:home"))