import os
import time
import json
import logging
from typing import Dict, Any, Optional
from app.llm.fake import FakeLLM

logger = logging.getLogger("ebuddy.llm")

# Check if offline / fake model selected
USE_FAKE = os.getenv("LLM_MODEL", "fake").lower() in ["fake", "test", "mock", ""]

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
        model = os.getenv("LLM_MODEL", self.model).lower()
        api_key = os.getenv("LLM_API_KEY", self.api_key or "")
        if (
            os.getenv("PYTEST_CURRENT_TEST")
            or model in ["fake", "test", "mock", ""]
            or not api_key
            or api_key.startswith("your_api_key")
        ):
            res = self.fake.complete(prompt, schema)
            duration_ms = int((time.time() - start_t) * 1000)
            self._log_call("fake-deterministic", purpose, len(prompt)//4, 50, duration_ms)
            return res

        # Real LiteLLM Call with airgap and cost map settings
        try:
            import litellm
            # Enforce airgap flags
            litellm.telemetry = False
            litellm.local_model_cost_map = True

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
            logger.warning(f"LiteLLM call failed ({str(e)}), falling back to deterministic template.")
            duration_ms = int((time.time() - start_t) * 1000)
            self._log_call(f"{self.model}-fallback", purpose, len(prompt)//4, 50, duration_ms)
            return self.fake.complete(prompt, schema)

    def completion(
        self,
        messages: Any,
        temperature: float = 0.2,
        timeout: int = 30,
        num_retries: int = 2,
        purpose: str = "recommender_explanation",
    ) -> Optional[str]:
        """Direct chat completion through LiteLLM reading config dynamically from env vars."""
        start_t = time.time()
        model = os.getenv("LLM_MODEL", self.model)
        api_key = os.getenv("LLM_API_KEY", self.api_key or "")
        api_base = os.getenv("LLM_API_BASE", self.api_base or "")

        if (
            os.getenv("PYTEST_CURRENT_TEST")
            or not model
            or model.lower() in ["fake", "test", "mock", ""]
            or not api_key
            or api_key.startswith("your_api_key")
        ):
            return None

        try:
            import litellm
            litellm.telemetry = False
            litellm.local_model_cost_map = True

            kwargs: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "timeout": timeout,
                "num_retries": num_retries,
            }
            if api_base:
                kwargs["api_base"] = api_base
            if api_key:
                kwargs["api_key"] = api_key

            response = litellm.completion(**kwargs)
            duration_ms = int((time.time() - start_t) * 1000)
            raw_text = response.choices[0].message.content
            prompt_toks = getattr(response.usage, "prompt_tokens", 50)
            comp_toks = getattr(response.usage, "completion_tokens", len(raw_text) // 4)
            self._log_call(model, purpose, prompt_toks, comp_toks, duration_ms)
            return raw_text
        except Exception as e:
            logger.warning(f"LiteLLM completion failed ({str(e)}), returning None for template fallback.")
            return None

# Global singleton client
llm_client = LLMClient()
