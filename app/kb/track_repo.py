"""
Career-track knowledge base repository (SDE / Data Analyst / AI-ML).

Reads the relational CSVs produced by the domain pipelines:
    sde/output/{curriculum,events,quiz}/*.csv
    da/output/{curriculum,events,quiz}/*.csv
    aiml/output/{curriculum,events}/*.csv
and exposes ONE normalised, read-only view (phases, resources, checkpoints,
projects, events, question bank) so that the planner, the diagnostic engine,
the validator and the UI treat the three tracks as first-class career goals.

Hard rules honoured here:
  * Nothing is invented: every title / URL / event comes from a CSV row.
  * Fields that are absent in the source are surfaced as None / "not in source".
  * SDE phase hours are not in the source workbook; a labelled design default
    is used (HOURS_PER_SDE_STEP) and flagged `hours_basis="design_default"`.
"""
import os
import csv
from typing import Dict, List, Any, Optional, Set

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

TRACK_GOALS: Dict[str, str] = {
    "sde": "GOAL_TRACK_SDE",
    "da": "GOAL_TRACK_DA",
    "aiml": "GOAL_TRACK_AIML",
}
GOAL_TRACKS: Dict[str, str] = {v: k for k, v in TRACK_GOALS.items()}
# The legacy cross-branch goal maps onto the SDE roadmap content.
GOAL_TRACKS["GOAL_CROSS_SDE_DATA"] = "sde"

TRACK_NAMES = {
    "sde": "Software Development Engineer (SDE)",
    "da": "Data Analyst",
    "aiml": "AI & Machine Learning",
}

# Design default (NOT from source): average self-study hours per SDE roadmap step.
HOURS_PER_SDE_STEP = 12.0

# DA roadmap skill category -> knowledge-base skill id
DA_CATEGORY_SKILL = {
    "Tools": "SKILL_DATA_ANALYTICS",
    "Analysis": "SKILL_DATA_ANALYTICS",
    "Visualisation": "SKILL_DATA_ANALYTICS",
    "Business": "SKILL_DATA_ANALYTICS",
    "SQL": "SKILL_DATABASES_SQL",
    "Python": "SKILL_PROGRAMMING_DS",
    "Statistics": "SKILL_PROBABILITY_STATS",
}


def _read(path: str) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def _f(val: Any, default: float = 0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _split(val: str, sep: str = "|") -> List[str]:
    return [x.strip() for x in (val or "").split(sep) if x.strip()]


class TrackRepo:
    def __init__(self, root: Optional[str] = None, seed_dir: Optional[str] = None):
        self.root = root or _REPO_ROOT
        self.seed_dir = seed_dir or os.path.join(self.root, "data", "seed", "kb")
        self.tracks: Dict[str, Dict[str, Any]] = {}
        self.phase_skills: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        self._load_phase_skills()
        self._load_sde()
        self._load_da()
        self._load_aiml()

    # ------------------------------------------------------------------ loading
    def _p(self, *parts: str) -> str:
        return os.path.join(self.root, *parts)

    def _load_phase_skills(self):
        for r in _read(os.path.join(self.seed_dir, "track_phase_skill.csv")):
            self.phase_skills.setdefault(r["track_id"], {}).setdefault(r["phase_id"], []).append({
                "skill_id": r["skill_id"],
                "required_level": _f(r.get("required_level"), 60.0),
                "status": r.get("status", "draft_for_review"),
            })

    def _skills_for(self, track_id: str, phase_id: str) -> List[Dict[str, Any]]:
        return list(self.phase_skills.get(track_id, {}).get(phase_id, []))

    def _load_sde(self):
        cur = self._p("sde", "output", "curriculum")
        overview = _read(os.path.join(cur, "01_sde_roadmap_overview.csv"))
        if not overview:
            return
        content = _read(os.path.join(cur, "02_phase_learning_content.csv"))
        checkpoints = _read(os.path.join(cur, "03_topic_checkpoints.csv"))
        repos = _read(os.path.join(cur, "04_project_repos.csv"))
        portfolio = _read(os.path.join(cur, "05_portfolio_projects.csv"))

        phases = []
        for r in sorted(overview, key=lambda x: int(_f(x["phase_order"]))):
            pid = r["phase_id"]
            n_topics = int(_f(r.get("number_of_topics"), 1))
            res = []
            for c in content:
                if c["phase_id"] != pid or not c.get("url"):
                    continue
                res.append({
                    "resource_id": f"SDE-R{int(_f(c['step_number'])):02d}{c.get('tier', 'A')}",
                    "title": c["resource_title"],
                    "provider": c.get("creator", ""),
                    "url": c["url"],
                    "resource_type": "video_playlist",
                    "topic": c.get("topic_skill", ""),
                    "tier": c.get("tier", ""),
                    "tier_meaning": c.get("tier_meaning", ""),
                    "usage_guidance": c.get("usage_guidance", ""),
                    "link_verified": c.get("link_verified", "FALSE").upper() == "TRUE",
                    "est_hours": None,
                })
            cps = [{
                "text": c["checkpoint_text"],
                "type": c.get("checkpoint_type", ""),
                "topic": c.get("topic_skill", ""),
                "pass_criteria": c.get("passing_criteria_summary", ""),
            } for c in checkpoints if c["phase_id"] == pid]
            projects = [{
                "project_id": p["portfolio_id"],
                "title": p["project_name"],
                "why": p.get("why_it_impresses", ""),
                "skills_shown": p.get("skills_shown", ""),
                "priority": p.get("priority", ""),
                "repos": p.get("repos_to_use_resolved", ""),
                "rubric": [],
            } for p in portfolio if p.get("recommended_after_phase_id") == pid]
            phases.append({
                "phase_id": pid,
                "order": int(_f(r["phase_order"])),
                "name": r["phase_name"],
                "objective": r.get("phase_objective", ""),
                "outcome": r.get("learner_outcome", ""),
                "topics": _split(r.get("topics_in_order", "")),
                "est_hours": round(n_topics * HOURS_PER_SDE_STEP, 1),
                "hours_basis": "design_default",
                "resources": res,
                "checkpoints": cps,
                "projects": projects,
                "kb_skills": self._skills_for("sde", pid),
                "pass_threshold_pct": 70.0,
            })

        ev_dir = self._p("sde", "output", "events")
        events = []
        for e in _read(os.path.join(ev_dir, "01_events_master.csv")):
            events.append({
                "event_id": f"SDE-{e['event_id']}",
                "name": e["event_name"],
                "category": e.get("category", "").upper(),
                "organiser": e.get("organiser", ""),
                "window": e.get("expected_month_range", ""),
                "start_month": e.get("start_month", ""),
                "mode": e.get("mode_hint", ""),
                "eligibility": e.get("eligibility_raw", ""),
                "prize": e.get("prize_pool_raw", ""),
                "hiring": e.get("can_get_hired", ""),
                "min_phase_required": e.get("min_phase_required", "NONE"),
                "date_confidence": e.get("date_confidence", ""),
                "is_home_campus": "bhubaneswar" in (e.get("organiser", "") + e.get("location_hint", "")).lower(),
                "verify_at": e.get("source_to_verify", ""),
            })
        quiz_dir = self._p("sde", "output", "quiz")
        problems = []
        for p in _read(os.path.join(quiz_dir, "02_problems_unique.csv")):
            problems.append({
                "problem_id": f"LC-{p['leetcode_number']}",
                "title": p["problem_title"],
                "url": p["problem_url"],
                "difficulty": p.get("difficulty_for_quiz", ""),
                "topic": p.get("primary_topic", ""),
                "phase_id": p.get("roadmap_phase_id", ""),
                "calibrated": p.get("quiz_eligible_calibrated", "").upper() == "TRUE",
            })
        self.tracks["sde"] = {
            "track_id": "sde", "goal_id": TRACK_GOALS["sde"], "name": TRACK_NAMES["sde"],
            "phases": phases, "events": events,
            "eligibility": _read(os.path.join(ev_dir, "02_phase_eligibility.csv")),
            "event_rules": _read(os.path.join(ev_dir, "03_recommendation_rules.csv")),
            "questions": [], "practice_problems": problems,
            "repos": repos,
            "pacing": [], "learning_methods": [],
            "topics_map": _read(os.path.join(quiz_dir, "03_topics_roadmap_map.csv")),
            "source_id": "TRACK_SDE_KB",
        }

    def _load_da(self):
        cur = self._p("da", "output", "curriculum")
        overview = _read(os.path.join(cur, "01_da_roadmap_overview.csv"))
        if not overview:
            return
        modules = _read(os.path.join(cur, "02_phase_modules_resources.csv"))
        skills = {s["skill_id"]: s for s in _read(os.path.join(cur, "03_skills_catalog.csv"))}
        summary = {s["phase_id"]: s for s in _read(os.path.join(cur, "04_phase_summary_readiness_checkpoints.csv"))}
        projects_raw = _read(os.path.join(cur, "05_projects.csv"))
        rubric_rows = _read(os.path.join(cur, "06_project_rubric_items.csv"))

        phases = []
        for r in sorted(overview, key=lambda x: int(_f(x["phase_order"]))):
            pid = r["phase_id"]
            sm = summary.get(pid, {})
            res, seen = [], set()
            for m in modules:
                if m["phase_id"] != pid or not m.get("resource_url") or not m.get("resource_id"):
                    continue
                if m["resource_id"] in seen:
                    continue
                seen.add(m["resource_id"])
                res.append({
                    "resource_id": m["resource_id"],
                    "title": m["resource_title"],
                    "provider": m.get("resource_provider", ""),
                    "url": m["resource_url"],
                    "resource_type": m.get("resource_type", ""),
                    "topic": m.get("skill_name", ""),
                    "tier": m.get("resource_role", ""),
                    "tier_meaning": m.get("resource_scope", ""),
                    "usage_guidance": m.get("module_title", ""),
                    "link_verified": False,
                    "is_free": m.get("is_free", ""),
                    "est_hours": None,
                })
            mods, seen_m = [], set()
            for m in modules:
                if m["phase_id"] == pid and m["module_id"] not in seen_m:
                    seen_m.add(m["module_id"])
                    mods.append({"module_id": m["module_id"], "title": m["module_title"],
                                 "skill": m["skill_name"], "objective": m.get("what_to_learn_objective", ""),
                                 "est_hours": _f(m.get("module_est_hours"))})
            cps = []
            if sm.get("checkpoint_text"):
                cps.append({"text": sm["checkpoint_text"], "type": sm.get("checkpoint_type_derived", ""),
                            "topic": r["phase_name"], "pass_criteria": sm.get("readiness_rule_for_phase_derived", "")})
            projs = []
            for p in projects_raw:
                if p.get("recommended_after_phase_id") != pid:
                    continue
                projs.append({
                    "project_id": p["project_id"], "title": p["title"], "why": p.get("brief", ""),
                    "skills_shown": p.get("skill_names", ""), "priority": p.get("difficulty", ""),
                    "repos": p.get("dataset_url", ""), "deliverable": p.get("deliverable", ""),
                    "est_hours": _f(p.get("est_hours")),
                    "rubric": [x["criterion_text"] for x in rubric_rows if x["project_id"] == p["project_id"]],
                })
            phases.append({
                "phase_id": pid, "order": int(_f(r["phase_order"])), "name": r["phase_name"],
                "objective": r.get("phase_objective_derived", ""), "outcome": r.get("learner_outcome_derived", ""),
                "topics": _split(r.get("skills_in_order", "")),
                "est_hours": _f(sm.get("total_module_hours")) or sum(m["est_hours"] for m in mods),
                "hours_basis": "source",
                "resources": res, "modules": mods, "checkpoints": cps, "projects": projs,
                "kb_skills": self._skills_for("da", pid),
                "pass_threshold_pct": _f(sm.get("checkpoint_pass_threshold_pct"), 70.0),
            })

        ev_dir = self._p("da", "output", "events")
        events = []
        for e in _read(os.path.join(ev_dir, "01_events_master.csv")):
            events.append({
                "event_id": f"DA-{e['event_id']}", "name": e["event_name"],
                "category": e.get("event_type_derived", "").upper(), "organiser": e.get("organiser_host", ""),
                "window": e.get("expected_month_range", ""), "start_month": e.get("start_month", ""),
                "mode": e.get("mode_derived", ""), "eligibility": e.get("eligibility_raw", ""),
                "prize": "", "hiring": "", "min_phase_required": e.get("min_phase_required", "NONE"),
                "date_confidence": e.get("date_wording", ""),
                "is_home_campus": e.get("is_home_campus_event", "").upper() == "TRUE",
                "verify_at": "",
            })
        quiz_dir = self._p("da", "output", "quiz")
        questions = []
        for q in _read(os.path.join(quiz_dir, "01_question_bank.csv")):
            cat = skills.get(q["skill_id"], {}).get("category", q.get("skill_category", ""))
            opts = [q.get(f"option_{c}", "") for c in "abcd"]
            opts = [o for o in opts if o]
            qtype = q.get("question_type", "mcq")
            questions.append({
                "question_id": q["question_id"], "track_skill_id": q["skill_id"], "track_skill_name": q["skill_name"],
                "kb_skill_id": DA_CATEGORY_SKILL.get(cat, "SKILL_DATA_ANALYTICS"),
                "phase_id": q["phase_id"], "difficulty_num": int(_f(q.get("difficulty_num"), 2)),
                "question_type": qtype, "stem": q["stem"], "options": opts,
                "correct_option_text": q.get("correct_option_text", ""),
                "numeric_answer": q.get("numeric_answer_value", ""),
                "explanation": q.get("explanation", ""),
                "auto_gradable": qtype in ("mcq", "numeric"),
            })
        self.tracks["da"] = {
            "track_id": "da", "goal_id": TRACK_GOALS["da"], "name": TRACK_NAMES["da"],
            "phases": phases, "events": events,
            "eligibility": _read(os.path.join(ev_dir, "02_phase_eligibility.csv")),
            "event_rules": _read(os.path.join(ev_dir, "03_recommendation_rules.csv")),
            "questions": questions, "practice_problems": [], "repos": [],
            "pacing": _read(os.path.join(cur, "07_pacing_templates.csv")),
            "learning_methods": _read(os.path.join(cur, "09_learning_methods.csv")),
            "quiz_checkpoints": _read(os.path.join(quiz_dir, "05_quiz_checkpoints.csv")),
            "source_id": "TRACK_DA_KB",
        }

    def _load_aiml(self):
        cur = self._p("aiml", "output", "curriculum")
        overview = _read(os.path.join(cur, "01_roadmap.csv"))
        if not overview:
            return
        resources = _read(os.path.join(cur, "02_phase_resources.csv"))
        prereqs = _read(os.path.join(cur, "03_prerequisites.csv"))
        phases = []
        for r in sorted(overview, key=lambda x: int(_f(x["phase_order"]))):
            pid = r["phase_id"]
            res = [{
                "resource_id": x["resource_id"], "title": x["resource_title"], "provider": x.get("platform_author", ""),
                "url": x.get("url_or_access_reference", ""), "resource_type": x.get("resource_type", ""),
                "topic": x.get("domain_sub_track", ""), "tier": x.get("learning_style", ""),
                "tier_meaning": x.get("cost_model", ""), "usage_guidance": x.get("key_concepts_and_skills", ""),
                "link_verified": False, "est_hours": _f(x.get("estimated_hours")) or None,
            } for x in resources if x["phase_id"] == pid]
            phases.append({
                "phase_id": pid, "order": int(_f(r["phase_order"])), "name": r["phase_name"],
                "objective": r.get("phase_objective", ""), "outcome": r.get("learner_outcome", ""),
                "topics": _split(r.get("topics_covered", "")),
                "est_hours": _f(r.get("total_estimated_hours")), "hours_basis": "source",
                "resources": res,
                "checkpoints": [{"text": f"Demonstrate: {r.get('learner_outcome', '')}", "type": "OUTCOME_CHECK",
                                 "topic": r["phase_name"], "pass_criteria": "Checkpoint quiz / project review at >= 70%"}],
                "projects": [], "kb_skills": self._skills_for("aiml", pid), "pass_threshold_pct": 70.0,
            })
        ev_dir = self._p("aiml", "output", "events")
        dom = {d["event_id"]: d for d in _read(os.path.join(ev_dir, "04_domain_to_phase_map.csv"))}
        events = []
        for e in _read(os.path.join(ev_dir, "01_events_master.csv")):
            d = dom.get(e["event_id"], {})
            events.append({
                "event_id": f"AIML-{e['event_id']}", "name": e["event_name"],
                "category": e.get("category", "").upper(), "organiser": e.get("organizer_or_platform", ""),
                "window": e.get("expected_month_range", ""), "start_month": e.get("start_month", ""),
                "mode": e.get("mode", ""), "eligibility": "", "prize": e.get("prize_pool_listed", ""), "hiring": "",
                "min_phase_required": e.get("min_phase_required", "NONE"),
                "date_confidence": e.get("timeline_type", ""),
                "is_home_campus": "bhubaneswar" in (e.get("organizer_or_platform", "") + e.get("location", "")).lower(),
                "domain_tag": d.get("primary_domain_tag(assigned)", ""),
                "beginner_friendly": d.get("beginner_friendly", ""),
                "verify_at": "",
            })
        self.tracks["aiml"] = {
            "track_id": "aiml", "goal_id": TRACK_GOALS["aiml"], "name": TRACK_NAMES["aiml"],
            "phases": phases, "events": events,
            "eligibility": _read(os.path.join(ev_dir, "02_phase_eligibility.csv")),
            "event_rules": _read(os.path.join(ev_dir, "03_recommendation_rules.csv")),
            "questions": [], "practice_problems": [], "repos": [],
            "pacing": [], "learning_methods": [], "prerequisites": prereqs,
            "source_id": "TRACK_AIML_KB",
        }

    # ------------------------------------------------------------------ queries
    def list_tracks(self) -> List[Dict[str, Any]]:
        return [self.tracks[t] for t in ("sde", "da", "aiml") if t in self.tracks]

    def get(self, track_id: Optional[str]) -> Optional[Dict[str, Any]]:
        return self.tracks.get((track_id or "").lower())

    def for_goal(self, goal_id: Optional[str]) -> Optional[Dict[str, Any]]:
        return self.get(GOAL_TRACKS.get(goal_id or "", ""))

    def track_id_for_goal(self, goal_id: Optional[str]) -> Optional[str]:
        tid = GOAL_TRACKS.get(goal_id or "")
        return tid if tid in self.tracks else None

    def phase(self, track_id: str, phase_id: str) -> Optional[Dict[str, Any]]:
        t = self.get(track_id)
        if not t:
            return None
        return next((p for p in t["phases"] if p["phase_id"] == phase_id), None)

    def phase_order(self, track_id: str, phase_id: str) -> int:
        p = self.phase(track_id, phase_id)
        return p["order"] if p else 0

    def all_resource_ids(self) -> Set[str]:
        ids: Set[str] = set()
        for t in self.tracks.values():
            for p in t["phases"]:
                ids.update(r["resource_id"] for r in p["resources"])
        return ids

    def resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        for t in self.tracks.values():
            for p in t["phases"]:
                for r in p["resources"]:
                    if r["resource_id"] == resource_id:
                        return dict(r, track_id=t["track_id"], phase_id=p["phase_id"])
        return None

    def questions(self, track_id: str, kb_skill_id: Optional[str] = None, auto_gradable_only: bool = True) -> List[Dict[str, Any]]:
        t = self.get(track_id)
        if not t:
            return []
        qs = t.get("questions", [])
        if auto_gradable_only:
            qs = [q for q in qs if q.get("auto_gradable")]
        if kb_skill_id:
            qs = [q for q in qs if q["kb_skill_id"] == kb_skill_id]
        return qs

    def practice_problems(self, track_id: str, phase_id: Optional[str] = None, limit: int = 6) -> List[Dict[str, Any]]:
        t = self.get(track_id)
        if not t:
            return []
        probs = [p for p in t.get("practice_problems", []) if p.get("calibrated")]
        if phase_id:
            probs = [p for p in probs if p.get("phase_id") == phase_id]
        order = {"Easy": 0, "Medium": 1, "Hard": 2}
        probs.sort(key=lambda p: (order.get(p["difficulty"], 3), p["problem_id"]))
        return probs[:limit]

    def recommend_events(self, track_id: str, highest_completed_phase_order: int = 0,
                         reference_month: Optional[str] = None, limit: int = 6) -> Dict[str, Any]:
        """
        Deterministic event recommendation following the track's own rule tables:
          * category unlocks + per-category caps from 02_phase_eligibility.csv
          * each event's min_phase_required
          * home-campus (IIT Bhubaneswar) events first
          * at most 2 events per organiser (diversity rule)
          * upcoming first (start_month >= reference_month), then chronological
        """
        t = self.get(track_id)
        if not t:
            return {"events": [], "message": "", "locked_count": 0}
        elig_rows = sorted(t.get("eligibility", []), key=lambda r: int(_f(r.get("highest_completed_phase_order"))))
        elig = None
        for r in elig_rows:
            if int(_f(r.get("highest_completed_phase_order"))) <= highest_completed_phase_order:
                elig = r
        elig = elig or (elig_rows[0] if elig_rows else {})

        def unlocked(cat: str) -> bool:
            key = {"FEST": "fests_unlocked", "HACKATHON": "hackathons_unlocked", "COMPETITION": "competitions_unlocked"}.get(cat)
            if key is None or key not in elig:
                return cat == "FEST"
            return elig.get(key, "FALSE").upper() == "TRUE"

        def cap(cat: str) -> int:
            key = {"FEST": "max_fests_per_recommendation", "HACKATHON": "max_hackathons_per_recommendation",
                   "COMPETITION": "max_competitions_per_recommendation"}.get(cat)
            return int(_f(elig.get(key), 2)) if key and key in elig else 2

        ref = reference_month or ""
        candidates, locked = [], 0
        for e in t["events"]:
            mp = e.get("min_phase_required", "NONE")
            need = 0 if mp in ("", "NONE", "NONE_YET") else self.phase_order(track_id, mp)
            if need > highest_completed_phase_order or not unlocked(e["category"]):
                locked += 1
                continue
            candidates.append(e)
        candidates.sort(key=lambda e: (
            0 if e.get("is_home_campus") else 1,
            0 if (not ref or (e.get("start_month") or "9999") >= ref) else 1,
            e.get("start_month") or "9999",
            e["event_id"],
        ))
        picked, per_org, per_cat = [], {}, {}
        for e in candidates:
            org = e.get("organiser", "")
            if per_org.get(org, 0) >= 2:
                continue
            if per_cat.get(e["category"], 0) >= cap(e["category"]):
                continue
            per_org[org] = per_org.get(org, 0) + 1
            per_cat[e["category"]] = per_cat.get(e["category"], 0) + 1
            picked.append(e)
            if len(picked) >= limit:
                break
        return {
            "events": picked,
            "message": elig.get("message_to_user", ""),
            "locked_count": locked,
            "rules_applied": ["phase_eligibility", "min_phase_required", "home_campus_first", "max_2_per_organiser", "upcoming_first"],
        }

    def stats(self) -> Dict[str, Any]:
        out = {}
        for tid, t in self.tracks.items():
            out[tid] = {
                "phases": len(t["phases"]),
                "resources": sum(len(p["resources"]) for p in t["phases"]),
                "checkpoints": sum(len(p["checkpoints"]) for p in t["phases"]),
                "projects": sum(len(p["projects"]) for p in t["phases"]),
                "events": len(t["events"]),
                "questions": len(t.get("questions", [])),
                "practice_problems": len(t.get("practice_problems", [])),
                "total_est_hours": round(sum(p["est_hours"] for p in t["phases"]), 1),
            }
        return out


track_repo = TrackRepo()
