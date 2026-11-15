# Course Recommender Status & Checklists

Last Updated: 2026-11-15 (Polish Complete: other_eligible Partition, Neutral Heading, Unstemmed Words, Resource Punctuation Cleaned, 45 Tests Green)

## 1. Feature Checklist

### DONE (Verified Green)
- [x] **Recommendations vs. Other Eligible Partitioning (`app/recommender/engine.py` & `explain.py`)**:
  - Only courses with `score >= MIN_RELEVANCE` (0.20) are placed into `recommendations`.
  - Eligible courses with score `< 0.20` (or beyond `top_k`) are placed into `other_eligible`.
  - Zero-score courses are strictly never described as recommended or relevant.
  - Drop the filler phrase `"eligible elective matching semester slot criteria"`.
  - Courses in `other_eligible` are presented under the neutral heading: `"Other eligible electives, not matched to your goal:"` (or `"Other eligible electives, not matched to your query:"`).
- [x] **Goal-Aware Phrasing (`app/recommender/explain.py`)**:
  - When `intent.source` is `"profile_goal"`, user-facing text says `"your goal (<goal text>)"` instead of `"your query"`.
- [x] **Unstemmed Original Words in User-Facing Text (`app/recommender/retrieval.py`)**:
  - Pure Python rule-based unstemmer (`unstem()`) maps stemmed tokens back to canonical human-readable words (e.g. `artificial`, `computing`, `solidification`, `simulation`, `structures`).
  - `matched_terms` outputs clean original words instead of raw stems like `artifici` or `compu`.
- [x] **Resource Title Punctuation Cleaned (`app/recommender/explain.py`)**:
  - Strips trailing punctuation from resource titles (`.rstrip(" :;,.")`) preventing stray punctuation like `):.` or `channel (browse by course name):.`.
- [x] **Approved Skill Mappings Applied (`data/seed/kb/course_skill.csv`, Commit `c1b69d6`)**:
  - Added approved skill mappings for 33 slot-candidate courses (34 total mappings, including dual skills for `EE6L011`).
  - `ML4L012` (*Materials in archaeology*) skipped per instructions.
  - Set `mapping_method="reviewed_title_inference"`, `status="draft_for_review"`, `source_id="DESIGN_TEAM"`.
- [x] **Audit and 10 Corrections of Existing `course_skill.csv` Mappings (Commit `35949f6`)**:
  - Corrected 10 anomalous seed mappings (e.g. `EE3L008 Soft Computing` -> `SKILL_AI_ML`, `EC6L005 Statistical Signal Processing` -> `SKILL_DSP`, `EE3L004 Power Electronics` -> `SKILL_POWER_ELECTRONICS`, etc.).
  - Documented before/after details in `docs/course_skill_corrections.md`.
  - Added 10 tracking entries in `data/seed/kb/data_issue.csv` (`ISSUE_SKILL_EC6L005` through `ISSUE_SKILL_ML4L003`) with status `resolved` and severity `medium`.
- [x] **Skill-Mapping Coverage Fix (`app/recommender/retrieval.py`)**:
  - For courses without `course_skill` rows, final relevance score is computed as `0.85 * text_score` (instead of being penalized to 30%).
  - Courses with `course_skill` rows maintain `0.7 * skill + 0.3 * text`.
  - Mapped and unmapped courses are directly comparable. `CS4L003` (*Artificial Intelligence*) scores `0.90` for goal *"Software engineering role"*.
  - Verified with `test_unmapped_course_scoring_comparable`.
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
  - Clean sentence phrasing with zero broken grammatical constructs.
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
======================= 45 passed, 1 warning in 10.61s ========================
```

Key verified test suites:
- `tests/test_recommender.py`: 23 passed (including `test_other_eligible_partition_and_neutral_heading`, `test_resource_punctuation_formatting_clean`, `test_unstemmed_original_words_in_matched_terms`, `test_unmapped_course_scoring_comparable`, determinism, credit limits, prerequisite checks, fallback templates, hallucination guard, MME duplicate codes, intent fallback, backlogs, relevance honesty, future options, multi-slot credits, template formatting, mocked LLM path, API validation & visibility).
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

---

## 5. Verified Sanity Case Rankings

### 1. EE Semester 5 (Goal: "Software engineering role", Query: "what course should I take this semester")
- **Intent**: Falls back to `profile_goal` (`query_had_topic: False`).
- **Credit Budget**: Core 18.0, Limit 25.0, Headroom 7.0 (2 open slots, needs 6.0-7.0 credits, status: `sufficient`).
- **Relevance Flag**: `weak_match: True`, `no_direct_match: True` (EE Sem 5 slots strictly offer `EE3L005` & `EE3L006`; neither matches software).
- **Recommendations**: *(None with score >= 0.20)*
- **Other Eligible (Not Matched to Goal)**:
  - `EE3L005`: Control System Technology (3.0 cr, score: 0.00)
  - `EE3L006`: Signals and Circuits (3.0 cr, score: 0.00)
- **Honest Explanation**: Plainly reports no direct matches for your goal (Software engineering role), lists available slot electives neutrally under `"Other eligible electives, not matched to your goal:"`, and highlights upcoming courses.
- **Future Options**:
  - `CS4L003`: Artificial Intelligence (Sem 7, 3.0 cr, score: 0.90)
  - `EE3L008`: Soft Computing and Applications (Sem 6, 3.0 cr, score: 0.80)
  - `CS6L001`: Computational Intelligence (Sem 7, 3.0 cr, score: 0.80)

### 2. EE Semester 7 (Goal: "Software engineering role", Query: "what course should I take this semester")
- **Intent**: Falls back to `profile_goal` (`query_had_topic: False`).
- **Credit Budget**: Core 12.0, Limit 19.0, Headroom 7.0 (2 open slots, needs 6.0-7.0 credits, status: `sufficient`).
- **Relevance Flag**: `weak_match: False`, `no_direct_match: False`.
- **Top Recommendations (score >= 0.20)**:
  - `CS4L003`: Artificial Intelligence (3.0 cr, score: 0.90, skill: `SKILL_AI_ML`)
  - `CS6L001`: Computational Intelligence (3.0 cr, score: 0.80, skill: `SKILL_AI_ML`)
- **Other Eligible (Not Matched to Goal, score < 0.20)**:
  - `EC4L001`: Semiconductor Devices (3.0 cr, score: 0.00)
  - `EC4L002`: Opto-Electronics (3.0 cr, score: 0.00)
  - `EC6L002`: Image and Video Processing (4.0 cr, score: 0.00)
  - `EC6L005`: Statistical Signal Processing (3.0 cr, score: 0.00)
  - `EC6L012`: Optical Communication (3.0 cr, score: 0.00)
  - `EE6L002`: Electric Power Quality (3.0 cr, score: 0.00)
  - `EE6L007`: Industrial Instrumentation (3.0 cr, score: 0.00)
  - `EE6L009`: High Voltage Engineering (3.0 cr, score: 0.00)
  - `EE6L010`: Advanced Power Electronics (3.0 cr, score: 0.00)
  - `EE6L011`: Energy Storage Systems (3.0 cr, score: 0.00)
- **Future Options**:
  - `EC6L027`: Pattern Recognition (Sem 8, 3.0 cr, score: 0.70)
  - `EC6L031`: Computer Vision (Sem 8, 3.0 cr, score: 0.70, missing prereq: `EC6L002`)
  - `EC6L030`: Embedded Systems (Sem 8, 3.0 cr, score: 0.57)

### 3. MME Semester 6 (Goal: "Materials research", Query: "what course should I take this semester")
- **Intent**: Falls back to `profile_goal` (`query_had_topic: False`).
- **Credit Budget**: Core 16.0, Limit 24.0, Headroom 8.0 (2 open slots, needs 6.0-8.0 credits, status: `sufficient`).
- **Relevance Flag**: `weak_match: False`, `no_direct_match: False`.
- **Top Recommendations (score >= 0.20)**:
  - `ML3L011`: Recent advances in composite materials (3.0 cr, score: 0.62, skill: `SKILL_COMPOSITES_NANO`)
  - `ML2L006`: Advances in nanoscience and nanotechnology (3.0 cr, score: 0.42, skill: `SKILL_COMPOSITES_NANO`)
  - `ML3L012`: Mineral processing plant design (3.0 cr, score: 0.21, skill: `SKILL_EXTRACTIVE_MET`)
- **Future Options**:
  - `ML4L002_ELEC (ML4L002)`: Solidification of metals and alloys (Sem 7, 3.0 cr, score: 0.90)
  - `ML4L001_ELEC (ML4L001)`: Joining of metals and alloys (Sem 7, 3.0 cr, score: 0.77)
  - `ML4L010`: Science and technology of composite materials (Sem 7, 3.0 cr, score: 0.67)

---

## 6. Known Seed Data Quirks & Handling

1. **MME Slot-Semester Mapping**:
   - In `data/seed/kb/slot_option.csv`, MME slot IDs do not contain semester numbers. The real slot IDs in data and code are:
     - `MM_LATERAL_1`, `MM_LATERAL_2`, `MM_LATERAL_3`
     - `MM_ELECTIVE_1`, `MM_ELECTIVE_2`, `MM_ELECTIVE_3`, `MM_ELECTIVE_4`, `MM_ELECTIVE_5`
   - In `app/recommender/kb.py`, the explicit mapping `MME_SLOT_SEMESTER_MAP` assigns:
     - `MM_LATERAL_1` -> Semester 4
     - `MM_LATERAL_2` -> Semester 5
     - `MM_LATERAL_3` -> Semester 6
     - `MM_ELECTIVE_1`, `MM_ELECTIVE_2` -> Semester 7
     - `MM_ELECTIVE_3`, `MM_ELECTIVE_4`, `MM_ELECTIVE_5` -> Semester 8
2. **Duplicate Course Codes in MME**: `ML4L001`, `ML4L002`, `ML4L003` appear twice in seed data (as both core courses and slot electives). Handled by mapping course IDs with `_CORE` and `_ELEC` suffixes in `resolve_course_id()` and displaying clean base codes to students.
3. **Sparse Skill Mappings & Seed Corrections**:
   - Resolved via approved Commit A (`c1b69d6`, 34 candidate mappings added) and Commit B (`35949f6`, 10 anomalies corrected and documented in `data/seed/kb/data_issue.csv` and `docs/course_skill_corrections.md`).
4. **Credit Cap Rules & Status**:
   - All academic rules in `data/seed/kb/academic_rule.json` have `status: "unsourced_baseline"` (`source_id: "UNSOURCED_BASELINE"`).
   - Baseline credit caps defined in `academic_rule.json` and enforced by `app/recommender/credits.py`:
     - Regular cap (`RULE_SEM_CREDIT_CAP_REGULAR`): 26.0 credits max (16.0 min). Overload up to 30.0 credits for CGPA >= 8.5 with Faculty Advisor approval.
     - Probation cap (`RULE_SEM_CREDIT_CAP_PROBATION`): 18.0 credits max (for CGPA < 6.0 or academic probation).
     - Minor eligibility (`RULE_MINOR_ELIGIBILITY`): CGPA >= 8.0, 18 credits between Sem V and Sem VIII.
     - Online credit transfer cap (`RULE_ONLINE_CREDIT_NPTEL`): Max 12 credits via approved 8/12-week NPTEL/SWAYAM courses.


