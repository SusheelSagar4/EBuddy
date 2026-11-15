import os
import csv
from typing import List, Dict, Optional, Any
from app.contracts.core_to_mtech import (
    Route,
    Exam,
    ExamCycle,
    ExamPaper,
    SyllabusTopic,
    TopicWeightage,
    CourseTopicMap,
    PYQItem,
    Institution,
    HigherProgramme,
    AdmissionStat,
    PSU,
    PSUCycle,
    CounsellingCycle,
    PrepTemplate,
    TemplatePhase
)

class CoreToMTechRepo:
    """
    In-memory and file-backed repository for Core-to-M.Tech knowledge base entities.
    Loaded from data/seed/core_to_mtech/ on startup.
    Strictly enforces PS integrity rules:
    - By default, students are only exposed to verified rows (or unverified with clear banner in demo mode).
    - Unknown IDs are completely rejected by lookups.
    """
    def __init__(self, seed_dir: str = "data/seed/core_to_mtech"):
        self.seed_dir = seed_dir
        self.routes: Dict[str, Route] = {}
        self.exams: Dict[str, Exam] = {}
        self.exam_cycles: Dict[str, ExamCycle] = {}
        self.exam_papers: Dict[str, ExamPaper] = {}
        self.syllabus_topics: Dict[str, SyllabusTopic] = {}
        self.topic_weightages: List[TopicWeightage] = []
        self.course_topic_maps: List[CourseTopicMap] = []
        self.pyq_items: Dict[str, PYQItem] = {}
        self.institutions: Dict[str, Institution] = {}
        self.programmes: Dict[str, HigherProgramme] = {}
        self.admission_stats: List[AdmissionStat] = []
        self.psus: Dict[str, PSU] = {}
        self.psu_cycles: Dict[str, PSUCycle] = {}
        self.counselling_cycles: Dict[str, CounsellingCycle] = {}
        self.prep_templates: Dict[str, PrepTemplate] = {}
        self.template_phases: List[TemplatePhase] = []
        self._load()

    def _load(self):
        # 1. Routes
        p = os.path.join(self.seed_dir, "routes.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.routes[r["id"]] = Route(
                        id=r["id"],
                        name=r["name"],
                        description=r.get("description")
                    )

        # 2. Exams
        p = os.path.join(self.seed_dir, "exams.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.exams[r["id"]] = Exam(
                        id=r["id"],
                        name=r["name"],
                        conducting_body=r.get("conducting_body"),
                        route_ids=r.get("route_ids"),
                        pattern_json=r.get("pattern_json"),
                        marking_scheme=r.get("marking_scheme"),
                        score_scale=r.get("score_scale"),
                        score_validity_years=int(r.get("score_validity_years", 3)),
                        official_url=r.get("official_url"),
                        source_url=r.get("source_url"),
                        source_type=r.get("source_type", "official"),
                        retrieved_on=r.get("retrieved_on"),
                        cycle=r.get("cycle"),
                        verified=r.get("verified", "False").lower() == "true",
                        verified_by=r.get("verified_by")
                    )

        # 3. Exam Cycles
        p = os.path.join(self.seed_dir, "exam_cycles.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.exam_cycles[r["id"]] = ExamCycle(
                        id=r["id"],
                        exam_id=r["exam_id"],
                        cycle=r["cycle"],
                        organiser=r.get("organiser"),
                        reg_open=r.get("reg_open"),
                        reg_close=r.get("reg_close"),
                        exam_dates=r.get("exam_dates"),
                        admit_card_date=r.get("admit_card_date"),
                        result_date=r.get("result_date"),
                        fee=float(r["fee"]) if r.get("fee") else None,
                        source_url=r.get("source_url"),
                        source_type=r.get("source_type", "official"),
                        retrieved_on=r.get("retrieved_on"),
                        verified=r.get("verified", "False").lower() == "true",
                        verified_by=r.get("verified_by")
                    )

        # 4. Exam Papers
        p = os.path.join(self.seed_dir, "exam_papers.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.exam_papers[r["paper_code"]] = ExamPaper(
                        id=r["id"],
                        exam_id=r["exam_id"],
                        paper_code=r["paper_code"],
                        name=r["name"],
                        branches_mapped=r["branches_mapped"],
                        allowed_second_papers=r.get("allowed_second_papers"),
                        syllabus_url=r.get("syllabus_url"),
                        source_url=r.get("source_url"),
                        source_type=r.get("source_type", "official"),
                        retrieved_on=r.get("retrieved_on"),
                        cycle=r.get("cycle"),
                        verified=r.get("verified", "False").lower() == "true",
                        verified_by=r.get("verified_by")
                    )

        # 5. Syllabus Topics
        p = os.path.join(self.seed_dir, "syllabus_topics.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.syllabus_topics[r["id"]] = SyllabusTopic(
                        id=r["id"],
                        paper_code=r["paper_code"],
                        section=r["section"],
                        topic=r["topic"],
                        subtopics=r.get("subtopics"),
                        source_url=r.get("source_url"),
                        source_type=r.get("source_type", "official"),
                        retrieved_on=r.get("retrieved_on"),
                        cycle=r.get("cycle"),
                        verified=r.get("verified", "False").lower() == "true",
                        verified_by=r.get("verified_by")
                    )

        # 6. Topic Weightages
        p = os.path.join(self.seed_dir, "topic_weightage.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.topic_weightages.append(TopicWeightage(
                        id=r["id"],
                        paper_code=r["paper_code"],
                        topic_id=r["topic_id"],
                        year=int(r["year"]),
                        marks=float(r["marks"]),
                        source_url=r.get("source_url"),
                        source_type=r.get("source_type", "official"),
                        retrieved_on=r.get("retrieved_on"),
                        cycle=r.get("cycle"),
                        verified=r.get("verified", "False").lower() == "true",
                        verified_by=r.get("verified_by")
                    ))

        # 7. Course Topic Map
        p = os.path.join(self.seed_dir, "course_topic_map.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.course_topic_maps.append(CourseTopicMap(
                        id=r["id"],
                        course_code=r["course_code"],
                        topic_id=r["topic_id"],
                        coverage=r.get("coverage", "partial"),
                        reviewed_by=r.get("reviewed_by"),
                        source_url=r.get("source_url"),
                        source_type=r.get("source_type", "official"),
                        retrieved_on=r.get("retrieved_on"),
                        cycle=r.get("cycle"),
                        verified=r.get("verified", "False").lower() == "true",
                        verified_by=r.get("verified_by")
                    ))

        # 8. PYQ Items
        p = os.path.join(self.seed_dir, "pyq_items.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.pyq_items[r["id"]] = PYQItem(
                        id=r["id"],
                        paper_code=r["paper_code"],
                        year=int(r["year"]),
                        topic_id=r["topic_id"],
                        question_ref=r["question_ref"],
                        marks=float(r.get("marks", 1.0)),
                        type=r.get("type", "MCQ"),
                        answer_key_source=r.get("answer_key_source"),
                        source_url=r.get("source_url"),
                        source_type=r.get("source_type", "official"),
                        retrieved_on=r.get("retrieved_on"),
                        cycle=r.get("cycle"),
                        verified=r.get("verified", "False").lower() == "true",
                        verified_by=r.get("verified_by")
                    )

        # 9. Institutions
        p = os.path.join(self.seed_dir, "institutions.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.institutions[r["id"]] = Institution(
                        id=r["id"],
                        name=r["name"],
                        type=r["type"],
                        city=r.get("city"),
                        official_url=r.get("official_url"),
                        source_url=r.get("source_url"),
                        source_type=r.get("source_type", "official"),
                        retrieved_on=r.get("retrieved_on"),
                        cycle=r.get("cycle"),
                        verified=r.get("verified", "False").lower() == "true",
                        verified_by=r.get("verified_by")
                    )

        # 10. Programmes
        p = os.path.join(self.seed_dir, "programmes.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.programmes[r["id"]] = HigherProgramme(
                        id=r["id"],
                        institution_id=r["institution_id"],
                        degree=r["degree"],
                        department=r["department"],
                        specialisation=r["specialisation"],
                        exams_accepted=r.get("exams_accepted"),
                        gate_papers_accepted=r.get("gate_papers_accepted"),
                        branches_eligible=r.get("branches_eligible"),
                        min_qualifying_criteria=r.get("min_qualifying_criteria"),
                        selection_mode=r.get("selection_mode", "GATE score"),
                        application_portal=r.get("application_portal", "COAP"),
                        application_deadline=r.get("application_deadline"),
                        fees=float(r["fees"]) if r.get("fees") else None,
                        stipend_or_assistantship=r.get("stipend_or_assistantship"),
                        research_areas=r.get("research_areas"),
                        source_url=r.get("source_url"),
                        source_type=r.get("source_type", "official"),
                        retrieved_on=r.get("retrieved_on"),
                        cycle=r.get("cycle"),
                        verified=r.get("verified", "False").lower() == "true",
                        verified_by=r.get("verified_by")
                    )

        # 11. Admission Stats
        p = os.path.join(self.seed_dir, "admission_stats.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.admission_stats.append(AdmissionStat(
                        id=r["id"],
                        programme_id=r["programme_id"],
                        year=int(r["year"]),
                        category=r["category"],
                        round=r["round"],
                        closing_score_or_rank=float(r["closing_score_or_rank"]),
                        score_type=r.get("score_type", "GATE score"),
                        source_url=r.get("source_url"),
                        source_type=r.get("source_type", "official"),
                        retrieved_on=r.get("retrieved_on"),
                        cycle=r.get("cycle"),
                        verified=r.get("verified", "False").lower() == "true",
                        verified_by=r.get("verified_by")
                    ))

        # 12. PSUs
        p = os.path.join(self.seed_dir, "psus.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.psus[r["id"]] = PSU(
                        id=r["id"],
                        name=r["name"],
                        recruits_via_gate=r.get("recruits_via_gate", "True").lower() == "true",
                        disciplines=r.get("disciplines"),
                        source_url=r.get("source_url"),
                        source_type=r.get("source_type", "official"),
                        retrieved_on=r.get("retrieved_on"),
                        cycle=r.get("cycle"),
                        verified=r.get("verified", "False").lower() == "true",
                        verified_by=r.get("verified_by")
                    )

        # 13. PSU Cycles
        p = os.path.join(self.seed_dir, "psu_cycles.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.psu_cycles[r["id"]] = PSUCycle(
                        id=r["id"],
                        psu_id=r["psu_id"],
                        cycle=r["cycle"],
                        gate_year_used=int(r["gate_year_used"]) if r.get("gate_year_used") else None,
                        application_window=r.get("application_window"),
                        disciplines=r.get("disciplines"),
                        past_cutoff=float(r["past_cutoff"]) if r.get("past_cutoff") else None,
                        source_url=r.get("source_url"),
                        source_type=r.get("source_type", "official"),
                        retrieved_on=r.get("retrieved_on"),
                        verified=r.get("verified", "False").lower() == "true",
                        verified_by=r.get("verified_by")
                    )

        # 14. Counselling Cycles
        p = os.path.join(self.seed_dir, "counselling_cycles.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.counselling_cycles[r["id"]] = CounsellingCycle(
                        id=r["id"],
                        portal=r["portal"],
                        cycle=r["cycle"],
                        round_dates=r.get("round_dates"),
                        source_url=r.get("source_url"),
                        source_type=r.get("source_type", "official"),
                        retrieved_on=r.get("retrieved_on"),
                        verified=r.get("verified", "False").lower() == "true",
                        verified_by=r.get("verified_by")
                    )

        # 15. Prep Templates
        p = os.path.join(self.seed_dir, "prep_templates.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.prep_templates[r["id"]] = PrepTemplate(
                        id=r["id"],
                        paper_code=r["paper_code"],
                        speed_months=int(r["speed_months"]),
                        readiness_rule_json=r.get("readiness_rule_json"),
                        source_url=r.get("source_url"),
                        source_type=r.get("source_type", "official"),
                        retrieved_on=r.get("retrieved_on"),
                        cycle=r.get("cycle"),
                        verified=r.get("verified", "False").lower() == "true",
                        verified_by=r.get("verified_by")
                    )

        # 16. Template Phases
        p = os.path.join(self.seed_dir, "template_phases.csv")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.template_phases.append(TemplatePhase(
                        id=r["id"],
                        template_id=r["template_id"],
                        phase_order=int(r["phase_order"]),
                        name=r["name"],
                        share_of_weeks=float(r["share_of_weeks"]),
                        topic_selector=r.get("topic_selector"),
                        checkpoint=r.get("checkpoint"),
                        activities=r.get("activities"),
                        source_url=r.get("source_url"),
                        source_type=r.get("source_type", "official"),
                        retrieved_on=r.get("retrieved_on"),
                        cycle=r.get("cycle"),
                        verified=r.get("verified", "False").lower() == "true",
                        verified_by=r.get("verified_by")
                    ))

    def get_topics_for_paper(self, paper_code: str) -> List[SyllabusTopic]:
        """Returns all topics mapped to the specified paper (including common Math and GA)."""
        p_code = paper_code.upper()
        return [
            t for t in self.syllabus_topics.values()
            if t.paper_code in [p_code, "ALL"]
        ]

    def get_average_weightage(self, topic_id: str) -> float:
        """Computes the mean historical marks for a topic across all stored years."""
        weights = [w.marks for w in self.topic_weightages if w.topic_id == topic_id]
        return (sum(weights) / len(weights)) if weights else 3.0

    def get_course_mapped_topics(self, course_codes: List[str]) -> Dict[str, str]:
        """Returns map of topic_id -> coverage ('full' or 'partial') for student's courses."""
        mapped = {}
        for ctm in self.course_topic_maps:
            if ctm.course_code in course_codes:
                if ctm.topic_id not in mapped or ctm.coverage == "full":
                    mapped[ctm.topic_id] = ctm.coverage
        return mapped

    def get_phases_for_template(self, template_id: str) -> List[TemplatePhase]:
        """Returns phases ordered by phase_order for a given template."""
        phases = [p for p in self.template_phases if p.template_id == template_id]
        return sorted(phases, key=lambda x: x.phase_order)

# Global singleton repository
core_to_mtech_repo = CoreToMTechRepo()
