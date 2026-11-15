# Course Recommender Status & Checklists

Last Updated: 2026-11-15 (Phase G Skill-Mapping Coverage Fix & Proposal Complete)

## 1. Feature Checklist

### DONE (Verified Green)
- [x] **Skill-Mapping Coverage Fix (`app/recommender/retrieval.py`)**:
  - For courses without `course_skill` rows, final relevance score is computed as `0.85 * text_score` (instead of being penalized to 30%).
  - Courses with `course_skill` rows maintain `0.7 * skill + 0.3 * text`.
  - Mapped and unmapped courses are now directly comparable. `CS4L003` (*Artificial Intelligence*) scores `0.5667 > 0.5` for goal *"Software engineering role"*.
  - Verified with `test_unmapped_course_scoring_comparable`.
- [x] **Proposed Skill Mapping Table (`docs/proposed_course_skill.csv`)**:
  - Generated proposed mapping for the 34 slot-candidate courses missing from `course_skill.csv`.
  - Strictly references valid `skill_id`s from `skill.csv`.
  - Skipped unmatchable courses (e.g. `ML4L012 Materials in archaeology`) per instructions.
  - Zero modifications made to `data/` seed files pending user approval.
- [x] **Audit of Existing `course_skill.csv` Mappings**:
  - Identified 11 anomalous or erroneous existing rows in `data/seed/kb/course_skill.csv` (e.g. `EC6L005 Statistical Signal Processing` -> `SKILL_EMBEDDED_SYSTEMS`, `EE3L008 Soft Computing` -> `SKILL_POWER_ELECTRONICS`).
- [x] **Intent Determination & Topic Fallback (`app/recommender/retrieval.py` & `app/recommender/engine.py`)**:
  - Pure Python rule-based tokenizer, stopword filtering, and suffix stemming (`light_stem`).
  - Generic noise words (`system`, `systems`, `engineering`, `technology`, `design`, `analysis`, `introduction`, `advanced`) filtered from retrieval stoplist.
  - Queries with no topic terms (e.g. *"what course should I take this semester"*) cleanly fall back to `intent.source = "profile_goal"`.
  - Added `intent.query_had_topic: bool` (False for generic queries, True for topical queries).
  - Expanded `GOAL_EXPANSION` across software, ai, machine learning, data science, vlsi, embedded, power, signal, material, research, gate.
- [x] **Completed Courses & Backlog Handling (`app/recommender/engine.py`)**:
  - `completed` = inferred core of all earlier semesters UNION explicit student `completed` list, MINUS optional request field `backlogs: list[str]`.
  - Explicit list never disables inference; students only list un-cleared core courses in `backlogs`.
  - Tested with EE Sem 7: `CS1L001` is inferred completed by default; adding `backlogs: ["CS1L001"]` correctly triggers prerequisite rejection for `CS4L003`.
- [x] **Relevance Honesty & Match Thresholding (`app/recommender/engine.py`)**:
  - `MIN_RELEVANCE = 0.2` constant enforced.
  - `weak_match: bool` flagged when best score is below `0.20`.
  - `no_direct_match: bool` flagged when best score is `0.0`.
  - Explanation honestly communicates when no courses strongly match rather than falsely claiming relevance.
- [x] **Multi-Slot Credit Budgeting (`app/recommender/credits.py` & `app/recommender/engine.py`)**:
  - `open_slot_info()` parses slot definition rows (`Lateral`, `Breadth`, `Elective`) without concrete codes.
  - Computes `open_slots`, `min_credits_needed`, `max_credits_needed`, and `slot_credit_status` (`"sufficient"`, `"tight"`, `"insufficient"`).
  - Explicitly states slot headroom and warns when choices are tight.
- [x] **Future Elective Options (`app/recommender/engine.py`)**:
  - Computes `future_options`: top 3 goal-relevant courses from later semesters' slots for the same branch.
  - Reports course code, title, credits, semester, relevance score, and missing prerequisites.
- [x] **Template Formatting & Grammar (`app/recommender/explain.py`)**:
  - Removed duplicate course code display (e.g. `**EE3L005** (EE3L005 ...)` -> `**EE3L005**: ...`).
  - Removed duplicated provider tags (e.g. `(NPTEL) (NPTEL)` -> single reference).
  - Fixed grammatical phrasing (`"eligible elective matching semester slot criteria"`).
- [x] **LLM Visibility & Error Transparency (`app/recommender/explain.py` & `app/recommender/api.py`)**:
  - Added `llm_used: bool` and `llm_error: Optional[str]` to `/recommend` response.
  - Logs exceptions at `WARNING` without leaking sensitive secrets.
  - Strict hallucination guard replaces uncited course codes with deterministic template fallback.
- [x] **FastAPI Route & Contract (`app/recommender/api.py`)**:
  - Registered in `app/main.py`.
  - `RecommendRequest` includes `backlogs: List[str]`.
  - `RecommendResponse` includes `answer`, `llm_used`, `llm_error`, `data`.
  - Validates branch (`EE`, `MME`) and semester range (`1` to `8`).
- [x] **Air-gap & Zero-Network Safety**:
  - `LITELLM_LOCAL_MODEL_COST_MAP=True` and `LITELLM_TELEMETRY=False` enforced at import time in `app/llm/client.py` and `tests/conftest.py`.
  - Autouse fixture in `tests/conftest.py` ensuring zero outbound network calls during tests.
  - Architectural boundaries in `tests/unit/test_import_boundaries.py` pass 100%.

### PARTIAL
- None.

### MISSING
- None.

### BROKEN
- None. All 42 tests pass cleanly across the repository.

---

## 2. Configuration & Where LLM Environment Variables Are Read

### 1. `app/config.py` (Pydantic BaseSettings)
- Class `Settings(BaseSettings)` reads configuration with `env_file=".env", env_file_encoding="utf-8"`.
- Loading order / precedence:
  1. **Shell Environment Variables** (highest precedence, e.g. `$env:LLM_MODEL = "openai/gpt-4o-mini"`).
  2. **`.env` file in the project root** (`LLM_MODEL=openai/gpt-4o-mini`, `LLM_API_KEY=your_key_here`).
  3. Default values declared in `Settings`.

### 2. `app/llm/client.py` (LLM Client Gateway)
- Reads dynamically on each call:
  ```python
  model = os.getenv("LLM_MODEL", self.model)
  api_key = os.getenv("LLM_API_KEY", self.api_key or "")
  api_base = os.getenv("LLM_API_BASE", self.api_base or "")
  ```
- To configure live LLM access:
  - Add to `.env`:
    ```ini
    LLM_MODEL=openai/gpt-4o-mini
    LLM_API_KEY=sk-...
    ```
  - Or set in PowerShell:
    ```powershell
    $env:LLM_MODEL = "openai/gpt-4o-mini"
    $env:LLM_API_KEY = "sk-..."
    ```

---

## 3. Test Verification Summary

Command executed:
```powershell
python -m pytest tests/test_recommender.py tests/unit/test_import_boundaries.py tests/test_db_free.py tests/conformance/test_persona_conformance.py tests/integration/test_walking_skeleton.py -v
```

Output:
```text
======================= 42 passed, 1 warning in 11.20s ========================
```

Key verified test suites:
- `tests/test_recommender.py`: 20 passed (including `test_unmapped_course_scoring_comparable`, determinism, credit limits, prerequisite checks, fallback templates, hallucination guard, MME duplicate codes, intent fallback, backlogs, relevance honesty, future options, multi-slot credits, template formatting, mocked LLM path, API validation & visibility).
- `tests/unit/test_import_boundaries.py`: 4 passed (clean LiteLLM isolation, engine boundaries, KB boundaries, contracts isolation).
- `tests/test_db_free.py`: 9 passed (env compliance, docker ignore, air-gap flags, seed data).
- `tests/conformance/test_persona_conformance.py`: 8 passed (all 8 persona gates).
- `tests/integration/test_walking_skeleton.py`: 1 passed (end-to-end walking skeleton).

---

## 4. Commands to Run & Test

### Run Pytest Test Suite
```powershell
python -m pytest tests/test_recommender.py tests/unit/test_import_boundaries.py -v
```

### Start Local Backend
```powershell
uvicorn app.main:app --reload --port 8000
```

### PowerShell API Test Invocation
```powershell
$body = @{
    branch = "EE"
    semester = 7
    cgpa = 8.0
    goal = "Software engineering role"
    query = "what course should I take this semester"
    completed = @("EE1L001")
    avoid = @()
    backlogs = @()
    overload_approved = $false
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/recommend" -Method Post -ContentType "application/json" -Body $body
$response | ConvertTo-Json -Depth 5
```
