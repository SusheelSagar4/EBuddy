from typing import Dict, Any, List, Optional
import json

class FakeLLM:
    """
    Deterministic offline Mock LLM for tests and airgap execution.
    Requires zero network access, produces consistent, schema-validated responses.
    """
    def __init__(self):
        self.call_history: List[Dict[str, Any]] = []

    def complete(self, prompt: str, schema: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        self.call_history.append({"prompt": prompt, "schema": schema, "kwargs": kwargs})

        # Deterministic responses based on task keywords in prompt
        p_lower = prompt.lower()
        msg_content = p_lower
        if "student message: '" in p_lower:
            msg_content = p_lower.split("student message: '")[1].split("'")[0]

        if "classify intent" in p_lower or "intent_router" in p_lower:
            if any(w in msg_content for w in ["weather", "movie", "cricket", "capital", "france", "world cup", "fifa", "football", "joke", "recipe", "song", "paris"]):
                return {"intent": "off_topic", "confidence": 0.99}
            elif "change goal" in msg_content or "switch" in msg_content:
                return {"intent": "goal_change", "confidence": 0.95}
            elif "why" in msg_content or "plan" in msg_content or "course" in msg_content:
                return {"intent": "plan_query", "confidence": 0.98}
            elif "quiz" in msg_content or "diagnostic" in msg_content:
                return {"intent": "diagnostic_request", "confidence": 0.92}
            return {"intent": "off_topic", "confidence": 0.85}

        elif "explain" in p_lower or "explainer" in p_lower:
            return {
                "short_summary": "Recommended based on your target career goal and prerequisite sequencing.",
                "detailed_rationale": "This course closes an identified skill gap while strictly complying with academic credit limits and semester parity.",
                "citations": ["EE_BTech_2016-17_Semester-wise_Curriculum.xlsx"]
            }

        elif "grade" in p_lower or "grader" in p_lower:
            return {
                "score": 85.0,
                "is_correct": True,
                "feedback": "Sound conceptual formulation and accurate derivation."
            }

        elif "clarify" in p_lower or "clarifier" in p_lower:
            return {
                "clarifying_question": "Would you prefer to focus on core VLSI or power system tracks for your electives?",
                "options": ["Core VLSI & Embedded", "Power Systems & Smart Grid", "Software & Data Science Transition"]
            }

        return {"response": "Processed deterministically by FakeLLM."}

