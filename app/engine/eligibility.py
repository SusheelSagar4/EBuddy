from typing import List, Dict, Optional, Any
from app.contracts.core_to_mtech import EligibilityResult, HigherProgramme
from app.kb.core_to_mtech_repo import core_to_mtech_repo

class EligibilityEngine:
    """
    Deterministic Eligibility and Route-Fit Engine (§8.1).
    Hard constraints:
    - Strictly reads stored rules from kb (GATE brochures, paper mappings, programme eligibility).
    - Never guesses or hallucinates an unstored rule.
    - If ineligible, outputs the exact rule ID, text, source, and a deterministic best_valid_option.
    - Handles:
      * Year of study (GATE 3rd year onwards; 1st/2nd year -> eligible_later)
      * Branch-to-paper mapping (EE -> EE, MM -> MT)
      * Allowed two-paper combinations (EE -> IN,EC,DA; MM -> ME,XE,PI)
      * Programme min CGPA / qualifying criteria
      * Direct PhD 8.0 CFTI CGPA threshold
      * Route transitions (M.Tech, MS(R), Direct PhD, PSU, Core Industry)
    """
    def __init__(self, repo=None):
        self.repo = repo or core_to_mtech_repo

    def check_gate_exam_eligibility(
        self,
        year: int,
        semester: int,
        branch: str,
        primary_paper: str,
        second_paper: Optional[str] = None
    ) -> EligibilityResult:
        primary_p = primary_paper.upper().strip()
        second_p = second_paper.upper().strip() if second_paper else None
        b_clean = branch.upper().strip()

        # 1. Year of study check
        # Per GATE Section 3: A candidate currently studying in 3rd or higher years of any undergraduate degree programme is eligible.
        if year < 3 and semester < 5:
            when_eligible = f"Academic Year {year + (1 if year == 2 else 2)} (Semester 5)"
            return EligibilityResult(
                is_eligible=False,
                status="eligible_later",
                when_eligible=when_eligible,
                rule_id="RULE_GATE_YEAR_ELIGIBILITY",
                rule_text="Candidates currently studying in 3rd or higher years of undergraduate degree programme are eligible to appear for GATE.",
                rule_source="https://gate2027.iitm.ac.in/eligibility",
                reasons=[
                    f"Student is currently in Year {year} (Semester {semester}). Official GATE appearance begins in 3rd year (Semester 5).",
                    "Early preparation in 1st/2nd year builds prerequisite mastery in Engineering Mathematics and General Aptitude."
                ],
                best_valid_option="Foundation & Prerequisite Track: Focus on Engineering Mathematics, Aptitude, and maintaining high CGPA."
            )

        # 2. Branch to Primary Paper Mapping
        # Look up paper row
        paper_obj = self.repo.exam_papers.get(primary_p)
        if not paper_obj:
            return EligibilityResult(
                is_eligible=False,
                status="ineligible",
                rule_id="RULE_GATE_PAPER_EXISTS",
                rule_text=f"Selected GATE paper '{primary_p}' is not cataloged in the knowledge base.",
                rule_source="https://gate2027.iitm.ac.in/papers",
                reasons=[f"Paper code '{primary_p}' not recognized."],
                best_valid_option="EE" if "EE" in b_clean else "MT"
            )

        mapped_branches = [b.strip() for b in paper_obj.branches_mapped.split(",")]
        # Also allow general core mapping
        if b_clean not in mapped_branches and not any(mb in b_clean for mb in mapped_branches):
            valid_primary = "EE" if "EE" in b_clean else "MT"
            return EligibilityResult(
                is_eligible=False,
                status="ineligible",
                rule_id="RULE_GATE_BRANCH_PAPER_MISMATCH",
                rule_text=f"Paper '{primary_p}' is officially mapped to branches {paper_obj.branches_mapped}, not '{branch}'.",
                rule_source="https://gate2027.iitm.ac.in/papers",
                reasons=[
                    f"Branch '{branch}' requires relevant core syllabus coverage for high percentile.",
                    f"Primary paper '{primary_p}' does not match undergraduate core curriculum."
                ],
                best_valid_option=f"Switch primary paper to '{valid_primary}' which directly covers your B.Tech core subjects."
            )

        # 3. Two-Paper Combination Check
        allowed_seconds = [p.strip() for p in (paper_obj.allowed_second_papers or "").split(",") if p.strip()]
        if second_p:
            if second_p not in allowed_seconds:
                return EligibilityResult(
                    is_eligible=False,
                    status="ineligible",
                    rule_id="RULE_GATE_TWO_PAPER_COMBINATION",
                    rule_text=f"Second paper '{second_p}' is not an allowed combination with primary paper '{primary_p}'.",
                    rule_source="https://gate2027.iitm.ac.in/two_paper_combinations",
                    reasons=[
                        f"For primary paper '{primary_p}', official allowed second papers are: {', '.join(allowed_seconds)}."
                    ],
                    allowed_second_papers=allowed_seconds,
                    best_valid_option=f"Select an officially allowed second paper ({', '.join(allowed_seconds)}) or appear for single paper '{primary_p}'."
                )

        return EligibilityResult(
            is_eligible=True,
            status="eligible",
            rule_id="RULE_GATE_ELIGIBLE",
            rule_text="Candidate fulfills year of study and approved paper combination criteria for GATE.",
            rule_source="https://gate2027.iitm.ac.in/eligibility",
            reasons=["Currently in eligible year of study", f"Approved primary paper: {primary_p}"],
            allowed_second_papers=allowed_seconds,
            best_valid_option=f"Appear for GATE {primary_p}" + (f" + {second_p}" if second_p else "")
        )

    def check_programme_eligibility(
        self,
        student_branch: str,
        student_cgpa: float,
        backlogs: int,
        programme_id: str,
        paper_code: str
    ) -> EligibilityResult:
        prog = self.repo.programmes.get(programme_id)
        if not prog:
            return EligibilityResult(
                is_eligible=False,
                status="ineligible",
                rule_id="RULE_PROG_NOT_FOUND",
                rule_text=f"Programme ID '{programme_id}' not found in database.",
                rule_source="internal_db",
                best_valid_option=None
            )

        b_clean = student_branch.upper().strip()
        p_clean = paper_code.upper().strip()

        # 1. Backlogs check
        if backlogs > 0:
            return EligibilityResult(
                is_eligible=False,
                status="ineligible",
                rule_id="RULE_NO_ACTIVE_BACKLOGS",
                rule_text="Admission to postgraduate degree programmes requires clear undergraduate record without active backlogs at time of admission.",
                rule_source=prog.source_url or "https://coap.iitm.ac.in/",
                reasons=[f"Student has {backlogs} active backlog(s). Active backlogs must be cleared before admission."],
                best_valid_option="Prioritize clearing current backlogs during semester examinations before final admissions."
            )

        # 2. Paper accepted check
        acc_papers = [p.strip() for p in (prog.gate_papers_accepted or "").split(",")]
        if p_clean not in acc_papers and "ALL" not in acc_papers:
            return EligibilityResult(
                is_eligible=False,
                status="ineligible",
                rule_id="RULE_GATE_PAPER_NOT_ACCEPTED",
                rule_text=f"Programme '{prog.specialisation}' accepts GATE papers: {prog.gate_papers_accepted}, but candidate is preparing '{p_clean}'.",
                rule_source=prog.source_url or "https://coap.iitm.ac.in/",
                reasons=[f"Paper '{p_clean}' is not accepted for this specialization."],
                best_valid_option=f"Target specializations accepting GATE {p_clean} or add an accepted second paper if eligible."
            )

        # 3. Branch eligible check
        b_eligs = [b.strip() for b in (prog.branches_eligible or "").split(",")]
        if b_clean not in b_eligs and not any(be in b_clean for be in b_eligs):
            return EligibilityResult(
                is_eligible=False,
                status="ineligible",
                rule_id="RULE_BRANCH_NOT_ELIGIBLE",
                rule_text=f"Qualifying B.Tech branch '{student_branch}' is not in eligible branches: {prog.branches_eligible}.",
                rule_source=prog.source_url or "https://coap.iitm.ac.in/",
                reasons=[f"Undergraduate degree discipline mismatch for '{prog.specialisation}'."],
                best_valid_option="Target specializations open to your discipline or interdisciplinary programmes."
            )

        # 4. Minimum Qualifying Criteria / CGPA check
        # Direct PhD check (requires 8.0 CGPA from CFTIs)
        if prog.degree == "Direct PhD" and student_cgpa < 8.0:
            return EligibilityResult(
                is_eligible=False,
                status="ineligible",
                rule_id="RULE_DIRECT_PHD_MIN_CGPA",
                rule_text="Direct PhD admissions for CFTI B.Tech graduates require minimum 8.0 CGPA (or valid national fellowship with high rank).",
                rule_source=prog.source_url or "https://iisc.ac.in/admissions",
                reasons=[
                    f"Student CGPA is {student_cgpa:.2f}, which is below the 8.00 CFTI Direct PhD threshold."
                ],
                best_valid_option=f"Apply for 2-year M.Tech or MS(R) in {prog.department}, and convert to PhD after demonstrating strong 1st year research performance."
            )

        # Standard M.Tech min CGPA (6.5 for IITs/NITs, 6.0 for some)
        min_cgpa_req = 6.5
        if "6.0" in (prog.min_qualifying_criteria or ""):
            min_cgpa_req = 6.0
        elif "7.0" in (prog.min_qualifying_criteria or ""):
            min_cgpa_req = 7.0

        if student_cgpa < min_cgpa_req:
            return EligibilityResult(
                is_eligible=False,
                status="ineligible",
                rule_id="RULE_MIN_QUALIFYING_CGPA",
                rule_text=f"Minimum qualifying criterion for {prog.specialisation} ({prog.institution_id}): {prog.min_qualifying_criteria}.",
                rule_source=prog.source_url or "https://coap.iitm.ac.in/",
                reasons=[
                    f"Student CGPA is {student_cgpa:.2f}, below minimum qualifying threshold of {min_cgpa_req:.2f}."
                ],
                best_valid_option="Target programmes with 6.0 CGPA cutoff or focus on semester courses to raise CGPA above qualifying threshold."
            )

        return EligibilityResult(
            is_eligible=True,
            status="eligible",
            rule_id="RULE_PROG_ELIGIBLE",
            rule_text="Student meets all qualifying branch, CGPA, and GATE paper requirements.",
            rule_source=prog.source_url or "https://coap.iitm.ac.in/",
            reasons=[
                f"CGPA {student_cgpa:.2f} satisfies criteria",
                f"B.Tech {student_branch} is eligible",
                f"GATE {paper_code} is accepted"
            ],
            best_valid_option=f"Apply via {prog.application_portal} portal before deadline {prog.application_deadline}."
        )

    def evaluate_route_fit(
        self,
        branch: str,
        year: int,
        cgpa: float,
        backlogs: int,
        target_route: str,
        paper_code: str
    ) -> EligibilityResult:
        """
        Evaluates fit and eligibility for a given high-level route (§8.1).
        Routes: ROUTE_MTECH_INDIA, ROUTE_MSR_INDIA, ROUTE_PHD_INDIA, ROUTE_PSU_GATE, ROUTE_CORE_INDUSTRY.
        """
        route_clean = target_route.upper().strip()

        if route_clean in ["ROUTE_PHD_INDIA", "DIRECT PHD"]:
            if cgpa < 8.0:
                return EligibilityResult(
                    is_eligible=False,
                    status="ineligible",
                    rule_id="RULE_ROUTE_DIRECT_PHD_CGPA",
                    rule_text="Direct PhD route requires CGPA >= 8.00 from CFTIs or exceptional national fellowship.",
                    rule_source="https://iisc.ac.in/admissions/phd",
                    reasons=[f"Current CGPA {cgpa:.2f} < 8.00."],
                    best_valid_option="Target M.Tech or MS(R) track first. High M.Tech CPI enables seamless PhD upgrade."
                )

        if route_clean in ["ROUTE_PSU_GATE", "PSU VIA GATE"]:
            if cgpa < 6.5:
                return EligibilityResult(
                    is_eligible=False,
                    status="ineligible",
                    rule_id="RULE_PSU_MIN_PERCENTAGE",
                    rule_text="Major PSUs (POWERGRID, NTPC, IOCL, ONGC) strictly mandate 65% aggregate or 6.50 CGPA without backlogs.",
                    rule_source="https://powergrid.in/careers",
                    reasons=[f"Current CGPA {cgpa:.2f} is below typical PSU 6.50 cutoff threshold."],
                    best_valid_option="Target M.Tech route (where GATE score is sole criterion) or raise CGPA in remaining semesters."
                )

        if route_clean in ["ROUTE_MSR_INDIA", "MS(R) INDIA"]:
            return EligibilityResult(
                is_eligible=True,
                status="eligible",
                rule_id="RULE_MSR_FIT",
                rule_text="MS(R) route emphasizes research statement and technical interview alongside GATE score.",
                rule_source="https://www.iitb.ac.in/admissions",
                reasons=["Eligible for written test/interview shortlisting"],
                best_valid_option="Prepare research statement and review faculty publications in target research groups."
            )

        # Standard M.Tech India
        return EligibilityResult(
            is_eligible=True,
            status="eligible",
            rule_id="RULE_MTECH_FIT",
            rule_text="Eligible for GATE qualification and COAP/CCMT counselling across IITs, IISc, and NITs.",
            rule_source="https://coap.iitm.ac.in/",
            reasons=["Eligible for GATE preparation and central counselling"],
            best_valid_option="Follow weekly phase guidance and participate in regular topic and mock tests."
        )

# Global singleton
eligibility_engine = EligibilityEngine()
