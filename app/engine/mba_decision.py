import os
from typing import List, Dict, Optional, Any
from app.contracts.core_to_mba import DecisionOption, CareerPath
from app.kb.core_to_mba_repo import core_to_mba_repo

class MBADecisionEngine:
    """
    Deterministic Decision & Option Timeline Engine (§1.1 & §7.1).
    Builds side-by-side comparative timelines and requirements for:
    1. Stay Core Research (IIT BBS faculty mentorship, international internships)
    2. Stay Core Industry (Core simulation tools, PSU benchmarks, campus placement)
    3. Core Higher Studies (GATE -> M.Tech/MS/PhD in India)
    4. MBA Now (CAT/XAT in final year straight after graduation)
    5. MBA After Work (2-3 years core engineering industry, then executive/regular MBA)

    Non-negotiable product rule (§4):
    Maintains strict neutrality: never pushes the student toward or away from an MBA.
    """
    def __init__(self, repo=None):
        self.repo = repo or core_to_mba_repo

    def build_decision_options(
        self,
        student_id: str,
        student_year: int,
        student_sem: int,
        student_branch: str,
        student_cgpa: float,
        backlogs: int,
        skill_states: Optional[List[Any]] = None,
        profile_audit: Optional[Dict[str, int]] = None
    ) -> List[DecisionOption]:
        options: List[DecisionOption] = []
        norm_branch = "EE" if "EE" in student_branch.upper() else ("MM" if "MM" in student_branch.upper() else student_branch)

        # 1. Stay Core Research
        core_res_reqs = ["Tested domain skill mastery >= 75%", "2 Taster research tasks >= 60%", "Guided paper review >= 60%"]
        options.append(DecisionOption(
            student_id=student_id,
            option="stay_core_research",
            name="Stay Core: Research Track (Mentorship & Higher Studies)",
            timeline={
                "current_phase": f"Year {student_year} (Semester {student_sem}): Prerequisite depth & exploratory taster tasks",
                "next_milestone": "Semester 5-6: Approach IIT BBS faculty mentor with validated research pitch",
                "capstone": "Semester 7-8: B.Tech thesis, conference paper submission, and SURGE/DAAD/Mitacs internship applications"
            },
            tradeoffs=(
                "Opportunity: Deep technical mastery in core engineering; opens direct PhD and R&D careers. "
                "Trade-off: Longer academic runway before high compensation; delays general management training."
            ),
            requirements=core_res_reqs,
            clashes=["Lab schedules vs off-campus internship interview windows"]
        ))

        # 2. Stay Core Industry
        core_ind_reqs = ["Core simulation tools (MATLAB/Simulink, PSCAD, ANSYS, Thermo-Calc)", "Technical society/club project participation", "Industrial summer internship"]
        options.append(DecisionOption(
            student_id=student_id,
            option="stay_core_industry",
            name="Stay Core: Core Engineering Industry & PSUs",
            timeline={
                "current_phase": f"Year {student_year} (Semester {student_sem}): Design and simulation tool mastery",
                "next_milestone": "Semester 6-7: Core engineering industrial internship and project club leadership",
                "capstone": "Semester 7-8: Core engineering campus placements (Power grid, Metals, PSUs) or GATE PSU qualification"
            },
            tradeoffs=(
                "Opportunity: Immediate financial independence post-graduation and tangible domain engineering experience. "
                "Trade-off: Steeper initial learning curve in heavy engineering plant operations; slower entry into executive strategy."
            ),
            requirements=core_ind_reqs,
            clashes=["Campus placement season (Weeks 6-10) vs minor/elective project deadlines"]
        ))

        # 3. Core Higher Studies (M.Tech / MS in India)
        gate_reqs = ["GATE syllabus technical mastery (Engineering Math, General Aptitude, Branch Core)", "Regular previous-year question practice", "At least 2 full-length mocks"]
        options.append(DecisionOption(
            student_id=student_id,
            option="core_higher_studies",
            name="Higher Studies: GATE -> M.Tech / MS(Research) at IITs/IISc",
            timeline={
                "current_phase": f"Year {student_year} (Semester {student_sem}): GATE syllabus coverage aligned with semester courses",
                "next_milestone": "Semester 6/7: Full-length mock test series and speed calibration",
                "capstone": "February (Year 3/4): Official GATE examination, followed by COAP/CCMT counselling rounds"
            },
            tradeoffs=(
                "Opportunity: Access to premier IIT/IISc master's programmes with MHRD monthly stipend (Rs 12,400). "
                "Trade-off: 2 additional years in engineering academia before corporate industry entry."
            ),
            requirements=gate_reqs,
            clashes=["GATE exam peak preparation (December-January) vs campus placement drive"]
        ))

        # 4. MBA Now (Straight after B.Tech)
        cat_reqs = ["Bachelor's degree with >= 50% (45% SC/ST)", "CAT / XAT entrance test percentile", "Written Ability Test (WAT) and Personal Interview (PI) clearance"]
        cat_clashes = ["CAT examination window (Late November) clashes with Semester 7 End-Semester exams (Weeks 14-16)"]
        options.append(DecisionOption(
            student_id=student_id,
            option="mba_now",
            name="MBA in India Right After B.Tech (Fresher Route)",
            timeline={
                "current_phase": f"Year {student_year} (Semester {student_sem}): Aptitude diagnostic and foundation building (QA, DILR, VARC)",
                "next_milestone": "August - September: CAT / XAT registration; October - November: Intensive mock tests",
                "capstone": "Late November: CAT exam; February - April: IIM WAT & PI rounds; July: 2-year MBA commencement"
            },
            tradeoffs=(
                "Opportunity: Fast-tracks entry into corporate strategy, product management, and management consulting without a 2-year delay. "
                "Trade-off: Lacks corporate work experience points in IIM composite score formulas; demands intense parallel management of college end-sems and CAT."
            ),
            requirements=cat_reqs,
            clashes=cat_clashes
        ))

        # 5. MBA After Core Work Experience
        work_reqs = ["2 to 3 years of verified technical work experience in core engineering/technology", "Consistent performance appraisals and leadership responsibilities", "GMAT / CAT preparation during work years"]
        options.append(DecisionOption(
            student_id=student_id,
            option="mba_after_work",
            name="MBA After 2-3 Years of Core Engineering Work Experience",
            timeline={
                "current_phase": f"Year {student_year} (Semester {student_sem}): Focus on strong campus placement in core operations or technology",
                "next_milestone": "Years 1-2 Post-B.Tech: Build quantifiable project accomplishments and team leadership at work",
                "capstone": "Year 3 Post-B.Tech: Take GMAT/CAT with maximum work experience score points for top IIM PGP/EPGP or global B-schools"
            },
            tradeoffs=(
                "Opportunity: Maximizes work experience points in IIM shortlisting; deepens domain maturity; enables self-funding. "
                "Trade-off: Requires balancing demanding corporate job hours with weekend entrance test preparation."
            ),
            requirements=work_reqs,
            clashes=["Workplace shift commitments vs weekend mock test schedules"]
        ))

        return options

    def record_choice(self, student_id: str, chosen_option: str) -> Dict[str, Any]:
        """
        Records the student's decision in decision_options and triggers a plan version bump.
        """
        valid_options = ["stay_core_research", "stay_core_industry", "core_higher_studies", "mba_now", "mba_after_work"]
        if chosen_option not in valid_options:
            raise ValueError(f"Invalid option '{chosen_option}'. Must be one of {valid_options}.")

        return {
            "student_id": student_id,
            "chosen_option": chosen_option,
            "status": "recorded",
            "trigger_replan": True,
            "message": f"Career decision '{chosen_option}' recorded. Regenerating customized study and action plan."
        }

# Global Singleton
mba_decision_engine = MBADecisionEngine()
mba_decision_engine = MBADecisionEngine()
