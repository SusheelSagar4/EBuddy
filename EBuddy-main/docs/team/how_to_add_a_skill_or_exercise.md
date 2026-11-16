# How to Add a Skill or Practice Exercise

This guide details how to extend knowledge-base skills, course-skill mappings, and practice exercises while preserving strict institutional provenance.

---

## 1. Adding a Knowledge Base Skill

Skills represent granular competencies (e.g. `SKILL_FOURIER_ANALYSIS`, `SKILL_POWDER_METALLURGY`).
To register a new skill:
1. Open `data/seed/kb/skill.csv`.
2. Add a row following the standard schema:
   - `skill_id`: Uppercase identifier prefixed with `SKILL_` (e.g. `SKILL_DIGITAL_FILTER_DESIGN`).
   - `name`: Human-readable name.
   - `domain`: Sub-discipline (e.g., `Signal Processing`, `Physical Metallurgy`).
   - `description`: Granular description of the competency.
   - `level_scale`: Scale identifier (default: `0-100`).
   - `status`: Either `draft_for_review` (if authored by design team) or `verified` (if sourced directly from an official syllabus).
   - `source_id`: Attribution source (`DESIGN_TEAM` or official source ID from `source.csv`).

---

## 2. Mapping Skills to Courses

1. Open `data/seed/kb/course_skill.csv`.
2. Map the course surrogate `course_id` to the `skill_id`:
   - `mapping_id`: Unique identifier (e.g., `CSK_EE_301`).
   - `course_id`: Target course surrogate (e.g., `EE3L001_EE`).
   - `skill_id`: Target skill (e.g., `SKILL_ELECTRIC_MACHINES`).
   - `contribution_level`: Weight from `0.0` to `1.0`.
   - `mapping_method`: **Must be `inferred_from_course_title`** unless official syllabus text is ingested.
   - `status`: `draft_for_review` or `verified`.
   - `source_id`: Attribution ID.

---

## 3. Adding Active Practice Exercises

Practice exercises drive the **Assess → Learn → Practise → Adapt** loop.
Exercises can be added globally to `data/seed/kb/exercise.json` or to persona-specific files in `data/seed/personas/<persona_id>/exercises.json`.

### Schema Example:
```json
{
  "exercise_id": "EX_MACHINES_04",
  "skill_id": "SKILL_ELECTRIC_MACHINES",
  "title": "Transformer Voltage Regulation Calculation",
  "prompt": "A 10 kVA, 2000/200 V single-phase transformer has R1 = 2.5 Ω, X1 = 4.2 Ω, R2 = 0.025 Ω, and X2 = 0.042 Ω. Determine the equivalent impedance referred to the primary side.",
  "exercise_type": "numerical",
  "difficulty": 0.6,
  "options": null,
  "correct_answer": "5.0 + j8.4",
  "tolerance": 0.05,
  "explanation": "Primary equivalent resistance Req1 = R1 + R2*(N1/N2)^2 = 2.5 + 0.025*(10)^2 = 5.0 Ω. Equivalent reactance Xeq1 = X1 + X2*(N1/N2)^2 = 4.2 + 0.042*(10)^2 = 8.4 Ω.",
  "status": "draft_for_review",
  "source_id": "DESIGN_TEAM"
}
```

### Deterministic vs Generative Grading:
- **MCQ & Numerical Questions:** Graded deterministically by `app/engine/diagnostic.py` and `app/engine/mastery.py` without LLM calls.
- **Short Answer / Conceptual Questions:** Evaluated by `app/llm/tasks/grader.py` against a strict rubric. In test environments, `FakeLLM` provides deterministic evaluations.

