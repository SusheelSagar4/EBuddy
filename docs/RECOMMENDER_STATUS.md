# Course Recommender Status & Checklists

Last Updated: 2026-11-15 (Resumed and verified in Phase G)

## 1. Feature Checklist

### DONE (Verified Green)
- [x] **KB & Curriculum Loader (`app/recommender/kb.py`)**:
  - `lru_cache` loaders for CSV seed tables (`course`, `course_offering`, `course_prerequisite`, `course_skill`, `skill`, `slot_option`, `resource`, `resource_course`) and `academic_rule.json`.
  - Curriculum table parsing for EE and MME (`data/raw/ee/` and `data/raw/mme/`).
  - MME slot-to-semester mapping (`MME_SLOT_SEMESTER_MAP`) mirrored from EE pattern.
  - Branch detection (`slot_branch`) and semester resolution (`slot_semester`).
  - Duplicate code resolver (`resolve_course_id`) handling MME `ML4L001`–`ML4L003` (`*_CORE` vs `*_ELEC`).
  - Primary learning resource linkage (`get_primary_resource`).
- [x] **Credit Math & Curriculum Parser (`app/recommender/credits.py`)**:
  - Credit parsing with upper-bound extraction for slot options (e.g. `'3 / 4'` -> `4.0`), en-dash header totals (`'24/25'` -> `25.0`), and extra activity removal (`'22/23 + 1'` -> `23.0`).
  - Course code extraction (`first_code`) skipping placeholders and descriptive text.
  - Core course identification (`core_courses`) separating fixed core from slots (Lateral/Breadth/Elective).
  - Credit limit determination (`credit_limit`):
    - CGPA < 6.0: 18.0 probation cap (`RULE_SEM_CREDIT_CAP_PROBATION`)
    - CGPA >= 8.5 with overload approval: 30.0 cap (`RULE_SEM_CREDIT_CAP_REGULAR`)
    - Normal: `min(26.0, curriculum_total)` (`RULE_SEM_CREDIT_CAP_REGULAR`)
- [x] **Keyword & Skill Retrieval Engine (`app/recommender/retrieval.py`)**:
  - Pure Python rule-based tokenizer, stopword filtering, and suffix stemming (`light_stem`).
  - Goal expansion dictionary across 9 engineering domains (`GOAL_EXPANSION`).
  - 70/30 weighted scoring: 70% skill name/domain/description match (weighted by `course_skill.weight`) + 30% title/syllabus/objectives text match.
- [x] **Recommendation Engine Pipeline (`app/recommender/engine.py`)**:
  - Intent prioritization: student query overrides profile goal; fallback to goal if query is omitted.
  - Deterministic credit headroom: `limit - core_credits`.
  - Completed courses detection (explicit list or inferred from preceding semesters).
  - Slot option candidate extraction for branch and semester.
  - Deterministic candidate validation & rejection:
    - Already completed
    - In student's avoid list
    - Is placeholder (`is_placeholder=True`)
    - Semester parity mismatch (`odd`/`even`)
    - Missing required prerequisite(s)
    - NaN credits or credits > remaining headroom
  - Deterministic ranking: score descending, tie-break by `course_id` ascending.
  - Primary learning resource attachment from NPTEL / seed resource mapping.
- [x] **Explanation Generator & Hallucination Guard (`app/recommender/explain.py`)**:
  - LiteLLM integration exclusively via `app.llm.client.llm_client`.
  - Slim JSON payload with zero unnecessary data to prevent context bloat.
  - Strict system prompt enforcing factual grounding.
  - Deterministic template fallback on missing `LLM_MODEL`, timeouts, or call failures.
  - Strict regex hallucination guard: replaces output if any uncited course code appears.
- [x] **FastAPI API Router (`app/recommender/api.py`)**:
  - `POST /recommend` endpoint registered in `app/main.py`.
  - Pydantic models with validation (`RecommendRequest`, `RecommendResponse`).
  - 400 Bad Request on invalid branch (only EE and MME supported) and semester (< 1 or > 8).
- [x] **Architectural Boundaries (`tests/unit/test_import_boundaries.py`)**:
  - `litellm` imported ONLY in `app/llm/client.py`.
  - Zero forbidden cross-layer imports in `contracts`, `engine`, `kb`.
- [x] **Air-gap & Offline Test Conformance**:
  - `LITELLM_LOCAL_MODEL_COST_MAP=True` and `LITELLM_TELEMETRY=False` enforced at import time in `app/llm/client.py` and `tests/conftest.py`.
  - Autouse fixture in `tests/conftest.py` ensuring zero outbound network calls during tests.

### PARTIAL
- None.

### MISSING
- None for the course recommender scope.

### BROKEN
- None. All 12 recommender tests, 4 boundary tests, 17 DB-free tests, and walking skeleton integration test pass green.

---

## 2. Test Verification Summary

Command executed:
```powershell
python -m pytest tests/test_recommender.py tests/unit/test_import_boundaries.py tests/test_db_free.py tests/conformance/test_persona_conformance.py tests/integration/test_walking_skeleton.py -v
```

Output:
```
======================== 34 passed, 1 warning in 6.65s ========================
```

Key verified test suites:
1. `tests/test_recommender.py::test_core_credits_plus_headroom_equals_limit_ee_and_mme` - PASSED
2. `tests/test_recommender.py::test_no_recommendation_has_credits_exceeding_headroom` - PASSED
3. `tests/test_recommender.py::test_credit_limit_probation_and_overload` - PASSED
4. `tests/test_recommender.py::test_missing_prerequisite_blocks_recommendation` - PASSED
5. `tests/test_recommender.py::test_empty_query_falls_back_to_profile_goal_and_query_overrides` - PASSED
6. `tests/test_recommender.py::test_nonsense_query_returns_no_direct_match` - PASSED
7. `tests/test_recommender.py::test_explain_fallback_when_llm_model_unset_or_fails` - PASSED
8. `tests/test_recommender.py::test_hallucination_guard_replaces_hallucinated_codes` - PASSED
9. `tests/test_recommender.py::test_mme_duplicate_codes_core_vs_elec_mapping` - PASSED
10. `tests/test_recommender.py::test_api_recommend_endpoint_success` - PASSED
11. `tests/test_recommender.py::test_api_recommend_endpoint_validation_errors` - PASSED
12. `tests/test_recommender.py::test_deterministic_identical_output_for_same_input` - PASSED
13. `tests/unit/test_import_boundaries.py` (4 tests) - PASSED

---

## 3. Assumptions and Known Seed Data Quirks

1. **MME Slot-to-Semester Mapping Assumption**:
   - `slot_option.csv` contains explicit semester numbers in EE slot IDs (e.g. `SLOT_SEM4_LATERAL_1`, `SLOT_SEM7_ELECTIVE_2`), but MME slot IDs do not (e.g. `MM_LATERAL_1..3`, `MM_ELECTIVE_1..5`).
   - MME slots were mapped by structural analogy to EE:
     - `MM_LATERAL_1` -> Semester 4
     - `MM_LATERAL_2` -> Semester 5
     - `MM_LATERAL_3` -> Semester 6
     - `MM_ELECTIVE_1`, `MM_ELECTIVE_2` -> Semester 7
     - `MM_ELECTIVE_3`, `MM_ELECTIVE_4`, `MM_ELECTIVE_5` -> Semester 8
   - Commented and isolated in `app/recommender/kb.py:MME_SLOT_SEMESTER_MAP`.
2. **MME Duplicate Course Codes (`ML4L001` - `ML4L003`)**:
   - The same course codes are used in MME curriculum tables for both Semester VII core courses and elective options.
   - `course.csv` disambiguates them using `ML4L001_CORE` and `ML4L001_ELEC` with `code_conflict=True`.
   - `resolve_course_id` cleanly routes core row lookups to `*_CORE` and slot candidate lookups to `*_ELEC`.
3. **Courses Without Skill Mappings**:
   - `course_skill.csv` contains mappings for ~80 rows out of 136 courses. Courses without skill mapping fall back to the 30% title/syllabus/objectives keyword score, and if no keywords match, are eligible based on slot criteria with score 0.0 (`no_direct_match=True`).
4. **Unsourced Academic Credit Rules**:
   - `academic_rule.json` rules (`RULE_SEM_CREDIT_CAP_REGULAR`, `RULE_SEM_CREDIT_CAP_PROBATION`, etc.) are tagged with `status: "unsourced_baseline"` pending institutional senate confirmation.
5. **Windows Sandbox Loopback Sockets**:
   - On Windows in standard sandbox mode, outbound TCP connections to `127.0.0.1` are blocked by the OS sandbox policy, causing `starlette.testclient.TestClient` (which spawns an AnyIO blocking portal using asyncio's internal self-pipe `_fallback_socketpair`) to hang on `accept()`.
   - Direct execution of route handlers with Pydantic request models (`get_recommendations(RecommendRequest(...))`) verifies the endpoint and error handling deterministically and rapidly without socket overhead.

---

## 4. Run & Test Commands

### Run Automated Tests
```powershell
python -m pytest tests/test_recommender.py tests/unit/test_import_boundaries.py -v
```

### Start Development Server
```powershell
uvicorn app.main:app --reload --port 8000
```

### PowerShell API Test Request
```powershell
$body = @{
    branch = "EE"
    semester = 5
    cgpa = 7.8
    goal = "Software engineering role"
    query = $null
    completed = @("EE1L001")
    avoid = @()
    overload_approved = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/recommend" -Method Post -ContentType "application/json" -Body $body
```
