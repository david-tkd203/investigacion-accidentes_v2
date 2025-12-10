# core/services/apiemail.py
import json
import logging
from django.conf import settings
from core.utils.token import Token

logger = logging.getLogger("core.services.apiemail")

def _omit_empty(d: dict) -> dict:
    """Devuelve un dict sin claves con valor None/[]/'' para calzar el ejemplo exacto cuando no hay CC/BCC/attachments."""
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}

def create_email_dto(body, subject, recipient, copy_recipient=None, hidden_copy_recipient=None, attachments=None, type_email_body=1):
    dto = {
        "body": body,
        "subject": subject,
        "recipient": recipient,
        "typeEmailBody": type_email_body,
    }
    if copy_recipient:
        dto["copyRecipient"] = copy_recipient
    if hidden_copy_recipient:
        dto["hiddenCopyRecipient"] = hidden_copy_recipient
    if attachments:
        dto["attachments"] = attachments
    return dto

def create_mail_unit(costumer_load_email, save_in_ftp, name_from_send, ip, email_dto):
    costumer_id = settings.API_ACCESS["API_EMAIL"]["CLIENT"]
    costumer_secret = settings.API_ACCESS["API_EMAIL"]["SECRET"]
    email_from_send = getattr(settings, "IST_EMAIL_FROM_EMAIL", costumer_load_email)
    mail_unit = {
        "costumerLoadEmail": costumer_load_email,
        "costumerId": costumer_id,
        "costumerSecret": costumer_secret,
        "idTramite": 0,
        "saveInFTP": bool(save_in_ftp),
        "emailFromSend": email_from_send,
        "nameFromSend": name_from_send,
        "IP": ip or "",
        "email": email_dto,
    }
    # Si deseas omitir claves vacías a nivel raíz, aplica _omit_empty también aquí.
    return mail_unit

def send_simple_mail(subject, body, recipient, copy_recipient, hidden_copy, costumer_load_email, name_from_send, ip):
    try:
        if not recipient:
            logger.error("send_simple_mail: recipient vacío → no se envía")
            return False

        logger.info("apiemail: preparando envío → to=%s subject=%r", recipient, subject)

        email_dto = create_email_dto(
            body=body or "",
            subject=subject or "",
            recipient=recipient,
            copy_recipient=copy_recipient,
            hidden_copy_recipient=hidden_copy,
            attachments=None,
            type_email_body=1,
        )
        mail_unit = create_mail_unit(
            costumer_load_email=costumer_load_email,
            save_in_ftp=False,
            name_from_send=name_from_send,
            ip=ip,
            email_dto=email_dto,
        )
        json_request = json.dumps(mail_unit)

        tk = Token(api="API_EMAIL")
        if not tk.token:
            logger.error("apiemail: no se obtuvo token (Token.token is None)")
            return False

        logger.info("apiemail: POST sendEmailUnit/emails (payload size=%d)", len(json_request))
        request_result = tk.query("sendEmailUnit/emails", "POST", json_request, 1)

        if request_result is None:
            logger.error("apiemail: Token.query devolvió None")
            return False

        status = request_result.status_code
        logger.info("apiemail: respuesta HTTP %s", status)

        data = {}
        try:
            data = request_result.json()
        except Exception:
            logger.warning("apiemail: cuerpo no JSON (trim): %s", request_result.text[:300])

        if status >= 400:
            logger.error("apiemail: HTTP error %s body=%s", status, request_result.text[:500])
            return False

        if data.get("status") == "ok":
            logger.info("apiemail: envío aceptado por API IST")
            return True

        logger.warning("apiemail: envío rechazado: %s", data)
        return False

    except Exception as e:
        logger.exception("apiemail: excepción no controlada: %s", e)
        return False
