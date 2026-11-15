import re
import datetime
from typing import List, Dict, Optional, Any
from app.contracts.core_to_mba import StoryDraft, MBAInterviewRubric
from app.kb.core_to_mba_repo import core_to_mba_repo

class MBAStoryEngine:
    """
    Story Building Engine (§1.6 & §7.5).
    Translates core engineering projects and career choices into structured business stories.

    Non-negotiable product rule (§4):
    STRICTLY NO GHOSTWRITING. The system never generates or rewrites essays for the student.
    It acts strictly as an interview coach: scoring student drafts against the 5-criterion
    interview rubric, highlighting missing quantifiable evidence, and asking probing questions.
    """
    def __init__(self, repo=None):
        self.repo = repo or core_to_mba_repo

    def evaluate_draft(
        self,
        student_id: str,
        kind: str,
        text: str,
        branch: str,
        previous_drafts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a student story draft, generates rubric scores, diffs, and probing feedback.
        """
        previous_drafts = previous_drafts or []
        version = len(previous_drafts) + 1
        norm_branch = "EE" if "EE" in branch.upper() else ("MM" if "MM" in branch.upper() else branch)

        cleaned_text = text.strip()
        words = cleaned_text.split()
        word_count = len(words)

        # 1. Structure Check (Problem -> Action -> Result / STAR framework)
        has_action_words = any(w in cleaned_text.lower() for w in ["built", "designed", "led", "developed", "analyzed", "reduced", "optimized", "implemented", "resolved"])
        has_result_words = any(w in cleaned_text.lower() for w in ["resulting in", "led to", "achieved", "delivered", "increased", "decreased", "improved", "enabled"])
        if word_count >= 60 and has_action_words and has_result_words:
            structure_score = 4
        elif word_count >= 35 and (has_action_words or has_result_words):
            structure_score = 3
        elif word_count >= 20:
            structure_score = 2
        else:
            structure_score = 1

        # 2. Content & Metrics Check (Numbers, percentages, technical domain terms)
        has_numbers = bool(re.search(r'\d+', cleaned_text))
        has_branch_terms = any(t in cleaned_text.lower() for t in [
            "circuit", "power", "grid", "voltage", "matlab", "simulink", "machine", "semiconductor",
            "alloy", "steel", "metallurgy", "furnace", "material", "yield", "scrap", "tensile",
            "operations", "supply chain", "cost", "efficiency", "client"
        ])
        if has_numbers and has_branch_terms and word_count >= 40:
            content_score = 4
        elif has_numbers or has_branch_terms:
            content_score = 3
        elif word_count >= 25:
            content_score = 2
        else:
            content_score = 1

        # 3. Self-Awareness & Transition Logic
        cliches = ["passion for management", "people person", "jack of all trades", "born leader", "money"]
        has_cliche = any(c in cleaned_text.lower() for c in cliches)
        has_reflection = any(r in cleaned_text.lower() for r in ["realized", "learned", "transition", "bridge", "gap", "perspective", "decision", "trade-off"])
        if has_reflection and not has_cliche:
            self_awareness_score = 4
        elif has_reflection:
            self_awareness_score = 3
        elif not has_cliche and word_count >= 25:
            self_awareness_score = 2
        else:
            self_awareness_score = 1

        # 4. Communication
        if 40 <= word_count <= 250 and not has_cliche:
            communication_score = 4
        elif word_count >= 25:
            communication_score = 3
        elif word_count >= 15:
            communication_score = 2
        else:
            communication_score = 1

        # 5. Handling Follow-ups
        # Evaluates robustness against counter-questions
        if structure_score >= 3 and content_score >= 3:
            followup_score = 4
        elif structure_score >= 2 or content_score >= 2:
            followup_score = 3
        else:
            followup_score = 2

        scores = {
            "Structure": structure_score,
            "Content": content_score,
            "Self-awareness": self_awareness_score,
            "Communication": communication_score,
            "Handling follow-ups": followup_score
        }

        # Build Probing Questions (Strictly coaching, NO ghostwriting)
        probing_questions: List[str] = []
        if not has_numbers:
            probing_questions.append(
                "Quantifiable evidence is missing: What were the exact metrics? (e.g. team size, % efficiency gained, hours saved, sample count, or budget managed)?"
            )
        if not has_branch_terms:
            probing_questions.append(
                f"Engineering grounding: How did your specific {norm_branch} technical intuition directly inform this decision or project outcome?"
            )
        if has_cliche:
            probing_questions.append(
                "Avoid common B-school clichés like 'passion for business'. What specific incident or operational bottleneck during your engineering studies made you realize you want to lead business decisions?"
            )
        if kind in ["why_mba", "why_not_core"] and "bridge" not in cleaned_text.lower() and "scale" not in cleaned_text.lower():
            probing_questions.append(
                f"Why an MBA instead of growing technically inside a {norm_branch} engineering firm? What executive responsibilities do you envision taking on that an M.Tech would not prepare you for?"
            )
        if not probing_questions:
            probing_questions.append(
                "If the interview panel challenges your assumptions by asking 'Why didn't you complete 2 years in industry first?', how would you substantiate your readiness today?"
            )

        # Version diff and progress analysis
        what_changed = None
        if previous_drafts:
            last_draft = previous_drafts[-1]
            last_scores = last_draft.get("rubric_scores", {})
            last_total = sum(last_scores.values()) if last_scores else 0
            cur_total = sum(scores.values())
            diff_pts = cur_total - last_total

            changes = []
            if len(words) > len(last_draft.get("text", "").split()):
                changes.append("Expanded detail and substantive argumentation")
            if has_numbers and not re.search(r'\d+', last_draft.get("text", "")):
                changes.append("Integrated concrete quantifiable metrics")
            if cur_total > last_total:
                changes.append(f"Rubric score improved by +{diff_pts} points ({last_total}/20 -> {cur_total}/20)")
            what_changed = "; ".join(changes) if changes else "Minor stylistic revisions."

        # Fetch rubric descriptions
        rubric_feedback = {}
        for crit, sc in scores.items():
            rub = self.repo.interview_rubrics.get(crit)
            bench = getattr(rub, f"score_{sc}", "") if rub else ""
            rubric_feedback[crit] = {
                "score": sc,
                "benchmark": bench
            }

        return {
            "student_id": student_id,
            "kind": kind,
            "version": version,
            "text": cleaned_text,
            "word_count": word_count,
            "scores": scores,
            "total_score": sum(scores.values()),
            "max_score": 20,
            "rubric_feedback": rubric_feedback,
            "probing_questions": probing_questions,
            "what_changed": what_changed,
            "coaching_notice": "Authoring rule: The buddy provides critique and probing feedback only; you author your own narrative."
        }

# Global Singleton
mba_story_engine = MBAStoryEngine()
