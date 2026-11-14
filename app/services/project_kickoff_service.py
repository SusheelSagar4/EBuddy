import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from app.contracts.core_to_core import ResearchMilestone, ResearchLogEntry, IndustryMilestone
from app.kb.core_to_core_repo import core_kb_repo

class ProjectKickoffService:
    """
    Project Kickoff & Milestone Tracking Service.
    
    Supports:
    - Core Research Track: Research milestones, guided research logs, and post-project next steps.
    - Core Industry Track: GATE timeline phases, simulation tool masteries, project clubs, and PSU/internship targets.
    """
    def __init__(self):
        self.kb_repo = core_kb_repo
        self.research_projects: Dict[str, Dict[str, Any]] = {}
        self.research_logs: Dict[str, List[ResearchLogEntry]] = {}

    def kickoff_research_project(
        self,
        student_id: str,
        faculty_id: str,
        project_title: str
    ) -> Dict[str, Any]:
        fac = self.kb_repo.get_faculty_by_id(faculty_id)
        fac_name = fac.name if fac else "Department Faculty"

        milestones = [
            ResearchMilestone(
                milestone_id=f"MILESTONE_RES_01_{uuid.uuid4().hex[:4]}",
                phase="Phase 1: Literature Synthesis & Problem Formulation",
                title="Comprehensive Literature Review & Baseline Reproduction",
                description=f"Read top publications from Prof. {fac_name}'s group; reproduce analytical baseline model.",
                target_week="Weeks 1-4",
                deliverable="Literature review report with cited equations and parameter table.",
                status="in_progress"
            ),
            ResearchMilestone(
                milestone_id=f"MILESTONE_RES_02_{uuid.uuid4().hex[:4]}",
                phase="Phase 2: Methodology & Simulation Setup",
                title="Simulation Formulation / Experimental Design",
                description="Formulate boundary conditions, code simulation scripts or laboratory protocol setup.",
                target_week="Weeks 5-8",
                deliverable="Validated simulation code / baseline experimental setup logs.",
                status="pending"
            ),
            ResearchMilestone(
                milestone_id=f"MILESTONE_RES_03_{uuid.uuid4().hex[:4]}",
                phase="Phase 3: Execution & Comparative Analysis",
                title="Parametric Testing & Results Verification",
                description="Execute comparative test matrix; benchmark performance against existing published literature.",
                target_week="Weeks 9-12",
                deliverable="Comparative result plots, error convergence curves, and discussion notes.",
                status="pending"
            ),
            ResearchMilestone(
                milestone_id=f"MILESTONE_RES_04_{uuid.uuid4().hex[:4]}",
                phase="Phase 4: Manuscript Preparation & Next Steps",
                title="Technical Report & Pre-print Drafting",
                description="Compile technical paper draft following IEEE/Springer LaTeX templates; review with advisor.",
                target_week="Weeks 13-16",
                deliverable="Full manuscript draft and project repository archive.",
                status="pending"
            )
        ]

        next_steps = [
            {
                "category": "Research Internships",
                "recommendations": [
                    "IIT Bhubaneswar SURGE / Winter Research Fellowships",
                    "DAAD WISE / Mitacs Globalink (Target deadline: August-September)",
                    "IISc / TIFR Summer Research Programs"
                ]
            },
            {
                "category": "Graduate Admissions & GATE/GRE",
                "recommendations": [
                    "GATE registration (August-September, Sem 7)",
                    "GRE / TOEFL preparation timeline for international MS/Ph.D. programs",
                    "Target Department Research Electives (600-level PG courses in Sem 7-8)"
                ]
            }
        ]

        project_data = {
            "student_id": student_id,
            "faculty_id": faculty_id,
            "faculty_name": fac_name,
            "project_title": project_title,
            "started_at": datetime.now().strftime("%Y-%m-%d"),
            "status": "active",
            "milestones": [m.model_dump() for m in milestones],
            "next_steps": next_steps
        }
        self.research_projects[student_id] = project_data
        return project_data

    def log_research_progress(
        self,
        student_id: str,
        week_number: int,
        summary: str,
        findings: str,
        blockers: Optional[str] = None
    ) -> ResearchLogEntry:
        entry = ResearchLogEntry(
            entry_id=f"LOG_{student_id}_{week_number}_{uuid.uuid4().hex[:4]}",
            student_id=student_id,
            week_number=week_number,
            summary=summary,
            findings=findings,
            blockers=blockers,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        self.research_logs.setdefault(student_id, []).append(entry)
        return entry

    def get_industry_roadmap(self, department: str) -> Dict[str, Any]:
        """
        Retrieves core-industry branch milestones: GATE route, tools, project clubs, PSU internships.
        """
        dept = "EE" if "EE" in department.upper() else "MM"
        milestones = self.kb_repo.get_milestones_by_department(dept)

        # Categorize
        gate_phases = [m.model_dump() for m in milestones if m.kind == "exam"]
        tool_skills = [m.model_dump() for m in milestones if m.kind == "tool_skill"]
        project_clubs = [m.model_dump() for m in milestones if m.kind == "project_club"]
        internships = [m.model_dump() for m in milestones if m.kind == "internship"]

        return {
            "department": dept,
            "track": "Core Industry / PSU Route",
            "summary": (
                "Personalized path focusing on GATE exam benchmarks, industrial design and simulation tools, "
                "engineering project clubs, and core PSU / corporate internship eligibility."
            ),
            "gate_preparation_phases": gate_phases,
            "simulation_and_design_tools": tool_skills,
            "project_clubs_and_competitions": project_clubs,
            "core_internships_and_psus": internships
        }

project_kickoff_service = ProjectKickoffService()
