from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class AccidentesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accidentes"

    def ready(self):
        from accidentes import signals
        # print("✅ [Accidentes] ready(): signals importados")  # DEBUG visible en consola
        logger.info("[Accidentes] ready(): signals importados")
