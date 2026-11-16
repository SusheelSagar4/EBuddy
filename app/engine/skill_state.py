"""
Skill-state estimation from the evidence ledger (deterministic).

Evidence reliability (PS Section 4)
-----------------------------------
Every evidence item carries a *reliability tier*:

    strong  - assessed: course grades, adaptive diagnostics, quizzes, timed quizzes,
              rubric-graded projects, mock interviews, official exam results
    medium  - untimed / self-paced practice exercises
    weak    - self-declared interest or self-rating

The tier multiplies the per-source weight, so a self-declared "I am good at X" (weak, 0.2)
can never outweigh a diagnostic result (strong, 1.0). Self-declaration alone is capped at
level 40 with confidence 0.20 and therefore can never skip content or reach mastery.
"""
from typing import List, Dict, Optional
from datetime import datetime, timezone
from app.contracts.student import EvidenceItem, SkillState
from app.engine.interfaces import ISkillStateUpdater

SOURCE_WEIGHTS = {
    'official_gate': 1.0,
    'full_mock': 0.9,
    'timed_quiz': 0.9,
    'project_rubric': 0.85,
    'mock_interview': 0.8,
    'topic_test': 0.8,
    'course_grade': 0.7,
    'quiz': 0.7,
    'diagnostic': 0.7,
    'exercise': 0.6,
    'self_declaration': 0.2
}

# Reliability tier per evidence source
SOURCE_TIER = {
    'official_gate': 'strong', 'full_mock': 'strong', 'timed_quiz': 'strong',
    'project_rubric': 'strong', 'mock_interview': 'strong', 'topic_test': 'strong',
    'course_grade': 'strong', 'quiz': 'strong', 'diagnostic': 'strong',
    'exercise': 'medium',
    'self_declaration': 'weak',
}
TIER_WEIGHTS = {'strong': 1.0, 'medium': 0.6, 'weak': 0.2}

# Each older assessed item of the same skill counts RECENCY_DECAY times the next newer one.
RECENCY_DECAY = 0.7
SELF_DECLARED_LEVEL_CAP = 40.0
SELF_DECLARED_CONFIDENCE = 0.20


def reliability_tier_for(source_type: str) -> str:
    return SOURCE_TIER.get(source_type, 'medium')


def evidence_weight(ev: EvidenceItem) -> float:
    """Base weight of one evidence item before recency: source weight x reliability x attempts x tier override."""
    tier = ev.reliability_tier or reliability_tier_for(ev.source_type)
    base = SOURCE_WEIGHTS.get(ev.source_type, 0.6) * ev.reliability
    # An explicit tier can only LOWER trust relative to the source default (never raise a self-declaration).
    default_tier = reliability_tier_for(ev.source_type)
    if TIER_WEIGHTS[tier] < TIER_WEIGHTS[default_tier]:
        base = min(base, SOURCE_WEIGHTS.get(ev.source_type, 0.6) * TIER_WEIGHTS[tier])
    attempt_factor = 1.0 / (1.0 + 0.1 * max(0, ev.attempts - 1))
    return base * attempt_factor


class SkillStateUpdater(ISkillStateUpdater):
    def update_states(self, student_id: str, evidence_items: List[EvidenceItem]) -> List[SkillState]:
        grouped: Dict[str, List[EvidenceItem]] = {}
        for ev in evidence_items:
            if ev.student_id == student_id:
                grouped.setdefault(ev.skill_id, []).append(ev)

        states: List[SkillState] = []
        now = datetime.now(timezone.utc)

        for skill_id, items in grouped.items():
            tiers = [(it.reliability_tier or reliability_tier_for(it.source_type)) for it in items]
            only_self_declared = all(it.source_type == 'self_declaration' for it in items)
            strong_n = sum(1 for t in tiers if t == 'strong')
            medium_n = sum(1 for t in tiers if t == 'medium')
            weak_n = sum(1 for t in tiers if t == 'weak')

            # Recency: newest assessed evidence first (stable for equal timestamps)
            order = sorted(range(len(items)), key=lambda i: (items[i].recorded_at, i), reverse=True)
            total_weight = 0.0
            weighted_score_sum = 0.0
            rank_assessed = 0
            latest_assessed: Optional[EvidenceItem] = None
            for i in order:
                it = items[i]
                w = evidence_weight(it)
                if tiers[i] != 'weak':
                    if latest_assessed is None:
                        latest_assessed = it
                    w *= (RECENCY_DECAY ** rank_assessed)
                    rank_assessed += 1
                total_weight += w
                weighted_score_sum += it.score * w

            if total_weight > 0:
                est_level = min(100.0, max(0.0, weighted_score_sum / total_weight))
                if only_self_declared or (strong_n == 0 and medium_n == 0):
                    # Hard rule: self-declaration alone never reaches mastery
                    est_level = min(SELF_DECLARED_LEVEL_CAP, est_level)
                    confidence = SELF_DECLARED_CONFIDENCE
                else:
                    raw_weight = sum(evidence_weight(it) for it, t in zip(items, tiers) if t != 'weak')
                    confidence = min(0.99, raw_weight / (raw_weight + 2.0))
                    confidence = max(confidence, 0.21)
            else:
                est_level = 0.0
                confidence = 0.1

            if strong_n and weak_n:
                basis = 'mixed'
            elif strong_n:
                basis = 'strong'
            elif medium_n:
                basis = 'medium'
            else:
                basis = 'weak'

            states.append(SkillState(
                student_id=student_id,
                skill_id=skill_id,
                estimated_level=round(est_level, 2),
                confidence=round(confidence, 2),
                last_updated=now,
                strong_evidence_count=strong_n,
                weak_evidence_count=weak_n,
                evidence_basis=basis,
                latest_assessed_score=latest_assessed.score if latest_assessed else None,
                latest_assessed_source=latest_assessed.source_type if latest_assessed else None,
            ))

        return states
