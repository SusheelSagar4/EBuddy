import os
import csv
import json
import uuid
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone

from app.contracts.student import EvidenceItem, SkillState
from app.engine.skill_state import SkillStateUpdater
from app.kb.field_repo import field_repo

class TopicProgressService:
    """
    Manages student progress on field roadmap topics, including:
    1. Prior-knowledge verification test (Requirement F6): 10-15 items, 70% threshold,
       auto-skipping passed topics and updating Bayesian evidence ledger with reliability=0.9.
    2. Topic completion and state tracking.
    3. Periodic retention quizzes with interleaving (Requirement F7): triggered every 2-3 topics,
       tagging topics as 'strong' (>=80%) or 'weak' (<60%). Weak topics get revision tasks.
    """
    def __init__(self, seed_dir: Optional[str] = None):
        self.field_repo = field_repo
        self.skill_updater = SkillStateUpdater()
        self.seed_dir = seed_dir or os.path.join(os.path.dirname(__file__), "..", "..", "data", "seed", "kb")
        # In-memory progress store: student_id -> {topic_id: progress_dict}
        self._progress: Dict[str, Dict[str, Dict[str, Any]]] = {}
        # In-memory quiz counter: (student_id, field_id) -> count_of_completions
        self._completions_since_last_quiz: Dict[str, int] = {}
        # Preloaded questions cache
        self._questions_cache: List[Dict[str, Any]] = []
        self._load_question_banks()

    def _load_question_banks(self):
        questions = []
        # 1. Load from data_analyst question bank if available
        da_q_file = os.path.join(os.path.dirname(__file__), "..", "..", "data_analyst", "output", "01_da_question_bank.csv")
        if os.path.exists(da_q_file):
            with open(da_q_file, "r", encoding="utf-8-sig") as f:
                for r in csv.DictReader(f):
                    opts = [r.get(f"option_{k}", "").strip() for k in ["a", "b", "c", "d"] if r.get(f"option_{k}")]
                    corr = r.get("correct_option_text") or r.get("correct_answer") or ""
                    qid = r.get("question_id") or r.get("\ufeffquestion_id", "Q_DA")
                    questions.append({
                        "question_id": qid,
                        "skill_id": r.get("skill_id", "SKILL_DATA_ANALYST"),
                        "prompt": r.get("stem", ""),
                        "options": opts,
                        "correct_answer": corr,
                        "difficulty": float(r.get("difficulty_num", 2)) * 20.0,
                        "field_ids": ["FIELD_DATA_ANALYST", "FIELD_AIML"]
                    })

        # 2. Load from exercise.csv
        ex_file = os.path.join(self.seed_dir, "exercise.csv")
        if os.path.exists(ex_file):
            with open(ex_file, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    raw_opts = r.get("options", "")
                    opts = []
                    if raw_opts:
                        try:
                            parsed = json.loads(raw_opts)
                            if isinstance(parsed, list):
                                opts = parsed
                            elif isinstance(parsed, dict):
                                opts = [f"{k}: {v}" for k, v in parsed.items()]
                        except Exception:
                            opts = [opt.strip() for opt in raw_opts.split(",") if opt.strip()]

                    corr = ""
                    ans_key = r.get("answer_key", "")
                    if ans_key:
                        try:
                            p_ans = json.loads(ans_key)
                            corr = p_ans.get("correct", "") or p_ans.get("correct_option", "")
                        except Exception:
                            corr = ans_key

                    questions.append({
                        "question_id": r["exercise_id"],
                        "skill_id": r.get("skill_id", "SKILL_CORE"),
                        "prompt": r.get("prompt", ""),
                        "options": opts,
                        "correct_answer": corr,
                        "difficulty": float(r.get("difficulty", 3)) * 20.0,
                        "field_ids": ["FIELD_SDE", "FIELD_AIML", "FIELD_GATE_EE", "FIELD_GATE_ME", "FIELD_UPSC", "FIELD_CORE_RESEARCH"]
                    })

        self._questions_cache = questions

    # -------------------------------------------------------------------------
    # Topic Status Management
    # -------------------------------------------------------------------------
    def mark_topic_status(
        self,
        student_id: str,
        topic_id: str,
        field_id: str,
        status: str, # 'completed', 'skipped', 'in_progress'
        quiz_score: Optional[float] = None,
        mastery_tag: Optional[str] = None # 'strong', 'weak', 'neutral'
    ) -> Dict[str, Any]:
        """Records student topic status in progress state."""
        st_map = self._progress.setdefault(student_id, {})
        entry = st_map.get(topic_id, {
            "id": f"PROG_{student_id}_{topic_id}_{uuid.uuid4().hex[:6]}",
            "student_id": student_id,
            "topic_id": topic_id,
            "field_id": field_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        entry["status"] = status
        entry["completed_at"] = datetime.now(timezone.utc).isoformat() if status in ["completed", "skipped"] else None
        if quiz_score is not None:
            entry["quiz_score"] = float(quiz_score)
        if mastery_tag is not None:
            entry["mastery_tag"] = mastery_tag

        st_map[topic_id] = entry

        # Track count for periodic retention quiz triggers
        if status == "completed":
            key = f"{student_id}:{field_id}"
            self._completions_since_last_quiz[key] = self._completions_since_last_quiz.get(key, 0) + 1

        return entry

    def get_completed_topics(self, student_id: str, field_id: Optional[str] = None) -> Set[str]:
        st_map = self._progress.get(student_id, {})
        completed = set()
        for tid, entry in st_map.items():
            if entry.get("status") in ["completed", "skipped"]:
                if field_id is None or entry.get("field_id") == field_id:
                    completed.add(tid)
        return completed

    def get_weak_topics(self, student_id: str, field_id: Optional[str] = None) -> Set[str]:
        st_map = self._progress.get(student_id, {})
        weak = set()
        for tid, entry in st_map.items():
            if entry.get("mastery_tag") == "weak":
                if field_id is None or entry.get("field_id") == field_id:
                    weak.add(tid)
        return weak

    def get_strong_topics(self, student_id: str, field_id: Optional[str] = None) -> Set[str]:
        st_map = self._progress.get(student_id, {})
        strong = set()
        for tid, entry in st_map.items():
            if entry.get("mastery_tag") == "strong":
                if field_id is None or entry.get("field_id") == field_id:
                    strong.add(tid)
        return strong

    def get_student_progress_summary(self, student_id: str, field_id: str) -> Dict[str, Any]:
        all_topics = self.field_repo.get_topics(field_id)
        completed = self.get_completed_topics(student_id, field_id)
        weak = self.get_weak_topics(student_id, field_id)
        strong = self.get_strong_topics(student_id, field_id)

        pct = (len(completed) / max(1, len(all_topics))) * 100.0

        return {
            "student_id": student_id,
            "field_id": field_id,
            "total_topics": len(all_topics),
            "completed_topics_count": len(completed),
            "completion_percentage": round(pct, 1),
            "weak_topics_count": len(weak),
            "strong_topics_count": len(strong),
            "completed_topics": list(completed),
            "weak_topics": list(weak),
            "strong_topics": list(strong)
        }

    # -------------------------------------------------------------------------
    # Requirement F6: Prior-Knowledge Verification Test
    # -------------------------------------------------------------------------
    def generate_prior_knowledge_test(
        self,
        student_id: str,
        field_id: str,
        num_items: int = 10
    ) -> Dict[str, Any]:
        """
        Builds a configurable 10-15 question prior-knowledge test across field topics.
        """
        # Clamp items to valid range 10-15
        num_items = max(10, min(15, num_items))
        topics = self.field_repo.get_topics(field_id)
        
        # Match questions to topics / skills
        field_questions = [
            q for q in self._questions_cache
            if field_id in q.get("field_ids", [])
        ]
        if not field_questions:
            field_questions = self._questions_cache

        selected: List[Dict[str, Any]] = []
        topic_map: Dict[str, str] = {} # question_id -> topic_id

        # Distribute across early phases of the field
        for idx in range(num_items):
            topic = topics[idx % len(topics)] if topics else None
            tid = topic["topic_id"] if topic else f"TOPIC_{idx}"
            
            # Find candidate question
            matching = [
                q for q in field_questions
                if q not in selected and (
                    topic and (q.get("skill_id") == topic.get("skill_id") or topic["title"].lower() in q["prompt"].lower())
                )
            ]
            chosen = matching[0] if matching else (
                [q for q in field_questions if q not in selected][0]
                if [q for q in field_questions if q not in selected]
                else {
                    "question_id": f"PK_Q_{field_id}_{idx+1}",
                    "skill_id": topic.get("skill_id", "SKILL_FOUNDATION") if topic else "SKILL_FOUNDATION",
                    "prompt": f"Prior-knowledge assessment item for {topic['title'] if topic else 'Field Competency'}.",
                    "options": ["A: Option A", "B: Option B", "C: Option C", "D: Option D"],
                    "correct_answer": "A: Option A",
                    "difficulty": 50.0
                }
            )
            selected.append(chosen)
            topic_map[chosen["question_id"]] = tid

        return {
            "test_type": "prior_knowledge",
            "student_id": student_id,
            "field_id": field_id,
            "total_questions": len(selected),
            "pass_threshold_percentage": 70.0,
            "questions": [
                {
                    "question_id": q["question_id"],
                    "topic_id": topic_map.get(q["question_id"]),
                    "skill_id": q.get("skill_id"),
                    "prompt": q["prompt"],
                    "options": q["options"],
                    "difficulty": q.get("difficulty", 50.0)
                }
                for q in selected
            ]
        }

    def submit_prior_knowledge_test(
        self,
        student_id: str,
        field_id: str,
        answers: List[Dict[str, Any]],
        pass_threshold: float = 70.0
    ) -> Dict[str, Any]:
        """
        Evaluates the prior-knowledge test:
        1. Grades each answer against correct answers.
        2. If overall / topic score >= 70%: marks topic as 'skipped' / 'completed'.
        3. Updates Bayesian SkillState ledger with reliability = 0.9.
        4. Identifies the first unskipped topic where the personalized weekly plan begins.
        """
        # Build answer lookup
        q_lookup = {q["question_id"]: q for q in self._questions_cache}
        
        total_answers = len(answers)
        correct_count = 0
        topic_scores: Dict[str, List[bool]] = {}
        skill_scores: Dict[str, List[bool]] = {}

        for a in answers:
            qid = a.get("question_id")
            student_ans = (a.get("answer") or "").strip().lower()
            q_meta = q_lookup.get(qid, {})
            correct_ans = (q_meta.get("correct_answer") or a.get("correct_answer") or "").strip().lower()

            is_correct = False
            if student_ans and correct_ans:
                # Direct match or option prefix match (e.g., 'a' matches 'a: ...')
                if student_ans == correct_ans:
                    is_correct = True
                elif len(student_ans) == 1 and correct_ans.startswith(student_ans + ":"):
                    is_correct = True
                elif len(correct_ans) == 1 and student_ans.startswith(correct_ans + ":"):
                    is_correct = True
            elif a.get("is_correct") is not None:
                is_correct = bool(a.get("is_correct"))

            if is_correct:
                correct_count += 1

            tid = a.get("topic_id")
            if tid:
                topic_scores.setdefault(tid, []).append(is_correct)
            sid = q_meta.get("skill_id") or a.get("skill_id", "SKILL_FOUNDATION")
            skill_scores.setdefault(sid, []).append(is_correct)

        overall_score_pct = (correct_count / max(1, total_answers)) * 100.0

        # Determine skipped topics
        skipped_topics: List[str] = []
        all_topics = self.field_repo.get_topics(field_id)

        for top in all_topics:
            tid = top["topic_id"]
            if tid in topic_scores:
                t_answers = topic_scores[tid]
                t_pct = (sum(1 for c in t_answers if c) / len(t_answers)) * 100.0
                if t_pct >= pass_threshold or overall_score_pct >= pass_threshold:
                    self.mark_topic_status(
                        student_id=student_id,
                        topic_id=tid,
                        field_id=field_id,
                        status="skipped",
                        quiz_score=t_pct,
                        mastery_tag="strong"
                    )
                    skipped_topics.append(tid)
            elif overall_score_pct >= pass_threshold:
                # If high overall score (e.g. >= 70%), skip foundational Phase 1 topics
                if "PH1" in top.get("phase_id", "") or top.get("prerequisite_topic_ids") == []:
                    self.mark_topic_status(
                        student_id=student_id,
                        topic_id=tid,
                        field_id=field_id,
                        status="skipped",
                        quiz_score=overall_score_pct,
                        mastery_tag="strong"
                    )
                    skipped_topics.append(tid)

        # Update Bayesian SkillState with evidence reliability = 0.9
        evidence_items: List[EvidenceItem] = []
        for sid, bools in skill_scores.items():
            s_pct = (sum(1 for c in bools if c) / len(bools)) * 100.0
            evidence_items.append(EvidenceItem(
                evidence_id=f"EV_PK_{uuid.uuid4().hex[:6]}",
                student_id=student_id,
                skill_id=sid,
                score=round(s_pct, 1),
                reliability=0.9, # Requirement F6: reliability = 0.9 for test results
                source_type="diagnostic",
                recorded_at=datetime.now(timezone.utc)
            ))

        updated_skills: List[SkillState] = []
        if evidence_items:
            updated_skills = self.skill_updater.update_states(student_id, evidence_items)

        # Find first unskipped topic
        completed_set = self.get_completed_topics(student_id, field_id)
        first_unskipped = None
        for top in all_topics:
            if top["topic_id"] not in completed_set:
                first_unskipped = top
                break

        return {
            "status": "evaluated",
            "student_id": student_id,
            "field_id": field_id,
            "total_questions": total_answers,
            "correct_count": correct_count,
            "score_percentage": round(overall_score_pct, 1),
            "passed": overall_score_pct >= pass_threshold,
            "skipped_topics": skipped_topics,
            "first_unskipped_topic": first_unskipped,
            "updated_skills": [s.model_dump() for s in updated_skills]
        }

    # -------------------------------------------------------------------------
    # Requirement F7: Periodic Retention Quizzes & Adaptation
    # -------------------------------------------------------------------------
    def should_trigger_retention_quiz(
        self,
        student_id: str,
        field_id: str,
        frequency: int = 3
    ) -> bool:
        """Triggers retention quiz every 2-3 completed topics (default 3)."""
        key = f"{student_id}:{field_id}"
        count = self._completions_since_last_quiz.get(key, 0)
        return count >= frequency

    def generate_retention_quiz(
        self,
        student_id: str,
        field_id: str,
        num_recent: int = 2,
        num_earlier: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Generates interleaved retention quiz covering recent completed topics
        plus 1 earlier topic to strengthen long-term memory.
        """
        st_map = self._progress.get(student_id, {})
        completed_list = [
            tid for tid, entry in st_map.items()
            if entry.get("status") in ["completed", "skipped"] and entry.get("field_id") == field_id
        ]
        if not completed_list:
            return None

        recent_topics = completed_list[-num_recent:]
        earlier_topics = [t for t in completed_list if t not in recent_topics]
        interleaved_earlier = earlier_topics[0] if earlier_topics else (recent_topics[0] if recent_topics else None)

        quiz_target_topics = list(recent_topics)
        if interleaved_earlier and interleaved_earlier not in quiz_target_topics:
            quiz_target_topics.append(interleaved_earlier)

        quiz_questions = []
        for tid in quiz_target_topics:
            top = self.field_repo.get_topic_by_id(tid)
            title = top["title"] if top else tid
            # Find matching question
            matching = [
                q for q in self._questions_cache
                if title.lower() in q["prompt"].lower() or (top and q.get("skill_id") == top.get("skill_id"))
            ]
            q_item = matching[0] if matching else {
                "question_id": f"RET_Q_{tid}",
                "topic_id": tid,
                "skill_id": top.get("skill_id", "SKILL_CORE") if top else "SKILL_CORE",
                "prompt": f"Retention checkpoint item verifying mastery of {title}.",
                "options": ["A: Concept A", "B: Concept B", "C: Concept C", "D: Concept D"],
                "correct_answer": "A: Concept A",
                "difficulty": 60.0
            }
            q_dict = dict(q_item)
            q_dict["topic_id"] = tid
            quiz_questions.append(q_dict)

        return {
            "quiz_type": "retention_checkpoint",
            "student_id": student_id,
            "field_id": field_id,
            "target_topics": quiz_target_topics,
            "questions": quiz_questions
        }

    def submit_retention_quiz(
        self,
        student_id: str,
        field_id: str,
        answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Grades retention quiz:
        - Score >= 80%: Topic tagged 'strong'
        - Score < 60%: Topic tagged 'weak' -> adds revision task into next weekly plan
        - Score 60-79%: Topic tagged 'neutral'
        """
        results: Dict[str, Dict[str, Any]] = {}
        for a in answers:
            tid = a.get("topic_id")
            if not tid:
                continue
            is_corr = bool(a.get("is_correct"))
            if a.get("student_answer") and a.get("correct_answer"):
                is_corr = a["student_answer"].strip().lower() == a["correct_answer"].strip().lower()

            results.setdefault(tid, {"correct": 0, "total": 0})
            results[tid]["total"] += 1
            if is_corr:
                results[tid]["correct"] += 1

        topic_evaluations: List[Dict[str, Any]] = []
        for tid, counts in results.items():
            pct = (counts["correct"] / max(1, counts["total"])) * 100.0
            if pct >= 80.0:
                tag = "strong"
            elif pct < 60.0:
                tag = "weak"
            else:
                tag = "neutral"

            self.mark_topic_status(
                student_id=student_id,
                topic_id=tid,
                field_id=field_id,
                status="completed",
                quiz_score=pct,
                mastery_tag=tag
            )
            topic_evaluations.append({
                "topic_id": tid,
                "score_percentage": round(pct, 1),
                "mastery_tag": tag,
                "needs_revision": (tag == "weak")
            })

        # Reset completions counter since retention quiz is completed
        key = f"{student_id}:{field_id}"
        self._completions_since_last_quiz[key] = 0

        return {
            "status": "evaluated",
            "student_id": student_id,
            "field_id": field_id,
            "evaluations": topic_evaluations,
            "weak_topics_updated": [e["topic_id"] for e in topic_evaluations if e["needs_revision"]]
        }

topic_progress_service = TopicProgressService()
