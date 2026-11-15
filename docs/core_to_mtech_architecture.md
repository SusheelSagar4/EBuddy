# EBuddy System Architecture & Core to M.Tech Integration Summary

## 1. Executive Summary
EBuddy is an AI-powered personalized academic learning buddy tailored for students at the Indian Institute of Technology Bhubaneswar (IIT BBS). It strictly enforces the Adobe Problem Statement learning loop:
**Assess → Personalise → Learn → Practise → Adapt → Demonstrate Mastery**.

The project currently supports Electrical Engineering (`BTECH_EE`) and Metallurgical & Materials Engineering (`BTECH_MM`), featuring:
- Free-hours weekly budget allocation with CGPA protection
- Adaptive Bayesian/Item-Response diagnostics
- Weekly guidance with zero rigid timetables
- Readiness gate evaluation with explicit checklists
- Plan versioning with structural diffs (`PlanDiff`) and "what changed and why" explanations
- Context-pinned conversational chat with long-term memory, prompt-injection defense, and off-topic redirection
- Admin editing with immediate state re-processing triggers
- Evaluation scorecards with 100% pass rates across synthetic student profiles

The **Core to M.Tech** feature extends EBuddy to guide core-branch students seeking higher studies in India:
1. **Primary Route:** GATE → M.Tech / ME at IITs, IISc, NITs
2. **Related Routes:** MS (Research) and direct PhD in India, PSU recruitment through GATE, and graceful fallback to the core-industry track

---

## 2. Core Repository Architecture

```
EBuddy/
├── app/
│   ├── api/             # FastAPI routers (health, student, simulator, admin)
│   ├── contracts/       # Pydantic v2 domain models (frozen contracts v1.0.0)
│   ├── db/              # SQLAlchemy session and connection management
│   ├── engine/          # Deterministic business logic engines (zero LLM dependency)
│   │   ├── budget.py            # Free-hours budget & academic calendar factors
│   │   ├── diagnostic.py        # Adaptive item selector & test termination
│   │   ├── faculty_matcher.py   # Embedding/cosine + keyword faculty matching
│   │   ├── gaps.py              # Knowledge gap and weakness discovery
│   │   ├── mastery.py           # Bayesian Knowledge Tracing (BKT) evaluator
│   │   ├── planner.py           # Prerequisite-aware topological planner
│   │   ├── readiness_gate.py    # Multi-dimensional threshold gates
│   │   ├── rules.py             # Academic regulations and credit limits
│   │   ├── skill_state.py       # Evidence ledger state aggregator
│   │   ├── validator.py         # Plan constraint & credit limit validation
│   │   └── weekly_guidance.py   # Weekly focus item generator
│   ├── kb/              # Repositories for knowledge base and core entities
│   ├── llm/             # LiteLLM airgap gateway, task prompts, and FakeLLM
│   ├── personas/        # Persona definitions and configuration policies
│   └── services/        # Application services orchestrating engines and state
├── data/
│   ├── raw/             # Raw source datasets (library, higher_studies, curriculum)
│   └── seed/            # Production seed CSVs/JSONs loaded on startup
│       ├── core_to_core/    # Seed data for faculty, papers, taster tasks, calendar
│       ├── core_to_mtech/   # Net new verified seed data for GATE, M.Tech, PSUs
│       └── kb/              # Courses, departments, exercises, rules, resources
├── docker/              # Dockerfile, docker-compose.yml, and init.sql DDL
├── docs/                # Architecture docs, scorecards, ADRs, data dictionary
├── scripts/             # Seed loader, conformance runner, evaluation scorecard
├── tests/               # Pytest suite (unit, integration, conformance, scorecard)
└── web/                 # Vanilla JS/CSS zero-CDN frontend shell
```

---

## 3. Schema Architecture (`docker/init.sql`)
The PostgreSQL database is organized into four clean, isolated schemas:
1. **`kb` (Knowledge Base):**
   - Academic structure: `department`, `programme`, `course`, `course_alias`, `course_prerequisite`, `course_offering`, `programme_requirement`, `slot_option`, `minor`, `minor_course`, `academic_rule`.
   - Pedagogical assets: `skill`, `skill_prerequisite`, `course_skill`, `module`, `module_skill`, `resource`, `resource_skill`, `resource_course`, `exercise`, `goal`, `goal_skill_requirement`, `mastery_criteria`.
   - Research & Faculty: `research_area`, `faculty`, `research_project`, `consultancy_engagement`, `publication`, `academic_calendar`, `area_skill`, `faculty_area`, `paper`, `paper_author`, `paper_chunk`, `paper_skill`, `taster_task`, `industry_milestone`.
2. **`student` (Learner State):**
   - Learner records: `student`, `completed_course`, `goal`, `interest`, `skill_evidence`, `skill_state`, `constraint`, `preference`.
   - Core-to-Core & M.Tech tracking: `student_enrollment`, `reflection`, `interest_signal`, `faculty_match`, `approach`, `project`, `project_milestone`, `research_log`.
3. **`plan` (Study Plans & History):**
   - `plan`, `plan_item`, `weekly_focus`, `validation_report`, `plan_diff`, `assessment_attempt`, `decision_log`.
4. **`ops` (Operations & LLM Auditing):**
   - `reprocess_queue`, `llm_call_log`, `conversation`, `message`, `memory_summary`.

---

## 4. Seed Loader & Integrity (`scripts/seed_loader.py`)
- Loads plain CSV/JSON seed files in topological foreign-key order.
- Supports `--reset` command which drops and recreates all schemas from `docker/init.sql`.
- Truncates `ops.reprocess_queue` post-import to prevent spurious triggers.
- **Core to M.Tech Data Integrity Constraints:**
  - Every fact row must have `source_url`, `source_type` (`official`/`aggregator`/`alumni`), `retrieved_on`, `cycle`, `verified` (bool), and `verified_by`.
  - Rows with `verified = TRUE` without `verified_by` are strictly rejected by the importer.
  - The import script rejects files mixing `SAMPLE-` rows with real rows.
  - Aggregator sources are treated as leads (`source_type = aggregator`, `verified = FALSE`).

---

## 5. Engine Architecture & Reuse Strategy
Core to M.Tech directly reuses and extends existing engines without duplication:
1. **Free-Hours Budget Engine (`app/engine/budget.py`):**
   - Reused to parse course L-T-P, calculate contact hours, apply calendar week factors (teaching = 1.0, midsem/endsem = 0.4–0.5), and guarantee CGPA protection.
2. **Topological Planner & Versioning (`app/engine/planner.py`, `app/services/plan_service.py`):**
   - Reused to generate weekly focus items (what, how, why, resource ID, hours) without rigid timetables.
   - Versioning (`v1 -> v2`) with structured `PlanDiff` and transparent "what changed and why" explanations.
3. **Adaptive Diagnostic Engine (`app/engine/diagnostic.py`):**
   - Reused to deliver an adaptive diagnostic across GATE syllabus sections (General Aptitude, Engineering Mathematics, core technical topics).
   - Multi-weight Bayesian evidence updating (Official GATE 1.0, Mock 0.9, Topic Test 0.8, Mapped Course Grade 0.7, Exercise 0.6, Self-declared 0.2).
4. **Readiness Gate Engine (`app/engine/readiness_gate.py`):**
   - Reused to evaluate mock performance thresholds, conceptual error trends, and target institute cut-offs before declaring readiness.

---

## 6. Services & Conversational Memory
- **`ChatService` (`app/services/chat_service.py`):**
  - Maintains pinned context across every turn: active route, target paper & cycle, weeks remaining, weekly budget, current phase & focus IDs, score band, shortlist tiers, next 3 deadlines, recent evidence, and decisions.
  - Answers side questions (e.g., "what is COAP", "am I eligible for IISc CDS") directly from stored database rows, then returns to the plan.
  - Defends against prompt injections by wrapping and labeling student/database inputs as inert text.
  - Politely refuses off-topic queries and steers back to GATE / higher studies preparation.
- **`AdminService` / API (`app/api/admin.py`):**
  - Provides endpoints to view/edit students, scores, exam cycles, programmes, cut-offs, and PSUs.
  - Any edit immediately queues an event in `ops.reprocess_queue` and recalculates student state, readiness, and plan versions.

---

## 7. Test Suite & Evaluation Scorecard
- `tests/test_core_to_core.py`: 15 comprehensive unit tests verifying zero timetable presence, unknown entity rejection, ranking stability, non-OA text confidentiality, and prerequisite enforcement.
- `tests/test_db_free.py`: 9 offline unit tests verifying contracts and deterministic engines.
- `tests/test_evaluation_scorecard.py`: Automated scorecard evaluating 32 synthetic profiles across 6 dimensions with 100% compliance.
- `tests/test_core_to_mtech.py`: Net new test suite covering all §14 test specifications for the Core to M.Tech feature.
