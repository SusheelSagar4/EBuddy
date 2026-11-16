"""
Student store and onboarding.

Profiles come from the deterministic seed (`data/seed/student/*.csv`, 75 synthetic students) and,
when PostgreSQL is reachable, from the `student.*` tables (so Adminer edits are picked up on reload).
State is held in memory for the deterministic engine; edits are mirrored to the database best-effort.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import os
import glob
import csv
import json
from app.contracts.student import StudentProfile, Constraint, Preference, EvidenceItem
from app.contracts.goal import Goal
from app.kb.repositories import GoalRepo
from app.db import persistence

class StudentNotFoundError(KeyError):
    """Raised for a student id that is not loaded, not in the seed or database, and not in a persona roster."""

    def __init__(self, student_id: str):
        super().__init__(student_id)
        self.student_id = student_id

    def __str__(self) -> str:
        return f"Student {self.student_id} not found. Create the profile first (POST /api/v2/students or /api/student/onboard)."


SEED_STUDENT_DIR = os.path.join("data", "seed", "student")
DEFAULT_GOALS = {"BTECH_EE": "GOAL_EE_CORE_POWER", "BTECH_MM": "GOAL_MM_PROCESS_ENGINEER"}


def _rows(name: str) -> List[Dict[str, str]]:
    path = os.path.join(SEED_STUDENT_DIR, name)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class OnboardingService:
    def __init__(self):
        self.goal_repo = GoalRepo()
        self._seed_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._init_state()

    def _init_state(self):
        self.students: Dict[str, StudentProfile] = {}
        self.completed_courses: Dict[str, List[str]] = {}
        self.backlog_courses: Dict[str, List[str]] = {}
        self.transcripts: Dict[str, List[Dict[str, Any]]] = {}
        self.goals: Dict[str, Goal] = {}
        self.previous_goals: Dict[str, List[str]] = {}
        self.interests: Dict[str, List[Dict[str, Any]]] = {}
        self.aims_and_aspirations: Dict[str, str] = {}
        self.target_timelines: Dict[str, str] = {}
        self.constraints: Dict[str, List[Constraint]] = {}
        self.preferences: Dict[str, List[Preference]] = {}

    def reset(self):
        """Drops all in-memory student state (used by the system reset)."""
        self._seed_cache = None
        self._init_state()

    # ------------------------------------------------------------------ seed access
    def _seed_bundles(self) -> Dict[str, Dict[str, Any]]:
        if self._seed_cache is not None:
            return self._seed_cache
        bundles: Dict[str, Dict[str, Any]] = {}
        for r in _rows("student.csv"):
            bundles[r["student_id"]] = {
                "profile": dict(student_id=r["student_id"], programme_id=r["programme_id"], year=int(r["year"]),
                                current_semester=int(r["current_semester"]), cgpa=float(r["cgpa"]),
                                persona_tag=r.get("persona_tag"), name=r.get("name") or r["student_id"],
                                backlogs=int(r.get("backlogs") or 0), first_year_track=r.get("first_year_track") or "A",
                                edge_case_tags=[t for t in (r.get("edge_case_tags") or "").split(";") if t],
                                aims=r.get("aims") or None),
                "courses": [], "goals": [], "interests": [], "evidence": [], "constraints": [], "preference": None,
            }
        for r in _rows("completed_course.csv"):
            if r["student_id"] in bundles:
                bundles[r["student_id"]]["courses"].append(dict(course_id=r["course_id"], grade=r["grade"], semester=int(r["semester"]),
                                                                is_backlog=r["is_backlog"].strip().upper() == "TRUE"))
        for r in _rows("student_goal.csv"):
            if r["student_id"] in bundles:
                bundles[r["student_id"]]["goals"].append(dict(goal_id=r["goal_id"], priority=int(r.get("priority") or 1),
                                                              status=r.get("status") or "active",
                                                              since_semester=int(r["since_semester"]) if r.get("since_semester") else None))
        for r in _rows("interest.csv"):
            if r["student_id"] in bundles:
                bundles[r["student_id"]]["interests"].append(dict(topic=r["topic"], weight=float(r.get("weight") or 1.0),
                                                                  declared_strength=r.get("declared_strength"), reliability_tier="weak"))
        for i, r in enumerate(_rows("skill_evidence.csv")):
            if r["student_id"] in bundles:
                bundles[r["student_id"]]["evidence"].append(dict(evidence_id=f"EV_SEED_{i:05d}", skill_id=r["skill_id"],
                                                                 source_type=r["source_type"], score=float(r["score"]),
                                                                 recorded_at=r["recorded_at"], reliability_tier=r.get("reliability_tier") or None,
                                                                 notes=r.get("notes") or None))
        for r in _rows("constraint.csv"):
            if r["student_id"] in bundles:
                bundles[r["student_id"]]["constraints"].append(dict(constraint_type=r["constraint_type"], parameters=json.loads(r["parameters"] or "{}")))
        for r in _rows("preference.csv"):
            if r["student_id"] in bundles:
                bundles[r["student_id"]]["preference"] = dict(preferred_learning_mode=r["preferred_learning_mode"], pace=r["pace"])
        self._seed_cache = bundles
        return bundles

    def get_bundle(self, student_id: str, prefer_db: bool = True) -> Optional[Dict[str, Any]]:
        if prefer_db:
            b = persistence.fetch_student_bundle(student_id)
            if b:
                return b
        return self._seed_bundles().get(student_id)

    def _legacy_roster(self) -> List[Dict[str, Any]]:
        students, seen = [], set()
        for f in sorted(glob.glob(os.path.join("data", "seed", "personas", "*", "students.csv"))):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    for r in csv.DictReader(fp):
                        sid = r["student_id"].strip()
                        if sid in seen:
                            continue
                        seen.add(sid)
                        students.append({
                            "student_id": sid, "name": r["name"].strip(), "programme_id": r["programme_id"].strip(),
                            "current_semester": int(r["current_semester"]), "cgpa": float(r["cgpa"]) if r.get("cgpa") else 8.0,
                            "backlogs": int(r.get("backlogs", 0) or 0),
                            "completed_courses": [c.strip() for c in r.get("completed_courses", "").split(";") if c.strip()],
                            "is_synthetic": True,
                        })
            except Exception as e:
                logging.getLogger("ebuddy.onboarding").warning("Failed to read persona roster %s: %s", f, e)
        return students

    def get_all_synthetic_students(self) -> List[Dict[str, Any]]:
        """All synthetic profiles (75 from the seed; falls back to the persona rosters)."""
        bundles = self._seed_bundles()
        if not bundles:
            return self._legacy_roster()
        out = []
        for sid, b in bundles.items():
            p = b["profile"]
            active = next((g["goal_id"] for g in b["goals"] if g["status"] == "active"), None)
            weekly = next((c["parameters"].get("max_hours") for c in b["constraints"] if c["constraint_type"] == "weekly_hours"), None)
            cap = next((c["parameters"].get("max_credits") for c in b["constraints"] if c["constraint_type"] == "credit_cap"), None)
            out.append({
                "student_id": sid, "name": p["name"], "programme_id": p["programme_id"], "year": p["year"],
                "current_semester": p["current_semester"], "cgpa": p["cgpa"], "backlogs": p["backlogs"],
                "completed_courses": [c["course_id"] for c in b["courses"] if not c["is_backlog"]],
                "backlog_courses": [c["course_id"] for c in b["courses"] if c["is_backlog"]],
                "goal_id": active, "previous_goal_ids": [g["goal_id"] for g in b["goals"] if g["status"] == "previous"],
                "persona_id": p.get("persona_tag"), "edge_case_tags": p["edge_case_tags"],
                "weekly_hours_cap": weekly, "credit_cap": cap,
                "interests": [i["topic"] for i in b["interests"]], "is_synthetic": True,
            })
        return out

    # ------------------------------------------------------------------ onboarding
    def _resolve_goal(self, goal_id: str) -> Goal:
        goal = self.goal_repo.get_by_id(goal_id)
        if goal:
            return goal
        goal_names = {
            "GOAL_EE_CORE_POWER": ("Power Systems & Smart Grid", "Core electrical engineering and smart grid operations"),
            "GOAL_EE_CORE_VLSI": ("Core VLSI & Semiconductor Engineering", "Semiconductor IC design and embedded hardware"),
            "GOAL_MM_ADVANCED_MATERIALS": ("Advanced Materials R&D & Physical Metallurgy", "Physical metallurgy, structural alloy design, and materials characterization"),
            "GOAL_MM_PROCESS_ENGINEER": ("Process Metallurgist (Iron & Steelmaking)", "Primary extraction, blast furnace operations, and steelmaking technology")
        }
        title, desc = goal_names.get(goal_id, ("Core Engineering Track", "Core discipline engineering"))
        return Goal(goal_id=goal_id, name=title, category="career", description=desc, source_id="DESIGN_TEAM")

    def load_from_bundle(self, bundle: Dict[str, Any], goal_id: Optional[str] = None, keep_runtime_evidence: bool = True) -> StudentProfile:
        """(Re)loads one student from a seed/DB bundle into memory, including the evidence ledger."""
        from app.services.diagnostic_service import diagnostic_service
        p = bundle["profile"]
        sid = p["student_id"]
        student = StudentProfile(
            student_id=sid, name=p.get("name") or sid, programme_id=p["programme_id"],
            current_semester=int(p["current_semester"]), cgpa=p.get("cgpa"), backlogs=int(p.get("backlogs") or 0),
            is_synthetic=True, created_at=datetime.now(timezone.utc), year=p.get("year"),
            first_year_track=p.get("first_year_track") or "A", edge_case_tags=list(p.get("edge_case_tags") or []),
            aims=p.get("aims"))
        self.students[sid] = student
        self.transcripts[sid] = list(bundle.get("courses", []))
        self.completed_courses[sid] = [c["course_id"] for c in bundle.get("courses", []) if not c.get("is_backlog")]
        self.backlog_courses[sid] = [c["course_id"] for c in bundle.get("courses", []) if c.get("is_backlog")]
        goals = bundle.get("goals", [])
        active = goal_id or next((g["goal_id"] for g in goals if g.get("status") == "active"), None) \
            or DEFAULT_GOALS.get(p["programme_id"], "GOAL_EE_CORE_POWER")
        self.goals[sid] = self._resolve_goal(active)
        self.previous_goals[sid] = [g["goal_id"] for g in goals if g.get("status") == "previous" and g["goal_id"] != active]
        self.interests[sid] = list(bundle.get("interests", []))
        self.aims_and_aspirations[sid] = p.get("aims") or "Excel in core engineering track"
        self.target_timelines.setdefault(sid, "By Semester 7 (Placement Season)")
        self.constraints[sid] = [
            Constraint(constraint_id=f"C_{sid}_{i}", student_id=sid, constraint_type=c["constraint_type"], parameters=c.get("parameters") or {})
            for i, c in enumerate(bundle.get("constraints", []))
        ]
        pref = bundle.get("preference")
        self.preferences[sid] = ([
            Preference(preference_id=f"P_{sid}_mode", student_id=sid, preference_type="learning_mode", value=pref["preferred_learning_mode"]),
            Preference(preference_id=f"P_{sid}_pace", student_id=sid, preference_type="pace", value=pref["pace"]),
        ] if pref else [])

        seeded = []
        for e in bundle.get("evidence", []):
            ts = e.get("recorded_at")
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            seeded.append(EvidenceItem(
                evidence_id=e["evidence_id"], student_id=sid, skill_id=e["skill_id"], source_type=e["source_type"],
                score=float(e["score"]), reliability=1.0, attempts=1, recorded_at=ts or datetime.now(timezone.utc),
                reliability_tier=e.get("reliability_tier") or None, notes=e.get("notes")))
        runtime = [ev for ev in diagnostic_service.evidence_ledger.get(sid, [])
                   if not (ev.evidence_id.startswith("EV_SEED_") or ev.evidence_id.startswith("EV_DB_"))] if keep_runtime_evidence else []
        diagnostic_service.set_ledger(sid, seeded + runtime)
        return student

    def student_exists(self, student_id: str) -> bool:
        """True for a student already loaded, in the seed or database, or in a persona roster (never fabricates one)."""
        if student_id in self.students:
            return True
        if self.get_bundle(student_id) is not None:
            return True
        return any(s["student_id"] == student_id for s in self._legacy_roster())

    def ensure_student_onboarded(self, student_id: str, goal_id: Optional[str] = None) -> StudentProfile:
        """Ensures the student is loaded in memory (seed / DB); an explicit goal_id selects the goal."""
        if student_id in self.students:
            if goal_id and self.goals.get(student_id) and self.goals[student_id].goal_id != goal_id:
                self.switch_goal(student_id, goal_id, persist=False)
            return self.students[student_id]

        bundle = self.get_bundle(student_id)
        if bundle:
            return self.load_from_bundle(bundle, goal_id=goal_id)

        target = next((s for s in self._legacy_roster() if s["student_id"] == student_id), None)
        if not target:
            # Never invent a profile (it used to create "Student <id>" with CGPA 8.0): callers get a 404 instead.
            raise StudentNotFoundError(student_id)
        prog = target["programme_id"]
        return self.onboard_student(
            student_id=target["student_id"], name=target["name"], programme_id=prog,
            current_semester=target["current_semester"], cgpa=target["cgpa"], backlogs=target["backlogs"],
            goal_id=goal_id or DEFAULT_GOALS.get(prog, "GOAL_EE_CORE_POWER"), completed_course_ids=target["completed_courses"])

    def switch_goal(self, student_id: str, new_goal_id: str, persist: bool = True) -> Goal:
        """Mid-degree goal switch: evidence, transcript and constraints are preserved; only the goal changes."""
        old = self.goals.get(student_id)
        new_goal = self._resolve_goal(new_goal_id)
        if old and old.goal_id != new_goal_id:
            prev = self.previous_goals.setdefault(student_id, [])
            if old.goal_id not in prev:
                prev.insert(0, old.goal_id)
        self.goals[student_id] = new_goal
        if persist:
            st = self.students.get(student_id)
            persistence.set_active_goal(student_id, new_goal_id, st.current_semester if st else None)
        return new_goal

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
        preferences: Optional[List[Dict[str, Any]]] = None,
        interests: Optional[List[Dict[str, Any]]] = None,
    ) -> StudentProfile:
        student = StudentProfile(
            student_id=student_id, name=name, programme_id=programme_id, current_semester=current_semester,
            cgpa=cgpa, backlogs=backlogs, is_synthetic=True, created_at=datetime.now(timezone.utc),
            year=(current_semester + 1) // 2, aims=aims_and_aspirations)
        self.students[student_id] = student
        self.completed_courses[student_id] = completed_course_ids or []
        self.backlog_courses.setdefault(student_id, [])
        self.transcripts.setdefault(student_id, [])
        self.aims_and_aspirations[student_id] = aims_and_aspirations or "Excel in core engineering track"
        self.target_timelines[student_id] = target_timeline or "By Semester 7 (Placement Season)"
        self.goals[student_id] = self._resolve_goal(goal_id)
        self.previous_goals.setdefault(student_id, [])
        self.interests[student_id] = list(interests or [])

        def norm(c: Dict[str, Any]) -> Constraint:
            ctype = c.get("constraint_type") or c.get("type", "study_hours")
            params = c.get("parameters") if isinstance(c.get("parameters"), dict) else c
            return Constraint(constraint_id=f"C_{student_id}_{ctype}", student_id=student_id, constraint_type=ctype, parameters=params)

        self.constraints[student_id] = [norm(c) for c in (constraints or [])]
        self.preferences[student_id] = [
            Preference(preference_id=f"P_{student_id}_{i}", student_id=student_id, preference_type=p.get("type", "mode"), value=p.get("value", "offline"))
            for i, p in enumerate(preferences or [])
        ]
        return student

    # ------------------------------------------------------------------ constraint helpers
    def set_constraint(self, student_id: str, constraint_type: str, parameters: Optional[Dict[str, Any]], persist: bool = True):
        aliases = {
            "weekly_hours": {"weekly_hours", "max_weekly_hours", "study_hours", "weekly_study_hours", "max_hours_per_week"},
            "credit_cap": {"credit_cap", "max_credits", "max_credits_per_sem"},
        }.get(constraint_type, {constraint_type})
        kept = [c for c in self.constraints.get(student_id, []) if c.constraint_type not in aliases]
        if parameters is not None:
            kept.append(Constraint(constraint_id=f"C_{student_id}_{constraint_type}", student_id=student_id,
                                   constraint_type=constraint_type, parameters=parameters))
        self.constraints[student_id] = kept
        if persist:
            persistence.replace_constraint(student_id, constraint_type, parameters)

    def add_avoid_course(self, student_id: str, course_id: str, persist: bool = True):
        cons = self.constraints.setdefault(student_id, [])
        if any(c.constraint_type == "avoid_course" and c.parameters.get("course_id") == course_id for c in cons):
            return
        cons.append(Constraint(constraint_id=f"C_{student_id}_AVOID_{course_id}", student_id=student_id,
                               constraint_type="avoid_course", parameters={"course_id": course_id}))
        if persist:
            persistence.add_avoid_course(student_id, course_id)

onboarding_service = OnboardingService()
