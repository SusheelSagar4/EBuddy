import os
import csv
import uuid
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone
from app.contracts.student import StudentProfile, Constraint, Preference
from app.contracts.goal import Goal
from app.contracts.plan import Plan, PlanItem, StructuredReason
from app.engine.interfaces import IPlanner
from app.engine.rules import RuleEngine

class Planner(IPlanner):
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self.rule_engine = RuleEngine(seed_dir)
        self.course_skills: Dict[str, List[str]] = {} # course_id -> [skill_id]
        self.skill_courses: Dict[str, List[str]] = {} # skill_id -> [course_id]
        self.course_info: Dict[str, Dict[str, Any]] = {}
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        # 1. Course skills
        cs_file = os.path.join(self.seed_dir, "course_skill.csv")
        if os.path.exists(cs_file):
            with open(cs_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    cid = r["course_id"].strip()
                    sid = r["skill_id"].strip()
                    self.course_skills.setdefault(cid, []).append(sid)
                    self.skill_courses.setdefault(sid, []).append(cid)

        # 2. Courses
        c_file = os.path.join(self.seed_dir, "course.csv")
        if os.path.exists(c_file):
            with open(c_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    self.course_info[r["course_id"]] = {
                        "credits": float(r.get("credits", 4.0)),
                        "title": r.get("title", ""),
                        "display_code": r.get("display_code", ""),
                        "code_conflict": r.get("code_conflict", "false").lower() == "true",
                        "status": r.get("status", "verified")
                    }

    def _get_prereq_chain(self, course_id: str, visited: Optional[Set[str]] = None) -> List[str]:
        if visited is None:
            visited = set()
        chain = []
        visited.add(course_id)
        prereqs = self.rule_engine.prereqs.get(course_id, set())
        for p in sorted(prereqs):
            if p not in visited and p in self.course_info:
                chain.extend(self._get_prereq_chain(p, visited))
                chain.append(p)
        return chain

    def generate_plan(
        self,
        student: StudentProfile,
        goal: Goal,
        gaps: List[Dict[str, Any]],
        constraints: List[Constraint],
        preferences: List[Preference],
        completed_course_ids: Optional[List[str]] = None
    ) -> Plan:
        items: List[PlanItem] = []
        assigned_courses = set(completed_course_ids or [])
        current_sem = student.current_semester

        # 1. Address major skill gaps with courses (respecting prerequisite topology)
        for g in gaps:
            if g["gap"] <= 0:
                continue
            sid = g["skill_id"]
            candidate_courses = self.skill_courses.get(sid, [])
            for cid in candidate_courses:
                if cid not in assigned_courses:
                    # Resolve prerequisites first
                    prereq_chain = self._get_prereq_chain(cid)
                    for pid in prereq_chain:
                        if pid not in assigned_courses:
                            assigned_courses.add(pid)
                            items.append(PlanItem(
                                item_id=f"ITEM_C_{pid}_{uuid.uuid4().hex[:6]}",
                                item_type="course",
                                course_id=pid,
                                semester_number=current_sem,
                                estimated_hours=4.0,
                                reason=StructuredReason(
                                    intent=f"Prerequisite foundation for {cid}",
                                    target_skills=self.course_skills.get(pid, [sid]),
                                    why_this=f"Required prerequisite foundation before taking {cid}.",
                                    prerequisite_for=[cid],
                                    rule_compliance=["Satisfies prerequisite chain"]
                                )
                            ))

                    assigned_courses.add(cid)
                    c_meta = self.course_info.get(cid, {})
                    is_conflict = c_meta.get("code_conflict", False)
                    c_title = c_meta.get("title", cid)
                    disp_code = c_meta.get("display_code", cid)

                    if is_conflict:
                        conflicting = [info["title"] for info in self.course_info.values() if info.get("display_code") == disp_code]
                        both_titles = " / ".join(conflicting)
                        why_reason = f"Addresses priority gap in {sid} [DRAFT FOR REVIEW]. Note: {disp_code} has code conflict in catalog ('{both_titles}')."
                    else:
                        why_reason = f"Addresses priority gap ({g['gap']} points) in {sid} [DRAFT FOR REVIEW] required for {goal.name}."

                    items.append(PlanItem(
                        item_id=f"ITEM_C_{cid}_{uuid.uuid4().hex[:6]}",
                        item_type="course",
                        course_id=cid,
                        semester_number=current_sem,
                        estimated_hours=4.0,
                        reason=StructuredReason(
                            intent=f"Close gap in {sid}",
                            target_skills=[sid],
                            why_this=why_reason,
                            prerequisite_for=[],
                            rule_compliance=["Complies with offering and credit limits [UNSOURCED BASELINE]"]
                        )
                    ))
                    # Add practice exercise
                    items.append(PlanItem(
                        item_id=f"ITEM_EX_{cid}_{uuid.uuid4().hex[:6]}",
                        item_type="exercise",
                        course_id=cid,
                        semester_number=current_sem,
                        estimated_hours=2.0,
                        reason=StructuredReason(
                            intent=f"Active practice for {sid}",
                            target_skills=[sid],
                            why_this=f"Active problem solving to demonstrate proficiency in {sid}.",
                            prerequisite_for=[],
                            rule_compliance=[]
                        )
                    ))
                    break # Take top match per skill gap

        # 2. Add milestone
        items.append(PlanItem(
            item_id=f"ITEM_MS_{uuid.uuid4().hex[:6]}",
            item_type="milestone",
            semester_number=current_sem,
            estimated_hours=0.0,
            reason=StructuredReason(
                intent="Semester Target Milestone",
                target_skills=[g["skill_id"] for g in gaps[:3]],
                why_this=f"Core milestone for goal {goal.name}.",
                prerequisite_for=[],
                rule_compliance=[]
            )
        ))

        plan = Plan(
            plan_id=f"PLAN_{student.student_id}_{uuid.uuid4().hex[:8]}",
            student_id=student.student_id,
            goal_id=goal.goal_id,
            version=1,
            items=items,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        return plan
