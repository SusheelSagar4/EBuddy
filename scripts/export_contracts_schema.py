import os
import sys
import json

sys.path.insert(0, os.path.abspath("."))

from app.contracts import (
    StudentProfile, EvidenceItem, SkillState, Constraint, Preference,
    Goal, GoalRequirement, MasteryCriteria, Milestone,
    Course, Module, Resource, Exercise, AcademicRule, ResearchProject, Skill,
    Plan, PlanItem, ValidationReport, PlanDiff,
    Intent, ContextCard, ChatTurn, Explanation,
    PersonaSpec
)

def export_schemas():
    out_dir = os.path.join("docs", "contracts")
    os.makedirs(out_dir, exist_ok=True)

    models = [
        StudentProfile, EvidenceItem, SkillState, Constraint, Preference,
        Goal, GoalRequirement, MasteryCriteria, Milestone,
        Course, Module, Resource, Exercise, AcademicRule, ResearchProject, Skill,
        Plan, PlanItem, ValidationReport, PlanDiff,
        ContextCard, ChatTurn, Explanation,
        PersonaSpec
    ]

    for model in models:
        schema = model.model_json_schema()
        file_path = os.path.join(out_dir, f"{model.__name__}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)
        print(f"Exported {file_path}")

    print(f"Successfully exported {len(models)} contract JSON schemas to {out_dir}/")

if __name__ == "__main__":
    export_schemas()
