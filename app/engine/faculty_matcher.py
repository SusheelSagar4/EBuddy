import os
import math
from typing import List, Dict, Optional, Any
from app.contracts.core_to_core import Faculty, FacultyMatch, Paper
from app.contracts.student import SkillState
from app.kb.core_to_core_repo import core_kb_repo
from app.llm.client import llm_client

class FacultyMatcherEngine:
    """
    Deterministic Faculty Matching and Ranking Engine.
    
    Weights:
    - Area similarity (w1 = 0.40): Area overlap and description relevance.
    - Skill fit (w2 = 0.30): Student skill proficiency vs required paper skills.
    - UG availability (w3 = 0.15): takes_ug_students flag (yes: 1.0, unknown: 0.5, no: 0.0).
    - Publication recency (w4 = 0.15): Active recent papers in the library.
    
    Grounding rule: Never fabricate faculty or papers. Every recommendation cites
    exact IDs, titles, and public profile links from seed data.
    """
    def __init__(self):
        self.kb_repo = core_kb_repo
        self.w1 = 0.40
        self.w2 = 0.30
        self.w3 = 0.15
        self.w4 = 0.15

    def rank_faculty(
        self,
        student_department: str,
        target_area_ids: List[str],
        skill_states: List[SkillState],
        interest_text: Optional[str] = None,
        top_k: int = 5
    ) -> List[FacultyMatch]:
        # Filter faculty by department (EE or MM)
        dept = "EE" if "EE" in student_department.upper() else "MM"
        all_faculty = self.kb_repo.get_faculty_by_department(dept)

        student_skills = {s.skill_id: s.estimated_level / 100.0 for s in skill_states}
        matches = []

        # Pre-group papers by faculty ID from paper_authors.csv or heuristics
        # In our seed data, papers are mapped by faculty_id or author order
        paper_author_file = os.path.join(self.kb_repo.seed_dir, "paper_authors.csv")
        fac_papers_map: Dict[str, List[str]] = {}
        if os.path.exists(paper_author_file):
            import csv
            with open(paper_author_file, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    fid = r.get("faculty_id")
                    if fid:
                        fac_papers_map.setdefault(fid, []).append(r["paper_id"])

        for fac in all_faculty:
            # 1. Area Similarity (w1)
            fac_areas = self.kb_repo.get_faculty_areas(fac.id)
            fac_area_ids = [fa.area_id for fa in fac_areas]
            
            overlap = [aid for aid in target_area_ids if aid in fac_area_ids]
            if target_area_ids:
                sim_score = len(overlap) / float(len(target_area_ids))
            else:
                sim_score = 0.5 if fac_area_ids else 0.2

            # 2. Skill Fit (w2)
            # Find required skills from papers associated with this faculty
            p_ids = fac_papers_map.get(fac.id, [])
            paper_objs = [self.kb_repo.papers[pid] for pid in p_ids if pid in self.kb_repo.papers]
            
            req_skills = set()
            for pid in p_ids:
                for ps in self.kb_repo.get_skills_for_paper(pid):
                    req_skills.add(ps.skill_id)

            if req_skills:
                skill_scores = [student_skills.get(sid, 0.4) for sid in req_skills]
                skill_fit_score = sum(skill_scores) / float(len(skill_scores))
            else:
                # Fallback to general area skill requirement
                area_skill_ids = [
                    ask.skill_id for ask in self.kb_repo.area_skills if ask.area_id in fac_area_ids
                ]
                if area_skill_ids:
                    skill_scores = [student_skills.get(sid, 0.4) for sid in area_skill_ids]
                    skill_fit_score = sum(skill_scores) / float(len(skill_scores))
                else:
                    skill_fit_score = 0.6

            # 3. UG Availability (w3)
            avail_flag = fac.takes_ug_students.lower()
            if avail_flag == "yes":
                avail_score = 1.0
            elif avail_flag == "unknown":
                avail_score = 0.5
            else:
                avail_score = 0.0

            # 4. Publication Recency (w4)
            recent_count = sum(1 for p in paper_objs if p.year >= 2020)
            recency_score = min(1.0, recent_count / 3.0) if paper_objs else 0.4

            # Compute combined deterministic score
            total_score = (
                (self.w1 * sim_score) +
                (self.w2 * skill_fit_score) +
                (self.w3 * avail_score) +
                (self.w4 * recency_score)
            )

            # Format cited papers (top 2)
            cited_papers_data = []
            for p in paper_objs[:2]:
                cited_papers_data.append({
                    "paper_id": p.id,
                    "title": p.title,
                    "year": p.year,
                    "venue": p.venue,
                    "doi_or_url": p.doi_or_url,
                    "open_access": p.open_access
                })

            # Grounded reason
            area_names = [
                self.kb_repo.research_areas[aid].name 
                for aid in overlap if aid in self.kb_repo.research_areas
            ]
            areas_str = ", ".join(area_names) if area_names else "Core Department Research"
            reason = (
                f"Specializes in {areas_str}. "
                f"Published {len(paper_objs)} verified works in the IIT BBS library. "
                f"Undergraduate Mentorship: {fac.takes_ug_students.capitalize()}."
            )

            matches.append(FacultyMatch(
                faculty_id=fac.id,
                name=fac.name,
                department=fac.department,
                designation=fac.designation,
                lab_name=fac.lab_name,
                profile_url=fac.profile_url,
                takes_ug_students=fac.takes_ug_students,
                match_score=round(total_score, 3),
                score_breakdown={
                    "area_similarity": round(sim_score, 2),
                    "skill_fit": round(skill_fit_score, 2),
                    "ug_availability": round(avail_score, 2),
                    "publication_recency": round(recency_score, 2)
                },
                overlapping_areas=overlap,
                cited_papers=cited_papers_data,
                match_reason=reason
            ))

        # Sort descending by match_score
        matches.sort(key=lambda m: m.match_score, reverse=True)
        return matches[:top_k]

faculty_matcher_engine = FacultyMatcherEngine()
