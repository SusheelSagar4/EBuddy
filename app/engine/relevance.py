import os
import csv
from typing import Dict, List, Any, Optional, Set, Tuple

class CourseRelevanceEngine:
    """
    Deterministic Course Relevance Engine.
    
    Principles:
    1. Relevance scores operate on an explicit 0-3 scale:
         0 = None (Unrelated)
         1 = Supporting (Foundational or domain breadth)
         2 = Useful (Relevant elective)
         3 = Essential (Core competency for target goal)
    2. Relevance scores are ONLY used to evaluate and rank elective/minor options.
       Major/Core courses are fixed by branch curriculum and are never excluded by relevance.
    3. An elective with an unmet prerequisite is NEVER recommended, regardless of relevance.
    """
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self.relevance_map: Dict[Tuple[str, str], Tuple[int, str]] = {} # (course_id, goal_id) -> (score, rationale)
        self.course_skills: Dict[str, Set[str]] = {}
        self._load()

    def _load(self):
        # 1. Load relevance tags
        rel_path = os.path.join(self.seed_dir, "relevance_tags.csv")
        if os.path.exists(rel_path):
            with open(rel_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    cid = r["course_id"].strip()
                    gid = r["goal_id"].strip()
                    score = int(r["relevance_score"])
                    rationale = r.get("rationale", "")
                    status = r.get("status", "draft_for_review")
                    source_id = r.get("source_id", "DESIGN_TEAM")
                    self.relevance_map[(cid, gid)] = (score, rationale, status, source_id)

        # 2. Load course skills for dynamic gap boosting
        cs_path = os.path.join(self.seed_dir, "course_skill.csv")
        if os.path.exists(cs_path):
            with open(cs_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    cid = r["course_id"].strip()
                    sid = r["skill_id"].strip()
                    self.course_skills.setdefault(cid, set()).add(sid)

    def get_relevance(self, course_id: str, goal_id: str) -> Tuple[int, str]:
        """Returns the canonical (score_0_to_3, rationale) for backwards compatibility."""
        entry = self.relevance_map.get((course_id, goal_id), (1, "General engineering curriculum", "draft_for_review", "DESIGN_TEAM"))
        return entry[0], entry[1]

    def get_relevance_details(self, course_id: str, goal_id: str) -> Dict[str, Any]:
        """Returns the full relevance metadata including status and source_id."""
        entry = self.relevance_map.get((course_id, goal_id), (1, "General engineering curriculum", "draft_for_review", "DESIGN_TEAM"))
        return {
            "score": entry[0],
            "rationale": entry[1],
            "status": entry[2],
            "source_id": entry[3]
        }

    def rank_electives(
        self,
        candidate_course_ids: List[str],
        goal_id: str,
        skill_gaps: Optional[List[Dict[str, Any]]] = None,
        completed_course_ids: Optional[List[str]] = None,
        prereq_map: Optional[Dict[str, Set[str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Filters and ranks elective course candidates:
        - Rejects candidates with unmet academic prerequisites.
        - Rejects candidates already completed.
        - Computes ranking score = base_relevance (0-3) + skill_gap_boost.
        - Returns ranked list sorted descending by ranking score.
        """
        completed_set = set(completed_course_ids or [])
        prereqs = prereq_map or {}
        gaps_dict = {g["skill_id"]: float(g.get("gap", 0.0)) for g in (skill_gaps or []) if g.get("gap", 0.0) > 0}

        ranked_candidates: List[Dict[str, Any]] = []

        for cid in candidate_course_ids:
            # 1. Reject if already taken
            if cid in completed_set:
                continue

            # 2. Reject if academic prerequisites are unmet
            required_prereqs = prereqs.get(cid, set())
            if not required_prereqs.issubset(completed_set):
                # Unmet prerequisite! Strictly exclude from recommendation
                continue

            # 3. Base relevance (0-3 scale) with provenance metadata
            rel_details = self.get_relevance_details(cid, goal_id)
            base_score = rel_details["score"]
            rationale = rel_details["rationale"]
            status = rel_details["status"]
            source_id = rel_details["source_id"]

            # 4. Skill gap boost (up to +1.0 for closing active gaps)
            gap_boost = 0.0
            closed_gaps = []
            for sid in self.course_skills.get(cid, set()):
                if sid in gaps_dict:
                    gap_boost += min(1.0, gaps_dict[sid] / 100.0)
                    closed_gaps.append(sid)

            total_rank = base_score + gap_boost

            ranked_candidates.append({
                "course_id": cid,
                "base_relevance": base_score,
                "total_rank": round(total_rank, 2),
                "rationale": rationale,
                "status": status,
                "source_id": source_id,
                "closed_gaps": closed_gaps,
                "prerequisites_satisfied": True
            })

        # Sort descending by total_rank, then base_relevance
        ranked_candidates.sort(key=lambda x: (x["total_rank"], x["base_relevance"]), reverse=True)
        return ranked_candidates

