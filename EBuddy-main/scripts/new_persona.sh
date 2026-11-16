#!/usr/bin/env bash
set -e

PERSONA_ID="$1"
if [ -z "$PERSONA_ID" ]; then
    echo "Usage: ./scripts/new_persona.sh <persona_id>"
    exit 1
fi

TARGET_DIR="app/personas/$PERSONA_ID"
SEED_DIR="data/seed/personas/$PERSONA_ID"

if [ -d "$TARGET_DIR" ]; then
    echo "Error: Persona folder '$TARGET_DIR' already exists!"
    exit 1
fi

mkdir -p "$TARGET_DIR/prompts"
mkdir -p "$SEED_DIR"

cat <<EOF > "$TARGET_DIR/persona.yaml"
persona_id: "$PERSONA_ID"
goal_id: "GOAL_${PERSONA_ID^^}"
description: "TODO: Describe the student archetype and career trajectory."
applicable_programmes:
  - "BTECH_EE"
target_semester_range: [3, 8]
eligibility_notes: "TODO: Minimum CGPA or prerequisite requirements."
planner_weights:
  cgpa_protection: 0.7
  skill_acceleration: 0.8
  workload_smoothing: 0.6
status: "draft_for_review"
EOF

cat <<EOF > "$TARGET_DIR/requirements.yaml"
- skill_id: "SKILL_CIRCUIT_ANALYSIS"
  required_level: 80.0
  importance: 1.0
- skill_id: "SKILL_POWER_ELECTRONICS"
  required_level: 75.0
  importance: 0.9
EOF

cat <<EOF > "$TARGET_DIR/mastery.yaml"
criteria_id: "MASTERY_${PERSONA_ID^^}"
goal_id: "GOAL_${PERSONA_ID^^}"
criteria:
  min_skill_level: 75.0
  required_project_milestones: 1
  required_timed_assessments: 2
  min_diagnostic_score: 70.0
EOF

cat <<EOF > "$TARGET_DIR/milestones.yaml"
- semester_target: 5
  title: "Core Domain Mini-Project"
  description: "Complete independent design and simulation project."
- semester_target: 7
  title: "Industry Internship / Capstone Selection"
  description: "Secure domain-relevant summer internship."
EOF

cat <<EOF > "$TARGET_DIR/diagnostic.yaml"
blueprint:
  target_skills:
    - "SKILL_CIRCUIT_ANALYSIS"
    - "SKILL_POWER_ELECTRONICS"
  item_counts: 5
  difficulty_range: [40.0, 85.0]
EOF

cat <<EOF > "$TARGET_DIR/policy.py"
from app.personas.policy import PersonaPolicy

class CustomPersonaPolicy(PersonaPolicy):
    """Custom policy hooks for $PERSONA_ID."""
    pass
EOF

cat <<EOF > "$TARGET_DIR/README.md"
# Persona Specification: $PERSONA_ID

## 1. Who This Persona Is
TODO: Characterize this student persona.
EOF

echo "Scaffolded persona plugin successfully at $TARGET_DIR"

