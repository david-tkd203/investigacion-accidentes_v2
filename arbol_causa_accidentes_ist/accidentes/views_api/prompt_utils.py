# accidentes/views_api/prompt_utils.py

import json
from json import JSONDecodeError
from pathlib import Path
import hashlib
import logging
import random
import time
from typing import Optional

from django.conf import settings
from django.core.cache import cache  # requiere caché configurada (Memcached/Redis/LocMem)
from decouple import Config, RepositoryEnv
from openai import OpenAI

logger = logging.getLogger(__name__)

# ─── Load IA prompts ────────────────────────────────────────────────────────────
PROMPT_FILE = Path(settings.BASE_DIR) / "accidentes" / "setting" / "prompt" / "prompt.json"
with open(PROMPT_FILE, encoding="utf-8") as f:
    PROMPTS = json.load(f)["prompts"]

# ─── OpenAI client setup ───────────────────────────────────────────────────────
ENV_PATH = Path(settings.BASE_DIR) / ".env"
config = Config(repository=RepositoryEnv(ENV_PATH))
openai_client = OpenAI(api_key=config("OPENAI_API_KEY"))

# ─── Config por defecto (puedes ajustar desde settings si quieres) ─────────────
DEFAULT_TIMEOUT_S = getattr(settings, "IA_TIMEOUT_S", 20)
DEFAULT_RETRIES = getattr(settings, "IA_RETRIES", 2)  # reintentos adicionales
DEFAULT_IDEM_TTL_S = getattr(settings, "IA_IDEM_TTL_S", 300)  # 5 min
MAX_PAYLOAD_CHARS = getattr(settings, "IA_MAX_PAYLOAD_CHARS", 50_000)
SINGLE_FLIGHT_LOCK_S = getattr(settings, "IA_SINGLE_FLIGHT_LOCK_S", 30)

# Log de payload (método A)
IA_LOG_PROMPTS = getattr(settings, "IA_LOG_PROMPTS", False)
IA_LOG_PROMPTS_MAX = getattr(settings, "IA_LOG_PROMPTS_MAX", 8000)


# ───────────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────────

def _minify_and_limit(input_str: str, max_chars: int = MAX_PAYLOAD_CHARS) -> str:
    """
    - Si es JSON válido, lo re-dumpa minificado (sin espacios).
    - Si no, colapsa espacios.
    - Si excede el límite, trunca con marca.
    """
    s = (input_str or "").strip()
    if not s:
        return ""

    # ¿Es JSON?
    try:
        obj = json.loads(s)
        s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        # No es JSON → colapsa whitespace
        s = " ".join(s.split())

    if len(s) > max_chars:
        s = s[: max_chars - 12] + " [TRUNCADO]"
        logger.warning("IA payload truncado a %s caracteres", max_chars)
    return s


def _idem_key(prompt_key: str, model: str, payload: str, temperature: Optional[float], top_p: Optional[float]) -> str:
    base = f"{prompt_key}|{model}|{temperature}|{top_p}|{payload}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _sleep_backoff(attempt: int) -> None:
    # attempt: 1..N  → 0.5s, 1.0s, 2.0s ... con jitter ±20%
    base = 0.5 * (2 ** (attempt - 1))
    jitter = random.uniform(-0.2, 0.2) * base
    time.sleep(max(0.1, base + jitter))


def _is_transient_error(exc: Exception) -> bool:
    # Heurística: rate limit, timeouts, 5xx
    msg = str(exc).lower()
    return any(k in msg for k in ["timeout", "rate", "429", "5", "temporar", "retry"])


def _call_openai_text(model: str, temperature: float, top_p: float, system: str, user: str, timeout_s: int) -> str:
    # Nota: la lib moderna de OpenAI acepta 'timeout' (httpx). Si tu versión usa otro nombre,
    # cámbialo por 'request_timeout'.
    resp = openai_client.chat.completions.create(
        model=model,
        temperature=temperature,
        top_p=top_p,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        timeout=timeout_s,  # <- clave
    )
    content = (resp.choices[0].message.content or "").strip()
    return content


# ───────────────────────────────────────────────────────────────────────────────
# API pública
# ───────────────────────────────────────────────────────────────────────────────

def call_ia_text(input_str: str, prompt_key: str,
                 *,
                 timeout_s: int = DEFAULT_TIMEOUT_S,
                 retries: int = DEFAULT_RETRIES,
                 idempotency: bool = True,
                 idem_ttl_s: int = DEFAULT_IDEM_TTL_S) -> str:

    cfg = PROMPTS.get(prompt_key)
    if not cfg:
        raise ValueError(f"Prompt '{prompt_key}' not found")

    model = cfg["model"]
    temperature = cfg.get("temperature", 0.7)
    top_p = cfg.get("top_p", 1.0)

    # Payload que realmente se enviará
    payload = _minify_and_limit(input_str, MAX_PAYLOAD_CHARS)
    if not payload:
        logger.warning("call_ia_text: payload vacío para prompt_key=%s", prompt_key)

    # LOG DEL PAYLOAD (método A)
    if IA_LOG_PROMPTS:
        sample = payload if len(payload) <= IA_LOG_PROMPTS_MAX else payload[:IA_LOG_PROMPTS_MAX] + " [TRUNCADO]"
        logger.debug(
            "[IA REQUEST] prompt=%s model=%s temp=%s top_p=%s len=%s\n%s",
            prompt_key, model, temperature, top_p, len(payload), sample
        )

    idem_key = _idem_key(prompt_key, model, payload, temperature, top_p) if idempotency else None
    cache_key = f"ia:{idem_key}:result" if idem_key else None
    lock_key = f"ia:{idem_key}:lock" if idem_key else None

    # Idempotencia: hit de caché
    if cache_key:
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info("IA idempotencia: HIT prompt=%s", prompt_key)
            return cached

    # Single-flight: acquire lock
    got_lock = False
    if lock_key:
        got_lock = cache.add(lock_key, "1", timeout=SINGLE_FLIGHT_LOCK_S)

    if not got_lock and cache_key:
        # Otra request está resolviendo la misma llamada → espera resultado
        logger.info("IA idempotencia: esperando resultado de otra request (prompt=%s)", prompt_key)
        waited = 0.0
        step = 0.25
        while waited < SINGLE_FLIGHT_LOCK_S:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            time.sleep(step)
            waited += step
        # Lock expiró sin resultado → seguimos y llamamos nosotros.

    attempts = retries + 1
    last_exc = None
    start = time.time()

    for attempt in range(1, attempts + 1):
        try:
            content = _call_openai_text(
                model=model,
                temperature=temperature,
                top_p=top_p,
                system=cfg["instruction"],
                user=payload,
                timeout_s=timeout_s,
            )

            if not content:
                raise RuntimeError("IA devolvió contenido vacío")

            # Cachea resultado para idempotencia
            if cache_key:
                cache.set(cache_key, content, timeout=idem_ttl_s)

            elapsed = int((time.time() - start) * 1000)
            logger.info("IA ok prompt=%s model=%s ms=%s attempt=%s", prompt_key, model, elapsed, attempt)
            return content

        except Exception as e:
            last_exc = e
            is_transient = _is_transient_error(e)
            if attempt < attempts and is_transient:
                logger.warning("IA retry prompt=%s attempt=%s/%s: %s", prompt_key, attempt, attempts, e)
                _sleep_backoff(attempt)
                continue
            # Sin más reintentos o error no transitorio
            logger.error("IA error prompt=%s attempt=%s/%s: %s", prompt_key, attempt, attempts, e)
            break
        finally:
            # Libera lock si eres el poseedor (aunque con caché por TTL no es crítico)
            if got_lock and lock_key:
                cache.delete(lock_key)
    
    # Fallback coherente (no explotar UX)
    raise RuntimeError(f"No se pudo completar la llamada IA para '{prompt_key}': {last_exc}")


def call_ia_json(input_str: str, prompt_key: str = "explora",
                 *,
                 timeout_s: int = DEFAULT_TIMEOUT_S,
                 retries: int = DEFAULT_RETRIES,
                 idempotency: bool = True,
                 idem_ttl_s: int = DEFAULT_IDEM_TTL_S) -> dict:
    """
    Llama a OpenAI esperando JSON.
    - Aplica mismas garantías que call_ia_text.
    - Desfencea bloques ``` si el modelo los agrega.
    """
    cfg = PROMPTS.get(prompt_key)
    if not cfg:
        raise ValueError(f"Prompt '{prompt_key}' not found")

    raw = call_ia_text(
        input_str=input_str,
        prompt_key=prompt_key,
        timeout_s=timeout_s,
        retries=retries,
        idempotency=idempotency,
        idem_ttl_s=idem_ttl_s,
    )

    content = raw.strip()
    if content.startswith("```"):
        lines = content.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    try:
        return json.loads(content)
    except JSONDecodeError:
        logger.error("call_ia_json: contenido inválido para prompt_key=%s len=%s", prompt_key, len(content))
        raise ValueError(f"IA response is not valid JSON:\n{content}")
