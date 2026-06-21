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

# ─── Config por defecto ─────────────────────────────────────────────────────────
IA_PROVIDER_CFG = getattr(settings, "IA_PROVIDER", "openai")
IS_OLLAMA = IA_PROVIDER_CFG == "ollama"
DEFAULT_TIMEOUT_S = getattr(settings, "IA_TIMEOUT_S", 300 if IS_OLLAMA else 20)
DEFAULT_RETRIES = getattr(settings, "IA_RETRIES", 0 if IS_OLLAMA else 2)
SINGLE_FLIGHT_LOCK_S = getattr(settings, "IA_SINGLE_FLIGHT_LOCK_S", 600 if IS_OLLAMA else 30)
DEFAULT_IDEM_TTL_S = getattr(settings, "IA_IDEM_TTL_S", 300)
MAX_PAYLOAD_CHARS = getattr(settings, "IA_MAX_PAYLOAD_CHARS", 50_000)
SINGLE_FLIGHT_LOCK_S = getattr(settings, "IA_SINGLE_FLIGHT_LOCK_S", 30)
IA_LOG_PROMPTS = getattr(settings, "IA_LOG_PROMPTS", False)
IA_LOG_PROMPTS_MAX = getattr(settings, "IA_LOG_PROMPTS_MAX", 8000)

# ─── Lazy clients ───────────────────────────────────────────────────────────────
_openai_client: Optional[OpenAI] = None
_ollama_client: Optional[OpenAI] = None
_groq_client: Optional[OpenAI] = None


def _get_openai_client() -> Optional[OpenAI]:
    global _openai_client
    if _openai_client is None:
        env_path = Path(settings.BASE_DIR) / ".env"
        cfg = Config(repository=RepositoryEnv(env_path))
        api_key = str(cfg("OPENAI_API_KEY", default=""))
        if not api_key or api_key == "sk-placeholder":
            logger.warning("OPENAI_API_KEY no configurada. El cliente OpenAI no estará disponible.")
            return None
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def _get_ollama_client() -> OpenAI:
    global _ollama_client
    if _ollama_client is None:
        base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434/v1")
        _ollama_client = OpenAI(api_key="ollama", base_url=base_url)
    return _ollama_client


def _get_groq_client() -> OpenAI:
    global _groq_client
    if _groq_client is None:
        env_path = Path(settings.BASE_DIR) / ".env"
        cfg = Config(repository=RepositoryEnv(env_path))
        api_key = str(cfg("GROQ_API_KEY", default=""))
        base_url = "https://api.groq.com/openai/v1"
        _groq_client = OpenAI(api_key=api_key, base_url=base_url)
    return _groq_client


# ───────────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────────

def _minify_and_limit(input_str: str, max_chars: int = MAX_PAYLOAD_CHARS) -> str:
    s = (input_str or "").strip()
    if not s:
        return ""
    try:
        obj = json.loads(s)
        s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        s = " ".join(s.split())
    if len(s) > max_chars:
        s = s[: max_chars - 12] + " [TRUNCADO]"
        logger.warning("IA payload truncado a %s caracteres", max_chars)
    return s


def _idem_key(prompt_key: str, model: str, payload: str, temperature: Optional[float], top_p: Optional[float]) -> str:
    base = f"{prompt_key}|{model}|{temperature}|{top_p}|{payload}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _sleep_backoff(attempt: int) -> None:
    base = 0.5 * (2 ** (attempt - 1))
    jitter = random.uniform(-0.2, 0.2) * base
    time.sleep(max(0.1, base + jitter))


def _is_transient_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in ["timeout", "rate", "429", "5", "temporar", "retry", "connection"])


def _call_llm(provider: str, model: str, temperature: float, top_p: float, system: str, user: str, timeout_s: int) -> str:
    """
    Dispatches to the correct LLM provider.
    Both Ollama and OpenAI use the same OpenAI-compatible client interface.
    """
    if provider == "ollama":
        client = _get_ollama_client()
    elif provider == "groq":
        client = _get_groq_client()
    else:
        client = _get_openai_client()

    if client is None:
        logger.warning("Cliente IA no disponible para provider='%s'", provider)
        raise RuntimeError(
            f"Cliente IA no disponible para provider='{provider}'. "
            "Verifica OPENAI_API_KEY en .env o que Ollama esté corriendo."
        )

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            top_p=top_p,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            timeout=timeout_s,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.error("Error en llamada IA provider=%s model=%s: %s", provider, model, e)
        raise


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

    # Provider: env var IA_PROVIDER sobreescribe lo que diga cada prompt
    env_provider = getattr(settings, "IA_PROVIDER", None)
    provider = env_provider or cfg.get("provider", "openai")
    temperature = cfg.get("temperature", 0.7)
    top_p = cfg.get("top_p", 1.0)

    # Modelo según el provider
    if provider == "ollama":
        model = cfg.get("ollama_model") or getattr(settings, "OLLAMA_DEFAULT_MODEL", "qwen2.5:7b")
    elif provider == "groq":
        model = getattr(settings, "GROQ_DEFAULT_MODEL", "llama-3.1-8b-instant")
    else:
        model = cfg.get("model", "gpt-4")

    payload = _minify_and_limit(input_str, MAX_PAYLOAD_CHARS)
    if not payload:
        logger.warning("call_ia_text: payload vacío para prompt_key=%s", prompt_key)

    if IA_LOG_PROMPTS:
        sample = payload if len(payload) <= IA_LOG_PROMPTS_MAX else payload[:IA_LOG_PROMPTS_MAX] + " [TRUNCADO]"
        logger.debug(
            "[IA REQUEST] prompt=%s provider=%s model=%s temp=%s top_p=%s len=%s\n%s",
            prompt_key, provider, model, temperature, top_p, len(payload), sample
        )

    idem_key = _idem_key(prompt_key, model, payload, temperature, top_p) if idempotency else None
    cache_key = f"ia:{idem_key}:result" if idem_key else None
    lock_key = f"ia:{idem_key}:lock" if idem_key else None

    if cache_key:
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info("IA idempotencia: HIT prompt=%s", prompt_key)
            return cached

    got_lock = False
    if lock_key:
        got_lock = cache.add(lock_key, "1", timeout=SINGLE_FLIGHT_LOCK_S)

    if not got_lock and cache_key:
        logger.info("IA idempotencia: esperando resultado de otra request (prompt=%s)", prompt_key)
        waited = 0.0
        step = 0.25
        while waited < SINGLE_FLIGHT_LOCK_S:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            time.sleep(step)
            waited += step

    attempts = retries + 1
    last_exc = None
    start = time.time()

    for attempt in range(1, attempts + 1):
        try:
            content = _call_llm(
                provider=provider,
                model=model,
                temperature=temperature,
                top_p=top_p,
                system=cfg["instruction"],
                user=payload,
                timeout_s=timeout_s,
            )

            if not content:
                raise RuntimeError("IA devolvió contenido vacío")

            if cache_key:
                cache.set(cache_key, content, timeout=idem_ttl_s)

            elapsed = int((time.time() - start) * 1000)
            logger.info("IA ok prompt=%s provider=%s model=%s ms=%s attempt=%s", prompt_key, provider, model, elapsed, attempt)
            return content

        except Exception as e:
            last_exc = e
            is_transient = _is_transient_error(e)
            if attempt < attempts and is_transient:
                logger.warning("IA retry prompt=%s attempt=%s/%s: %s", prompt_key, attempt, attempts, e)
                _sleep_backoff(attempt)
                continue
            logger.error("IA error prompt=%s attempt=%s/%s: %s", prompt_key, attempt, attempts, e)
            break
        finally:
            if got_lock and lock_key:
                cache.delete(lock_key)

    raise RuntimeError(f"No se pudo completar la llamada IA para '{prompt_key}': {last_exc}")


def call_ia_json(input_str: str, prompt_key: str = "explora",
                 *,
                 timeout_s: int = DEFAULT_TIMEOUT_S,
                 retries: int = DEFAULT_RETRIES,
                 idempotency: bool = True,
                 idem_ttl_s: int = DEFAULT_IDEM_TTL_S) -> dict:
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
