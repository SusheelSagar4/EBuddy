# Data Gaps & Open Ambiguities Register

**Scope:** Formally records missing information, unverified fields, and data discrepancies identified in raw source files for **B.Tech Electrical Engineering** and **B.Tech Metallurgical and Materials Engineering (SMMME)** at IIT Bhubaneswar.  
**Release Constraint:** `make check-data --release` must fail if any placeholder remains unresolved.

---

## 1. High-Severity Blockers

| Issue ID | Entity / Field | Description | Proposed Resolution | Status |
|---|---|---|---|---|
| `ISSUE_PREREQ_EE6L007` | `kb.course_prerequisite`<br>(`EE6L007`) | Prerequisite is listed as `"Measurement and Electronic Instruments"`, which does not exist in the course table. | Team decision: prerequisite set to `EE3L010` (*Measurement and Instrumentation*, the closest course). The official wording is kept as a student-facing note (`data/seed/kb/course_note.csv`). | **RESOLVED**<br>(team decision) |
| `ISSUE_MME_CURR_03` | `kb.course`<br>(`ML4L001`–`ML4L003`) | Semester VII core courses (*Light metals and alloys*, *Elements of electroceramics*, *Polymers and nanocomposites*) clash with 3 Metallurgical electives (*Joining of metals and alloys*, *Solidification of metals and alloys*, *Electrochemical methods in metallurgy*). | Team decision: keep all six courses under separate internal ids (`ML4L001_CORE` / `ML4L001_ELEC`, ...); codes are never treated as unique (lookups resolve a code to every matching course and refuse ambiguous input); students see "The official curriculum uses this code for two different courses. Please confirm with the department." wherever these courses appear. | **ACKNOWLEDGED & OPEN**<br>(department confirmation still needed) |
| `ISSUE_MME_SUSPECT_AMOUNT_045` | `kb.research_project`<br>(`PROJ_MM_SPON_14`) | Suspect project amount: ₹ 0.45 Lakhs for UGC-DAE CSR project. May be travel contingency or print typo for ₹45 L or ₹4.5 L. | Flagged `amount_suspect = true`. Preserved as printed. | **UNRESOLVED** |
| `ISSUE_MME_SUSPECT_AMOUNT_289` | `kb.research_project`<br>(`PROJ_MM_SPON_44`) | Suspect project amount: ₹ 289 Lakhs for DFG Germany project. Likely international consortium funding in Euros rather than direct IIT BBS grant. | Flagged `amount_suspect = true`. Preserved as printed. | **UNRESOLVED** |
| `ISSUE_MME_DUPLICATE_NAB` | `kb.research_project`<br>(`PROJ_MM_SPON_43`) | Duplicate project entry in source catalog: *Improving damping capacity of cast NAB alloys* listed as row 33 and row 43. | Flagged `duplicate_of = 'PROJ_MM_SPON_33'`. Kept distinct to preserve source numbering. | **UNRESOLVED** |
| `ISSUE_MME_PULSATOR_CONFLICT` | `kb.research_project`<br>(`PROJ_MM_SPON_01`) | Conflict on pulsator thickener project: Catalog lists duration and agency as '—'; Faculty profile lists *Ministry of Mines, ₹45 L, 2026–28*. | Alternate values stored in `alt_value` column. | **UNRESOLVED** |
| `ISSUE_MME_WATERMARK_LEGIBILITY` | `kb.research_project`<br>(`PROJ_MM_SPON_02`) | Project title contains watermark bracket artifact: `[Development] of Design...` | Flagged `legibility = 'partial'`. | **ACKNOWLEDGED** |
| `ISSUE_FACULTY_NAME_VARIANTS` | `kb.faculty`<br>(SMMME Faculty) | Name variants between catalog and profiles (e.g. *Partha Sarathi De* vs *Partha S. De*, *Rama Krushna Sabat* vs *R. K. Sabat*). | Profiles used as canonical; variants cataloged. | **ACKNOWLEDGED** |

---

Every discrepancy in section 3 keeps the value listed first in the official source and has a student-facing note in `data/seed/kb/course_note.csv`, shown on the roadmap, the Learn cards and in chat.

## 2. Curriculum Content Gaps

| Issue ID | Scope | Impact | Status |
|---|---|---|---|
| `GAP_SYLLABUS_TEXT` | Detailed syllabus topics & learning objectives | `syllabus_text = NULL` on courses; derived modules set to `is_placeholder = true`. | User to provide syllabus text / course booklet. |
| `GAP_MME_SEM_I_II` | MME Curriculum Sem I–II | Sem I–II is simply missing from SMMME raw documents. Source PDF covers Sem III–VIII only. | **Sem I–II is simply missing.** Zero courses, completions, or common first-year curriculum assumptions made. Exactly 0 rows exist in `kb.course_offering` and `kb.programme_requirement` for MME in Semesters I–II. Official curriculum document for Sem I–II is required from SMMME. |
| `GAP_ACADEMIC_RULES` | Official UG Regulations document | Credit caps, minor eligibility, and backlog policies currently use initial baseline rules. | User to provide UG ordinances document. |
| `GAP_CURRENCY_2016_17` | Academic Batch Currency | Raw curriculum reflects 2016-17 batch. | Flagged with warning label in UI and reports. |

---

## 3. Discrepancies Recorded from Source Curriculum Sheets

### Electrical Engineering (17 Items)
| Item # | Course Code / Title | Source Discrepancy | Treatment Applied |
|---|---|---|---|
| 1 | `EE2L003` Electric Machines | Table gives `EE2L003`; syllabus header gives `EE3L001`. | `EE2L003` used from semester table. |
| 2 | `EE3L003` Control Systems | Table gives 4 credits (3-1-0); syllabus header gives 3 credits. | 4 credits used from semester table. |
| 3 | `EE4L005` Digital Control Systems | Table gives 3-0-0 (3 credits); syllabus header gives 3-1-0 (4 credits). | 3 credits used from semester table. |
| 4 | `EE4L006` Renewable Energy Systems | Table gives 3-0-0 (3 credits); syllabus header gives 3-1-0 (4 credits). | 3 credits used from semester table. |
| 5 | `EC6L002` Image & Video Processing | Elective pool gives 3-1-0 (4 credits); syllabus header gives 3-0-0 (3 credits). | 4 credits used from elective table. |
| 6 | `EC4L003` VLSI Design | Listed as *"VLSI Design"* in table; *"Introduction to VLSI Design"* in syllabus. | *"VLSI Design"* used. |
| 7 | `EC6L023` Adaptive Signal Processing | Listed as *"Adaptive Signal Processing"* in table; *"Adaptive Digital Signal Processing"* in syllabus. | *"Adaptive Signal Processing"* used. |
| 8 | `EE2L004`, `EE3L009` | Course codes blank in syllabus section. | Codes resolved from lateral option list. |
| 9 | `EC6L012` Optical Communication | Listed in elective table with no syllabus or books. | Marked with `is_placeholder = false`, syllabus NULL. |
| 10 | `EC2L005`, `EC6L004` | Syllabi provided but absent from semester table. | Moved to `in_semester_table = false` in EE (activated in MME). |

### Metallurgical and Materials Engineering (12 Items)
| Item # | Topic | Source Discrepancy | Treatment Applied |
|---|---|---|---|
| 1 | Scope of PDF | Covers Sem III–VIII only; no syllabi/prereqs/books in source PDF. | Shown as "—". Basic Electronics books imported from EE PDF. |
| 2 | Basic Electronics (`EC2L005`) | Appears in EE curriculum with syllabus. | Prerequisite and books imported from EE curriculum. |
| 3 | Code Clash (`ML4L001`–`003`) | Duplicate codes between Sem VII core and electives. | Disambiguated in DB with suffix `E`; flagged high severity. |
| 4 | Environmental Science Code | Source prints both `ID2L003` and `ID3L003`. | `ID2L003` used (matches EE curriculum). |
| 5 | Elective Placeholders | Sem VII & VIII electives use placeholder `ML4LXXX`. | Single pool of 15 electives mapped to 5 slots via `slot_option`. |
| 6 | Lateral Slots | 3 courses in lateral list not mapped to individual slots. | Mapped to `MM_LATERAL_1`..`3` via `slot_option`. |
| 7 | Breadth / Lateral rows | Credits and contact hours given as "3 / 4". | Handled as credit range 3.0–4.0 in `programme_requirement`. |
| 8 | Mineral processing plant design | Lateral `ML3L012` and elective `ML4L013` have near-identical titles. | Both preserved under their respective codes. |
| 9 | Projects, seminar, training | Source gives 0 contact hours for non-zero LTP. | Preserved as printed. |
| 10 | Totals | Semester totals verified against rows. Total programme credit not stated. | Baseline set to 180 credits. |
| 11 | Course Type column | Elective groups given as headings. | Mapped to core, lateral, elective. |
| 12 | Legend | "—" indicates missing in source. | Handled as NULL / unverified. |
