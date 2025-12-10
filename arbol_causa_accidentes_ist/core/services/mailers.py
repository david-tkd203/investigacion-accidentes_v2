# core/services/mailers.py
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)

def _abs_url(path: str, request=None) -> str:
    if request:
        protocol = "https" if request.is_secure() else "http"
        domain = request.get_host()
    else:
        protocol = getattr(settings, "DEFAULT_LINK_PROTOCOL", "http")
        domain   = getattr(settings, "DEFAULT_LINK_DOMAIN", "20.106.186.24")
    return f"{protocol}://{domain}{path}"

def send_case_assigned_email(case, assigned_user, assigned_by=None, request=None) -> bool:
    """
    Envía email al usuario asignado a un caso (primera asignación).
    Las plantillas viven en accounts/templates/assignation/.
    """
    if not assigned_user or not assigned_user.email:
        logger.warning("send_case_assigned_email: usuario sin email → no se envía")
        return False

    # Ajusta al name real de tu vista de detalle del caso:
    try:
        path = reverse("accidentes:detalle", kwargs={"accidente_id": case.pk})
    except Exception:
        path = reverse("accidentes:home")

    ctx = {
        "user": assigned_user,
        "case": case,
        "case_url": _abs_url(path, request),
        "assigned_by": assigned_by,
        "site_name": getattr(settings, "SITE_NAME", "Sistema de Investigación"),
    }

    # 👉 rutas refactorizadas a accounts/templates/assignation/
    subject = render_to_string("assignation/case_assigned_subject.txt", ctx).strip()
    html_body = render_to_string("assignation/case_assigned_email.html", ctx)

    msg = EmailMultiAlternatives(subject=subject, body=html_body, to=[assigned_user.email])
    msg.attach_alternative(html_body, "text/html")
    ok = msg.send()
    logger.info("case assigned email: enviado=%s → to=%s case_id=%s", ok, assigned_user.email, case.pk)
    return bool(ok)
