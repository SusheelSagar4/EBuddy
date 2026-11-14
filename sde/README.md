# Software Development Engineer (SDE) Knowledge Base

This package contains the official data sources, transformation scripts, and generated relational CSV knowledge bases for the Software Development Engineer (SDE) personalized learning path in **eBuddy** (Adobe Personalised Learning Buddy, Inter IIT Tech Meet 15.0).

---

## Directory Structure

```text
sde/
├── data/                                 # Raw source Excel files
│   ├── SDE_Prep_Roadmap_with_Playlists.xlsx      # 35 roadmap steps & 105 tiered curated playlists
│   ├── Top_SDE_Project_GitHub_Repos.xlsx         # 35 curated GitHub repos & 8 portfolio path projects
│   └── SDE_Competitions_Hackathons_2026-27.xlsx  # 41 fests, hackathons & competitions (2026–2027)
├── scripts/                              # Automated Python transformation pipelines
│   ├── build_sde_csvs.py                         # Generates SDE curriculum, checkpoints & repos
│   └── build_sde_events_csvs.py                  # Generates SDE events, eligibility & rules
├── output/                               # Clean, relational CSV files (UTF-8 with BOM)
│   ├── 01_sde_roadmap_overview.csv               # 8-phase roadmap overview (35 topics)
│   ├── 02_phase_learning_content.csv             # 105 tiered learning resources (Tiers A, B, C)
│   ├── 03_topic_checkpoints.csv                  # 35 proof-of-learning checkpoints & passing criteria
│   ├── 04_project_repos.csv                      # 35 curated GitHub repos with required skills & phases
│   ├── 05_portfolio_projects.csv                 # 8 flagship resume portfolio projects
│   ├── 01_events_master.csv                      # Master events catalog (2 FEST, 26 HACK, 13 COMP)
│   ├── 02_phase_eligibility.csv                  # 9-stage unlock gating rules & user messages
│   └── 03_recommendation_rules.csv               # Engine recommendation rules (R01–R14)
└── README.md                             # Package documentation (this file)
```

---

## Generated CSV Catalog (`sde/output/`)

| File | Rows | Description |
|---|---|---|
| **`01_sde_roadmap_overview.csv`** | 8 | High-level 8-phase SDE roadmap overview spanning foundational programming to interview preparation. |
| **`02_phase_learning_content.csv`** | 105 | Exhaustive tiered curriculum content covering all 35 steps across Tiers A, B, and C (35 × 3). Live URLs extracted from OpenPyXL hyperlink targets. |
| **`03_topic_checkpoints.csv`** | 35 | Relational proof-of-learning checkpoints for every step of the SDE learning path with passing criteria. |
| **`04_project_repos.csv`** | 35 | Curated catalog of open-source GitHub repositories with prerequisite roadmap steps and difficulty tiers. |
| **`05_portfolio_projects.csv`** | 8 | Structured portfolio project recommendations highlighting recruiter-facing proof of competence. |
| **`01_events_master.csv`** | 41 | Unified SDE events catalog covering 2 Tech Fests, 26 Hackathons, and 13 Coding Competitions relative to reference date `2026-11-15`. |
| **`02_phase_eligibility.csv`** | 9 | Stage-wise gating rules defining category unlocks (`fests_unlocked`, `hackathons_unlocked`, `competitions_unlocked`), recommendation quotas, and contextual user nudges. |
| **`03_recommendation_rules.csv`** | 14 | Machine-readable engine rules (R01–R14) governing eligibility, set sizing, category mix, diversity, timeline filters, and hiring preferences. |

---

## Running the Pipelines

To regenerate the SDE curriculum knowledge base:
```bash
python sde/scripts/build_sde_csvs.py
```

To regenerate the SDE events and competitions knowledge base:
```bash
python sde/scripts/build_sde_events_csvs.py
```
