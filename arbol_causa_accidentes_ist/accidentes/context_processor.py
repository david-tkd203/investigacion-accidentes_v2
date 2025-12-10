# accidentes/context_processor.py
from django.urls import reverse
from django.urls import resolve

# Mapea los url_name a etiquetas del breadcrumb
LABELS = {
    "buscar": ("Inicio",),
    "cargar_accidente": ("Inicio", "Cargar accidente"),

    "empresa": ("Inicio", "Datos empresa"),
    "trabajador": ("Inicio", "Datos trabajador"),
    "accidente": ("Inicio", "Datos accidente"),

    "ia_declaraciones": ("Inicio", "Asistente de entrevistas"),
    "ia_relato": ("Inicio", "Construcción del relato"),
    "ia_hechos": ("Inicio", "Análisis de hechos"),
    "ia_arbol": ("Inicio", "Árbol de causas"),
    "ia_fotos": ("Inicio", "Fotos y documentos"),
    "ia_medidas": ("Inicio", "Medidas correctivas"),
    "generar_arbol": ("Inicio", "Generar árbol (IA)"),
}

def breadcrumbs(request):
    rm = getattr(request, "resolver_match", None)
    if not rm:
        return {}

    url_name = rm.url_name
    labels = LABELS.get(url_name)
    if not labels:
        return {}  # sin mapeo → el base cae al fallback

    items = []
    # Primer item: Inicio con link a home (Mis casos)
    items.append({"label": "Inicio", "url": reverse("accidentes:home")})

    # Resto: sin link (o agrega links si tienes rutas intermedias)
    for label in labels[1:]:
        items.append({"label": label, "url": None})

    # Ejemplo: si quieres agregar el código al último nivel
    codigo = rm.kwargs.get("codigo") if rm.kwargs else None
    if codigo and len(items) >= 1:
        # Añade “ · ABC123” al último label
        items[-1]["label"] = f'{items[-1]["label"]} · {codigo}'

    return {"breadcrumbs": items}

def accidente_nav_context(request):
    """
    Expone variables para el menú lateral de investigación SIN usar sesión.
    - acc_codigo: código del caso si la ruta actual lo incluye.
    - acc_menu_visible: bandera para mostrar/ocultar el menú.
    """
    codigo = None
    try:
        match = resolve(request.path_info)
        codigo = match.kwargs.get("codigo")
    except Exception:
        pass

    return {
        "acc_codigo": codigo,
        "acc_menu_visible": bool(codigo),
    }
