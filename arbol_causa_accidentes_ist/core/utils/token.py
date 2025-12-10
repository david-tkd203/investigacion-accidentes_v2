# core/utils/token.py
import base64
import logging
import requests
from django.conf import settings

logger = logging.getLogger("core.utils.token")

DEFAULT_CONNECT_TIMEOUT = 7
DEFAULT_READ_TIMEOUT = 15

class Token(object):
    def __init__(self, api='SIGEA'):
        try:
            cfg = settings.API_ACCESS[api]
            self.client = cfg['CLIENT']
            self.secret = cfg['SECRET']
            self.url = cfg['BASE_URL']
            self.token_endpoint = cfg['TOKEN_ENDPOINT']
            self.ttl = cfg.get('TTL', 0)
            self.grant_type = 'client_credentials'
            source = f"{self.client}:{self.secret}"
            self.encodedCredentials = base64.b64encode(source.encode("utf-8")).decode("utf-8")
            self.token = self.getToken()
            logger.info("Token init para api=%s → token_obtenido=%s", api, bool(self.token))
        except Exception as e:
            logger.exception("No se pudieron leer credenciales para %s: %s", api, e)
            self.client = None
            self.secret = None
            self.url = None
            self.encodedCredentials = None
            self.token = None

    def getToken(self):
        if not self.encodedCredentials or not self.url or not self.token_endpoint:
            logger.error("getToken: configuración incompleta (encoded/url/token_endpoint)")
            return None

        url = self.url.rstrip("/") + "/" + self.token_endpoint.lstrip("/")
        payload = "grant_type=" + self.grant_type
        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
            'Authorization': "Basic " + self.encodedCredentials,
            'cache-control': "no-cache",
        }
        try:
            logger.info("Solicitando access_token a %s", url)
            response = requests.request(
                "POST", url, data=payload, headers=headers,
                timeout=(DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT)
            )
            logger.info("Respuesta token: HTTP %s", response.status_code)
            if response.status_code == 200:
                json_body = {}
                try:
                    json_body = response.json()
                except Exception:
                    logger.error("getToken: respuesta 200 pero JSON inválido")
                    return None

                token = json_body.get('access_token')
                if not token:
                    logger.error("getToken: JSON sin 'access_token'")
                    return None

                self.token = token
                return token
            else:
                # No loguear body completo si puede contener datos sensibles
                logger.error("getToken: HTTP %s. Body (trim): %s", response.status_code, response.text[:500])
                return None

        except requests.RequestException as e:
            logger.exception("getToken: error de red hacia %s: %s", url, e)
            return None
        except Exception as e:
            logger.exception("getToken: excepción no controlada: %s", e)
            return None

    def checkToken(self, token):
        try:
            url = self.url.rstrip("/") + "/oauth/check_token"
            params = {"token": token}
            headers = {
                'Authorization': "Basic " + self.encodedCredentials,
                'cache-control': "no-cache",
            }
            response = requests.request(
                "GET", url, headers=headers, params=params,
                timeout=(DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT)
            )
            logger.info("checkToken: HTTP %s", response.status_code)
            # Deja la lógica original pero añade try/catch
            try:
                first_key = response.text.split(",")[0].split(":")[0][2:-1]
                return first_key != "error"
            except Exception:
                # Si el formato no es el esperado, intenta heurística simple:
                return response.status_code == 200
        except Exception as e:
            logger.exception("checkToken: excepción: %s", e)
            return False

    def query(self, urlMethod, requestMethod, payload="", contentTypeFlag=0):
        if not self.token:
            logger.error("query: token no disponible (None)")
            return None

        url = self.url.rstrip("/") + "/" + urlMethod.lstrip("/")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "cache-control": "no-cache",
        }
        if contentTypeFlag == 1:
            headers["Content-Type"] = "application/json"

        try:
            logger.info("IST request %s %s", requestMethod, url)
            # Evita imprimir payload completo si contiene HTML; loguea tamaño
            try:
                size = len(payload or "")
            except Exception:
                size = -1
            logger.info("Payload size: %s bytes", size)

            result = requests.request(
                requestMethod, url, data=payload, headers=headers,
                timeout=(DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT)
            )

            body_preview = ""
            try:
                body_preview = result.text[:500]
            except Exception:
                body_preview = "<no readable body>"

            logger.info("IST response: HTTP %s body=%s", result.status_code, body_preview)
            return result

        except requests.RequestException as e:
            logger.exception("query: error de red hacia %s: %s", url, e)
            return None
        except Exception as e:
            logger.exception("query: excepción no controlada: %s", e)
            return None
