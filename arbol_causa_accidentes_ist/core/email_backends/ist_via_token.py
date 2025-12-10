# core/email_backends/ist_via_token.py
import logging
import sys
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from core.services.apiemail import send_simple_mail

logger = logging.getLogger("core.email_backends")

def _extract_html(message: EmailMultiAlternatives) -> str:
    if getattr(message, "alternatives", None):
        for content, mimetype in message.alternatives:
            if "html" in mimetype:
                return content
    return message.body or ""

class EmailBackend(BaseEmailBackend):
    """
    Email backend que usa tu Token y tu apiemail.send_simple_mail,
    para enviar con el JSON del endpoint 'sendEmailUnit/emails'.
    """
    def send_messages(self, email_messages):
        print(">>> HIT EmailBackend.send_messages", file=sys.stderr)
        logger.info("EmailBackend.send_messages: count=%s", len(email_messages) if email_messages else 0)

        if not email_messages:
            return 0

        sent = 0
        costumer_load_email = getattr(settings, "IST_EMAIL_ACTOR", "asistente@ist.cl")
        name_from_send = getattr(settings, "IST_EMAIL_FROM_NAME", "Asistente de Investigación de Accidentes")
        ip = getattr(settings, "IST_EMAIL_SOURCE_IP", "")

        for idx, msg in enumerate(email_messages, start=1):
            try:
                logger.info("[msg %s] subject=%r", idx, getattr(msg, "subject", None))
                logger.info("[msg %s] to=%s", idx, getattr(msg, "to", None))
                logger.info("[msg %s] cc=%s", idx, getattr(msg, "cc", None))
                logger.info("[msg %s] bcc=%s", idx, getattr(msg, "bcc", None))

                recipients = list(msg.to or [])
                if not recipients:
                    logger.warning("[msg %s] sin destinatarios: no se enviará", idx)
                    continue

                html_body = _extract_html(msg) or ""
                logger.info("[msg %s] invocando send_simple_mail(...) a %s", idx, recipients)

                ok = send_simple_mail(
                    subject=msg.subject or "",
                    body=html_body,
                    recipient=recipients,     # lista ["usuario@..."]
                    copy_recipient=None,       # reset: sin CC
                    hidden_copy=None,          # reset: sin CCO
                    costumer_load_email=costumer_load_email,
                    name_from_send=name_from_send,
                    ip=ip,
                )

                logger.info("[msg %s] resultado API IST: %s", idx, ok)
                if ok:
                    sent += 1
                else:
                    logger.warning("[msg %s] API IST no confirmó envío (status != ok)", idx)

            except Exception as e:
                logger.exception("[msg %s] excepción en EmailBackend: %s", idx, e)
                # seguir con el siguiente mensaje
                continue

        logger.info("EmailBackend.send_messages: enviados=%s", sent)
        return sent
