# Data Dictionary — Personalised Learning Buddy (IIT Bhubaneswar)

**Scope:** Schema and column specifications across the 4 PostgreSQL schemas: `kb`, `student`, `plan`, and `ops`.  
**Last Updated:** Phase 1 (Foundation & Data Model)  
**Target Institute:** Indian Institute of Technology Bhubaneswar (IIT BBS)

---

## 1. Schema `kb` (Knowledge Base)

### Table: `kb.source`
Stores provenance, licensing, and reliability metadata for every ingested curriculum, rule, and open educational resource.
- `source_id` (VARCHAR(100), PK): Unique source identifier (e.g. `IITBBS_EE_CURRICULUM_2016_17`).
- `title` (VARCHAR(255), NOT NULL): Official title of document/catalog.
- `url` (TEXT): Public URL or canonical link.
- `publisher` (VARCHAR(255)): Publishing institution or department.
- `licence` (VARCHAR(100)): Content license (e.g., CC-BY, Public Academic Curriculum).
- `retrieved_on` (DATE): Ingestion date.
- `doc_type` (VARCHAR(50)): `curriculum_pdf`, `course_page`, `rules`, `oer`.
- `reliability` (VARCHAR(50)): `official`, `compiled_secondary`, `placeholder`.
- `academic_year` (VARCHAR(50)): Academic batch currency (e.g. `2016-17`).
- `notes` (TEXT): Additional provenance remarks.

### Table: `kb.department`
Academic schools/departments offering courses.
- `department_id` (VARCHAR(50), PK): Department code (`EE`, `EC`, `CS`, `MM`, `ME`, `CE`, `BS`, `HSS`).
- `name` (VARCHAR(255), NOT NULL): Full department title.

### Table: `kb.programme`
Degree programmes supported by the buddy.
- `programme_id` (VARCHAR(50), PK): Programme code (`BTECH_EE`, `BTECH_MM`).
- `name` (VARCHAR(255), NOT NULL): Full degree title.
- `department_id` (VARCHAR(50), FK -> `kb.department`): Offering parent department.
- `total_credits_required` (NUMERIC(5,1), NOT NULL): Degree credit requirement (181.0 for EE).
- `duration_semesters` (INT, NOT NULL DEFAULT 8): Programme length.
- `curriculum_version` (VARCHAR(50) DEFAULT '2016-17'): Batch version.

### Table: `kb.course`
Course catalog master register.
- `course_code` (VARCHAR(20), PK): Course alphanumeric code (e.g. `EE2L001`).
- `title` (VARCHAR(255), NOT NULL): Full course name.
- `department_id` (VARCHAR(50)): Department tag.
- `credits` (NUMERIC(4,1), NOT NULL): Academic credit weight.
- `ltp` (VARCHAR(20)): Lecture-Tutorial-Practical structure (e.g. `3-1-0`).
- `course_type` (VARCHAR(50), NOT NULL): `core`, `lateral`, `breadth`, `elective`, `laboratory`.
- `type_source` (VARCHAR(20) DEFAULT 'source'): `source` or `inferred`.
- `mode` (VARCHAR(20) DEFAULT 'offline'): `offline` or `online`.
- `level` (VARCHAR(20) DEFAULT 'UG'): `UG` or `PG`.
- `syllabus_text` (TEXT): Detailed topic list (NULL until provided in `data/raw/`).
- `learning_objectives` (TEXT): Stated outcomes.
- `in_semester_table` (BOOLEAN DEFAULT TRUE): False for syllabus-only courses (`EC2L005`, `EC6L004`).
- `source_id` (VARCHAR(100), FK -> `kb.source`): Source provenance citation.
- `is_placeholder` (BOOLEAN DEFAULT FALSE): True if row is synthetic/placeholder.

### Table: `kb.course_alias`
Mapping from colloquial prerequisite text tokens to formal course codes.
- `alias_name` (VARCHAR(255), PK): Normalized prerequisite string (e.g. `"signals and systems"`).
- `target_course_code` (VARCHAR(20), FK -> `kb.course`): Resolved target code (`EC2L002`).

### Table: `kb.course_prerequisite`
Acyclic directed prerequisite graph.
- `course_code` (VARCHAR(20), FK -> `kb.course`): Dependent course.
- `prereq_code` (VARCHAR(20), FK -> `kb.course`): Prerequisite required.
- `relation` (VARCHAR(50) DEFAULT 'required'): `required`, `recommended`, `corequisite`.

### Table: `kb.course_offering`
Semester scheduling parity and track routing.
- `id` (SERIAL, PK): Row identifier.
- `course_code` (VARCHAR(20), FK -> `kb.course`): Course code.
- `semester_number` (INT): Recommended semester ($1$–$8$).
- `parity` (VARCHAR(10)): `odd` (Autumn) or `even` (Spring).
- `track` (VARCHAR(10) DEFAULT 'ALL'): `A`, `B`, or `ALL` for swapped-order first-year pairs.
- `offering_basis` (VARCHAR(100)): Provenance tag (`inferred_from_semester_table`).

### Table: `kb.programme_requirement`
Curriculum slots defining degree requirements.
- `slot_id` (VARCHAR(100), PK): Slot identifier (`SLOT_SEM4_LATERAL_1`).
- `programme_id` (VARCHAR(50), FK -> `kb.programme`): Target degree.
- `semester_number` (INT): Semester position.
- `slot_name` (VARCHAR(255)): Descriptive slot name.
- `slot_type` (VARCHAR(50)): `core`, `lateral`, `breadth`, `elective`.
- `min_credits` (NUMERIC(4,1)): Minimum credit weight.
- `max_credits` (NUMERIC(4,1)): Maximum credit weight.
- `option_pool` (VARCHAR(255)): Name of candidate option pool.

### Table: `kb.slot_option`
Maps individual courses into eligible elective/lateral slot pools.
- `slot_id` (VARCHAR(100), FK -> `kb.programme_requirement`).
- `course_code` (VARCHAR(20), FK -> `kb.course`).

### Table: `kb.academic_rule`
Machine-readable institutional constraints executed by the deterministic validator.
- `rule_id` (VARCHAR(100), PK): Rule identifier (`RULE_SEM_CREDIT_CAP_REGULAR`).
- `rule_type` (VARCHAR(50)): `credit_cap`, `minor_eligibility`, `prereq`, `online_credit`.
- `parameters` (JSONB): Structured parameters (thresholds, cut-offs).
- `human_text` (TEXT): Exact quotation from academic ordinances.
- `source_id` (VARCHAR(100), FK -> `kb.source`).

### Table: `kb.skill`
Atomic academic & industry capabilities.
- `skill_id` (VARCHAR(100), PK): e.g. `SKILL_POWER_ELECTRONICS`.
- `name` (VARCHAR(255)): Human display name.
- `domain` (VARCHAR(100)): Technical area.
- `description` (TEXT): Scope of capability.
- `level_scale` (VARCHAR(50)): Scale definition (`0-100`).

### Table: `kb.resource`
Curated external video playlists and reading materials (stored as links + metadata).
- `resource_id` (VARCHAR(100), PK): Resource ID (`RES_EE3L004_PRIMARY`).
- `title` (VARCHAR(255)): Course/series title.
- `provider` (VARCHAR(100)): `NPTEL`, `MIT OCW`, `third-party`.
- `url` (TEXT): Web hyperlink (not fetched at runtime).
- `licence` (VARCHAR(100)): License.
- `resource_type` (VARCHAR(50)): `playlist`, `single_video`, `channel_search`.
- `coverage_status` (VARCHAR(50)): `Playlist found`, `Partial / related only`, `Not confirmed`.
- `link_verified` (BOOLEAN DEFAULT FALSE): Set true only after verification.
- `source_id` (VARCHAR(100), FK -> `kb.source`).

### Table: `kb.research_project`
Institutional research grants and faculty projects (for Higher Studies persona).
- `project_id` (VARCHAR(100), PK): e.g. `PROJ_EE_001`.
- `area_id` (VARCHAR(50), FK -> `kb.research_area`): Research group area.
- `title` (VARCHAR(500)): Project title.
- `funding_agency` (VARCHAR(255)): Sponsoring agency (SERB, DRDO, CPRI, etc.).
- `grant_lakhs` (NUMERIC(8,2)): Grant value in ₹ Lakhs.
- `start_year` (INT), `end_year` (INT): Project timeline.
- `scope_text` (TEXT): Technical scope abstract.
- `detail_level` (VARCHAR(20)): `full` (68 projects) or `title_only` (70 projects).
- `verified` (BOOLEAN DEFAULT FALSE): Verification flag.
- `source_confidence` (VARCHAR(50)): `compiled_secondary`.

### Table: `kb.faculty`
Faculty members and collaborative research groups.
- `faculty_id` (VARCHAR(100), PK): e.g. `FAC_PROF_SUBHRANSU_RANJAN_SAMANTARAY`.
- `display_name` (VARCHAR(255)): Name as published.
- `title` (VARCHAR(50)): Title (`Prof.`, `Dr.`).
- `group_name` (VARCHAR(255)): Empty for persons; group name for teams.
- `is_person` (BOOLEAN NOT NULL DEFAULT TRUE): False for research groups.

### Table: `kb.data_issue`
Audit trail of discrepancies discovered in raw source documents.
- `issue_id` (VARCHAR(100), PK): e.g. `ISSUE_CURR_01`.
- `entity_type` (VARCHAR(50)): Entity affected (`curriculum`, `faculty`, `prerequisite`).
- `entity_key` (VARCHAR(255)): Subject course code or name.
- `severity` (VARCHAR(20)): `high`, `medium`, `low`.
- `description` (TEXT): Description of ambiguity/conflict in source PDF.
- `resolution_notes` (TEXT): Treatment applied by loader.
- `status` (VARCHAR(50)): `acknowledged`, `unresolved`.

---

## 2. Schema `student` (Profiles, Evidence, Constraints)

- `student.student`: Core student profile (`student_id`, `programme_id`, `year`, `current_semester`, `cgpa`, `is_synthetic`, `persona_tag`).
- `student.completed_course`: Academic transcript (`student_id`, `course_code`, `grade`, `semester`, `is_backlog`).
- `student.goal`: Student declared aspirations (`student_id`, `goal_id`, `status`, `priority`).
- `student.interest`: Self-declared topical interests (`student_id`, `topic`, `strength`, `source`).
- `student.skill_evidence`: Append-only evidence ledger (`evidence_id`, `student_id`, `skill_id`, `source_type`, `score_0_100`, `reliability_weight`, `attempts`, `time_spent_min`).
- `student.skill_state`: Derived skill estimation (`student_id`, `skill_id`, `estimated_level`, `confidence`, `last_updated`).
- `student.constraint`: Planning constraints (`student_id`, `kind`, `value` JSONB).
- `student.preference`: Pedagogical preferences (`student_id`, `key`, `value`).

---

## 3. Schema `plan` (Outputs & Memory)

- `plan.plan`: Versioned learning plans (`plan_id`, `student_id`, `version`, `trigger`, `status`).
- `plan.plan_item`: Semester/week breakdown (`plan_id`, `semester_no`, `week_no`, `item_type`, `ref_id`, `hours`, `reason_json`).
- `plan.validation_report`: Hard deterministic audit output (`plan_id`, `passed`, `checks` JSONB).
- `plan.plan_diff`: Structural diff between versions (`from_plan_id`, `to_plan_id`, `summary_json`, `explanation_text`).
- `plan.decision_log`: Student overrides and choices (`student_id`, `ts`, `decision_type`, `detail` JSONB).
- `plan.assessment_attempt`: Diagnostic attempt records (`attempt_id`, `student_id`, `exercise_id`, `score`, `graded_by`).

---

## 4. Schema `ops` (Operations & Re-processing Queue)

- `ops.conversation` & `ops.message`: Multi-turn chat persistence.
- `ops.memory_summary`: Compact rolling memory summaries per student.
- `ops.reprocess_queue`: Event queue populated by PostgreSQL triggers on direct database modifications (`queue_id`, `entity_type`, `entity_id`, `action`, `status`).
- `ops.llm_call_log`: Telemetry audit log (`call_id`, `model`, `purpose`, `tokens_in`, `tokens_out`, `latency_ms`, `cache_hit`, `error`).

---

## 5. Supplementary Knowledge Repositories

### Repository: `data/raw/library/` (Central Library Publications)
Stores institutional academic publications and faculty output for contextual matching, research interest extraction, and higher-studies lab alignment.
- `publications.csv`: 3,000 bibliographic entries with fields (`sn`, `authors`, `title`, `source_title`, `document_type`, `institute_author`, `pub_type`, `school`, `doi`).
- `publications_electrical.csv`: 765 publications from the School of Electrical Sciences.
- `publications_metallurgy.csv`: 176 publications from the School of Minerals, Metallurgical & Materials Engineering.
- `publications_summary.csv`: Aggregated counts across schools and document types.

### Repository: `data/seed/higher_studies/` (Higher Studies Planning Database)
Seed tables supporting post-graduate pathways (GATE, CAT, GRE, GMAT, TOEFL, IELTS):
- `paths.csv`: 7 core pathways (`P1` M.Tech India to `P7` MBA abroad).
- `exams.csv`: Exam structures, marking schemes, and conducting bodies.
- `exam_cycles.csv`: Temporal cycles, deadlines, fees, and verification status.
- `institutions.csv`: 26 institutes and universities across India, US, Europe, Singapore.
- `programmes.csv`: PG degrees, specializations, cutoffs, and funding mechanisms.
- `milestones.csv`: 16 academic and preparation milestones (`M1` to `M16`).
- `prep_templates.csv` & `template_phases.csv`: 10 speed-based study templates (12/6/3 months) broken into 48 weekly phases with concrete checkpoints.
- `prep_methods.csv`: Evidence-based study strategies (`PM1` active recall, `PM2` PYQs by topic, `PM3` error log, etc.).
- `resources.csv`: Curated official and open educational resources.
- `Survey.csv` (in `data/raw/higher_studies/`): 35 survey questions across 6 sections (A–F) + 5 senior interview prompts.

