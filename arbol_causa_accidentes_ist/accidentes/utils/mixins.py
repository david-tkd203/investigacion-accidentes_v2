# accidentes/utils/mixins.py
from django.http import HttpResponseRedirect
from django.urls import reverse
import logging
logger = logging.getLogger(__name__)

class AnchorRedirectMixin:
    anchor_param = "anchor"

    def _build_redirect(self, request, url_name, args=None, anchor=None):
        url = reverse(url_name, args=args or [])
        if anchor:
            url = f"{url}#{anchor}"
        return HttpResponseRedirect(url)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        try:
            if getattr(response, "status_code", None) == 302:
                anchor = request.POST.get(self.anchor_param)
                if anchor:
                    loc = response["Location"].split("#")[0]
                    response["Location"] = f"{loc}#{anchor}"
        except Exception as e:
            logger.exception("AnchorRedirectMixin.post: error ajustando Location: %s", e)
        return response


class AccidenteScopedByCodigoMixin:
    """
    Expone self.accidente a partir de <codigo> (kwargs) validando alcance
    con get_accidente_scoped_or_404. Stateless por defecto.
    """
    codigo_url_kwarg = "codigo"
    select_related = (
        "empresa", "empresa__holding",
        "centro", "centro__empresa",
        "trabajador", "usuario_asignado",
    )
    sync_session = False      # ⬅️ stateless
    login_url = "/accounts/login/"

    accidente = None  # se llena en dispatch

    def get_codigo(self):
        return self.kwargs.get(self.codigo_url_kwarg)

    def accidente_from(self, codigo):
        # import diferido para evitar ciclos
        from accidentes.access import get_accidente_scoped_or_404
        acc = get_accidente_scoped_or_404(
            user=self.request.user,
            codigo=codigo,
            select_related=self.select_related,
        )
        if self.sync_session:
            try:
                self.request.session["accidente_id"] = acc.pk
            except Exception:
                logger.debug("No se pudo sincronizar accidente_id en sesión.")
        self.accidente = acc
        return acc

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        codigo = self.get_codigo()
        if codigo and self.accidente is None:
            self.accidente_from(codigo)  # deja propagar 404/PermissionDenied si corresponde
        return super().dispatch(request, *args, **kwargs)


class AccidenteAccessMixin(AccidenteScopedByCodigoMixin):
    pass
