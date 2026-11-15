# Data Analyst Knowledge Base

This package contains the official source workbooks, transformation pipelines, and generated relational CSV knowledge bases for the Data Analyst personalized learning, events recommendation, and assessment quiz path in **eBuddy** (Adobe Personalised Learning Buddy, Inter IIT Tech Meet 15.0).

---

## Directory Structure

```text
data_analyst/
├── data/                                 # Raw source Excel workbooks
│   ├── Data_Analyst_Roadmap.xlsx         # 9 relational sheets (curriculum, skills, modules, projects, rubrics)
│   ├── Data_Analytics_Hackathons.xlsx    # 35 curated all-India data hackathons & competitions
│   └── Data_Analyst_Questions.xlsx       # 47 curated assessment questions across 20 skills
├── scripts/                              # Automated Python transformation pipelines
│   ├── build_da_csvs.py                  # Generates curriculum & portfolio CSV datasets
│   ├── build_da_events_csvs.py           # Generates events master, eligibility gating & recommendation rules
│   └── build_da_quiz_csvs.py             # Generates question bank, skills map, related skills, pool & checkpoints
├── output/                               # Clean, relational CSV files (UTF-8 with BOM)
│   ├── 01_da_roadmap_overview.csv        # 5-phase overview roadmap with skills in order and outcomes
│   ├── 02_phase_modules_resources.csv    # 44 curriculum modules joined with learning resources
│   ├── 03_skills_catalog.csv             # 20 distinct skills with prerequisite chains and levels
│   ├── 04_phase_summary_readiness_checkpoints.csv # Phase completion summaries & readiness checkpoints
│   ├── 05_projects.csv                   # 3 end-to-end portfolio projects with difficulty, rubrics & dataset links
│   ├── 06_project_rubric_items.csv       # 12 granular rubric evaluation criteria
│   ├── 07_pacing_templates.csv           # 3 pacing templates (DA-12, DA-6, DA-3) across 5 phases
│   ├── 08_milestones.csv                 # 6 sequential career and learning milestones
│   ├── 09_learning_methods.csv           # 6 evidence-based pedagogical study methods
│   ├── 01_events_master.csv              # Unified events catalog (12 Hackathons, 23 Competitions)
│   ├── 02_phase_eligibility.csv          # Stage-wise unlock gating rules (6 stages: NONE_YET to DA-PH5)
│   ├── 03_recommendation_rules.csv       # Machine-readable recommendation engine rules (R01–R12)
│   ├── 01_question_bank.csv              # 47 calibrated assessment items (MCQ, Numeric, SQL)
│   ├── 02_skills_phase_map.csv           # 20 skills taxonomy with question pool coverage & shortfall metrics
│   ├── 03_related_skills.csv             # 62 directional relationships (Prerequisite, Dependent, Same Category)
│   ├── 04_skill_difficulty_pool.csv      # 60 difficulty slots with status and fallback difficulty resolution
│   ├── 05_quiz_checkpoints.csv           # 17 adaptive quiz checkpoints (Cluster Checks, Phase End & Final)
│   └── 06_quiz_rules.csv                 # 29 machine-readable rules across 6 operational assessment scenarios
└── README.md                             # Package documentation (this file)
```

---

## Generated CSV Catalog (`data_analyst/output/`)

### 1. Curriculum & Portfolio Knowledge Base
| File | Rows | Description |
|---|---|---|
| **`01_da_roadmap_overview.csv`** | 5 | High-level roadmap showing phase progression across `DA-PH1` (Foundations), `DA-PH2` (Core SQL and Python), `DA-PH3` (Cleaning, EDA and visualisation), `DA-PH4` (BI, advanced SQL and statistics), and `DA-PH5` (Storytelling, portfolio and interview prep). |
| **`02_phase_modules_resources.csv`** | 78 | Granular curriculum table joining 44 learning modules to their mapped learning resources, 4 derived key concepts per module, and source data quality flags. |
| **`03_skills_catalog.csv`** | 20 | Complete catalog of 20 skills categorized by domain (Tools, SQL, Python, Business, Visualisation, Statistics), difficulty level, canonical phase, and prerequisite skill chains. |
| **`04_phase_summary_readiness_checkpoints.csv`** | 5 | Canonical checkpoint assessment types (`QUIZ`, `TIMED_TEST_PLUS_EXERCISE`, `PROJECT_RUBRIC`, `PROJECT_PLUS_QUIZ`, `PROJECT_PLUS_MOCK_INTERVIEW`) and phase summary texts for eBuddy chat. |
| **`05_projects.csv`** | 3 | Curated portfolio projects (`DA-P01`, `DA-P02`, `DA-P03`) linked to verified open datasets (UCI Online Retail, NYC TLC Trip Records, World Bank Open Data) and deliverables. |
| **`06_project_rubric_items.csv`** | 12 | Relational breakdown of project evaluation rubrics into individual measurable criteria for automated and peer grading. |
| **`07_pacing_templates.csv`** | 15 | Cross-product of 3 velocity templates (`DA-12`: 12 months @ 6 hrs/wk; `DA-6`: 6 months @ 12 hrs/wk; `DA-3`: 3 months @ 24 hrs/wk) across 5 phases with weekly allocations and readiness rules. |
| **`08_milestones.csv`** | 6 | Sequential learning milestones (`DA-MS1` through `DA-MS6`) with phase mappings, dependency chains, and placement timings. |
| **`09_learning_methods.csv`** | 6 | Pedagogical guidance for the learner (Learn by querying, Error log, Spaced review, Think out loud, Timeboxed problem solving, Feynman technique). |

### 2. Events & Competitions Knowledge Base (Reference Date: 2026-11-15)
| File | Rows | Description |
|---|---|---|
| **`01_events_master.csv`**<br/>*(alias: `01_da_events_master.csv`)* | 35 | Master catalog of 35 curated Indian data hackathons (12) and competitions (23) covering expected month ranges, ISO timeline start/end, offline venues, eligibility criteria, restriction flags, and mapped DA skills. |
| **`02_phase_eligibility.csv`**<br/>*(alias: `02_da_phase_eligibility.csv`)* | 6 | Stage-wise gating rules defining category unlocks (`hackathons_unlocked`, `competitions_unlocked`), recommendation quotas, and contextual user nudges across `NONE_YET` and Phases `DA-PH1` through `DA-PH5`. |
| **`03_recommendation_rules.csv`**<br/>*(alias: `03_da_recommendation_rules.csv`)* | 12 | Machine-readable engine rules (R01–R12) governing eligibility, set sizing, category mix, diversity, timeline filters, home campus preference, and skill readiness hints. |

### 3. Assessment & Quiz Engine Knowledge Base
| File | Rows | Description |
|---|---|---|
| **`01_question_bank.csv`**<br/>*(alias: `01_da_question_bank.csv`)* | 47 | Master question bank covering 32 MCQs, 10 Numeric, and 5 SQL problems. Features exact source preservation, derived grading methods (`MCQ_EXACT_OPTION_TEXT`, `NUMERIC_TOLERANCE`, `SQL_RESULT_COMPARE`), parsed numeric values, unit hints (`percent`), extracted SQL schema definitions, and option length bias metrics. |
| **`02_skills_phase_map.csv`**<br/>*(alias: `02_da_skills_phase_map.csv`)* | 20 | Complete 20-skill taxonomy mapped across Phases 1 to 5 with question counts by difficulty and type, pool health status (`OK`, `THIN`, `VERY_THIN`), and shortfall relative to the 3-question design target. |
| **`03_related_skills.csv`**<br/>*(alias: `03_da_related_skills.csv`)* | 62 | Directional inter-skill dependency graph linking skills via `PREREQUISITE` (STRONG, 22), `DEPENDENT` (STRONG, 22), and `SAME_CATEGORY` (MODERATE, 18) with concise pedagogical rationale strings ($\le 12$ words). |
| **`04_skill_difficulty_pool.csv`**<br/>*(alias: `04_da_skill_difficulty_pool.csv`)* | 60 | Exhaustive grid of 20 skills $\times$ 3 difficulty levels with question counts, pool status (`OK`, `THIN`, `EMPTY`), nearest fallback difficulty with questions, and synthetic generation flags. |
| **`05_quiz_checkpoints.csv`**<br/>*(alias: `05_da_quiz_checkpoints.csv`)* | 17 | Comprehensive checkpoint registry featuring 12 Skill Cluster Checks, 4 Phase-End Barrier Quizzes, and 1 Final Cumulative Quiz with target lengths, difficulty mixes, new vs. review shares, pass thresholds (70%), and pool shortfall evaluations. |
| **`06_quiz_rules.csv`**<br/>*(alias: `06_da_quiz_rules.csv`)* | 29 | Machine-readable operational rules (G01–G05, D01–D08, S01–S04, C01–C04, P01–P04, L01–L04) governing item presentation, option shuffling, numeric tolerance, SQL sandbox testing, diagnostic onboarding, and spaced repetition. |

---

## Running the Pipelines

To regenerate the Data Analyst curriculum knowledge base:
```bash
python data_analyst/scripts/build_da_csvs.py
```

To regenerate the Data Analyst events and hackathons knowledge base:
```bash
python data_analyst/scripts/build_da_events_csvs.py
```

To regenerate the Data Analyst quiz assessment knowledge base:
```bash
python data_analyst/scripts/build_da_quiz_csvs.py
```

Or run via repository root forwarders:
```bash
python build_da_csvs.py
python build_da_events_csvs.py
python build_da_quiz_csvs.py
```
