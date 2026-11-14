# Changelog — Personalised Learning Buddy

All notable changes and phase milestones are documented in this file.

## [Contracts v1.2.0 & Adaptive Memory Architecture] - 2026-11-15
### Added
- **Contracts (`app/contracts/` v1.2.0):**
  - Added `conflict_flag: Optional[str]` and `optional_overload_proposals: List[Dict[str, Any]]` to `Plan` (`app/contracts/plan.py`).
  - Added `weekly_hours_budget: Optional[float]` and `deferred_tasks: List[str]` to `WeeklyRoadmap` (`app/contracts/roadmap.py`).
  - Added `long_term_memory: Optional[str]` to `ContextCard` (`app/contracts/chat.py`).
  - Bumped `VERSION` to `1.2.0` and regenerated all 28 JSON schemas in `docs/contracts/`.
- **Student Constraint Strict Bounding & Overload Routing:**
  - Student-stated constraints (`credit_cap`, `headroom`, `weekly_hours`, `avoid_course`, `not_together`) are enforced as HARD limits by default.
  - Courses exceeding student credit limits or avoiding student filters are excluded from default plan items and routed to `plan.optional_overload_proposals` awaiting student confirmation.
  - Unsourced institute rules (`unsourced_baseline`) emit non-blocking warnings without dropping courses.
- **Interest-vs-Evidence Conflict Detection:**
  - `GapAnalyzer` detects divergence between high target goals ($\ge 70$) and weak demonstrated/diagnostic evidence ($< 40$).
  - Surfaces conflict flag in `PlanItem.reason.why_this`, `Plan.conflict_flag`, and Agent 4 conversational advisories.
- **Adaptive Diagnostic Engine:**
  - `AdaptiveDiagnostic` starts at medium difficulty (50.0), raises difficulty (+15.0) on correct responses, and lowers difficulty (-15.0) on incorrect responses.
  - Terminates between 5 and 8 items once confidence threshold ($\ge 0.85$) is attained.
- **Rolling Long-Term Conversation Memory:**
  - Persists multi-turn rolling conversation summaries in `ops.memory_summary` table (and in-memory fallback).
  - Automatically loads prior summaries into `ContextCard.long_term_memory` on subsequent conversational turns.
- **Original Non-Copyrighted Question Bank:**
  - Authored 10 verified engineering questions with step-by-step answer keys for `ee_power_core` in `data/seed/personas/ee_power_core/questions.yaml`, `exercises.csv`, and canonical `data/seed/kb/exercise.csv`.
  - Added `status="draft_for_review"` and `source_id="DESIGN_TEAM"` to `kb.exercise`.
- **Persona Conformance Quality Gate:**
  - Conformance runner validates all registered personas against concrete student profiles in `data/seed/personas/<id>/students.csv`, failing if any persona lacks profiles.
  - Generates comprehensive Persona $\times$ Profile $\times$ Check matrix in `docs/evaluation/conformance_report.md`.

## [Contracts v1.1.0 & Four-Agent Architecture] - 2026-11-14
### Added
- **Domain Contracts (`app/contracts/`):**
  - Bumped contract version to `1.1.0` in `app/contracts/VERSION`.
  - Added `ChangeProposal` and `ProposalStatus` (`app/contracts/proposal.py`).
  - Added `WeeklyRoadmap`, `DailyTask`, and `RoadmapVersionRecord` (`app/contracts/roadmap.py`).
  - Exported 28 JSON schemas to `docs/contracts/*.json`.
- **Four-Agent Architecture (`app/agents/`):**
  - `RoadmapPlannerAgent` (Agent 1): Sole designated writer for roadmap versions and weekly roadmaps.
  - `LearningResourceAgent` (Agent 2): Daily resource curation and backup alternative retrieval with zero URL fabrication.
  - `AssessmentQuizAgent` (Agent 3): Diagnostic generation, grading, and remediation proposals for low mastery.
  - `QueryAdaptationAgent` (Agent 4): Student conversation, prompt-injection defense, and workload reduction proposals.
- **Curriculum and Course Relevance Engine:**
  - `CourseRelevanceEngine` (`app/engine/relevance.py`) and seed dataset `relevance_tags.csv` (1,496 rows with `status="draft_for_review"` and `source_id="DESIGN_TEAM"`).
  - Branch-specific core curriculum enforcement: major/core courses are fixed and never excluded by career relevance.
  - Strict academic prerequisite gating: electives with unmet prerequisites are never recommended.
  - Dynamic minor course track (`data/seed/kb/minor_course.csv`).
  - Unsourced baseline rules (credit cap, minor eligibility) emit labeled warnings without silently dropping courses.
- **Clean Architecture Import Boundaries:**
  - Added `test_agents_import_boundaries` to `tests/unit/test_import_boundaries.py` ensuring `app/agents/` never imports `litellm` directly or `app/api/`.

## [Phase F: Foundation & Team Architecture] - 2026-11-14
### Added
- **F1 Shared Frozen Contracts (`app/contracts/`):**
  - 24 Pydantic v2 data models versioned at `1.0.0` (`VERSION` file).
  - JSON Schemas generated into `docs/contracts/*.json`.
  - Comprehensive contract documentation in `docs/technical/contracts.md`.
- **F2 Layered Engine & Isolated LLM Gateway:**
  - Repositories in `app/kb/` (`CourseRepo`, `SkillRepo`, `GoalRepo`, `ResourceRepo`, `RuleRepo`).
  - Deterministic engine modules in `app/engine/`: `rules.py` (RuleEngine), `planner.py` (recursive topological prerequisite scheduling), `validator.py` (PlanValidator), `skill_state.py` (evidence ledger updater), `mastery.py` (MasteryEvaluator), `diagnostic.py` (adaptive diagnostic item selector).
  - LiteLLM strictly isolated to `app/llm/client.py`; deterministic `FakeLLM` in `app/llm/fake.py` for all test runs with zero network calls.
  - Task modules in `app/llm/tasks/`: `intent_router.py`, `explainer.py`, `grader.py`, `question_gen.py`, `clarifier.py`.
- **F3 Persona Plugin System (`app/personas/`):**
  - Self-contained persona folder structure (`persona.yaml`, `requirements.yaml`, `mastery.yaml`, `milestones.yaml`, `diagnostic.yaml`, `policy.py`, `README.md`).
  - Auto-discovery registry `app/personas/registry.py`.
  - Scaffolding scripts `scripts/new_persona.ps1` and `scripts/new_persona.sh`.
  - Canonical live persona: `ee_power_core` (Power Systems & Core Electrical Engineering).
- **F4 Conformance Test Suite:**
  - `tests/conformance/test_persona_conformance.py` evaluating 8 automated checks against all registered personas with FakeLLM.
  - Automated report generation in `docs/evaluation/conformance_report.md`.
- **F5 Walking Skeleton Endpoints & Services:**
  - Endpoints in `app/api/`: `/api/student/*` (onboard, diagnostic, plan, learn, progress, chat), `/api/sim/*` (quiz simulation), `/api/admin/*` (personas, stats).
  - Orchestration services in `app/services/`: `onboarding_service.py`, `diagnostic_service.py`, `plan_service.py`, `adapt_service.py`, `mastery_service.py`, `chat_service.py`.
  - End-to-end integration test `tests/integration/test_walking_skeleton.py` passing 100%.
- **F6 Zero-CDN Frontend Shell (`web/`):**
  - Design tokens in `tokens.json` & `tokens.css`.
  - Typed API client in `src/api/client.js`.
  - Persona-agnostic screen modules: Onboarding, Diagnostic, Plan with "Why this?", Learn/Practise, Progress/Mastery, Chat, Adapt Simulator, Admin.
  - Client-side hash routing shell in `index.html` and `app.js`.
  - UX specification in `docs/product/ux_design.md`.
- **F7 Team Workflow Tooling & Architectural Governance:**
  - `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md`, and `.github/CODEOWNERS`.
  - CI pipeline scripts `scripts/ci.ps1` and `scripts/ci.sh` verifying import boundaries, tests, conformance, data check, secret scan, and zero-outbound network audit.
  - Clean import boundary test `tests/unit/test_import_boundaries.py`.
  - Team guides in `docs/team/`: `ownership.md`, `how_to_add_a_persona.md`, `how_to_add_a_skill_or_exercise.md`, `definition_of_done.md`.
  - Architecture Decision Records in `docs/decisions/` (ADR-0001 through ADR-0004).
  - `scripts/dev.ps1` and `Makefile` updated with all developer targets.
- **F8 Test Fixtures:**
  - Isolated TEST-ONLY dataset in `tests/fixtures/` (`TEST_*`) clearly separated from product database seeds.

## [Phase 2: Knowledge Base Ingestion — Electrical & Metallurgical Engineering] - 2026-11-14
### Added
- **Library Publications Dataset:** Created `data/raw/library/` containing:
  - `publications.csv`: 3,000 research articles, conference proceedings, book chapters, and books across all 7 academic schools of IIT Bhubaneswar.
  - `publications_electrical.csv`: 765 publications from the School of Electrical Sciences.
  - `publications_metallurgy.csv`: 176 publications from the School of Minerals, Metallurgical & Materials Engineering.
  - `publications_summary.csv`: Aggregated breakdown across schools and document types.
- **Higher Studies Guidance Database:** Structured and extracted 22 sheets from workbook into:
  - `data/raw/higher_studies/`: Documentation and instrumentation (`README.md`, `Survey.csv` with 35 questions + 5 interview prompts, `Schema.csv`, `Sources.csv`).
  - `data/seed/higher_studies/`: Relational tables for higher-studies planning (`paths.csv` [P1–P7], `exams.csv` [GATE, CAT, GRE, etc.], `exam_cycles.csv`, `syllabus_topics.csv`, `institutions.csv` [26 universities], `programmes.csv`, `admission_stats.csv`, `milestones.csv` [M1–M16], `prep_templates.csv` [10 speed templates], `template_phases.csv` [48 weekly phases], `template_check.csv`, `prep_methods.csv` [PM1–PM6], `resources.csv` [R1–R7], `students.csv`, `evidence.csv`, `study_plans.csv`, `applications.csv`, `survey_responses.csv`).
- **MME Raw Data Pipeline:** Created `data/raw/mme/` containing:
  - `curriculum_semester_table.csv` (Sem III–VIII courses, lateral & elective pools).
  - `curriculum_notes_discrepancies.csv` (12 curriculum issues and discrepancies).
  - `video_playlists.csv` (45 video playlist mappings with NPTEL/OCW links).
  - `research_projects_sponsored.csv` (45 sponsored research projects from SMMME).
  - `research_projects_consultancy.csv` (17 industry consultancy projects).
  - `research_projects_seed.csv` (13 internal seed grant projects).
  - `faculty_profiles.csv` (16 current SMMME faculty members with Google Scholar citations).
- **MME Ingestion Script:** Created `scripts/ingest_mme_curriculum.py` to non-destructively merge MME data into `data/seed/kb/`.
- **Knowledge Base Expansion:**
  - `kb.course`: Expanded to 136 total courses (87 EE + 49 net new MME courses).
  - `kb.programme_requirement`: Expanded to 25 slots (13 EE + 12 MME: 4 Breadth, 3 Lateral, 5 Electives).
  - `kb.slot_option`: Expanded to 186 options (102 EE + 84 MME).
  - `kb.faculty`: Expanded to 51 entities (28 EE persons + 7 EE groups + 16 MME persons).
  - `kb.research_project`: Expanded to 213 projects (138 EE + 75 MME across 12 research areas).
  - `kb.research_area`: Expanded to 12 areas (6 EE + 6 SMMME areas).
  - `kb.resource`: Expanded to 248 learning resources (163 EE + 85 MME).
  - `kb.resource_course`: Expanded to 231 resource-course links.
  - `kb.data_issue`: Expanded to 32 cataloged items (19 EE + 13 MME).
- **Unified Skill & Goal Matrix:** Updated `scripts/generate_skills_and_goals.py`:
  - 32 total skills across Electrical and Materials engineering.
  - 80 course-skill associations validated against `kb.course`.
  - 11 career and research goals (6 EE + 5 MME).
  - 41 goal skill requirements.
- **Data Quality & Audit:**
  - Updated `scripts/check_data.py` to audit both EE and MME course syntax, project areas, slot integrity, and DAG acyclicity.
  - Automated report generation in `docs/data_quality_report.md`.
  - Verified idempotent reset via `dev.ps1 reset` loading 2134 rows.

## [Phase 1: Foundation & Data Model] - 2026-11-14
### Added
- Repository skeleton: `.gitignore`, `.dockerignore`, `.env.example`, `docker-compose.yml`, `Makefile`, and `requirements.txt`.
- Multi-schema PostgreSQL DDL in `docker/init.sql` defining 4 schemas: `kb`, `student`, `plan`, and `ops`.
- Native PostgreSQL triggers (`AFTER INSERT OR UPDATE OR DELETE`) on editable tables notifying `ops.reprocess_queue` via `pg_notify('reprocess_channel', ...)`.
- Reproducible curriculum ingestion script `scripts/ingest_ee_curriculum.py` for Electrical Engineering.
- Base seed files in `data/seed/kb/` covering 87 courses, 13 slots, 64 resolved prerequisites, 163 learning resources, 138 research projects, and 35 faculty entities.
- Idempotent seed loader `scripts/seed_loader.py` supporting `--reset` and foreign key topological order.
- FastAPI foundation in `app/main.py` with `/health` endpoint and Pydantic configuration (`app/config.py`).
- Strict 3-second database connection timeouts across application and tests to prevent silent hangs.
- Separated test suite: `tests/test_db_free.py` (offline, 9 passed) and `tests/test_db_dependent.py` (connection-timeout protected).
- Documentation: `README.md`, `docs/DATA_DICTIONARY.md`, `docs/architecture/overview.md`, `docs/decisions/ADR-001-stack-and-schema-architecture.md`, `docs/DATA_GAPS.md`.
