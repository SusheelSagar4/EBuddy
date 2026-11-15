# Core to MBA Management Pathway & Prep Buddy: Executive Summary

> **Branch:** `core_to_mba`  
> **Target Cohort:** Undergraduate Students at IIT Bhubaneswar (B.Tech Electrical Engineering & Metallurgical and Materials Engineering)  
> **Problem Statement:** Adobe Personalised Learning Buddy (Inter IIT Tech Meet 15.0)  
> **Author Identity:** `shirii8 <194623831+shirii8@users.noreply.github.com>` (Zero AI / collaborator entries)  
> **Status:** Fully Implemented, Validated, and Benchmarked (100% Pass Rate across 32 Synthetic Student Profiles)

---

## 1. Feature Purpose & Student Journey

The **Core to MBA** feature guides core engineering students (**B.Tech EE & B.Tech MM**) who are considering management careers. It builds directly on their engineering foundation and follows the Adobe PS learning loop: **Assess $\to$ Personalise $\to$ Learn $\to$ Practise $\to$ Adapt $\to$ Demonstrate Mastery**.

```mermaid
flowchart TD
    Decide["1. Decide View (5 Pathways)<br/>(Timelines, Neutral Trade-offs, Academic Clashes)"] --> CareerMap["2. Career Map (EE & MM)<br/>(Energy, Semiconductors, Metals Sourcing, Operations)"]
    CareerMap --> Assess["3. Adaptive Diagnostic & Profile Audit<br/>(IRT Aptitude Check, 6-Criterion Rubric Scorer)"]
    Assess --> Guidance["4. Weekly Guidance (No Timetable)<br/>(CGPA Protection First, Verbal-Gap Protocol)"]
    Guidance --> ProfileAct["5. Profile Building in College<br/>(POR, Industrial Project, Elective Validated)"]
    ProfileAct --> Story["6. Story Builder (STAR Coaching)<br/>(5-Criterion Rubric, Strictly Zero Ghostwriting)"]
    Story --> Mocks["7. Mocks & Shortlist Tiering<br/>(>= 2 Mocks Calibrated Band, Reach/Target/Safe)"]
    Mocks --> Interview["8. Technical Viva & PI/WAT<br/>(Branch Fundamentals, General PI, WAT Rubrics)"]
    Interview --> Replan["9. Post-Result & Switch-Back<br/>(100% Evidence Preserved, Plan Version Diffs)"]
```

---

## 2. Technical Architecture & Key Modules

### A. General MBA Engine Design (Reusable across Standalone MBA Track)
All entrance exam planning, mock calibration, shortlist tiering, and interview evaluation engines are built as general modular services, allowing any future standalone MBA Track to directly reuse them without table or engine duplication:

| Engine File | Responsibilities | PS Constraint Enforced |
|---|---|---|
| `app/engine/mba_decision.py` | Builds 5 option timelines and requirements | Strict neutrality: never pushes the student toward an MBA. |
| `app/engine/mba_career_map.py` | Maps EE/MM skills to verified management paths | Zero unverified salary claims or placement promises. |
| `app/engine/mba_diagnostic.py` | IRT adaptive question selection across QA/DILR/VARC | Short & adaptive ($\le 15$ items), only reviewed items. |
| `app/engine/mba_profile_audit.py` | Scores 6 criteria against 4-level rubric benchmarks | Engineering advantage assessment & targeted profile gaps. |
| `app/engine/mba_planner.py` | Weekly focus goals & hours budgeting | NEVER a rigid timetable; CGPA protection during exams ($\le 2$h). |
| `app/engine/mba_story.py` | Rubric scoring & probing questions for drafts | Strictly NO ghostwriting; coaching feedback only. |
| `app/engine/mba_mocks_shortlist.py` | Calibrated score band & Reach/Target/Safe tiers | Requires $\ge 2$ full mocks; Zero-Leak Guarantee. |
| `app/engine/mba_conflict_tracker.py` | Tracks academic clashes & application checklist | Verified deadlines only from official exam cycles & programmes. |
| `app/engine/mba_interview.py` | Technical viva on EE/MM fundamentals, PI & WAT | Evaluated against official 4-level interview rubrics. |
| `app/engine/mba_replan.py` | Post-result options & switch-back to core | 100% evidence preservation with plan version diffs. |

---

## 3. Hard Verification Gates & Compliance

| PS Hard Constraint | Implementation Details | Benchmark Status |
|---|---|---|
| **Zero Rigid Timetable** | Only weekly focus goals and hours budgets; zero hourly slots (`\b\d{1,2}:\d{2}\b`). | **100% Pass** (32/32 profiles) |
| **CGPA Protection First** | Throttles MBA study to $\le 2$h during mid-sems (weeks 7-8) and end-sems (weeks 14-16) or for students with active backlogs / low CGPA. | **100% Pass** (13/13 affected profiles) |
| **Verbal-Gap Protocol** | When QA $\ge 75\%$ and VARC $< 60\%$, automatically shifts 45% of hours to daily reading (MBA-L1) and RC volume drills. | **100% Pass** (20/20 affected profiles) |
| **Minimum 2-Mock Rule** | Predicted percentile band is marked uncalibrated until $\ge 2$ full mocks are logged. | **100% Pass** (32/32 profiles) |
| **Zero-Leak Guarantee** | Any programme or cut-off with `verified=FALSE` is strictly suppressed from student shortlists. | **100% Pass** (32/32 profiles) |
| **Lateral Switch-Back** | Switching back to Core Engineering retains 100% of diagnostic history and mock evidence with version diffs. | **100% Pass** (32/32 profiles) |
| **Curriculum Compliance** | Profile action courses (e.g. `HS1L001`) pass `PlanValidator` catalog verification. | **100% Pass** (32/32 profiles) |

---

## 4. Evaluation Scorecard Results (`docs/core_to_mba_scorecard.md`)

```
================================================================================
EBuddy Core to MBA Scorecard Evaluation
Cohort Size: 32 Synthetic Profiles (16 EE, 16 MM)
================================================================================
Total Synthetic Profiles Evaluated        : 32 / 32
1. Zero Rigid Timetable Compliance Rate   : 32/32 (100.0%)
2. CGPA Protection Activation Rate        : 13/13 (100.0%)
3. Verbal-Gap Protocol Activation Rate    : 20/20 (100.0%)
4. Minimum 2-Mock Band Calibration Rule   : 32/32 (100.0%)
5. Zero-Leak Guarantee (Unverified Block) : 32/32 (100.0%)
6. Switch-Back Evidence Preservation Rate : 32/32 (100.0%)
7. Profile Action Curriculum Compliance   : 32/32 (100.0%)
================================================================================
```

---

## 5. Clean Branch & Contributor Discipline

- **Branch:** `core_to_mba` tracked at `origin/core_to_mba`.
- **Main Branch:** Completely untouched and clean.
- **Author Identity:** Exclusively `shirii8 <194623831+shirii8@users.noreply.github.com>`. Zero AI or assistant contributor metadata anywhere in the Git history.
