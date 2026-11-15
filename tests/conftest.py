import os
import pytest

# Ensure all tests operate with zero outbound network calls
os.environ["LLM_MODEL"] = ""
os.environ["LITELLM_TELEMETRY"] = "False"
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"

@pytest.fixture(autouse=True)
def block_llm_network(monkeypatch):
    """Enforce zero-outbound network access for LLMs during test runs."""
    monkeypatch.setenv("LLM_MODEL", "")
    monkeypatch.setenv("LITELLM_TELEMETRY", "False")
    monkeypatch.setenv("LITELLM_LOCAL_MODEL_COST_MAP", "True")
