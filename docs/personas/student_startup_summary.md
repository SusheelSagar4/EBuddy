# Handover Note: student_startup Persona Integration

## 1. Scope
- **Persona ID:** `student_startup`
- **Target Goal:** `GOAL_STARTUP_FOUNDER` (Student Startup Founder)
- **Applicable Programmes:** `BTECH_EE` (Electrical Engineering) and `BTECH_MM` (Metallurgical and Materials Engineering) at IIT Bhubaneswar
- **Target Semesters:** Semesters 1 through 8 (from idea log & customer discovery in Sem 1–3 to MVP in Sem 4, pilot in Sem 6, funding readiness in Sem 7, and traction decision in Sem 8)

## 2. Files Added or Moved
- **Persona Package:** `app/personas/student_startup/` containing exactly the 8 standard files:
  - `persona.yaml` (Persona specification and planner weights)
  - `requirements.yaml` (11 startup goal skills and target proficiency levels, updated for v2 with `SKILL_STARTUP_PRODUCT_ANALYTICS`)
  - `mastery.yaml` (Mastery threshold criteria `MASTERY_STARTUP_FOUNDER`)
  - `milestones.yaml` (8 progression milestones across Sem 2–8, updated with v2 PRD/wireframe, TAM/SAM/SOM, and North Star/AARRR metrics)
  - `diagnostic.yaml` (Diagnostic blueprint targeting 3 skills, 5 items each, difficulty 30.0–70.0)
  - `policy_rules.yaml` (Rules S1–S7 with tunable default parameters)
  - `policy.py` (Deterministic persona policy implementing S1–S7 and plan item adjustments)
  - `README.md` (Persona documentation, archetype profile, governance rules, and draft notices)
- **Raw Startup Domain Data:** Placed in `data/raw/higher_studies/startup/` (`diagnostic_items.csv`, `milestones.csv`, `resources.csv`, `skills.csv`, `diagnostic.yaml`, `milestones.yaml`, `persona.yaml`, `policy_rules.yaml`, `CHANGES.md`).
- **Shared Institute Data:** Loaded once from `data/raw/institute/` (`institute_calendar.csv`, `institute_programmes.csv`, `institute_curriculum_slots.csv`) shared with `btech_upsc`. Zero duplicate tables or raw files.
- **KB Seed Extensions:** Appended normalized rows into existing `data/seed/kb/` tables matching exact schemas:
  - `data/seed/kb/goal.csv` (`GOAL_STARTUP_FOUNDER`)
  - `data/seed/kb/skill.csv` (11 startup skills including `SKILL_STARTUP_PRODUCT_ANALYTICS`)
  - `data/seed/kb/goal_skill_requirement.csv` (11 goal-skill requirements)
  - `data/seed/kb/resource.csv` (42 resources `SR01`–`SR42`, with `link_verified=False` for `SR12`, `SR14`, `SR15`, and verified `SR16`–`SR42`)
  - `data/seed/kb/mastery_criteria.json` (`MASTERY_STARTUP_FOUNDER`)

## 3. Shared Code Changes
- **Shared Code Audit:** **Zero changes** to shared engine contracts, loaders, or existing personas.
  - `app/engine/planner.py`: **Unchanged** (reused existing `enable_plan_adjustment` policy hook).
  - `app/contracts/*`: **Unchanged** (`PersonaSpec`, `StudentProfile`, `PlanItem`, etc. used without modification).
  - `app/personas/btech_upsc/*`: **Unchanged**.
  - `app/personas/ee_power_core/*`: **Unchanged**.
  - `app/personas/registry.py`: **Unchanged** (auto-discovers `student_startup` via directory scan).

## 4. Deterministic Policy Rules (S1–S7)
- **S1 (exam_weeks_pause):** If `end_sem_within_14d` OR `mid_sem_within_7d`: pauses new build work; keeps weekly customer calls and 1-hour sprint reviews; shifts milestone windows +1 week (uses dynamic date calculations against shared `institute_calendar.csv`).
- **S2 (cgpa_guard):** If `cgpa < floor_hard` (6.5) OR `cgpa_drop_last_sem >= 0.3` OR `active_backlog > 0`: caps venture hours at 6 hrs/wk (3 hrs/wk in Sem 1–2); freezes spending; displays departmental core fallback (`GOAL_EE_CORE_POWER` for EE; `GOAL_FALLBACK_MME_CORE` for MM).
- **S3 (validation_gate):** If `interviews_logged < 10` AND `milestone == startup_team_and_mvp`: blocks MVP spending and feature work; forces `startup_problem_validation` tasks.
- **S4 (runway_guard):** If `runway_months < 3` AND `monthly_burn > 0`: blocks new expenditures; surfaces cost-cutting, pausing, and incubation/grant options via official portals (`SR08` IIT BBS REP and `SR09` Startup India).
- **S5 (ip_before_disclosure):** If `public_demo_planned` AND `ip_status == unchecked`: inserts IP check task (`SR07`) and institute IP policy review prior to demo date.
- **S6 (placement_interplay):** If `sem == 7` AND `placement_registered`: preserves 5 hrs/wk venture floor during placement season; mandates written continue / pause / job-first decision in Sem 8 (`startup_traction_decision`).
- **S7 (project_alignment):** If `sem >= 7` AND `project_topic_unrelated_to_venture`: prompts student to discuss aligning their B.Tech project with the venture prototype with their project guide. Surfaced as a **prompt only**.

## 5. Key Architecture & Design Decisions
- **Clean Raw Data Boundaries:** All raw CSV seed files reside strictly in `data/raw/higher_studies/startup/`. The persona directory `app/personas/student_startup/` retains only the 8 standard specification and policy files.
- **No `facts.csv` Rule (Hard Rule 3):** No `facts.csv` was created for startup. The engine never quotes scheme grant amounts, subsidy figures, eligibility limits, or deadlines for Startup India, Startup Odisha, or IIT BBS REP; it only links official pages (`SR08`, `SR09`) and directs the student to "check the official page".
- **Unverified Resources Safeguard (Hard Rule 2):** Resources `SR12` (Hisrich textbook), `SR14` (IIT BBS EE/MME textbooks), and `SR15` (Startup India team lessons) have `verified: FALSE` and are strictly forbidden from becoming `resource` plan items. Any mention in plan reasons or exercises explicitly displays `"not confirmed yet"`.
- **v2 Resource and Metric Enhancements:**
  - Expanded resources to 42 items (`SR01`–`SR42`). New resources `SR16`–`SR42` are all verified (`verified=TRUE`).
  - `SKILL_STARTUP_TEAM_EXECUTION` gained verified resource `SR31` (*Atlassian Agile Coach & Figma Official Crash Courses*).
  - Only `SKILL_STARTUP_TECH_DEPTH` remains without verified resources (only `SR14`, `verified=FALSE`), whose practice exercises explicitly state `"not confirmed yet"`.
  - Updated Milestone Metrics:
    - `startup_team_and_mvp`: 1-page PRD, wireframe flow, and MVP core feature list.
    - `startup_business_model_economics`: Bottom-up TAM/SAM/SOM market sizing, CAC, and LTV estimates.
    - `startup_summer_pilot`: North Star metric, AARRR funnel metrics, retention baseline, and prerequisite `SKILL_STARTUP_PRODUCT_ANALYTICS`.
- **NPTEL Next-Run Notice (Hard Rule 5):** Because NPTEL course availability changes across semesters, all NPTEL resources display official enrollment links accompanied by `"check the course page for the next run"`.
- **Zero Invented Course-Skill Overlaps (Extra Rule 8):** No artificial course-to-startup skill mappings were created in `data/seed/kb/course_skill.csv`. All startup skills are covered via verified resources and active practice exercises.
- **Curriculum Track from Admission Year (Extra Rule 9):** Resolved dynamically via the helper: admitted 2025-26 or later $\rightarrow$ NEP track; admitted prior $\rightarrow$ 2016-17 (pre-NEP) track.

## 6. Known Gaps & Draft Defaults
- **Draft Defaults:** All requirement levels (70.0–80.0, including `SKILL_STARTUP_PRODUCT_ANALYTICS` at 75.0, importance 0.9) in `requirements.yaml` and mastery thresholds in `mastery.yaml` (min skill level 70.0, 2 project milestones, 2 timed assessments, 65.0 diagnostic score) are draft defaults pending formal validation by startup mentors and IIT BBS REP.
- **Missing Fallback Graceful Handling:** For `BTECH_MM`, the fallback goal `GOAL_FALLBACK_MME_CORE` refers to an unfulfilled upstream stub (`persona_mme_core_stub.yaml`). The policy handles missing fallback packages gracefully without throwing exceptions.
- **Diagnostic Bank:** 45 diagnostic items (15 per target skill across difficulties 30.0–58.0) are initial original drafts requiring validation by entrepreneurship educators. Diagnostic blueprint remains focused on 3 core skills (`SKILL_STARTUP_CUSTOMER_DISCOVERY`, `SKILL_STARTUP_UNIT_ECONOMICS_FINANCE`, `SKILL_STARTUP_IP_LEGAL_COMPLIANCE`).

## 7. Code Reuse Audit & Shared Module Proposal

### Functions in `student_startup/policy.py` vs `btech_upsc/policy.py`:
1. `get_track_for_admission_year`: **Imports and delegates** to `BTechUPSCPolicy.get_track_for_admission_year`.
2. `get_curriculum_slots`: **Copy with domain adaptation** (copies heavy/light slot filtering and academic hours calculation formula from `btech_upsc`, but adjusts available hours for venture scheduling and attaches S7 project alignment prompt).
3. `_load_policy_data` (calendar & curriculum slots loading): **Copy** (both classes independently read shared `institute_calendar.csv` and `institute_curriculum_slots.csv`).
4. `adjust_plan_items`: **Copy with domain adaptation** (copies the verified resource / active practice exercise synthetic item generation mechanism, adding startup-specific compliance notices for NPTEL runs, scheme portals, and unverified reference labels).

### Proposed Shared Module (`app/personas/shared/`):
To prevent logic drift across future personas, we propose introducing an `app/personas/shared/` package:
- `app/personas/shared/calendar.py`: Institute academic calendar parser, mid-sem/end-sem proximity checker (`is_end_sem_within_days(current_date, days)`).
- `app/personas/shared/curriculum.py`: Track resolution (`get_track_for_admission_year`), curriculum slot loader, and heavy/light slot partition (`classify_slots(slots)`).
- `app/personas/shared/planner_helpers.py`: Generic synthetic plan item generation covering skill gaps with verified resources and active practice exercises.

## 8. Test Verification & Commit History

### Test Counts (80 Tests Passing):
- `tests/unit/test_startup_data_validation.py`: 6 passed
- `tests/unit/test_startup_policy_rules.py`: 9 passed
- `tests/unit/test_startup_curriculum_slot_wiring.py`: 5 passed
- `tests/unit/test_startup_plan_adjustments.py`: 5 passed
- `tests/integration/test_startup_e2e_student_scenarios.py`: 4 passed (Sem 3 EE, Sem 6 MME, Sem 8 EE, plus unverified resources & scheme figures audit)
- `tests/unit/test_upsc_data_validation.py`: 5 passed
- `tests/unit/test_upsc_policy_rules.py`: 10 passed
- `tests/unit/test_upsc_curriculum_slot_wiring.py`: 5 passed
- `tests/unit/test_upsc_plan_adjustments.py`: 6 passed
- `tests/integration/test_upsc_e2e_student_scenarios.py`: 3 passed
- `tests/unit/test_import_boundaries.py`: 4 passed
- `tests/integration/test_walking_skeleton.py`: 1 passed
- `tests/test_db_free.py`: 9 passed
- `tests/conformance/test_persona_conformance.py`: 8 passed (all 8 checks passed across all personas)
- `scripts/check_data.py`: Data quality audit passed (0 placeholders, high-severity blockers = 2 upstream baseline issues)
- `scripts/check_placeholders.py`: 0 placeholders in seed CSVs

### Commit Log on `startup_roadmap`:
1. `1399b37` - feat(task1): loader, seed mapping and startup domain data validation
2. `96df5e8` - feat(task2): register student_startup persona with conformance files and fallback handling
3. `2294ae5` - feat(task3): implement startup policy rules S1-S7 with unit tests
4. `5f2988e` - feat(task4): wire curriculum slot analysis, heavy/light scheduling and project alignment prompt
5. `146b7a3` - feat(task5): end-to-end student scenarios and full conformance verification
6. `c89e449` - chore: update conformance report execution timestamp
7. `8a62e17` - fix: clean raw seed redundancy, add unverified resource audit tests, and add startup summary handover
8. `feat` - update student_startup with startup_v2 bundle, product analytics skill and SR16-SR42 resources
