# accidentes/utils/notification.py

from django.contrib import messages

class NotificationMixin:
    """
    Mixin para centralizar el envío de notificaciones tipo Django-Messages.
    Proporciona métodos para success, info, warning y error.
    """
    def notify_success(self, request, text, context_tag="success"):
        messages.success(request, text, extra_tags=context_tag)

    def notify_info(self, request, text, context_tag="info"):
        messages.info(request, text, extra_tags=context_tag)

    def notify_warning(self, request, text, context_tag="warning"):
        messages.warning(request, text, extra_tags=context_tag)

    def notify_error(self, request, text, context_tag="danger"):
        messages.error(request, text, extra_tags=context_tag)
