from typing import List, Dict
from datetime import datetime, timezone
from app.contracts.student import EvidenceItem, SkillState
from app.engine.interfaces import ISkillStateUpdater

SOURCE_WEIGHTS = {
    'official_gate': 1.0,
    'full_mock': 0.9,
    'topic_test': 0.8,
    'course_grade': 0.7,
    'quiz': 0.7,
    'diagnostic': 0.7,
    'exercise': 0.6,
    'self_declaration': 0.2
}

class SkillStateUpdater(ISkillStateUpdater):
    def update_states(self, student_id: str, evidence_items: List[EvidenceItem]) -> List[SkillState]:
        # Group evidence by skill_id
        grouped: Dict[str, List[EvidenceItem]] = {}
        for ev in evidence_items:
            if ev.student_id == student_id:
                grouped.setdefault(ev.skill_id, []).append(ev)

        states: List[SkillState] = []
        now = datetime.now(timezone.utc)

        for skill_id, items in grouped.items():
            total_weight = 0.0
            weighted_score_sum = 0.0
            only_self_declared = all(it.source_type == 'self_declaration' for it in items)

            for it in items:
                base_w = SOURCE_WEIGHTS.get(it.source_type, 0.6) * it.reliability
                # More attempts slightly penalizes raw score or adjusts confidence
                attempt_factor = 1.0 / (1.0 + 0.1 * max(0, it.attempts - 1))
                w = base_w * attempt_factor
                total_weight += w
                weighted_score_sum += it.score * w

            if total_weight > 0:
                est_level = min(100.0, max(0.0, weighted_score_sum / total_weight))
                # Hard rule (§8.2): Self-declaration alone never reaches mastery
                if only_self_declared:
                    est_level = min(40.0, est_level)
                    confidence = 0.20
                else:
                    # Confidence scales asymptotically with total weight
                    confidence = min(0.99, total_weight / (total_weight + 2.0))
            else:
                est_level = 0.0
                confidence = 0.1

            states.append(SkillState(
                student_id=student_id,
                skill_id=skill_id,
                estimated_level=round(est_level, 2),
                confidence=round(confidence, 2),
                last_updated=now
            ))

        return states

