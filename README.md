# Adobe Personalised Learning Buddy (IIT Bhubaneswar)

An AI-powered adaptive academic buddy for undergraduate students at **IIT Bhubaneswar**, covering **B.Tech Electrical Engineering (EE)** and **B.Tech Metallurgical and Materials Engineering (MME / SMMME)**, alongside non-core career pathways in **Software Development Engineering (SDE)**, **AI & Machine Learning (AI/ML)**, and **Data Analytics (DA)**.

The system guides students through the complete learning cycle: **Assess → Personalise → Learn → Practise → Adapt → Demonstrate Mastery**, strictly bounded by institutional academic rules, verifiable prerequisite DAGs, multi-schema PostgreSQL persistence, higher-studies pathways (GATE, CAT, GRE, GMAT, TOEFL, IELTS), and a four-agent collaborative architecture.

```mermaid
flowchart LR
    Student["Student Web UI<br/>(Zero-CDN, Local Assets)"] --> Gateway["FastAPI Server<br/>(:8000)"]
    Adminer["Adminer DB Viewer<br/>(:8080)"] --> DB[("PostgreSQL 16<br/>(4 Schemas: kb, student, plan, ops)")]
    
    subgraph MultiAgentSystem["Four-Agent Collaborative System"]
        Agent1["Agent 1: Academic Planner<br/>(Single Writer for Roadmap & Proposals)"]
        Agent2["Agent 2: Learning Material Orchestrator<br/>(KB Resource & Video Retrieval)"]
        Agent3["Agent 3: Assessment & Diagnostic<br/>(Adaptive CAT Theta Convergence)"]
        Agent4["Agent 4: Query Explainer<br/>(Grounded RAG & Citations)"]
    end

    Gateway --> MultiAgentSystem
    Agent1 <--> DB
    Agent2 <--> DB
    Agent3 <--> DB
    Agent4 <--> DB
    MultiAgentSystem --> LiteLLM["LiteLLM Wrapper<br/>(Air-Gapped, Local Pricing)"]
    DB -- "pg_notify('reprocess_channel')" --> Gateway
```

---

## 1. Quick Start

### Run the Complete Stack in 3 Commands

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Set your LLM provider key in .env (or leave blank to run in offline deterministic mode)
# Edit .env: set LLM_API_KEY=your_key_here, LLM_MODEL=openai/gpt-4o-mini

# 3. Start the entire containerized stack (PostgreSQL 16, Adminer, FastAPI Web UI)
docker compose up --build
```

On first boot, the application automatically verifies database connectivity, applies migrations/DDL, seeds PostgreSQL if empty with all 2,399+ verified rows, and exposes:
- **Learning Buddy Web UI:** [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Adminer DB Viewer:** [http://localhost:8080](http://localhost:8080)
  - *System:* PostgreSQL
  - *Server:* `db` (or `localhost` if connecting from host)
  - *Username:* `ebuddy_user`
  - *Password:* `ebuddy_password`
  - *Database:* `ebuddy`

### Windows Host Automation (`scripts\dev.ps1`)
On Windows environments without `make`, use the built-in PowerShell control script:
```powershell
# Start services
.\scripts\dev.ps1 up

# Reset database to clean seed state (idempotent, reloads all schemas & seeds)
.\scripts\dev.ps1 reset

# Run data quality & DAG audit report (generates docs/data_quality_report.md)
.\scripts\dev.ps1 check-data

# Run full test suite (58 passed tests + 49 subtests)
.\scripts\dev.ps1 test

# View service health and status
.\scripts\dev.ps1 status
```

---

## 2. Web UI Pages & Capabilities

The user interface is an air-gapped, zero-CDN web shell (vanilla HTML5, CSS3, ES6 JavaScript) served directly by FastAPI with zero external network requests:

| Page Route | Title | Core Features |
|---|---|---|
| **`/`** | **Home / Profile Selector** | Switch between synthetic persona profiles (`CONF_STU_EE_POWER_01`, `CONF_STU_MME_PROCESS_01`, etc.), displaying branch, semester, CGPA, and completed courses with synthetic data disclaimers. |
| **`/goals`** | **Goal Selection** | Browse available institutional goals filtered by branch plus cross-branch pathways (Power Systems, VLSI, SDE & Data, Core Metallurgy, UPSC Prep, etc.) with skill requirement badges. |
| **`/roadmap`** | **Academic Roadmap** | Visual semester roadmap highlighting fixed institutional core courses, ranked electives (skill-overlap driven), minor pathways, and unachievable student overload proposals. Traceable KB codes and provenance tags. |
| **`/diagnostic`** | **Adaptive Diagnostic** | Real-time Computerized Adaptive Testing (CAT) based on 1PL Item Response Theory. Questions dynamically selected based on student ability estimate ($\theta$), stopping on convergence spread ($\le 4.0$) or question cap. Shuffled answer options. |
| **`/chat`** | **Academic Tutor Chat** | Grounded question answering and course advice. Queries route deterministically or via LLM with strict KB citations. Course recommendations outside the student's branch produce non-blocking warnings. |
| **`/approvals`** | **Change Proposals** | Review student-driven and system-generated roadmap changes (overload credits, schedule changes, elective swaps). Formal Accept / Reject workflow preserving audit ledger. |
| **`/admin`** | **System Admin & DB Viewer** | System health status, database connection metrics, live row counts across all 4 schemas, and safe read-only preview of knowledge base tables with offline CSV fallbacks. |

---

## 3. Four-Agent Architecture & Single-Writer Rule

The core logic is orchestrated by four specialized agents operating under strict dependency boundaries:

```mermaid
flowchart TD
    User([Student / System Request]) --> Router{Task Classifier}
    
    Router -->|Roadmap / Schedule / Overload| A1[Agent 1: Academic Planner]
    Router -->|Learning Resources / Practice| A2[Agent 2: Learning Material Orchestrator]
    Router -->|Diagnostic Test / Evaluation| A3[Agent 3: Assessment & Diagnostic]
    Router -->|Academic Query / Explanation| A4[Agent 4: Query Explainer]
    
    A1 -->|Single Writer| PlanDB[(plan.plan & plan.change_proposal)]
    A2 -->|Read-Only Retrieval| ResDB[(kb.resource & kb.exercise)]
    A3 -->|CAT Theta Convergence| TestDB[(kb.exercise & student.skill_evidence)]
    A4 -->|Deterministic / LLM Grounded| Repos[(KB Repositories)]
    
    A2 -.->|Propose Resource/Task| A1
    A3 -.->|Report Weak Skills| A1
    A4 -.->|Propose Elective Change| A1
```

1. **Agent 1: Academic Planner (`app/agents/agent_1_planner.py`)**
   - **Exclusive Single-Writer Authority:** Agent 1 is the sole agent permitted to create, mutate, or version records in `plan.plan` and `plan.change_proposal`.
   - **Hard Student Constraints vs. Warning Baselines:** Student constraints (credit cap, weekly hours, headroom, avoid-course, not-together) are **hard** boundaries and never breached. Unsourced institutional baselines emit labelled non-blocking warnings.
   - **Deterministic DAG Scheduling:** Topological sort resolves prerequisite dependencies before dependent semesters.
2. **Agent 2: Learning Material Orchestrator (`app/agents/agent_2_learning.py`)**
   - Retrieves curated NPTEL, SWAYAM, and YouTube resources from `kb.resource` and practice items from `kb.exercise`.
   - Cannot directly edit the student plan; issues structured `ChangeProposal` records to Agent 1.
3. **Agent 3: Assessment & Diagnostic (`app/agents/agent_3_assessment.py`)**
   - Implements Computerized Adaptive Testing (CAT) with continuous ability updates ($\theta$).
   - Dynamically selects exercises at current ability, stopping when $n \ge 5$ and the range of the last 3 thetas $\le 4.0$, or $n \ge 8$.
   - Shuffles options at serve-time; scores deterministically against verified keys.
4. **Agent 4: Query Explainer (`app/agents/agent_4_query.py`)**
   - Answers student curriculum questions using grounded retrieval from KB repositories.
   - Never calls LiteLLM directly; delegates to `app/llm/client.py` with full call logging in `ops.llm_call_log`.

---

## 4. Models & Air-Gapped LLM Gateway

- **Primary LLM:** `openai/gpt-4o-mini` (Configured default in `.env.example`; supports `gemini/gemini-1.5-flash`, `azure/<deployment>`, or `ollama/<model>` purely via environment variables).
- **LiteLLM Gateway:** All model interactions route exclusively through `app/llm/client.py`. No agent or engine imports `litellm` directly, enforcing strict architectural layering.
- **Strict Air-Gap & Cost Isolation:**
  - `LITELLM_LOCAL_MODEL_COST_MAP=True`: Prohibits runtime fetching of remote cost maps from GitHub.
  - `LITELLM_TELEMETRY=False`: Disables all outbound usage reporting.
- **Deterministic Independence:** All prerequisite resolution, academic rule validation, credit limits, CAT item selection, and DAG scheduling execute in deterministic Python with zero model dependencies.

---

## 5. Configuration Reference

All application settings are read dynamically from environment variables without code modification:

| Variable | Default Value | Purpose |
|---|---|---|
| `LLM_MODEL` | `openai/gpt-4o-mini` | Model string passed directly to LiteLLM wrapper. |
| `LLM_API_KEY` | *(empty in example)* | API credential for configured provider. |
| `LLM_API_BASE` | *(empty)* | Optional custom endpoint (Ollama, Azure, LiteLLM proxy). |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Model for vector representations if active. |
| `LITELLM_LOCAL_MODEL_COST_MAP` | `True` | Forces LiteLLM to use local pricing tables (no GitHub fetch). |
| `LITELLM_TELEMETRY` | `False` | Completely disables third-party usage reporting. |
| `DATABASE_URL` | `postgresql+psycopg://...` | Connection URI with connection pooling and timeouts. |
| `APP_PORT` | `8000` | Exposed FastAPI application port. |
| `ADMINER_PORT` | `8080` | Exposed Adminer database viewer port. |

---

## 6. Academic Institutional Data & Raw Sources

The project ingests and structures official institutional data for IIT Bhubaneswar across two engineering schools, the Central Library, and higher-studies pathways:

### Canonical Raw Data Structure (`data/raw/`)

| Directory | Branch / Domain | Contents & Source Files | Structured Ingest Outputs |
|---|---|---|---|
| **`data/raw/ee/`** | **Electrical Engineering (EE)** | • `curriculum_semester_table.csv`<br/>• `curriculum_syllabus_only.csv`<br/>• `curriculum_notes_discrepancies.csv`<br/>• `video_playlists.csv` (90 courses)<br/>• `research_projects_v2.csv` (68 projects with PI)<br/>• `research_projects_all.csv` (138 projects) | • 87 courses (85 semester + 2 syllabus-only)<br/>• 13 requirement slots<br/>• 64 resolved prerequisite edges<br/>• 163 video resource URLs<br/>• 138 research projects<br/>• 35 faculty & group entities |
| **`data/raw/mme/`** | **Metallurgical & Materials Engg (MME / SMMME)** | • `curriculum_semester_table.csv`<br/>• `curriculum_notes_discrepancies.csv`<br/>• `video_playlists.csv` (45 courses)<br/>• `faculty_profiles.csv` (16 faculty)<br/>• `research_projects_sponsored.csv` (45 projects)<br/>• `research_projects_consultancy.csv` (17 projects)<br/>• `research_projects_seed.csv` (13 projects) | • 49 net new courses (136 total across both)<br/>• 12 net new slots (25 total)<br/>• 84 net new slot options (186 total)<br/>• 85 video resource URLs (248 total)<br/>• 75 research projects (213 total)<br/>• 16 verified faculty profiles (51 total) |
| **`data/raw/library/`** | **Central Library Publications** | • `publications.csv` (3,000 research publications)<br/>• `publications_electrical.csv` (765 EE papers)<br/>• `publications_metallurgy.csv` (176 MME papers)<br/>• `publications_summary.csv` | • Structured catalog converted from HTML/Excel records with author, department, and citation indexing. |
| **`data/raw/higher_studies/`** | **Higher Studies Database** | • 22 CSV tables covering GATE, CAT, GRE, GMAT, TOEFL, IELTS (`admission_stats.csv`, `exam_cycles.csv`, `exams.csv`, `institutions.csv`, `milestones.csv`, `paths.csv`, `prep_methods.csv`, `prep_templates.csv`, `programmes.csv`, `resources.csv`, `study_plans.csv`, `survey_responses.csv`, `syllabus_topics.csv`, `template_phases.csv`, `template_check.csv`, etc.) | • Relational schema for institutional admission trends, target percentiles, syllabus topic mapping, and multi-phase prep milestones. |

### Course Video Playlists & Learning Resources
Curated video learning resources from NPTEL, YouTube, and SWAYAM have been ingested, mapped to curriculum courses, and validated with zero fabricated links:

| Programme | Catalog Courses Mapped | Total URLs in `kb.resource` | Course Links in `kb.resource_course` | Coverage Status Breakdown |
|---|---|---|---|---|
| **Electrical Engineering (EE)** | 90 courses | **163 URLs** | 160 links (81 distinct courses) | • Playlist found: 73 URLs<br/>• Partial / related: 40 URLs<br/>• Not confirmed: 33 URLs<br/>• Lab theory: 17 URLs |
| **Metallurgical Engg (MME)** | 45 courses | **85 URLs** | 71 links (46 distinct courses) | • Playlist found: 16 URLs<br/>• Partial / related: 24 URLs<br/>• Not confirmed: 33 URLs<br/>• Lab theory: 12 URLs |
| **Combined in Database** | **135 courses** | **252 URLs** | **231 links** (127 distinct courses) | **All marked `link_verified = false`** |

*Data Hygiene Rules Enforced:*
1. **Link Verification Safety:** Every resource has `link_verified = false` until verified by live network health checks.
2. **No False Coverage:** Playlists with `"Not confirmed"` status are cataloged for review but **never** claimed as confirmed coverage.
3. **No Fabricated Data:** Courses designated `"No video applicable"` (e.g. seminars, internships) generate 0 dummy links.
4. **Multi-Role Mapping:** Primary, Backup 1, Backup 2, and Lab Theory links are explicitly tagged.

---

## 7. Knowledge Base Data Topology & Storage Map

The database architecture is partitioned into four explicit schemas: `kb` (Knowledge Base), `student` (Profiles & Ledger), `plan` (Deterministic Plans & Proposals), and `ops` (Reprocessing & LLM Audit Logs).

| Schema & Table | Seed File Path | Rows (DB) | Role & Provenance Status |
|---|---|---|---|
| `kb.source` | `data/seed/kb/source.csv` | 14 | Audit citations, institutional sources, and `AI_DRAFT` provenance tag. |
| `kb.department` | `data/seed/kb/department.csv` | 6 | Academic schools (SECS, SMMME, SMS, SIF, SBS, SHSSM). |
| `kb.programme` | `data/seed/kb/programme.csv` | 2 | Degree programs (`BTECH_EE`, `BTECH_MME`). |
| `kb.course` | `data/seed/kb/course.csv` | 136 | Unified course catalog (87 EE, 49 MME, 4 shared). Audited against raw tables. |
| `kb.course_alias` | `data/seed/kb/course_alias.csv` | 158 | Prerequisite name-to-code resolution dictionary. |
| `kb.course_prerequisite` | `data/seed/kb/course_prerequisite.csv` | 64 | Deterministic DAG prerequisite edges (EE verified). |
| `kb.course_offering` | `data/seed/kb/course_offering.csv` | 185 | Track-aware semester offerings (Track A vs. Track B). |
| `kb.programme_requirement` | `data/seed/kb/programme_requirement.csv` | 141 | Degree requirement slots derived directly from raw semester tables. |
| `kb.slot_option` | `data/seed/kb/slot_option.csv` | 186 | Courses fulfilling elective/lateral slots (102 EE + 84 MME). |
| `kb.resource` | `data/seed/kb/resource.csv` | 252 | Video, textbook, and public reference learning resources. |
| `kb.resource_course` | `data/seed/kb/resource_course.csv` | 231 | Course-to-resource mapping with role designations. |
| `kb.resource_skill` | `data/seed/kb/resource_skill.csv` | 5 | Resource-to-skill coverage for skills lacking institute courses (e.g., DB/SQL, OS). |
| `kb.minor_course` | `data/seed/kb/minor_course.csv` | 5 | Dynamic minor course options for CSE and AI minors (`draft_for_review`). |
| `kb.exercise` | `data/seed/kb/exercise.csv` | 61 | Calibrated practice items with difficulties, topics, and shuffled options. |
| `kb.skill` | `data/seed/kb/skill.csv` | 37 | Reconciled skill taxonomy (`SKILL_*`), mapped to courses and resources. |
| `kb.course_skill` | `data/seed/kb/course_skill.csv` | 80 | Validated course-to-skill mappings with PK `(course_code, skill_id)`. |
| `kb.goal` | `data/seed/kb/goal.csv` | 11 | Career, higher studies, and research pathways. |
| `kb.goal_skill_requirement` | `data/seed/kb/goal_skill_requirement.csv` | 41 | Required skill proficiency thresholds per goal. |
| `kb.relevance_tags` | `data/seed/kb/relevance_tags.csv` | 1,496 | Skill-first elective relevance matrix (`AI_DRAFT`, `draft_for_review`). |
| `kb.faculty` | `data/seed/kb/faculty.csv` | 51 | Faculty entities (44 individual persons, 7 groups). |
| `kb.research_project` | `data/seed/kb/research_project.csv` | 213 | Institute projects (138 EE + 75 MME: sponsored/consultancy/seed). |
| `kb.project_faculty` | `data/seed/kb/project_faculty.csv` | 149 | PI and Co-PI project affiliations. |
| `kb.project_keyword` | `data/seed/kb/project_keyword.csv` | 240 | Searchable keywords linked to research projects. |
| `student.student` | `data/seed/personas/*/students.csv` | 8 | Synthetic student profiles with distinct academic standings and constraints. |
| `plan.plan` | *(generated)* | — | Student study plans with versioning and validation reports. |
| `plan.change_proposal` | *(generated)* | — | Human-in-the-loop proposals for elective swaps and overload requests. |
| `ops.llm_call_log` | *(generated)* | — | Complete audit trail of prompt, context, token usage, and latency. |
| `ops.reprocess_queue` | *(trigger populated)* | — | Reactive event queue driven by PostgreSQL triggers. |

---

## 8. System Reset & Reactive Re-processing

### Idempotent Database Reset
To drop and reseed the database to a verified state:
- **Windows (PowerShell):**
  ```powershell
  .\scripts\dev.ps1 reset
  ```
- **Linux / macOS:**
  ```bash
  make reset
  ```
*Both scripts run `scripts/seed_loader.py --reset`, executing `docker/init.sql` and loading all 2,399+ seed rows in strict foreign-key dependency order. Running reset twice yields 100% identical row counts.*

### Reactive Re-processing Triggers
Native PostgreSQL triggers on editable tables publish change events into `ops.reprocess_queue` and dispatch `pg_notify('reprocess_channel', ...)` notifications:
```sql
CREATE TRIGGER trg_reprocess_kb_course
AFTER INSERT OR UPDATE OR DELETE ON kb.course
FOR EACH ROW EXECUTE FUNCTION ops.notify_reprocess_event();
```
A background listener consumes these events, re-evaluates impacted student skill states, re-runs the DAG planner and deterministic validator, and records plan diffs with `trigger = 'admin_edit'`.

---

## 9. Non-Core Career Pathways & Domain Packages (SDE, AI/ML & DA)

The repository integrates three specialized, non-core career transformation packages equipping core engineering undergraduates (EE and MME) to transition into high-growth software and data domains:

```mermaid
flowchart TD
    CoreLearner(["IIT BBS Core Student (EE / MME)"]) --> Tracks{Non-Core Domain Track}
    
    Tracks -->|SDE Pathway| SDE["Software Development Engineer (sde/)"]
    Tracks -->|AI/ML Pathway| AIML["AI & Machine Learning (aiml/)"]
    Tracks -->|Data Analyst Pathway| DA["Data Analytics (data_analyst/)"]
    
    SDE --> SDE_Out["Curriculum (35 Steps) • Tiers A/B/C (105 Rows)<br/>Checkpoints (35) • GitHub Repos (35) • Portfolios (8)<br/>Events & Hackathons (41) • LeetCode Problem Bank (1,193)"]
    AIML --> AIML_Out["Roadmap (6 Phases, 1,624 hrs) • Curated Resources (55)<br/>CBSE Math Prereqs (16 Chapters)<br/>Top IIT Fests (7) • Hackathons (25) • Competitions (30)"]
    DA --> DA_Out["5 Phases (20 Skills, 314 hrs) • Modules (44)<br/>Portfolio Projects (3) • Rubric Items (12)<br/>Hackathons & Contests (35) • Verified Quiz Bank (47)"]
```

### A. Software Development Engineer Package (`sde/`)

1. **Curriculum & Tiered Content (`sde/scripts/build_sde_csvs.py`):**
   - **8-Phase Roadmap (`01_sde_roadmap_overview.csv`):** `1_Programming_Foundations` through `8_Interview_Prep`.
   - **Tiered Learning Pedagogy (`02_phase_learning_content.csv`):** 35 steps × 3 tiers (105 total rows).
     - **Tier A (Introductory):** Recommended primary watch playlist.
     - **Tier B (Conceptual Deep Dive):** Mathematical / architectural foundations.
     - **Tier C (Hands-on Practice):** Applied coding problems and implementations.
   - **Proof-of-Learning Checkpoints (`03_topic_checkpoints.csv`):** Actionable criteria for every step.
   - **High-Impact GitHub Repositories (`04_project_repos.csv`):** 35 curated repositories (13 marked `HIGH` priority, e.g. `codecrafters-io/build-your-own-x`, `donnemartin/system-design-primer`).
   - **Flagship Portfolio Projects (`05_portfolio_projects.csv`):** 8 structured projects with target phases.

2. **SDE Competitions & Hackathons (`sde/scripts/build_sde_events_csvs.py`):**
   - **Master Event Catalog (`01_events_master.csv`):** 41 curated events (2 Tech Fests, 26 Hackathons, 13 Programming Competitions, e.g., ICPC India Regionals, TCS CodeVita, Microsoft Imagine Cup).
   - **Stage Eligibility Gating (`02_phase_eligibility.csv`):** Fests unlocked at `NONE_YET`; hackathons and contests unlock at `P1_Programming_and_Dev_Basics`.
   - **Recommendation Rules (`03_recommendation_rules.csv`):** 14 machine-readable rules governing diversity quotas (max 2 per organizer), registration filters, and hiring preferences (`YES` > `POSSIBLE` > `EXPOSURE_ONLY`).

3. **SDE Diagnostic Assessment Bank (`sde/scripts/build_sde_quiz_csvs.py`):**
   - **Raw Extraction (`01_problem_bank_raw.csv`):** 1,519 LeetCode DSA problems across Easy (259), Medium (684), and Hard (576) workbooks with 100% hyperlink resolution.
   - **Conflict Resolution & Deduplication (`02_problems_unique.csv`):** 1,193 unique problems. Cleanly isolates 320 cross-file difficulty conflicts as `AMBIGUOUS` (safe for topic practice), preserving 873 calibrated problems for difficulty-based scoring.
   - **15 Canonical Topics (`03_topics_roadmap_map.csv`):** Mapped to SDE steps 4–26 with automated quiz readiness verdicts: 9 `READY`, 4 `LIMITED`, 2 `INSUFFICIENT`.

---

### B. AI & Machine Learning Package (`aiml/`)

1. **Curriculum & Knowledge Base Pipeline (`aiml/scripts/build_csvs.py`):**
   - **6-Phase Roadmap (`01_roadmap.csv`):** `0_Foundations`, `1_Classical_ML`, `2_Deep_Learning`, `3_Projects`, `4_Specialization`, `5_Research` (1,624 total estimated hours).
   - **Curated Resources (`02_phase_resources.csv`):** 55 high-quality resources spanning Stanford CS229, Fast.ai, DeepLearning.AI, Karpathy’s Zero-to-Hero, and Hugging Face.
   - **CBSE/NCERT High School Math Expansion (`03_prerequisites.csv`):** Maps foundational requirements into 16 structured CBSE Class 11–12 chapters (calculus, linear algebra, vector algebra, coordinate geometry, probability).

2. **Events & Hackathons Pipeline (`aiml/scripts/build_events_csvs.py`):**
   - **Master Event Catalog (`01_events_master.csv`):** 62 events (7 Top IIT Tech Fests: Mood Indigo, Techfest, Shaastra, Kshitij, Techkriti, Wissenaire; 25 Hackathons; 30 Leaderboard Competitions: Kaggle, DrivenData, Zindi).
   - **Stage-Wise Unlocking (`02_phase_eligibility.csv`):** Exposure fests available to novices; hackathons/competitions unlock upon completing `1_Classical_ML`.
   - **Domain Mapping (`04_domain_to_phase_map.csv`):** Closed-vocabulary technical classification across 16 canonical domains.

---

### C. Data Analyst Package (`data_analyst/` / alias `da/`)

1. **Curriculum & Projects Pipeline (`data_analyst/scripts/build_da_csvs.py`):**
   - **5 Canonical Phases (`01_da_roadmap_overview.csv`):** `DA-PH1` (Foundations) through `DA-PH5` (Storytelling, Portfolio, Interviews).
   - **Curriculum Modules & Resources (`02_phase_modules_resources.csv`):** 44 modules across 20 skills with 78 module-resource join rows. Total curriculum duration: 314 hours.
   - **20-Skill Catalog (`03_skills_catalog.csv`):** Tools, SQL, Python, Business, Visualization, Statistics with verified prerequisite DAGs.
   - **Portfolio Projects & Rubrics (`05_projects.csv`, `06_project_rubric_items.csv`):** 3 real-world portfolio projects (UCI Online Retail, NYC TLC Trip Data, World Bank Open Data) with 12 structured rubric criteria.
   - **Flexible Pacing Profiles (`07_pacing_templates.csv`):** 12 months (6 hrs/wk), 6 months (12 hrs/wk), and 3 months (24 hrs/wk).

2. **Data Analyst Events & Hackathons (`data_analyst/scripts/build_da_events_csvs.py`):**
   - **Curated Indian Event Catalog (`01_events_master.csv`):** 35 events (12 Hackathons, 23 Competitions).
   - **Home Campus Boost:** Rule `R07` gives recommendation preference to IIT Bhubaneswar events (Wissenaire, TechZephyr).
   - **Diversity Quota:** Rule `R11` caps recommendations from any single host at 2.

3. **Data Analyst Assessment Engine (`data_analyst/scripts/build_da_quiz_csvs.py`):**
   - **Master Question Bank (`01_question_bank.csv`):** 47 questions (32 MCQs, 10 Numeric, 5 SQL).
   - **Source Position Bias Mitigation:** In the raw source, 81.25% of correct MCQ answers were option `b`. Rule `G02` enforces dynamic option shuffling and grades strictly by option text.
   - **Deterministic Grading:** Numeric tolerance ($\le \max(0.01, 1\%)$) and in-memory SQL result-set diffing.
   - **17 Checkpoints (`05_quiz_checkpoints.csv`):** 12 cluster checks, 4 phase-end barrier tests, and 1 final cumulative quiz.

---

### Executing the Domain Pipelines

All pipelines include intelligent path resolution and can be run from the repository root:

```bash
# 1. AI/ML Transformation Pipelines
python build_csvs.py
python build_events_csvs.py

# 2. SDE Transformation Pipelines
python build_sde_csvs.py
python build_sde_events_csvs.py
python build_sde_quiz_csvs.py

# 3. Data Analyst Transformation Pipelines
python build_da_csvs.py
python build_da_events_csvs.py
python build_da_quiz_csvs.py
```
*Pipelines can also be run directly within their package directories (`python sde/scripts/build_sde_csvs.py`, etc.).*

---

## 10. Testing & Quality Assurance

The repository includes a comprehensive 6-stage CI verification pipeline:

```bash
# 1. Run the complete automated test suite (58 tests, 49 subtests)
python -m pytest tests -q

# 2. Run the full CI pipeline (Windows PowerShell)
.\scripts\ci.ps1

# 2b. Run the full CI pipeline (Linux / macOS Bash)
./scripts/ci.sh

# 3. Run the live Web UI smoke test against running container
powershell -ExecutionPolicy Bypass -File .\scripts\ui_smoke.ps1
```

### CI Pipeline Verification Stages (`scripts/ci.ps1`):
1. **Import Boundary Validation:** Asserts that `litellm` is never imported inside `app/agents/` or `app/engine/`. All LLM calls pass through `app/llm/client.py`.
2. **Automated Test Suites:** Runs all unit, integration, and UI endpoint tests (58 passed in < 9s).
3. **Persona Conformance Matrix:** Evaluates 7 synthetic student profiles against 9 academic invariants (100% GREEN).
4. **Knowledge-Base Integrity Audit:** Audits course codes, prerequisite DAGs, and provenance labels.
5. **Secret & Model Name Scan:** Ensures no API keys or hard-coded vendor model names are committed.
6. **Zero-Outbound Air-Gap Scan:** Scans templates, static assets, and backend code to guarantee zero external CDNs, fonts, or network requests.

---

## 11. Compliance Checklist

| Rule # | Requirement | Implementation & Verification |
|---|---|---|
| **Rule 1** | LiteLLM Only via Client | Gateway in `app/llm/client.py`; verified by `test_import_boundaries.py`. |
| **Rule 2** | Configuration by Env Vars Only | `app/config.py` uses Pydantic BaseSettings; verified by secret & model scans. |
| **Rule 3** | `.env.example` Committed | Default tuned to `openai/gpt-4o-mini`; verified by automated tests. |
| **Rule 4** | Single-command Start, < 5 GB, linux/amd64 | `docker compose up --build` starts `app`, `db`, and `adminer` seamlessly. |
| **Rule 5** | No Secrets in Image | `.env` ignored in `.gitignore` and `.dockerignore`. |
| **Rule 6** | Plain CSV/JSON Seeds & Idempotent Reset | `scripts/seed_loader.py --reset` loads 2,399+ rows idempotently in topological order. |
| **Rule 7** | Data Control & Reactive Re-processing | Native PG triggers on editable tables fire `pg_notify` to `ops.reprocess_queue`. |
| **Rule 8** | Zero Outbound Network Traffic | Zero CDNs, zero Google Fonts, local static assets; verified by `test_no_external_references.py`. |
| **Rule 9** | Data Ethics & Provenance | Synthetic profiles tagged `is_synthetic = true`. AI-drafted content tagged `source_id = AI_DRAFT`, `status = draft_for_review`. |
| **Rule 10** | Never Fabricate Academic Data | Raw data strictly derived from `data/raw/`. Mismatches marked `unsourced`. |
| **Rule 11** | Valid KB Course Codes | Verified by deterministic foreign keys and topological DAG resolution. |
| **Rule 12** | Deterministic Plan Validator | Student constraints are strictly hard-blocked; unsourced baselines emit non-blocking warnings. |

---

## 12. Project Directory Layout

```
.
├── app/
│   ├── agents/                           # Four-agent collaborative system
│   │   ├── agent_1_planner.py            # Exclusive writer for roadmaps & proposals
│   │   ├── agent_2_learning.py           # Resource & practice orchestrator
│   │   ├── agent_3_assessment.py         # Adaptive CAT diagnostic assessor
│   │   └── agent_4_query.py              # Grounded curriculum query explainer
│   ├── api/                              # REST API endpoints
│   │   ├── health.py                     # Health & database probe
│   │   ├── student.py                    # Student profile & onboarding
│   │   └── ui_routes.py                  # Web UI JSON APIs (roadmap, chat, diagnostic, admin)
│   ├── contracts/                        # Strict Pydantic contracts & schemas
│   ├── engine/                           # Deterministic algorithmic core
│   │   ├── planner.py                    # Topological prerequisite DAG planner
│   │   ├── diagnostic.py                 # 1PL IRT adaptive testing engine
│   │   ├── relevance.py                  # Skill-first elective relevance scorer
│   │   ├── validator.py                  # Hard vs warning constraint validator
│   │   └── gaps.py                       # Skill gap analyzer
│   ├── kb/repositories.py                # Relational in-memory & DB query repositories
│   ├── llm/client.py                     # Air-gapped LiteLLM client with ops logging
│   ├── static/                           # Air-gapped static assets (CSS, JS; zero CDNs)
│   │   ├── css/style.css                 # Clean, responsive stylesheet
│   │   └── js/app.js                     # Vanilla JavaScript SPA controller
│   ├── templates/                        # Jinja2 HTML templates for all 7 UI pages
│   │   ├── base.html                     # Base layout with synthetic disclaimer banner
│   │   ├── index.html                    # Student profile selector
│   │   ├── goals.html                    # Goal browser
│   │   ├── roadmap.html                  # Academic roadmap viewer
│   │   ├── diagnostic.html               # Adaptive diagnostic test interface
│   │   ├── chat.html                     # Academic tutor chat
│   │   ├── approvals.html                # Change proposal review & decision
│   │   └── admin.html                    # System admin & table inspector
│   └── main.py                           # FastAPI application entrypoint
├── data/
│   ├── raw/                              # Canonical institutional data sources
│   │   ├── ee/                           # Electrical Engineering curriculum, videos, research
│   │   ├── mme/                          # Metallurgical Engineering curriculum, videos, faculty
│   │   ├── library/                      # Central Library catalog (3,000 publications)
│   │   └── higher_studies/               # Higher Studies pathways (GATE, CAT, GRE, GMAT, TOEFL, IELTS)
│   └── seed/                             # Structured relational seed data (2,399+ rows)
│       ├── kb/                           # Knowledge Base CSVs/JSONs (courses, skills, goals, resources)
│       ├── higher_studies/               # 14 relational tables for higher studies pathways
│       ├── personas/                     # Synthetic test personas & calibrated exercise banks
│       ├── student/                      # Student profiles, completed courses, and goals
│       └── survey/                       # Baseline survey instrument & diagnostic rubrics
├── sde/                                  # Software Development Engineer (SDE) domain package
│   ├── data/                             # Raw SDE Excel knowledge base sources
│   ├── scripts/                          # SDE transformation pipelines (build_sde_*.py)
│   ├── output/                           # Generated SDE relational CSV datasets
│   └── README.md                         # SDE domain catalog & execution guide
├── aiml/                                 # AI & Machine Learning (AI/ML) domain package
│   ├── data/                             # Raw AI/ML Excel knowledge base sources
│   ├── scripts/                          # AI/ML transformation pipelines (build_*.py)
│   ├── output/                           # Generated AI/ML relational CSV datasets
│   └── README.md                         # AI/ML domain catalog & execution guide
├── data_analyst/                         # Data Analyst (DA) domain package
│   ├── data/                             # Raw DA Excel knowledge base sources
│   ├── scripts/                          # DA transformation pipelines (build_da_*.py)
│   ├── output/                           # Generated DA relational CSV datasets (UTF-8 with BOM)
│   └── README.md                         # DA domain catalog & execution guide
├── da/                                   # Shorthand alias package for Data Analyst
├── output/                               # Unified legacy output directory (synchronized mirrors)
├── docker/
│   ├── Dockerfile                        # Multi-stage slim Docker image (linux/amd64)
│   ├── entrypoint.sh                     # Container initialization & seed loader check
│   └── init.sql                          # DDL creating schemas kb, student, plan, ops + triggers
├── docs/
│   ├── technical/                        # Architecture, contracts, and schema documentation
│   ├── evaluation/conformance_report.md  # Persona conformance test results matrix
│   ├── DATA_GAPS.md                      # Documented omissions and discrepancies
│   ├── data_quality_report.md            # Automated curriculum & prerequisite DAG report
│   ├── UI.md                             # Web UI design & airgap compliance documentation
│   └── CHANGELOG.md                      # Detailed changelog across all phases
├── scripts/
│   ├── ci.ps1 / ci.sh                    # Automated 6-stage CI verification runner
│   ├── dev.ps1                           # Windows automation (up, down, reset, test, check-data)
│   ├── seed_loader.py                    # Database seed loader and reset engine
│   ├── run_conformance.py                # Persona conformance test runner
│   ├── audit_course_catalogue.py         # Course catalog audit script
│   ├── ui_smoke.ps1                      # Live Web UI smoke test script
│   └── regenerate_relevance.py           # Skill-first relevance matrix generator
├── tests/
│   ├── api/test_ui_endpoints.py          # UI REST endpoint & HTML page rendering tests
│   ├── conformance/                      # Persona conformance test suite
│   ├── integration/                      # Multi-agent & curriculum integration tests
│   ├── unit/                             # Agent features, import boundary, & zero-external checks
│   ├── test_db_free.py                   # Offline compliance & syntax unit tests
│   └── test_db_dependent.py              # PostgreSQL integration tests
├── .env.example                          # Committed environment variable template
├── docker-compose.yml                    # Multi-container orchestration (app, db, adminer)
└── requirements.txt                      # Project Python dependencies
```
