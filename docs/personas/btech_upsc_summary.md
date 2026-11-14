# Handover Note: btech_upsc Persona Integration

## 1. Scope
- **Persona ID:** `btech_upsc`
- **Target Goal:** `GOAL_UPSC_CSE` (UPSC Civil Services Examination)
- **Applicable Programmes:** `BTECH_EE` (Electrical Engineering) and `BTECH_MM` (Metallurgical and Materials Engineering) at IIT Bhubaneswar
- **Target Semesters:** Semesters 1 through 8 (first realistic attempt: Semester 8 or post-graduation)

## 2. Files Added or Moved
- **Persona Package:** `app/personas/btech_upsc/` containing `persona.yaml`, `requirements.yaml`, `mastery.yaml`, `milestones.yaml`, `diagnostic.yaml`, `policy.py`, `policy_rules.yaml`, and `README.md`.
- **Raw UPSC Domain Data:** Placed in `data/raw/higher_studies/upsc/` (`cutoffs.csv`, `facts.csv`, `optional_catalog.csv`, `diagnostic_items.csv`, `milestones.csv`, `prep_templates_upsc.csv`, `prep_template_phases_upsc.csv`, `resources.csv`, `skills.csv`).
- **Shared Institute Data:** Relocated from UPSC raw folder to `data/raw/institute/` (`institute_calendar.csv`, `institute_programmes.csv`, `institute_curriculum_slots.csv`) for reuse across all personas.
- **KB Seed Extensions:** Rows appended matching existing schemas in:
  - `data/seed/kb/goal.csv` (`GOAL_UPSC_CSE`)
  - `data/seed/kb/skill.csv` (12 UPSC skills)
  - `data/seed/kb/goal_skill_requirement.csv` (12 requirement rows)
  - `data/seed/kb/resource.csv` (25 UPSC resources)
  - `data/seed/kb/course_skill.csv` (2 verified course-skill overlaps)
  - `data/raw/higher_studies/prep_templates.csv`, `template_phases.csv`, `template_check.csv`, `exams.csv`.

## 3. Shared Code Changes
- **`app/contracts/persona.py`:** Added `fallback_goals: Dict[str, str] = {}` to `PersonaSpec` with updated schema in `docs/contracts/PersonaSpec.json` (satisfies Pydantic `extra="forbid"` on `BaseContract`).
- **`app/engine/planner.py`:** Added an opt-in policy hook delegating plan item adjustments to registered policies when `enable_plan_adjustment == True`. If a policy raises an exception, the error is logged with `persona_id` via the standard `logging` module and execution safely falls back to unadjusted items.
- **`app/personas/policy.py`:** Added default `enable_plan_adjustment = False` on base `PersonaPolicy` and updated `adjust_plan_items` signature with optional `gaps`.
- **`data/seed/kb/programme.csv`:** Removed duplicate `BTECH_MME` row; normalized on existing `BTECH_MM`.
- **`scripts/check_placeholders.py`:** Added graceful fallback to audit `data/seed/kb/*.csv` directly when PostgreSQL container is offline.

## 4. Deterministic Policy Rules (R1–R10)
- **R1 (Workload Overload):** Pauses optional/static preparation and shifts milestones by 1 week when semester workload is heavy (< 10 hrs/wk available) in Sem 6/7.
- **R2 (CGPA Guard):** Caps weekly UPSC preparation (3 hrs/wk in Sem 1–2; 6 hrs/wk in Sem 3+) and routes to departmental core fallback when CGPA < 6.5 or backlogs exist.
- **R3 (Optional Gate):** Blocks advanced optional skills and forces `upsc_optional_lock_in` if undecided by Sem 5 (EE) or Sem 6 (MM), flagging MM for SME review.
- **R4 (NCERT Baseline Gate):** Blocks static syllabus pass 1 and forces baseline completion if NCERT reading completion < 80% by Sem 3.
- **R5 (CSAT Remediation):** Injects 4 hrs/wk CSAT remedial practice if diagnostic score is < 40/100.
- **R6 (Placement Interplay):** Pauses optional prep and increases target semester study hours to 25 hrs/wk if no placement offer is secured in Sem 7.
- **R7 (Attempt Decision):** Requires $\ge 2$ verified cut-off cycles (otherwise outputs "not confirmed yet") and 3 benchmark mocks $\ge \text{target} - 15$ to attempt during Sem 8.
- **R8 (Late Start):** Routes students joining in Sem 7 with static completion < 50% to attempt after graduation.
- **R9 (Age Check):** Validates age $\ge 21$ by target exam year based on verified facts `F01`/`F02`.
- **R10 (Sem 8 Clashes):** Enforces static cutoff (22 Apr 2027), viva cap (until 19 May 2027), and revision-only mode before Prelims (23 May 2027).

## 5. Key Architecture & Design Decisions
- **`BTECH_MM` Code:** Normalized all references (`persona.yaml`, curriculum slots, optional catalog, programme tables) to existing code `BTECH_MM`.
- **Admission-Year Track Resolution:** Curriculum track is determined by admission year (admitted 2025-26 or later $\rightarrow$ NEP; prior $\rightarrow$ 2016-17 pre-NEP), not inferred from semester number.
- **Skill Gap Coverage:** UPSC skills lacking institutional courses are covered via verified `resource` items and active `exercise` items.
- **Unverified Data Handling:** Any fact or resource with `verified=FALSE` is never presented as confirmed fact; policy and item reasons output `"not confirmed yet"`.
- **Fact `F22`:** Placement CGPA cutoff has `source_url: ""` with `value: NOT_FOUND` and `verified: FALSE` (permitted by updated validation tests).

## 6. Course-Skill Mappings
- **Retained (Real Overlaps):**
  - `EE2L001` (Network Theory) $\rightarrow$ `SKILL_UPSC_OPTIONAL` (Direct overlap with UPSC Electrical Engineering Optional Paper 1).
  - `ID2L003` (Environmental Science, Tech & Mgmt) $\rightarrow$ `SKILL_UPSC_GS3_STI_ENV_SECURITY` (Direct overlap with GS-3 ecology, biodiversity, climate change).
- **Removed (Artificial Overlaps):**
  - `MA1L001`, `MA2L003`, `CS1L001` $\rightarrow$ `SKILL_UPSC_CSAT` / `TESTCRAFT` (Calculus, differential equations, and C coding do not cover Class X basic numeracy or UPSC testcraft).
  - `HS1L001`, `HS1L002` $\rightarrow$ GS1/GS2/GS3/GS4/Ethics/Essay/Answer Writing (Basic English communication does not teach civil services general studies or analytical answer writing).
  - `ML2L002` $\rightarrow$ `SKILL_UPSC_OPTIONAL` (UPSC does not offer Metallurgical Engineering as an optional subject per Fact F08).

## 7. Known Gaps & Draft Defaults
- **Draft Defaults:** All values in `mastery.yaml` and `requirements.yaml` are draft defaults derived from `skills.csv` and `ee_power_core` pending final SME validation.
- **Placement CGPA Floor:** 6.5 hard floor and 7.0 soft floor in `policy_rules.yaml` are draft assumptions pending official CDC placement data (Data Request D01).
- **Cutoffs:** Only CSE-2025 cutoffs are confirmed; earlier cycles remain unverified.
- **Degree Proof:** Provision for appearing in Prelims before final degree proof is subject to verification in the CSE-2027 notification (due 13 Jan 2027).
- **MME Fallback Stub:** `GOAL_FALLBACK_MME_CORE` points to `persona_mme_core_stub.yaml` pending full MME core persona implementation.
- **Diagnostic Items:** 45 items (15 per diagnostic skill) are initial drafts requiring mentor validation.
- **Upstream Data Issues:** `ISSUE_PREREQ_EE6L007` (prerequisite title mismatch) and `ISSUE_MME_CURR_03` (duplicate course codes `ML4L001`–`ML4L003` in curriculum) exist on `origin/main` and are cataloged as upstream issues.

## 8. Test Verification & Commit History
### Test Counts (51 Tests Passing):
- `tests/unit/test_upsc_data_validation.py`: 5 passed
- `tests/unit/test_upsc_policy_rules.py`: 10 passed
- `tests/unit/test_upsc_curriculum_slot_wiring.py`: 5 passed
- `tests/unit/test_upsc_plan_adjustments.py`: 6 passed
- `tests/unit/test_import_boundaries.py`: 4 passed
- `tests/integration/test_upsc_e2e_student_scenarios.py`: 3 passed
- `tests/integration/test_walking_skeleton.py`: 1 passed
- `tests/test_db_free.py`: 9 passed
- `tests/conformance/test_persona_conformance.py`: 8 passed (Checks 1–8 OK)
- `scripts/check_data.py` & `scripts/check_placeholders.py`: 0 placeholders

### Commit Log:
1. `a5c4012` - feat(task1): loader, seed mapping and upsc domain data validation
2. `52ee173` - feat(task2): register btech_upsc persona package and normalize BTECH_MME programme
3. `89509bc` - feat(task3): implement deterministic policy rules R1-R10 and unit test coverage
4. `28957f3` - feat(task4): planner curriculum slot wiring and optional catalog recommendations
5. `3979a37` - feat(task5): add end-to-end multi-persona verification for Sem3 EE, Sem6 MME, and Sem8 EE
6. `bd30b32` - fix: address review items on upsc persona, shared institute data, admission track resolution, and course overlaps
7. `aea7a34` - feat: implement opt-in plan item adjustment for upsc persona covering skill gaps via verified resources and exercises
8. `72545cc` - docs: add btech_upsc handover summary and add logger error handling in planner

## 9. Next Steps
- Branch from `upsc_roadmap` to build the second persona (`btech_startup`).
- Refresh UPSC domain facts, cutoffs, and exam calendar dates upon publication of the official UPSC CSE-2027 notification (expected 13 January 2027).
