import os
from dotenv import load_dotenv
load_dotenv()
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
import litellm
litellm.telemetry = False
litellm.drop_params = True

import json
import logging
import re
import time
from typing import Any, Dict, Optional

from app.llm.fake import FakeLLM

logger = logging.getLogger("ebuddy.llm")

# Check if offline / fake model selected
USE_FAKE = os.getenv("LLM_MODEL", "fake").lower() in ["fake", "test", "mock", ""]


def sanitize_error(msg: str, api_key: Optional[str] = None) -> str:
    """Strip API keys and sensitive tokens matching 'AQ.' or provider keys."""
    if not msg:
        return "Unknown error"
    s = str(msg)
    if api_key and len(api_key) > 4:
        s = s.replace(api_key, "[REDACTED]")
    # Never include the API key or any text matching "AQ." in it
    s = re.sub(r"AQ\.[A-Za-z0-9_\-]+", "[REDACTED]", s)
    s = re.sub(r"AIza[0-9A-Za-z-_]{35}", "[REDACTED]", s)
    s = re.sub(r"sk-[A-Za-z0-9_\-]{20,}", "[REDACTED]", s)
    return s


def classify_error(e: Exception) -> str:
    """Classify exception into standard error name and status code."""
    status_code = getattr(e, "status_code", None) or getattr(e, "code", None)
    err_type = type(e).__name__
    err_msg = str(e)

    # 503 / Service Unavailable
    if (
        isinstance(e, getattr(litellm.exceptions, "ServiceUnavailableError", ()))
        or status_code == 503
        or "503" in err_msg
        or "ServiceUnavailable" in err_type
    ):
        return "ServiceUnavailableError 503"

    # 429 / Rate Limit
    if (
        isinstance(e, getattr(litellm.exceptions, "RateLimitError", ()))
        or status_code == 429
        or "429" in err_msg
        or "RateLimit" in err_type
    ):
        return "RateLimitError 429"

    # Timeout
    if (
        isinstance(e, (getattr(litellm.exceptions, "Timeout", ()), TimeoutError))
        or "timeout" in err_msg.lower()
        or "Timeout" in err_type
    ):
        return "Timeout"

    # Auth (401, 403)
    if (
        isinstance(e, (getattr(litellm.exceptions, "AuthenticationError", ()), getattr(litellm.exceptions, "PermissionDeniedError", ())))
        or status_code in (401, 403)
        or "401" in err_msg
        or "403" in err_msg
        or "Authentication" in err_type
        or "PermissionDenied" in err_type
    ):
        code_str = f" {status_code}" if status_code else " 401"
        return f"AuthenticationError{code_str}"

    # 404 / Not Found
    if (
        isinstance(e, getattr(litellm.exceptions, "NotFoundError", ()))
        or status_code == 404
        or "404" in err_msg
        or "NotFound" in err_type
    ):
        return "NotFoundError 404"

    clean_msg = sanitize_error(err_msg)
    code_part = f" {status_code}" if status_code else ""
    return f"{err_type}{code_part}: {clean_msg}"


def is_transient_error(e: Exception) -> bool:
    """Check whether error is transient (503, 429, timeout) and safe to retry."""
    status_code = getattr(e, "status_code", None) or getattr(e, "code", None)
    err_type = type(e).__name__
    err_msg = str(e).lower()

    # Do not retry auth or 404 errors
    if isinstance(e, (
        getattr(litellm.exceptions, "AuthenticationError", ()),
        getattr(litellm.exceptions, "PermissionDeniedError", ()),
        getattr(litellm.exceptions, "NotFoundError", ()),
    )):
        return False
    if status_code in (401, 403, 404):
        return False
    if "auth" in err_msg or "not found" in err_msg or "401" in err_msg or "404" in err_msg:
        return False

    # Retry transient errors: 503, 429, timeout
    if isinstance(e, (
        getattr(litellm.exceptions, "ServiceUnavailableError", ()),
        getattr(litellm.exceptions, "RateLimitError", ()),
        getattr(litellm.exceptions, "Timeout", ()),
        TimeoutError,
    )):
        return True
    if status_code in (503, 429):
        return True
    if "503" in err_msg or "429" in err_msg or "timeout" in err_msg:
        return True

    return False


class LLMClient:
    """
    Unified LLM Gateway client.
    Hard Rule: This is the ONLY module in the entire application that imports litellm.
    """
    def __init__(self):
        self.model = os.getenv("LLM_MODEL", "fake")
        self.api_base = os.getenv("LLM_API_BASE")
        self.api_key = os.getenv("LLM_API_KEY")
        self.fake = FakeLLM()
        self.last_error: Optional[str] = None

    def _log_call(self, model: str, purpose: str, prompt_tokens: int, completion_tokens: int, duration_ms: int, student_id: Optional[str] = None):
        try:
            import psycopg
            conn = psycopg.connect("postgresql://ebuddy_user:ebuddy_password@127.0.0.1:5432/ebuddy", connect_timeout=2)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ops.llm_call_log 
                    (student_id, model_name, purpose, prompt_tokens, completion_tokens, cost_usd, duration_ms)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (student_id, model, purpose, prompt_tokens, completion_tokens, 0.0, duration_ms)
                )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"Unable to write to ops.llm_call_log: {e}")

    def generate(self, prompt: str, schema: Optional[Dict[str, Any]] = None, timeout: int = 15, purpose: str = "general") -> Dict[str, Any]:
        start_t = time.time()
        self.last_error = None
        model = os.getenv("LLM_MODEL", self.model).lower()
        api_key = os.getenv("LLM_API_KEY", self.api_key or "")
        if (
            model in ["fake", "test", "mock", ""]
            or not api_key
            or api_key.startswith("your_api_key")
        ):
            res = self.fake.complete(prompt, schema)
            duration_ms = int((time.time() - start_t) * 1000)
            self._log_call("fake-deterministic", purpose, len(prompt)//4, 50, duration_ms)
            return res

        # Real LiteLLM Call with airgap and cost map settings
        try:
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "timeout": timeout,
                "temperature": 0.0
            }
            if self.api_base:
                kwargs["api_base"] = self.api_base
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if schema:
                kwargs["response_format"] = {"type": "json_object"}

            response = litellm.completion(**kwargs)
            duration_ms = int((time.time() - start_t) * 1000)
            raw_text = response.choices[0].message.content

            prompt_toks = getattr(response.usage, "prompt_tokens", len(prompt)//4)
            comp_toks = getattr(response.usage, "completion_tokens", len(raw_text)//4)
            self._log_call(self.model, purpose, prompt_toks, comp_toks, duration_ms)

            if schema:
                try:
                    return json.loads(raw_text)
                except Exception:
                    # Fallback retry once or return FakeLLM deterministic response
                    return self.fake.complete(prompt, schema)
            return {"content": raw_text}

        except Exception as e:
            err_classified = classify_error(e)
            self.last_error = sanitize_error(err_classified, api_key)
            logger.warning(f"LiteLLM call failed ({self.last_error}), falling back to deterministic template.")
            duration_ms = int((time.time() - start_t) * 1000)
            self._log_call(f"{self.model}-fallback", purpose, len(prompt)//4, 50, duration_ms)
            return self.fake.complete(prompt, schema)

    def completion(
        self,
        messages: Any,
        temperature: float = 0.2,
        timeout: int = 45,
        num_retries: int = 2,
        purpose: str = "recommender_explanation",
    ) -> Optional[str]:
        """Direct chat completion through LiteLLM reading config dynamically from env vars with transient retry."""
        start_t = time.time()
        self.last_error = None
        model = os.getenv("LLM_MODEL", self.model)
        api_key = os.getenv("LLM_API_KEY", self.api_key or "")
        api_base = os.getenv("LLM_API_BASE", self.api_base or "")

        if not model or model.lower() in ["fake", "test", "mock", "none", ""]:
            self.last_error = "LLM_MODEL not configured"
            return None

        if not api_key or api_key.startswith("your_api_key"):
            self.last_error = "LLM_API_KEY not configured"
            return None

        # Retry transient errors (503, 429, timeout) up to 2 times with backoff 1s then 3s,
        # total time bounded by the request timeout. Do not retry auth or 404 errors.
        backoffs = [1.0, 3.0]
        max_attempts = 1 + min(num_retries, len(backoffs))

        for attempt in range(max_attempts):
            elapsed = time.time() - start_t
            remaining_time = timeout - elapsed
            if remaining_time <= 0:
                self.last_error = "Timeout"
                logger.warning(f"LiteLLM call timed out after {elapsed:.1f}s (budget: {timeout}s)")
                return None

            try:
                kwargs: Dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "timeout": max(1, int(remaining_time)),
                }
                if api_base:
                    kwargs["api_base"] = api_base
                if api_key:
                    kwargs["api_key"] = api_key

                response = litellm.completion(**kwargs)
                duration_ms = int((time.time() - start_t) * 1000)

                choice = response.choices[0]
                raw_text = choice.message.content
                finish_reason = getattr(choice, "finish_reason", "unknown")

                if not raw_text or not raw_text.strip():
                    self.last_error = f"empty_content finish_reason={finish_reason}"
                    logger.warning(f"LiteLLM returned empty content with finish_reason={finish_reason}")
                    return None

                prompt_toks = getattr(response.usage, "prompt_tokens", 50)
                comp_toks = getattr(response.usage, "completion_tokens", len(raw_text) // 4)
                self._log_call(model, purpose, prompt_toks, comp_toks, duration_ms)
                return raw_text

            except Exception as e:
                err_classified = classify_error(e)
                self.last_error = sanitize_error(err_classified, api_key)
                logger.warning(
                    f"LiteLLM completion attempt {attempt + 1}/{max_attempts} failed: {self.last_error}"
                )

                # Check if error is transient and we have remaining retries
                if attempt < len(backoffs) and is_transient_error(e):
                    sleep_time = backoffs[attempt]
                    if (time.time() - start_t) + sleep_time >= timeout:
                        self.last_error = "Timeout"
                        logger.warning(f"Cannot retry; backoff sleep ({sleep_time}s) would exceed timeout ({timeout}s)")
                        return None
                    time.sleep(sleep_time)
                    continue

                # Non-transient error (e.g. auth, 404) or exhausted retries
                return None

        return None


# Global singleton client
llm_client = LLMClient()
