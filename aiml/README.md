# Artificial Intelligence & Machine Learning (AI/ML) Knowledge Base

This package contains the official data sources, transformation scripts, and generated relational CSV knowledge bases for the AI/ML personalized learning path in **eBuddy** (Adobe Personalised Learning Buddy, Inter IIT Tech Meet 15.0).

---

## Directory Structure

```text
aiml/
├── data/                                 # Raw source Excel files
│   ├── AI_ML_Learning_Roadmap_KnowledgeBase-v2.xlsx           # 6-phase AI/ML curriculum & 55 resources
│   ├── top7_iit_fests_26-27.xlsx                              # Top 7 IIT tech fests & 55 AI/ML hackathons
│   └── ai_ml_hackathons_and_top7_iit_fests_2026-2027.xlsx     # Canonical mirror validation Excel
├── scripts/                              # Automated Python transformation pipelines
│   ├── build_csvs.py                                          # Generates AI/ML roadmap, resources & DAG
│   └── build_events_csvs.py                                   # Generates AI/ML fests, hackathons & rules
├── output/                               # Clean, relational CSV files (UTF-8 with BOM)
│   ├── 01_roadmap.csv                                         # 6-phase overview roadmap with hours & outcomes
│   ├── 02_phase_resources.csv                                 # 55 phase-wise curated learning resources
│   ├── 03_prerequisites.csv                                   # Relational prerequisite DAG & NCERT math
│   ├── 01_events_master.csv                                   # Unified catalog (7 fests, 25 hacks, 30 comps)
│   ├── 02_phase_eligibility.csv                               # Stage-wise unlock gating rules (7 stages)
│   ├── 03_recommendation_rules.csv                            # Machine-readable recommendation rules (R01–R11)
│   └── 04_domain_to_phase_map.csv                             # Topic tagging, prerequisite phases & beginner flags
└── README.md                             # Package documentation (this file)
```

---

## Generated CSV Catalog (`aiml/output/`)

| File | Rows | Description |
|---|---|---|
| **`01_roadmap.csv`** | 6 | High-level roadmap showing phase progression across `0_Foundations`, `1_Classical_ML`, `2_Deep_Learning`, `3_Projects`, `4_Specialization`, and `5_Research` (1,624 total hours). |
| **`02_phase_resources.csv`** | 55 | Detailed catalog of curated learning resources sorted by phase and curriculum order across 11 normalized format groups. |
| **`03_prerequisites.csv`** | Long Format | Relational prerequisite mapping linking every resource to its prerequisites, including 16 granular CBSE/NCERT Class 11–12 mathematics chapters. |
| **`01_events_master.csv`** | 62 | Unified master catalog covering 7 Top IIT Tech Fests, 25 Hackathons, and 30 Leaderboard Competitions. |
| **`02_phase_eligibility.csv`** | 7 | Stage-wise gating rules defining category unlocks (`fests_unlocked`, `hackathons_unlocked`, `competitions_unlocked`), recommendation quotas, and user nudges across 7 stages. |
| **`03_recommendation_rules.csv`** | 11 | Machine-readable engine rules (R01–R11) governing eligibility, set sizing, category mix, diversity, timeline filters, and domain matching. |
| **`04_domain_to_phase_map.csv`** | 62 | Fine-grained classification linking events to 16 canonical technical domains, unlock phases, and beginner-friendly flags. |

---

## Running the Pipelines

To regenerate the AI/ML curriculum knowledge base:
```bash
python aiml/scripts/build_csvs.py
```

To regenerate the AI/ML events and competitions knowledge base:
```bash
python aiml/scripts/build_events_csvs.py
```
