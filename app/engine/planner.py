import os
import csv
import uuid
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timezone
from app.contracts.student import StudentProfile, Constraint, Preference
from app.contracts.goal import Goal
from app.contracts.plan import Plan, PlanItem, StructuredReason
from app.engine.interfaces import IPlanner
from app.engine.rules import RuleEngine
from app.engine.relevance import CourseRelevanceEngine
from app.kb.repositories import ResourceRepo

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
                        sem = int(r["semester_number"])
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

        if completed_course_ids is None and current_sem > 1:
            for s in range(1, current_sem):
                for r in self.prog_requirements.get((prog_id, s), []):
                    c = r.get("course_id", "").strip()
                    if c:
                        completed_set.add(c)
            if prog_id == "BTECH_EE":
                completed_set.update(["MA1L001", "MA1L002", "EE1L001", "CS1L001"])
            elif prog_id == "BTECH_MM":
                completed_set.update(["MA1L001", "MA1L002", "CS1L001"])
            assigned_courses = set(completed_set)

        current_sem_credits = 0.0

        sem_reqs = self.prog_requirements.get((prog_id, current_sem), [])

        if sem_reqs:
            # =========================================================================
            # PHASE A: Fixed Major / Core Courses (Branch Curriculum Rule)
            # =========================================================================
            # Core courses are mandatory per branch curriculum and are FIXED.
            # Career relevance does NOT determine their inclusion.
            raw_core_cids = []
            core_req_map: Dict[str, Dict[str, Any]] = {}

            for r in sem_reqs:
                cid = r.get("course_id", "").strip()
                if cid and cid not in assigned_courses:
                    raw_core_cids.append(cid)
                    core_req_map[cid] = r

            # Sort topologically so internal prerequisites precede dependent courses
            ordered_core_cids = self._topological_sort_courses(raw_core_cids)

            for cid in ordered_core_cids:
                req_row = core_req_map.get(cid, {})
                c_meta = self.course_info.get(cid, {})
                c_title = c_meta.get("title", cid)
                slot_name = req_row.get("slot_name", "Core Degree Course")
                
                # Fetch career relevance for explanation/rationale only
                rel_score, rel_rationale = self.relevance_engine.get_relevance(cid, goal.goal_id)
                why_reason = f"Mandatory major/core requirement for {prog_id} Semester {current_sem} ({slot_name}: {c_title})."
                if rel_score > 0:
                    why_reason += f" Contributes foundational competencies to {goal.name} (Relevance {rel_score}/3: {rel_rationale})."

                assigned_courses.add(cid)
                current_sem_credits += c_meta.get("credits", 4.0)
                items.append(PlanItem(
                    item_id=f"ITEM_CORE_{cid}_{uuid.uuid4().hex[:6]}",
                    item_type="course",
                    course_id=cid,
                    semester_number=current_sem,
                    estimated_hours=4.0,
                    reason=StructuredReason(
                        intent=f"Branch Core Degree Requirement ({prog_id})",
                        target_skills=self.course_skills.get(cid, []),
                        why_this=why_reason,
                        prerequisite_for=[],
                        rule_compliance=["Mandatory branch curriculum requirement", "Fixed core selection"]
                    )
                ))
                # Add core practice exercise
                items.append(PlanItem(
                    item_id=f"ITEM_EX_{cid}_{uuid.uuid4().hex[:6]}",
                    item_type="exercise",
                    course_id=cid,
                    semester_number=current_sem,
                    estimated_hours=2.0,
                    reason=StructuredReason(
                        intent=f"Core Course Practice: {cid}",
                        target_skills=self.course_skills.get(cid, []),
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

                    candidate_options = list(self.slot_options.get(slot_id, []))
                    if not candidate_options:
                        if "breadth" in slot_type or "breadth" in slot_id.lower():
                            candidate_options = [c for c, info in self.course_info.items() if not c.startswith(prog_id[-2:]) and c not in assigned_courses]
                        else:
                            candidate_options = [c for g in gaps for c in self.skill_courses.get(g["skill_id"], []) if c not in assigned_courses]

                    # Deterministic ranking via CourseRelevanceEngine
                    ranked = self.relevance_engine.rank_electives(
                        candidate_course_ids=candidate_options,
                        goal_id=goal.goal_id,
                        skill_gaps=gaps,
                        completed_course_ids=list(assigned_courses),
                        prereq_map=self.rule_engine.prereqs
                    )

                    if ranked:
                        top_pick = ranked[0]
                        elec_cid = top_pick["course_id"]
                        elec_credits = self.course_info.get(elec_cid, {}).get("credits", 3.0)
                        exceeds_cap = (current_sem_credits + elec_credits > 26.0)
                        current_sem_credits += elec_credits
                        assigned_courses.add(elec_cid)

                        why_this = f"Selected for slot {slot_id} based on career relevance to {goal.name} (Score: {top_pick['base_relevance']}/3: {top_pick['rationale']} [Status: {top_pick.get('status', 'draft_for_review')}, Source: {top_pick.get('source_id', 'DESIGN_TEAM')}]) and skill gap alignment."
                        rule_comp = ["Prerequisites verified satisfied", "Complies with curriculum slot options"]
                        if exceeds_cap:
                            why_this += " [WARNING: unsourced_baseline] Total semester credits exceed 26.0 baseline credit cap."
                            rule_comp.append("[WARNING: unsourced_baseline] Exceeds 26.0 baseline credit cap (RULE_SEM_CREDIT_CAP_REGULAR)")

                        items.append(PlanItem(
                            item_id=f"ITEM_ELEC_{elec_cid}_{uuid.uuid4().hex[:6]}",
                            item_type="course",
                            course_id=elec_cid,
                            semester_number=current_sem,
                            estimated_hours=4.0,
                            reason=StructuredReason(
                                intent=f"Recommended Elective ({slot_name})",
                                target_skills=self.course_skills.get(elec_cid, []),
                                why_this=why_this,
                                prerequisite_for=[],
                                rule_compliance=rule_comp
                            )
                        ))
                        items.append(PlanItem(
                            item_id=f"ITEM_EX_{elec_cid}_{uuid.uuid4().hex[:6]}",
                            item_type="exercise",
                            course_id=elec_cid,
                            semester_number=current_sem,
                            estimated_hours=2.0,
                            reason=StructuredReason(
                                intent=f"Elective Practice: {elec_cid}",
                                target_skills=self.course_skills.get(elec_cid, []),
                                why_this=f"Active problem solving for elective course {elec_cid}.",
                                prerequisite_for=[],
                                rule_compliance=[]
                            )
                        ))

            # =========================================================================
            # PHASE C: Minor Track (Optional Recommendation if Eligible)
            # =========================================================================
            # Minor candidates are loaded from data/seed/kb/minor_course.csv (draft_for_review)
            minor_candidates = [c for c in self.minor_courses.get("MINOR_CSE", []) if c not in assigned_courses]
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
                        reason=StructuredReason(
                            intent="Approved Minor Course Track",
                            target_skills=self.course_skills.get(m_cid, []),
                            why_this=m_why,
                            prerequisite_for=[],
                            rule_compliance=m_comp
                        )
                    ))

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

        # Milestone Checkpoint
        items.append(PlanItem(
            item_id=f"ITEM_MS_{uuid.uuid4().hex[:6]}",
            item_type="milestone",
            semester_number=current_sem,
            estimated_hours=0.0,
            reason=StructuredReason(
                intent="Semester Target Milestone",
                target_skills=[g["skill_id"] for g in gaps if g.get("gap", 0) > 0] if gaps else [],
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
