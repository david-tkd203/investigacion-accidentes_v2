from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        """
        Aquí NO tocamos la base de datos.
        Solo cargamos señales.
        """
        import accounts.signals