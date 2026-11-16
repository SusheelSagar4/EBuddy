from typing import Dict, Any, List, Iterable
from app.contracts.chat import ContextCard
from app.llm.client import llm_client
from app.llm import guardrails


class Answerer:
    """
    Grounded free-text answer. The context handed to the model is a small, budgeted fact sheet built
    deterministically from the plan and the knowledge base; the model's output is post-filtered so that
    it cannot introduce course codes that are not in the catalogue.
    """

    def build_context(self, card: ContextCard, max_items: int = 12) -> str:
        lines = [
            f"Programme: {card.programme_id} | Semester: {card.current_semester} | CGPA: {card.cgpa}",
            f"Goal: {card.goal_name} ({card.goal_id})",
        ]
        current = [it for it in card.current_plan_items if (it.get("planning_status") in (None, "current"))][:max_items]
        if current:
            lines.append("Current-semester plan items:")
            for it in current:
                label = it.get("course_id") or it.get("title") or it.get("item_type")
                why = str((it.get("reason") or {}).get("why_this", ""))[:140]
                lines.append(f"- [{it.get('item_type')}] {label} {it.get('title') or ''}: {why}")
        if card.skill_gaps:
            lines.append("Skill levels (evidence-weighted): " + "; ".join(
                f"{g.get('skill_id')}={g.get('estimated_level')}" for g in card.skill_gaps[:8]))
        for f in card.verified_facts[:4]:
            lines.append(f"Fact: {f.get('fact')}: {f.get('value')}")
        for a in card.unverified_advisories[:3]:
            lines.append(f"Not confirmed yet: {a.get('advisory')}")
        return "\n".join(lines)

    def answer(self, question: str, card: ContextCard, valid_course_ids: Iterable[str]) -> Dict[str, Any]:
        prompt = (
            "Answer Task.\nCONTEXT:\n" + self.build_context(card) + "\n\n"
            + guardrails.wrap_untrusted(question, "STUDENT_QUESTION", limit=600)
            + "\nAnswer using only the CONTEXT."
        )
        res = llm_client.generate(prompt, purpose="answerer", student_id=card.student_id)
        meta = res.get("_meta", {})
        text = res.get("content")
        if not text or meta.get("fallback_used"):
            return {"text": None, "fallback_used": True, "meta": meta, "removed_codes": []}
        clean = guardrails.sanitize_output(text, valid_course_ids)
        return {"text": clean["text"], "fallback_used": False, "meta": meta, "removed_codes": clean["removed_codes"]}
