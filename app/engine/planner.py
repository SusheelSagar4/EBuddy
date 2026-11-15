import os
import csv
import uuid
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timezone
from app.contracts.student import StudentProfile, Constraint, Preference, SkillState
from app.contracts.goal import Goal
from app.contracts.plan import (
    Plan, PlanItem, StructuredReason,
    WeeklyScheduleItem, MonthlyTheme, SemesterBlock, TimelineRoadmap
)
from app.config import settings
from app.engine.interfaces import IPlanner
from app.engine.rules import RuleEngine
from app.engine.relevance import CourseRelevanceEngine
from app.kb.repositories import ResourceRepo

logger = logging.getLogger(__name__)

class Planner(IPlanner):
    """
    Deterministic Academic Planner Engine.
    
    Principles:
    1. Python decides curriculum and rules; LLM/Agents explain and propose.
    2. Major/Core courses are determined by branch curriculum (programme_requirement.csv) and are FIXED.
       They are never excluded or ranked out by career relevance scores.
    3. Electives and Lateral slots are recommendation candidates ranked via CourseRelevanceEngine
       (0-3 scale + skill gap boost) strictly respecting prerequisite gating.
    4. Minor track is recommended only when student satisfies academic eligibility (Sem >= 5, CGPA >= 8.0, 0 backlogs)
       and within credit cap.
    5. Resources are relationally retrieved from verified knowledge base (resource_course.csv -> resource.csv).
    """
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self.rule_engine = RuleEngine(seed_dir)
        self.relevance_engine = CourseRelevanceEngine(seed_dir)
        self.resource_repo = ResourceRepo(seed_dir)
        self.course_skills: Dict[str, List[str]] = {} # course_id -> [skill_id]
        self.skill_courses: Dict[str, List[str]] = {} # skill_id -> [course_id]
        self.course_info: Dict[str, Dict[str, Any]] = {}
        self.prog_requirements: Dict[Tuple[str, int], List[Dict[str, Any]]] = {} # (prog_id, sem) -> [req_row]
        self.slot_options: Dict[str, List[str]] = {} # slot_id -> [course_id]
        self.minor_courses: Dict[str, List[str]] = {} # minor_id -> [course_id]
        self.academic_calendar: List[Dict[str, Any]] = []
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
                        "status": r.get("status", "verified"),
                        "department_id": r.get("department_id", "")
                    }

        # 3. Programme requirements
        pr_file = os.path.join(self.seed_dir, "programme_requirement.csv")
        if os.path.exists(pr_file):
            with open(pr_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    prog = r["programme_id"].strip().upper()
                    try:
                        sem = int(float(r["semester_number"]))
                    except (ValueError, TypeError):
                        continue
                    self.prog_requirements.setdefault((prog, sem), []).append(r)

        # 4. Slot options
        so_file = os.path.join(self.seed_dir, "slot_option.csv")
        if os.path.exists(so_file):
            with open(so_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    slot = r["slot_id"].strip()
                    cid = r["course_id"].strip()
                    self.slot_options.setdefault(slot, []).append(cid)

        # 5. Minor courses
        mc_file = os.path.join(self.seed_dir, "minor_course.csv")
        if os.path.exists(mc_file):
            with open(mc_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    mid = r["minor_id"].strip()
                    cid = r["course_id"].strip()
                    self.minor_courses.setdefault(mid, []).append(cid)

        # 6. Academic calendar (for verified dates and exam weeks)
        cal_file = os.path.join(os.path.dirname(self.seed_dir), "core_to_core", "academic_calendar.csv")
        if not os.path.exists(cal_file):
            cal_file = os.path.join("data", "seed", "core_to_core", "academic_calendar.csv")
        if os.path.exists(cal_file):
            with open(cal_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    self.academic_calendar.append(r)

    def _topological_sort_courses(self, course_ids: List[str]) -> List[str]:
        """Ensures courses within the same batch are ordered so prerequisites precede dependents."""
        c_set = set(course_ids)
        ordered = []
        visited = set()

        def visit(c):
            if c in visited:
                return
            visited.add(c)
            for p in self.rule_engine.prereqs.get(c, set()):
                if p in c_set:
                    visit(p)
            ordered.append(c)

        for c in course_ids:
            visit(c)
        return ordered

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
        state_map = {s.skill_id: s.estimated_level for s in states}
        aims_lower = ((aims_text or "") + " " + goal.name + " " + goal.description).lower()

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

        if any(kw in aims_lower for kw in ["high-entropy alloy", "aerospace titanium", "biomaterials", "superalloys", "nanomaterials", "corrosion"]):
            metal_level = state_map.get("SKILL_PHYSICAL_METALLURGY", 100.0)
            thermo_level = state_map.get("SKILL_THERMODYNAMICS", 100.0)
            if metal_level < 70.0 or thermo_level < 70.0:
                weak_skill = "SKILL_PHYSICAL_METALLURGY" if metal_level < 70.0 else "SKILL_THERMODYNAMICS"
                val = metal_level if metal_level < 70.0 else thermo_level
                return {
                    "mismatch_detected": True,
                    "target_interest": "Advanced Structural Alloys & High-Entropy Materials",
                    "missing_prerequisite": weak_skill,
                    "current_level": val,
                    "required_level": 70.0,
                    "explanation": (
                        f"Interest vs. Evidence Mismatch Detected: You have ambitious research aspirations in Advanced Materials Design, "
                        f"but diagnostic evidence shows foundational gaps in {weak_skill} ({val:.1f}% vs required 70.0%). "
                        f"Thermodynamic phase equilibria and dislocation theory are vital before attempting advanced multicomponent alloy formulation."
                    ),
                    "tradeoff": f"Scheduled foundational remediation in {weak_skill} prior to specialized alloy synthesis electives."
                }

        return None

    def calculate_adaptive_phase_weeks(self, gaps: List[Dict[str, Any]], skill_states: Optional[List[SkillState]] = None) -> Dict[str, str]:
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
        required_courses_list: List[PlanItem] = []
        recommended_items_list: List[PlanItem] = []
        completed_set = set(completed_course_ids or [])
        assigned_courses: Set[str] = set(completed_set)
        current_sem = student.current_semester

        # Normalize branch/programme code
        raw_prog = (student.programme_id or "").upper().strip()
        if raw_prog in ["BTECH_MME", "MME", "MM"]:
            prog_id = "BTECH_MM"
        elif raw_prog in ["BTECH_EE", "EE"]:
            prog_id = "BTECH_EE"
        else:
            prog_id = raw_prog

        if (completed_course_ids is None or student.backlogs == 0) and current_sem > 1:
            for s in range(1, current_sem):
                for r in self.prog_requirements.get((prog_id, s), []):
                    c = r.get("course_id", "").strip()
                    if c:
                        completed_set.add(c)
            if prog_id == "BTECH_EE":
                completed_set.update(["MA1L001", "MA1L002", "EE1L001", "CS1L001"])
            # Note: For BTECH_MM, Sem I-II is simply missing from official raw documents; no courses or completions are assumed.
            assigned_courses = set(completed_set)

        # Student-stated constraints (HARD bounds)
        student_credit_cap: Optional[float] = None
        student_headroom: float = 0.0
        student_weekly_hours: Optional[float] = None
        avoid_courses: Set[str] = set()
        not_together_pairs: List[Set[str]] = []

        for c in (constraints or []):
            if not getattr(c, "is_active", True):
                continue
            ctype = (getattr(c, "constraint_type", "") or "").lower()
            params = getattr(c, "parameters", {}) or {}

            if ctype in ["credit_cap", "max_credits"]:
                val = params.get("max_credits") or params.get("credit_cap") or params.get("credits") or params.get("value")
                if val is not None:
                    student_credit_cap = float(val)
            elif ctype == "headroom":
                val = params.get("headroom") or params.get("credit_headroom") or params.get("value")
                if val is not None:
                    student_headroom = float(val)
            elif ctype in ["weekly_hours", "max_weekly_hours", "study_hours"]:
                val = params.get("max_hours") or params.get("weekly_hours") or params.get("hours") or params.get("value")
                if val is not None:
                    student_weekly_hours = float(val)
            elif ctype in ["avoid_course", "avoid_courses"]:
                cid = params.get("course_id") or params.get("course")
                if cid:
                    avoid_courses.add(cid.strip())
                cids = params.get("courses") or params.get("course_ids")
                if isinstance(cids, list):
                    for x in cids:
                        avoid_courses.add(x.strip())
            elif ctype in ["not_together", "mutually_exclusive"]:
                pair = params.get("courses") or params.get("course_ids") or params.get("pair")
                if isinstance(pair, list):
                    not_together_pairs.append({x.strip() for x in pair})

        effective_student_credit_cap: Optional[float] = None
        if student_credit_cap is not None:
            effective_student_credit_cap = student_credit_cap - student_headroom
        elif student_headroom > 0.0:
            effective_student_credit_cap = 26.0 - student_headroom

        optional_overload_proposals: List[Dict[str, Any]] = []

        # Detect interest-vs-evidence conflict from gaps
        conflicted_skills = {g["skill_id"] for g in gaps if g.get("conflict_flag")}
        plan_conflict_flag = "HIGH_INTEREST_LOW_FOUNDATION: Remedial bridge required" if conflicted_skills else None

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

        current_sem_credits = 0.0

        def schedule_missing_prereqs(dependent_cid: str) -> None:
            """Schedule any uncompleted prerequisites of dependent_cid ahead of it (deepest first).

            Core and backlog courses are mandatory, so instead of dropping them when a
            prerequisite is missing (e.g. a backlog student who never cleared EE1L001),
            the missing prerequisite chain is cleared first in the same semester.
            """
            nonlocal current_sem_credits
            for pid in self._get_prereq_chain(dependent_cid):
                if pid in assigned_courses:
                    continue
                p_meta = self.course_info.get(pid, {})
                assigned_courses.add(pid)
                current_sem_credits += p_meta.get("credits", 4.0)
                items.append(PlanItem(
                    item_id=f"ITEM_PREREQ_{pid}_{uuid.uuid4().hex[:6]}",
                    item_type="course",
                    course_id=pid,
                    semester_number=current_sem,
                    estimated_hours=4.0,
                    phase=p1_label,
                    prep_hours_weekly=6.0,
                    reason=StructuredReason(
                        intent=f"Prerequisite Clearance for {dependent_cid}",
                        target_skills=self.course_skills.get(pid, []),
                        why_this=f"PREREQUISITE NOT CLEARED: {pid} ({p_meta.get('title', pid)}) is required before {dependent_cid} and has not been completed. Scheduled ahead of {dependent_cid}.",
                        prerequisite_for=[dependent_cid],
                        rule_compliance=["Satisfies prerequisite chain"]
                    )
                ))

        sem_reqs = self.prog_requirements.get((prog_id, current_sem), [])

        if sem_reqs:
            # =========================================================================
            # PHASE 0: Prioritized Backlog Clearance
            # =========================================================================
            # If student has backlogs, identify and prioritize uncompleted core courses
            # from prior semesters before scheduling regular electives.
            if current_sem > 1 and student.backlogs > 0:
                for s in range(1, current_sem):
                    for r in self.prog_requirements.get((prog_id, s), []):
                        c = r.get("course_id", "").strip()
                        if c and c not in completed_set and c not in assigned_courses:
                            schedule_missing_prereqs(c)
                            c_meta = self.course_info.get(c, {})
                            c_title = c_meta.get("title", c)
                            c_skills = self.course_skills.get(c, [])
                            assigned_courses.add(c)
                            current_sem_credits += c_meta.get("credits", 4.0)
                            items.append(PlanItem(
                                item_id=f"ITEM_BACKLOG_{c}_{uuid.uuid4().hex[:6]}",
                                item_type="course",
                                course_id=c,
                                semester_number=current_sem,
                                estimated_hours=4.0,
                                phase=p1_label,
                                prep_hours_weekly=6.0,
                                reason=StructuredReason(
                                    intent="Backlog Core Clearance Prioritized",
                                    target_skills=c_skills,
                                    why_this=f"PRIORITIZED BACKLOG: Mandatory core course {c} ({c_title}) from Semester {s} was uncompleted. Prioritized for clearance before advanced electives.",
                                    prerequisite_for=[],
                                    rule_compliance=["Academic standing rule: Prioritize uncompleted core backlog courses"]
                                )
                            ))

            # =========================================================================
            # PHASE A: Fixed Major / Core Courses (Branch Curriculum Rule)
            # =========================================================================
            # Core courses are mandatory per branch curriculum and are FIXED.
            # Career relevance does NOT determine their inclusion.
            active_policy = None
            try:
                from app.personas.registry import persona_registry
                for pkg in persona_registry.list_all():
                    if pkg.spec and pkg.spec.goal_id == goal.goal_id:
                        active_policy = pkg.policy
                        break
            except Exception:
                pass
            if active_policy is None:
                from app.personas.policy import PersonaPolicy
                active_policy = PersonaPolicy({})

            raw_core_cids = []
            core_req_map: Dict[str, Dict[str, Any]] = {}

            for r in sem_reqs:
                cid = r.get("course_id", "").strip()
                slot_type = (r.get("slot_type", "") or "").strip().lower()
                course_type = (r.get("course_type", "") or "").strip().lower()
                is_choosable_type = (
                    slot_type in ["elective", "lateral", "breadth", "minor"] or
                    course_type in ["elective", "vertical elective", "lateral", "breadth", "minor"]
                )
                if cid and not is_choosable_type and cid not in assigned_courses:
                    is_req = active_policy.classify_requirement(cid, r.get("slot_id"), student, default_is_required=True)
                    if is_req:
                        raw_core_cids.append(cid)
                        core_req_map[cid] = r

            # Sort topologically so internal prerequisites precede dependent courses
            ordered_core_cids = self._topological_sort_courses(raw_core_cids)

            for cid in ordered_core_cids:
                # May already be scheduled as a prerequisite of an earlier core course
                if cid in assigned_courses:
                    continue
                schedule_missing_prereqs(cid)
                req_row = core_req_map.get(cid, {})
                c_meta = self.course_info.get(cid, {})
                c_title = c_meta.get("title", cid)
                c_credits = float(c_meta.get("credits", 4.0))
                slot_name = req_row.get("slot_name", "Core Degree Course")
                slot_id = req_row.get("slot_id")

                hours_per_credit = float(settings.PLANNER_ASSUMPTIONS.get("hours_per_credit", 1.0))
                weekly_load = c_credits * hours_per_credit
                
                # Fetch career relevance for explanation/rationale only
                rel_score, rel_rationale = self.relevance_engine.get_relevance(cid, goal.goal_id)
                goal_emphasis = None
                why_reason = f"Mandatory major/core requirement for {prog_id} Semester {current_sem} ({slot_name}: {c_title}). Locked commitment."
                if rel_score > 0:
                    goal_emphasis = f"Target Mastery: Core competency for {goal.name} (Relevance {rel_score}/3). Master {rel_rationale}."
                    why_reason += f" {goal_emphasis}"

                c_skills = self.course_skills.get(cid, [])
                if any(s in conflicted_skills for s in c_skills):
                    why_reason += " [CONFLICT: Interest vs Evidence] Student has high interest/aspiration, but diagnostic evidence indicates foundational gaps (<40). Scheduled foundational bridge before advanced coursework."

                assigned_courses.add(cid)
                current_sem_credits += c_credits

                core_item = PlanItem(
                    item_id=f"ITEM_CORE_{cid}_{uuid.uuid4().hex[:6]}",
                    item_type="REQUIRED_COURSE",
                    course_id=cid,
                    slot_id=slot_id,
                    semester_number=current_sem,
                    estimated_hours=weekly_load,
                    hours_per_week=weekly_load,
                    phase=p1_label,
                    prep_hours_weekly=weekly_load,
                    status_badge="LOCKED",
                    goal_emphasis=goal_emphasis,
                    cited_kb_codes=[cid],
                    reason=StructuredReason(
                        intent=f"Branch Core Degree Requirement ({prog_id})",
                        target_skills=c_skills,
                        why_this=why_reason,
                        prerequisite_for=[],
                        rule_compliance=["Mandatory branch curriculum requirement", "Fixed core selection (LOCKED)"]
                    )
                )
                items.append(core_item)
                required_courses_list.append(core_item)

                # Add core practice exercise
                items.append(PlanItem(
                    item_id=f"ITEM_EX_{cid}_{uuid.uuid4().hex[:6]}",
                    item_type="EXERCISE_SET",
                    course_id=cid,
                    semester_number=current_sem,
                    estimated_hours=2.0,
                    hours_per_week=2.0,
                    phase=p1_label,
                    prep_hours_weekly=2.0,
                    status_badge="LOCKED",
                    cited_kb_codes=[cid],
                    reason=StructuredReason(
                        intent=f"Core Course Practice: {cid}",
                        target_skills=c_skills,
                        why_this=f"Active problem solving and concept mastery for core course {cid}.",
                        prerequisite_for=[],
                        rule_compliance=[]
                    )
                ))

            # =========================================================================
            # PHASE B: Elective Slots (Lateral, Breadth, Elective)
            # =========================================================================
            # Elective slots are recommendation candidates ranked using CourseRelevanceEngine
            # (0-3 scale) + active skill gap boost, respecting prerequisite gating.
            for r in sem_reqs:
                cid = r.get("course_id", "").strip()
                if not cid:
                    slot_id = r.get("slot_id", "").strip()
                    slot_type = r.get("slot_type", "elective").strip().lower()
                    slot_name = r.get("slot_name", slot_id)

                    is_req = active_policy.classify_requirement(None, slot_id, student, default_is_required=False)
                    if is_req:
                        continue

                    # Mark pool rule status if unknown (e.g. MME pools)
                    pool_rule_status = None
                    if prog_id == "BTECH_MM" and ("BREADTH" in slot_id.upper() or "LATERAL" in slot_id.upper() or "ELECTIVE" in slot_id.upper()):
                        pool_rule_status = "pool rule unknown"

                    candidate_options = list(self.slot_options.get(slot_id, []))
                    if not candidate_options:
                        if "breadth" in slot_type or "breadth" in slot_id.lower():
                            candidate_options = [c for c, info in self.course_info.items() if not c.startswith(prog_id[-2:]) and c not in assigned_courses]
                        else:
                            candidate_options = [c for g in gaps for c in self.skill_courses.get(g["skill_id"], []) if c not in assigned_courses]

                    # Filter out student-stated avoid_courses and not_together conflicts
                    allowed_options = []
                    for c in candidate_options:
                        if c in avoid_courses:
                            optional_overload_proposals.append({
                                "proposal_id": f"PROP_AVOID_{c}_{uuid.uuid4().hex[:6]}",
                                "course_id": c,
                                "title": self.course_info.get(c, {}).get("title", c),
                                "credits": self.course_info.get(c, {}).get("credits", 3.0),
                                "reason": f"Matches student-stated avoid constraint. Placed in optional proposal requiring student approval.",
                                "status": "pending_student_approval"
                            })
                            continue

                        conflicts = any(c in pair and any(x in assigned_courses for x in (pair - {c})) for pair in not_together_pairs)
                        if conflicts:
                            optional_overload_proposals.append({
                                "proposal_id": f"PROP_NOT_TOGETHER_{c}_{uuid.uuid4().hex[:6]}",
                                "course_id": c,
                                "title": self.course_info.get(c, {}).get("title", c),
                                "credits": self.course_info.get(c, {}).get("credits", 3.0),
                                "reason": f"Conflicts with student-stated not-together constraint. Placed in optional proposal requiring student approval.",
                                "status": "pending_student_approval"
                            })
                            continue

                        allowed_options.append(c)

                    # Deterministic ranking via CourseRelevanceEngine
                    ranked = self.relevance_engine.rank_electives(
                        candidate_course_ids=allowed_options,
                        goal_id=goal.goal_id,
                        skill_gaps=gaps,
                        completed_course_ids=list(assigned_courses),
                        prereq_map=self.rule_engine.prereqs
                    )

                    if ranked:
                        top_pick = ranked[0]
                        elec_cid = top_pick["course_id"]
                        elec_credits = float(self.course_info.get(elec_cid, {}).get("credits", 3.0))
                        hours_per_credit = float(settings.PLANNER_ASSUMPTIONS.get("hours_per_credit", 1.0))
                        elec_weekly_load = elec_credits * hours_per_credit

                        # Student constraint check (HARD limit)
                        if effective_student_credit_cap is not None and (current_sem_credits + elec_credits > effective_student_credit_cap):
                            optional_overload_proposals.append({
                                "proposal_id": f"PROP_OVERLOAD_{elec_cid}_{uuid.uuid4().hex[:6]}",
                                "course_id": elec_cid,
                                "title": self.course_info.get(elec_cid, {}).get("title", elec_cid),
                                "credits": elec_credits,
                                "reason": f"Exceeds student-stated credit limit ({effective_student_credit_cap:.1f} credits). Total would be {current_sem_credits + elec_credits:.1f} credits. Placed in optional proposal requiring student approval.",
                                "status": "pending_student_approval"
                            })
                        else:
                            # Baseline institute limit is a warning, not a hard block
                            exceeds_cap = (current_sem_credits + elec_credits > 26.0)
                            current_sem_credits += elec_credits
                            assigned_courses.add(elec_cid)

                            covered_gaps = top_pick.get("covered_gaps", [])
                            skill_gap_reason = f"Closes gap in {', '.join(covered_gaps) if covered_gaps else 'domain competencies'} for {slot_name}."
                            why_this = f"Selected for slot {slot_id} based on career relevance to {goal.name} (Score: {top_pick['base_relevance']}/3: {top_pick['rationale']} [Status: {top_pick.get('status', 'draft_for_review')}, Source: {top_pick.get('source_id', 'DESIGN_TEAM')}]) and skill gap alignment."
                            rule_comp = ["Prerequisites verified satisfied", "Complies with curriculum slot options"]
                            if pool_rule_status:
                                rule_comp.append(f"Slot rule note: {pool_rule_status}")
                            if exceeds_cap:
                                why_this += " [WARNING: unsourced_baseline] Total semester credits exceed 26.0 baseline credit cap."
                                rule_comp.append("[WARNING: unsourced_baseline] Exceeds 26.0 baseline credit cap (RULE_SEM_CREDIT_CAP_REGULAR)")

                            elec_item = PlanItem(
                                item_id=f"ITEM_ELEC_{elec_cid}_{uuid.uuid4().hex[:6]}",
                                item_type="ELECTIVE_PICK",
                                course_id=elec_cid,
                                slot_id=slot_id,
                                semester_number=current_sem,
                                estimated_hours=elec_weekly_load,
                                hours_per_week=elec_weekly_load,
                                phase=p2_label,
                                prep_hours_weekly=elec_weekly_load,
                                status_badge="RECOMMENDED",
                                skill_gap_reason=skill_gap_reason,
                                cited_kb_codes=[elec_cid, slot_id],
                                pool_rule_status=pool_rule_status,
                                reason=StructuredReason(
                                    intent=f"Recommended Elective ({slot_name})",
                                    target_skills=self.course_skills.get(elec_cid, []),
                                    why_this=why_this,
                                    prerequisite_for=[],
                                    rule_compliance=rule_comp
                                )
                            )
                            items.append(elec_item)
                            recommended_items_list.append(elec_item)

                            ex_elec = PlanItem(
                                item_id=f"ITEM_EX_{elec_cid}_{uuid.uuid4().hex[:6]}",
                                item_type="EXERCISE_SET",
                                course_id=elec_cid,
                                semester_number=current_sem,
                                estimated_hours=2.0,
                                hours_per_week=2.0,
                                phase=p2_label,
                                prep_hours_weekly=2.0,
                                status_badge="RECOMMENDED",
                                cited_kb_codes=[elec_cid],
                                reason=StructuredReason(
                                    intent=f"Elective Practice: {elec_cid}",
                                    target_skills=self.course_skills.get(elec_cid, []),
                                    why_this=f"Active problem solving for elective course {elec_cid}.",
                                    prerequisite_for=[],
                                    rule_compliance=[]
                                )
                            )
                            items.append(ex_elec)
                            recommended_items_list.append(ex_elec)
                    else:
                        no_cand_item = PlanItem(
                            item_id=f"ITEM_SLOT_EMPTY_{slot_id}_{uuid.uuid4().hex[:6]}",
                            item_type="ELECTIVE_PICK",
                            slot_id=slot_id,
                            semester_number=current_sem,
                            status_badge="NO_CANDIDATE",
                            skill_gap_reason=f"No suitable elective candidate found in catalog for slot {slot_name} ({slot_id}).",
                            pool_rule_status=pool_rule_status,
                            cited_kb_codes=[slot_id],
                            reason=StructuredReason(
                                intent=f"Elective Slot ({slot_name})",
                                target_skills=[],
                                why_this=f"No suitable elective candidate found for slot {slot_name} ({slot_id}) in catalog.",
                                prerequisite_for=[],
                                rule_compliance=[]
                            )
                        )
                        items.append(no_cand_item)
                        recommended_items_list.append(no_cand_item)

            # =========================================================================
            # PHASE C: Minor Track (Optional Recommendation if Eligible)
            # =========================================================================
            # Minor candidates are loaded from data/seed/kb/minor_course.csv (draft_for_review)
            minor_candidates = [c for c in self.minor_courses.get("MINOR_CSE", []) if c not in assigned_courses and c not in avoid_courses]
            if minor_candidates and self.rule_engine.check_minor_eligibility(student):
                ranked_minor = self.relevance_engine.rank_electives(
                    candidate_course_ids=minor_candidates,
                    goal_id=goal.goal_id,
                    skill_gaps=gaps,
                    completed_course_ids=list(assigned_courses),
                    prereq_map=self.rule_engine.prereqs
                )
                if ranked_minor:
                    top_minor = ranked_minor[0]
                    m_cid = top_minor["course_id"]
                    m_credits = self.course_info.get(m_cid, {}).get("credits", 3.0)

                    not_together_conflict = any(m_cid in pair and any(x in assigned_courses for x in (pair - {m_cid})) for pair in not_together_pairs)

                    if not_together_conflict:
                        optional_overload_proposals.append({
                            "proposal_id": f"PROP_NOT_TOGETHER_{m_cid}_{uuid.uuid4().hex[:6]}",
                            "course_id": m_cid,
                            "title": self.course_info.get(m_cid, {}).get("title", m_cid),
                            "credits": m_credits,
                            "reason": f"Conflicts with student-stated not-together constraint. Placed in optional proposal requiring student approval.",
                            "status": "pending_student_approval"
                        })
                    elif effective_student_credit_cap is not None and (current_sem_credits + m_credits > effective_student_credit_cap):
                        optional_overload_proposals.append({
                            "proposal_id": f"PROP_OVERLOAD_{m_cid}_{uuid.uuid4().hex[:6]}",
                            "course_id": m_cid,
                            "title": self.course_info.get(m_cid, {}).get("title", m_cid),
                            "credits": m_credits,
                            "reason": f"Exceeds student-stated credit limit ({effective_student_credit_cap:.1f} credits). Total would be {current_sem_credits + m_credits:.1f} credits. Placed in optional proposal requiring student approval.",
                            "status": "pending_student_approval"
                        })
                    else:
                        exceeds_minor_cap = (current_sem_credits + m_credits > 26.0)
                        current_sem_credits += m_credits
                        assigned_courses.add(m_cid)

                        m_why = f"Student satisfies minor eligibility (Sem {current_sem} >= 5, CGPA {student.cgpa} >= 8.0). Course {m_cid} selected for CSE/DS Minor to accelerate {goal.name} (Relevance {top_minor['base_relevance']}/3: {top_minor['rationale']} [Status: {top_minor.get('status', 'draft_for_review')}])."
                        m_comp = ["Satisfies minor eligibility rules [draft_for_review data]"]
                        if exceeds_minor_cap:
                            m_why += " [WARNING: unsourced_baseline] Total semester credits exceed 26.0 baseline credit cap."
                            m_comp.append("[WARNING: unsourced_baseline] Exceeds 26.0 baseline credit cap (RULE_SEM_CREDIT_CAP_REGULAR)")

                        items.append(PlanItem(
                            item_id=f"ITEM_MIN_{m_cid}_{uuid.uuid4().hex[:6]}",
                            item_type="course",
                            course_id=m_cid,
                            semester_number=current_sem,
                            estimated_hours=4.0,
                            phase=p2_label,
                            prep_hours_weekly=4.0,
                            reason=StructuredReason(
                                intent="Approved Minor Course Track",
                                target_skills=self.course_skills.get(m_cid, []),
                                why_this=m_why,
                                prerequisite_for=[],
                                rule_compliance=m_comp
                            )
                        ))
            elif minor_candidates and not self.rule_engine.check_minor_eligibility(student):
                optional_overload_proposals.append({
                    "proposal_id": f"PROP_MINOR_INELIGIBLE_{uuid.uuid4().hex[:6]}",
                    "reason": f"Student CGPA ({f'{student.cgpa:.2f}' if student.cgpa is not None else 'not provided'}) is below the required 8.00 cutoff or has active backlogs ({student.backlogs}). Ineligible for Minor in Computer Science per academic regulations.",
                    "status": "ineligible_explanation"
                })

        else:
            # Fallback for unconfigured programmes: plan from skill gaps
            for g in gaps:
                if g["gap"] <= 0:
                    continue
                sid = g["skill_id"]
                candidate_courses = self.skill_courses.get(sid, [])
                for cid in candidate_courses:
                    if cid not in assigned_courses:
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
                        items.append(PlanItem(
                            item_id=f"ITEM_C_{cid}_{uuid.uuid4().hex[:6]}",
                            item_type="course",
                            course_id=cid,
                            semester_number=current_sem,
                            estimated_hours=4.0,
                            reason=StructuredReason(
                                intent=f"Close gap in {sid}",
                                target_skills=[sid],
                                why_this=f"Addresses priority gap ({g['gap']} points) in {sid} required for {goal.name}.",
                                prerequisite_for=[],
                                rule_compliance=["Complies with offering and credit limits"]
                            )
                        ))
                        break

        # Open Courseware Resource Coverage for skills with no course coverage (e.g., Databases & OS)
        for g in gaps:
            sid = g.get("skill_id")
            courses_for_sid = self.skill_courses.get(sid, [])
            if not courses_for_sid or not any(c in assigned_courses for c in courses_for_sid):
                skill_res = self.resource_repo.get_resources_for_skill(sid)
                for r_obj in skill_res:
                    res_item = PlanItem(
                        item_id=f"ITEM_RES_{r_obj.resource_id}_{uuid.uuid4().hex[:6]}",
                        item_type="RESOURCE",
                        resource_id=r_obj.resource_id,
                        semester_number=current_sem,
                        estimated_hours=3.0,
                        hours_per_week=3.0,
                        phase=p2_label,
                        prep_hours_weekly=3.0,
                        status_badge="RECOMMENDED",
                        cited_kb_codes=[r_obj.resource_id],
                        skill_gap_reason=f"Open courseware coverage for {sid}",
                        reason=StructuredReason(
                            intent=f"Open Courseware Resource: {sid}",
                            target_skills=[sid],
                            why_this=f"Addresses competency requirement in {sid} using verified open courseware ({r_obj.title}, Provider: {r_obj.provider}) as no departmental course exists in the institute curriculum.",
                            prerequisite_for=[],
                            rule_compliance=["Self-paced open resource study"]
                        )
                    )
                    items.append(res_item)
                    recommended_items_list.append(res_item)

        # UPSC Domain Roadmap & Disclaimers
        if goal.goal_id == "GOAL_UPSC_COMPETITIVE":
            upsc_ms = PlanItem(
                item_id=f"ITEM_MS_UPSC_GS_{uuid.uuid4().hex[:6]}",
                item_type="CHECKPOINT",
                semester_number=current_sem,
                estimated_hours=8.0,
                hours_per_week=8.0,
                phase=p2_label,
                prep_hours_weekly=8.0,
                status_badge="RECOMMENDED",
                cited_kb_codes=["UPSC_GS_SYLLABUS"],
                skill_gap_reason="Non-curricular competitive exam preparation",
                reason=StructuredReason(
                    intent="UPSC General Studies Preparation",
                    target_skills=["SKILL_RESEARCH_WRITING", "SKILL_ENGINEERING_MATH"],
                    why_this="The institutional course catalogue contains zero General Studies (GS) coverage (History, Polity, Economy, Geography, Ethics). UPSC Civil Services preparation must be pursued via structured roadmap milestones and open educational resources alongside degree requirements.",
                    prerequisite_for=[],
                    rule_compliance=["Non-curricular competitive exam preparation"]
                )
            )
            items.append(upsc_ms)
            recommended_items_list.append(upsc_ms)

        # Milestone Checkpoint
        cp_ms = PlanItem(
            item_id=f"ITEM_MS_{uuid.uuid4().hex[:6]}",
            item_type="CHECKPOINT",
            semester_number=current_sem,
            estimated_hours=2.0,
            hours_per_week=2.0,
            phase=p3_label,
            prep_hours_weekly=2.0,
            status_badge="CHECKPOINT",
            cited_kb_codes=["MILESTONE_CHECKPOINT"],
            skill_gap_reason=f"Mastery checkpoint gate for {goal.name}",
            reason=StructuredReason(
                intent="Semester Target Milestone",
                target_skills=[g["skill_id"] for g in gaps if g.get("gap", 0) > 0] if gaps else [],
                why_this=f"Core milestone for goal {goal.name}.",
                prerequisite_for=[],
                rule_compliance=[]
            )
        )
        items.append(cp_ms)

        # 3. Opt-in persona policy adjustment hook
        current_persona_id = None
        try:
            from app.personas.registry import persona_registry
            for pkg in persona_registry.list_all():
                if pkg.spec and pkg.spec.goal_id == goal.goal_id:
                    current_persona_id = pkg.spec.persona_id
                    if getattr(pkg.policy, "enable_plan_adjustment", False):
                        items = pkg.policy.adjust_plan_items(student, items, gaps=gaps)
                    break
        except Exception as e:
            logger.error(
                "Error adjusting plan items for persona '%s': %s",
                current_persona_id or goal.goal_id,
                e,
                exc_info=True
            )
            # Fall back to unadjusted items

        # =========================================================================
        # Workload Cap Enforcement & Extra Load Shedding (Hard Constraint)
        # =========================================================================
        req_weekly_hours = sum(float(getattr(it, "hours_per_week", 0.0) or getattr(it, "estimated_hours", 0.0)) for it in required_courses_list)
        extra_items = [it for it in items if it not in required_courses_list]
        extra_weekly_hours = sum(float(getattr(it, "hours_per_week", 0.0) or getattr(it, "estimated_hours", 0.0)) for it in extra_items)
        total_weekly_load = req_weekly_hours + extra_weekly_hours
        workload_cap_explanation = None

        if student_weekly_hours is not None and total_weekly_load > student_weekly_hours:
            allowed_extras = max(0.0, student_weekly_hours - req_weekly_hours)
            if req_weekly_hours >= student_weekly_hours:
                workload_cap_explanation = (
                    f"Total required core academic workload ({req_weekly_hours:.1f}h/week) meets or exceeds your stated study cap ({student_weekly_hours:.1f}h/week). "
                    f"Mandatory core courses ({req_weekly_hours:.1f}h/week) are locked commitments and cannot be dropped under curriculum regulations. "
                    f"All supplementary extras (elective practice, extra modules, open resources) have been reduced/deferred to protect your workload."
                )
                items = [
                    it.model_copy(update={"hours_per_week": 0.0}) if it in extra_items else it
                    for it in items
                ]
                recommended_items_list = [
                    it.model_copy(update={"hours_per_week": 0.0}) for it in recommended_items_list
                ]
            else:
                workload_cap_explanation = (
                    f"Total requested workload ({total_weekly_load:.1f}h/week) exceeded weekly study hours cap ({student_weekly_hours:.1f}h/week). "
                    f"Mandatory core courses ({req_weekly_hours:.1f}h/week) are locked commitments and preserved. "
                    f"Non-mandatory extras were reduced from {extra_weekly_hours:.1f}h to {allowed_extras:.1f}h to fit your weekly limit."
                )
                scale = allowed_extras / extra_weekly_hours if extra_weekly_hours > 0 else 0.0
                items = [
                    it.model_copy(update={"hours_per_week": round(float(getattr(it, "hours_per_week", 0.0)) * scale, 1)})
                    if it in extra_items else it
                    for it in items
                ]
                recommended_items_list = [
                    it.model_copy(update={"hours_per_week": round(float(getattr(it, "hours_per_week", 0.0)) * scale, 1)})
                    for it in recommended_items_list
                ]

        # =========================================================================
        # Multi-Semester Horizon & Semester Blocks
        # =========================================================================
        semester_blocks: List[SemesterBlock] = []
        hours_per_credit = float(settings.PLANNER_ASSUMPTIONS.get("hours_per_credit", 1.0))
        for sem in range(current_sem, 9):
            sem_name = f"Autumn 2026 (Semester {sem})" if sem % 2 == 1 else f"Spring 2027 (Semester {sem})"
            cal_entries = [r for r in self.academic_calendar if r.get("semester", "").strip().lower() == ("autumn 2026" if sem % 2 == 1 else "spring 2027")]
            if cal_entries:
                start_d = cal_entries[0]["week_start"]
                end_d = cal_entries[-1]["week_start"]
                is_ind = False
            else:
                start_d = str(settings.PLANNER_ASSUMPTIONS.get("default_autumn_start", "2026-08-03")) if sem % 2 == 1 else str(settings.PLANNER_ASSUMPTIONS.get("default_spring_start", "2027-01-04"))
                end_d = "2026-11-23" if sem % 2 == 1 else "2027-04-26"
                is_ind = True

            sem_req_items = [it for it in required_courses_list if it.semester_number == sem]
            sem_elec_items = [it for it in recommended_items_list if it.semester_number == sem and it.item_type == "ELECTIVE_PICK"]

            # If sem > current_sem, fetch future required courses from prog_requirements
            if sem > current_sem:
                for r in self.prog_requirements.get((prog_id, sem), []):
                    c = r.get("course_id", "").strip()
                    if c:
                        c_meta = self.course_info.get(c, {})
                        c_title = c_meta.get("title", c)
                        c_credits = float(c_meta.get("credits", 4.0))
                        rel_score, rel_rationale = self.relevance_engine.get_relevance(c, goal.goal_id)
                        sem_req_items.append(PlanItem(
                            item_id=f"ITEM_CORE_S{sem}_{c}_{uuid.uuid4().hex[:4]}",
                            item_type="REQUIRED_COURSE",
                            course_id=c,
                            semester_number=sem,
                            estimated_hours=c_credits * hours_per_credit,
                            hours_per_week=c_credits * hours_per_credit,
                            status_badge="LOCKED",
                            cited_kb_codes=[c],
                            goal_emphasis=f"Target Mastery: Foundational for {goal.name} (Relevance {rel_score}/3)." if rel_score > 0 else None,
                            reason=StructuredReason(
                                intent=f"Mandatory Degree Core Requirement (Semester {sem})",
                                target_skills=self.course_skills.get(c, []),
                                why_this=f"Fixed core requirement for {prog_id} Semester {sem} ({c_title}). Locked commitment.",
                                prerequisite_for=[],
                                rule_compliance=["Mandatory branch curriculum requirement"]
                            )
                        ))

            # 4 Monthly themes
            monthly_themes = [
                MonthlyTheme(
                    month_index=1,
                    theme_name="Foundational Depth & Diagnostic Gate",
                    focus_skills=[g["skill_id"] for g in gaps[:2]],
                    checkpoint={"week": 4, "type": "diagnostic_gate"},
                    weekly_hours_cap=student_weekly_hours or 20.0
                ),
                MonthlyTheme(
                    month_index=2,
                    theme_name="Core Depth & Midsem Assessment",
                    focus_skills=[g["skill_id"] for g in gaps[2:4]] if len(gaps) > 2 else [],
                    checkpoint={"week": 8, "type": "midsem_gate"},
                    weekly_hours_cap=(student_weekly_hours or 20.0) * float(settings.PLANNER_ASSUMPTIONS.get("exam_week_factor", 0.4))
                ),
                MonthlyTheme(
                    month_index=3,
                    theme_name="Specialization, Electives & Lab Projects",
                    focus_skills=[g["skill_id"] for g in gaps],
                    checkpoint={"week": 12, "type": "mastery_gate"},
                    weekly_hours_cap=student_weekly_hours or 20.0
                ),
                MonthlyTheme(
                    month_index=4,
                    theme_name="Integration, Comprehensive Review & Endsem",
                    focus_skills=[g["skill_id"] for g in gaps],
                    checkpoint={"week": 16, "type": "semester_mastery_gate"},
                    weekly_hours_cap=(student_weekly_hours or 20.0) * 0.2
                )
            ]

            sem_tot_credits = sum(float(self.course_info.get(it.course_id, {}).get("credits", 4.0)) for it in sem_req_items if it.course_id)
            sem_tot_credits += sum(float(self.course_info.get(it.course_id, {}).get("credits", 3.0)) for it in sem_elec_items if it.course_id)

            semester_blocks.append(SemesterBlock(
                semester_number=sem,
                semester_name=sem_name,
                start_date=start_d,
                end_date=end_d,
                is_indicative=is_ind,
                required_courses=sem_req_items,
                elective_picks=sem_elec_items,
                monthly_themes=monthly_themes,
                total_credits=sem_tot_credits,
                buffer_exam_weeks=[8, 15, 16]
            ))

        # =========================================================================
        # Next 4 Weeks Detailed Schedule
        # =========================================================================
        next_4_weeks: List[WeeklyScheduleItem] = []
        base_h = req_weekly_hours / 4.0 if req_weekly_hours > 0 else 4.0

        # Week 1
        next_4_weeks.append(WeeklyScheduleItem(
            item_id=f"WEEK_1_CORE_{uuid.uuid4().hex[:4]}",
            item_type="REQUIRED_COURSE",
            title=f"Core Lectures & Foundations (Semester {current_sem})",
            hours_per_week=round(min(base_h, (student_weekly_hours or 20.0) * 0.4), 1),
            week_index=1,
            is_indicative=semester_blocks[0].is_indicative if semester_blocks else True,
            skill_gap_reason="Mandatory curriculum foundation",
            status_badge="LOCKED",
            cited_kb_codes=[it.course_id for it in required_courses_list if it.course_id][:3]
        ))
        next_4_weeks.append(WeeklyScheduleItem(
            item_id=f"WEEK_1_EX_{uuid.uuid4().hex[:4]}",
            item_type="EXERCISE_SET",
            title="Core Problem Set 1: Foundational Problem Solving",
            hours_per_week=2.0,
            week_index=1,
            is_indicative=True,
            status_badge="LOCKED"
        ))

        # Week 2
        next_4_weeks.append(WeeklyScheduleItem(
            item_id=f"WEEK_2_CORE_{uuid.uuid4().hex[:4]}",
            item_type="REQUIRED_COURSE",
            title="Core Lectures Continuation & Analytical Techniques",
            hours_per_week=round(min(base_h, (student_weekly_hours or 20.0) * 0.4), 1),
            week_index=2,
            is_indicative=True,
            status_badge="LOCKED"
        ))
        if recommended_items_list:
            top_rec = recommended_items_list[0]
            next_4_weeks.append(WeeklyScheduleItem(
                item_id=f"WEEK_2_ELEC_{uuid.uuid4().hex[:4]}",
                item_type="ELECTIVE_PICK",
                title=f"Recommended Elective Study: {top_rec.course_id or top_rec.slot_id}",
                hours_per_week=3.0,
                week_index=2,
                is_indicative=True,
                skill_gap_reason=top_rec.skill_gap_reason,
                status_badge="RECOMMENDED",
                cited_kb_codes=top_rec.cited_kb_codes
            ))

        # Week 3
        next_4_weeks.append(WeeklyScheduleItem(
            item_id=f"WEEK_3_CORE_{uuid.uuid4().hex[:4]}",
            item_type="REQUIRED_COURSE",
            title="Core Advanced Concepts & Lab Preparation",
            hours_per_week=round(min(base_h, (student_weekly_hours or 20.0) * 0.4), 1),
            week_index=3,
            is_indicative=True,
            status_badge="LOCKED"
        ))
        next_4_weeks.append(WeeklyScheduleItem(
            item_id=f"WEEK_3_PROJ_{uuid.uuid4().hex[:4]}",
            item_type="PROJECT",
            title=f"Applied Project / Research Taster Setup for {goal.name}",
            hours_per_week=2.5,
            week_index=3,
            is_indicative=True,
            status_badge="RECOMMENDED"
        ))

        # Week 4
        next_4_weeks.append(WeeklyScheduleItem(
            item_id=f"WEEK_4_CORE_{uuid.uuid4().hex[:4]}",
            item_type="REQUIRED_COURSE",
            title="Core Synthesis & Monthly Revision",
            hours_per_week=round(min(base_h, (student_weekly_hours or 20.0) * 0.4), 1),
            week_index=4,
            is_indicative=True,
            status_badge="LOCKED"
        ))
        next_4_weeks.append(WeeklyScheduleItem(
            item_id=f"WEEK_4_CHECKPOINT_{uuid.uuid4().hex[:4]}",
            item_type="CHECKPOINT",
            title="Month 1 Diagnostic & Mastery Gate Checkpoint",
            hours_per_week=2.0,
            week_index=4,
            is_indicative=True,
            status_badge="CHECKPOINT",
            skill_gap_reason="End of Month 1 Diagnostic Evaluation"
        ))

        grad_year = 2026 + (8 - current_sem) // 2
        grad_sem = "May" if current_sem % 2 == 1 else "December"
        horizon_deadline = f"{grad_sem} {grad_year} (Degree Completion)"

        timeline_roadmap = TimelineRoadmap(
            plan_id=f"PLAN_{student.student_id}_{uuid.uuid4().hex[:8]}",
            student_id=student.student_id,
            goal_id=goal.goal_id,
            horizon_deadline=horizon_deadline,
            semester_blocks=semester_blocks,
            next_4_weeks=next_4_weeks,
            assumptions=dict(settings.PLANNER_ASSUMPTIONS)
        )

        plan = Plan(
            plan_id=f"PLAN_{student.student_id}_{uuid.uuid4().hex[:8]}",
            student_id=student.student_id,
            goal_id=goal.goal_id,
            version=version,
            items=items,
            timeline_roadmap=timeline_roadmap,
            semester_blocks=semester_blocks,
            next_4_weeks=next_4_weeks,
            required_courses=required_courses_list,
            recommended_items=recommended_items_list,
            workload_cap_explanation=workload_cap_explanation,
            conflict_flag=plan_conflict_flag,
            optional_overload_proposals=optional_overload_proposals,
            mismatch_warning=mismatch,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        return plan

    def adapt_plan_on_checkpoint(
        self,
        plan: Plan,
        checkpoint_item_id: str,
        score: float,
        target_skill: str = "CORE_TOPIC"
    ) -> Plan:
        """
        Adaptive Checkpoint gate:
        - Weak result (score < 50): Inserts targeted remediation, shifts later items.
        - Strong result (score >= 85): Accelerates plan by shortening practice and advancing milestones.
        """
        new_items = list(plan.items)
        if score < 50.0:
            rem_item = PlanItem(
                item_id=f"ITEM_REM_{checkpoint_item_id}_{uuid.uuid4().hex[:6]}",
                item_type="remediation",
                estimated_hours=4.0,
                hours_per_week=4.0,
                status_badge="REMEDIATION",
                reason=StructuredReason(
                    intent=f"Checkpoint Remediation: {target_skill}",
                    target_skills=[target_skill],
                    why_this=f"Weak checkpoint mastery score ({score:.1f}/100 < 50). Remedial practice inserted; later modules shifted.",
                    prerequisite_for=[],
                    rule_compliance=["Academic load managed; remedial clearance prioritized"]
                )
            )
            cp_idx = len(new_items)
            for idx, it in enumerate(new_items):
                if it.item_id == checkpoint_item_id or it.item_type == "CHECKPOINT":
                    cp_idx = idx + 1
                    break
            new_items.insert(cp_idx, rem_item)
            change_summary = f"Checkpoint Weak Result ({score:.1f}/100): Inserted 4.0h remedial bridge in {target_skill} and shifted subsequent items."
        else:
            new_items = [it for it in new_items if not (it.item_type in ["exercise", "EXERCISE_SET"] and it.estimated_hours <= 2.0 and getattr(it, "status_badge", "") == "RECOMMENDED")]
            change_summary = f"Checkpoint Strong Mastery ({score:.1f}/100): Accelerated plan by shortening basic exercises and advancing next milestone."

        return plan.model_copy(update={
            "items": new_items,
            "version": plan.version + 1,
            "what_changed_and_why": change_summary
        })

    create_plan = generate_plan
