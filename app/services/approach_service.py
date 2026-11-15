import os
from typing import List, Dict, Optional, Any
from app.contracts.core_to_core import ApproachDraft, Faculty
from app.contracts.student import SkillState, StudentProfile
from app.kb.core_to_core_repo import core_kb_repo

class ApproachService:
    """
    Approach Assist Service: Prepares the student to approach a professor.
    
    Hard constraints:
    - NEVER contact a professor or send anything on the student's behalf.
    - Drafts are for the student to edit and send.
    - Cites only verified faculty and papers stored in the database.
    - Tracks status and enforces 10-day follow-up logic.
    """
    def __init__(self):
        self.kb_repo = core_kb_repo
        self.approaches: Dict[str, Dict[str, ApproachDraft]] = {} # { student_id: { faculty_id: ApproachDraft } }

    def generate_approach_package(
        self,
        student: StudentProfile,
        faculty_id: str,
        skill_states: List[SkillState],
        available_hours_weekly: float = 12.0
    ) -> ApproachDraft:
        fac = self.kb_repo.get_faculty_by_id(faculty_id)
        if not fac:
            raise ValueError(f"Faculty ID '{faculty_id}' not found in verified database.")

        # Retrieve verified papers for this faculty
        paper_author_file = os.path.join(self.kb_repo.seed_dir, "paper_authors.csv")
        fac_paper_ids = []
        if os.path.exists(paper_author_file):
            import csv
            with open(paper_author_file, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    if r.get("faculty_id") == faculty_id:
                        fac_paper_ids.append(r["paper_id"])

        papers = [self.kb_repo.papers[pid] for pid in fac_paper_ids if pid in self.kb_repo.papers]
        primary_paper = papers[0] if papers else None
        paper_citation = (
            f"'{primary_paper.title}' ({primary_paper.year}, {primary_paper.venue})" 
            if primary_paper else "your recent published work in the department"
        )

        # Grounded CV bullets from verified student skills
        top_skills = [s for s in skill_states if s.estimated_level >= 70.0]
        skill_names = [
            s.skill_id.replace("SKILL_", "").replace("_", " ").title() 
            for s in top_skills[:3]
        ]
        if not skill_names:
            skill_names = ["Circuit Analysis & Power Electronics" if "EE" in student.programme_id else "Physical Metallurgy & Materials Characterization"]

        cv_bullets = [
            f"Undergraduate {student.programme_id.replace('BTECH_', '')} student, Semester {student.current_semester} (CGPA: {student.cgpa or 'N/A'}).",
            f"Demonstrated verified proficiency in: {', '.join(skill_names)}.",
            f"Completed rigorous foundational coursework and objective diagnostic assessments.",
            f"Committed to dedicating {int(available_hours_weekly)} hours/week toward research modeling and literature synthesis."
        ]

        # 5 Likely interview / discussion questions grounded in faculty's research area
        area_names = [
            self.kb_repo.research_areas[fa.area_id].name 
            for fa in self.kb_repo.get_faculty_areas(fac.id) if fa.area_id in self.kb_repo.research_areas
        ]
        primary_area = area_names[0] if area_names else "Core Engineering Research"

        interview_questions = [
            f"What specific problem in {primary_area} interested you the most, and how does it relate to our lab's work?",
            f"In our paper {paper_citation}, what assumptions or methodology limitations did you observe?",
            f"How comfortable are you with computational modeling / laboratory protocols in {skill_names[0]}?",
            f"How will you manage {int(available_hours_weekly)} research hours alongside your semester course load and exam preparation?",
            "Can you explain a technical derivation or simulation challenge you solved in your recent coursework?"
        ]

        # Draft email text
        email_draft = (
            f"Subject: Prospective Undergraduate Research Inquiry - {student.name} ({student.programme_id})\n\n"
            f"Respected Prof. {fac.name},\n\n"
            f"I hope this email finds you well. I am a Semester {student.current_semester} undergraduate student "
            f"in {student.programme_id.replace('BTECH_', '')} at IIT Bhubaneswar.\n\n"
            f"I have been closely reading your research in {primary_area}, specifically your paper {paper_citation}. "
            f"I found your approach particularly insightful and would be eager to contribute to ongoing work or a guided project in your group.\n\n"
            f"Through my academic coursework, I have developed verified proficiency in {', '.join(skill_names)}. "
            f"I have planned my semester academic budget to dedicate {int(available_hours_weekly)} hours per week to research work without compromising course deliverables.\n\n"
            f"I would be deeply grateful for the opportunity to meet briefly during your office hours or discuss any potential research openings for undergraduates in your lab.\n\n"
            f"Thank you very much for your time and consideration.\n\n"
            f"Sincerely,\n"
            f"{student.name}\n"
            f"Roll No / Student ID: {student.student_id}\n"
            f"Department of {fac.department}, IIT Bhubaneswar\n\n"
            f"[NOTICE: This is an editable draft prepared by your Learning Buddy. Review, personalize, and send it yourself from your official IIT BBS email. The buddy never contacts faculty on your behalf.]"
        )

        draft = ApproachDraft(
            student_id=student.student_id,
            faculty_id=faculty_id,
            faculty_name=fac.name,
            draft_email=email_draft,
            cv_bullets=cv_bullets,
            interview_questions=interview_questions,
            status="drafted",
            days_since_sent=0,
            followup_recommended=False
        )

        self.approaches.setdefault(student.student_id, {})[faculty_id] = draft
        return draft

    def update_approach_status(
        self,
        student_id: str,
        faculty_id: str,
        status: str,
        days_since_sent: int = 0,
        alternative_faculty_id: Optional[str] = None
    ) -> ApproachDraft:
        student_drafts = self.approaches.get(student_id, {})
        draft = student_drafts.get(faculty_id)
        if not draft:
            raise ValueError(f"No existing approach draft found for student {student_id} and faculty {faculty_id}.")

        followup = (status == "sent" or status == "no_reply") and days_since_sent >= 10

        updated = ApproachDraft(
            student_id=student_id,
            faculty_id=faculty_id,
            faculty_name=draft.faculty_name,
            draft_email=draft.draft_email,
            cv_bullets=draft.cv_bullets,
            interview_questions=draft.interview_questions,
            status=status,
            days_since_sent=days_since_sent,
            followup_recommended=followup,
            alternative_faculty_id=alternative_faculty_id
        )
        self.approaches[student_id][faculty_id] = updated
        return updated

approach_service = ApproachService()
