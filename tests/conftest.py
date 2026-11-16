import os
import tempfile
import pytest

# Ensure all tests use the deterministic FakeLLM with zero network access
os.environ["LLM_MODEL"] = "fake"
# Engine/service tests are hermetic: no mirroring of in-memory state to PostgreSQL
os.environ["EBUDDY_DB_SYNC"] = "off"
os.environ["LITELLM_TELEMETRY"] = "False"
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
# Admin endpoints open unless a test opts in: an ADMIN_TOKEN in the shell or container must not change results
os.environ["ADMIN_TOKEN"] = ""
# Scorecard tests write their reports here instead of overwriting the committed files in docs/
os.environ.setdefault("EBUDDY_REPORTS_DIR", tempfile.mkdtemp(prefix="ebuddy_reports_"))

@pytest.fixture(autouse=True)
def enforce_fake_llm(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "fake")

