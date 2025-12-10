# accidentes/forms_template/home.py
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.urls import reverse

from accidentes.models import Accidentes

PAGE_SIZE = 10


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
    """Heurística ligera por User-Agent (sin dependencias externas)."""
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
      2) Heurística UA → móvil: cards / desktop: table
    """
    forced = (request.GET.get("view") or "").strip().lower()
    is_mobile = _is_mobile(request)
    
    print(f"🔍 DEBUG _pick_home_partial:")
    print(f"  - User-Agent: {request.META.get('HTTP_USER_AGENT', 'N/A')[:100]}")
    print(f"  - Forced view: '{forced}'")
    print(f"  - is_mobile(): {is_mobile}")
    
    if forced in ("cards", "card"):
        print(f"  - ✅ Usando CARDS (forzado)")
        return "accidentes/partials/home/cards.html"
    if forced in ("table", "tabla"):
        print(f"  - ✅ Usando TABLE (forzado)")
        return "accidentes/partials/home/table.html"
    
    template = "accidentes/partials/home/cards.html" if is_mobile else "accidentes/partials/home/table.html"
    print(f"  - ✅ Usando {'CARDS' if is_mobile else 'TABLE'} (auto-detectado)")
    return template


def _opciones_filtros_home(user):
    """
    Construye opciones de selects igual que mis_investigaciones.html
    """
    from accidentes.models import Empresas
    from accidentes.access import scope_empresas_q
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Obtener accidentes visibles
    base_qs = (
        Accidentes.objects
        .visibles_para(user)
        .values("empresa_id", "usuario_asignado_id")
    )
    
    empresa_ids = {row["empresa_id"] for row in base_qs if row["empresa_id"]}
    investigador_ids = {row["usuario_asignado_id"] for row in base_qs if row["usuario_asignado_id"]}
    
    empresas = Empresas.objects.filter(empresa_id__in=empresa_ids).order_by("empresa_sel")
    investigadores = User.objects.filter(id__in=investigador_ids).order_by("first_name", "last_name", "username")
    
    return empresas, investigadores


@login_required
def home_view(request):
    # Resetea cualquier caso en sesión al entrar al home
    for k in ("accidente_id", "accidente_resultado", "accidente_preview"):
        request.session.pop(k, None)

    # Obtener opciones para filtros (igual que mis_investigaciones)
    empresas, investigadores = _opciones_filtros_home(request.user)
    tipos_accidente = Accidentes.TIPO_ACCIDENTE_CHOICES

    ctx = {
        "current_user_id": _current_user_id(request),
        "header_user": _header_user_info(request),
        "tipos_accidente": tipos_accidente,
        "empresas": empresas,
        "investigadores": investigadores,
    }
    return render(request, "accidentes/home.html", ctx)


@login_required
def home_assigned_cases_partial(request):
    """
    Lista paginada de accidentes dentro del alcance del usuario.
    Pensada para HTMX. Si se accede directo (sin HTMX), redirige al home full.
    """
    # Leer filtros del GET
    search_query = (request.GET.get("q") or "").strip()
    search_columns = (request.GET.get("columns") or "").strip()
    tipo_accidente = (request.GET.get("tipo_accidente") or "").strip()
    empresa_id = (request.GET.get("empresa") or "").strip()
    investigador_id = (request.GET.get("investigador") or "").strip()
    fecha_desde = (request.GET.get("fecha_desde") or "").strip()
    fecha_hasta = (request.GET.get("fecha_hasta") or "").strip()
    
    # Parsear columnas seleccionadas
    selected_columns = search_columns.split(',') if search_columns else []
    
    try:
        page_number = int(request.GET.get("page") or 1)
        if page_number < 1:
            page_number = 1
    except (TypeError, ValueError):
        page_number = 1

    # Base queryset con scope unificado
    qs = (
        Accidentes.objects
        .visibles_para(request.user)
        .select_related("empresa", "centro", "trabajador", "usuario_asignado")
        .annotate(codigo_accidente_db=F("codigo_accidente"))
        .order_by("-accidente_id")
    )

    # BÚSQUEDA GENERAL: Buscar en columnas seleccionadas
    if search_query:
        # Si no hay columnas seleccionadas, buscar en todas por defecto
        if not selected_columns:
            selected_columns = ['trabajador', 'codigo', 'centro', 'asignado', 'tipo']
        
        # Construir Q objects dinámicamente según las columnas seleccionadas
        q_objects = Q()
        
        if 'trabajador' in selected_columns:
            q_objects |= Q(trabajador__nombre_trabajador__icontains=search_query)
        
        if 'codigo' in selected_columns:
            q_objects |= Q(codigo_accidente__icontains=search_query)
        
        if 'centro' in selected_columns:
            q_objects |= Q(centro__nombre_local__icontains=search_query)
        
        if 'asignado' in selected_columns:
            q_objects |= Q(usuario_asignado__first_name__icontains=search_query)
            q_objects |= Q(usuario_asignado__last_name__icontains=search_query)
            q_objects |= Q(usuario_asignado__nombre__icontains=search_query)
            q_objects |= Q(usuario_asignado__apepat__icontains=search_query)
            q_objects |= Q(usuario_asignado__apemat__icontains=search_query)
        
        if 'tipo' in selected_columns:
            q_objects |= Q(tipo_accidente__icontains=search_query)
        
        # Aplicar filtro
        if q_objects:
            qs = qs.filter(q_objects)
    
    # Filtros específicos adicionales
    if tipo_accidente:
        qs = qs.filter(tipo_accidente=tipo_accidente)
    
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)
    
    if investigador_id:
        qs = qs.filter(usuario_asignado_id=investigador_id)
    
    if fecha_desde:
        try:
            from datetime import datetime
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            qs = qs.filter(fecha_accidente__gte=fecha_desde_obj)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            from datetime import datetime
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            qs = qs.filter(fecha_accidente__lte=fecha_hasta_obj)
        except ValueError:
            pass

    paginator = Paginator(qs, PAGE_SIZE)
    page_obj = paginator.get_page(page_number)

    # Mantener filtros en paginación
    base = reverse("accidentes:home-assigned-partial")
    query_bits = []
    if search_query:
        query_bits.append(f"q={search_query}")
    if search_columns:
        query_bits.append(f"columns={search_columns}")
    if tipo_accidente:
        query_bits.append(f"tipo_accidente={tipo_accidente}")
    if empresa_id:
        query_bits.append(f"empresa={empresa_id}")
    if investigador_id:
        query_bits.append(f"investigador={investigador_id}")
    if fecha_desde:
        query_bits.append(f"fecha_desde={fecha_desde}")
    if fecha_hasta:
        query_bits.append(f"fecha_hasta={fecha_hasta}")
    view_param = (request.GET.get("view") or "").strip().lower()
    if view_param in ("cards", "card", "table", "tabla"):
        query_bits.append(f"view={view_param}")
    query = ("&" + "&".join(query_bits)) if query_bits else ""

    prev_url = f"{base}?page={page_obj.number - 1}{query}" if page_obj.has_previous() else None
    next_url = f"{base}?page={page_obj.number + 1}{query}" if page_obj.has_next() else None

    ctx = {
        "page_obj": page_obj,
        "paginator": paginator,
        "prev_url": prev_url,
        "next_url": next_url,
        "request": request,
    }

    template_name = _pick_home_partial(request)
    return render(request, template_name, ctx)
