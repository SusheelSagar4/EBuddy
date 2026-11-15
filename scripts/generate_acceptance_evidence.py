import os
import csv
import json
from app.contracts.student import StudentProfile, Constraint
from app.contracts.goal import Goal, GoalRequirement
from app.engine.planner import Planner
from app.engine.gaps import GapAnalyzer
from app.personas.registry import persona_registry

persona_registry.discover()
planner = Planner()
gap_analyzer = GapAnalyzer()

def load_profile(persona_id, student_id):
    csv_path = os.path.join("data", "seed", "personas", persona_id, "students.csv")
    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        if r["student_id"].strip() == student_id:
            completed = [c.strip() for c in r.get("completed_courses", "").split(";") if c.strip()]
            stu = StudentProfile(
                student_id=r["student_id"].strip(),
                name=r["name"].strip(),
                programme_id=r["programme_id"].strip(),
                current_semester=int(r["current_semester"]),
                cgpa=float(r["cgpa"]) if r.get("cgpa") else 8.0,
                backlogs=int(r.get("backlogs", 0)),
                is_synthetic=True
            )
            return stu, completed
    raise ValueError(f"Student {student_id} not found in {csv_path}")

print("================================================================================")
print("ACCEPTANCE EVIDENCE 1: EE Profile (Goal: Power Systems Engineering)")
print("Profile: CONF_STU_EE_POWER_01 | Goal: GOAL_EE_CORE_POWER")
print("================================================================================")
stu1, comp1 = load_profile("ee_power_core", "CONF_STU_EE_POWER_01")
pkg1 = persona_registry.get("ee_power_core")
goal1 = Goal(goal_id="GOAL_EE_CORE_POWER", name="Power Systems Engineering", category="career", description="Core Power Systems", source_id="RAW")
reqs1 = [GoalRequirement(goal_id=goal1.goal_id, skill_id=r["skill_id"], required_level=float(r["required_level"]), source_id="RAW") for r in pkg1.requirements]
gaps1 = gap_analyzer.analyze_gaps(goal1, reqs1, [])
plan1 = planner.generate_plan(stu1, goal1, gaps1, [], [], completed_course_ids=comp1)

print(f"\n[Plan Summary] ID: {plan1.plan_id} | Version: {plan1.version} | Student: {plan1.student_id} | Goal: {plan1.goal_id}")
print(f"Horizon Deadline: {plan1.timeline_roadmap.horizon_deadline}")

print("\n--- A. REQUIRED Degree Core Courses (Locked Commitments) ---")
for it in plan1.required_courses:
    print(f"  • [{it.status_badge}] {it.course_id} (Sem {it.semester_number}) - {it.hours_per_week} hrs/wk | Title: {it.reason.intent}")
    if it.goal_emphasis:
        print(f"    └─ Emphasis: {it.goal_emphasis}")

print("\n--- B. RECOMMENDED Elective Picks & Supplementary Tasks ---")
for it in plan1.recommended_items:
    cid_str = it.course_id or it.slot_id or it.resource_id or it.exercise_id or it.item_id
    print(f"  • [{it.status_badge}] {it.item_type}: {cid_str} - {it.hours_per_week} hrs/wk | Gap Closed: {it.skill_gap_reason or it.reason.intent}")

print("\n================================================================================")
print("ACCEPTANCE EVIDENCE 2: EE Profile Pivoted to SDE (Goal: SDE / Data Engineering)")
print("Profile: CONF_STU_EE_EDGE_GOAL_PIVOT | Goal: GOAL_CROSS_SDE_DATA")
print("================================================================================")
stu2, comp2 = load_profile("ee_power_core", "CONF_STU_EE_EDGE_GOAL_PIVOT")
goal2 = Goal(goal_id="GOAL_CROSS_SDE_DATA", name="Software Development & Data Engineering", category="career", description="SDE Track", source_id="RAW")
reqs2 = [
    GoalRequirement(goal_id=goal2.goal_id, skill_id="SKILL_PROGRAMMING_DS", required_level=85.0, source_id="RAW"),
    GoalRequirement(goal_id=goal2.goal_id, skill_id="SKILL_DATA_STRUCTURES_ALGO", required_level=85.0, source_id="RAW"),
    GoalRequirement(goal_id=goal2.goal_id, skill_id="SKILL_DATABASES_SQL", required_level=80.0, source_id="RAW"),
    GoalRequirement(goal_id=goal2.goal_id, skill_id="SKILL_AI_ML", required_level=80.0, source_id="RAW")
]
gaps2 = gap_analyzer.analyze_gaps(goal2, reqs2, [])
plan2 = planner.generate_plan(stu2, goal2, gaps2, [], [], completed_course_ids=comp2)

print(f"\n[Plan Summary] ID: {plan2.plan_id} | Version: {plan2.version} | Student: {plan2.student_id} | Goal: {plan2.goal_id}")
print(f"Horizon Deadline: {plan2.timeline_roadmap.horizon_deadline}")

print("\n--- A. REQUIRED Degree Core Courses (Locked Commitments) ---")
for it in plan2.required_courses:
    print(f"  • [{it.status_badge}] {it.course_id} (Sem {it.semester_number}) - {it.hours_per_week} hrs/wk | Title: {it.reason.intent}")
    if it.goal_emphasis:
        print(f"    └─ Emphasis: {it.goal_emphasis}")

print("\n--- B. RECOMMENDED Elective Picks & SDE Supplementary Tasks ---")
for it in plan2.recommended_items:
    cid_str = it.course_id or it.slot_id or it.resource_id or it.exercise_id or it.item_id
    print(f"  • [{it.status_badge}] {it.item_type}: {cid_str} - {it.hours_per_week} hrs/wk | Gap Closed: {it.skill_gap_reason or it.reason.intent}")

print("\n================================================================================")
print("ACCEPTANCE EVIDENCE 3: MME Profile (Goal: Metallurgical Process Engineer)")
print("Profile: CONF_STU_MME_PROCESS_01 | Goal: GOAL_MM_PROCESS_ENGINEER")
print("================================================================================")
stu3, comp3 = load_profile("mme_materials_core", "CONF_STU_MME_PROCESS_01")
pkg3 = persona_registry.get("mme_materials_core")
goal3 = Goal(goal_id="GOAL_MM_PROCESS_ENGINEER", name="Metallurgical Process Engineer", category="career", description="Core MME", source_id="RAW")
reqs3 = [GoalRequirement(goal_id=goal3.goal_id, skill_id=r["skill_id"], required_level=float(r["required_level"]), source_id="RAW") for r in pkg3.requirements]
gaps3 = gap_analyzer.analyze_gaps(goal3, reqs3, [])
plan3 = planner.generate_plan(stu3, goal3, gaps3, [], [], completed_course_ids=comp3)

print(f"\n[Plan Summary] ID: {plan3.plan_id} | Version: {plan3.version} | Student: {plan3.student_id} | Goal: {plan3.goal_id}")
print(f"Horizon Deadline: {plan3.timeline_roadmap.horizon_deadline}")

print("\n--- A. REQUIRED Degree Core Courses (Locked Commitments) ---")
for it in plan3.required_courses:
    print(f"  • [{it.status_badge}] {it.course_id} (Sem {it.semester_number}) - {it.hours_per_week} hrs/wk | Title: {it.reason.intent}")
    if it.goal_emphasis:
        print(f"    └─ Emphasis: {it.goal_emphasis}")

print("\n--- B. RECOMMENDED Elective Picks (with Pool Rule Unknown handling) ---")
for it in plan3.recommended_items:
    cid_str = it.course_id or it.slot_id or it.resource_id or it.exercise_id or it.item_id
    pool_str = f" [Tag: {it.pool_rule_status}]" if it.pool_rule_status else ""
    print(f"  • [{it.status_badge}]{pool_str} {it.item_type}: {cid_str} - {it.hours_per_week} hrs/wk | Gap Closed: {it.skill_gap_reason or it.reason.intent}")

print("\n================================================================================")
print("ACCEPTANCE EVIDENCE 4: Weekly Plan Snippet (Next 4 Weeks Operational Window)")
print("Profile: CONF_STU_EE_POWER_01")
print("================================================================================")
for w_item in plan1.next_4_weeks:
    ind_str = " (indicative)" if w_item.is_indicative else ""
    kb_str = f" | Cited KB: {w_item.cited_kb_codes}" if w_item.cited_kb_codes else ""
    print(f"  Week {w_item.week_index}: [{w_item.status_badge}] {w_item.item_type} - '{w_item.title}' ({w_item.hours_per_week} hrs/wk){ind_str}{kb_str}")

print("\n================================================================================")
print("ACCEPTANCE EVIDENCE 5: Extra Workload Cap Exceeded Shedding")
print("Profile: CONF_STU_EE_POWER_01 with 12.0h Weekly Cap (Core load alone > 12h)")
print("================================================================================")
cap_constraint = Constraint(
    constraint_id="C_HOURS_12",
    student_id=stu1.student_id,
    constraint_type="weekly_hours",
    parameters={"max_hours": 12.0}
)
plan_overload = planner.generate_plan(stu1, goal1, gaps1, [cap_constraint], [], completed_course_ids=comp1)

print(f"Stated Weekly Hours Cap: 12.0 hrs/week")
req_h = sum(it.hours_per_week for it in plan_overload.required_courses if it.course_id)
extra_h = sum(it.hours_per_week for it in plan_overload.items if it not in plan_overload.required_courses)
print(f"Locked Required Core Hours: {req_h:.1f} hrs/week (PRESERVED - Never dropped)")
print(f"Supplementary Extras Hours: {extra_h:.1f} hrs/week (SHED / REDUCED FIRST)")
print(f"\nStudent-Facing Explanation:")
print(f"  \"{plan_overload.workload_cap_explanation}\"")
