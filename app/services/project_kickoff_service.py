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
                "category": "Verified Competitive Research Fellowships & Internships",
                "opportunities": [
                    {
                        "name": "IIT Bhubaneswar Summer Undergraduate Research Grant for Excellence (SURGE)",
                        "organizer": "Dean (R&D), IIT Bhubaneswar",
                        "eligibility": "B.Tech students completing 2nd or 3rd year (Semesters 4 or 6) with CGPA >= 7.5 or top 10% in batch.",
                        "duration": "8 weeks (May–July)",
                        "stipend_and_support": "Fixed research fellowship stipend (~INR 6,000–8,000/month) plus subsidized on-campus hostel accommodation.",
                        "application_window": "February 15 – March 20 annually",
                        "official_url": "https://www.iitbbs.ac.in/research/internships"
                    },
                    {
                        "name": "DAAD WISE (Working Internships in Science and Engineering) - Germany",
                        "organizer": "German Academic Exchange Service (DAAD)",
                        "eligibility": "Full-time 3rd year B.Tech students (Semester 5/6) at premier Indian institutions (IITs/NITs) with CGPA >= 8.5.",
                        "duration": "2 to 3 months (between May and August at German university / research lab)",
                        "stipend_and_support": "Monthly scholarship of €934, lump-sum travel allowance (~€1,075), and comprehensive health/accident insurance.",
                        "application_window": "Portal opens in July; annual national deadline is November 1",
                        "official_url": "https://www.daad.in/en/find-funding/wise-program/"
                    },
                    {
                        "name": "Mitacs Globalink Research Internship (GRI) - Canada",
                        "organizer": "Mitacs Canada & Universities across 10 provinces",
                        "eligibility": "Full-time B.Tech students with 1 to 3 semesters remaining (typically after Sem 5 or 6) with CGPA >= 8.0.",
                        "duration": "12 consecutive weeks (between May and October)",
                        "stipend_and_support": "Full round-trip airfare, student visa fee reimbursement, housing/food stipend (~CAD $300/week), and emergency health coverage.",
                        "application_window": "Opens early August; application deadline late September",
                        "official_url": "https://www.mitacs.ca/en/programs/globalink/globalink-research-internship"
                    },
                    {
                        "name": "IISc / TIFR Visiting Students Research Programme (VSRP)",
                        "organizer": "Indian Institute of Science & Tata Institute of Fundamental Research",
                        "eligibility": "Pre-final year B.Tech students with strong mathematical/analytical coursework and CGPA >= 8.0.",
                        "duration": "6 to 8 weeks (June–July)",
                        "stipend_and_support": "On-campus accommodation, sleeper class round-trip train fare, and monthly stipend (~INR 7,000–10,000/month).",
                        "application_window": "December 15 – January 31 annually",
                        "official_url": "https://www.iisc.ac.in/academics/internships/"
                    }
                ]
            },
            {
                "category": "Graduate Admissions & GATE/GRE Timelines",
                "milestones": [
                    {
                        "pathway": "GATE (Graduate Aptitude Test in Engineering)",
                        "target_timing": "August–September of Semester 7 (Registration); February of Semester 8 (Exam)",
                        "purpose": "PSU recruitment (IOCL, NTPC, ONGC, BHEL) and direct M.Tech/Ph.D. admissions at IITs/IISc."
                    },
                    {
                        "pathway": "GRE & TOEFL / IELTS (International MS/Ph.D.)",
                        "target_timing": "June–August between Semester 6 and 7 (Exams); October–December (Fall admissions deadlines)",
                        "purpose": "Applications to US, European, and Canadian research universities with graduate assistantships."
                    },
                    {
                        "pathway": "IIT Bhubaneswar Department Research Electives",
                        "target_timing": "Semester 7 and Semester 8 Course Preregistration",
                        "purpose": "Enrolling in 600-level PG research electives aligned with your B.Tech thesis (BTP) topic."
                    }
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
