from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import os
import glob
import csv
from app.contracts.student import StudentProfile, Constraint, Preference
from app.contracts.goal import Goal, canonicalize_goal_id
from app.kb.repositories import GoalRepo

def get_student_db_goal(student_id: str) -> Optional[str]:
    """Retrieves active goal from PostgreSQL student.goal table."""
    try:
        import psycopg
        conn = psycopg.connect("postgresql://ebuddy_user:ebuddy_password@127.0.0.1:5432/ebuddy", connect_timeout=1)
        with conn.cursor() as cur:
            cur.execute("SELECT goal_id FROM student.goal WHERE student_id = %s ORDER BY priority ASC LIMIT 1", (student_id,))
            row = cur.fetchone()
            if row and row[0]:
                conn.close()
                return canonicalize_goal_id(row[0])
        conn.close()
    except Exception:
        pass
    return None

def set_student_db_goal(student_id: str, goal_id: str):
    """Persists active goal to PostgreSQL student.goal table."""
    canonical_id = canonicalize_goal_id(goal_id)
    try:
        import psycopg
        conn = psycopg.connect("postgresql://ebuddy_user:ebuddy_password@127.0.0.1:5432/ebuddy", connect_timeout=1)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM student.goal WHERE student_id = %s", (student_id,))
            cur.execute("INSERT INTO student.goal (student_id, goal_id, priority) VALUES (%s, %s, 1)", (student_id, canonical_id))
        conn.commit()
        conn.close()
    except Exception:
        pass

class OnboardingService:
    def __init__(self):
        self.goal_repo = GoalRepo()
        # Active in-memory session store (or backed by DB)
        self.students: Dict[str, StudentProfile] = {}
        self.completed_courses: Dict[str, List[str]] = {}
        self.goals: Dict[str, Optional[Goal]] = {}
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
        """
        Ensures student is loaded in memory.
        Does NOT hard-code a default goal. With no goal specified or in DB,
        the student has goal=None and the UI shows the Goal Intake box.
        """
        if not isinstance(goal_id, str):
            goal_id = None

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
        
        # Check DB if goal_id not explicitly supplied
        if not goal_id:
            goal_id = get_student_db_goal(student_id)

        if goal_id:
            goal_id = canonicalize_goal_id(goal_id)

        # If already onboarded with exact goal, return
        current_g = self.goals.get(student_id)
        current_gid = current_g.goal_id if current_g else None
        if student_id in self.students and current_gid == goal_id and (goal_id is not None or current_gid is None):
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
        goal_id: Optional[str] = None,
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
        self.aims_and_aspirations[student_id] = aims_and_aspirations or "Excel in chosen academic pathway"
        self.target_timelines[student_id] = target_timeline or "By Graduation"
        
        if not isinstance(goal_id, str):
            goal_id = None

        if goal_id:
            goal_id = canonicalize_goal_id(goal_id)
            set_student_db_goal(student_id, goal_id)
            goal = self.goal_repo.get_by_id(goal_id)
            if not goal:
                goal_names = {
                    "GOAL_EE_CORE_POWER": ("Power Systems & Smart Grid", "Core electrical engineering and smart grid operations"),
                    "GOAL_EE_CORE_VLSI": ("Core VLSI & Semiconductor Engineering", "Semiconductor IC design and embedded hardware"),
                    "GOAL_MM_ADVANCED_MATERIALS": ("Advanced Materials R&D & Physical Metallurgy", "Physical metallurgy, structural alloy design, and materials characterization"),
                    "GOAL_MM_PROCESS_ENGINEER": ("Process Metallurgist (Iron & Steelmaking)", "Primary extraction, blast furnace operations, and steelmaking technology"),
                    "GOAL_CORE_TO_MBA": ("Core Engineering to MBA Pathway & Preparation", "CAT/XAT/GMAT prep with profile building"),
                    "GOAL_UPSC_CSE": ("UPSC Civil Services Examination (CSE)", "Public administration and competitive examination"),
                    "GOAL_STARTUP_FOUNDER": ("Student Startup Founder", "Building and launching a student venture")
                }
                title, desc = goal_names.get(goal_id, ("Target Academic Goal", "Personalized academic pathway"))
                goal = Goal(
                    goal_id=goal_id,
                    name=title,
                    category="career",
                    description=desc,
                    source_id="DESIGN_TEAM"
                )
            self.goals[student_id] = goal
        else:
            self.goals[student_id] = None

        self.constraints[student_id] = [
            Constraint(constraint_id=f"C_{student_id}_{i}", student_id=student_id, constraint_type=c.get("type", "study_hours"), parameters=c)
            for i, c in enumerate(constraints or [])
        ]
        self.preferences[student_id] = [
            Preference(preference_id=f"P_{student_id}_{i}", student_id=student_id, preference_type=p.get("type", "mode"), value=p.get("value", "offline"))
            for i, p in enumerate(preferences or [])
        ]

        return student

onboarding_service = OnboardingService()
