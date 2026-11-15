# Product Flow Gap Analysis: EBuddy (IIT Bhubaneswar)
**Version:** 1.0.0  
**Phase:** Phase 1 Verification & Audit  
**Target Milestone:** Full Target Product Flow Implementation (F1 through F11)  
**Baseline Test Status:** 168 passed, 287 subtests passed (Unit, integration, conformance, and API suites green; 4 tests in `test_db_dependent.py` require running Postgres 16 container).

---

## 1. Executive Summary of Audit

An exhaustive code audit was conducted across `app/services/onboarding_service.py`, `app/api/student.py`, `app/api/ui_routes.py`, `app/engine/{planner,budget,weekly_guidance,relevance,rules,diagnostic,skill_state}.py`, the four agents, `app/personas/*`, `web/src/screens/*.js`, `docker/init.sql`, `data/seed/`, and domain packages `sde/`, `aiml/`, `data_analyst/`.

The system already possesses a mature, tested architectural foundation (Four Agents, 29 deterministic engine modules, 28 Pydantic v2 contracts, 2,399+ seed rows, and complete scorecards for `core_to_core`, `core_to_mba`, and `core_to_mtech`). The primary task is to **bridge the gap** between this foundation and the unified target product flow (**login → onboarding → brief roadmap → phases/topics → weekly personalised plans → quizzes → chat adjustments**), extending existing engines and agents without rewriting or breaking existing invariants.

---

## 2. Granular Gap Analysis Matrix (F1 through F11)

| Req ID | Requirement Description | Status | Existing Files Doing Part of It | Exact Gap to Close | Data Needed & Seed Availability |
|---|---|---|---|---|---|
| **F1** | **Unified Onboarding Form**<br/>Single form collecting branch (EE/MME), current semester (1-8), completed courses multi-select, CGPA, and field of interest (SDE, AI/ML, DA, Higher Studies, MBA, UPSC, Core Research/Industry, Startup). Range & prerequisite consistency validation. Persist to `student.*`. | **Partial** | • `app/services/onboarding_service.py`<br/>• `app/api/student.py` (`POST /api/student/onboard`)<br/>• `app/api/ui_routes.py`<br/>• `web/src/screens/onboarding.js` | Currently, onboarding is persona-switcher-centric, selecting from pre-set synthetic profiles (`CONF_STU_EE_POWER_01`). It lacks a unified flow where students pick branch, semester, multi-select completed courses from `kb.course` filtered by semester, input CGPA, and choose a career field. Consistency validation (prerequisites of completed courses satisfied) is missing. | `kb.course` has 136 courses (87 EE, 49 MME) and prerequisites in `kb.course_prerequisite`. All required course and prerequisite seed data **exists in seeds**. |
| **F2** | **Brief Roadmap for Chosen Field**<br/>Immediately post-onboarding, show a concise field roadmap overview derived strictly from database data. | **Partial** | • `sde/output/01_sde_roadmap_overview.csv`<br/>• `aiml/output/01_roadmap.csv`<br/>• `data_analyst/output/01_da_roadmap_overview.csv`<br/>• `data/seed/higher_studies/paths.csv` | SDE, AI/ML, and Data Analyst roadmap overview CSVs exist in domain package folders, but are not yet unified into relational `kb` tables or served via a standard API endpoint (`GET /api/field-roadmap/{field_id}`) to the frontend. | 8-phase SDE, 6-phase AI/ML, 5-phase DA, GATE/CAT templates exist in package outputs and seeds. Need unified seed loading into `kb.field_roadmap`. |
| **F3** | **Phases → Topics → Resources → Personalised Weekly Plans**<br/>Field roadmap decomposed into phases, topics, resources (SDE tiers, AI/ML resources, DA modules). Weekly plan via Agent 1 using deterministic capacity model: Available Hours = $f(\text{Contact Hours}, \text{Calendar Factor}, \text{CGPA Protection})$, Topic Cost = `est_hours`. Carry forward deferred tasks. | **Partial** | • `app/engine/budget.py`<br/>• `app/engine/weekly_guidance.py`<br/>• `app/agents/agent_1_planner.py`<br/>• `app/contracts/roadmap.py` (`WeeklyRoadmap`, `DailyTask`, `deferred_tasks`) | Existing `budget.py` and `weekly_guidance.py` convert college courses into study hours, but do not schedule **field-roadmap topics** into weeks. A deterministic field topic capacity model (`app/engine/field_planner.py`) is needed to schedule topics based on free hours, enforce min/max bounds (1-4 topics/week), and carry forward `deferred_tasks`. | SDE has 35 steps $\times$ 3 tiers; AI/ML has 55 resources; DA has 44 modules with hours. Topic estimated hours need explicit mapping or derivation from phase hours. |
| **F4** | **Chat / Query Plan Adjustments & One-Week Exceptions**<br/>Agent 4 + orchestrator handling plan edits ("slow down", "swap topic", "more projects") and one-week exceptions in **both** directions ("classes cancelled" $\to$ increase; "exams" $\to$ reduce). Only target week modified; other weeks untouched. | **Partial** | • `app/agents/agent_4_query.py`<br/>• `app/llm/tasks/intent_router.py`<br/>• `app/contracts/chat.py` (`Intent`)<br/>• `app/contracts/proposal.py`<br/>• `app/services/roadmap_orchestrator.py` | Agent 4 currently only creates workload *reduction* proposals (e.g. 30 min/day during exams). It lacks capacity *increase* proposals ("cancelled classes") and scoped single-week overrides that leave all other weeks untouched. `Intent` enum lacks `PLAN_EDIT` and `WEEK_EXCEPTION`. | No external data required; relies on Pydantic contract extension and Agent 4 / orchestrator logic. |
| **F5** | **College Course Recommendations (Eligibility + Redundancy Filters)**<br/>Recommend college courses (prereqs, minors, electives, laterals) passing BOTH eligibility filter (F8) and redundancy filter (pure function dropping courses whose topics the learning plan will cover before/at course offering date). | **Partial** | • `app/engine/relevance.py`<br/>• `app/engine/rules.py`<br/>• `data/seed/kb/course_skill.csv`<br/>• `data/seed/kb/slot_option.csv`, `minor_course.csv` | `relevance.py` ranks electives by skill relevance, but has NO plan-timing redundancy filter. A pure function `filter_redundant_courses` comparing plan scheduled dates vs course offering semesters is needed. Domain topics need topic-to-skill links. | `kb.course_skill` has 80 associations. Topic-to-skill mappings for SDE/AIML/DA need to be mapped to `kb.skill` taxonomy (flagged `SAMPLE-` where unsourced). |
| **F6** | **Prior-Knowledge Claim $\to$ 10–15 Question Quiz**<br/>If student claims prior knowledge, verify via 10–15 question quiz. Passing skips verified topics/phases; failing requires starting from Phase 1. | **Partial** | • `app/engine/diagnostic.py` (`AdaptiveDiagnostic`)<br/>• `app/engine/skill_state.py`<br/>• `app/services/diagnostic_service.py`<br/>• `data/seed/kb/exercise.csv` | `AdaptiveDiagnostic` stops at 5–8 items by default. Length must be configurable (10–15 items for prior knowledge) without breaking 5–8 default for existing tests. Questions must be drawn from domain banks, and skipping must be decided per topic/phase using evidence reliability $> 0.2$. | 61 questions in `kb.exercise`, 47 questions in `data_analyst/`, LeetCode problem bank in `sde/`. Question pools are readily available. |
| **F7** | **Periodic Quizzes Every 2–3 Topics + Strong/Weak Adaptation**<br/>Quiz triggered after every 2–3 completed topics (default 3) covering recent topics + retention items. Weak topics ($< 60\%$) get more resources and revision slots; strong topics ($\ge 80\%$) get expedited pacing. | **Partial** | • `app/agents/agent_3_assessment.py`<br/>• `app/llm/tasks/grader.py`<br/>• `app/engine/skill_state.py`<br/>• Checkpoint CSVs in `sde/` and `data_analyst/` | Topic completion tracking does not exist (students cannot currently mark topics done in the UI or API). No trigger exists to generate a retention quiz after every 2–3 completed topics, nor does Agent 2 currently scale resources based on weak/strong tags. | 35 SDE checkpoints and 17 DA quiz checkpoints exist in package outputs. Need a topic completion tracking table/service. |
| **F8** | **Shared Eligibility Service by CGPA**<br/>One unified function checking CGPA cut-offs, branch restrictions, semester offerings, and prerequisites. Used across recommendations, validation, overload proposals, and chat. | **Partial** | • `app/engine/rules.py` (`RuleEngine`)<br/>• `app/engine/validator.py` (`PlanValidator`)<br/>• `data/seed/kb/academic_rule.json` | Eligibility logic is currently split between `RuleEngine`, `Planner`, and `PlanValidator`. A single canonical function `check_course_eligibility(student, course_id, target_semester)` returning an `EligibilityResult` is required. | Institute academic rules exist in `academic_rule.json`. Minor CGPA cutoffs ($\ge 8.0$) exist; explicit seed table for course-specific CGPA cutoffs will be formalized. |
| **F9** | **Higher Studies (GATE, CAT, GRE, CGPA Maintenance)**<br/>Best-fit colleges (Reach/Target/Safe), entrance prep roadmaps (GATE 12/6/3 mo, CAT 16 wk, GRE/GMAT/IELTS), and explicit CGPA-maintenance formula. | **Partial** | • `app/engine/gate_readiness_shortlist.py`<br/>• `app/engine/gate_planner.py`<br/>• `app/engine/mba_mocks_shortlist.py`<br/>• `app/engine/mba_planner.py`<br/>• `data/seed/higher_studies/*` | GATE (M.Tech) and CAT (MBA) engines are fully built and verified (32/32 scorecards). Missing unified routing from the new onboarding form, GRE/MS abroad guidance, and an explicit CGPA-maintenance calculation formula. | 14 relational tables in `data/seed/higher_studies/` covering exams, institutions, cutoffs, and speed templates exist. |
| **F10** | **Civil Services (UPSC CSE / ESE)**<br/>Exam-prep plan (Prelims, Mains, Interview, Optional subject) structured into phases, topics, and weekly plans via the F3 planner. | **Partial** | • `app/personas/btech_upsc/`<br/>• `tests/integration/test_upsc_e2e_student_scenarios.py` | The `btech_upsc` persona has milestone and policy rules, but lacks fine-grained syllabus topics and study resources structured for weekly topic scheduling. | High-level UPSC syllabus exists in persona YAML. Need structured topic seeds for Prelims GS, CSAT, and Engineering Optional (flagged `SAMPLE-` where appropriate). |
| **F11** | **Unified Web UI (Zero-CDN ES6 SPA)**<br/>Expose F1–F10 in the frontend: unified onboarding form, brief roadmap view, phases/topics with "mark done" toggles, weekly plans with capacity breakdown, course recommendation cards with rule badges, prior-knowledge & periodic quiz views, and chat approval cards. | **Partial** | • `web/index.html`<br/>• `web/src/app.js`<br/>• `web/src/screens/*.js`<br/>• `web/src/api/client.js` | Screens currently focus on persona switcher, plan items, and individual feature tabs. Need to add the unified onboarding form, field brief roadmap, topic completion toggles, 10–15 question quiz flow, periodic quiz cards, and recommendation badges. | Design tokens in `tokens.css` and local layout styling in `style.css` exist. Zero-CDN rule preserved. |

---

## 3. Architectural Mapping & Resolution Strategy

To respect Ground Rule 0 ("Do NOT start from scratch, re-scaffold, rename or delete existing modules"):
1. **Mapping New Flow to Existing Personas/Goals:**
   - Field `SDE` $\longrightarrow$ `GOAL_SDE` / `sde` domain package.
   - Field `AI/ML` $\longrightarrow$ `GOAL_AIML` / `aiml` domain package.
   - Field `Data Analytics` $\longrightarrow$ `GOAL_DA` / `data_analyst` domain package.
   - Field `Higher Studies (GATE / M.Tech)` $\longrightarrow$ `GOAL_MTECH_GATE` / `core_to_mtech`.
   - Field `Higher Studies (MBA / CAT)` $\longrightarrow$ `GOAL_MBA_CAT` / `core_to_mba`.
   - Field `Civil Services (UPSC)` $\longrightarrow$ `GOAL_UPSC` / `btech_upsc` persona.
   - Field `Core Engineering Research` $\longrightarrow$ `GOAL_CORE_RESEARCH` / `core_to_core`.
   - Field `Core Engineering Industry` $\longrightarrow$ `GOAL_CORE_INDUSTRY` / `core_to_core`.
   - Field `Student Startup / Entrepreneurship` $\longrightarrow$ `GOAL_STARTUP` / `student_startup` persona.

2. **Single-Writer Rule Preservation:**
   - Any modification to a student's active plan (from F4 chat edits, F6 prior-knowledge quiz skipping, or F7 periodic quiz weak/strong adjustments) is formulated as a `ChangeProposal`.
   - `RoadmapOrchestrator` manages student approval and triggers `RoadmapPlannerAgent` (Agent 1) to validate with `PlanValidator` and write Plan Version $N+1$.

3. **Deterministic Core vs. LLM Boundary:**
   - The capacity model, topic allocation, prerequisite scheduling, eligibility evaluation, and redundancy filtering are 100% deterministic Python functions located in `app/engine/`.
   - The LLM (`app/llm/client.py`) is invoked only for conversational presentation, explanation phrasing, and intent classification.

---

## 4. Next Implementation Steps (Following Prompt Section 3 Order)

1. **Step 2 (Data Layer):** 
   - Load SDE, AI/ML, and DA roadmap CSVs into unified seed tables.
   - Create topic-to-skill mappings and estimated hours metadata.
   - Add structured UPSC syllabus topics and higher studies tables into `data/seed/`.
   - Update `docs/DATA_DICTIONARY.md` and `docs/DATA_GAPS.md`.
2. **Step 3 (Eligibility & Onboarding):**
   - Implement shared eligibility service (`app/engine/course_eligibility.py` or consolidate in `app/engine/rules.py`).
   - Implement unified onboarding service and endpoint (`POST /api/student/onboard-unified` / updated `onboard_student`).
   - Implement brief roadmap endpoint (`GET /api/field-roadmap/{field_id}`).
3. **Step 4 (Field Planner & Capacity Model):**
   - Implement `app/engine/field_planner.py` with the deterministic capacity model.
   - Wire weekly plan generation through Agent 1 (`WeeklyRoadmap`).
4. **Step 5 (Course Recommendations with Redundancy Filter):**
   - Implement pure function `filter_redundant_courses` in `app/engine/relevance.py` or `course_eligibility.py`.
   - Test the NLP Semester 4 vs Semester 6 / Semester 5 test cases.
5. **Step 6 (Quizzes & Adaptation):**
   - Configure `AdaptiveDiagnostic` for 10-15 items for prior knowledge claim verification.
   - Implement topic completion tracking (`TopicProgressService`) and "every 2-3 topics" retention quiz trigger.
   - Wire weak/strong topic adaptation back into weekly plan generation.
6. **Step 7 (Chat & Scoped One-Week Exceptions):**
   - Update `app/contracts/chat.py` with `PLAN_EDIT` and `WEEK_EXCEPTION` intents (bump contract to v1.3.0 and export schemas).
   - Update Agent 4 and orchestrator to handle capacity increase ("classes cancelled") and scoped one-week overrides.
7. **Step 8 (Higher Studies & Civil Services Routing):**
   - Implement CGPA maintenance calculator and link unified onboarding to existing GATE/MBA/UPSC engines.
8. **Step 9 (UI & Comprehensive Testing):**
   - Update SPA screens in `web/src/screens/` and API client.
   - Add unit, API, integration, and scenario tests for all new capabilities.
   - Verify all tests pass, update documentation and generate final test report.
