# Core to M.Tech Evaluation Scorecard

*Evaluated on 2026-11-15 22:11:56 across 32 synthetic student profiles (16 EE, 16 MM).*

## 1. Summary Metrics

| Evaluation Dimension | Tested | Passed | Pass Rate | Benchmark Status |
|---|---|---|---|---|
| **Eligibility Determination Correctness** | 32 | 32 | 100.0% | PASS (100%) |
| **Cited Rule Grounding & Traceability** | 32 | 32 | 100.0% | PASS (100%) |
| **Zero Unverified Data Leak Compliance** | 32 | 32 | 100.0% | PASS (100%) |
| **Deterministic Shortlist Stability (3 Runs)** | 28 | 28 | 100.0% | PASS (100%) |
| **Dynamic Adaptation Scenarios** | 4 | 4 | 100.0% | PASS (100%) |
| **Diagnostic Question Grounding & Verification** | 2 Papers | 2 Papers | 100.0% | PASS (100%) |

## 2. Cohort Demographics

- **Departments:** 16 B.Tech Electrical Engineering (`BTECH_EE`), 16 B.Tech Metallurgical and Materials Engineering (`BTECH_MM`).
- **Academic Years:** 2nd Year (4 profiles), 3rd Year (16 profiles), 4th Year (12 profiles).
- **CGPA Range:** 5.5 to 9.5 (covering high performers, average performers, and academic recovery cases).
- **Backlogs:** 0 backlogs (20), 1 backlog (6), 2 backlogs (6).
- **Target Routes:** M.Tech/ME (14), MS(Research) & Direct PhD (8), PSU Recruitment (6), Undecided (4).
- **Prep Statuses:** Just starting (10), Halfway (16), Advanced (6).
- **Mock Trends:** Rising (14), Plateaued (6), Falling (4), Inconsistent (4), None / Not Started (4).
- **Edge Cases Tested:**
  - Low CGPA (<6.5) aiming for IISc Direct PhD (properly gated and redirected).
  - High CGPA (>9.0) aiming for PSU (aligned with Maharatna cut-offs).
  - Sudden mock drops (diagnosed and calibrated with wider uncertainty band).
  - Backlogs with GATE prep (CGPA protection prioritized to clear backlogs before GATE load).
  - 2nd year students testing early (accurately marked `eligible_later` with RULE_GATE_YEAR_ELIGIBILITY cited).

## 3. Four Dynamic Adaptation Scenarios

1. **Strong vs. Weak Mock Trend Calibration:**
   - Profile `SYN_MTECH_EE_10` (rising trend: 780, 830, 860) yields predicted score band [800.0, 846.7] with high confidence.
   - Profile `SYN_MTECH_EE_04` (falling trend: 710, 640, 580) yields predicted score band [603.3, 683.3] with explicit recommendation to pause mocks and remediate foundation topics.
2. **Placement & End-Sem Clash Protection:**
   - Week 7 Placement clash detected: Surfaces Option A (maintain 1 full mock on Sunday, defer topic tests) vs. Option B (pause mocks for 2 weeks, accept delay in full-syllabus coverage) with quantified trade-offs.
   - Week 14 End-Sem clash detected: Automatically prioritizes semester subjects mapped to GATE (double-benefit) and curtails pure GATE study to protect CGPA.
3. **Post-Result Re-Planning for Below-Target Scores:**
   - Actual GATE score 420 (below all top IIT targets) triggers `score_below_target_warning=True`.
   - Immediately generates 3 viable alternatives: MS(Research) with written test/interview, GATE retake with targeted gap plan, or pivot to core-industry track with zero lost evidence.
4. **Route Switching to PSU Recruitment:**
   - Switching from `ROUTE_MTECH_INDIA` to `ROUTE_PSU_GATE` preserves 100% of the 16 recorded evidence items.
   - Creates a new plan version with diffs: carries over technical syllabus mastery, replaces COAP/CCMT milestones with PSU notification windows (IOCL, NTPC, PGCIL, SAIL).

## 4. PS Compliance Audit Checklist

- [x] **Zero Rigid Timetables:** Weekly focus goals and hours budget only; no time-of-day slots.
- [x] **Curriculum DAG & Prereq Safety:** Verified against institute course structures.
- [x] **Deterministic Engine Split:** 100% of eligibility, tiering, scoring, and conflict logic runs via deterministic code; LLM is used strictly for conversational delivery.
- [x] **Zero Outbound Runtime Network Calls:** All exam, cut-off, and syllabus data loaded from local air-gapped seed files.
- [x] **Data Integrity Protocol:** All fact rows contain source URLs, retrieved dates, and verification flags.
