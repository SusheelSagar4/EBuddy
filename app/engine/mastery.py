"""
Mastery evaluation: COURSE COMPLETION is not DEMONSTRATED PROFICIENCY (PS 2.5).

Two separate ledgers are produced and never merged:

  course_completion         what the transcript says: courses passed (grade), courses registered now
  demonstrated_proficiency  what assessed evidence says, per goal skill:
                              - a timed assessment (timed quiz / quiz / adaptive diagnostic) at or above the threshold
                              - an evidence-weighted level at or above the goal's required level
                            and, at goal level, rubric-scored projects and mock interviews.

A skill whose course is passed but which has no qualifying assessment is reported as
`course_completed_only` - visible to the student as "completed, not yet demonstrated".
Self-declared evidence never counts towards any criterion.
"""
from typing import List, Dict, Any, Optional
from app.contracts.goal import Goal, MasteryCriteria, GoalRequirement
from app.contracts.student import EvidenceItem, SkillState
from app.engine.interfaces import IMasteryEvaluator

TIMED_SOURCES = ("timed_quiz", "quiz", "diagnostic")
PROJECT_SOURCES = ("project_rubric",)
INTERVIEW_SOURCES = ("mock_interview",)


class MasteryEvaluator(IMasteryEvaluator):
    def evaluate_mastery(
        self,
        student_id: str,
        goal: Goal,
        criteria: MasteryCriteria,
        evidence: List[EvidenceItem],
        requirements: Optional[List[GoalRequirement]] = None,
        skill_states: Optional[List[SkillState]] = None,
        completed_course_ids: Optional[List[str]] = None,
        current_course_ids: Optional[List[str]] = None,
        course_skills: Optional[Dict[str, List[str]]] = None,
        course_titles: Optional[Dict[str, str]] = None,
        skill_names: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        student_ev = [e for e in evidence if e.student_id == student_id]
        p = criteria.criteria
        min_skill_level = float(p.get("min_skill_level", 75.0))
        timed_thr = float(p.get("timed_quiz_threshold", 70.0))
        project_thr = float(p.get("rubric_project_threshold", 70.0))
        interview_thr = float(p.get("mock_interview_threshold", 65.0))
        req_projects = int(p.get("required_project_milestones", 1))
        req_assessments = int(p.get("required_timed_assessments", 2))
        req_interviews = int(p.get("required_mock_interviews", 0))

        # ---------------- legacy goal-level metrics (kept for backwards compatibility)
        quiz_scores = [e.score for e in student_ev if e.source_type in ("quiz", "diagnostic", "exercise", "timed_quiz")]
        avg_score = (sum(quiz_scores) / len(quiz_scores)) if quiz_scores else 0.0
        project_count = sum(1 for e in student_ev if (e.source_type in PROJECT_SOURCES and e.score >= project_thr)
                            or (e.source_type == "exercise" and e.score >= 70.0))
        assessment_count = sum(1 for e in student_ev if e.source_type in ("quiz", "timed_quiz"))
        interview_count = sum(1 for e in student_ev if e.source_type in INTERVIEW_SOURCES and e.score >= interview_thr)
        passed_score = avg_score >= min_skill_level
        passed_projects = project_count >= req_projects
        passed_assessments = assessment_count >= req_assessments
        passed_interviews = interview_count >= req_interviews
        is_completed = len(student_ev) >= 3
        demonstrated = passed_score and passed_projects and passed_assessments and passed_interviews

        # ---------------- ledger 1: course completion
        completed = list(completed_course_ids or [])
        current = list(current_course_ids or [])
        cs = course_skills or {}
        titles = course_titles or {}
        names = skill_names or {}
        goal_skill_ids = [r.skill_id for r in (requirements or [])]
        relevant_done = [c for c in completed if any(s in goal_skill_ids for s in cs.get(c, []))]
        relevant_now = [c for c in current if any(s in goal_skill_ids for s in cs.get(c, []))]
        course_completion = {
            "completed_courses": len(completed),
            "registered_this_semester": len(current),
            "goal_relevant_completed": [{"course_id": c, "title": titles.get(c, c), "skills": [s for s in cs.get(c, []) if s in goal_skill_ids]} for c in relevant_done],
            "goal_relevant_in_progress": [{"course_id": c, "title": titles.get(c, c), "skills": [s for s in cs.get(c, []) if s in goal_skill_ids]} for c in relevant_now],
            "note": "Passing or registering for a course is recorded here only. It does not count as demonstrated proficiency.",
        }

        # ---------------- ledger 2: demonstrated proficiency per goal skill
        states = {s.skill_id: s for s in (skill_states or [])}
        skills_out = []
        for r in (requirements or []):
            sid = r.skill_id
            evs = [e for e in student_ev if e.skill_id == sid]

            def best(sources):
                vals = [e.score for e in evs if e.source_type in sources]
                return max(vals) if vals else None

            timed_best, proj_best, int_best = best(TIMED_SOURCES), best(PROJECT_SOURCES), best(INTERVIEW_SOURCES)
            grade_best = best(("course_grade",))
            self_best = best(("self_declaration",))
            st = states.get(sid)
            level = st.estimated_level if st else 0.0
            assessed_ok = timed_best is not None and timed_best >= timed_thr
            level_ok = level >= r.required_level
            courses_done = [c for c in completed if sid in cs.get(c, [])]
            if assessed_ok and level_ok:
                status = "demonstrated"
            elif courses_done and not assessed_ok:
                status = "course_completed_only"
            elif evs and any(e.source_type != "self_declaration" for e in evs):
                status = "in_progress"
            elif self_best is not None:
                status = "self_declared_only"
            else:
                status = "no_evidence"
            skills_out.append({
                "skill_id": sid, "skill_name": names.get(sid, sid), "required_level": r.required_level,
                "estimated_level": round(level, 1), "confidence": st.confidence if st else 0.0,
                "evidence_basis": st.evidence_basis if st else None,
                "status": status,
                "courses_completed": courses_done,
                "evidence": {"timed_assessment_best": timed_best, "project_rubric_best": proj_best, "mock_interview_best": int_best,
                             "course_grade_based": grade_best, "self_declared": self_best},
                "criteria": [
                    {"name": f"Timed assessment >= {timed_thr:.0f}%", "met": assessed_ok,
                     "value": timed_best, "counts_towards_mastery": True},
                    {"name": f"Evidence-weighted level >= {r.required_level:.0f}", "met": level_ok,
                     "value": round(level, 1), "counts_towards_mastery": True},
                    {"name": "Course passed", "met": bool(courses_done), "value": ", ".join(courses_done) or None,
                     "counts_towards_mastery": False},
                    {"name": "Self-declared", "met": self_best is not None, "value": self_best, "counts_towards_mastery": False},
                ],
            })
        n_dem = sum(1 for s in skills_out if s["status"] == "demonstrated")
        total = len(skills_out)
        gap_list = [s["skill_id"] for s in skills_out if s["status"] == "course_completed_only"]
        goal_demonstrated = bool(total) and n_dem == total and passed_projects and passed_interviews
        demonstrated_proficiency = {
            "skills": skills_out,
            "skills_demonstrated": n_dem, "skills_total": total,
            "percentage": round(100.0 * n_dem / total, 1) if total else 0.0,
            "goal_level": [
                {"name": f"Rubric-scored projects >= {project_thr:.0f}%", "required": req_projects, "achieved": project_count, "met": passed_projects},
                {"name": "Timed assessments taken", "required": req_assessments, "achieved": assessment_count, "met": passed_assessments},
                {"name": f"Mock interviews >= {interview_thr:.0f}%", "required": req_interviews, "achieved": interview_count, "met": passed_interviews},
            ],
            "goal_demonstrated": goal_demonstrated,
            "completed_but_not_demonstrated": gap_list,
            "thresholds": {"timed_quiz": timed_thr, "rubric_project": project_thr, "mock_interview": interview_thr, "min_skill_level": min_skill_level},
        }

        return {
            "student_id": student_id,
            "goal_id": goal.goal_id,
            "status": "demonstrated_proficiency" if demonstrated else ("completed" if is_completed else "in_progress"),
            "demonstrated_proficiency": demonstrated,
            "is_completed": is_completed,
            "metrics": {
                "average_score": round(avg_score, 2),
                "threshold_score": min_skill_level,
                "completed_projects": project_count,
                "required_projects": req_projects,
                "completed_assessments": assessment_count,
                "required_assessments": req_assessments,
                "completed_mock_interviews": interview_count,
                "required_mock_interviews": req_interviews,
            },
            "evidence_count": len(student_ev),
            "course_completion": course_completion,
            "proficiency": demonstrated_proficiency,
        }
