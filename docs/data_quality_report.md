# Data Quality & Integrity Report — IIT Bhubaneswar (EE & MME)

**Automated Audit Run via:** `scripts/check_data.py`
**Mode:** DEVELOPMENT
**Curriculum Batch Currency:** `2016-17` (Warning: Confirm applicability to current target batch)

## 1. Course Code & Identity Verification
- **Total Unique Courses (course_id PK):** 136
- **Syntax Check on display_code (`^[A-Z]{2}\d[A-Z]\d{3}$`):** PASSED (0 violations)
- **Courses Flagged with code_conflict = true:** 6 (Expected 6: ML4L001/002/003 core vs electives)

## 2. Prerequisite Graph & DAG Verification
- **Total Directed Edges:** 64
- **Acyclicity Check (DAG Property):** PASSED (Zero cycles detected)
- **Track-Aware Temporal Ordering:** PASSED (0 violations)

## 3. Curriculum Slots & Option Pools
- **Programme Slots Defined:** 25 (13 EE + 12 MME)
- **Slot Option Referential Integrity:** PASSED (100% options exist in kb.course)
- **Plannable Course Credits (> 0):** PASSED (100% valid)

## 4. Learning Resources & Playlists Coverage
- **Total Stored Resources:** 319
- **Verified Links:** 52 (0% - Defaults to False per data hygiene)
- **Official NPTEL / MIT OCW:** 231 (72.4%)
- **Full Playlist Coverage:** 89 (27.9%)

## 5. Research Projects & Faculty Directory
- **Faculty Isolation Rule:** PASSED (0 group terms in persons)
- **Total Research Projects:** 12 areas, 196 projects

## 6. Open Data Issues Register
- **Total Cataloged Issues:** 38
- **High-Severity Blockers:** 2
  - **ISSUE_PREREQ_EE6L007** [UNRESOLVED] `EE6L007`: Prerequisite 'Measurement and Electronic Instruments' matches no course name in curriculum semester table.
  - **ISSUE_MME_CURR_03** [ACKNOWLEDGED] `Duplicate codes ML4L001–ML4L003`: Sem VII core courses (Light metals and alloys, Elements of electroceramics, Polymers and nanocomposites) use the same codes as three Metallurgical electives (Joining of metals and alloys, Solidification of metals and alloys, Electrochemical methods in metallurgy).

## 7. Status & Placeholder Audit Across All Tables
- **Flagged Placeholders (is_placeholder = true):** 0
- **Unsourced Baselines (rules/credits/minors):** 7
- **Draft for Review (skills/goals):** 2067
  - `academic_rule`: {'unsourced_baseline': 4}
  - `course_skill`: {'draft_for_review': 91}
  - `exercise`: {'draft_for_review': 60}
  - `goal`: {'draft_for_review': 13}
  - `goal_skill_requirement`: {'draft_for_review': 66}
  - `mastery_criteria`: {'draft_for_review': 5}
  - `minor`: {'unsourced_baseline': 2}
  - `minor_course`: {'draft_for_review': 4}
  - `programme`: {'unsourced_baseline': 1}
  - `relevance_tags`: {'draft_for_review': 1768}
  - `skill`: {'draft_for_review': 60}
