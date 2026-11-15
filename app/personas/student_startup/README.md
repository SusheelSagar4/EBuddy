# Persona Specification: student_startup

## 1. Archetype Profile
- **Persona ID:** `student_startup`
- **Target Goal:** Student Startup Founder (`GOAL_STARTUP_FOUNDER`).
- **Student Profile:** Undergraduate engineering students in Electrical Engineering (`BTECH_EE`) or Metallurgical & Materials Engineering (`BTECH_MM`) at IIT Bhubaneswar (Semesters 1–8) building a venture during their degree (from customer discovery and validation to MVP, piloting, and first traction/revenue).
- **Key Competencies:**
  1. `SKILL_STARTUP_CUSTOMER_DISCOVERY`: Customer Discovery and Validation
  2. `SKILL_STARTUP_BUSINESS_MODEL`: Business Model and Value Proposition
  3. `SKILL_STARTUP_MVP_BUILD`: MVP and Prototype Build
  4. `SKILL_STARTUP_TECH_DEPTH`: Engineering Depth for the Venture
  5. `SKILL_STARTUP_UNIT_ECONOMICS_FINANCE`: Unit Economics and Startup Finance
  6. `SKILL_STARTUP_GTM_SALES`: Go-to-Market and Sales
  7. `SKILL_STARTUP_IP_LEGAL_COMPLIANCE`: IP, Legal and Compliance Basics
  8. `SKILL_STARTUP_PITCH_FUNDRAISING`: Pitching and Fundraising
  9. `SKILL_STARTUP_TEAM_EXECUTION`: Team, Founder Agreements and Execution
  10. `SKILL_STARTUP_ECOSYSTEM_SCHEMES`: Incubators and Government Schemes

## 2. Curricular Trade-Offs & Policy Rules (S1–S7)
- **S1 (Exam Weeks Pause):** Pauses new build work when end-semester examination is within 14 days or mid-semester within 7 days (via shared `institute_calendar.csv`). Retains weekly customer calls and a 1-hour sprint review; shifts milestone windows by +1 week.
- **S2 (CGPA Guard & Core Fallback):** If CGPA drops below 6.5 (`floor_hard`), drops by >= 0.3 in the last semester, or an active backlog occurs, venture weekly hours are capped at 6 hr/week (3 hr/week in Sem 1–2), spending is frozen, and a departmental core fallback card is presented:
  - `BTECH_EE` -> `GOAL_EE_CORE_POWER` (Active core persona)
  - `BTECH_MM` -> `GOAL_FALLBACK_MME_CORE` (Handled gracefully as a stub pending MME data)
- **S3 (Validation Gate):** Blocks MVP spend and prototype feature work if fewer than 10 customer interviews have been logged; forces execution of `startup_problem_validation` tasks.
- **S4 (Runway Guard):** If financial runway is under 3 months with active burn (`monthly_burn > 0`), freezes new expenditures and presents options: cut costs, pause, or seek incubation/grants via IIT BBS REP (`SR08`) and Startup India (`SR09`).
- **S5 (IP Before Disclosure):** Inserts an IP assessment task (`SR07`) and institute IP policy review prior to scheduled public demos or pitch competitions.
- **S6 (Placement Interplay):** During Sem 7 placement registration, venture time is protected with a 5 hr/week floor, requiring a written continue / pause / job-first decision in Sem 8 (`startup_traction_decision`).
- **S7 (B.Tech Project Alignment):** In Semesters 7 & 8, prompts students whose project topic is unrelated to their venture to consult their project guide regarding aligning the B.Tech project with the venture prototype. Displayed as a **prompt only**.

## 3. Draft Status of Requirements and Mastery Defaults
> [!NOTE] Draft Defaults Notice
> All threshold values, levels, and weights in `requirements.yaml` and `mastery.yaml` are **draft defaults** derived from domain skills (`skills.csv`), milestone targets (`milestones.csv`), and `ee_power_core`/`btech_upsc` conventions pending formal review by faculty mentors and the IIT BBS Research and Entrepreneurship Park (REP).
> - Target skill requirement levels: Customer Discovery (80.0), Business Model (75.0), MVP Build (80.0), Tech Depth (75.0), Unit Economics (75.0), GTM Sales (75.0), IP/Legal (70.0), Pitching (75.0), Team Execution (75.0), Ecosystem Schemes (70.0).
> - Mastery criteria: minimum skill level 70.0, 2 project milestones, 2 timed assessments, and 65.0 minimum diagnostic score.

## 4. Strict Seed Data & Knowledge Base Governance Rules
1. **Zero Invented Data:** Only verified and documented facts from the provided seed bundle are utilized.
2. **Unverified Resources (`verified: FALSE`):** Resources `SR12` (Robert Hisrich textbook), `SR14` (IIT BBS EE/MME textbooks), and `SR15` (Startup India team lessons) are unverified and strictly surfaced with the note `"not confirmed yet"`.
3. **No `facts.csv` Rule:** The planning engine never quotes grant amounts, subsidy figures, eligibility thresholds, or deadlines for Startup India, Startup Odisha, or IIT BBS REP. The system always links to official portals (`SR08`, `SR09`) and directs the student to `"check the official page"`.
4. **NPTEL Course Run Notice:** NPTEL course availability varies by semester; all NPTEL resources (`SR02`, `SR03`, `SR04`, `SR05`, `SR06`, `SR07`) display official enrollment links accompanied by `"check the course page for the next run"`.
5. **Missing MME Core Fallback Handling:** The `BTECH_MM` fallback goal `GOAL_FALLBACK_MME_CORE` refers to an upstream stub (`data/raw/higher_studies/upsc/persona_mme_core_stub.yaml`) pending MME curriculum and PSU hiring data. The engine catches missing fallback persona packages gracefully without system exceptions.
