import os
import pytest

# Ensure all tests use the deterministic FakeLLM with zero network access
os.environ["LLM_MODEL"] = "fake"
# Engine/service tests are hermetic: no mirroring of in-memory state to PostgreSQL
os.environ["EBUDDY_DB_SYNC"] = "off"
os.environ["LITELLM_TELEMETRY"] = "False"
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"

@pytest.fixture(autouse=True)
def enforce_fake_llm(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "fake")

