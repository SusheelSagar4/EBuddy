# Higher Studies Database Manifest & Data Authenticity Notice

**Source Workbook:** `media_1794647743389_24fb1e07.xlsx` (`Higher_Studies_Database.xlsx`)  
**Status in System:** **NOT LOADED INTO DATABASE** (Stored strictly in `data/raw/higher_studies/` for reference).

---

## 1. Provenance & Nature of Records

Per the workbook's own `README` sheet:
> *"Green row = EXAMPLE row showing the expected format. Replace or delete it once real rows are added."*  
> *"Every row that states a date, fee, cut-off or pattern must have source_url, retrieved_on, cycle and verified."*

### Table-by-Table Data Classification

| File Path in `data/raw/` | Nature of Data | Workbook Citation / Evidence | Treatment in Project |
|---|---|---|---|
| `data/raw/higher_studies/students.csv` | **Sample / Template Example** | Row contains dummy record `id = S-EX1` (*"Student Example 1"*). Matches the green example formatting. | **Not a real student record.** Will NEVER be treated as student data. |
| `data/raw/higher_studies/survey_responses.csv` | **Empty Template** | Header only (`response_id, branch, year, answers_json, submitted_on`), 0 data rows. | **Zero survey results.** |
| `data/raw/higher_studies/Survey.csv` | **Instrument Definition** | 35 structured questions across 7 sections + 5 interview follow-up prompts. | **Questionnaire instrument**, not student responses. |
| `data/raw/higher_studies/study_plans.csv` | **Sample / Template Example** | Row contains `student_id = S-EX1`, linking to the example student. | **Demonstration plan template**, not an active student plan. |

---

## 2. Hard Policy Binding

1. **Zero Database Insertion:** None of these tables are loaded into the PostgreSQL database (`kb`, `student`, `plan`, `ops`).
2. **Zero Fabrication:** Neither `S-EX1` nor any sample row shall be presented as real student data or survey findings for IIT Bhubaneswar.
3. **Seed Directory Purged:** `data/seed/higher_studies/` has been permanently deleted from disk.

