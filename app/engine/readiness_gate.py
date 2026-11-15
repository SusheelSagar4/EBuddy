import os
from typing import List, Dict, Optional, Any
from app.contracts.core_to_core import ReadinessGateResult
from app.contracts.student import EvidenceItem, SkillState
from app.kb.core_to_core_repo import core_kb_repo

class ReadinessGateEngine:
    """
    Deterministic Readiness Gate Evaluator.
    
    Hard constraints:
    - Never passes on self-declared evidence alone.
    - Requires:
      1. Tested mastery >= 0.75 (75%) on foundation skills for the target research area.
      2. At least 2 completed taster tasks with score >= 60%.
      3. At least 1 paper summary / literature check with score >= 60%.
    """
    def __init__(self):
        self.kb_repo = core_kb_repo

    def evaluate_gate(
        self,
        student_id: str,
        target_area_id: str,
        skill_states: List[SkillState],
        evidence_ledger: List[EvidenceItem],
        completed_taster_tasks: Optional[List[Dict[str, Any]]] = None,
        completed_paper_summaries: Optional[List[Dict[str, Any]]] = None
    ) -> ReadinessGateResult:
        completed_taster = completed_taster_tasks or []
        completed_papers = completed_paper_summaries or []

        # 1. Foundation skills for the area
        area_skills = [as_map for as_map in self.kb_repo.area_skills if as_map.area_id == target_area_id]
        if not area_skills:
            # Fallback to general department skills if area not found
            req_skill_ids = ["SKILL_CIRCUIT_ANALYSIS"] if "EE" in target_area_id else ["SKILL_PHYSICAL_METALLURGY"]
        else:
            req_skill_ids = [as_map.skill_id for as_map in area_skills]

        state_by_skill = {st.skill_id: st for st in skill_states}
        
        # Check evidence sources: MUST NOT be purely self-declaration
        tested_evidence_skills = set()
        for ev in evidence_ledger:
            if ev.source_type != "self_declaration" and ev.score >= 60.0:
                tested_evidence_skills.add(ev.skill_id)

        foundation_met = True
        skill_details = {}
        missing_reasons = []

        for sid in req_skill_ids:
            st = state_by_skill.get(sid)
            current_lvl = st.estimated_level if st else 0.0
            # Check if evidence exists from objective tests
            has_tested_ev = sid in tested_evidence_skills or (st is not None and st.confidence >= 0.5)
            
            # Target is 75.0 (0.75 on scale 0-100)
            passed_skill = (current_lvl >= 75.0) and has_tested_ev
            skill_details[sid] = {
                "current_level": current_lvl,
                "required_level": 75.0,
                "has_tested_evidence": has_tested_ev,
                "passed": passed_skill
            }
            if not passed_skill:
                foundation_met = False
                if not has_tested_ev:
                    missing_reasons.append(f"Foundation skill {sid} lacks verified test/quiz evidence.")
                else:
                    missing_reasons.append(f"Foundation skill {sid} proficiency is {current_lvl:.1f}% (required: 75.0%).")

        # 2. Taster Tasks: At least 2 with score >= 60%
        valid_tasters = [t for t in completed_taster if float(t.get("score", 0.0)) >= 60.0]
        taster_met = len(valid_tasters) >= 2
        avg_taster_score = (sum(float(t.get("score", 0.0)) for t in valid_tasters) / len(valid_tasters)) if valid_tasters else 0.0

        if not taster_met:
            missing_reasons.append(
                f"Completed {len(valid_tasters)}/2 required research taster tasks with score >= 60%."
            )

        # 3. Paper Summary: At least 1 with score >= 60%
        valid_papers = [p for p in completed_papers if float(p.get("score", 0.0)) >= 60.0]
        paper_met = len(valid_papers) >= 1
        best_paper_score = max([float(p.get("score", 0.0)) for p in valid_papers], default=0.0)

        if not paper_met:
            missing_reasons.append("Requires at least 1 guided paper reading and summary assessment with score >= 60%.")

        overall_passed = foundation_met and taster_met and paper_met

        return ReadinessGateResult(
            passed=overall_passed,
            student_id=student_id,
            foundation_skills_met=foundation_met,
            foundation_skills_details=skill_details,
            taster_tasks_met=taster_met,
            taster_tasks_completed=len(valid_tasters),
            taster_tasks_avg_score=avg_taster_score,
            paper_summary_met=paper_met,
            paper_summary_score=best_paper_score,
            reasons=missing_reasons if not overall_passed else ["All prerequisite readiness criteria satisfied. Faculty matching unlocked."]
        )

readiness_gate_engine = ReadinessGateEngine()
