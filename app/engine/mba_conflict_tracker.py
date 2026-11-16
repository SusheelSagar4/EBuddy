from typing import List, Dict, Optional, Any
from app.contracts.core_to_mba import MBAApplicationChecklistItem, MBAExamCycle
from app.kb.core_to_mba_repo import core_to_mba_repo

class MBAConflictTrackerEngine:
    """
    Academic Conflict & Application Tracker Engine (§1.7, §7.6 & §11).
    Tracks institutional academic clashes, application document checklists, and verified deadlines.

    Non-negotiable product rule (§4):
    Zero unverified dates or deadlines presented to students. All deadlines come directly
    from verified rows in kb.mba_exam_cycle and kb.mba_programme.
    """
    def __init__(self, repo=None):
        self.repo = repo or core_to_mba_repo
        self.student_checklist_state: Dict[str, Dict[str, bool]] = {}

    def get_known_academic_clashes(self, semester: int = 7) -> List[Dict[str, Any]]:
        """
        Returns structured calendar clashes between IIT BBS academic milestones and MBA admission cycles.
        """
        clashes = [
            {
                "id": "CLASH-01",
                "milestone_a": "Semester 7 End-Semester Exams (Weeks 14-16, late Nov)",
                "milestone_b": "CAT Examination (Last Sunday of November)",
                "severity": "High",
                "recommended_mitigation": (
                    "Complete final CAT full-length mock simulation by Week 12. "
                    "In Weeks 14-16, throttle MBA study hours to <= 2 hrs/week and focus 100% on academic CGPA."
                )
            },
            {
                "id": "CLASH-02",
                "milestone_a": "Campus Placement Season Phase-1 (December Weeks 1-2)",
                "milestone_b": "XAT / SNAP Entrance Exams (December - early January)",
                "severity": "Medium",
                "recommended_mitigation": (
                    "If sitting for core campus placements, prepare technical interview basics in October. "
                    "Reserve weekends for timed speed drills rather than multi-hour full mocks during placement week."
                )
            },
            {
                "id": "CLASH-03",
                "milestone_a": "Semester 8 B.Tech Major Project Submission & Viva (April)",
                "milestone_b": "IIM and Top B-School WAT / Personal Interview Rounds (Feb - March)",
                "severity": "Medium",
                "recommended_mitigation": (
                    "Front-load major project simulation and experimental work in January before PI travel begins."
                )
            }
        ]
        return clashes

    def get_application_checklist(self, student_id: str, category: str = "GEN") -> Dict[str, Any]:
        """
        Returns application document requirements and current completion state.
        """
        norm_cat = category.upper().strip()
        student_state = self.student_checklist_state.setdefault(student_id, {})

        items: List[Dict[str, Any]] = []
        for chk in self.repo.application_checklist_items:  # a list (calling .values() crashed every request)
            # `applies_to` in the seed is descriptive text ("All programmes", "Only if claiming a category", ...), not a
            # category code, so matching it against "ALL" / the category dropped every item. Show each item with its
            # applicability note; the only case the data lets us decide is the category certificate for GEN.
            applies = chk.applies_to.lower()
            if "claiming a category" in applies and norm_cat == "GEN":
                continue

            is_done = student_state.get(chk.id, False)
            items.append({
                "item_id": chk.id,
                "document": chk.item,
                "applies_to": chk.applies_to,
                "is_completed": is_done
            })

        completed_count = sum(1 for it in items if it["is_completed"])
        return {
            "student_id": student_id,
            "category": norm_cat,
            "total_items": len(items),
            "completed_items": completed_count,
            "pending_items": len(items) - completed_count,
            "checklist": items
        }

    def update_checklist_item(self, student_id: str, item_id: str, completed: bool) -> Dict[str, Any]:
        """
        Toggles completion state of a student application document checklist item.
        """
        if not any(chk.id == item_id for chk in self.repo.application_checklist_items):
            raise KeyError(f"Unknown checklist item {item_id}")
        student_state = self.student_checklist_state.setdefault(student_id, {})
        student_state[item_id] = completed
        return {"student_id": student_id, "item_id": item_id, "completed": completed}

    def get_verified_deadlines(self) -> List[Dict[str, Any]]:
        """
        Returns all verified official entrance exam cycle and programme application deadlines.
        """
        deadlines: List[Dict[str, Any]] = []

        # 1. Exam Cycles
        for cycle in self.repo.exam_cycles:
            if not cycle.verified:
                continue
            exam = self.repo.exams.get(cycle.exam_id)
            exam_name = exam.name if exam else cycle.exam_id

            if cycle.reg_close:
                deadlines.append({
                    "entity": exam_name,
                    "event": f"{exam_name} Registration Deadline ({cycle.cycle})",
                    "date": cycle.reg_close,
                    "type": "exam_registration",
                    "source_url": cycle.source_url,
                    "verified": True
                })
            if cycle.exam_dates:
                deadlines.append({
                    "entity": exam_name,
                    "event": f"{exam_name} Examination Date ({cycle.cycle})",
                    "date": cycle.exam_dates,
                    "type": "exam_date",
                    "source_url": cycle.source_url,
                    "verified": True
                })

        # 2. Programme Deadlines
        for prog in self.repo.programmes.values():
            if not prog.verified or not prog.application_deadline:
                continue
            inst = self.repo.institutions.get(prog.institution_id)
            inst_name = inst.name if inst else prog.institution_id
            deadlines.append({
                "entity": inst_name,
                "event": f"{prog.programme_name} Application Deadline",
                "date": prog.application_deadline,
                "type": "programme_application",
                "source_url": prog.source_url,
                "verified": True
            })

        # Sort chronologically by date
        deadlines.sort(key=lambda x: x["date"])
        return deadlines

# Global Singleton
mba_conflict_tracker_engine = MBAConflictTrackerEngine()
