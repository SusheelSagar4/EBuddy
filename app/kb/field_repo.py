import os
import csv
from typing import List, Dict, Any, Optional

class FieldRoadmapRepo:
    """
    Repository for Field Roadmaps, Phases, Topics, and Course Eligibility.
    Loads relational CSV seeds with graceful offline fallback.
    """
    def __init__(self, seed_dir: Optional[str] = None):
        if not seed_dir:
            seed_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "seed", "kb")
        self.seed_dir = seed_dir
        
        self.roadmaps: Dict[str, Dict[str, Any]] = {}
        self.phases: Dict[str, Dict[str, Any]] = {} # phase_id -> phase
        self.topics: Dict[str, Dict[str, Any]] = {} # topic_id -> topic
        self.field_phases: Dict[str, List[Dict[str, Any]]] = {} # field_id -> [phases in order]
        self.phase_topics: Dict[str, List[Dict[str, Any]]] = {} # phase_id -> [topics in order]
        self.field_topics: Dict[str, List[Dict[str, Any]]] = {} # field_id -> [all topics in order]
        self.course_eligibilities: Dict[str, Dict[str, Any]] = {} # course_id -> eligibility_rule
        
        self._load_data()

    def _load_data(self):
        # 1. Field Roadmaps
        rm_path = os.path.join(self.seed_dir, "field_roadmap.csv")
        if os.path.exists(rm_path):
            with open(rm_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    fid = r["field_id"].strip()
                    self.roadmaps[fid] = {
                        "field_id": fid,
                        "name": r["name"].strip(),
                        "category": r["category"].strip(),
                        "description": r.get("description", "").strip(),
                        "total_phases": int(r.get("total_phases", 0)),
                        "total_estimated_hours": float(r.get("total_estimated_hours", 0.0)),
                        "source_id": r.get("source_id", "OFFICIAL")
                    }

        # 2. Field Phases
        ph_path = os.path.join(self.seed_dir, "field_phase.csv")
        if os.path.exists(ph_path):
            with open(ph_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    pid = r["phase_id"].strip()
                    fid = r["field_id"].strip()
                    phase_obj = {
                        "phase_id": pid,
                        "field_id": fid,
                        "phase_order": int(r.get("phase_order", 1)),
                        "phase_name": r["phase_name"].strip(),
                        "phase_objective": r.get("phase_objective", "").strip(),
                        "learner_outcome": r.get("learner_outcome", "").strip(),
                        "estimated_hours": float(r.get("estimated_hours", 0.0))
                    }
                    self.phases[pid] = phase_obj
                    self.field_phases.setdefault(fid, []).append(phase_obj)
            for fid in self.field_phases:
                self.field_phases[fid].sort(key=lambda x: x["phase_order"])

        # 3. Field Topics
        top_path = os.path.join(self.seed_dir, "field_topic.csv")
        if os.path.exists(top_path):
            with open(top_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    tid = r["topic_id"].strip()
                    fid = r["field_id"].strip()
                    pid = r["phase_id"].strip()
                    prereqs = [p.strip() for p in r.get("prerequisite_topic_ids", "").split(",") if p.strip()]
                    top_obj = {
                        "topic_id": tid,
                        "field_id": fid,
                        "phase_id": pid,
                        "topic_order": int(r.get("topic_order", 1)),
                        "title": r["title"].strip(),
                        "key_concepts": r.get("key_concepts", "").strip(),
                        "est_hours": float(r.get("est_hours", 6.0)),
                        "skill_id": r.get("skill_id", "").strip(),
                        "prerequisite_topic_ids": prereqs,
                        "resource_title": r.get("resource_title", "").strip(),
                        "resource_url": r.get("resource_url", "").strip()
                    }
                    self.topics[tid] = top_obj
                    self.phase_topics.setdefault(pid, []).append(top_obj)
                    self.field_topics.setdefault(fid, []).append(top_obj)
            for pid in self.phase_topics:
                self.phase_topics[pid].sort(key=lambda x: x["topic_order"])
            for fid in self.field_topics:
                self.field_topics[fid].sort(key=lambda x: x["topic_order"])

        # 4. Course Eligibility
        el_path = os.path.join(self.seed_dir, "course_eligibility.csv")
        if os.path.exists(el_path):
            with open(el_path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    cid = r["course_id"].strip()
                    progs = [p.strip().upper() for p in r.get("allowed_programmes", "ANY").split(",") if p.strip()]
                    self.course_eligibilities[cid] = {
                        "id": r.get("id", f"ELIG_{cid}"),
                        "course_id": cid,
                        "min_cgpa": float(r.get("min_cgpa", 0.0)),
                        "min_semester": int(r.get("min_semester", 1)),
                        "max_backlogs": int(r.get("max_backlogs", 99)),
                        "allowed_programmes": progs,
                        "rule_name": r.get("rule_name", "RULE_REGULAR_COURSE_ELIGIBILITY"),
                        "source_url": r.get("source_url", ""),
                        "verified": str(r.get("verified", "true")).lower() == "true"
                    }

    def list_roadmaps(self) -> List[Dict[str, Any]]:
        return list(self.roadmaps.values())

    def get_roadmap(self, field_id: str) -> Optional[Dict[str, Any]]:
        return self.roadmaps.get(field_id)

    def get_phases(self, field_id: str) -> List[Dict[str, Any]]:
        return self.field_phases.get(field_id, [])

    def get_topics(self, field_id: str, phase_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if phase_id:
            return self.phase_topics.get(phase_id, [])
        return self.field_topics.get(field_id, [])

    def get_topic_by_id(self, topic_id: str) -> Optional[Dict[str, Any]]:
        return self.topics.get(topic_id)

    def get_course_eligibility(self, course_id: str) -> Optional[Dict[str, Any]]:
        return self.course_eligibilities.get(course_id)

field_repo = FieldRoadmapRepo()

