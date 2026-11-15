import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
import os
import glob
import csv
from app.contracts.student import StudentProfile, Constraint, Preference
from app.contracts.goal import Goal
from app.kb.repositories import GoalRepo, CourseRepo
from app.kb.field_repo import field_repo

class OnboardingService:
    def __init__(self):
        self.goal_repo = GoalRepo()
        self.course_repo = CourseRepo()
        self.field_repo = field_repo
        # Active in-memory session store (or backed by DB)
        self.students: Dict[str, StudentProfile] = {}
        self.completed_courses: Dict[str, List[str]] = {}
        self.goals: Dict[str, Goal] = {}
        self.student_fields: Dict[str, str] = {}
        self.aims_and_aspirations: Dict[str, str] = {}
        self.target_timelines: Dict[str, str] = {}
        self.constraints: Dict[str, List[Constraint]] = {}
        self.preferences: Dict[str, List[Preference]] = {}

    def get_all_synthetic_students(self) -> List[Dict[str, Any]]:
        """Discovers and parses all synthetic profiles from data/seed/personas/*/students.csv."""
        students = []
        seen = set()
        pattern = os.path.join("data", "seed", "personas", "*", "students.csv")
        for f in sorted(glob.glob(pattern)):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    reader = csv.DictReader(fp)
                    for r in reader:
                        sid = r["student_id"].strip()
                        if sid not in seen:
                            seen.add(sid)
                            completed = [c.strip() for c in r.get("completed_courses", "").split(";") if c.strip()]
                            students.append({
                                "student_id": sid,
                                "name": r["name"].strip(),
                                "programme_id": r["programme_id"].strip(),
                                "current_semester": int(r["current_semester"]),
                                "cgpa": float(r["cgpa"]) if r.get("cgpa") else 8.0,
                                "backlogs": int(r.get("backlogs", 0)),
                                "completed_courses": completed,
                                "is_synthetic": True
                            })
            except Exception as e:
                print(f"Notice: Failed to read {f}: {e}")
        return students

    def ensure_student_onboarded(self, student_id: str, goal_id: Optional[str] = None) -> StudentProfile:
        """Ensures student is loaded in memory from synthetic student seeds."""
        all_students = self.get_all_synthetic_students()
        target = next((s for s in all_students if s["student_id"] == student_id), None)
        
        if not target:
            target = {
                "student_id": student_id,
                "name": f"Student {student_id}",
                "programme_id": "BTECH_MM" if ("MM" in student_id or "MET" in student_id or "MAT" in student_id) else "BTECH_EE",
                "current_semester": 3,
                "cgpa": 8.0,
                "backlogs": 0,
                "completed_courses": ["MA1L001", "PH1L001"],
                "is_synthetic": True
            }

        prog = target["programme_id"]
        if not goal_id:
            goal_id = "GOAL_MM_PROCESS_ENGINEER" if prog == "BTECH_MM" else "GOAL_EE_CORE_POWER"

        # If already onboarded with exact goal, return
        if student_id in self.students and self.goals.get(student_id) and self.goals[student_id].goal_id == goal_id:
            return self.students[student_id]

        return self.onboard_student(
            student_id=target["student_id"],
            name=target["name"],
            programme_id=prog,
            current_semester=target["current_semester"],
            cgpa=target["cgpa"],
            backlogs=target["backlogs"],
            goal_id=goal_id,
            completed_course_ids=target["completed_courses"]
        )

    def onboard_student(
        self,
        student_id: str,
        name: str,
        programme_id: str,
        current_semester: int,
        cgpa: Optional[float] = None,
        backlogs: int = 0,
        goal_id: str = "GOAL_EE_CORE_POWER",
        aims_and_aspirations: Optional[str] = None,
        target_timeline: Optional[str] = None,
        completed_course_ids: Optional[List[str]] = None,
        constraints: Optional[List[Dict[str, Any]]] = None,
        preferences: Optional[List[Dict[str, Any]]] = None
    ) -> StudentProfile:
        student = StudentProfile(
            student_id=student_id,
            name=name,
            programme_id=programme_id,
            current_semester=current_semester,
            cgpa=cgpa,
            backlogs=backlogs,
            is_synthetic=True,
            created_at=datetime.now(timezone.utc)
        )
        self.students[student_id] = student
        self.completed_courses[student_id] = completed_course_ids or []
        self.aims_and_aspirations[student_id] = aims_and_aspirations or "Excel in core engineering track"
        self.target_timelines[student_id] = target_timeline or "By Semester 7 (Placement Season)"
        
        goal = self.goal_repo.get_by_id(goal_id)
        if not goal:
            goal_names = {
                "GOAL_EE_CORE_POWER": ("Power Systems & Smart Grid", "Core electrical engineering and smart grid operations"),
                "GOAL_EE_CORE_VLSI": ("Core VLSI & Semiconductor Engineering", "Semiconductor IC design and embedded hardware"),
                "GOAL_MM_ADVANCED_MATERIALS": ("Advanced Materials R&D & Physical Metallurgy", "Physical metallurgy, structural alloy design, and materials characterization"),
                "GOAL_MM_PROCESS_ENGINEER": ("Process Metallurgist (Iron & Steelmaking)", "Primary extraction, blast furnace operations, and steelmaking technology"),
                "GOAL_EE_NONCORE_SDE": ("Software Development Engineer", "SDE career pathway spanning DSA, System Design, and software engineering"),
                "GOAL_EE_NONCORE_DATA": ("Data Analyst & AI Engineer", "Data Analytics, AI & Machine Learning career pathway"),
                "GOAL_EE_HIGHER_STUDIES": ("Higher Studies Pathway (GATE/GRE/CAT)", "Postgraduate degree preparation"),
                "GOAL_CORE_TO_MBA": ("Core to MBA Management Pathway", "Strategic engineering management career preparation"),
                "GOAL_BTECH_UPSC": ("Civil Services (UPSC CSE/ESE)", "UPSC Civil Services and Engineering Services preparation"),
                "GOAL_STUDENT_STARTUP": ("Student Entrepreneurship & Startup Venture", "Venture creation, prototyping, and startup incubation")
            }
            title, desc = goal_names.get(goal_id, ("Academic Career Pathway", "Academic and professional pathway"))
            goal = Goal(
                goal_id=goal_id,
                name=title,
                category="career",
                description=desc,
                source_id="DESIGN_TEAM"
            )
        self.goals[student_id] = goal

        self.constraints[student_id] = [
            Constraint(constraint_id=f"C_{student_id}_{i}", student_id=student_id, constraint_type=c.get("type", "study_hours"), parameters=c)
            for i, c in enumerate(constraints or [])
        ]
        self.preferences[student_id] = [
            Preference(preference_id=f"P_{student_id}_{i}", student_id=student_id, preference_type=p.get("type", "mode"), value=p.get("value", "offline"))
            for i, p in enumerate(preferences or [])
        ]

        return student

    def resolve_field_and_goal(self, field_input: str, branch: str) -> Tuple[str, str]:
        f_norm = field_input.strip().lower().replace("-", "_").replace(" ", "_")
        field_map = {
            "sde": ("FIELD_SDE", "GOAL_EE_NONCORE_SDE"),
            "software": ("FIELD_SDE", "GOAL_EE_NONCORE_SDE"),
            "ai_ml": ("FIELD_AIML", "GOAL_EE_NONCORE_DATA"),
            "aiml": ("FIELD_AIML", "GOAL_EE_NONCORE_DATA"),
            "data_analytics": ("FIELD_DA", "GOAL_EE_NONCORE_DATA"),
            "da": ("FIELD_DA", "GOAL_EE_NONCORE_DATA"),
            "higher_studies": ("FIELD_GATE_MTECH", "GOAL_EE_HIGHER_STUDIES"),
            "gate": ("FIELD_GATE_MTECH", "GOAL_EE_HIGHER_STUDIES"),
            "mtech": ("FIELD_GATE_MTECH", "GOAL_EE_HIGHER_STUDIES"),
            "mba": ("FIELD_CAT_MBA", "GOAL_CORE_TO_MBA"),
            "cat": ("FIELD_CAT_MBA", "GOAL_CORE_TO_MBA"),
            "civil_services": ("FIELD_UPSC", "GOAL_BTECH_UPSC"),
            "upsc": ("FIELD_UPSC", "GOAL_BTECH_UPSC"),
            "core_research": ("FIELD_CORE_RESEARCH", "GOAL_MM_ADVANCED_MATERIALS" if "MM" in branch else "GOAL_EE_CORE_POWER"),
            "research": ("FIELD_CORE_RESEARCH", "GOAL_MM_ADVANCED_MATERIALS" if "MM" in branch else "GOAL_EE_CORE_POWER"),
            "core_industry": ("FIELD_CORE_INDUSTRY", "GOAL_MM_PROCESS_ENGINEER" if "MM" in branch else "GOAL_EE_CORE_POWER"),
            "industry": ("FIELD_CORE_INDUSTRY", "GOAL_MM_PROCESS_ENGINEER" if "MM" in branch else "GOAL_EE_CORE_POWER"),
            "startup": ("FIELD_STARTUP", "GOAL_STUDENT_STARTUP"),
            "entrepreneurship": ("FIELD_STARTUP", "GOAL_STUDENT_STARTUP"),
        }
        for k, v in field_map.items():
            if k in f_norm:
                return v
        return ("FIELD_SDE", "GOAL_EE_NONCORE_SDE")

    def validate_onboarding_inputs(
        self,
        current_semester: int,
        cgpa: float,
        completed_course_ids: List[str]
    ) -> List[str]:
        errors = []
        if current_semester < 1 or current_semester > 8:
            errors.append(f"Invalid current_semester '{current_semester}'. Must be an integer between 1 and 8.")
        if cgpa < 0.0 or cgpa > 10.0:
            errors.append(f"Invalid CGPA '{cgpa}'. Must be between 0.0 and 10.0.")

        # Prerequisite graph
        prereqs_path = os.path.join(self.course_repo.seed_dir, "course_prerequisite.csv")
        prereq_map = {}
        if os.path.exists(prereqs_path):
            with open(prereqs_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    prereq_map.setdefault(r["course_id"].strip(), []).append(r["prereq_id"].strip())

        completed_set = set(completed_course_ids)
        for cid in completed_course_ids:
            c = self.course_repo.get_by_id(cid)
            if not c:
                errors.append(f"Course '{cid}' does not exist in the institutional knowledge base.")
            # Check prerequisites
            reqs = prereq_map.get(cid, [])
            missing = [p for p in reqs if p not in completed_set]
            if missing:
                errors.append(f"Inconsistent course history: Course '{cid}' requires prerequisites {missing} which are not marked completed.")

        return errors

    def onboard_unified_student(
        self,
        student_id: Optional[str],
        name: str,
        branch: str,
        current_semester: int,
        cgpa: float,
        field_of_interest: str,
        completed_course_ids: Optional[List[str]] = None,
        backlogs: int = 0
    ) -> Dict[str, Any]:
        """
        Unified Onboarding Flow (Requirement F1) + Immediate Brief Roadmap (Requirement F2).
        """
        completed = completed_course_ids or []
        errors = self.validate_onboarding_inputs(current_semester, cgpa, completed)
        if errors:
            raise ValueError("; ".join(errors))

        norm_branch = "BTECH_MM" if ("MM" in branch.upper() or "MET" in branch.upper() or "MAT" in branch.upper()) else "BTECH_EE"
        sid = student_id or f"STU_{uuid.uuid4().hex[:8].upper()}"

        field_id, goal_id = self.resolve_field_and_goal(field_of_interest, norm_branch)

        student = self.onboard_student(
            student_id=sid,
            name=name,
            programme_id=norm_branch,
            current_semester=current_semester,
            cgpa=cgpa,
            backlogs=backlogs,
            goal_id=goal_id,
            completed_course_ids=completed
        )

        self.student_fields[sid] = field_id

        # Retrieve brief field roadmap from DB (Requirement F2)
        roadmap = self.field_repo.get_roadmap(field_id) or {
            "field_id": field_id,
            "name": field_of_interest,
            "total_phases": 4,
            "total_estimated_hours": 300.0
        }
        phases = self.field_repo.get_phases(field_id)

        brief_roadmap = {
            "field_id": field_id,
            "field_name": roadmap.get("name", field_of_interest),
            "category": roadmap.get("category", "career"),
            "description": roadmap.get("description", ""),
            "total_phases": len(phases),
            "total_estimated_hours": roadmap.get("total_estimated_hours", 0.0),
            "phases": [
                {
                    "phase_id": p["phase_id"],
                    "phase_order": p["phase_order"],
                    "phase_name": p["phase_name"],
                    "phase_objective": p["phase_objective"],
                    "learner_outcome": p["learner_outcome"],
                    "estimated_hours": p["estimated_hours"]
                }
                for p in phases
            ]
        }

        return {
            "status": "success",
            "message": "Student successfully onboarded into unified field track.",
            "student": {
                "student_id": student.student_id,
                "name": student.name,
                "programme_id": student.programme_id,
                "current_semester": student.current_semester,
                "cgpa": student.cgpa,
                "backlogs": student.backlogs,
                "field_id": field_id,
                "goal_id": goal_id,
                "completed_courses_count": len(completed)
            },
            "brief_roadmap": brief_roadmap
        }

onboarding_service = OnboardingService()
