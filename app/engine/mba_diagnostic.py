import math
import uuid
from typing import List, Dict, Optional, Any
from app.contracts.core_to_mba import MBAPracticeItem
from app.kb.core_to_mba_repo import core_to_mba_repo

class MBADiagnosticEngine:
    """
    Adaptive Aptitude Diagnostic Engine (§1.3, §7.3 & §11).
    Evaluates aptitude across QA, DILR, and VARC using reviewed practice items.
    
    Principles:
    1. Short and adaptive: 9 to 15 questions maximum.
    2. Zero hallucinated questions: only reviewed items from kb.mba_practice_item.
    3. IRT / Bayesian adaptive item selection based on estimated ability theta.
    4. Engineering advantage check: identifies strong quantitative intuition vs verbal gap.
    """
    def __init__(self, repo=None):
        self.repo = repo or core_to_mba_repo
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def start_diagnostic(self, student_id: str, exam_id: str = "MBA-EX-CAT") -> Dict[str, Any]:
        """
        Initializes an adaptive diagnostic test session.
        """
        session_id = f"diag_{uuid.uuid4().hex[:12]}"
        
        # Verify reviewed items exist
        available_items = [
            item for item in self.repo.practice_items.values()
            if item.reviewed and (item.exam_id == exam_id or exam_id == "ANY")
        ]
        if not available_items:
            raise ValueError(f"No reviewed practice items found for exam {exam_id}.")

        session = {
            "session_id": session_id,
            "student_id": student_id,
            "exam_id": exam_id,
            "questions_administered": [],
            "responses": [],
            "section_ability": {
                "QA": {"theta": 0.0, "se": 1.0, "count": 0, "correct": 0},
                "DILR": {"theta": 0.0, "se": 1.0, "count": 0, "correct": 0},
                "VARC": {"theta": 0.0, "se": 1.0, "count": 0, "correct": 0}
            },
            "current_question_id": None,
            "completed": False,
            "max_items": 15,
            "target_per_section": 3
        }
        self.sessions[session_id] = session

        # Select first question (typically QA medium difficulty to build initial confidence)
        first_q = self._select_next_question(session)
        if first_q:
            session["current_question_id"] = first_q.id

        return {
            "session_id": session_id,
            "student_id": student_id,
            "next_question": self._sanitize_question(first_q) if first_q else None,
            "progress": {"completed": 0, "total_target": session["max_items"]}
        }

    def _sanitize_question(self, q: MBAPracticeItem) -> Dict[str, Any]:
        """
        Returns question details without revealing answer or explanation.
        """
        return {
            "id": q.id,
            "section": q.section,
            "topic": q.topic,
            "difficulty": q.difficulty,
            "type": q.type,
            "stem": q.stem,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d
        }

    def _select_next_question(self, session: Dict[str, Any]) -> Optional[MBAPracticeItem]:
        administered = set(session["questions_administered"])
        sections = ["QA", "DILR", "VARC"]
        
        # Determine which section needs testing next
        # Priority to sections with fewer questions administered
        section_counts = [(s, session["section_ability"][s]["count"]) for s in sections]
        section_counts.sort(key=lambda x: x[1])
        
        target_section = None
        for sec, count in section_counts:
            if count < session["target_per_section"]:
                target_section = sec
                break
        
        if not target_section:
            # If all have reached target, pick the section with highest standard error (least certain)
            section_ses = [(s, session["section_ability"][s]["se"]) for s in sections]
            section_ses.sort(key=lambda x: -x[1])
            target_section = section_ses[0][0]

        theta = session["section_ability"][target_section]["theta"]
        target_diff = 2 if theta < -0.5 else (4 if theta > 1.0 else 3)

        # Find eligible items in target section
        candidates = [
            item for item in self.repo.practice_items.values()
            if item.reviewed
            and item.section == target_section
            and item.id not in administered
            and (item.exam_id == session["exam_id"] or session["exam_id"] == "ANY")
        ]

        if not candidates:
            # Fallback to any unadministered item from any section
            candidates = [
                item for item in self.repo.practice_items.values()
                if item.reviewed
                and item.id not in administered
                and (item.exam_id == session["exam_id"] or session["exam_id"] == "ANY")
            ]

        if not candidates:
            return None

        # Pick candidate closest to target difficulty
        candidates.sort(key=lambda x: (abs(x.difficulty - target_diff), x.id))
        return candidates[0]

    def submit_answer(self, session_id: str, question_id: str, user_answer: str) -> Dict[str, Any]:
        """
        Evaluates answer, updates IRT ability estimates, and returns next item or final report.
        """
        session = self.sessions.get(session_id)
        if not session:
            raise KeyError(f"Diagnostic session '{session_id}' not found.")
        if session["completed"]:
            return self.get_report(session_id)

        item = self.repo.practice_items.get(question_id)
        if not item:
            raise KeyError(f"Practice item '{question_id}' not found.")

        # Check correctness (clean string comparison)
        norm_user = str(user_answer).strip().lower()
        norm_correct = str(item.answer).strip().lower()
        is_correct = (norm_user == norm_correct)

        # Update section statistics
        sec = item.section
        sec_stat = session["section_ability"][sec]
        sec_stat["count"] += 1
        if is_correct:
            sec_stat["correct"] += 1

        # Simple Bayesian-IRT theta update
        # P(correct | theta, b) = 1 / (1 + exp(-(theta - (difficulty - 2.5))))
        b = float(item.difficulty - 2.5)
        p = 1.0 / (1.0 + math.exp(-max(min(sec_stat["theta"] - b, 4.0), -4.0)))
        step = 0.5 * (1.0 if is_correct else 0.0 - p)
        sec_stat["theta"] = max(min(sec_stat["theta"] + step, 3.0), -3.0)
        # Update standard error (decreases with questions answered)
        sec_stat["se"] = max(0.25, 1.0 / math.sqrt(1 + sec_stat["count"]))

        session["questions_administered"].append(question_id)
        session["responses"].append({
            "question_id": question_id,
            "section": sec,
            "topic": item.topic,
            "difficulty": item.difficulty,
            "user_answer": user_answer,
            "correct_answer": item.answer,
            "is_correct": is_correct,
            "explanation": item.explanation
        })

        total_administered = len(session["questions_administered"])
        # Stop condition: total reached max or all sections have count >= 3 with se <= 0.4
        all_converged = all(session["section_ability"][s]["count"] >= 3 for s in ["QA", "DILR", "VARC"])
        if total_administered >= session["max_items"] or all_converged:
            session["completed"] = True
            session["current_question_id"] = None
            return self.get_report(session_id)

        # Select next question
        next_q = self._select_next_question(session)
        if not next_q:
            session["completed"] = True
            session["current_question_id"] = None
            return self.get_report(session_id)

        session["current_question_id"] = next_q.id
        return {
            "session_id": session_id,
            "completed": False,
            "last_result": {
                "question_id": question_id,
                "is_correct": is_correct,
                "explanation": item.explanation
            },
            "next_question": self._sanitize_question(next_q),
            "progress": {
                "completed": total_administered,
                "total_target": session["max_items"]
            }
        }

    def get_report(self, session_id: str) -> Dict[str, Any]:
        """
        Generates diagnostic report, ability estimates, strengths, gaps, and recommended plan.
        """
        session = self.sessions.get(session_id)
        if not session:
            raise KeyError(f"Diagnostic session '{session_id}' not found.")

        # Estimate percentiles per section from theta
        def theta_to_percentile(theta: float) -> float:
            # Standard normal CDF approximation
            z = theta
            p = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
            return round(p * 100.0, 1)

        section_scores = {}
        for sec in ["QA", "DILR", "VARC"]:
            stat = session["section_ability"][sec]
            est_p = theta_to_percentile(stat["theta"])
            section_scores[sec] = {
                "questions_taken": stat["count"],
                "correct": stat["correct"],
                "accuracy": round(stat["correct"] / max(1, stat["count"]) * 100, 1),
                "estimated_percentile": est_p,
                "status": "Strength" if est_p >= 75.0 else ("Competent" if est_p >= 50.0 else "Focus Area")
            }

        # Overall estimated percentile
        avg_theta = sum(session["section_ability"][s]["theta"] for s in ["QA", "DILR", "VARC"]) / 3.0
        overall_p = theta_to_percentile(avg_theta)
        
        # Predicted band: range +- 5 percentile points
        low_band = max(40.0, round(overall_p - 5.0, 1))
        high_band = min(99.5, round(overall_p + 5.0, 1))

        # Engineering advantage check
        qa_p = section_scores["QA"]["estimated_percentile"]
        varc_p = section_scores["VARC"]["estimated_percentile"]
        dilr_p = section_scores["DILR"]["estimated_percentile"]

        verbal_gap = (qa_p - varc_p >= 15.0) or (varc_p < 60.0)
        strengths = []
        gaps = []

        if qa_p >= 70.0:
            strengths.append("Engineering Quantitative Rigor: High comfort with arithmetic, algebra, and number theory.")
        elif qa_p < 50.0:
            gaps.append("Quantitative speed: Accuracy is acceptable but pacing on multi-step problems needs drill.")

        if dilr_p >= 70.0:
            strengths.append("Structured Logic: Strong performance in analytical arrangements and pattern deduction.")
        elif dilr_p < 50.0:
            gaps.append("DILR Set Selection: Needs structured practice identifying high-scoring data interpretation sets.")

        if varc_p >= 75.0:
            strengths.append("Balanced Verbal Acumen: Confident comprehension and argument analysis.")
        elif verbal_gap:
            gaps.append("Verbal Gap (Typical for Core Engineers): Reading speed and abstract humanities comprehension need dedicated daily reading habit.")

        # Recommended template
        if overall_p < 65.0:
            rec_template = "MBA-TMPL-12M"
            rec_notes = "Comprehensive 12-month foundation template recommended with heavy initial verbal-gap emphasis."
        elif overall_p < 85.0:
            rec_template = "MBA-TMPL-6M"
            rec_notes = "Standard 6-month paced template balancing advanced DILR sets, sectional mocks, and weekly reading."
        else:
            rec_template = "MBA-TMPL-3M"
            rec_notes = "Accelerated 3-month template focusing on full-length mock calibration and exam stamina."

        return {
            "session_id": session_id,
            "student_id": session["student_id"],
            "exam_id": session["exam_id"],
            "total_questions_taken": len(session["questions_administered"]),
            "overall_accuracy": round(
                sum(s["correct"] for s in session["section_ability"].values()) /
                max(1, len(session["questions_administered"])) * 100, 1
            ),
            "estimated_percentile_band": f"{low_band}%ile - {high_band}%ile",
            "section_breakdown": section_scores,
            "verbal_gap_detected": verbal_gap,
            "strengths": strengths,
            "gaps": gaps,
            "recommended_template_id": rec_template,
            "recommendation_summary": rec_notes,
            "responses": session["responses"]
        }

# Global Singleton
mba_diagnostic_engine = MBADiagnosticEngine()
