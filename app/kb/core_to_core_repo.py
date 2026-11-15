import os
import csv
from typing import List, Dict, Optional, Any
from app.contracts.core_to_core import (
    AcademicCalendarWeek,
    ResearchArea,
    AreaSkill,
    Faculty,
    FacultyArea,
    Paper,
    PaperChunk,
    PaperSkill,
    TasterTask,
    IndustryMilestone
)

class CoreToCoreRepo:
    """
    In-memory and file-backed repository for Core-to-Core knowledge base entities.
    Loaded from data/seed/core_to_core/ on startup.
    """
    def __init__(self, seed_dir: str = "data/seed/core_to_core"):
        self.seed_dir = seed_dir
        self.academic_calendar: List[AcademicCalendarWeek] = []
        self.research_areas: Dict[str, ResearchArea] = {}
        self.area_skills: List[AreaSkill] = []
        self.faculty: Dict[str, Faculty] = {}
        self.faculty_areas: List[FacultyArea] = []
        self.papers: Dict[str, Paper] = {}
        self.paper_chunks: List[PaperChunk] = []
        self.paper_skills: List[PaperSkill] = []
        self.taster_tasks: Dict[str, TasterTask] = {}
        self.industry_milestones: Dict[str, IndustryMilestone] = {}
        self._load()

    def _load(self):
        # 1. Academic Calendar
        cal_path = os.path.join(self.seed_dir, "academic_calendar.csv")
        if os.path.exists(cal_path):
            with open(cal_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.academic_calendar.append(AcademicCalendarWeek(
                        semester=r["semester"],
                        week_number=int(r["week_number"]),
                        week_start=r["week_start"],
                        week_type=r["week_type"],
                        calendar_factor=float(r["calendar_factor"]),
                        source_url=r["source_url"],
                        verified=r.get("verified", "True").lower() == "true"
                    ))

        # 2. Research Areas
        area_path = os.path.join(self.seed_dir, "research_areas.csv")
        if os.path.exists(area_path):
            with open(area_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.research_areas[r["area_id"]] = ResearchArea(
                        area_id=r["area_id"],
                        name=r["name"],
                        department=r["department"],
                        description=r["description"],
                        parent_area_id=r.get("parent_area_id") or None
                    )

        # 3. Area Skills
        as_path = os.path.join(self.seed_dir, "area_skills.csv")
        if os.path.exists(as_path):
            with open(as_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.area_skills.append(AreaSkill(
                        area_id=r["area_id"],
                        skill_id=r["skill_id"],
                        required_level=float(r["required_level"])
                    ))

        # 4. Faculty
        fac_path = os.path.join(self.seed_dir, "faculty.csv")
        if os.path.exists(fac_path):
            with open(fac_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    fid = r.get("faculty_id") or r.get("id")
                    self.faculty[fid] = Faculty(
                        id=fid,
                        name=r["name"],
                        department=r["department"],
                        designation=r["designation"],
                        lab_name=r.get("lab_name") or None,
                        profile_url=r["profile_url"],
                        email_public=r.get("email_public") or None,
                        takes_ug_students=r.get("takes_ug_students", "unknown"),
                        source_url=r["source_url"],
                        retrieved_on=r["retrieved_on"],
                        verified=r.get("verified", "True").lower() == "true"
                    )

        # 5. Faculty Areas
        fa_path = os.path.join(self.seed_dir, "faculty_areas.csv")
        if os.path.exists(fa_path):
            with open(fa_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.faculty_areas.append(FacultyArea(
                        faculty_id=r["faculty_id"],
                        area_id=r["area_id"],
                        weight=float(r.get("weight", 1.0))
                    ))

        # 6. Papers
        p_path = os.path.join(self.seed_dir, "papers.csv")
        if os.path.exists(p_path):
            with open(p_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    pid = r.get("paper_id") or r.get("id")
                    self.papers[pid] = Paper(
                        id=pid,
                        title=r["title"],
                        year=int(r["year"]),
                        venue=r["venue"],
                        doi_or_url=r["doi_or_url"],
                        abstract=r.get("abstract") or None,
                        open_access=r.get("open_access", "False").lower() == "true",
                        licence=r.get("licence") or None,
                        fulltext_path=r.get("fulltext_path") or None,
                        source_url=r["source_url"],
                        retrieved_on=r["retrieved_on"],
                        verified=r.get("verified", "True").lower() == "true"
                    )

        # 7. Paper Chunks
        chunk_path = os.path.join(self.seed_dir, "paper_chunks.csv")
        if os.path.exists(chunk_path):
            with open(chunk_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.paper_chunks.append(PaperChunk(
                        chunk_id=r["chunk_id"],
                        paper_id=r["paper_id"],
                        page=int(r["page"]),
                        chunk_index=int(r["chunk_index"]),
                        text=r["text"]
                    ))

        # 8. Paper Skills
        ps_path = os.path.join(self.seed_dir, "paper_skills.csv")
        if os.path.exists(ps_path):
            with open(ps_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.paper_skills.append(PaperSkill(
                        paper_id=r["paper_id"],
                        skill_id=r["skill_id"],
                        level=float(r["level"]),
                        reviewed=r.get("reviewed", "True").lower() == "true"
                    ))

        # 9. Taster Tasks
        tt_path = os.path.join(self.seed_dir, "taster_tasks.csv")
        if os.path.exists(tt_path):
            with open(tt_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.taster_tasks[r["id"]] = TasterTask(
                        id=r["id"],
                        area_id=r["area_id"],
                        kind=r["kind"],
                        prompt=r["prompt"],
                        rubric=r["rubric"],
                        est_minutes=int(r["est_minutes"])
                    )

        # 10. Industry Milestones
        im_path = os.path.join(self.seed_dir, "industry_milestones.csv")
        if os.path.exists(im_path):
            with open(im_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.industry_milestones[r["id"]] = IndustryMilestone(
                        id=r["id"],
                        department=r["department"],
                        name=r["name"],
                        kind=r["kind"],
                        typical_timing=r["typical_timing"],
                        related_exam_id=r.get("related_exam_id") or None,
                        source_url=r.get("source_url") or None
                    )

    def get_calendar_week(self, week_number: int) -> Optional[AcademicCalendarWeek]:
        for w in self.academic_calendar:
            if w.week_number == week_number:
                return w
        return None

    def get_faculty_by_id(self, faculty_id: str) -> Optional[Faculty]:
        return self.faculty.get(faculty_id)

    def get_faculty_by_department(self, dept: str) -> List[Faculty]:
        return [f for f in self.faculty.values() if f.department.upper() == dept.upper()]

    def get_faculty_areas(self, faculty_id: str) -> List[FacultyArea]:
        return [fa for fa in self.faculty_areas if fa.faculty_id == faculty_id]

    def get_papers_by_author(self, author_name: str) -> List[Paper]:
        author_clean = author_name.strip().lower()
        # Search via paper title or doi or matched author in metadata
        matching = []
        for p in self.papers.values():
            if author_clean in p.venue.lower() or author_clean in p.doi_or_url.lower():
                matching.append(p)
        return matching

    def get_chunks_for_paper(self, paper_id: str) -> List[PaperChunk]:
        return [c for c in self.paper_chunks if c.paper_id == paper_id]

    def get_skills_for_paper(self, paper_id: str) -> List[PaperSkill]:
        return [ps for ps in self.paper_skills if ps.paper_id == paper_id]

    def get_tasks_for_area(self, area_id: str) -> List[TasterTask]:
        return [t for t in self.taster_tasks.values() if t.area_id == area_id]

    def get_milestones_by_department(self, dept: str) -> List[IndustryMilestone]:
        return [m for m in self.industry_milestones.values() if m.department.upper() == dept.upper()]

core_kb_repo = CoreToCoreRepo()
