# How to Add a Persona Plugin

This guide walks teammates through creating and testing a new career or academic persona (e.g., `ee_embedded_vlsi`, `mme_materials_design`). Because personas are modular plugins, **adding a persona requires editing ZERO shared core files**.

---

## Step 1: Scaffold the Persona Directory

Run the scaffolding tool:
```powershell
# On Windows
.\scripts\dev.ps1 new-persona ee_embedded_vlsi

# On Linux/macOS
./scripts/new_persona.sh ee_embedded_vlsi
```

This creates the complete persona template in:
```
app/personas/ee_embedded_vlsi/
  ├── persona.yaml        # Metadata, goal id, applicable programmes
  ├── requirements.yaml   # Required skills and target competency thresholds
  ├── mastery.yaml        # Mastery demonstration criteria
  ├── milestones.yaml     # Semestral milestone roadmap
  ├── diagnostic.yaml     # Blueprint for adaptive diagnostic
  ├── policy.py           # Optional engine hooks (weights, preferences)
  └── README.md           # Rationale, survey evidence, trade-offs
```
and its seed folder:
```
data/seed/personas/ee_embedded_vlsi/
  ├── students.csv        # Synthetic profiles (is_synthetic=true)
  ├── exercises.json      # Persona-specific practice exercises
  └── resources.csv       # Targeted open courseware links
```

---

## Step 2: Define the Goal & Competencies

1. **`persona.yaml`**: Set `goal_id` to match an existing KB goal or a new track.
2. **`requirements.yaml`**: List competencies required for this persona and their target proficiency levels (0-100 scale):
   ```yaml
   requirements:
     - skill_id: SKILL_DIGITAL_SYSTEMS
       required_level: 80.0
       importance: 1.0
     - skill_id: SKILL_VLSI_DESIGN
       required_level: 85.0
       importance: 1.0
   ```
3. **`mastery.yaml`**: Define what separates mere course completion from verified proficiency (e.g. project demonstration, minimum proctored test score).

---

## Step 3: Configure Adaptive Diagnostic Blueprint

In `diagnostic.yaml`, specify the skills and difficulty ranges to evaluate during onboarding:
```yaml
blueprint:
  target_skills:
    - SKILL_DIGITAL_SYSTEMS
    - SKILL_MICROPROCESSORS
  questions_per_skill: 2
  difficulty_range: [0.3, 0.8]
```

---

## Step 4: Add Synthetic Profiles

In `data/seed/personas/<persona_id>/students.csv`, define at least 2 synthetic student profiles to test corner cases:
- A regular student on track.
- An edge case student (e.g. with low CGPA, backlogs, or tight credit caps).

> **IMPORTANT:** Ensure `is_synthetic` is set to `true` on every synthetic profile. Never use real student roll numbers or names.

---

## Step 5: Verify with the Conformance Suite

Every persona must pass the 8 automated conformance checks:
```powershell
.\scripts\dev.ps1 conformance
```

The conformance runner validates that:
1. Valid academic plan is produced.
2. All cited courses exist and prerequisites are recursively satisfied in topological order.
3. No pre-mastered courses are scheduled.
4. All gap skills are covered.
5. Active practice exercises are provided.
6. Adaptation works on simulated score changes.
7. Plan generation is deterministic.
8. Unachievable requests (e.g. credit cap violation) trigger a clear refusal and valid alternative.

Once all 8 checks pass, open a PR with the branch name `persona/<persona_id>`!

