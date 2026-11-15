from typing import Dict, Any, List
from app.contracts.chat import ContextCard, Explanation
from app.llm.client import llm_client

class Explainer:
    def explain_recommendation(self, item_description: str, card: ContextCard) -> Explanation:
        prompt = (
            f"Explainer Task.\n"
            f"Explain to student why {item_description} was recommended.\n"
            f"Verified Facts: {card.verified_facts}\n"
            f"Skill Gaps: {card.skill_gaps}\n"
            f"Disclaimer: {card.disclaimer}\n"
            f"Return JSON with 'short_summary', 'detailed_rationale', and 'citations'."
        )
        res = llm_client.generate(prompt, schema={"type": "object"}, purpose="explainer")
        return Explanation(
            subject=item_description,
            audience="student",
            short_summary=res.get("short_summary", "Recommended to target your priority skill gaps."),
            detailed_rationale=res.get("detailed_rationale", "This item addresses key requirements for your selected goal."),
            citations=res.get("citations", ["IITBBS Curriculum Records"])
        )

