import uuid
import re
from typing import List, Dict, Optional, Any
from app.contracts.core_to_mba import BranchPITopic, BranchPIQuestion, MBAInterviewQuestion, MBAInterviewRubric
from app.kb.core_to_mba_repo import core_to_mba_repo

class MBAInterviewEngine:
    """
    Interview and Branch Fundamentals Engine (§1.8, §7.7 & §11).
    Prepares core engineering students (EE & MM) for MBA admissions interviews:
    1. Technical viva on branch fundamentals (circuits, machines, power, metallurgy, materials).
    2. General Personal Interview (PI) questions (Introduction, Why MBA, Leadership, Ethics).
    3. Written Ability Test (WAT) essay evaluations.
    4. Rubric scoring (Structure, Content, Self-awareness, Communication, Handling follow-ups).
    """
    def __init__(self, repo=None):
        self.repo = repo or core_to_mba_repo
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def _normalize_branch(self, branch: str) -> str:
        b = branch.upper().strip()
        if "EE" in b:
            return "EE"
        if "MM" in b or "META" in b:
            return "MM"
        return b

    def get_branch_topics(self, branch: str) -> List[BranchPITopic]:
        norm_b = self._normalize_branch(branch)
        return [t for t in self.repo.branch_pi_topics.values() if t.reviewed and t.branch.upper() == norm_b]

    def get_branch_questions(self, branch: str, topic_id: Optional[str] = None) -> List[BranchPIQuestion]:
        norm_b = self._normalize_branch(branch)
        questions = [
            q for q in self.repo.branch_pi_questions.values()
            if q.reviewed and q.branch.upper() == norm_b
        ]
        if topic_id:
            questions = [q for q in questions if q.topic_id == topic_id]
        return questions

    def get_general_pi_questions(self, category: Optional[str] = None) -> List[MBAInterviewQuestion]:
        qs = [q for q in self.repo.interview_questions.values() if q.category.upper() != "WAT"]
        if category:
            qs = [q for q in qs if q.category.lower() == category.lower()]
        return qs

    def get_wat_topics(self) -> List[MBAInterviewQuestion]:
        return [q for q in self.repo.interview_questions.values() if q.category.upper() == "WAT"]

    def start_mock_pi_session(self, student_id: str, branch: str) -> Dict[str, Any]:
        """
        Assembles a 5-question structured mock interview panel.
        """
        norm_b = self._normalize_branch(branch)
        session_id = f"pi_{uuid.uuid4().hex[:12]}"

        # Assemble mix:
        # 1. Intro (MBA-IQ01)
        # 2. Why MBA / Why not core (MBA-IQ04 or MBA-IQ02)
        # 3. Branch Tech Q1
        # 4. Branch Tech Q2
        # 5. Leadership / Failure (MBA-IQ09 or MBA-IQ08)
        flow: List[Dict[str, Any]] = []

        q_intro = self.repo.interview_questions.get("MBA-IQ01")
        if q_intro:
            flow.append({
                "question_id": q_intro.id,
                "type": "General PI",
                "category": q_intro.category,
                "question": q_intro.question,
                "what_good_looks_like": q_intro.what_good_looks_like
            })

        q_why = self.repo.interview_questions.get("MBA-IQ04") or self.repo.interview_questions.get("MBA-IQ02")
        if q_why:
            flow.append({
                "question_id": q_why.id,
                "type": "Motivation",
                "category": q_why.category,
                "question": q_why.question,
                "what_good_looks_like": q_why.what_good_looks_like
            })

        tech_qs = self.get_branch_questions(norm_b)
        if len(tech_qs) >= 2:
            flow.append({
                "question_id": tech_qs[0].id,
                "type": "Branch Technical",
                "category": f"{norm_b} Fundamentals",
                "question": tech_qs[0].question,
                "what_good_looks_like": tech_qs[0].what_good_looks_like
            })
            flow.append({
                "question_id": tech_qs[1].id,
                "type": "Branch Technical",
                "category": f"{norm_b} Techno-Commercial",
                "question": tech_qs[1].question,
                "what_good_looks_like": tech_qs[1].what_good_looks_like
            })

        q_lead = self.repo.interview_questions.get("MBA-IQ09") or self.repo.interview_questions.get("MBA-IQ08")
        if q_lead:
            flow.append({
                "question_id": q_lead.id,
                "type": "Leadership & Experience",
                "category": q_lead.category,
                "question": q_lead.question,
                "what_good_looks_like": q_lead.what_good_looks_like
            })

        session = {
            "session_id": session_id,
            "student_id": student_id,
            "branch": norm_b,
            "questions": flow,
            "current_index": 0,
            "responses": [],
            "completed": False
        }
        self.sessions[session_id] = session

        return {
            "session_id": session_id,
            "student_id": student_id,
            "branch": norm_b,
            "total_questions": len(flow),
            "current_question": flow[0] if flow else None
        }

    def evaluate_response(
        self,
        session_id: str,
        question_id: str,
        answer_text: str
    ) -> Dict[str, Any]:
        """
        Evaluates a mock interview response against rubric and expected benchmark.
        """
        session = self.sessions.get(session_id)
        if not session:
            raise KeyError(f"PI Session '{session_id}' not found.")

        # Find target question in session or repo
        q_obj = None
        for q in session["questions"]:
            if q["question_id"] == question_id:
                q_obj = q
                break

        expected = q_obj.get("what_good_looks_like", "") if q_obj else ""
        cleaned = answer_text.strip()
        words = cleaned.split()
        word_count = len(words)

        # Rubric scoring
        # 1. Structure
        if word_count >= 50 and any(w in cleaned.lower() for w in ["first", "second", "specifically", "therefore", "for example"]):
            structure = 4
        elif word_count >= 30:
            structure = 3
        elif word_count >= 15:
            structure = 2
        else:
            structure = 1

        # 2. Content & Accuracy
        # Check keyword overlaps with expected benchmark
        exp_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', expected.lower()))
        ans_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', cleaned.lower()))
        overlap = len(exp_words.intersection(ans_words))
        
        if overlap >= 3 and word_count >= 40:
            content = 4
        elif overlap >= 1 or word_count >= 30:
            content = 3
        elif word_count >= 15:
            content = 2
        else:
            content = 1

        # 3. Self-awareness
        if any(w in cleaned.lower() for w in ["learned", "realized", "perspective", "trade-off", "limitation"]):
            self_awareness = 4
        elif word_count >= 25:
            self_awareness = 3
        else:
            self_awareness = 2

        # 4. Communication
        if 35 <= word_count <= 250:
            comm = 4
        elif word_count >= 20:
            comm = 3
        else:
            comm = 2

        # 5. Handling follow-ups
        followup = min(4, max(2, (structure + content) // 2 + 1))

        scores = {
            "Structure": structure,
            "Content": content,
            "Self-awareness": self_awareness,
            "Communication": comm,
            "Handling follow-ups": followup
        }
        total_score = sum(scores.values())

        # Construct feedback
        feedback_points = []
        if content < 3:
            feedback_points.append(f"Technical precision: Anchor your response closer to the core mechanism ({expected}).")
        if structure < 3:
            feedback_points.append("Structure: Begin with a direct answer or thesis before illustrating with context.")
        if not feedback_points:
            feedback_points.append("Strong response: Crisp delivery with correct technical and contextual grounding.")

        # Follow-up grilling question
        followup_grill = (
            "Panel Follow-up: 'If an executive challenges your premise and asks why you wouldn't implement this "
            "with a lower-cost software alternative instead, how do you justify the capital outlay?'"
        )

        response_record = {
            "question_id": question_id,
            "answer_text": cleaned,
            "scores": scores,
            "total_score": total_score,
            "max_score": 20,
            "feedback": "; ".join(feedback_points),
            "followup_question": followup_grill
        }
        session["responses"].append(response_record)

        session["current_index"] += 1
        has_next = session["current_index"] < len(session["questions"])
        next_q = session["questions"][session["current_index"]] if has_next else None
        if not has_next:
            session["completed"] = True

        return {
            "session_id": session_id,
            "evaluated_question_id": question_id,
            "scores": scores,
            "total_score": total_score,
            "feedback": "; ".join(feedback_points),
            "followup_grill": followup_grill,
            "completed": not has_next,
            "next_question": next_q
        }

    def evaluate_wat_essay(self, student_id: str, topic_id: str, essay_text: str) -> Dict[str, Any]:
        """
        Evaluates a Written Ability Test (WAT) essay against structure and argument rubrics.
        """
        q = self.repo.interview_questions.get(topic_id)
        topic_title = q.question if q else "General WAT Topic"

        cleaned = essay_text.strip()
        words = cleaned.split()
        word_count = len(words)

        # Scoring
        # Ideal WAT essay is 180 to 250 words
        if 160 <= word_count <= 260:
            comm = 4
        elif 120 <= word_count <= 320:
            comm = 3
        else:
            comm = 2

        has_thesis = any(w in cleaned.lower() for w in ["in conclusion", "furthermore", "on the other hand", "while", "however"])
        structure = 4 if has_thesis and word_count >= 150 else (3 if has_thesis else 2)
        content = 4 if word_count >= 150 and any(w in cleaned.lower() for w in ["economic", "social", "policy", "impact", "industry"]) else 3
        self_awareness = 3
        followup = 3

        scores = {
            "Structure": structure,
            "Content": content,
            "Self-awareness": self_awareness,
            "Communication": comm,
            "Handling follow-ups": followup
        }

        return {
            "student_id": student_id,
            "topic_id": topic_id,
            "topic": topic_title,
            "word_count": word_count,
            "target_word_count": "180 - 250 words",
            "scores": scores,
            "total_score": sum(scores.values()),
            "max_score": 20,
            "critique": (
                "Well-structured argument with balanced perspectives."
                if sum(scores.values()) >= 16 else
                "Ensure your position is clearly stated in the introductory paragraph and backed by two distinct arguments."
            )
        }

# Global Singleton
mba_interview_engine = MBAInterviewEngine()
