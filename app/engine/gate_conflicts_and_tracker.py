from typing import List, Dict, Any, Optional, Tuple
from app.contracts.core_to_mtech import ConflictAlert, StudentApplication
from app.kb.core_to_mtech_repo import core_to_mtech_repo
from app.engine.budget import BudgetEngine

class GATEConflictsAndTrackerEngine:
    """
    Deterministic Application Tracker, Milestone Schedule, and Conflict Detection Engine (§8.6).
    Hard constraints:
    - Surfaces clashes explicitly: GATE prep vs campus placements, mock weeks vs end-sems, deadlines vs exams.
    - Provides explicit trade-off options and their cost; never silently overloads the student.
    - Checklists and deadlines are derived strictly from stored rows.
    """
    def __init__(self, repo=None, budget_engine=None):
        self.repo = repo or core_to_mtech_repo
        self.budget_engine = budget_engine or BudgetEngine()

    def detect_conflicts(
        self,
        current_week: int,
        placement_active: bool = False,
        placement_window_weeks: Tuple[int, int] = (6, 10),
        target_programmes: Optional[List[str]] = None
    ) -> List[ConflictAlert]:
        """
        Scans for academic calendar clashes, placement conflicts, and deadline collisions (§8.6).
        """
        conflicts: List[ConflictAlert] = []

        # 1. GATE Prep vs. Campus Placements
        if placement_active or (placement_window_weeks[0] <= current_week <= placement_window_weeks[1]):
            conflicts.append(ConflictAlert(
                kind="placement_clash",
                title="Conflict Alert: Campus Placement Drive vs. GATE Prep Peak",
                date_window=f"Semester Weeks {placement_window_weeks[0]}–{placement_window_weeks[1]} (Campus Placement Season)",
                severity="high",
                options=[
                    "Option A (Dual Track): Allocate 12 hrs/week to placement coding/tests, 8 hrs/week to high-weightage GATE topics (Math & Aptitude).",
                    "Option B (Placement Priority): Pause GATE mocks until placement phase ends, then switch to the 3-Month Fast-Track GATE template.",
                    "Option C (GATE Dedicated): Skip generic IT placements and focus 100% on GATE for PSU recruitment and top-tier M.Tech."
                ],
                trade_off_description=(
                    "Cost of Option A: Slower progress on both tracks but keeps both career safety and GATE viability alive. "
                    "Cost of Option B: Loss of early full mocks, requiring higher intensity in January. "
                    "Cost of Option C: Forfeits on-campus job offer security."
                )
            ))

        # 2. Mock Weeks vs. End-Semester Examination
        cal_week = self.budget_engine.get_calendar_week(current_week)
        if cal_week.week_type.lower() in ["midsem", "endsem", "exam"] or current_week in [14, 15, 16]:
            conflicts.append(ConflictAlert(
                kind="exam_clash",
                title="Conflict Alert: End-Semester Examinations vs. Full-Length Mocks",
                date_window=f"Week {current_week} ({cal_week.week_type})",
                severity="high",
                options=[
                    "Option A (Protect CGPA - Recommended): Suspend full 3-hour mocks during exam week. Allocate study hours exclusively to course revision.",
                    "Option B (Light Touch): Maintain 1 timed 45-minute sectional test on weekend; protect remaining time for semester papers."
                ],
                trade_off_description=(
                    "Trade-off: A low semester GPA permanently damages M.Tech/PSU qualifying eligibility. "
                    "Temporarily deferring 1 mock preserves your institute CGPA without harming long-term GATE retention."
                )
            ))

        # 3. Programme Application Deadlines vs. Semester Exams
        if target_programmes:
            for pid in target_programmes:
                prog = self.repo.programmes.get(pid)
                if prog and prog.application_deadline:
                    # If deadline falls around April / May exam periods
                    if "04-" in prog.application_deadline or "05-" in prog.application_deadline:
                        conflicts.append(ConflictAlert(
                            kind="deadline_clash",
                            title=f"Deadline Notice: {prog.specialisation} ({prog.institution_id})",
                            date_window=f"Deadline: {prog.application_deadline}",
                            severity="medium",
                            options=[
                                "Pre-fill portal registration and upload transcripts 2 weeks prior to avoid server congestion.",
                                "Set phone calendar reminder for portal fee payment verification."
                            ],
                            trade_off_description="Missing admission deadline forfeits counselling round consideration regardless of GATE score."
                        ))

        return conflicts

    def get_milestones_schedule(self, cycle: str = "2027") -> List[Dict[str, Any]]:
        """
        Gathers verified official milestones across GATE, COAP, CCMT, and PSUs (§8.6).
        """
        milestones = []

        # GATE cycle milestones
        for c in self.repo.exam_cycles.values():
            if c.cycle == cycle:
                milestones.append({
                    "event": "GATE Application Window",
                    "dates": f"{c.reg_open} to {c.reg_close}",
                    "source": c.source_url,
                    "verified": c.verified
                })
                milestones.append({
                    "event": "GATE Admit Card Release",
                    "dates": c.admit_card_date or "January 2027",
                    "source": c.source_url,
                    "verified": c.verified
                })
                milestones.append({
                    "event": "GATE Examination Dates",
                    "dates": c.exam_dates,
                    "source": c.source_url,
                    "verified": c.verified
                })
                milestones.append({
                    "event": "GATE Result Announcement",
                    "dates": c.result_date or "March 2027",
                    "source": c.source_url,
                    "verified": c.verified
                })

        # Counselling cycles (COAP / CCMT)
        for cc in self.repo.counselling_cycles.values():
            if cc.cycle == cycle:
                milestones.append({
                    "event": f"{cc.portal} Counselling Rounds",
                    "dates": cc.round_dates,
                    "source": cc.source_url,
                    "verified": cc.verified
                })

        return milestones

    def get_application_checklist(self, programme_id: str) -> Dict[str, Any]:
        """
        Returns structured application checklist for a programme (§8.6).
        """
        prog = self.repo.programmes.get(programme_id)
        is_research = prog.degree in ["MS(R)", "Direct PhD"] if prog else False

        checklist = [
            {"item": "Official GATE Scorecard (PDF downloaded from GOAPS portal)", "required": True, "done": False},
            {"item": "B.Tech Grade Sheets / Consolidated Transcript up to current semester", "required": True, "done": False},
            {"item": f"Registration on {prog.application_portal if prog else 'COAP'} portal", "required": True, "done": False},
            {"item": "Valid Category Certificate (OBC-NCL / EWS issued after April 1 of admission year, or SC/ST)", "required": True, "done": False},
            {"item": "Valid Govt Photo ID (Aadhaar / Passport / Voter ID)", "required": True, "done": False}
        ]

        if is_research:
            checklist.append({"item": "Statement of Purpose (SOP) tailored to department research areas (1-2 pages)", "required": True, "done": False})
            checklist.append({"item": "Research Proposal / Resume highlighting undergraduate projects and publications", "required": True, "done": False})

        return {
            "programme_id": programme_id,
            "degree": prog.degree if prog else "M.Tech",
            "specialisation": prog.specialisation if prog else "Engineering",
            "portal": prog.application_portal if prog else "COAP",
            "checklist": checklist
        }

# Global singleton
gate_conflicts_and_tracker_engine = GATEConflictsAndTrackerEngine()
