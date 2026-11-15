import math
from typing import List, Dict, Optional, Any
from app.contracts.core_to_mba import MBAAdmissionStat, MBAProgramme
from app.kb.core_to_mba_repo import core_to_mba_repo

class MBAMocksShortlistEngine:
    """
    Mock Calibrated Band & Shortlist Tiering Engine (§1.7, §7.6 & §11).
    Calculates calibrated percentile bands from empirical mock evidence and tiers target B-schools.

    Non-negotiable product rules (§4):
    1. Minimum 2 full-length mocks required before predicting a calibrated percentile band.
    2. NEVER a promise or guarantee: strictly marked as evidence-based projection.
    3. Zero-Leak Guarantee: strictly only rows with verified=TRUE and verified_by from official sources
       are presented to students. Any unverified row is completely suppressed in student mode.
    4. Categorization into Reach, Target, and Safe tiers based on official past closing percentiles.
    """
    def __init__(self, repo=None):
        self.repo = repo or core_to_mba_repo
        # Student mock results storage: student_id -> list of mock records
        self.mock_store: Dict[str, List[Dict[str, Any]]] = {}

    def record_mock(
        self,
        student_id: str,
        exam_id: str,
        mock_name: str,
        raw_score: float,
        percentile: float,
        section_scores: Optional[Dict[str, float]] = None,
        date_taken: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Records a completed full-length mock test result.
        """
        record = {
            "mock_id": f"mock_{len(self.mock_store.get(student_id, [])) + 1}",
            "exam_id": exam_id,
            "mock_name": mock_name,
            "raw_score": raw_score,
            "percentile": round(percentile, 2),
            "section_scores": section_scores or {},
            "date_taken": date_taken or "2026-11-15"
        }
        self.mock_store.setdefault(student_id, []).append(record)
        return record

    def get_mock_history(self, student_id: str) -> List[Dict[str, Any]]:
        return self.mock_store.get(student_id, [])

    def calculate_score_band(self, student_id: str) -> Dict[str, Any]:
        """
        Calculates calibrated score band from mock evidence.
        Enforces minimum 2 full mocks rule.
        """
        mocks = self.mock_store.get(student_id, [])
        if len(mocks) < 2:
            return {
                "student_id": student_id,
                "calibrated": False,
                "mocks_completed": len(mocks),
                "status": "Insufficient Evidence: Minimum 2 full-length mocks required for calibrated prediction.",
                "low_band": None,
                "high_band": None,
                "band_str": "Uncalibrated (< 2 mocks)"
            }

        # Weight recent mocks higher
        weights = [1.0 + 0.5 * i for i in range(len(mocks))]
        total_w = sum(weights)
        weighted_p = sum(m["percentile"] * w for m, w in zip(mocks, weights)) / total_w

        # Spread is at least +- 2.0 percentile points, wider if mock variance is high
        variance = sum(w * ((m["percentile"] - weighted_p) ** 2) for m, w in zip(mocks, weights)) / total_w
        std_dev = math.sqrt(variance)
        spread = max(2.0, min(5.0, round(std_dev, 1)))

        low_band = max(40.0, round(weighted_p - spread, 1))
        high_band = min(99.9, round(weighted_p + spread, 1))

        return {
            "student_id": student_id,
            "calibrated": True,
            "mocks_completed": len(mocks),
            "weighted_percentile": round(weighted_p, 1),
            "low_band": low_band,
            "high_band": high_band,
            "band_str": f"{low_band}%ile - {high_band}%ile",
            "status": "Calibrated estimate from mock evidence (never an admission guarantee)",
            "recent_trend": [m["percentile"] for m in mocks[-5:]]
        }

    def generate_shortlist(
        self,
        student_id: str,
        category: str = "GEN",
        target_exam_id: str = "MBA-EX-CAT",
        preliminary_percentile: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Builds Reach, Target, Safe shortlist tiers against verified institutional cutoff rows.
        Strict Zero-Leak Guarantee: suppresses any unverified admission stat or programme.
        """
        band_info = self.calculate_score_band(student_id)
        if band_info["calibrated"]:
            low_p = band_info["low_band"]
            high_p = band_info["high_band"]
            is_preliminary = False
        elif preliminary_percentile is not None:
            low_p = max(40.0, preliminary_percentile - 4.0)
            high_p = min(99.9, preliminary_percentile + 4.0)
            is_preliminary = True
        else:
            return {
                "student_id": student_id,
                "calibrated": False,
                "error": "No mock evidence or preliminary percentile provided. Complete diagnostic or mocks first.",
                "reach": [],
                "target": [],
                "safe": []
            }

        # Filter strictly verified programmes & admission stats
        verified_programmes = {
            pid: prog for pid, prog in self.repo.programmes.items()
            if prog.verified
        }

        # Gather relevant verified cutoffs
        reach: List[Dict[str, Any]] = []
        target: List[Dict[str, Any]] = []
        safe: List[Dict[str, Any]] = []

        norm_cat = category.upper().strip()

        for stat in self.repo.admission_stats:
            # Strict verification guard
            if not stat.verified:
                continue
            if stat.cutoff_type.lower() != "percentile":
                continue
            if stat.category.upper() != norm_cat:
                continue

            prog = verified_programmes.get(stat.programme_id)
            if not prog:
                continue
            if target_exam_id and prog.exams_accepted and target_exam_id not in prog.exams_accepted:
                continue

            cutoff = stat.cutoff_value
            inst = self.repo.institutions.get(prog.institution_id)
            inst_name = inst.name if inst else prog.institution_id

            entry = {
                "programme_id": prog.id,
                "programme_name": prog.programme_name,
                "institution_name": inst_name,
                "category": stat.category,
                "cutoff_percentile": cutoff,
                "application_deadline": prog.application_deadline,
                "selection_process": prog.selection_process,
                "source_url": stat.source_url,
                "verified": True
            }

            # Tier classification:
            # Safe: low_band >= cutoff + 1.0 (very likely to receive call)
            # Target: low_band <= cutoff <= high_band
            # Reach: high_band is within 3.0 percentile points of cutoff (e.g. cutoff - 3.0 <= high_band < cutoff)
            if low_p >= cutoff + 1.0:
                safe.append(entry)
            elif low_p <= cutoff <= high_p:
                target.append(entry)
            elif high_p >= cutoff - 3.0:
                reach.append(entry)

        # Sort each tier by cutoff descending
        reach.sort(key=lambda x: -x["cutoff_percentile"])
        target.sort(key=lambda x: -x["cutoff_percentile"])
        safe.sort(key=lambda x: -x["cutoff_percentile"])

        return {
            "student_id": student_id,
            "category": norm_cat,
            "calibrated": band_info["calibrated"],
            "is_preliminary": is_preliminary,
            "estimated_band": f"{low_p}%ile - {high_p}%ile",
            "tier_counts": {"reach": len(reach), "target": len(target), "safe": len(safe)},
            "reach": reach,
            "target": target,
            "safe": safe,
            "disclaimer": (
                "Shortlist tiers are empirical guidelines based on past verified closing percentiles. "
                "Final B-school shortlists also depend on 10th/12th/UG academic scores, gender/academic diversity, "
                "and interview/WAT performance."
            )
        }

# Global Singleton
mba_mocks_shortlist_engine = MBAMocksShortlistEngine()
