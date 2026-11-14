import os
import csv
import uuid
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone
from app.contracts.student import StudentProfile, Constraint, Preference, SkillState
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

    def detect_interest_evidence_mismatch(
        self,
        student: StudentProfile,
        goal: Goal,
        states: List[SkillState],
        aims_text: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Detects mismatch between student's desired ambition/goal and actual tested evidence.
        Example: Student wants Power Electronics / Smart Grid, but is weak in Circuit Analysis.
        Or Student wants High-Entropy Alloys, but is weak in Physical Metallurgy or Thermodynamics.
        """
        state_map = {s.skill_id: s.estimated_level for s in states}
        aims_lower = ((aims_text or "") + " " + goal.name + " " + goal.description).lower()

        # EE Mismatch Rule: Wants Power Electronics / Smart Grid / Power Transmission, weak in Circuits
        if any(kw in aims_lower for kw in ["power electronics", "smart grid", "power system", "power transmission", "relay", "converter", "ev drive", "hvdc"]):
            circ_level = state_map.get("SKILL_CIRCUIT_ANALYSIS", 100.0)
            if circ_level < 75.0:
                return {
                    "mismatch_detected": True,
                    "target_interest": "Power Electronics & Energy Systems",
                    "missing_prerequisite": "SKILL_CIRCUIT_ANALYSIS",
                    "current_level": circ_level,
                    "required_level": 75.0,
                    "explanation": (
                        f"Interest vs. Evidence Mismatch Detected: You expressed strong ambition in Power Electronics & Energy Systems, "
                        f"but verified diagnostic evidence indicates your proficiency in Circuit Analysis is {circ_level:.1f}% (required: 75.0%). "
                        f"Circuit analysis theorems (KVL/KCL, Thevenin equivalent, AC steady-state and transient response) are strictly required "
                        f"before designing converter topologies. To safeguard your GPA and ensure genuine competence, your study roadmap has "
                        f"automatically prioritized Circuit Analysis foundations in Phase 1 before advancing to converter design."
                    ),
                    "tradeoff": "Prioritized prerequisite Circuit Analysis remediation over premature advanced converter modeling."
                }

        # MM Mismatch Rule: Wants Advanced Alloys / Materials Processing, weak in Metallurgy/Thermodynamics
        if any(kw in aims_lower for kw in ["materials", "alloy", "processing", "nanomaterial", "additive", "steel", "rolling", "extractive", "metallurgy"]):
            phys_level = state_map.get("SKILL_PHYSICAL_METALLURGY", 100.0)
            therm_level = state_map.get("SKILL_THERMODYNAMICS_MAT", 100.0)
            if phys_level < 75.0:
                return {
                    "mismatch_detected": True,
                    "target_interest": "Advanced Alloy Design & Materials Processing",
                    "missing_prerequisite": "SKILL_PHYSICAL_METALLURGY",
                    "current_level": phys_level,
                    "required_level": 75.0,
                    "explanation": (
                        f"Interest vs. Evidence Mismatch Detected: You expressed strong ambition in Advanced Alloy Design, "
                        f"but verified diagnostic evidence indicates your proficiency in Physical Metallurgy is {phys_level:.1f}% (required: 75.0%). "
                        f"Phase diagrams, Fe-C transformations, and crystallographic defect mechanics are essential foundations before exploring alloy design. "
                        f"Your study roadmap has automatically prioritized Physical Metallurgy core principles in Phase 1."
                    ),
                    "tradeoff": "Prioritized foundational Physical Metallurgy concepts before advanced high-entropy alloy tasks."
                }
            elif therm_level < 70.0:
                return {
                    "mismatch_detected": True,
                    "target_interest": "Materials Processing & Extraction",
                    "missing_prerequisite": "SKILL_THERMODYNAMICS_MAT",
                    "current_level": therm_level,
                    "required_level": 70.0,
                    "explanation": (
                        f"Interest vs. Evidence Mismatch Detected: You expressed ambition in Materials Processing, "
                        f"but your verified proficiency in Thermodynamics of Materials is {therm_level:.1f}% (required: 70.0%). "
                        f"Ellingham diagrams and Gibbs free energy criteria must be mastered before modeling high-temperature processing. "
                        f"Your roadmap has prioritized Thermodynamics foundations in Phase 1."
                    ),
                    "tradeoff": "Prioritized prerequisite Thermodynamics of Materials review over advanced processing simulations."
                }

        return None

    def calculate_adaptive_phase_weeks(self, gaps: List[Dict[str, Any]], skill_states: Optional[List[SkillState]] = None) -> Dict[str, str]:
        """
        Dynamically adapts phase week spans based on student competency and progress:
        - High proficiency (avg >= 80%): Compresses Phase 1 to Weeks 1-2, expands Phase 2 to Weeks 3-8, Phase 3 to Weeks 9-16.
        - Remedial / Gaps (avg < 60%): Expands Phase 1 to Weeks 1-6, Phase 2 to Weeks 7-12, Phase 3 to Weeks 13-16+.
        - Balanced (60%-80%): Phase 1 (Weeks 1-4), Phase 2 (Weeks 5-10), Phase 3 (Weeks 11-16).
        """
        if skill_states:
            avg_score = sum(s.estimated_level for s in skill_states) / len(skill_states)
        else:
            avg_gap = sum(g.get("gap", 0) for g in gaps) / (len(gaps) or 1)
            avg_score = max(30.0, 100.0 - avg_gap)

        if avg_score >= 80.0:
            return {
                "phase_1": "Phase 1: Foundation (Weeks 1–2 Accelerated)",
                "phase_2": "Phase 2: Core Depth (Weeks 3–8)",
                "phase_3": "Phase 3: Applied Mastery (Weeks 9–16)"
            }
        elif avg_score < 60.0:
            return {
                "phase_1": "Phase 1: Foundation (Weeks 1–6 Extended Remediation)",
                "phase_2": "Phase 2: Core Depth (Weeks 7–12)",
                "phase_3": "Phase 3: Applied Mastery (Weeks 13–16+)"
            }
        else:
            return {
                "phase_1": "Phase 1: Foundation (Weeks 1–4)",
                "phase_2": "Phase 2: Core Depth (Weeks 5–10)",
                "phase_3": "Phase 3: Applied Mastery (Weeks 11–16)"
            }

    def generate_plan(
        self,
        student: StudentProfile,
        goal: Goal,
        gaps: List[Dict[str, Any]],
        constraints: List[Constraint],
        preferences: List[Preference],
        completed_course_ids: Optional[List[str]] = None,
        skill_states: Optional[List[SkillState]] = None,
        aims_text: Optional[str] = None,
        version: int = 1
    ) -> Plan:
        items: List[PlanItem] = []
        assigned_courses = set(completed_course_ids or [])
        current_sem = student.current_semester

        # 1. Determine adaptive phase weeks based on evidence
        phase_labels = self.calculate_adaptive_phase_weeks(gaps, skill_states)
        p1_label = phase_labels["phase_1"]
        p2_label = phase_labels["phase_2"]
        p3_label = phase_labels["phase_3"]

        # 2. Check for Interest vs. Evidence Mismatch
        mismatch = self.detect_interest_evidence_mismatch(
            student=student,
            goal=goal,
            states=skill_states or [],
            aims_text=aims_text
        )

        # If mismatch detected, inject high-priority remedial foundation course/exercise in Phase 1
        if mismatch:
            missing_skill = mismatch["missing_prerequisite"]
            remedial_cid = "EE2L001" if "CIRCUIT" in missing_skill else "ML2L002"
            items.append(PlanItem(
                item_id=f"ITEM_REM_PREREQ_{missing_skill}_{uuid.uuid4().hex[:4]}",
                item_type="remediation",
                course_id=remedial_cid,
                semester_number=current_sem,
                estimated_hours=4.0,
                phase=p1_label,
                prep_hours_weekly=6.0,
                reason=StructuredReason(
                    intent=f"[{p1_label}] Address Interest vs. Evidence Gap in {missing_skill}",
                    target_skills=[missing_skill],
                    why_this=mismatch["explanation"],
                    prerequisite_for=[goal.name],
                    rule_compliance=["Academic load managed; prerequisite gap resolved before advanced topics"]
                )
            ))

        # 3. Address major skill gaps with courses (respecting prerequisite topology)
        for g in gaps:
            if g["gap"] <= 0:
                continue
            sid = g["skill_id"]
            candidate_courses = self.skill_courses.get(sid, [])
            for cid in candidate_courses:
                if cid not in assigned_courses:
                    # Resolve prerequisites first (Phase 1)
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
                                phase=p1_label,
                                prep_hours_weekly=6.0,
                                reason=StructuredReason(
                                    intent=f"[{p1_label}] Prerequisite foundation for {cid}",
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
                        why_reason = f"[{p2_label}] Addresses priority gap in {sid}. Note: {disp_code} has code conflict in catalog ('{both_titles}')."
                    else:
                        why_reason = f"[{p2_label}] Addresses priority gap ({g['gap']} points) in {sid} required for {goal.name}."

                    items.append(PlanItem(
                        item_id=f"ITEM_C_{cid}_{uuid.uuid4().hex[:6]}",
                        item_type="course",
                        course_id=cid,
                        semester_number=current_sem,
                        estimated_hours=4.0,
                        phase=p2_label,
                        prep_hours_weekly=8.0,
                        reason=StructuredReason(
                            intent=f"[{p2_label}] Close gap in {sid}",
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
                        phase=p2_label,
                        prep_hours_weekly=3.0,
                        reason=StructuredReason(
                            intent=f"[{p2_label}] Active practice for {sid}",
                            target_skills=[sid],
                            why_this=f"Active problem solving and check-in tasks to demonstrate proficiency in {sid}.",
                            prerequisite_for=[],
                            rule_compliance=[]
                        )
                    ))
                    break # Take top match per skill gap

        # 4. Add Phase 3: Applied Mastery milestone
        items.append(PlanItem(
            item_id=f"ITEM_MS_{uuid.uuid4().hex[:6]}",
            item_type="milestone",
            semester_number=current_sem,
            estimated_hours=0.0,
            phase=p3_label,
            prep_hours_weekly=4.0,
            reason=StructuredReason(
                intent=f"[{p3_label}] Goal Mastery Demonstration",
                target_skills=[g["skill_id"] for g in gaps[:3]],
                why_this=f"Demonstrate verified proficiency through capstone project and timed mock interviews for {goal.name}.",
                prerequisite_for=[],
                rule_compliance=[]
            )
        ))

        plan = Plan(
            plan_id=f"PLAN_{student.student_id}_{uuid.uuid4().hex[:8]}",
            student_id=student.student_id,
            goal_id=goal.goal_id,
            version=version,
            items=items,
            mismatch_warning=mismatch,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        return plan
