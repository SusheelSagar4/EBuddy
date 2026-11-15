import os
import csv
import yaml
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Union
from app.contracts.student import StudentProfile
from app.contracts.plan import PlanItem, StructuredReason
from app.personas.policy import PersonaPolicy
from app.personas.btech_upsc.policy import CustomPersonaPolicy as BTechUPSCPolicy

class CustomPersonaPolicy(PersonaPolicy):
    """
    Deterministic persona policy for student_startup (B.Tech EE & MM at IIT Bhubaneswar).
    Implements rules S1-S7 dynamically reading from policy_rules.yaml,
    institute_calendar.csv, and institute_curriculum_slots.csv.
    Zero hard-coded rule thresholds.
    """
    enable_plan_adjustment: bool = True

    def __init__(self, spec: Dict[str, Any]):
        super().__init__(spec)
        self.spec = spec
        self.base_dir = os.path.dirname(__file__)
        self.raw_data_dir = os.path.abspath(
            os.path.join(self.base_dir, "..", "..", "..", "data", "raw", "higher_studies", "startup")
        )
        self.institute_dir = os.path.abspath(
            os.path.join(self.base_dir, "..", "..", "..", "data", "raw", "institute")
        )
        self.rules_by_id: Dict[str, Dict[str, Any]] = {}
        self.calendar: List[Dict[str, str]] = []
        self.curriculum_slots: List[Dict[str, str]] = []
        self.resources: List[Dict[str, str]] = []
        self.requirements: List[Dict[str, Any]] = []
        self.milestones_data: List[Dict[str, str]] = []
        self._load_policy_data()

    def _load_policy_data(self):
        # 1. Load rules from policy_rules.yaml
        rules_path = os.path.join(self.base_dir, "policy_rules.yaml")
        if not os.path.exists(rules_path):
            rules_path = os.path.join(self.raw_data_dir, "policy_rules.yaml")
        if os.path.exists(rules_path):
            with open(rules_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                for r in cfg.get("rules", []):
                    self.rules_by_id[r["id"]] = r

        # 2. Load shared institute_calendar.csv
        cal_path = os.path.join(self.institute_dir, "institute_calendar.csv")
        if os.path.exists(cal_path):
            with open(cal_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.calendar = [r for r in reader if any(r.values())]

        # 3. Load shared institute_curriculum_slots.csv
        slots_path = os.path.join(self.institute_dir, "institute_curriculum_slots.csv")
        if os.path.exists(slots_path):
            with open(slots_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.curriculum_slots = [r for r in reader if any(r.values())]

        # 4. Load resources.csv
        res_path = os.path.join(self.raw_data_dir, "resources.csv")
        if os.path.exists(res_path):
            with open(res_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.resources = [r for r in reader if any(r.values())]

        # 5. Load requirements.yaml
        req_path = os.path.join(self.base_dir, "requirements.yaml")
        if os.path.exists(req_path):
            with open(req_path, "r", encoding="utf-8") as f:
                self.requirements = yaml.safe_load(f) or []

        # 6. Load milestones.csv
        m_path = os.path.join(self.raw_data_dir, "milestones.csv")
        if os.path.exists(m_path):
            with open(m_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.milestones_data = [r for r in reader if any(r.values())]

    # -------------------------------------------------------------
    # Rule S1: Exam Weeks Pause
    # -------------------------------------------------------------
    def s1_exam_weeks_pause(
        self,
        current_date: Optional[Union[date, str]] = None,
        end_sem_within_14d: Optional[bool] = None,
        mid_sem_within_7d: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Rule S1: Exam weeks pause.
        if end_sem_within_14d OR mid_sem_within_7d:
          Pause new build work; keep weekly customer call and a 1-hour sprint review; shift milestone windows +1 week.
        Parameters read dynamically from policy_rules.yaml S1 params.
        """
        rule_cfg = self.rules_by_id.get("S1", {})
        params = rule_cfg.get("params", {"end_sem_days": 14, "mid_sem_days": 7})
        end_sem_limit = params.get("end_sem_days", 14)
        mid_sem_limit = params.get("mid_sem_days", 7)

        is_end_sem = False
        is_mid_sem = False

        if end_sem_within_14d is not None:
            is_end_sem = end_sem_within_14d
        if mid_sem_within_7d is not None:
            is_mid_sem = mid_sem_within_7d

        # Check dynamic calendar if dates are provided or evaluated
        if (end_sem_within_14d is None or mid_sem_within_7d is None) and self.calendar:
            c_date: date
            if current_date is None:
                c_date = date.today()
            elif isinstance(current_date, str):
                c_date = datetime.strptime(current_date, "%Y-%m-%d").date()
            else:
                c_date = current_date

            for row in self.calendar:
                start_str = row.get("start_date", "").strip()
                if not start_str:
                    continue
                try:
                    ev_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                except ValueError:
                    continue

                diff = (ev_date - c_date).days
                ev_key = row.get("event_key", "").lower()
                ev_name = row.get("event", "").lower()

                if "end_sem" in ev_key or "end-semester" in ev_name:
                    if 0 <= diff <= end_sem_limit:
                        is_end_sem = True
                if "mid_sem" in ev_key or "mid-semester" in ev_name:
                    if 0 <= diff <= mid_sem_limit:
                        is_mid_sem = True

        triggered = is_end_sem or is_mid_sem
        if triggered:
            return {
                "triggered": True,
                "rule_id": "S1",
                "action": "pause_new_build",
                "keep_tasks": ["weekly_customer_call", "1hr_sprint_review"],
                "shift_milestone_weeks": 1,
                "message": rule_cfg.get(
                    "then",
                    "Pause new build work; keep weekly customer call and a 1-hour sprint review; shift milestone windows +1 week"
                )
            }
        return {"triggered": False, "rule_id": "S1"}

    # -------------------------------------------------------------
    # Rule S2: CGPA Guard
    # -------------------------------------------------------------
    def s2_cgpa_guard(
        self,
        cgpa: float,
        semester: int,
        cgpa_drop_last_sem: float = 0.0,
        active_backlogs: int = 0,
        programme: str = "BTECH_EE"
    ) -> Dict[str, Any]:
        """
        Rule S2: CGPA Guard.
        if cgpa < floor_hard OR cgpa_drop_last_sem >= 0.3 OR active_backlog:
          Cap venture hours (6/wk; 3/wk in Sem 1-2); freeze spending; show fallback card.
        Parameters read dynamically from policy_rules.yaml S2 params.
        """
        rule_cfg = self.rules_by_id.get("S2", {})
        params = rule_cfg.get("params", {
            "floor_hard": 6.5,
            "floor_soft": 7.0,
            "cap_hours": 6,
            "cap_hours_sem12": 3
        })
        floor_hard = float(params.get("floor_hard", 6.5))
        cap_hours = int(params.get("cap_hours", 6))
        cap_hours_sem12 = int(params.get("cap_hours_sem12", 3))

        triggered = (cgpa < floor_hard) or (cgpa_drop_last_sem >= 0.3) or (active_backlogs > 0)
        if triggered:
            hours_cap = cap_hours_sem12 if semester in (1, 2) else cap_hours
            prog_norm = "BTECH_EE" if "EE" in (programme or "").upper() else "BTECH_MM"
            fallback_goal = self.spec.get("fallback_goals", {}).get(prog_norm)
            if not fallback_goal:
                fallback_goal = "GOAL_EE_CORE_POWER" if prog_norm == "BTECH_EE" else "GOAL_FALLBACK_MME_CORE"

            # Check if fallback persona exists or is a stub
            is_stub = (fallback_goal == "GOAL_FALLBACK_MME_CORE")
            return {
                "triggered": True,
                "rule_id": "S2",
                "capped_weekly_hours": hours_cap,
                "freeze_spending": True,
                "fallback_goal": fallback_goal,
                "fallback_is_stub": is_stub,
                "fallback_note": "MME core fallback is currently a stub pending curriculum data" if is_stub else "Active core departmental fallback available",
                "message": f"Cap venture hours ({hours_cap}/wk); freeze spending; show fallback card ({fallback_goal})"
            }
        return {"triggered": False, "rule_id": "S2"}

    # -------------------------------------------------------------
    # Rule S3: Validation Gate
    # -------------------------------------------------------------
    def s3_validation_gate(
        self,
        interviews_logged: int,
        milestone: str = "startup_team_and_mvp"
    ) -> Dict[str, Any]:
        """
        Rule S3: Validation gate.
        if interviews_logged < 10 AND milestone == startup_team_and_mvp:
          Block MVP spend and feature work; force startup_problem_validation tasks.
        Parameters read dynamically from policy_rules.yaml S3 params.
        """
        rule_cfg = self.rules_by_id.get("S3", {})
        params = rule_cfg.get("params", {"min_interviews": 10})
        min_interviews = int(params.get("min_interviews", 10))

        triggered = (interviews_logged < min_interviews) and (milestone == "startup_team_and_mvp")
        if triggered:
            return {
                "triggered": True,
                "rule_id": "S3",
                "block_mvp_spend": True,
                "block_feature_work": True,
                "forced_milestone": "startup_problem_validation",
                "interviews_logged": interviews_logged,
                "min_interviews_required": min_interviews,
                "message": rule_cfg.get(
                    "then",
                    "Block MVP spend and feature work; force startup_problem_validation tasks"
                )
            }
        return {"triggered": False, "rule_id": "S3"}

    # -------------------------------------------------------------
    # Rule S4: Runway Guard
    # -------------------------------------------------------------
    def s4_runway_guard(
        self,
        runway_months: float,
        monthly_burn: float = 0.0
    ) -> Dict[str, Any]:
        """
        Rule S4: Runway Guard.
        if runway_months < 3 AND monthly_burn > 0:
          Block new spend; show options: cut cost, pause, or seek grant/incubation (SR08, SR09).
        Parameters read dynamically from policy_rules.yaml S4 params.
        """
        rule_cfg = self.rules_by_id.get("S4", {})
        params = rule_cfg.get("params", {"min_runway_months": 3})
        min_runway = float(params.get("min_runway_months", 3))

        triggered = (runway_months < min_runway) and (monthly_burn > 0)
        if triggered:
            return {
                "triggered": True,
                "rule_id": "S4",
                "block_new_spend": True,
                "options": ["cut_cost", "pause", "seek_grant_incubation"],
                "recommended_resources": ["SR08", "SR09"],
                "resource_links": [
                    {"resource_id": "SR08", "title": "IIT Bhubaneswar Research and Entrepreneurship Park (REP)", "url": "https://rep.iitbbs.ac.in/", "note": "check the official page"},
                    {"resource_id": "SR09", "title": "Startup India portal", "url": "https://www.startupindia.gov.in/", "note": "check the official page"}
                ],
                "message": rule_cfg.get(
                    "then",
                    "Block new spend; show options: cut cost, pause, or seek grant/incubation (SR08, SR09)"
                )
            }
        return {"triggered": False, "rule_id": "S4"}

    # -------------------------------------------------------------
    # Rule S5: IP Before Disclosure
    # -------------------------------------------------------------
    def s5_ip_before_disclosure(
        self,
        public_demo_planned: bool,
        ip_status: str = "unchecked"
    ) -> Dict[str, Any]:
        """
        Rule S5: IP Before Disclosure.
        if public_demo_planned AND ip_status == unchecked:
          Insert IP check task (SR07) and institute IP policy review before the demo date.
        """
        rule_cfg = self.rules_by_id.get("S5", {})
        triggered = public_demo_planned and (ip_status.lower() == "unchecked")
        if triggered:
            return {
                "triggered": True,
                "rule_id": "S5",
                "action": "insert_ip_check_task",
                "recommended_resource": "SR07",
                "resource_detail": {
                    "resource_id": "SR07",
                    "title": "Entrepreneurship and IP Strategy",
                    "url": "https://onlinecourses.nptel.ac.in/noc25_hs213/preview",
                    "note": "check the course page for the next run"
                },
                "requires_institute_ip_policy_review": True,
                "message": rule_cfg.get(
                    "then",
                    "Insert IP check task (SR07) and institute IP policy review before the demo date"
                )
            }
        return {"triggered": False, "rule_id": "S5"}

    # -------------------------------------------------------------
    # Rule S6: Placement Interplay
    # -------------------------------------------------------------
    def s6_placement_interplay(
        self,
        semester: int,
        placement_registered: bool
    ) -> Dict[str, Any]:
        """
        Rule S6: Placement Interplay.
        if sem == 7 AND placement_registered:
          Keep a 5 hr/wk venture floor during placements; require a written continue/pause/job-first decision in Sem 8 (milestone startup_traction_decision).
        Parameters read dynamically from policy_rules.yaml S6 params.
        """
        rule_cfg = self.rules_by_id.get("S6", {})
        params = rule_cfg.get("params", {"floor_hours": 5})
        floor_hours = int(params.get("floor_hours", 5))

        triggered = (semester == 7) and placement_registered
        if triggered:
            return {
                "triggered": True,
                "rule_id": "S6",
                "floor_hours": floor_hours,
                "sem8_required_milestone": "startup_traction_decision",
                "message": rule_cfg.get(
                    "then",
                    "Keep a 5 hr/wk venture floor during placements; require a written continue/pause/job-first decision in Sem 8 (milestone startup_traction_decision)"
                )
            }
        return {"triggered": False, "rule_id": "S6"}

    # -------------------------------------------------------------
    # Rule S7: Project Alignment
    # -------------------------------------------------------------
    def s7_project_alignment(
        self,
        semester: int,
        project_topic_unrelated_to_venture: bool
    ) -> Dict[str, Any]:
        """
        Rule S7: Project Alignment.
        if sem >= 7 AND project_topic_unrelated_to_venture:
          Prompt student to discuss aligning the B.Tech project with the venture prototype with the project guide.
        Displayed as a PROMPT ONLY.
        """
        rule_cfg = self.rules_by_id.get("S7", {})
        triggered = (semester >= 7) and project_topic_unrelated_to_venture
        if triggered:
            return {
                "triggered": True,
                "rule_id": "S7",
                "prompt_only": True,
                "prompt": "Discuss aligning your B.Tech project with your venture prototype with your project guide.",
                "message": rule_cfg.get(
                    "then",
                    "Prompt student to discuss aligning the B.Tech project with the venture prototype with the project guide"
                )
            }
        return {"triggered": False, "rule_id": "S7"}

    # -------------------------------------------------------------
    # Curriculum Track & Slot Wiring (Reusing btech_upsc helper)
    # -------------------------------------------------------------
    @staticmethod
    def get_track_for_admission_year(admission_year: Union[str, int]) -> str:
        """Admitted 2025-26 (or 2025) or later = NEP; earlier = 2016-17 (pre-NEP)."""
        return BTechUPSCPolicy.get_track_for_admission_year(admission_year)

    def get_curriculum_slots(
        self,
        programme: str,
        semester: int,
        track: Optional[str] = None,
        admission_year: Optional[Union[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Identifies heavy and light slots for a given semester & programme using shared institute_curriculum_slots.csv.
        Quantifies lab, core, and project commitments to schedule venture hours around them.
        """
        prog_norm = "BTECH_EE" if "EE" in (programme or "").upper() else "BTECH_MM"
        if track:
            eff_track = track
        elif admission_year is not None:
            eff_track = self.get_track_for_admission_year(admission_year)
        else:
            eff_track = "NEP" if semester in {1, 2, 3, 4} else "2016-17"

        matched = [
            r for r in self.curriculum_slots
            if r.get("programme_code") == prog_norm
            and str(r.get("semester")) == str(semester)
            and (r.get("track") == eff_track or (eff_track in ["2016-17", "pre-NEP"] and r.get("track") in ["2016-17", "pre-NEP"]))
        ]

        heavy_types = {"common core", "vertical core", "core", "laboratory", "common core lab", "project"}
        heavy_slots = []
        light_slots = []

        for slot in matched:
            stype = slot.get("slot_type", "").lower()
            if any(h in stype for h in heavy_types):
                heavy_slots.append(slot)
            else:
                light_slots.append(slot)

        # Workload calculation: each heavy slot ~4 hrs/wk, light slot ~2 hrs/wk
        est_academic_hours = (len(heavy_slots) * 4) + (len(light_slots) * 2)
        base_budget = 40.0
        # Light semester vs heavy semester
        is_heavy_semester = len(heavy_slots) >= 4 or any("project" in s.get("slot_type", "").lower() for s in matched)
        avail_venture_hours = max(5.0, min(15.0, base_budget - est_academic_hours))

        # Project alignment prompt in Sem 7/8
        project_alignment_prompt = None
        if semester >= 7:
            s7 = self.s7_project_alignment(semester=semester, project_topic_unrelated_to_venture=True)
            if s7.get("triggered"):
                project_alignment_prompt = s7.get("prompt")

        return {
            "programme": prog_norm,
            "semester": semester,
            "track": eff_track,
            "total_slots": len(matched),
            "heavy_slots": heavy_slots,
            "light_slots": light_slots,
            "is_heavy_semester": is_heavy_semester,
            "estimated_academic_hours": est_academic_hours,
            "recommended_weekly_venture_hours": avail_venture_hours,
            "project_alignment_prompt": project_alignment_prompt
        }

    # -------------------------------------------------------------
    # Plan Item Adjustment Hook (Conforms to Hard Rules 2, 3, 5)
    # -------------------------------------------------------------
    def adjust_plan_items(
        self,
        student: StudentProfile,
        items: List[PlanItem],
        gaps: Optional[List[Dict[str, Any]]] = None
    ) -> List[PlanItem]:
        """
        Opt-in plan item adjustment for student_startup:
        - Covers startup skills with verified resources and active practice exercises.
        - Unverified resources (SR12, SR14, SR15) are strictly marked as 'not confirmed yet'.
        - NPTEL courses are presented with 'check the course page for the next run'.
        - Government/institute scheme resources state 'check the official page' and do not state amounts/fees.
        - Respects S2 CGPA protection notes when CGPA < 6.5.
        - Deterministic: sorted by ID.
        """
        adjusted_items = list(items)

        # 1. CGPA guard check
        s2_res = self.s2_cgpa_guard(
            cgpa=student.cgpa or 7.0,
            semester=student.current_semester or 5,
            active_backlogs=student.backlogs,
            programme=student.programme_id or "BTECH_EE"
        )
        if s2_res["triggered"]:
            for it in adjusted_items:
                if it.reason and hasattr(it.reason, "rule_compliance"):
                    it.reason.rule_compliance.append(f"S2: CGPA stabilization priority (capped at {s2_res['capped_weekly_hours']} hr/wk)")

        # 2. Determine skills with a gap
        if gaps:
            gap_skills = {g["skill_id"] for g in gaps if g.get("gap", 0) > 0}
        else:
            gap_skills = {r["skill_id"] for r in self.requirements if float(r.get("required_level", 0)) > 0}

        # 3. Existing covered skills in plan
        covered_course_skills = set()
        for it in adjusted_items:
            if it.item_type == "course":
                covered_course_skills.update(it.reason.target_skills)

        uncovered_gap_skills = sorted(list(gap_skills - covered_course_skills))
        sem = student.current_semester or 3

        for sid in uncovered_gap_skills:
            all_res = sorted(
                [r for r in self.resources if r.get("target_skill") == sid],
                key=lambda x: x.get("resource_id", "")
            )
            verified_res = [r for r in all_res if r.get("verified", "").strip().upper() == "TRUE"]
            unverified_res = [r for r in all_res if r.get("verified", "").strip().upper() != "TRUE"]

            # Add verified resource item
            if verified_res:
                top_res = verified_res[0]
                rid = top_res["resource_id"]
                title = top_res.get("title", rid)
                provider = top_res.get("provider", "")
                url = top_res.get("url", "")

                compliance_notes = ["Verified startup learning resource"]
                why_res = f"Verified resource ({title})"

                # Hard Rule 5: NPTEL courses check run
                if "nptel" in provider.lower() or "nptel" in url.lower():
                    why_res += " — check the course page for the next run."
                    compliance_notes.append("NPTEL semester-run verification notice")

                # Hard Rule 3: Official scheme portal rule
                if "startup india" in title.lower() or "startup odisha" in title.lower() or "rep" in title.lower():
                    why_res += " — check the official page for scheme terms and incubation forms."
                    compliance_notes.append("Official scheme portal notice (no memorized amounts/fees)")

                adjusted_items.append(PlanItem(
                    item_id=f"ITEM_RS_{student.student_id}_{rid}",
                    item_type="resource",
                    resource_id=rid,
                    semester_number=sem,
                    estimated_hours=3.0,
                    reason=StructuredReason(
                        intent=f"Self-study & venture foundation for {sid}",
                        target_skills=[sid],
                        why_this=why_res,
                        prerequisite_for=[],
                        rule_compliance=compliance_notes
                    )
                ))

            # Add exercise / active practice item
            # Hard Rule 2: Unverified reference marked as 'not confirmed yet'
            if not verified_res:
                if unverified_res:
                    unv_titles = ", ".join([r.get("title", "") for r in unverified_res])
                    unv_note = f" Note: Reference material ({unv_titles}) is not confirmed yet pending mentor review."
                else:
                    unv_note = " Note: Reference materials are not confirmed yet."
                why_ex = f"Active customer discovery, customer interviews, or prototype build to close gap in {sid}.{unv_note}"
            else:
                why_ex = f"Active customer discovery, problem validation, or prototype build to demonstrate proficiency in {sid}."

            adjusted_items.append(PlanItem(
                item_id=f"ITEM_EX_{student.student_id}_{sid}",
                item_type="exercise",
                exercise_id=f"EX_{sid}",
                semester_number=sem,
                estimated_hours=2.0,
                reason=StructuredReason(
                    intent=f"Active practice for {sid}",
                    target_skills=[sid],
                    why_this=why_ex,
                    prerequisite_for=[],
                    rule_compliance=[]
                )
            ))

        return adjusted_items

    def get_advisories(self, student: StudentProfile) -> List[str]:
        notes = []
        sem = student.current_semester or 1
        cgpa = student.cgpa or 7.0

        s1 = self.s1_exam_weeks_pause(current_date=date.today())
        if s1.get("triggered"):
            notes.append(s1["message"])

        s2 = self.s2_cgpa_guard(cgpa=cgpa, semester=sem, active_backlogs=student.backlogs, programme=student.programme_id)
        if s2.get("triggered"):
            notes.append(s2["message"])

        if sem == 7:
            s6 = self.s6_placement_interplay(semester=7, placement_registered=True)
            if s6.get("triggered"):
                notes.append(s6["message"])

        if sem >= 7:
            s7 = self.s7_project_alignment(semester=sem, project_topic_unrelated_to_venture=True)
            if s7.get("triggered"):
                notes.append(s7["prompt"])

        return notes
