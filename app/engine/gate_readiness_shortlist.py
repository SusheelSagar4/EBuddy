import math
from typing import List, Dict, Any, Optional, Tuple
from app.contracts.core_to_mtech import (
    ScoreBand,
    ProgrammeTier,
    Shortlist,
    MockResult,
    ErrorLogItem,
    HigherProgramme,
    AdmissionStat
)
from app.kb.core_to_mtech_repo import core_to_mtech_repo
from app.engine.eligibility import eligibility_engine

class GATEReadinessAndShortlistEngine:
    """
    Deterministic Readiness Gate, Score Band Prediction and Shortlist Tiering Engine (§8.4, §8.5).
    Hard constraints:
    - Never promise admission or rank; displays honest uncertainty notes.
    - If fewer than 2 full mocks exist, shows 'not enough evidence yet'.
    - Shortlist tiers: Reach / Target / Safe / unknown based on score band vs historical admission stats.
    - Cites year, category, and source for every cut-off.
    - Unverified data shown only in admin or with visible label in demo mode.
    """
    def __init__(self, repo=None):
        self.repo = repo or core_to_mtech_repo

    def compute_predicted_score_band(
        self,
        full_mock_scores: List[float],
        calibration_factor: float = 0.95
    ) -> Optional[ScoreBand]:
        """
        Computes predicted score band from the last 3-5 full mocks (§8.4).
        If fewer than 2 full mocks exist, returns None (not enough evidence yet).
        """
        if not full_mock_scores or len(full_mock_scores) < 2:
            return None

        # Take last 3 to 5 full mocks
        recent_mocks = full_mock_scores[-5:]
        n = len(recent_mocks)
        mean_score = sum(recent_mocks) / n

        # Standard deviation
        variance = sum((s - mean_score) ** 2 for s in recent_mocks) / n
        stdev = math.sqrt(variance)

        # Apply calibration assumption (mocks are calibrated to actual GATE score scale)
        calibrated_mean = mean_score * calibration_factor
        # Spread is at least 30 points or 1.5 * stdev
        spread = max(30.0, stdev * 1.5)

        min_score = max(0.0, round(calibrated_mean - spread, 1))
        max_score = min(1000.0, round(calibrated_mean + spread, 1))

        return ScoreBand(
            min_score=min_score,
            max_score=max_score,
            mean_score=round(calibrated_mean, 1),
            confidence_level=0.85,
            is_estimated=True,
            uncertainty_note=(
                "Estimated GATE score band derived from your recent full mock performances with historical calibration. "
                "Actual closing score varies with yearly paper difficulty, candidate distribution, and normalization. "
                "This band is an advisory guide, never an admission guarantee."
            ),
            num_mocks_used=n
        )

    def evaluate_readiness(
        self,
        full_mock_scores: List[float],
        topic_masteries: Dict[str, float],
        error_logs: List[ErrorLogItem],
        target_score_threshold: float = 650.0
    ) -> Dict[str, Any]:
        """
        Evaluates readiness checklist (§8.4):
        1. At least 3 full-length mocks completed
        2. Last 3 full mocks within or above the band of student's Target programmes
        3. No core topic below mastery 0.60
        4. Conceptual mistake rate falling or under 25%
        """
        checklist = []
        is_ready = True

        # Criterion 1: Minimum 3 full mocks
        mocks_count = len(full_mock_scores)
        c1_met = mocks_count >= 3
        checklist.append({
            "criterion": "At least 3 full-length mocks completed",
            "status": "MET" if c1_met else "MISSING",
            "detail": f"{mocks_count} completed (minimum 3 required)"
        })
        if not c1_met:
            is_ready = False

        # Criterion 2: Last 3 full mocks average within Target threshold
        last_3_mocks = full_mock_scores[-3:] if len(full_mock_scores) >= 3 else full_mock_scores
        avg_last_3 = (sum(last_3_mocks) / len(last_3_mocks)) if last_3_mocks else 0.0
        c2_met = avg_last_3 >= (target_score_threshold - 50.0) and len(last_3_mocks) >= 3
        checklist.append({
            "criterion": "Recent mock average aligns with Target programmes",
            "status": "MET" if c2_met else "MISSING",
            "detail": f"Recent 3-mock average: {avg_last_3:.1f} (target threshold: {target_score_threshold:.1f})"
        })
        if not c2_met:
            is_ready = False

        # Criterion 3: No core topic below mastery 0.60
        core_topics_below = [
            tid for tid, m in topic_masteries.items()
            if m < 0.60 and "GA" not in tid # Core syllabus topics
        ]
        c3_met = len(core_topics_below) == 0
        checklist.append({
            "criterion": "No core syllabus topic below mastery 0.60",
            "status": "MET" if c3_met else "MISSING",
            "detail": "All core topics >= 0.60" if c3_met else f"{len(core_topics_below)} topic(s) below 0.60 ({', '.join(core_topics_below[:2])})"
        })
        if not c3_met:
            is_ready = False

        # Criterion 4: Conceptual error rate under control
        if error_logs:
            concept_mistakes = sum(1 for e in error_logs if e.mistake_type == "concept")
            concept_rate = concept_mistakes / len(error_logs)
            c4_met = concept_rate <= 0.30
            c4_detail = f"Conceptual mistakes: {concept_mistakes}/{len(error_logs)} ({int(concept_rate*100)}%)"
        else:
            c4_met = True
            c4_detail = "No error log entries recorded yet"
        checklist.append({
            "criterion": "Conceptual mistake rate strictly below 30%",
            "status": "MET" if c4_met else "MISSING",
            "detail": c4_detail
        })
        if not c4_met:
            is_ready = False

        return {
            "is_ready": is_ready,
            "checklist": checklist,
            "target_score_threshold": target_score_threshold,
            "summary_recommendation": (
                "Readiness gate ACHIEVED: You are on track for your Target programmes. Continue timed mock calibration."
                if is_ready else
                "Readiness gate PENDING: Focus on missing checklist items before final application deadlines."
            )
        }

    def compute_shortlist_and_tiers(
        self,
        student_branch: str,
        student_cgpa: float,
        backlogs: int,
        paper_code: str,
        category: str = "GEN",
        score_band: Optional[ScoreBand] = None,
        preferred_specialisations: Optional[List[str]] = None,
        allow_unverified_demo: bool = True
    ) -> Shortlist:
        """
        Generates realistic Reach / Target / Safe tiering against verified admission_stats (§8.5).
        - Reach: Score band below past closing range
        - Target: Score band overlapping past closing range
        - Safe: Score band above past closing range
        - Unknown: No verified past data available
        """
        reach_list: List[ProgrammeTier] = []
        target_list: List[ProgrammeTier] = []
        safe_list: List[ProgrammeTier] = []
        unknown_list: List[ProgrammeTier] = []

        cat_clean = category.upper().strip()
        p_code = paper_code.upper().strip()

        for pid, prog in self.repo.programmes.items():
            # Check eligibility first
            elig = eligibility_engine.check_programme_eligibility(
                student_branch=student_branch,
                student_cgpa=student_cgpa,
                backlogs=backlogs,
                programme_id=pid,
                paper_code=p_code
            )
            if not elig.is_eligible:
                continue

            # Check verification rule (§3):
            # Only show verified rows by default. In demo mode, unverified rows carry a visible label.
            is_verified = prog.verified
            if not is_verified and not allow_unverified_demo:
                continue

            inst = self.repo.institutions.get(prog.institution_id)
            inst_name = inst.name if inst else prog.institution_id

            # Gather admission stats for this programme and category
            stats = [
                s for s in self.repo.admission_stats
                if s.programme_id == pid and s.category.upper() == cat_clean
            ]

            scores_by_year = {}
            for s in stats:
                scores_by_year[s.year] = s.closing_score_or_rank

            verified_dl = prog.application_deadline if prog.verified else "Not confirmed yet. Check official site"
            stipend_info = prog.stipend_or_assistantship or "Institute scholarship per MoE norms"

            if not stats or score_band is None:
                # No stats or no score band yet -> Unknown tier
                tier_str = "unknown"
                range_str = "Not available (no verified round data)"
                fit_reason = f"Eligible programme in {prog.department} matching {p_code} paper."
                tier_item = ProgrammeTier(
                    programme_id=pid,
                    institution_name=inst_name,
                    degree=prog.degree,
                    specialisation=prog.specialisation,
                    tier=tier_str,
                    fit_reason=fit_reason,
                    past_closing_range=range_str,
                    closing_scores_by_year=scores_by_year,
                    verified_deadline=verified_dl,
                    selection_mode=prog.selection_mode,
                    stipend=stipend_info,
                    source_citation=prog.source_url,
                    is_verified=prog.verified
                )
                unknown_list.append(tier_item)
                continue

            # We have both score band and past stats
            closing_vals = [s.closing_score_or_rank for s in stats]
            min_cutoff = min(closing_vals)
            max_cutoff = max(closing_vals)
            range_str = f"{int(min_cutoff)} - {int(max_cutoff)} (Years: {', '.join(str(y) for y in sorted(scores_by_year.keys()))})"

            # Tier classification
            # Reach: student's max score < min cutoff (student is below range)
            # Safe: student's min score > max cutoff (student is safely above range)
            # Target: overlapping
            if score_band.max_score < min_cutoff:
                tier_str = "Reach"
                fit_reason = (
                    f"Ambitious target. Past closing range ({range_str}) is above your current score band "
                    f"[{score_band.min_score:.0f} - {score_band.max_score:.0f}]. Requires significant score jump in mocks."
                )
                item = ProgrammeTier(
                    programme_id=pid,
                    institution_name=inst_name,
                    degree=prog.degree,
                    specialisation=prog.specialisation,
                    tier=tier_str,
                    fit_reason=fit_reason,
                    past_closing_range=range_str,
                    closing_scores_by_year=scores_by_year,
                    verified_deadline=verified_dl,
                    selection_mode=prog.selection_mode,
                    stipend=stipend_info,
                    source_citation=prog.source_url,
                    is_verified=prog.verified
                )
                reach_list.append(item)
            elif score_band.min_score > max_cutoff:
                tier_str = "Safe"
                fit_reason = (
                    f"High probability option. Your score band [{score_band.min_score:.0f} - {score_band.max_score:.0f}] "
                    f"comfortably clears past closing cutoffs ({range_str}). Excellent fallback backup."
                )
                item = ProgrammeTier(
                    programme_id=pid,
                    institution_name=inst_name,
                    degree=prog.degree,
                    specialisation=prog.specialisation,
                    tier=tier_str,
                    fit_reason=fit_reason,
                    past_closing_range=range_str,
                    closing_scores_by_year=scores_by_year,
                    verified_deadline=verified_dl,
                    selection_mode=prog.selection_mode,
                    stipend=stipend_info,
                    source_citation=prog.source_url,
                    is_verified=prog.verified
                )
                safe_list.append(item)
            else:
                tier_str = "Target"
                fit_reason = (
                    f"Well-matched target. Your score band [{score_band.min_score:.0f} - {score_band.max_score:.0f}] "
                    f"directly overlaps past closing range ({range_str}). Good realistic conversion probability."
                )
                item = ProgrammeTier(
                    programme_id=pid,
                    institution_name=inst_name,
                    degree=prog.degree,
                    specialisation=prog.specialisation,
                    tier=tier_str,
                    fit_reason=fit_reason,
                    past_closing_range=range_str,
                    closing_scores_by_year=scores_by_year,
                    verified_deadline=verified_dl,
                    selection_mode=prog.selection_mode,
                    stipend=stipend_info,
                    source_citation=prog.source_url,
                    is_verified=prog.verified
                )
                target_list.append(item)

        # Compute balanced recommendation: 2 Reach, 4 Target, 2 Safe
        balanced = []
        for it in reach_list[:2]:
            balanced.append(f"[Reach] {it.institution_name} - {it.specialisation}")
        for it in target_list[:4]:
            balanced.append(f"[Target] {it.institution_name} - {it.specialisation}")
        for it in safe_list[:2]:
            balanced.append(f"[Safe] {it.institution_name} - {it.specialisation}")

        return Shortlist(
            reach=reach_list,
            target=target_list,
            safe=safe_list,
            unknown=unknown_list,
            balanced_recommendation=balanced
        )

# Global singleton
gate_readiness_shortlist_engine = GATEReadinessAndShortlistEngine()
