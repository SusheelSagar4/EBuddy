# Course Recommender Status & Checklists

Last Updated: 2026-11-15 (Phase G Enhancements Complete & Verified)

## 1. Feature Checklist

### DONE (Verified Green)
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
  - Explicitly states slot headroom and warns when choices are tight (e.g. headroom 7 vs two 4-credit electives requiring 8).
- [x] **Future Elective Options (`app/recommender/engine.py`)**:
  - Computes `future_options`: top 3 goal-relevant courses from later semesters' slots for the same branch.
  - Reports course code, title, credits, semester, relevance score, and missing prerequisites.
  - Highlighted in explanation to aid academic roadmapping.
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
- None. All 41 tests pass cleanly across the repository.

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
======================= 41 passed, 1 warning in 11.01s ========================
```

Key verified test suites:
- `tests/test_recommender.py`: 19 passed (determinism, credit limits, prerequisite checks, fallback templates, hallucination guard, MME duplicate codes, intent fallback, backlogs, relevance honesty, future options, multi-slot credits, template formatting, mocked LLM path, API validation & visibility).
- `tests/unit/test_import_boundaries.py`: 4 passed (clean LiteLLM isolation, engine boundaries, KB boundaries, contracts isolation).
- `tests/test_db_free.py`: 9 passed (env compliance, docker ignore, air-gap flags, seed data).
- `tests/conformance/test_persona_conformance.py`: 8 passed (all 8 persona gates).
- `tests/integration/test_walking_skeleton.py`: 1 passed (end-to-end walking skeleton).

---

## 4. Sanity Report

### Case 1: EE Semester 5
- **Request**: Branch: `EE`, Semester: `5`, CGPA: `7.8`, Goal: `"Software engineering role"`, Query: `"what course should I take this semester"`
- **Intent**: `source`: `"profile_goal"`, `query_had_topic`: `False`, terms: `['algorithm', 'artifici', 'cod', 'compu', 'data', 'database', 'develop', 'embedd', 'intelligence', 'machine', 'oop', 'programm', 'python', 'software', 'structur']`
- **Budget**: Limit: `25.0`, Core Credits: `18.0`, Headroom: `7.0`, Open Slots: `2` (requires min `6.0` cr, max `7.0` cr), Status: `"sufficient"`
- **Match Status**: `weak_match`: `True`, `no_direct_match`: `True` (all Sem 5 EE lateral options are power/circuits)
- **Recommendations**:
  1. `EE3L005`: Control System Technology (3.0 cr, score: 0.0)
  2. `EE3L006`: Signals and Circuits (3.0 cr, score: 0.0)
- **Future Options (Sem 7 Electives matching goal)**:
  1. `CS6L001`: Computational Intelligence [Sem 7, 3.0 cr, score: 0.8]
  2. `EC6L005`: Statistical Signal Processing [Sem 7, 3.0 cr, score: 0.4667] (Prerequisites needed: EC3L003)
  3. `CS4L003`: Artificial Intelligence [Sem 7, 3.0 cr, score: 0.2]
- **Generated Answer**:
  ```text
  Credit Summary: Your semester limit is 25.0 credits under RULE_SEM_CREDIT_CAP_REGULAR. Core courses require 18.0 credits, leaving 7.0 credits of headroom for 2 open slot(s) (requires at least 6.0 credits).

  Note: No direct matches were found for your query. Here are the eligible elective courses for this semester:

  - **EE3L005**: Control System Technology (3.0 cr) – eligible elective matching semester slot criteria. Resource: Control Engineering – Prof. M. Gopal, IIT Delhi (NPTEL).

  - **EE3L006**: Signals and Circuits (3.0 cr) – eligible elective matching semester slot criteria. Resource: Networks, Signals and Systems – Prof. T.K. Basu, IIT Kharagpur (NPTEL).

  Upcoming Electives in Later Semesters:

  - **CS6L001**: Computational Intelligence [Sem 7, 3.0 cr]

  - **EC6L005**: Statistical Signal Processing [Sem 7, 3.0 cr] (Prerequisites needed: EC3L003)

  - **CS4L003**: Artificial Intelligence [Sem 7, 3.0 cr]

  What specific topics or elective areas would you prefer to focus on?
  ```

### Case 2: EE Semester 7
- **Request**: Branch: `EE`, Semester: `7`, CGPA: `8.0`, Goal: `"Software engineering role"`, Query: `"what course should I take this semester"`
- **Intent**: `source`: `"profile_goal"`, `query_had_topic`: `False`
- **Budget**: Limit: `19.0`, Core Credits: `12.0`, Headroom: `7.0`, Open Slots: `2` (requires min `6.0` cr, max `7.0` cr), Status: `"sufficient"`
- **Match Status**: `weak_match`: `False`, `no_direct_match`: `False` (strong matches found)
- **Recommendations**:
  1. `CS6L001`: Computational Intelligence (3.0 cr, score: 0.8, skill: Machine Learning & Pattern Recognition)
  2. `EC6L005`: Statistical Signal Processing (3.0 cr, score: 0.4667, skill: Embedded Systems & Real-Time Computing)
  3. `CS4L003`: Artificial Intelligence (3.0 cr, score: 0.2, topics: artificial, intelligence)
  4. `EC4L001`: Semiconductor Devices (3.0 cr, score: 0.0)
  5. `EC4L002`: Opto-Electronics (3.0 cr, score: 0.0)
- **Future Options (Sem 8 Electives)**:
  1. `EC6L030`: Embedded Systems [Sem 8, 3.0 cr, score: 0.1]
  2. `EC4L003`: VLSI Design [Sem 8, 3.0 cr, score: 0.0] (Prerequisites needed: EC4L001)
  3. `EC6L015`: Biomedical Signal Processing [Sem 8, 3.0 cr, score: 0.0]
- **Generated Answer**:
  ```text
  Credit Summary: Your semester limit is 19.0 credits under RULE_SEM_CREDIT_CAP_REGULAR. Core courses require 12.0 credits, leaving 7.0 credits of headroom for 2 open slot(s) (requires at least 6.0 credits).

  Here are your recommended courses:

  - **CS6L001**: Computational Intelligence (3.0 cr) – teaches Machine Learning & Pattern Recognition. Resource: Introduction to Soft Computing Live 1 – Prof. D. Samanta, IIT Kharagpur (NPTEL) – single video.

  - **EC6L005**: Statistical Signal Processing (3.0 cr) – teaches Embedded Systems & Real-Time Computing. Resource: Statistical Signal Processing Lec 9 (NPTEL NOC20_EE53) – single video; its description links the full playlist.

  - **CS4L003**: Artificial Intelligence (3.0 cr) – covers topics in artifici, intelligence. Resource: Artificial Intelligence – Prof. D. Khemani, IIT Madras (NPTEL).

  - **EC4L001**: Semiconductor Devices (3.0 cr) – eligible elective matching semester slot criteria. Resource: Electron Devices – Prof. A.N. Chandorkar, IIT Bombay (NPTEL lectures).

  - **EC4L002**: Opto-Electronics (3.0 cr) – eligible elective matching semester slot criteria. Resource: Advanced Optical Communication – Prof. R.K. Shevgaonkar, IIT Bombay (NPTEL).

  Upcoming Electives in Later Semesters:

  - **EC6L030**: Embedded Systems [Sem 8, 3.0 cr]

  - **EC4L003**: VLSI Design [Sem 8, 3.0 cr] (Prerequisites needed: EC4L001)

  - **EC6L015**: Biomedical Signal Processing [Sem 8, 3.0 cr]
  ```

### Case 3: MME Semester 6
- **Request**: Branch: `MME`, Semester: `6`, CGPA: `7.5`, Goal: `"Materials research"`
- **Budget**: Limit: `24.0`, Core Credits: `16.0`, Headroom: `8.0`, Open Slots: `2` (requires min `6.0` cr, max `8.0` cr), Status: `"sufficient"`
- **Recommendations**:
  1. `ML3L011`: Recent advances in composite materials (3.0 cr, score: 0.62, skill: Composites & Nanostructured Materials)
  2. `ML2L006`: Advances in nanoscience and nanotechnology (3.0 cr, score: 0.42, skill: Composites & Nanostructured Materials)
  3. `ML3L012`: Mineral processing plant design (3.0 cr, score: 0.21, skill: Mineral Processing & Extractive Metallurgy)
- **Future Options (Sem 7 Electives)**:
  1. `ML4L010`: Science and technology of composite materials [Sem 7, 3.0 cr, score: 0.6667]
  2. `ML4L006`: Energy materials [Sem 7, 3.0 cr, score: 0.5667]
  3. `ML4L004`: Powder metallurgy [Sem 7, 3.0 cr, score: 0.3333]
- **Generated Answer**:
  ```text
  Credit Summary: Your semester limit is 24.0 credits under RULE_SEM_CREDIT_CAP_REGULAR. Core courses require 16.0 credits, leaving 8.0 credits of headroom for 2 open slot(s) (requires at least 6.0 credits).

  Here are your recommended courses:

  - **ML3L011**: Recent advances in composite materials (3.0 cr) – teaches Composites & Nanostructured Materials. Resource: NPTEL 'Metallurgy and Material Science' channel (browse by course name):.

  - **ML2L006**: Advances in nanoscience and nanotechnology (3.0 cr) – teaches Composites & Nanostructured Materials. Resource: NPTEL 'Metallurgy and Material Science' channel (browse by course name):.

  - **ML3L012**: Mineral processing plant design (3.0 cr) – teaches Mineral Processing & Extractive Metallurgy. Resource: NPTEL 'Metallurgy and Material Science' channel (browse by course name):.

  Upcoming Electives in Later Semesters:

  - **ML4L010**: Science and technology of composite materials [Sem 7, 3.0 cr]

  - **ML4L006**: Energy materials [Sem 7, 3.0 cr]

  - **ML4L004**: Powder metallurgy [Sem 7, 3.0 cr]
  ```

---

## 5. Commands to Run & Test

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
