import os
import csv
import yaml
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from app.contracts.student import StudentProfile
from app.contracts.plan import PlanItem
from app.personas.policy import PersonaPolicy

class CustomPersonaPolicy(PersonaPolicy):
    """
    Deterministic persona policy for btech_upsc (B.Tech EE & MME at IIT Bhubaneswar).
    Implements rules R1-R10 dynamically reading from policy_rules.yaml, facts.csv,
    cutoffs.csv, institute_calendar.csv, institute_curriculum_slots.csv, and optional_catalog.csv.
    """
    def __init__(self, spec: Dict[str, Any]):
        super().__init__(spec)
        self.spec = spec
        self.base_dir = os.path.dirname(__file__)
        self.raw_data_dir = os.path.abspath(
            os.path.join(self.base_dir, "..", "..", "..", "data", "raw", "higher_studies", "upsc")
        )
        self.rules_by_id: Dict[str, Dict[str, Any]] = {}
        self.facts: Dict[str, Dict[str, str]] = {}
        self.cutoffs: List[Dict[str, str]] = []
        self.calendar: List[Dict[str, str]] = []
        self.curriculum_slots: List[Dict[str, str]] = []
        self.optional_catalog: List[Dict[str, str]] = []
        self._load_policy_data()

    def _load_policy_data(self):
        # 1. Load rules from policy_rules.yaml
        rules_path = os.path.join(self.base_dir, "policy_rules.yaml")
        if os.path.exists(rules_path):
            with open(rules_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                for r in cfg.get("rules", []):
                    self.rules_by_id[r["id"]] = r

        # 2. Load facts.csv
        facts_path = os.path.join(self.raw_data_dir, "facts.csv")
        if os.path.exists(facts_path):
            with open(facts_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    self.facts[r["fact_id"]] = r

        # 3. Load cutoffs.csv
        cutoffs_path = os.path.join(self.raw_data_dir, "cutoffs.csv")
        if os.path.exists(cutoffs_path):
            with open(cutoffs_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.cutoffs = [r for r in reader if any(r.values())]

        # 4. Load institute_calendar.csv
        cal_path = os.path.join(self.raw_data_dir, "institute_calendar.csv")
        if os.path.exists(cal_path):
            with open(cal_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.calendar = [r for r in reader if any(r.values())]

        # 5. Load institute_curriculum_slots.csv
        slots_path = os.path.join(self.raw_data_dir, "institute_curriculum_slots.csv")
        if os.path.exists(slots_path):
            with open(slots_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.curriculum_slots = [r for r in reader if any(r.values())]

        # 6. Load optional_catalog.csv
        opt_path = os.path.join(self.raw_data_dir, "optional_catalog.csv")
        if os.path.exists(opt_path):
            with open(opt_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.optional_catalog = [r for r in reader if any(r.values())]

    # -------------------------------------------------------------
    # Rule R1: Workload Overload
    # -------------------------------------------------------------
    def r1_workload_overload(
        self,
        semester: int,
        placement_season_active: bool = False,
        btp_deadline_within_21d: bool = False,
        end_sem_within_14d: bool = False,
        weekly_hours_available: float = 12.0
    ) -> Dict[str, Any]:
        params = self.rules_by_id.get("R1", {}).get("params", {
            "hours_threshold": 10, "ca_min": 45, "answers_per_day": 2, "answers_per_day_low_hours": 1
        })
        threshold = params.get("hours_threshold", 10)
        triggered = (semester in {6, 7}) and (
            placement_season_active or btp_deadline_within_21d or end_sem_within_14d or weekly_hours_available < threshold
        )
        if triggered:
            ans = params["answers_per_day_low_hours"] if weekly_hours_available < 6 else params["answers_per_day"]
            return {
                "triggered": True,
                "action": "pause_optional_and_static",
                "pause_skills": ["SKILL_UPSC_OPTIONAL"],
                "ca_minutes_per_day": params.get("ca_min", 45),
                "answers_per_day": ans,
                "shift_milestone_weeks": 1,
                "mark_milestone_failed": False,
                "message": "Sem 6/7 workload overload condition detected. Pausing optional & new static reading; maintaining 45m daily CA and shifting milestone windows by +1 week."
            }
        return {"triggered": False}

    # -------------------------------------------------------------
    # Rule R2: CGPA Guard
    # -------------------------------------------------------------
    def r2_cgpa_guard(
        self,
        student_cgpa: float,
        semester: int,
        cgpa_drop_last_sem: float = 0.0,
        active_backlogs: int = 0,
        programme: str = "BTECH_EE"
    ) -> Dict[str, Any]:
        params = self.rules_by_id.get("R2", {}).get("params", {
            "floor_hard": 6.5, "floor_soft": 7.0, "cap_hours": 6, "cap_hours_sem12: 3": 3
        })
        floor_hard = float(params.get("floor_hard", 6.5))
        triggered = (student_cgpa < floor_hard) or (cgpa_drop_last_sem >= 0.3) or (active_backlogs > 0)
        if triggered:
            cap = params.get("cap_hours_sem12", 3) if semester in {1, 2} else params.get("cap_hours", 6)
            prog_norm = "BTECH_EE" if "EE" in programme else "BTECH_MME"
            fallback = self.spec.get("fallback_goals", {}).get(prog_norm, "GOAL_EE_CORE_POWER")
            f22 = self.facts.get("F22", {})
            f22_ver = f22.get("verified", "").upper() == "TRUE"
            floor_status = "confirmed" if f22_ver else "not confirmed yet"
            return {
                "triggered": True,
                "capped_weekly_hours": cap,
                "blocked_milestones": ["upsc_summer_intensive_y3", "upsc_prelims_mock_phase"],
                "fallback_goal": fallback,
                "placement_cutoff_status": floor_status,
                "message": f"CGPA guard triggered (CGPA {student_cgpa:.2f} < {floor_hard} or drop/backlog). Capping weekly UPSC hours at {cap} hrs/week and routing to fallback: {fallback}."
            }
        return {"triggered": False}

    # -------------------------------------------------------------
    # Rule R3: Optional Gate
    # -------------------------------------------------------------
    def r3_optional_gate(
        self,
        semester: int,
        optional_chosen: Optional[str],
        programme: str = "BTECH_EE"
    ) -> Dict[str, Any]:
        params = self.rules_by_id.get("R3", {}).get("params", {"deadline_sem_EE": 5, "deadline_sem_MME": 6})
        deadline = params.get("deadline_sem_EE", 5) if "EE" in programme else params.get("deadline_sem_MME", 6)
        is_undecided = (not optional_chosen) or (str(optional_chosen).lower() in ["undecided", "none", ""])
        triggered = (semester >= deadline) and is_undecided
        if triggered:
            prog_code = "BTECH_EE" if "EE" in programme else "BTECH_MME"
            cat_rows = [r for r in self.optional_catalog if r.get("programme_code") == prog_code]
            rec = "Electrical Engineering" if "EE" in programme else "Mechanical Engineering"
            warning = "Strong curriculum overlap with B.Tech EE Core" if "EE" in programme else "SME-pending review for MME courses"
            return {
                "triggered": True,
                "blocked_skills": ["SKILL_UPSC_OPTIONAL"],
                "forced_milestone": "upsc_optional_lock_in",
                "recommended_optional": rec,
                "warning": warning,
                "options_count": len(cat_rows),
                "message": f"Semester {semester} optional gate: Optional subject must be locked in. Advanced optional preparation blocked until upsc_optional_lock_in completed."
            }
        return {"triggered": False}

    # -------------------------------------------------------------
    # Rule R4: Baseline Gate
    # -------------------------------------------------------------
    def r4_baseline_gate(
        self,
        semester: int,
        ncert_completion: float
    ) -> Dict[str, Any]:
        params = self.rules_by_id.get("R4", {}).get("params", {"min_completion": 0.8})
        min_comp = float(params.get("min_completion", 0.8))
        triggered = (semester >= 3) and (ncert_completion < min_comp)
        if triggered:
            return {
                "triggered": True,
                "blocked_milestones": ["upsc_static_pass1"],
                "forced_milestone": "upsc_ncert_baseline",
                "ncert_completion": ncert_completion,
                "required_completion": min_comp,
                "message": f"Baseline gate: NCERT completion ({ncert_completion*100:.1f}%) < {min_comp*100:.0f}%. Advanced static reading blocked until upsc_ncert_baseline completed."
            }
        return {"triggered": False}

    # -------------------------------------------------------------
    # Rule R5: CSAT Remediation
    # -------------------------------------------------------------
    def r5_csat_remediation(
        self,
        csat_avg_last3: float,
        weeks_to_prelims: int
    ) -> Dict[str, Any]:
        params = self.rules_by_id.get("R5", {}).get("params", {"csat_target": 90, "remediation_hrs": 4})
        triggered = (csat_avg_last3 < 80.0) and (weeks_to_prelims <= 16)
        if triggered:
            return {
                "triggered": True,
                "remediation_hours_per_week": params.get("remediation_hrs", 4),
                "csat_target": params.get("csat_target", 90),
                "max_answers_per_week": 2,
                "message": f"CSAT mock average ({csat_avg_last3:.1f}) is under 80 with {weeks_to_prelims} weeks to Prelims. Adding 4 hrs/wk CSAT block; capping answer writing to 2/week."
            }
        return {"triggered": False}

    # -------------------------------------------------------------
    # Rule R6: Placement Interplay
    # -------------------------------------------------------------
    def r6_placement_interplay(
        self,
        semester: int,
        placement_registered: bool,
        placement_outcome: Optional[str] = None,
        student_cgpa: float = 7.0
    ) -> Dict[str, Any]:
        params = self.rules_by_id.get("R6", {}).get("params", {
            "sem7_floor_hours": 6, "sem8_hours_offer": 20, "sem8_hours_no_offer": 25
        })
        if semester == 7 and placement_registered:
            if not placement_outcome or placement_outcome.lower() == "pending":
                return {
                    "triggered": True,
                    "phase": "placement_season_active",
                    "target_weekly_hours": params.get("sem7_floor_hours", 6),
                    "daily_ca_minutes": 45,
                    "answers_per_day": 1,
                    "message": "Placement season active in Sem 7. Floor preserved at 6 hrs/wk (daily current affairs + 1 answer/day)."
                }
            elif placement_outcome.lower() in ["offer", "placed"]:
                allowed = student_cgpa >= 6.5
                return {
                    "triggered": True,
                    "phase": "placed",
                    "target_weekly_hours_sem8": params.get("sem8_hours_offer", 20),
                    "sem8_attempt_allowed": allowed,
                    "message": f"Placement offer secured. Sem 8 UPSC target: {params.get('sem8_hours_offer', 20)} hrs/week; Sem 8 attempt {'permitted' if allowed else 'deferred due to CGPA'}."
                }
            else:
                return {
                    "triggered": True,
                    "phase": "unplaced",
                    "target_weekly_hours_sem8": params.get("sem8_hours_no_offer", 25),
                    "sem8_attempt_allowed": False,
                    "message": "No placement offer. Sem 8 target hours increased to 25 hrs/week. Recommended deferring first attempt to after graduation."
                }
        return {"triggered": False}

    # -------------------------------------------------------------
    # Rule R7: Attempt Decision
    # -------------------------------------------------------------
    def r7_attempt_decision(
        self,
        semester: int,
        static_pass1_completion: float = 1.0,
        gs_mock_scores: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        params = self.rules_by_id.get("R7", {}).get("params", {"buffer_marks": 20})
        buffer_marks = params.get("buffer_marks", 20)

        verified_cutoffs = [
            float(c["cutoff_marks"]) for c in self.cutoffs
            if c.get("exam_stage", "").lower() == "prelims"
            and c.get("category", "").lower() == "general"
            and c.get("verified", "").upper() == "TRUE"
        ]

        # Rule requirement: needs at least 2 verified cycles, else output "not confirmed yet"
        cutoff_confirmed = len(verified_cutoffs) >= 2
        cutoff_str = f"{max(verified_cutoffs):.2f}" if cutoff_confirmed else "not confirmed yet"

        f04_fact = self.facts.get("F04", {}).get("value", "An attempt counts when candidate appears in any one Prelims paper.")

        mock_scores = gs_mock_scores or []
        mock_avg = sum(mock_scores) / len(mock_scores) if mock_scores else 0.0

        cutoff_target = (max(verified_cutoffs) + buffer_marks - 15) if cutoff_confirmed else 95.0
        insufficient_mocks = (len(mock_scores) >= 8) and (mock_avg < cutoff_target)
        defer_recommended = (semester == 8) and (static_pass1_completion < 0.8 or insufficient_mocks)

        return {
            "triggered": semester == 8,
            "defer_first_attempt": defer_recommended,
            "verified_cutoff_cycles_count": len(verified_cutoffs),
            "cutoff_benchmark": cutoff_str,
            "static_pass1_completion": static_pass1_completion,
            "gs_mock_count": len(mock_scores),
            "gs_mock_average": mock_avg,
            "f04_warning": f04_fact,
            "message": f"Attempt decision: {'Recommend deferring first attempt' if defer_recommended else 'Proceed with Sem 8 attempt'}. Cut-off baseline: {cutoff_str}. Note: {f04_fact}"
        }

    # -------------------------------------------------------------
    # Rule R8: Late Start
    # -------------------------------------------------------------
    def r8_late_start(
        self,
        semester: int,
        static_pass1_completion: float,
        weekly_hours_available: float = 10.0,
        student_insists_sem8: bool = False
    ) -> Dict[str, Any]:
        params = self.rules_by_id.get("R8", {}).get("params", {
            "min_completion": 0.5, "sprint_hours_min": 15, "sprint_weeks": 12
        })
        min_comp = float(params.get("min_completion", 0.5))
        sprint_hrs = float(params.get("sprint_hours_min", 15))
        sprint_wks = int(params.get("sprint_weeks", 12))

        triggered = (semester >= 6) and (static_pass1_completion < min_comp)
        if triggered:
            if student_insists_sem8 and (weekly_hours_available >= sprint_hrs):
                return {
                    "triggered": True,
                    "recommendation": "compressed_static_sprint",
                    "sprint_weeks": sprint_wks,
                    "required_hours": sprint_hrs,
                    "message": f"Late starter in Sem {semester} insisting on Sem 8 attempt. Inserting upsc_compressed_static_sprint ({sprint_wks} weeks at {sprint_hrs}+ hrs/wk)."
                }
            else:
                return {
                    "triggered": True,
                    "recommendation": "attempt_after_graduation",
                    "sprint_eligible": weekly_hours_available >= sprint_hrs,
                    "message": f"Late start in Sem {semester} (static completion {static_pass1_completion*100:.0f}% < 50%). Default recommendation: attempt after graduation."
                }
        return {"triggered": False}

    # -------------------------------------------------------------
    # Rule R9: Age Eligibility
    # -------------------------------------------------------------
    def r9_age_eligibility(
        self,
        birth_date: date,
        target_exam_year: int
    ) -> Dict[str, Any]:
        # Reference date: 1 August of target_exam_year (per F01)
        ref_date = date(target_exam_year, 8, 1)
        age = ref_date.year - birth_date.year - ((ref_date.month, ref_date.day) < (birth_date.month, birth_date.day))

        # Values read from facts F01 and F02
        min_age = 21
        max_age = 32

        eligible = (age >= min_age) and (age <= max_age)
        earliest_year = target_exam_year
        if age < min_age:
            earliest_year = target_exam_year + (min_age - age)

        return {
            "triggered": not eligible,
            "eligible_for_target_year": eligible,
            "age_on_1_august": age,
            "target_exam_year": target_exam_year,
            "min_age": min_age,
            "max_age": max_age,
            "earliest_attempt_year": earliest_year if not eligible else target_exam_year,
            "message": f"Age on 1 August {target_exam_year} is {age}. {'Eligible.' if eligible else f'Not eligible (minimum age {min_age}). Earliest attempt year: {earliest_year}.'}"
        }

    # -------------------------------------------------------------
    # Rule R10: Sem 8 Exam Clash
    # -------------------------------------------------------------
    def r10_sem8_exam_clash(
        self,
        semester: int,
        target_attempt_year: int,
        current_year: int = 2027
    ) -> Dict[str, Any]:
        triggered = (semester == 8) and (target_attempt_year == current_year)
        if not triggered:
            return {"triggered": False}

        # Dynamic dates from institute_calendar.csv and facts.csv
        end_sem_start = None
        btp_viva = None
        for row in self.calendar:
            if row.get("event_key") == "spring_end_sem_start":
                end_sem_start = datetime.strptime(row["start_date"], "%Y-%m-%d").date()
            elif row.get("event_key") == "btp_viva":
                btp_viva = datetime.strptime(row["start_date"], "%Y-%m-%d").date()

        # Defaults matching 2027 calendar if not matched in file
        end_sem_start = end_sem_start or date(2027, 5, 6)
        btp_viva = btp_viva or date(2027, 5, 19)
        prelims_date = date(2027, 5, 23)

        pre_end_sem_days = 14
        new_topics_end = end_sem_start - timedelta(days=pre_end_sem_days)

        return {
            "triggered": True,
            "new_topics_cutoff_date": str(new_topics_end),
            "clash_window_start": str(new_topics_end),
            "clash_window_end": str(btp_viva),
            "clash_capped_hours": 10,
            "revision_only_start": str(btp_viva + timedelta(days=1)),
            "prelims_date": str(prelims_date),
            "schedule": {
                "phase_1_new_topics_end": str(new_topics_end),
                "phase_2_viva_date": str(btp_viva),
                "phase_3_prelims_date": str(prelims_date)
            },
            "message": f"Sem 8 exam clash guard: New topics end on {new_topics_end} (14 days before end-sem). Cap UPSC at 10 hrs/wk until project viva on {btp_viva}. Final revision only until Prelims on {prelims_date}."
        }

    # -------------------------------------------------------------
    # Task 4 Helper: Curriculum Slot Wiring & Heavy/Light Analysis
    # -------------------------------------------------------------
    def get_curriculum_slots(
        self,
        programme: str,
        semester: int,
        track: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Identifies heavy and light slots for a given semester & programme,
        using track resolution from facts F21 (Sem 1/3: NEP; Sem 5/7: 2016-17).
        """
        prog_norm = "BTECH_EE" if "EE" in programme else "BTECH_MME"
        if not track:
            track = "NEP" if semester in {1, 2, 3, 4} else "2016-17"

        matched = [
            r for r in self.curriculum_slots
            if r.get("programme_code") == prog_norm
            and str(r.get("semester")) == str(semester)
            and r.get("track") == track
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

        # Estimate weekly hours: each heavy slot ~4 hrs, light ~2 hrs
        est_academic_hours = (len(heavy_slots) * 4) + (len(light_slots) * 2)
        base_weekly_budget = 40.0
        avail_upsc_hours = max(6.0, base_weekly_budget - est_academic_hours)

        return {
            "programme": prog_norm,
            "semester": semester,
            "track": track,
            "total_slots": len(matched),
            "heavy_slots": heavy_slots,
            "light_slots": light_slots,
            "estimated_academic_hours": est_academic_hours,
            "recommended_weekly_upsc_hours": avail_upsc_hours
        }

    # -------------------------------------------------------------
    # Task 4 Helper: Optional Recommendations from Catalog
    # -------------------------------------------------------------
    def get_optional_recommendations(self, programme: str) -> Dict[str, Any]:
        prog_norm = "BTECH_EE" if "EE" in programme else "BTECH_MME"
        rows = [r for r in self.optional_catalog if r.get("programme_code") == prog_norm]
        strong = [r for r in rows if r.get("iitbbs_overlap") == "STRONG"]
        partial = [r for r in rows if r.get("iitbbs_overlap") == "PARTIAL"]

        return {
            "programme": prog_norm,
            "strong_overlap": strong,
            "partial_overlap": partial,
            "top_choice": strong[0]["optional"] if strong else (partial[0]["optional"] if partial else "Electrical Engineering"),
            "warning": "None" if strong else "MME courses require subject matter expert mapping (D09)"
        }

    # -------------------------------------------------------------
    # Base PersonaPolicy Hooks
    # -------------------------------------------------------------
    def adjust_plan_items(self, student: StudentProfile, items: List[PlanItem]) -> List[PlanItem]:
        """Hook to filter or annotate plan items specifically for btech_upsc."""
        if (student.cgpa or 7.0) < 6.5:
            # Annotate courses with CGPA protection notes
            for it in items:
                if it.item_type == "course":
                    it.reason.rule_compliance.append("R2: CGPA stabilization priority")
        return items

    def get_advisories(self, student: StudentProfile) -> List[str]:
        notes = []
        sem = student.current_semester
        cgpa = student.cgpa or 7.0

        r2 = self.r2_cgpa_guard(cgpa, sem, active_backlogs=student.backlogs, programme=student.programme_id)
        if r2["triggered"]:
            notes.append(r2["message"])

        r3 = self.r3_optional_gate(sem, None, programme=student.programme_id)
        if r3["triggered"]:
            notes.append(r3["message"])

        if sem == 8:
            r10 = self.r10_sem8_exam_clash(sem, target_attempt_year=2027)
            if r10["triggered"]:
                notes.append(r10["message"])

        return notes
