import os
import csv
from typing import List, Dict, Optional, Any
from app.contracts.core_to_mba import (
    MBARoute,
    MBAExam,
    MBAExamCycle,
    MBAExamSection,
    MBASyllabusTopic,
    MBAInstitution,
    MBAProgramme,
    MBAAdmissionStat,
    MBAMilestone,
    MBAPrepTemplate,
    MBATemplatePhase,
    MBAPracticeItem,
    MBAInterviewQuestion,
    MBAInterviewRubric,
    MBAApplicationChecklistItem,
    MBALearningMethod,
    MBAResource,
    CareerPath,
    BranchPITopic,
    BranchPIQuestion,
    ProfileAuditRubric,
    ProfileAction,
    StoryDraft,
    DecisionOption
)

class CoreToMBARepo:
    """
    In-memory and file-backed repository for general MBA entities and Core to MBA entities.
    Loads from data/seed/mba/ and data/seed/core_to_mba/.
    """
    def __init__(
        self,
        mba_seed_dir: str = "data/seed/mba",
        c2m_seed_dir: str = "data/seed/core_to_mba"
    ):
        self.mba_seed_dir = mba_seed_dir
        self.c2m_seed_dir = c2m_seed_dir

        # MBA entities
        self.routes: Dict[str, MBARoute] = {}
        self.exams: Dict[str, MBAExam] = {}
        self.exam_cycles: List[MBAExamCycle] = []
        self.exam_sections: List[MBAExamSection] = []
        self.syllabus_topics: Dict[str, MBASyllabusTopic] = {}
        self.institutions: Dict[str, MBAInstitution] = {}
        self.programmes: Dict[str, MBAProgramme] = {}
        self.admission_stats: List[MBAAdmissionStat] = []
        self.milestones: Dict[str, MBAMilestone] = {}
        self.prep_templates: Dict[str, MBAPrepTemplate] = {}
        self.template_phases: List[MBATemplatePhase] = []
        self.practice_items: Dict[str, MBAPracticeItem] = {}
        self.interview_questions: Dict[str, MBAInterviewQuestion] = {}
        self.interview_rubrics: Dict[str, MBAInterviewRubric] = {}
        self.application_checklist_items: List[MBAApplicationChecklistItem] = []
        self.learning_methods: Dict[str, MBALearningMethod] = {}
        self.resources: Dict[str, MBAResource] = {}

        # Core to MBA entities
        self.career_paths: Dict[str, CareerPath] = {}
        self.branch_pi_topics: Dict[str, BranchPITopic] = {}
        self.branch_pi_questions: Dict[str, BranchPIQuestion] = {}
        self.profile_audit_rubrics: Dict[str, ProfileAuditRubric] = {}
        self.profile_actions: Dict[str, ProfileAction] = {}
        self.story_drafts: List[StoryDraft] = []
        self.decision_options: List[DecisionOption] = []

        self._load()

    def _load(self):
        # 1. Routes
        f = os.path.join(self.mba_seed_dir, "mba_routes.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    self.routes[r["id"]] = MBARoute(**r)

        # 2. Exams
        f = os.path.join(self.mba_seed_dir, "mba_exams.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    r_dict = dict(r)
                    r_dict["verified"] = str(r_dict.get("verified", "FALSE")).lower() == "true"
                    r_dict["total_minutes"] = int(r_dict["total_minutes"]) if r_dict.get("total_minutes") else None
                    self.exams[r["id"]] = MBAExam(**r_dict)

        # 3. Exam Cycles
        f = os.path.join(self.mba_seed_dir, "mba_exam_cycles.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    r_dict = dict(r)
                    r_dict["verified"] = str(r_dict.get("verified", "FALSE")).lower() == "true"
                    r_dict["fee"] = r_dict.get("fee") or None
                    self.exam_cycles.append(MBAExamCycle(**r_dict))

        # 4. Exam Sections
        f = os.path.join(self.mba_seed_dir, "mba_exam_sections.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    r_dict = dict(r)
                    r_dict["verified"] = str(r_dict.get("verified", "FALSE")).lower() == "true"
                    r_dict["minutes"] = int(r_dict["minutes"]) if r_dict.get("minutes") else None
                    self.exam_sections.append(MBAExamSection(**r_dict))

        # 5. Syllabus Topics
        f = os.path.join(self.mba_seed_dir, "mba_syllabus_topics.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    r_dict = dict(r)
                    r_dict["verified"] = str(r_dict.get("verified", "FALSE")).lower() == "true"
                    self.syllabus_topics[r["id"]] = MBASyllabusTopic(**r_dict)

        # 6. Institutions
        f = os.path.join(self.mba_seed_dir, "mba_institutions.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    r_dict = dict(r)
                    r_dict["verified"] = str(r_dict.get("verified", "FALSE")).lower() == "true"
                    self.institutions[r["id"]] = MBAInstitution(**r_dict)

        # 7. Programmes
        f = os.path.join(self.mba_seed_dir, "mba_programmes.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    r_dict = dict(r)
                    r_dict["verified"] = str(r_dict.get("verified", "FALSE")).lower() == "true"
                    r_dict["duration_months"] = int(r_dict["duration_months"]) if r_dict.get("duration_months") else None
                    r_dict["fees"] = r_dict.get("fees") or None
                    self.programmes[r["id"]] = MBAProgramme(**r_dict)

        # 8. Admission Stats
        f = os.path.join(self.mba_seed_dir, "mba_admission_stats.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    r_dict = dict(r)
                    r_dict["verified"] = str(r_dict.get("verified", "FALSE")).lower() == "true"
                    r_dict["year"] = int(r_dict["year"]) if r_dict.get("year") else 2024
                    r_dict["cutoff_value"] = float(r_dict["cutoff_value"]) if r_dict.get("cutoff_value") else 90.0
                    self.admission_stats.append(MBAAdmissionStat(**r_dict))

        # 9. Milestones
        f = os.path.join(self.mba_seed_dir, "mba_milestones.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    self.milestones[r["id"]] = MBAMilestone(**r)

        # 10. Prep Templates
        f = os.path.join(self.mba_seed_dir, "mba_prep_templates.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    r_dict = dict(r)
                    r_dict["speed_months"] = int(r_dict["speed_months"])
                    r_dict["weekly_hours"] = int(r_dict["weekly_hours"])
                    self.prep_templates[r["id"]] = MBAPrepTemplate(**r_dict)

        # 11. Template Phases
        f = os.path.join(self.mba_seed_dir, "mba_template_phases.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    r_dict = dict(r)
                    r_dict["order"] = int(r_dict["order"])
                    r_dict["share_of_weeks"] = float(r_dict["share_of_weeks"])
                    self.template_phases.append(MBATemplatePhase(**r_dict))

        # 12. Practice Items
        f = os.path.join(self.mba_seed_dir, "mba_practice_items.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    r_dict = dict(r)
                    r_dict["difficulty"] = float(r_dict["difficulty"]) if r_dict.get("difficulty") else 1.0
                    r_dict["reviewed"] = str(r_dict.get("reviewed", "FALSE")).lower() == "true"
                    self.practice_items[r["id"]] = MBAPracticeItem(**r_dict)

        # 13. Interview Questions
        f = os.path.join(self.mba_seed_dir, "mba_interview_questions.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    self.interview_questions[r["id"]] = MBAInterviewQuestion(**r)

        # 14. Interview Rubric
        f = os.path.join(self.mba_seed_dir, "mba_interview_rubric.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    self.interview_rubrics[r["criterion"]] = MBAInterviewRubric(**r)

        # 15. Application Checklist Items
        f = os.path.join(self.mba_seed_dir, "mba_application_checklist_items.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    self.application_checklist_items.append(MBAApplicationChecklistItem(**r))

        # 16. Learning Methods
        f = os.path.join(self.mba_seed_dir, "mba_learning_methods.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    self.learning_methods[r["id"]] = MBALearningMethod(**r)

        # 17. Resources
        f = os.path.join(self.mba_seed_dir, "mba_resources.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    r_dict = dict(r)
                    r_dict["free"] = str(r_dict.get("free", "TRUE")).lower() == "true"
                    self.resources[r["id"]] = MBAResource(**r_dict)

        # ----------------------------------------------------
        # Core to MBA files
        # ----------------------------------------------------
        # 1. Career Paths
        f = os.path.join(self.c2m_seed_dir, "career_paths.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    r_dict = dict(r)
                    r_dict["reviewed"] = str(r_dict.get("reviewed", "FALSE")).lower() == "true"
                    self.career_paths[r["id"]] = CareerPath(**r_dict)

        # 2. Branch PI Topics
        f = os.path.join(self.c2m_seed_dir, "branch_pi_topics.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    r_dict = dict(r)
                    r_dict["reviewed"] = str(r_dict.get("reviewed", "FALSE")).lower() == "true"
                    self.branch_pi_topics[r["id"]] = BranchPITopic(**r_dict)

        # 3. Branch PI Questions
        f = os.path.join(self.c2m_seed_dir, "branch_pi_questions.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    r_dict = dict(r)
                    r_dict["reviewed"] = str(r_dict.get("reviewed", "FALSE")).lower() == "true"
                    self.branch_pi_questions[r["id"]] = BranchPIQuestion(**r_dict)

        # 4. Profile Audit Rubric
        f = os.path.join(self.c2m_seed_dir, "profile_audit_rubric.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    self.profile_audit_rubrics[r["criterion"]] = ProfileAuditRubric(**r)

        # 5. Profile Actions
        f = os.path.join(self.c2m_seed_dir, "profile_actions.csv")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    r_dict = dict(r)
                    r_dict["effort_hours"] = int(r_dict["effort_hours"]) if r_dict.get("effort_hours") else 4
                    r_dict["reviewed"] = str(r_dict.get("reviewed", "FALSE")).lower() == "true"
                    self.profile_actions[r["id"]] = ProfileAction(**r_dict)

    def get_phases_for_template(self, template_id: str) -> List[MBATemplatePhase]:
        return [p for p in self.template_phases if p.template_id == template_id]

    def get_career_paths_for_branch(self, branch: str) -> List[CareerPath]:
        norm_branch = "EE" if "EE" in branch.upper() else ("MM" if "MM" in branch.upper() else branch)
        return [cp for cp in self.career_paths.values() if cp.branch.upper() in [norm_branch.upper(), "ANY"]]

    def get_pi_questions_for_branch(self, branch: str) -> List[BranchPIQuestion]:
        norm_branch = "EE" if "EE" in branch.upper() else ("MM" if "MM" in branch.upper() else branch)
        return [q for q in self.branch_pi_questions.values() if q.branch.upper() == norm_branch.upper()]

# Global Singleton Instance
core_to_mba_repo = CoreToMBARepo()
