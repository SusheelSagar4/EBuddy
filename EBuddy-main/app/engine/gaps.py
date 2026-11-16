from typing import List, Dict, Any
from app.contracts.goal import Goal, GoalRequirement
from app.contracts.student import SkillState
from app.engine.interfaces import IGapAnalyzer

class GapAnalyzer(IGapAnalyzer):
    def analyze_gaps(
        self,
        goal: Goal,
        requirements: List[GoalRequirement],
        skill_states: List[SkillState]
    ) -> List[Dict[str, Any]]:
        state_map = {s.skill_id: s.estimated_level for s in skill_states}
        conf_map = {s.skill_id: s.confidence for s in skill_states}

        gaps = []
        for req in requirements:
            if req.goal_id == goal.goal_id:
                current = state_map.get(req.skill_id, 0.0)
                conf = conf_map.get(req.skill_id, 0.0)
                gap_magnitude = max(0.0, req.required_level - current)

                # Prioritize by gap magnitude * importance
                priority = round(gap_magnitude * req.importance, 2)

                gaps.append({
                    "skill_id": req.skill_id,
                    "target_level": req.required_level,
                    "current_level": current,
                    "gap": round(gap_magnitude, 2),
                    "confidence": conf,
                    "importance": req.importance,
                    "priority": priority,
                    "needs_remediation": gap_magnitude > 20.0
                })

        # Sort descending by priority
        gaps.sort(key=lambda x: -x["priority"])
        return gaps

