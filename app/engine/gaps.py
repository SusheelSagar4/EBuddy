from typing import List, Dict, Any, Optional
from app.contracts.goal import Goal, GoalRequirement
from app.contracts.student import SkillState, EvidenceItem
from app.engine.interfaces import IGapAnalyzer

class GapAnalyzer(IGapAnalyzer):
    def analyze_gaps(
        self,
        goal: Goal,
        requirements: List[GoalRequirement],
        skill_states: List[SkillState],
        interests: Optional[List[Dict[str, Any]]] = None,
        evidence: Optional[List[EvidenceItem]] = None
    ) -> List[Dict[str, Any]]:
        state_map = {s.skill_id: s.estimated_level for s in skill_states}
        conf_map = {s.skill_id: s.confidence for s in skill_states}

        # Index evidence by skill
        diagnostic_evidence_map: Dict[str, float] = {}
        if evidence:
            for ev in evidence:
                if ev.source_type == "diagnostic":
                    diagnostic_evidence_map[ev.skill_id] = ev.score

        gaps = []
        for req in requirements:
            if req.goal_id == goal.goal_id:
                current = state_map.get(req.skill_id, 0.0)
                conf = conf_map.get(req.skill_id, 0.0)
                gap_magnitude = max(0.0, req.required_level - current)

                # Prioritize by gap magnitude * importance
                priority = round(gap_magnitude * req.importance, 2)

                # Interest-vs-evidence conflict detection:
                # If target requirement is high (>= 70) and demonstrated level is low (< 40)
                # or diagnostic evidence score < 40 while enrolled in high target goal
                diag_score = diagnostic_evidence_map.get(req.skill_id)
                has_conflict = False
                conflict_reason = None

                if req.required_level >= 70.0 and (current < 40.0 or (diag_score is not None and diag_score < 40.0)):
                    has_conflict = True
                    conflict_reason = (
                        f"Student has high target aspiration ({req.required_level:.0f} in {req.skill_id}), "
                        f"but diagnostic/demonstrated evidence is low ({current:.1f}/100). "
                        "Remedial foundations must be bridged before advanced topics."
                    )

                gaps.append({
                    "skill_id": req.skill_id,
                    "target_level": req.required_level,
                    "current_level": current,
                    "gap": round(gap_magnitude, 2),
                    "confidence": conf,
                    "importance": req.importance,
                    "priority": priority,
                    "needs_remediation": gap_magnitude > 20.0 or has_conflict,
                    "conflict_flag": "HIGH_INTEREST_LOW_FOUNDATION" if has_conflict else None,
                    "conflict_description": conflict_reason
                })

        # Sort descending by priority
        gaps.sort(key=lambda x: -x["priority"])
        return gaps

