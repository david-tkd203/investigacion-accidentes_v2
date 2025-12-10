from pathlib import Path
import json
from accidentes.models import Accidentes

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

class AccidenteService:
    @staticmethod
    def fetch_accidente_por_codigo(codigo):
        try:
            return Accidentes.objects.select_related(
                "trabajador", "centro", "usuario"
            ).get(codigo_accidente=codigo)
        except Accidentes.DoesNotExist:
            return None
