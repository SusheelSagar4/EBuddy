# Software Development Engineer (SDE) Knowledge Base

This package contains the official data sources, transformation scripts, and generated relational CSV knowledge bases for the Software Development Engineer (SDE) personalized learning path in **eBuddy** (Adobe Personalised Learning Buddy, Inter IIT Tech Meet 15.0).

---

## Directory Structure

```text
sde/
├── data/                                 # Raw source Excel files
│   ├── SDE_Prep_Roadmap_with_Playlists.xlsx      # 35 roadmap steps & 105 tiered curated playlists
│   ├── Top_SDE_Project_GitHub_Repos.xlsx         # 35 curated GitHub repos & 8 portfolio path projects
│   ├── SDE_Competitions_Hackathons_2026-27.xlsx  # 41 fests, hackathons & competitions (2026–2027)
│   ├── LeetCode_DSA_Easy.xlsx                    # 259 curated Easy practice problems
│   ├── LeetCode_DSA_Medium.xlsx                  # 684 curated Medium practice problems
│   └── LeetCode_DSA_Hard.xlsx                    # 576 curated Hard practice problems
├── scripts/                              # Automated Python transformation pipelines
│   ├── build_sde_csvs.py                         # Generates SDE curriculum, checkpoints & repos
│   ├── build_sde_events_csvs.py                  # Generates SDE events, eligibility & rules
│   └── build_sde_quiz_csvs.py                    # Generates SDE quiz bank, unique catalog & roadmap map
├── output/                               # Clean, relational CSV files (UTF-8 with BOM)
│   ├── 01_sde_roadmap_overview.csv               # 8-phase roadmap overview (35 topics)
│   ├── 02_phase_learning_content.csv             # 105 tiered learning resources (Tiers A, B, C)
│   ├── 03_topic_checkpoints.csv                  # 35 proof-of-learning checkpoints & passing criteria
│   ├── 04_project_repos.csv                      # 35 curated GitHub repos with required skills & phases
│   ├── 05_portfolio_projects.csv                 # 8 flagship resume portfolio projects
│   ├── 01_events_master.csv                      # Master events catalog (2 FEST, 26 HACK, 13 COMP)
│   ├── 02_phase_eligibility.csv                  # 9-stage unlock gating rules & user messages
│   ├── 03_recommendation_rules.csv               # Engine recommendation rules (R01–R14)
│   ├── 01_problem_bank_raw.csv                   # 1,519 raw LeetCode problem records with live URLs
│   ├── 02_problems_unique.csv                    # 1,193 deduplicated catalog with conflict resolutions
│   └── 03_topics_roadmap_map.csv                 # 15 canonical topics mapped to SDE roadmap steps
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
| **`01_problem_bank_raw.csv`** | 1,519 | Complete LeetCode practice bank combining Easy (259), Medium (684), and Hard (576) workbooks with row IDs (`EASY-0001`, `MED-0001`, `HARD-0001`), live URLs extracted via OpenPyXL hyperlinks, canonical topic mapping, and subgroup tracking. |
| **`02_problems_unique.csv`** | 1,193 | Deduplicated LeetCode problem master catalog. Features cross-file conflict detection (`difficulty_conflict`, `topic_conflict`), calibrated eligibility flags (`quiz_eligible_calibrated`), and linkage to primary roadmap steps and phases. |
| **`03_topics_roadmap_map.csv`** | 15 | Canonical 15-topic taxonomy mapped to SDE roadmap steps (Steps 4 to 26; Phases P2 to P5) with difficulty-stratified inventory, prerequisite relationships, and automated quiz readiness status (`READY`, `LIMITED`, `INSUFFICIENT`). |

---

## Canonical Topics & Quiz Readiness

| Topic ID | Canonical Topic | Roadmap Steps | Phase | Mapping | Calibrated Medium | Readiness Status |
|---|---|---|---|---|---|---|
| **T01** | Arrays & Hashing | 4 \| 6 | P2_DSA_Foundations | FULL | 76 | **READY** |
| **T02** | Strings | 5 | P2_DSA_Foundations | FULL | 51 | **READY** |
| **T03** | Two Pointers & Sliding Window | 9 \| 10 | P3_DSA_Core_Techniques | FULL | 29 | **READY** |
| **T04** | Binary Search & Sorting | 7 \| 8 | P2_DSA_Foundations | FULL | 16 | **READY** |
| **T05** | Linked List | 11 | P3_DSA_Core_Techniques | FULL | 6 | **LIMITED** |
| **T06** | Stack & Queue | 12 \| 13 | P3_DSA_Core_Techniques | FULL | 9 | **LIMITED** |
| **T07** | Trees & BST | 18 \| 19 | P4_Trees_and_Graphs | FULL | 37 | **READY** |
| **T08** | Heap & Priority Queue | 20 | P4_Trees_and_Graphs | FULL | 3 | **INSUFFICIENT** |
| **T09** | Dynamic Programming | 25 \| 26 | P5_Dynamic_Programming_and_Practice | FULL | 34 | **READY** |
| **T10** | Graphs | 22 \| 23 \| 24 | P4_Trees_and_Graphs | FULL | 22 | **READY** |
| **T11** | Greedy & Intervals | 17 | P3_DSA_Core_Techniques | FULL | 8 | **LIMITED** |
| **T12** | Backtracking | 14 \| 15 | P3_DSA_Core_Techniques | FULL | 17 | **READY** |
| **T13** | Trie | 21 | P4_Trees_and_Graphs | FULL | 4 | **INSUFFICIENT** |
| **T14** | Matrix | 4 | P2_DSA_Foundations | PARTIAL | 13 | **LIMITED** |
| **T15** | Math & Bit Manipulation | 16 | P3_DSA_Core_Techniques | PARTIAL | 39 | **READY** |

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

To regenerate the SDE quiz assessment problem bank and topic map:
```bash
python sde/scripts/build_sde_quiz_csvs.py
```
