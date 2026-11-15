# B.Tech UPSC CSE Preparation Roadmap Specification (`btech_upsc`)

This document is the complete, implementation-ready product and full-stack UX specification for integrating the `btech_upsc` persona (`GOAL_UPSC_CSE`) into the `EBuddy` deterministic academic planning engine at IIT Bhubaneswar. It defines the recommendation rules, multi-semester timeline divisions, curriculum slot wiring, resource allocation, and frontend screen bindings for B.Tech Electrical Engineering (`BTECH_EE`) and B.Tech Metallurgical & Materials Engineering (`BTECH_MME`) students across Semesters 1 through 8.

---

## Section 1: End-to-End Suggestion & Personalization Flow (Engine -> UI)

### 1.1 Architectural Flow: Student Inputs to Personalized Roadmap

EBuddy personalizes the UPSC CSE preparation roadmap through a deterministic, air-gapped pipeline driven by Agent 1 (Roadmap Planner) with single-writer guarantees. The engine evaluates student parameters without invoking external networks or stochastic language models, deriving all plans directly from institutional curriculum tables and verified domain facts.

```
+-----------------------------------------------------------------------------------------------+
|                                      STUDENT INPUT PROFILE                                    |
|  - Programme: BTECH_EE / BTECH_MM                     - Date of Birth (DOB) -> Age Check     |
|  - Current Semester: 1 through 8                      - CGPA, Drop Last Sem, Active Backlogs  |
|  - Admission Year: -> Track Resolution (NEP vs Pre)  - Available Study Hours: 6 to 25 hrs/wk  |
+-----------------------------------------------------------------------------------------------+
                                                |
                                                v
+-----------------------------------------------------------------------------------------------+
|                                5-ITEM BASELINE DIAGNOSTIC QUIZ                                 |
|  - SKILL_UPSC_GS2_POLITY_GOVERNANCE_IR (Items P01-P15, difficulty: [30.0, 70.0])              |
|  - SKILL_UPSC_CSAT (Items C01-C15, difficulty: [30.0, 70.0])                                   |
|  - SKILL_UPSC_GS3_ECONOMY (Items E01-E15, difficulty: [30.0, 70.0])                           |
+-----------------------------------------------------------------------------------------------+
                                                |
                                                v
+-----------------------------------------------------------------------------------------------+
|                               PREP TEMPLATE SELECTION (prep_templates_upsc.csv)               |
|  - Sem 1-4 (>= 24 mo): UPSC-24 (10 hrs/wk min; 6 sequential phases; NCERT -> Mocks)          |
|  - Sem 5-6 (>= 12 mo): UPSC-12 (15 hrs/wk min; 5 compressed phases; Static Basics -> Mocks)  |
|  - Sem 7-8 (< 12 mo):  UPSC-6  (20 hrs/wk min; conditional via Rule R8; Sprint -> Clash Taper)|
+-----------------------------------------------------------------------------------------------+
                                                |
                                                v
+-----------------------------------------------------------------------------------------------+
|                            DETERMINISTIC POLICY EVALUATOR (policy.py: R1-R10)                 |
|  - R1: Workload Overload (Pause Optional & Static, +1 wk shift, preserve 45m CA + 2 ans/day) |
|  - R2: CGPA Guard (Cap 6h/wk or 3h/wk in Sem1-2; block Summer & Mock phases; show Fallback)   |
|  - R3: Optional Gate (Force lock-in by Sem 5 for EE / Sem 6 for MME; block optional skills)   |
|  - R4: Baseline Gate (Force NCERT baseline if < 80% completion in Sem >= 3)                   |
|  - R5: CSAT Remediation (+4h/wk CSAT block, cap answers to 2/wk if CSAT < 80 within 16 wks)  |
|  - R6: Placement Interplay (Sem 7 floor 6h/wk; post-offer: 20h/wk; unplaced: defer attempt)   |
|  - R7: Attempt Decision (Sem 8 readiness: static >= 80% + mock score >= cutoff; F04 warning)  |
|  - R8: Late Start (Sem >= 6 static < 50%: default defer; if >= 15h/wk: compressed sprint)    |
|  - R9: Age Eligibility (Must be >= 21 on Aug 1 of exam year per F01; calculate earliest year) |
|  - R10: Sem 8 Exam Clash (2027: New topics end 22 Apr; 10h/wk cap to 19 May Viva; Prelims 23) |
+-----------------------------------------------------------------------------------------------+
                                                |
                                                v
+-----------------------------------------------------------------------------------------------+
|                             SYNTHESIZED ROADMAP JSON (Plan.json)                              |
|  - Validated PlanItems: Milestones, Resources, Curriculum Slot Overlaps, Rule Banners         |
+-----------------------------------------------------------------------------------------------+
```

### 1.2 Step-by-Step Personalization Mechanics

1. **Curriculum Track Resolution:**
   - Admitted in academic year 2025–26 or later $\rightarrow$ Assigned to the **NEP Curriculum Track**.
   - Admitted prior to 2025–26 (e.g. 2023, 2024) $\rightarrow$ Assigned to the **2016–17 Pre-NEP Curriculum Track** (`app/personas/btech_upsc/policy.py:get_track_for_admission_year`).
   - Track resolution determines exact credit loads and mandatory laboratory densities from `data/raw/institute/institute_curriculum_slots.csv`.

2. **Age Eligibility & Attempt Year Calculation (`R9`):**
   - Candidate Date of Birth (DOB) is compared against 1 August of the target UPSC CSE exam year (`facts.csv:F01`).
   - If candidate age on 1 August is $< 21$, the target year is hard-blocked. The engine computes:
     $$\text{earliest\_attempt\_year} = \text{target\_year} + (21 - \text{age})$$
   - Maximum age limit is verified against `facts.csv:F02` (32 years for General category, +5 years for SC/ST, +3 years for OBC, +10 years for PwBD).

3. **Academic Health & Capacity Floor (`R2`):**
   - The student's current CGPA is evaluated against the institutional guardrail:
     * Hard floor: $\text{CGPA} < 6.50$ (placeholder pending official CDC placement data `facts.csv:F22`).
     * Drop guard: $\Delta \text{CGPA} \ge 0.30$ drop in the prior semester.
     * Backlog guard: Count of active backlogs $> 0$.
   - When triggered, UPSC weekly study time is capped at **6.0 hours/week** (reduced to **3.0 hours/week** in Semesters 1–2).
   - Milestone progression into `upsc_summer_intensive_y3` and `upsc_prelims_mock_phase` is blocked until academic standing recovers.
   - The UI surfaces the departmental fallback card: `GOAL_EE_CORE_POWER` for Electrical Engineering or `persona_mme_core_stub` for Metallurgical Engineering.

4. **Diagnostic Benchmarking (`diagnostic.yaml` & `diagnostic_items.csv`):**
   - The student completes a 5-question baseline assessment sampled across:
     * `SKILL_UPSC_GS2_POLITY_GOVERNANCE_IR` (Items P01–P15)
     * `SKILL_UPSC_CSAT` (Items C01–C15)
     * `SKILL_UPSC_GS3_ECONOMY` (Items E01–E15)
   - Questions range in calibrated difficulty from 30.0 to 70.0.
   - Scoring below 40% on Polity or Economy flags early foundational weakness and locks entry into advanced static textbooks until NCERT modules are verified.
   - Scoring below 60% on CSAT items flags early CSAT risk, scheduling foundational numeracy resources (`RS23`) starting in Semester 3.

5. **Template Selection (`prep_templates_upsc.csv`):**
   - **Semesters 1–4 (24+ Months Runway):** Selected for `UPSC-24` (Speed: 24 months, minimum 10 hrs/week). Phased progression from NCERTs to full prelims simulation.
   - **Semesters 5–6 (12–18 Months Runway):** Selected for `UPSC-12` (Speed: 12 months, minimum 15 hrs/week). Compressed static pass 1 and accelerated optional start.
   - **Semesters 7–8 (< 12 Months Runway):** Evaluated under Rule `R8`. If static coverage $< 50\%$, the engine defaults to recommending an attempt after graduation. If the student explicitly insists on attempting CSE in Semester 8 and commits $\ge 15\text{ hrs/week}$, template `UPSC-6` (Speed: 6 months, minimum 20 hrs/week) is activated.

### 1.3 Dynamic Rule Enforcement (`R1`–`R10`)

| Rule ID | Rule Name | Trigger Condition (`if`) | Engine Action & UI Alteration (`then`) |
|---|---|---|---|
| **R1** | `workload_overload` | `sem in {6, 7}` AND (`placement_season_active` OR `btp_deadline_within_21d` OR `end_sem_within_14d` OR `weekly_hours < 10`) | Pauses `SKILL_UPSC_OPTIONAL` tasks and new static chapters. Preserves 45 min/day current affairs streak and 2 answers/day (1 answer/day if hours $< 6$). Shifts milestone deadlines by +1 week without marking milestones failed. |
| **R2** | `cgpa_guard` | `cgpa < 6.50` OR `cgpa_drop_last_sem >= 0.30` OR `active_backlog > 0` | Caps weekly UPSC hours to 6 hrs/wk (3 hrs/wk in Sem 1–2). Blocks `upsc_summer_intensive_y3` and `upsc_prelims_mock_phase`. Displays departmental fallback banner (`GOAL_EE_CORE_POWER` or `persona_mme_core_stub`). Displays `"Not confirmed yet"` for placement cutoff status per Fact `F22`. |
| **R3** | `optional_gate` | `sem >= 5` (EE) or `sem >= 6` (MME) AND `optional == undecided` | Blocks all `SKILL_UPSC_OPTIONAL` roadmap tasks. Forces milestone `upsc_optional_lock_in`. EE UI displays Electrical Engineering as the primary recommendation (bachelor's level per Fact `F09`). MME UI displays candidate optionals with mandatory `"SME-pending review"` warning (`sme_reviewed=FALSE`). |
| **R4** | `baseline_gate` | `sem >= 3` AND `ncert_completion < 0.80` (80%) | Blocks `upsc_static_pass1` and all subsequent static reading milestones. Forces milestone `upsc_ncert_baseline`. |
| **R5** | `csat_remediation` | `csat_avg_last3 < 80` (out of 200) AND `weeks_to_prelims <= 16` | Automatically schedules a mandatory 4 hrs/wk CSAT numerical reasoning block (`RS23`). Reduces Mains answer writing quota to 2 answers per week. Target CSAT benchmark set to 90/200 (Fact `F05`). |
| **R6** | `placement_interplay` | `sem == 7` AND `placement_registered == true` | During active placement season: Enforces floor of 6 hrs/wk (45 min daily CA + 1 answer/day). Post-placement outcome: If offer secured AND CGPA $\ge 6.50$, Sem 8 target set to 20 hrs/wk and final-year attempt permitted; if unplaced, Sem 8 target set to 25 hrs/wk and engine recommends deferring first attempt to after graduation. |
| **R7** | `attempt_decision` | `sem == 8` AND (`static_pass1_completion < 0.80` OR `gs_mock_avg < cutoff_plus_buffer - 15` after 8 full mocks) | Buffer marks = 20. Cutoff baseline requires at least 2 verified General GS-I cutoffs in `cutoffs.csv`. Because only CSE-2025 (92.66) is `verified=TRUE` while 2024 and 2023 are `verified=FALSE`, the engine displays `"Not confirmed yet"` for the cutoff baseline. Recommends deferring first attempt (student confirms). Prominently displays Fact `F04`: *"An attempt counts when candidate appears in any one Prelims paper."* |
| **R8** | `late_start` | `sem >= 6` AND `static_pass1_completion < 0.50` (50%) | Default recommendation: Attempt after graduation. If student insists on Semester 8 attempt AND commits $\ge 15\text{ hrs/week}$, inserts `upsc_compressed_static_sprint` (12 weeks, 15+ hrs/wk). If weekly hours $< 15$, blocks the sprint and mandates deferral. |
| **R9** | `age_eligibility` | $\text{age\_on\_1\_august}(\text{target\_year}) < 21$ per Fact `F01` | Hard-blocks target attempt year. Calculates earliest eligible exam cycle based on minimum age 21 on 1 August. Validates against upper age limit of 32 for General candidates per Fact `F02`. |
| **R10** | `sem8_exam_clash` | `sem == 8` AND `target_attempt_year == current_year` (2027) | Enforces academic protection window from institute calendar and Fact `F11`: All new syllabus topics end by `2027-04-22` (14 days prior to Spring end-sem start on `2027-05-06`). From `2027-04-22` to B.Tech Project viva on `2027-05-19`, UPSC hours capped at 10 hrs/wk (daily CA + 1 timed paper/wk + revision). From `2027-05-20` to `2027-05-22`: pure revision only. Prelims on `2027-05-23`. Result published `2027-05-25` (2 days after Prelims). |

---

## Section 2: Phase-Wise Division of the UPSC Roadmap

### 2.1 Sequential 4-Phase Architecture

EBuddy structures the B.Tech UPSC journey into 4 sequential Phases that synchronize the 10 domain milestones (`milestones.csv`) and template phases (`prep_template_phases_upsc.csv`) with IIT Bhubaneswar's semestral academic rhythm:

1. **Phase 1: Orientation, Newspaper Habit & NCERT Foundation (Semesters 1–3)**
   - Establishes syllabus familiarity, 60-day national daily newspaper reading habit, and secondary school NCERT mastery across History, Geography, Polity, and Economy.
2. **Phase 2: Core Static Pass 1, Current Affairs System & Optional Subject Lock-In (Semesters 4–5)**
   - Covers standard foundational reference texts (Polity, Modern History, Art & Culture, Economy, Environment), operationalizes monthly current affairs compilations, and finalizes the Optional Subject.
3. **Phase 3: Answer Writing, Ethics/Essay & Post-Sem 6 Summer Intensive (Semester 6 + Summer)**
   - Develops Mains answer writing speed, covers GS-4 Ethics case studies and essay structures, and executes a 200-hour post-Sem 6 summer intensive (adjusted to 120 hours if concurrent with mandatory industrial training).
4. **Phase 4: Revision Pass 2, Prelims Mock Sprint & Attempt Decision / Late-Starter Sprint (Semesters 7–8)**
   - Executes second static revision pass, timed sectional tests, 25 full-length GS-I Prelims mocks, and 10 CSAT mocks; enforces the Rule `R7` attempt decision and Rule `R10` exam-clash freeze window.

### 2.2 Phase-Wise Specification Table

| Phase Name | Template Phase Share (%) | Target Semesters | Included Milestones (`milestone_slug`) | Target Skills | Entry Gate / Unlock Condition | Concrete Verification Metric | Active Policy Guardrails |
|---|---|---|---|---|---|---|---|
| **Phase 1: Orientation, Newspaper Habit & NCERT Foundation** | **UPSC-24:** 15%<br>*(Phase 1: 15%)* | Sem 1–3 | `upsc_orientation_habit`<br>`upsc_ncert_baseline` | `SKILL_UPSC_CURRENT_AFFAIRS`<br>`SKILL_UPSC_GS1_HISTORY_CULTURE`<br>`SKILL_UPSC_GS1_GEOGRAPHY_SOCIETY`<br>`SKILL_UPSC_GS2_POLITY_GOVERNANCE_IR`<br>`SKILL_UPSC_GS3_ECONOMY` | Onboarding profile complete; Age $\ge 21$ projection verified (`R9`) | 60-day newspaper streak at 30+ min/day (max 3 missed days); 1-page syllabus map; 10-year Prelims topic sheet; $\ge 90\%$ NCERT chapters read with 1-page summary notes (`F17`) | `R2` (Cap 3h/wk in Sem 1-2)<br>`R4` (NCERT $\ge 80\%$ required by Sem 3)<br>`R9` (Min age 21 check) |
| **Phase 2: Core Static Pass 1, Current Affairs System & Optional Lock-In** | **UPSC-24:** 40%<br>*(Phase 2: 25% + Phase 3: 15%)*<br>**UPSC-12:** 40%<br>*(Phase 1: 30% + Phase 2: 10%)* | Sem 4–5 | `upsc_static_pass1`<br>`upsc_optional_lock_in`<br>`upsc_current_affairs_system` | `SKILL_UPSC_GS1_HISTORY_CULTURE`<br>`SKILL_UPSC_GS1_GEOGRAPHY_SOCIETY`<br>`SKILL_UPSC_GS2_POLITY_GOVERNANCE_IR`<br>`SKILL_UPSC_GS3_ECONOMY`<br>`SKILL_UPSC_GS3_STI_ENV_SECURITY`<br>`SKILL_UPSC_OPTIONAL`<br>`SKILL_UPSC_CURRENT_AFFAIRS` | Phase 1 verified; NCERT completion $\ge 80\%$ (`R4`); CGPA $\ge 6.50$ (`R2`) | 6 core books read once (Polity, Modern History, Art & Culture, Economy, Geography, Environment); $\ge 20$ PYQs per subject at $\ge 60\%$ accuracy; 90-day CA streak at 45+ min/day; $\ge 3$ monthly compilations mapped; 1 optional logged with $\ge 3$ PYQ papers analyzed | `R1` (Workload monitor)<br>`R2` (CGPA $\ge 6.50$ floor)<br>`R3` (Optional locked by Sem 5 EE / Sem 6 MME)<br>`R4` (Baseline gate) |
| **Phase 3: Answer Writing, Ethics/Essay & Summer Intensive** | **UPSC-24:** 20%<br>*(Phase 4: 20%)*<br>**UPSC-12:** 10%<br>*(Phase 4: 10%)* | Sem 6 + Summer | `upsc_answer_writing_foundation`<br>`upsc_summer_intensive_y3` | `SKILL_UPSC_ANSWER_WRITING`<br>`SKILL_UPSC_GS4_ETHICS_CASES`<br>`SKILL_UPSC_ESSAY`<br>`SKILL_UPSC_CSAT`<br>`SKILL_UPSC_OPTIONAL`<br>`SKILL_UPSC_PRELIMS_TESTCRAFT` | Static Pass 1 complete; Optional Subject locked in (`R3`); CGPA $\ge 6.50$ (`R2`) | 30 timed answers ($\ge 5$ per GS paper) rated $\ge 3/5$ on rubric; 5 ethics cases; 2 essays; Summer: $\ge 200$ logged hours ($\ge 120$ hrs if on industrial training); 10 timed CSAT papers averaging $\ge 90/200$; Optional Paper 1 first pass | `R1` (Sem 6 overload pause)<br>`R2` (Blocks summer intensive if CGPA $< 6.5$)<br>`R5` (CSAT check) |
| **Phase 4: Revision Pass 2, Prelims Mock Sprint & Attempt Decision** | **UPSC-24:** 25%<br>*(Phase 5: 10% + Phase 6: 15%)*<br>**UPSC-12:** 50%<br>*(Phase 3: 25% + Phase 5: 25%)*<br>**UPSC-6:** 100%<br>*(Phase 1: 40% + Phase 2: 20% + Phase 3: 30% + Phase 4: 10%)* | Sem 7–8 | `upsc_revision_pass2_sectionals`<br>`upsc_prelims_mock_phase`<br>*(Conditional:)*<br>`upsc_compressed_static_sprint` | `SKILL_UPSC_GS2_POLITY_GOVERNANCE_IR`<br>`SKILL_UPSC_GS3_ECONOMY`<br>`SKILL_UPSC_CURRENT_AFFAIRS`<br>`SKILL_UPSC_ANSWER_WRITING`<br>`SKILL_UPSC_PRELIMS_TESTCRAFT`<br>`SKILL_UPSC_CSAT` | Summer Intensive complete (or Sprint qualified via `R8`); CGPA $\ge 6.50$ (`R2`) | Pass 2 of core static subjects; 20 sectional tests at $\ge 60\%$; 25 full-length GS-I mocks & 10 CSAT mocks logged with error analysis; GS mock average $\ge \text{cutoff} + \text{buffer}$; CSAT average $\ge 90/200$; Late starters: 12-week sprint at $\ge 15$ hrs/wk | `R1` (Sem 7 overload pause)<br>`R5` (CSAT remediation if $< 80$)<br>`R6` (Placement interplay)<br>`R7` (Attempt decision)<br>`R8` (Late-start deferral)<br>`R10` (Sem 8 exam clash freeze) |

### 2.3 Mathematical Proof of Phase Share Integrity

Per `prep_template_phases_upsc.csv`, all phase shares sum strictly to **100%**:

- **Template `UPSC-24`:**
  $$\sum = 15\% \text{ (Phase 1)} + 25\% \text{ (Phase 2)} + 15\% \text{ (Phase 3)} + 20\% \text{ (Phase 4)} + 10\% \text{ (Phase 5)} + 15\% \text{ (Phase 6)} = 100\%$$
- **Template `UPSC-12`:**
  $$\sum = 30\% \text{ (Phase 1)} + 10\% \text{ (Phase 2)} + 25\% \text{ (Phase 3)} + 10\% \text{ (Phase 4)} + 25\% \text{ (Phase 5)} = 100\%$$
- **Template `UPSC-6` (Compressed Sprint):**
  $$\sum = 40\% \text{ (Phase 1)} + 20\% \text{ (Phase 2)} + 30\% \text{ (Phase 3)} + 10\% \text{ (Phase 4)} = 100\%$$

---

## Section 3: Resource & Optional Subject Recommendation Logic

### 3.1 Diagnostic Mastery to Resource Allocation Logic

Resource recommendations are keyed to the student's mastery level ($\theta$) across the 12 UPSC skills (`skills.csv`) and their active milestone (`resources.csv`):

- **Novice / Beginner ($\theta < 40.0$):** Sourced from `foundation` tier materials. Focuses on government portals, official exam notices (`RS01`), and foundational NCERT texts (`RS03`, `RS23`).
- **Competent ($40.0 \le \theta < 70.0$):** Sourced from `core` tier materials. Assigns standard core reference texts (`RS04`–`RS08`, `RS17`), daily official news wires (`RS10`, `RS11`), and university NPTEL courses (`RS19`, `RS20`, `RS22`).
- **Proficient / Advanced ($\theta \ge 70.0$):** Sourced from `advanced` tier materials. Assigns official policy documents (`RS09`), administrative reform reports (`RS12`), specialized energy and economic policy courses (`RS21`, `RS25`), and timed test series simulations (`RS02`, `RS15`).

### 3.2 Optional Subject Selection: `BTECH_EE` vs `BTECH_MME`

The engine evaluates optional subjects using `data/raw/higher_studies/upsc/optional_catalog.csv` and institutional curriculum slots (`data/raw/institute/institute_curriculum_slots.csv`):

```
+--------------------------------------------------------------------------------------------------+
|                                    OPTIONAL SUBJECT OVERVIEW                                     |
+------------------------------------+-------------------------------------------------------------+
| B.Tech Electrical Engineering      | STRONG OVERLAP: Electrical Engineering Optional             |
|                                    | - Bachelor's degree level syllabus (Fact F09).             |
|                                    | - 12+ Core courses map directly to Paper 1 and Paper 2.     |
|                                    | - Supported by Breadth Economics electives (Fact F20).       |
+------------------------------------+-------------------------------------------------------------+
| B.Tech Metallurgical & Materials   | NO METALLURGY OPTIONAL IN UPSC CSE (Fact F08)               |
|                                    | Candidates must choose non-metallurgical optionals:         |
|                                    | - Mechanical Engineering: Partial overlap (ME1L002/P001)    |
|                                    | - Geology: Earth-science overlap (SME Review Pending)       |
|                                    | - Chemistry / Physics / Maths: Partial 1st-year overlap     |
|                                    | - Humanities: Economics / Philosophy / Psychology breadth   |
|                                    | * MANDATORY UI BADGE: "SME Review Pending"                  |
+------------------------------------+-------------------------------------------------------------+
```

1. **B.Tech Electrical Engineering (`BTECH_EE`):**
   - **Verdict:** `STRONG` curriculum overlap.
   - **Curriculum Alignment:** UPSC CSE offers *Electrical Engineering* as a formal optional subject (`facts.csv:F08`). Per Fact `F09`, engineering optionals are pegged to the bachelor's degree level.
   - **Course Mapping:** Core courses provide direct coverage:
     * Paper 1: `EE2L001` (Network Theory), `EE3L011` (EM Field Theory), `EE3L003` (Control Systems), `EE3L004` (Power Electronics), `EE3L010` (Measurement & Instrumentation).
     * Paper 2: `EC2L006` (Digital Electronics & Microprocessors), `EC3L003` (Digital Signal Processing), `EE3L007` (Power Transmission & Distribution), `EE2L003` (Electric Machines).
   - **Breadth Support:** 7 Economics breadth electives provide humanities foundations (`facts.csv:F20`).
   - **Policy Directive:** Locked in by Semester 5 under Rule `R3`.

2. **B.Tech Metallurgical & Materials Engineering (`BTECH_MME` / `BTECH_MM`):**
   - **Verdict:** `NONE` for departmental subject; `PARTIAL` / `UNKNOWN` for candidate alternatives.
   - **Curriculum Constraint:** UPSC CSE does **not** offer Metallurgical Engineering as an optional subject (`facts.csv:F08`).
   - **Candidate Options:**
     * *Mechanical Engineering:* Partial overlap from first-year mechanics (`ME1L001`, `ME1L002`) and materials processing courses.
     * *Geology:* Potential overlap with mineralogy and earth science; requires SME mapping (`data_requests.md:D09`).
     * *Chemistry / Physics / Mathematics:* Partial coverage from common first-year foundational coursework.
     * *Humanities Options (Economics, Philosophy, Psychology):* Supported by institute breadth courses (`facts.csv:F20`).
   - **Policy Directive:** Locked in by Semester 6 under Rule `R3`. All MME candidate options carry `sme_reviewed=FALSE` and must display the `"SME-pending review"` warning.

### 3.3 Complete Phase-to-Resource Mapping Table (`resources.csv`)

In strict accordance with Anti-Hallucination Rule 2, any resource with `verified=FALSE` displays the disclaimer badge: `"Not confirmed yet — confirm edition with mentor"`.

| Phase | Skill | Resource ID & Title | Provider | Type | Verified Status | UI Badge / Disclaimer |
|---|---|---|---|---|---|---|
| **Phase 1** | `SKILL_UPSC_ANSWER_WRITING` | `RS01`: UPSC CSE Notification (CSE-2026) | UPSC | portal | **TRUE** | `Verified` |
| **Phase 1** | `SKILL_UPSC_GS1_HISTORY_CULTURE` | `RS03`: NCERT Textbooks (e-books) | NCERT | portal | **TRUE** | `Verified` *(Chapter list pending mentor approval D03)* |
| **Phase 1** | `SKILL_UPSC_CURRENT_AFFAIRS` | `RS16`: Newspaper (The Hindu / Indian Express) | Publisher | portal | **FALSE** | `Not confirmed yet — confirm edition with mentor` |
| **Phase 2** | `SKILL_UPSC_GS2_POLITY_GOVERNANCE_IR` | `RS04`: Indian Polity | M. Laxmikanth (McGraw Hill) | book | **FALSE** | `Not confirmed yet — confirm edition with mentor` |
| **Phase 2** | `SKILL_UPSC_GS1_HISTORY_CULTURE` | `RS05`: A Brief History of Modern India | Rajiv Ahir (Spectrum) | book | **FALSE** | `Not confirmed yet — confirm edition with mentor` |
| **Phase 2** | `SKILL_UPSC_GS1_HISTORY_CULTURE` | `RS06`: Indian Art and Culture | Nitin Singhania (McGraw Hill) | book | **FALSE** | `Not confirmed yet — confirm edition with mentor` |
| **Phase 2** | `SKILL_UPSC_GS3_ECONOMY` | `RS07`: Indian Economy | Ramesh Singh (McGraw Hill) | book | **FALSE** | `Not confirmed yet — confirm edition with mentor` |
| **Phase 2** | `SKILL_UPSC_GS1_GEOGRAPHY_SOCIETY` | `RS08`: Certificate Physical & Human Geography | Goh Cheng Leong (OUP) | book | **FALSE** | `Not confirmed yet — confirm edition with mentor` |
| **Phase 2** | `SKILL_UPSC_CURRENT_AFFAIRS` | `RS10`: Press Information Bureau (PIB) Releases | Govt. of India | portal | **TRUE** | `Verified` |
| **Phase 2** | `SKILL_UPSC_GS2_POLITY_GOVERNANCE_IR` | `RS11`: PRS Legislative Research Summaries | PRS India | portal | **TRUE** | `Verified` |
| **Phase 2** | `SKILL_UPSC_OPTIONAL` | `RS14`: Electrical Engineering Optional Syllabus | UPSC | portal | **TRUE** | `Verified` |
| **Phase 2** | `SKILL_UPSC_GS3_STI_ENV_SECURITY` | `RS17`: Environment Book / Notes | Shankar IAS Academy | book | **FALSE** | `Not confirmed yet — confirm edition with mentor` |
| **Phase 2** | `SKILL_UPSC_GS2_POLITY_GOVERNANCE_IR` | `RS20`: Fundamentals of Public Policy & Analysis | NPTEL / IIT Roorkee | course | **TRUE** | `Verified` |
| **Phase 2** | `SKILL_UPSC_GS3_ECONOMY` | `RS22`: Indian Economy: Contemporary Perspectives | NPTEL / IIT Kanpur | course | **TRUE** | `Verified` |
| **Phase 2** | `SKILL_UPSC_GS3_STI_ENV_SECURITY` | `RS25`: Energy Economics and Policy | NPTEL / IIT Mandi | course | **TRUE** | `Verified` |
| **Phase 3** | `SKILL_UPSC_GS4_ETHICS_CASES` | `RS12`: Second ARC Report on Ethics in Governance | DARPG | portal | **FALSE** | `Not confirmed yet — confirm edition with mentor` |
| **Phase 3** | `SKILL_UPSC_GS4_ETHICS_CASES` | `RS18`: Ethics, Integrity and Aptitude Textbook | Mentor Selected | book | **FALSE** | `Not confirmed yet — confirm edition with mentor` |
| **Phase 3** | `SKILL_UPSC_GS4_ETHICS_CASES` | `RS19`: Moral Thinking: Introduction to Values & Ethics | NPTEL / IIT Kanpur | course | **TRUE** | `Verified` |
| **Phase 3** | `SKILL_UPSC_CSAT` | `RS23`: NCERT Mathematics Classes 6–10 | NCERT | book | **TRUE** | `Verified` |
| **Phase 3** | `SKILL_UPSC_ESSAY` | `RS24`: UPSC Previous Essay Papers | UPSC | portal | **FALSE** | `Not confirmed yet — confirm edition with mentor` |
| **Phase 4** | `SKILL_UPSC_PRELIMS_TESTCRAFT` | `RS02`: UPSC Official Cut-off Marks Page | UPSC | portal | **TRUE** | `Verified` |
| **Phase 4** | `SKILL_UPSC_GS3_ECONOMY` | `RS09`: Economic Survey & Union Budget Documents | Ministry of Finance | portal | **TRUE** | `Verified` |
| **Phase 4** | `SKILL_UPSC_PRELIMS_TESTCRAFT` | `RS13`: Previous Year Question Papers | UPSC | portal | **FALSE** | `Not confirmed yet — confirm edition with mentor` |
| **Phase 4** | `SKILL_UPSC_PRELIMS_TESTCRAFT` | `RS15`: Commercial Prelims Test Series | Vision / Forum / Insights | test_series | **FALSE** | `Not confirmed yet — confirm edition with mentor` |
| **Phase 4** | `SKILL_UPSC_ECONOMY` | `RS21`: Economics of Public Policy | NPTEL / IISER Mohali | course | **TRUE** | `Verified` |

---

## Section 4: Screen-by-Screen Frontend Walkthrough (What the User Sees)

### 4.1 Onboarding & Diagnostic Screen (`onboarding.js` & `diagnostic.js`)

1. **Onboarding Form (`web/src/screens/onboarding.js`):**
   - **Student ID & Branch Select:** Roll number entered (`24EE01042`); dropdown selects `BTECH_EE` or `BTECH_MM`.
   - **Academic Parameters:** Semester (1–8) and current CGPA (with soft floor 7.00 and hard floor 6.50 warnings).
   - **DOB Input (`R9` Age Check):** Date picker prompts for birth date. The engine dynamically checks age as of August 1 of the projected attempt year (`facts.csv:F01`).
   - **Target Career Track:** Goal dropdown selects `GOAL_UPSC_CSE` (Civil Services Examination).
   - **Weekly Hours Slider:** Allocates 6 to 25 hours/week. If CGPA $< 6.50$, slider is locked to max 6 hours/week by Rule `R2`.

2. **Diagnostic Quiz View (`web/src/screens/diagnostic.js`):**
   - Renders a 5-item adaptive assessment sampled from `diagnostic_items.csv` covering Polity, CSAT, and Economy.
   - Question cards render item stems, 4 radio options (`A`, `B`, `C`, `D`), and metadata badges:
     * Badge 1: Item ID (`P04`)
     * Badge 2: Skill (`GS2_POLITY_GOVERNANCE_IR`)
     * Badge 3: Estimated Difficulty (`40.0`)
   - Submission calculates baseline mastery $\theta$, logs error entries, and seamlessly transitions the student to `#plan`.

### 4.2 Phase-Wise Roadmap Screen (`web/src/screens/plan.js`)

1. **Phase Containers & Progress Bars:**
   - 4 collapsible phase containers matching the template breakdown.
   - Visual progress bars reflect completed milestones and verified hours against the template allocation (`prep_template_phases_upsc.csv`).

2. **Semester Swimlanes & Lab Density Badges:**
   - Integrates `institute_curriculum_slots.csv` to flag institutional workload:
     * **Semesters 4, 5, 6:** Tagged with `HEAVY LAB SEMESTER (2-3 Laboratories)` (e.g. `EE2P003`, `EC2P006`, `EE3P004`, `EE3P005`). UPSC weekly hours are throttled.
     * **Semesters 7, 8:** Tagged with `LIGHT LAB SEMESTER (0-1 Laboratory)`. Accommodates mock test series and intensive revision.

3. **Optional Subject Comparison Card (`R3`):**
   - For `BTECH_EE`: Highlights `Electrical Engineering` with a bright green `STRONG OVERLAP` badge and list of 12 overlapping core courses.
   - For `BTECH_MME`: Highlights candidate optionals (Mechanical, Geology, Economics) with an amber `SME REVIEW PENDING` warning badge.

4. **Sem 8 Viva / Prelims Countdown Banner (`R10`):**
   - When active in Semester 8, renders a persistent countdown timer:
     * *New Topics End:* `2027-04-22` (14 days before end-sem start on `2027-05-06`).
     * *B.Tech Project Viva:* `2027-05-19` (UPSC capped at 10 hrs/wk).
     * *Prelims Day:* `2027-05-23` (Pure revision mode from 20 to 22 May).

### 4.3 Resource & Learning Screen (`web/src/screens/learn.js`)

1. **Curated Materials Pane (Left Column):**
   - Displays daily and milestone learning items from `resources.csv`.
   - Each card displays resource title, provider, and difficulty tag.
   - **Verification Badges:**
     * If `verified=TRUE`: Renders green `VERIFIED SOURCE` badge with direct link to official portal or NPTEL preview.
     * If `verified=FALSE`: Renders prominent amber badge: `NOT CONFIRMED YET — CONFIRM EDITION WITH MENTOR`.
   - **Degree-Proof Disclaimer Banner:** If student views degree-proof prerequisites, the UI displays:
     > *"Degree-proof timing not confirmed yet until official CSE-2027 notification (Data Request D05 / Fact F10)."*

2. **Practice & Check-in Tasks Pane (Right Column):**
   - Daily active practice exercises: 45-minute daily newspaper tracker, 2 Mains answers per day rubric, and CSAT numeracy practice cards.

### 4.4 Adaptation & Alert Banners (`adapt.js` & `progress.js`)

1. **Simulator & Policy Diff View (`web/src/screens/adapt.js`):**
   - Allows students to simulate academic shocks (e.g. end-sem exam clash, CGPA drop below 6.50, placement registration) and inspect deterministic plan adjustments.
   - Renders visual alert banners corresponding to triggered rules:
     * `ALERT_R1_WORKLOAD`: *"Sem 6/7 workload overload detected. Pausing optional tasks; shifting timeline +1 week."*
     * `ALERT_R2_CGPA_GUARD`: *"CGPA dropped below 6.50 floor. Capping UPSC prep at 6 hrs/week. Review departmental fallback."*
     * `ALERT_R6_PLACEMENT`: *"Placement season active. Preserving 6 hrs/wk floor until placement outcome."*
     * `ALERT_R7_ATTEMPT_DECISION`: *"Attempt Decision: Cut-off baseline not confirmed yet. Deferral recommended."*
     * `ALERT_R8_LATE_START`: *"Late start detected (< 50% static pass 1). Default track: Attempt after graduation."*
     * `ALERT_R9_AGE_GUARD`: *"Under-21 on 1 August. Earliest eligible exam cycle: 2028."*
     * `ALERT_R10_EXAM_CLASH`: *"Sem 8 Exam Clash: New syllabus study freezes on 2027-04-22. Capping hours to 10 hrs/wk."*

2. **Goal Mastery & Evidence Ledger (`web/src/screens/progress.js`):**
   - Visualizes demonstrated competency across the 12 UPSC skills (`skills.csv`).
   - Distinguishes between mere syllabus reading and evidence-backed proficiency (derived from proctored sectional tests, evaluated Mains rubrics, and error-logged mocks).

---

## Section 5: Concrete Sample JSON & UI Wireframe Mock

### 5.1 Sample `Plan.json` Response Object

The following JSON payload represents an active, personalized roadmap for a Semester 5 `BTECH_EE` student (`student_id: 24EE01042`) on the `btech_upsc` track. It strictly adheres to `docs/contracts/Plan.json` and `docs/contracts/PlanItem.json` (`additionalProperties: false`, valid enums, complete `StructuredReason` objects, and schema-compliant `ValidationReport`):

```json
{
  "plan_id": "PLAN_UPSC_2026_EE_SEM5_001",
  "student_id": "24EE01042",
  "goal_id": "GOAL_UPSC_CSE",
  "version": 1,
  "items": [
    {
      "item_id": "ITEM_MS_04",
      "item_type": "milestone",
      "course_id": null,
      "exercise_id": null,
      "resource_id": null,
      "semester_number": 5,
      "scheduled_week": 1,
      "estimated_hours": 10.0,
      "reason": {
        "intent": "Lock in UPSC Optional Subject",
        "target_skills": [
          "SKILL_UPSC_OPTIONAL"
        ],
        "why_this": "Rule R3 requires B.Tech EE students to finalize their optional subject by Semester 5.",
        "prerequisite_for": [
          "upsc_summer_intensive_y3"
        ],
        "rule_compliance": [
          "R3:optional_gate",
          "F08:optional_list",
          "F09:optional_level"
        ]
      }
    },
    {
      "item_id": "ITEM_RES_RS14",
      "item_type": "resource",
      "course_id": null,
      "exercise_id": null,
      "resource_id": "RS14",
      "semester_number": 5,
      "scheduled_week": 2,
      "estimated_hours": 6.0,
      "reason": {
        "intent": "Syllabus alignment for Electrical Engineering Optional",
        "target_skills": [
          "SKILL_UPSC_OPTIONAL"
        ],
        "why_this": "Review official UPSC EE Optional syllabus against completed Semester 3-5 core courses.",
        "prerequisite_for": [
          "upsc_optional_lock_in"
        ],
        "rule_compliance": [
          "RS14:verified_true"
        ]
      }
    },
    {
      "item_id": "ITEM_RES_RS10",
      "item_type": "resource",
      "course_id": null,
      "exercise_id": null,
      "resource_id": "RS10",
      "semester_number": 5,
      "scheduled_week": 3,
      "estimated_hours": 5.25,
      "reason": {
        "intent": "Daily current affairs synthesis",
        "target_skills": [
          "SKILL_UPSC_CURRENT_AFFAIRS"
        ],
        "why_this": "Maintain daily 45-minute national news habit mapped to GS syllabus topics.",
        "prerequisite_for": [
          "upsc_current_affairs_system"
        ],
        "rule_compliance": [
          "R1:workload_overload",
          "RS10:verified_true"
        ]
      }
    },
    {
      "item_id": "ITEM_CRS_EE3L004",
      "item_type": "course",
      "course_id": "EE3L004",
      "exercise_id": null,
      "resource_id": null,
      "semester_number": 5,
      "scheduled_week": 4,
      "estimated_hours": 4.0,
      "reason": {
        "intent": "Core B.Tech course dual-alignment with Optional Paper 1",
        "target_skills": [
          "SKILL_UPSC_OPTIONAL"
        ],
        "why_this": "Power Electronics covers solid-state converters and drives matching Section 3 of Optional Paper 1.",
        "prerequisite_for": [
          "upsc_optional_lock_in"
        ],
        "rule_compliance": [
          "optional_catalog:BTECH_EE_STRONG"
        ]
      }
    }
  ],
  "validation_report": {
    "plan_id": "PLAN_UPSC_2026_EE_SEM5_001",
    "passed": true,
    "checks": [
      {
        "check_name": "CGPA_Guard_R2",
        "passed": true,
        "severity": "info",
        "message": "Student CGPA 7.82 exceeds hard floor 6.50 and soft floor 7.00. Standard 12 hrs/wk allocated."
      },
      {
        "check_name": "Optional_Gate_R3",
        "passed": true,
        "severity": "info",
        "message": "Semester 5 B.Tech EE student prompted for Electrical Engineering Optional lock-in."
      },
      {
        "check_name": "Age_Eligibility_R9",
        "passed": true,
        "severity": "info",
        "message": "Candidate born 2004-03-15 will be 23 on 2027-08-01 (meets minimum age 21 per facts F01)."
      }
    ],
    "messages": [
      "Plan successfully validated against deterministic policy rules R1-R10 and curriculum slots."
    ]
  },
  "conflict_flag": null,
  "optional_overload_proposals": [],
  "is_active": true,
  "created_at": "2026-11-15T22:30:00Z"
}
```

### 5.2 Frontend Component Wireframe Mocks

#### Wireframe 1: Phase-Wise Roadmap Screen (`web/src/screens/plan.js`)

```
+==================================================================================================+
|  EBuddy Academic & Career Navigator | IIT Bhubaneswar                        [Profile: 24EE01042] |
+==================================================================================================+
|  ACTIVE TRACK: UPSC Civil Services Examination (GOAL_UPSC_CSE)                                   |
|  BRANCH: B.Tech Electrical Engineering (EE) | CURRENT SEMESTER: 5 | CGPA: 7.82                   |
|  TEMPLATE: UPSC-24 (24 Months, Speed: 12 hrs/wk) | TARGET EXAM CYCLE: CSE-2027                   |
+--------------------------------------------------------------------------------------------------+
|  [!] PERSISTENT NOTICE: Degree-proof timing not confirmed yet until official CSE-2027 notice    |
+--------------------------------------------------------------------------------------------------+

  [Switch to Weekly Schedule]  [Switch to Semestral View]  [Begin Study & Check-in Tasks ->]

  +----------------------------------------------------------------------------------------------+
  | PHASE 1: Orientation, Newspaper Habit & NCERT Foundation (Sem 1-3)            [100% COMPLETE] |
  | Progress: [==============================================================================] 15% |
  | [x] upsc_orientation_habit: 60-day newspaper streak verified.                                |
  | [x] upsc_ncert_baseline: 90% NCERT chapters completed with 1-page notes.                      |
  +----------------------------------------------------------------------------------------------+

  +----------------------------------------------------------------------------------------------+
  | PHASE 2: Core Static Pass 1, CA System & Optional Lock-In (Sem 4-5)              [IN PROGRESS] |
  | Progress: [======================================>.......................................] 22% |
  | Target Share: 40% | Allocated Hours: 12.0 hrs/wk | B.Tech Workload: HEAVY LAB (EE3P004/005)   |
  |                                                                                              |
  | [>] CURRENT MILESTONE: upsc_optional_lock_in (Rule R3 Mandatory Lock-In)                     |
  |     +--------------------------------------------------------------------------------------+ |
  |     | OPTIONAL SUBJECT COMPARISON & CURRICULUM OVERLAP:                                    | |
  |     | Recommended: Electrical Engineering [STRONG OVERLAP - 12 B.Tech Core Courses]        | |
  |     | Overlapping Core Courses: EE2L001 (Networks), EE3L004 (Power Elec), EE3L007 (Grid)   | |
  |     | Status: [Confirm Electrical Engineering as Optional]  [Explore Breadth Economics]    | |
  |     +--------------------------------------------------------------------------------------+ |
  |                                                                                              |
  | [*] UPCOMING MILESTONES:                                                                     |
  |     - upsc_static_pass1: 4 of 6 core texts completed (Polity, Modern History, Economy, Geog) |
  |     - upsc_current_affairs_system: 90-day streak in progress (Day 42/90)                     |
  +----------------------------------------------------------------------------------------------+

  +----------------------------------------------------------------------------------------------+
  | PHASE 3: Answer Writing, Ethics/Essay & Summer Intensive (Sem 6 + Summer)           [LOCKED] |
  | Target Share: 20% | Unlock Condition: Complete Phase 2 + Optional Subject Locked             |
  +----------------------------------------------------------------------------------------------+

  +----------------------------------------------------------------------------------------------+
  | PHASE 4: Revision Pass 2, Prelims Mock Sprint & Attempt Decision (Sem 7-8)          [LOCKED] |
  | Target Share: 25% | Exam Clash Freeze Window (R10): Starts 2027-04-22 (Viva: 2027-05-19)     |
  +----------------------------------------------------------------------------------------------+
```

#### Wireframe 2: Curated Learning & Verification Screen (`web/src/screens/learn.js`)

```
+==================================================================================================+
|  Daily Learning & Curated Materials (Agent 2)                             [<- Back to Roadmap]  |
+==================================================================================================+

  +---------------------------------------------+  +---------------------------------------------+
  | COLUMN 1: CURATED KNOWLEDGE BASE MATERIALS  |  | COLUMN 2: ACTIVE CHECK-IN & PRACTICE TASKS  |
  +---------------------------------------------+  +---------------------------------------------+
  | [RS14] Electrical Engineering Optional      |  | [TASK 1] Daily Current Affairs Synthesis    |
  | Provider: UPSC Official Notification        |  | Target: The Hindu / PIB Summaries           |
  | Type: Official Syllabus Portal              |  | Duration: 45 minutes mandatory habit        |
  | Target Skill: SKILL_UPSC_OPTIONAL           |  | [Log Today's 45-min Reading Session]        |
  | [VERIFIED SOURCE]                           |  +---------------------------------------------+
  | Link: https://www.upsc.gov.in/...pdf        |  | [TASK 2] Daily Mains Answer Writing         |
  +---------------------------------------------+  | Question: "Discuss the role of renewable    |
  | [RS04] Indian Polity (6th Edition)          |  | grid integration in energy security (GS3)." |
  | Provider: M. Laxmikanth (McGraw Hill)       |  | Word Limit: 150 words | Time: 10 minutes    |
  | Type: Core Book                             |  | [Submit Answer for Peer/Mentor Rubric]      |
  | Target Skill: SKILL_UPSC_GS2_POLITY         |  +---------------------------------------------+
  | [!] NOT CONFIRMED YET - CONFIRM EDITION     |  | [TASK 3] CSAT Baseline Numeracy Sprint      |
  | Note: Edition & syllabus mapping pending.   |  | Resource: RS23 NCERT Mathematics Class 10   |
  +---------------------------------------------+  | Topic: Ratios, Speed-Distance, Averages     |
  | [RS10] Press Information Bureau (PIB)       |  | 5 Practice Questions | Accuracy Goal: 80%   |
  | Provider: Government of India               |  | [Start 15-Minute CSAT Drill]                |
  +---------------------------------------------+  +---------------------------------------------+
```

---

## Discrepancies

- `ux_design.md` named in the task prompt does not exist in the repository; mapped cleanly to `docs/UI.md` and `web/src/screens/*.js`.
- `cutoffs.csv` contains only one cycle with `verified=TRUE` (CSE-2025 General Prelims GS-I: 92.66 / 200); CSE-2024 (87.98) and CSE-2023 (75.41) are marked `verified=FALSE`, which deterministically causes Rule `R7` to output `"Not confirmed yet"` for the cutoff baseline due to requiring at least 2 verified cycles.
- Degree-proof timing (`D05` / Fact `F10`) is unconfirmed (`verified=FALSE`); the engine and UI strictly display `"Degree-proof timing not confirmed yet until official CSE-2027 notification"` per policy rules.
- Metallurgy is not an optional subject in UPSC CSE (`facts.csv:F08`); candidate optionals for MME students in `optional_catalog.csv` (Mechanical Engineering, Geology, Chemistry, Physics) are all flagged `sme_reviewed=FALSE` pending curriculum-to-syllabus mapping (`data_requests.md:D09`).
- Diagnostic test item bank (`diagnostic_items.csv`) contains 45 draft questions across Polity, CSAT, and Economy, all flagged `verified=FALSE` pending subject-matter expert review.
- Curriculum track assignment (`facts.csv:F21`): The rule assuming Semesters 1 and 3 follow the NEP curriculum while Semesters 5 and 7 follow the 2016–17 pre-NEP curriculum is unconfirmed (`verified=FALSE`, `data_requests.md:D04`).
