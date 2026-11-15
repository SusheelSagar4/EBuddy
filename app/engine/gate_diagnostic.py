import os
import csv
import json
from typing import List, Dict, Any, Optional, Set
from app.contracts.kb import Exercise
from app.contracts.core_to_mtech import SyllabusTopic
from app.kb.core_to_mtech_repo import core_to_mtech_repo

# Evidence weights (§8.2)
GATE_EVIDENCE_WEIGHTS = {
    "official_gate": 1.0,
    "full_mock": 0.9,
    "topic_test": 0.8,
    "course_grade": 0.7,
    "exercise": 0.6,
    "self_declaration": 0.2
}

class GATEDiagnosticItem:
    def __init__(
        self,
        item_id: str,
        paper_code: str,
        topic_id: str,
        section: str,
        question_text: str,
        question_type: str,
        options: List[str],
        correct_answer: str,
        difficulty: float, # 1.0 to 5.0
        solution_text: str
    ):
        self.item_id = item_id
        self.paper_code = paper_code
        self.topic_id = topic_id
        self.section = section
        self.question_text = question_text
        self.question_type = question_type
        self.options = options
        self.correct_answer = correct_answer
        self.difficulty = difficulty
        self.solution_text = solution_text

class GATEAdaptiveDiagnostic:
    """
    Adaptive Diagnostic Engine for GATE Preparation (§8.2).
    - Items come from verified practice questions tagged to syllabus topics.
    - Start at medium difficulty; adjust up or down; probe prerequisite topics on errors.
    - Stop per topic at 3 items or high confidence; cap 15 items per session.
    - Skip topics proven by strong course grades in mapped courses (coverage = full, grade >= 8.5).
    - Evidence weights: official GATE 1.0, full mock 0.9, topic test 0.8, course grade 0.7, exercise 0.6, self-declared 0.2.
    """
    def __init__(self, seed_file: str = "data/seed/core_to_mtech/practice_questions.csv", repo=None):
        self.repo = repo or core_to_mtech_repo
        self.item_bank: Dict[str, List[GATEDiagnosticItem]] = {} # topic_id -> items
        self.items_by_id: Dict[str, GATEDiagnosticItem] = {}
        self._load_items(seed_file)

    def _load_items(self, seed_file: str):
        if not os.path.exists(seed_file):
            return
        with open(seed_file, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                opts = []
                if r.get("options_json"):
                    try:
                        opts = json.loads(r["options_json"])
                    except Exception:
                        opts = [opt.strip() for opt in r["options_json"].split(",")]
                item = GATEDiagnosticItem(
                    item_id=r["id"],
                    paper_code=r["paper_code"],
                    topic_id=r["topic_id"],
                    section=r["section"],
                    question_text=r["question_text"],
                    question_type=r["question_type"],
                    options=opts,
                    correct_answer=r["correct_answer"],
                    difficulty=float(r.get("difficulty", 2.5)),
                    solution_text=r.get("solution_text", "")
                )
                self.item_bank.setdefault(r["topic_id"], []).append(item)
                self.items_by_id[r["id"]] = item

    def get_candidate_topics(
        self,
        paper_code: str,
        completed_courses: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        Returns topics for the paper, skipping those proven by strong grades (grade >= 8.5)
        in fully-mapped courses (§8.2).
        """
        all_topics = self.repo.get_topics_for_paper(paper_code)
        skipped_topics: Set[str] = set()

        if completed_courses:
            for cc in completed_courses:
                ccode = cc.get("course_code") or cc.get("course_id")
                gp = cc.get("grade_points", 0.0)
                grade_str = str(cc.get("grade", "")).upper()
                if gp >= 8.5 or grade_str in ["EX", "A", "A+"]:
                    # Check if this course maps with coverage == 'full'
                    for ctm in self.repo.course_topic_maps:
                        if ctm.course_code == ccode and ctm.coverage == "full":
                            skipped_topics.add(ctm.topic_id)

        candidates = [t.id for t in all_topics if t.id not in skipped_topics]
        return candidates

    def select_next_item(
        self,
        candidate_topics: List[str],
        previous_answers: List[Dict[str, Any]],
        max_session_items: int = 15
    ) -> Optional[GATEDiagnosticItem]:
        """
        Selects next item using Item Response Theory (IRT) adaptation.
        Caps at 15 items per session.
        Stops per topic at 3 items or when 2 consecutive answers are correct.
        """
        if len(previous_answers) >= max_session_items:
            return None

        asked_ids = {a["item_id"] for a in previous_answers}

        # Count questions and correct answers per topic
        topic_stats: Dict[str, Dict[str, Any]] = {}
        for a in previous_answers:
            tid = a["topic_id"]
            stat = topic_stats.setdefault(tid, {"count": 0, "correct": 0, "consecutive_correct": 0, "last_diff": 2.5})
            stat["count"] += 1
            if a.get("is_correct"):
                stat["correct"] += 1
                stat["consecutive_correct"] += 1
            else:
                stat["consecutive_correct"] = 0
            stat["last_diff"] = a.get("difficulty", 2.5)

        for tid in candidate_topics:
            stat = topic_stats.get(tid, {"count": 0, "correct": 0, "consecutive_correct": 0, "last_diff": 2.5})
            # Termination criteria per topic: 3 items or 2 consecutive correct answers
            if stat["count"] >= 3 or stat["consecutive_correct"] >= 2:
                continue

            available = [it for it in self.item_bank.get(tid, []) if it.item_id not in asked_ids]
            if not available:
                continue

            # Determine target difficulty based on last answer
            if stat["count"] == 0:
                target_diff = 2.5 # start medium
            elif previous_answers[-1]["topic_id"] == tid and previous_answers[-1].get("is_correct"):
                target_diff = min(5.0, stat["last_diff"] + 1.2) # step up difficulty
            else:
                target_diff = max(1.0, stat["last_diff"] - 1.2) # step down / probe prerequisites

            # Pick closest available item
            available.sort(key=lambda x: abs(x.difficulty - target_diff))
            return available[0]

        return None

    def evaluate_answer(
        self,
        item_id: str,
        student_answer: str
    ) -> Dict[str, Any]:
        item = self.items_by_id.get(item_id)
        if not item:
            return {"is_correct": False, "score": 0.0, "solution": ""}

        is_corr = False
        if item.question_type == "NAT":
            try:
                ans_float = float(student_answer.strip())
                corr_float = float(item.correct_answer.strip())
                is_corr = abs(ans_float - corr_float) <= 0.20 # numerical tolerance
            except Exception:
                is_corr = False
        elif item.question_type == "MSQ":
            try:
                corr_set = set(json.loads(item.correct_answer))
                stu_set = set(json.loads(student_answer) if student_answer.startswith("[") else [student_answer.strip()])
                is_corr = (corr_set == stu_set)
            except Exception:
                is_corr = (student_answer.strip().lower() == item.correct_answer.strip().lower())
        else:
            is_corr = (student_answer.strip().lower() == item.correct_answer.strip().lower())

        score = 100.0 if is_corr else 0.0
        return {
            "item_id": item_id,
            "topic_id": item.topic_id,
            "difficulty": item.difficulty,
            "is_correct": is_corr,
            "score": score,
            "solution": item.solution_text
        }

    def compute_topic_mastery(
        self,
        topic_id: str,
        evidence_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Computes Bayesian topic mastery using evidence weights (§8.2).
        Hard constraint: self-declared evidence has weight 0.2 and alone CANNOT reach mastery (> 40.0).
        """
        topic_ev = [e for e in evidence_list if e.get("topic_id") == topic_id]
        if not topic_ev:
            return {"topic_id": topic_id, "mastery": 0.0, "confidence": 0.1, "is_mastered": False}

        # Check if ONLY self-declared
        only_self_declared = all(e.get("source_type") == "self_declaration" for e in topic_ev)

        total_weight = 0.0
        weighted_sum = 0.0

        for ev in topic_ev:
            stype = ev.get("source_type", "exercise")
            w = GATE_EVIDENCE_WEIGHTS.get(stype, 0.6)
            score = float(ev.get("score", 0.0))
            total_weight += w
            weighted_sum += (score * w)

        if total_weight > 0:
            raw_mastery = weighted_sum / total_weight
        else:
            raw_mastery = 0.0

        # Enforce rule: self-declared alone never reaches mastery
        if only_self_declared:
            raw_mastery = min(40.0, raw_mastery)
            confidence = 0.20
        else:
            confidence = min(0.99, total_weight / (total_weight + 1.5))

        mastery_0_1 = round(raw_mastery / 100.0, 3)
        return {
            "topic_id": topic_id,
            "mastery": mastery_0_1,
            "confidence": round(confidence, 2),
            "is_mastered": (mastery_0_1 >= 0.75 and not only_self_declared)
        }

# Global singleton
gate_diagnostic_engine = GATEAdaptiveDiagnostic()
