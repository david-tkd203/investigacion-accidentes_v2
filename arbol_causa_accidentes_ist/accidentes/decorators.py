# accidentes/decorators.py
from functools import wraps
from django.http import Http404
from accidentes.access import get_accidente_scoped_or_404

def require_accidente_scope(*, source="kwarg", kwarg="codigo", param=None, select_related=None):
    """
    source: 'session' | 'kwarg'
    kwarg : nombre del kwarg que trae el código (por defecto 'codigo')
    param : (DEPRECATED) alias de 'kwarg' para compatibilidad
    select_related: tuple/list opcional para optimizar fetch del accidente
    """
    if param and not kwarg:
        kwarg = param  # compat con código antiguo

    def decorator(viewfunc):
        @wraps(viewfunc)
        def wrapper(request, *args, **kwargs):
            if source not in {"session", "kwarg"}:
                raise RuntimeError("source debe ser 'kwarg' o 'session'.")

            if source == "session":
                acc_id = request.session.get("accidente_id")
                if not acc_id:
                    raise Http404("Caso no disponible.")
                from accidentes.models import Accidentes
                qs = Accidentes.objects.visibles_para(request.user)
                if select_related:
                    qs = qs.select_related(*select_related)
                acc = qs.filter(pk=acc_id).first()
                if not acc:
                    raise Http404("Caso no disponible.")
                request.accidente = acc
            else:
                codigo_val = kwargs.get(kwarg or "codigo")
                if not codigo_val:
                    raise Http404("Caso no disponible.")
                acc = get_accidente_scoped_or_404(
                    request.user, codigo=codigo_val,
                    select_related=tuple(select_related) if select_related else ()
                )
                request.accidente = acc

            return viewfunc(request, *args, **kwargs)
        return wrapper
    return decorator
