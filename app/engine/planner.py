"""
Deterministic Academic Planner Engine (no LLM, no network).

Principles
----------
1. Python decides curriculum, rules and schedule; the LLM only explains.
2. Mandatory branch courses come from kb.programme_requirement and are FIXED.
   Elective / lateral / breadth rows that carry a course_id are *options of a pool*,
   never mandatory courses (they are ranked, one per slot).
3. Elective slots are ranked with CourseRelevanceEngine (0-3) + evidence-weighted
   skill-gap boost + a small, clearly labelled self-declared-interest boost.
4. Evidence reliability is explicit: assessed evidence (grades, diagnostics, timed
   quizzes, rubric projects, mock interviews) is STRONG; self-declared interest is
   WEAK and can never by itself skip content or reach mastery.
5. Student-stated constraints (credit cap, weekly hours, avoid-course, not-together)
   are HARD. Unsourced institute baselines produce labelled warnings.
6. `horizon="semester"` plans the current semester (legacy behaviour);
   `horizon="degree"` plans every remaining semester up to Semester 8 and paces
   goal preparation (career-track phases, persona milestones) inside the weekly-hours cap.
"""
import os
import csv
import uuid
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timezone
from app.contracts.student import StudentProfile, Constraint, Preference, SkillState, EvidenceItem
from app.contracts.goal import Goal
from app.contracts.plan import Plan, PlanItem, StructuredReason
from app.engine.interfaces import IPlanner
from app.engine.rules import RuleEngine
from app.engine.relevance import CourseRelevanceEngine
from app.engine.skill_state import reliability_tier_for, TIER_WEIGHTS
from app.kb.repositories import ResourceRepo
from app.kb.track_repo import TrackRepo

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- design constants
# Design defaults (labelled as such in plan.horizon["assumptions"]; not institute rules).
SELF_STUDY_HOURS_PER_CREDIT = 0.5      # weekly self-study outside class per registered credit
PRACTICE_HOURS_PER_COURSE = 0.5        # weekly active practice per core/elective course
REMEDIATION_HOURS_WEEKLY = 2.0         # weekly hours for one remedial prerequisite block
DEFAULT_WEEKLY_HOURS = 20.0            # used only when the student states no weekly-hours cap
TEACHING_WEEKS_PER_SEMESTER = 16
INSTITUTE_REGULAR_CAP = 26.0           # RULE_SEM_CREDIT_CAP_REGULAR (unsourced_baseline)
INSTITUTE_PROBATION_CAP = 18.0         # RULE_SEM_CREDIT_CAP_PROBATION (unsourced_baseline)
FINAL_SEMESTER = 8
INTEREST_BOOST_MAX = 0.2               # weak-evidence boost ceiling (vs. up to +1.0 for assessed gaps)
STRONG_TEST_OUT_LEVEL = 85.0           # latest assessed score at which practice items are tested out
TEST_OUT_MIN_ESTIMATE = 70.0           # ...provided the overall evidence-weighted estimate is at least this
WEAK_REMEDIATION_LEVEL = 40.0          # assessed level below which remedial prerequisites are injected

OPTION_SLOT_TYPES = {"elective", "lateral", "breadth"}
NON_BREADTH_KINDS = {"P", "S", "D", "T"}   # labs, seminars, projects, training are not breadth candidates


def _norm_prog(raw: Optional[str]) -> str:
    p = (raw or "").upper().strip()
    if p in ("BTECH_MME", "MME", "MM"):
        return "BTECH_MM"
    if p in ("BTECH_EE", "EE"):
        return "BTECH_EE"
    return p


class Planner(IPlanner):
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self.rule_engine = RuleEngine(seed_dir)
        self.relevance_engine = CourseRelevanceEngine(seed_dir)
        self.resource_repo = ResourceRepo(seed_dir)
        self.track_repo = TrackRepo()
        self.course_skills: Dict[str, List[str]] = {}
        self.skill_courses: Dict[str, List[str]] = {}
        self.course_info: Dict[str, Dict[str, Any]] = {}
        self.prog_requirements: Dict[Tuple[str, int], List[Dict[str, Any]]] = {}
        self.slot_options: Dict[str, List[str]] = {}
        self.minor_courses: Dict[str, List[str]] = {}
        self.skill_names: Dict[str, str] = {}
        self.first_year_alternates: Dict[str, Set[str]] = {}
        self._load_knowledge_base()

    # ======================================================================= loading
    def _load_knowledge_base(self):
        self.course_skills.clear(); self.skill_courses.clear(); self.course_info.clear()
        self.prog_requirements.clear(); self.slot_options.clear(); self.minor_courses.clear()

        def rows(name: str) -> List[Dict[str, str]]:
            path = os.path.join(self.seed_dir, name)
            if not os.path.exists(path):
                return []
            with open(path, "r", encoding="utf-8") as f:
                return list(csv.DictReader(f))

        for r in rows("course_skill.csv"):
            cid, sid = r["course_id"].strip(), r["skill_id"].strip()
            self.course_skills.setdefault(cid, []).append(sid)
            self.skill_courses.setdefault(sid, []).append(cid)

        for r in rows("skill.csv"):
            self.skill_names[r["skill_id"]] = r.get("name", r["skill_id"])

        for r in rows("course.csv"):
            self.course_info[r["course_id"]] = {
                "credits": float(r.get("credits") or 4.0),
                "title": r.get("title", ""),
                "display_code": r.get("display_code", ""),
                "code_conflict": (r.get("code_conflict") or "false").lower() == "true",
                "status": r.get("status", "verified"),
                "department_id": r.get("department_id", ""),
            }

        for r in rows("programme_requirement.csv"):
            prog = r["programme_id"].strip().upper()
            try:
                sem = int(float(r["semester_number"]))
            except (ValueError, TypeError):
                continue
            self.prog_requirements.setdefault((prog, sem), []).append(r)

        for r in rows("slot_option.csv"):
            self.slot_options.setdefault(r["slot_id"].strip(), []).append(r["course_id"].strip())

        for r in rows("minor_course.csv"):
            self.minor_courses.setdefault(r["minor_id"].strip(), []).append(r["course_id"].strip())

        self._derive_first_year_requirements(rows("course_offering.csv"))

    def _derive_first_year_requirements(self, offerings: List[Dict[str, str]]):
        """
        The official semester table lists the first-year common core as "A / B" alternates
        (Track A takes the A-set in Sem I and the B-set in Sem II; Track B the reverse).
        kb.course_offering records that track for each common course (offering_basis =
        inferred_from_semester_table). Here the Track-A view is materialised as requirement
        rows for B.Tech EE so that Year-1 students get a complete, non-fabricated plan.

        For B.Tech MME the source document omits Sem I-II entirely. The same institute
        common core is offered with status `assumed_common_first_year`; it is used only to
        plan a Year-1 MME student's own first-year semesters (flagged in the plan) and is
        never used to infer completions or backlogs.
        """
        track_of: Dict[str, str] = {}
        for o in offerings:
            try:
                sem = int(o["semester_number"])
            except (ValueError, TypeError, KeyError):
                continue
            if sem in (1, 2) and o.get("track") in ("A", "B"):
                track_of[o["course_id"].strip()] = o["track"]
        if not track_of:
            return
        # HS1L001 / HS1L002 are alternates for one slot ("English for Communication or Learning English").
        self.first_year_alternates = {"HS1L001": {"HS1L002"}, "HS1L002": {"HS1L001"}}
        a_set = sorted(c for c, t in track_of.items() if t == "A" and c in self.course_info)
        b_set = sorted(c for c, t in track_of.items() if t == "B" and c in self.course_info and c != "HS1L002")
        self.fy_track_sets = {"A": set(a_set), "B": set(b_set) | {"HS1L002"}}

        def add(prog: str, sem: int, cid: str, fy_track: str, status: str, source: str):
            existing = {r.get("course_id", "").strip() for r in self.prog_requirements.get((prog, sem), [])}
            if cid in existing:
                return
            title = self.course_info[cid]["title"]
            kind = "laboratory" if (len(cid) > 3 and cid[3] == "P") else "common_core"
            self.prog_requirements.setdefault((prog, sem), []).append({
                "slot_id": f"REQ_FY_{prog[-2:]}_{cid}", "programme_id": prog, "semester_number": str(sem),
                "slot_name": title, "slot_type": kind, "min_credits": "", "max_credits": "", "option_pool": "",
                "course_id": cid, "course_type": "common core", "status": status, "source_id": source,
                "fy_track": fy_track, "derived_from": "kb.course_offering",
            })

        for cid in a_set:
            add("BTECH_EE", 1, cid, "A", "verified", "IITBBS_EE_CURRICULUM_2016_17")
        for cid in b_set:
            add("BTECH_EE", 2, cid, "B", "verified", "IITBBS_EE_CURRICULUM_2016_17")
        # MME: assumed institute common first year (source document has no Sem I-II table)
        for sem, cids, trk in ((1, ["MA1L001", "ID1T001"] + a_set, "A"), (2, ["MA1L002", "ID1T002"] + b_set, "B")):
            for cid in cids:
                if cid in self.course_info:
                    fy = trk if cid in track_of else "ALL"
                    add("BTECH_MM", sem, cid, fy, "assumed_common_first_year", "IITBBS_EE_CURRICULUM_2016_17")

    # ======================================================================= requirement helpers
    def requirement_rows(self, prog_id: str, sem: int, fy_track: str = "A") -> List[Dict[str, Any]]:
        """Requirement rows for a programme semester, with the first-year A/B track swap applied."""
        rows = list(self.prog_requirements.get((prog_id, sem), []))
        if sem in (1, 2) and (fy_track or "A").upper() == "B":
            other = self.prog_requirements.get((prog_id, 3 - sem), [])
            own_all = [r for r in rows if r.get("fy_track", "ALL") == "ALL" or "fy_track" not in r]
            swapped = [r for r in other if r.get("fy_track") in ("A", "B")]
            rows = own_all + swapped
        return rows

    @staticmethod
    def _is_mandatory_row(r: Dict[str, Any], include_assumed: bool = False) -> bool:
        if not (r.get("course_id") or "").strip():
            return False
        if (r.get("slot_type") or "").strip().lower() in OPTION_SLOT_TYPES:
            return False
        status = (r.get("status") or "verified").strip().lower()
        if status == "verified":
            return True
        return include_assumed and status == "assumed_common_first_year"

    def mandatory_courses(self, prog_id: str, sem: int, fy_track: str = "A", include_assumed: bool = False) -> List[Dict[str, Any]]:
        return [r for r in self.requirement_rows(prog_id, sem, fy_track) if self._is_mandatory_row(r, include_assumed)]

    def slot_rows(self, prog_id: str, sem: int) -> List[Dict[str, Any]]:
        return [r for r in self.prog_requirements.get((prog_id, sem), []) if not (r.get("course_id") or "").strip()]

    def programme_course_ids(self, prog_id: str) -> Set[str]:
        ids: Set[str] = set()
        for (p, _s), rws in self.prog_requirements.items():
            if p != prog_id:
                continue
            for r in rws:
                cid = (r.get("course_id") or "").strip()
                if cid:
                    ids.add(cid)
                else:
                    ids.update(self.slot_options.get(r.get("slot_id", "").strip(), []))
        return ids

    def _topological_sort_courses(self, course_ids: List[str]) -> List[str]:
        """Orders a batch so prerequisites precede dependents (stable, deterministic)."""
        c_set = set(course_ids)
        ordered: List[str] = []
        visited: Set[str] = set()

        def visit(c: str):
            if c in visited:
                return
            visited.add(c)
            for p in sorted(self.rule_engine.prereqs.get(c, set())):
                if p in c_set:
                    visit(p)
            ordered.append(c)

        for c in course_ids:
            visit(c)
        return ordered

    def _get_prereq_chain(self, course_id: str, visited: Optional[Set[str]] = None) -> List[str]:
        if visited is None:
            visited = set()
        chain: List[str] = []
        visited.add(course_id)
        for p in sorted(self.rule_engine.prereqs.get(course_id, set())):
            if p not in visited and p in self.course_info:
                chain.extend(self._get_prereq_chain(p, visited))
                chain.append(p)
        return chain

    def _dependents_of(self, course_id: str, universe: Set[str]) -> List[str]:
        return sorted(c for c in universe if course_id in self.rule_engine.prereqs.get(c, set()))

    # ======================================================================= evidence & mismatch
    def summarise_evidence(
        self,
        gaps: List[Dict[str, Any]],
        skill_states: Optional[List[SkillState]],
        evidence: Optional[List[EvidenceItem]],
        interests: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Evidence-weight ledger shown to the student: what the plan trusts, and how much."""
        states = {s.skill_id: s for s in (skill_states or [])}
        per_skill: Dict[str, Dict[str, Any]] = {}
        for ev in (evidence or []):
            tier = ev.reliability_tier or reliability_tier_for(ev.source_type)
            d = per_skill.setdefault(ev.skill_id, {"strong": 0, "medium": 0, "weak": 0, "sources": []})
            d[tier] += 1
            if ev.source_type not in d["sources"]:
                d["sources"].append(ev.source_type)
        rows = []
        for g in gaps:
            sid = g.get("skill_id")
            st = states.get(sid)
            d = per_skill.get(sid, {"strong": 0, "medium": 0, "weak": 0, "sources": []})
            if d["strong"] and d["weak"]:
                basis = "mixed"
            elif d["strong"] or d["medium"]:
                basis = "strong" if d["strong"] else "medium"
            elif d["weak"]:
                basis = "weak"
            else:
                basis = "strong" if (st and st.confidence > 0.2) else ("weak" if st else "none")
            rows.append({
                "skill_id": sid,
                "skill_name": self.skill_names.get(sid, sid),
                "target_level": g.get("target_level"),
                "estimated_level": st.estimated_level if st else None,
                "confidence": st.confidence if st else 0.0,
                "strong_evidence": d["strong"], "medium_evidence": d["medium"], "weak_evidence": d["weak"],
                "sources": d["sources"], "basis": basis,
                "planner_treatment": (
                    "No assessed evidence: full content kept" if basis in ("none", "weak")
                    else ("Tested out: practice shortened" if st and st.estimated_level >= STRONG_TEST_OUT_LEVEL
                          else ("Remedial prerequisites injected" if st and st.estimated_level < WEAK_REMEDIATION_LEVEL
                                else "Standard pacing"))
                ),
            })
        return {
            "tier_weights": dict(TIER_WEIGHTS),
            "rule": ("Assessed evidence (grades, diagnostics, timed quizzes, rubric projects, mock interviews) "
                     "is STRONG and drives skipping / remediation. Self-declared interest is WEAK: it can raise an "
                     f"elective's rank by at most +{INTEREST_BOOST_MAX} and is capped at level 40 in the skill state."),
            "skills": rows,
            "declared_interests": [
                {"topic": i.get("topic"), "weight": i.get("weight", 1.0), "reliability_tier": "weak"}
                for i in (interests or [])
            ],
        }

    def detect_interest_evidence_mismatch(
        self,
        student: StudentProfile,
        goal: Goal,
        states: List[SkillState],
        aims_text: Optional[str] = None,
        gaps: Optional[List[Dict[str, Any]]] = None,
        interests: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        state_map = {s.skill_id: s.estimated_level for s in states}
        conf_map = {s.skill_id: s.confidence for s in states}
        aims_lower = ((aims_text or "") + " " + goal.name + " " + goal.description).lower()

        # --- Legacy named rules (kept verbatim for traceability) ---------------------------------
        if any(kw in aims_lower for kw in ["power electronics", "smart grid", "power system", "power transmission", "relay", "converter", "ev drive", "hvdc"]):
            circ_level = state_map.get("SKILL_CIRCUIT_ANALYSIS", 100.0)
            if circ_level < 75.0:
                return {
                    "mismatch_detected": True,
                    "severity": "clash" if circ_level < 50.0 else "foundation_gap",
                    "target_interest": "Power Electronics & Energy Systems",
                    "missing_prerequisite": "SKILL_CIRCUIT_ANALYSIS",
                    "current_level": circ_level,
                    "required_level": 75.0,
                    "interest_evidence": "weak (self-declared)",
                    "skill_evidence": "strong (assessed)",
                    "explanation": (
                        f"Interest vs. Evidence Mismatch Detected: You expressed strong ambition in Power Electronics & Energy Systems, "
                        f"but verified diagnostic evidence indicates your proficiency in Circuit Analysis is {circ_level:.1f}% (required: 75.0%). "
                        f"Circuit analysis theorems (KVL/KCL, Thevenin equivalent, AC steady-state and transient response) are strictly required "
                        f"before designing converter topologies. To safeguard your GPA and ensure genuine competence, your study roadmap has "
                        f"automatically prioritized Circuit Analysis foundations in Phase 1 before advancing to converter design."
                    ),
                    "tradeoff": "Prioritized prerequisite Circuit Analysis remediation over premature advanced converter modeling."
                }

        if any(kw in aims_lower for kw in ["high-entropy alloy", "aerospace titanium", "biomaterials", "superalloys", "nanomaterials", "corrosion"]):
            metal_level = state_map.get("SKILL_PHYSICAL_METALLURGY", 100.0)
            thermo_level = state_map.get("SKILL_THERMODYNAMICS_MAT", state_map.get("SKILL_THERMODYNAMICS", 100.0))
            if metal_level < 70.0 or thermo_level < 70.0:
                weak_skill = "SKILL_PHYSICAL_METALLURGY" if metal_level < 70.0 else "SKILL_THERMODYNAMICS_MAT"
                val = metal_level if metal_level < 70.0 else thermo_level
                return {
                    "mismatch_detected": True,
                    "severity": "clash" if val < 50.0 else "foundation_gap",
                    "target_interest": "Advanced Structural Alloys & High-Entropy Materials",
                    "missing_prerequisite": weak_skill,
                    "current_level": val,
                    "required_level": 70.0,
                    "interest_evidence": "weak (self-declared)",
                    "skill_evidence": "strong (assessed)",
                    "explanation": (
                        f"Interest vs. Evidence Mismatch Detected: You have ambitious research aspirations in Advanced Materials Design, "
                        f"but diagnostic evidence shows foundational gaps in {weak_skill} ({val:.1f}% vs required 70.0%). "
                        f"Thermodynamic phase equilibria and dislocation theory are vital before attempting advanced multicomponent alloy formulation."
                    ),
                    "tradeoff": f"Scheduled foundational remediation in {weak_skill} prior to specialized alloy synthesis electives."
                }

        # --- General rule: declared goal/interest (WEAK) vs assessed skill level (STRONG) ----------
        candidates: List[Tuple[float, float, str, float]] = []
        for g in (gaps or []):
            sid = g.get("skill_id")
            if sid not in state_map or conf_map.get(sid, 0.0) <= 0.2:
                continue  # no assessed evidence -> unknown, not a mismatch
            level = state_map[sid]
            target = float(g.get("target_level") or 85.0)
            threshold = min(target, 75.0)
            if level < threshold and float(g.get("gap", 1.0) or 0.0) > 0:
                candidates.append((level, -float(g.get("importance", 1.0) or 1.0), sid, threshold))
        if not candidates:
            return None
        candidates.sort()
        level, _neg_imp, sid, threshold = candidates[0]
        name = self.skill_names.get(sid, sid.replace("SKILL_", "").replace("_", " ").title())
        declared = ", ".join(str(i.get("topic")) for i in (interests or [])[:3]) or (aims_text or goal.name)
        severity = "clash" if level < 50.0 else "foundation_gap"
        return {
            "mismatch_detected": True,
            "severity": severity,
            "target_interest": goal.name,
            "missing_prerequisite": sid,
            "current_level": level,
            "required_level": threshold,
            "interest_evidence": "weak (self-declared)",
            "skill_evidence": "strong (assessed)",
            "explanation": (
                f"Interest vs. Evidence Mismatch Detected: you declared a strong interest in {declared} "
                f"(self-declared = weak evidence, weight {TIER_WEIGHTS['weak']}), but assessed evidence "
                f"(strong, weight {TIER_WEIGHTS['strong']}) puts {name} at {level:.1f}% against the {threshold:.0f}% "
                f"this goal needs. The plan therefore follows the assessed evidence: it schedules a foundation block in "
                f"{name} first and keeps the goal itself unchanged."
            ),
            "tradeoff": f"Scheduled foundational remediation in {name} before advanced work towards {goal.name}."
        }

    def calculate_adaptive_phase_weeks(self, gaps: List[Dict[str, Any]], skill_states: Optional[List[SkillState]] = None) -> Dict[str, str]:
        if skill_states:
            avg_score = sum(s.estimated_level for s in skill_states) / len(skill_states)
        else:
            avg_gap = sum(g.get("gap", 0) for g in gaps) / (len(gaps) or 1)
            avg_score = max(30.0, 100.0 - avg_gap)

        if avg_score >= 80.0:
            return {
                "phase_1": "Phase 1: Foundation (Weeks 1–2 Accelerated)",
                "phase_2": "Phase 2: Core Depth (Weeks 3–8)",
                "phase_3": "Phase 3: Applied Mastery (Weeks 9–16)"
            }
        elif avg_score < 60.0:
            return {
                "phase_1": "Phase 1: Foundation (Weeks 1–6 Extended Remediation)",
                "phase_2": "Phase 2: Core Depth (Weeks 7–12)",
                "phase_3": "Phase 3: Applied Mastery (Weeks 13–16+)"
            }
        else:
            return {
                "phase_1": "Phase 1: Foundation (Weeks 1–4)",
                "phase_2": "Phase 2: Core Depth (Weeks 5–10)",
                "phase_3": "Phase 3: Applied Mastery (Weeks 11–16)"
            }

    # ======================================================================= constraints
    @staticmethod
    def parse_constraints(constraints: Optional[List[Constraint]]) -> Dict[str, Any]:
        out: Dict[str, Any] = {"credit_cap": None, "headroom": 0.0, "weekly_hours": None,
                               "avoid": set(), "not_together": []}
        for c in (constraints or []):
            if not getattr(c, "is_active", True):
                continue
            ctype = (getattr(c, "constraint_type", "") or "").lower()
            params = getattr(c, "parameters", {}) or {}
            if ctype in ("credit_cap", "max_credits", "max_credits_per_sem"):
                val = params.get("max_credits") or params.get("credit_cap") or params.get("credits") or params.get("value")
                if val is not None:
                    out["credit_cap"] = float(val)
            elif ctype == "headroom":
                val = params.get("headroom") or params.get("credit_headroom") or params.get("value")
                if val is not None:
                    out["headroom"] = float(val)
            elif ctype in ("weekly_hours", "max_weekly_hours", "study_hours", "weekly_study_hours", "max_hours_per_week"):
                val = params.get("max_hours") or params.get("weekly_hours") or params.get("hours") or params.get("value")
                if val is not None:
                    out["weekly_hours"] = float(val)
            elif ctype in ("avoid_course", "avoid_courses"):
                cid = params.get("course_id") or params.get("course")
                if cid:
                    out["avoid"].add(str(cid).strip())
                cids = params.get("courses") or params.get("course_ids")
                if isinstance(cids, list):
                    out["avoid"].update(str(x).strip() for x in cids)
            elif ctype in ("not_together", "mutually_exclusive"):
                pair = params.get("courses") or params.get("course_ids") or params.get("pair")
                if isinstance(pair, list):
                    out["not_together"].append({str(x).strip() for x in pair})
        return out

    # ======================================================================= main entry
    def generate_plan(
        self,
        student: StudentProfile,
        goal: Goal,
        gaps: List[Dict[str, Any]],
        constraints: List[Constraint],
        preferences: List[Preference],
        completed_course_ids: Optional[List[str]] = None,
        skill_states: Optional[List[SkillState]] = None,
        aims_text: Optional[str] = None,
        version: int = 1,
        horizon: str = "semester",
        evidence: Optional[List[EvidenceItem]] = None,
        interests: Optional[List[Dict[str, Any]]] = None,
    ) -> Plan:
        items: List[PlanItem] = []
        proposals: List[Dict[str, Any]] = []
        advisories: List[str] = []
        completed_set = set(completed_course_ids or [])
        current_sem = student.current_semester
        prog_id = _norm_prog(student.programme_id)
        fy_track = (getattr(student, "first_year_track", "A") or "A").upper()
        # The transcript is stronger evidence of the first-year track than the profile default:
        # a Sem-2 student who already passed the B-set took Track B in Sem 1.
        if current_sem == 2 and completed_set and getattr(self, "fy_track_sets", None):
            a_done = len(completed_set & self.fy_track_sets["A"])
            b_done = len(completed_set & self.fy_track_sets["B"])
            if a_done != b_done:
                fy_track = "A" if a_done > b_done else "B"
        multi = (horizon == "degree")

        # ---- Transcript inference (unchanged semantics): a student with zero backlogs has cleared
        #      every mandatory course of earlier semesters even if the transcript list is sparse.
        if (completed_course_ids is None or student.backlogs == 0) and current_sem > 1:
            for s in range(1, current_sem):
                for r in self.requirement_rows(prog_id, s, fy_track):
                    c = (r.get("course_id") or "").strip()
                    if c and (r.get("status") or "verified") != "assumed_common_first_year":
                        completed_set.add(c)
            if prog_id == "BTECH_EE" and current_sem >= 3:
                # legacy sparse transcripts: the first-year foundation is behind a Year-2+ student with no backlog
                completed_set.update(["MA1L001", "MA1L002", "EE1L001", "CS1L001"])
        assigned: Set[str] = set(completed_set)

        cons = self.parse_constraints(constraints)
        avoid_courses: Set[str] = cons["avoid"]
        not_together_pairs: List[Set[str]] = cons["not_together"]
        student_cap: Optional[float] = None
        if cons["credit_cap"] is not None:
            student_cap = cons["credit_cap"] - cons["headroom"]
        elif cons["headroom"] > 0.0:
            student_cap = INSTITUTE_REGULAR_CAP - cons["headroom"]
        weekly_cap: Optional[float] = cons["weekly_hours"]

        on_probation = (student.cgpa is not None and student.cgpa < 6.0)
        institute_cap = INSTITUTE_PROBATION_CAP if on_probation else INSTITUTE_REGULAR_CAP
        institute_rule = "RULE_SEM_CREDIT_CAP_PROBATION" if on_probation else "RULE_SEM_CREDIT_CAP_REGULAR"

        state_map = {s.skill_id: s for s in (skill_states or [])}
        conflicted_skills = {g["skill_id"] for g in gaps if g.get("conflict_flag")}
        plan_conflict_flag = "HIGH_INTEREST_LOW_FOUNDATION: Remedial bridge required" if conflicted_skills else None

        phase_labels = self.calculate_adaptive_phase_weeks(gaps, skill_states)
        p1_label, p2_label, p3_label = phase_labels["phase_1"], phase_labels["phase_2"], phase_labels["phase_3"]

        mismatch = self.detect_interest_evidence_mismatch(
            student=student, goal=goal, states=skill_states or [], aims_text=aims_text, gaps=gaps, interests=interests
        )

        def assessed_level(sid: str) -> Optional[float]:
            st = state_map.get(sid)
            if st is None or st.confidence <= 0.2:
                return None
            return st.estimated_level

        def latest_score(sid: str) -> Optional[float]:
            st = state_map.get(sid)
            if st is None or st.confidence <= 0.2:
                return None
            return st.latest_assessed_score if st.latest_assessed_score is not None else st.estimated_level

        # Test-out: latest assessed score >= 85 AND overall estimate >= 70 (one lucky result is not enough).
        # Remediation: latest assessed score < 40 OR overall assessed estimate < 40.
        tested_out_skills = {
            sid for sid in state_map
            if (latest_score(sid) or 0.0) >= STRONG_TEST_OUT_LEVEL and (assessed_level(sid) or 0.0) >= TEST_OUT_MIN_ESTIMATE
        }
        weak_skills = sorted(
            sid for sid in state_map
            if assessed_level(sid) is not None
            and (assessed_level(sid) < WEAK_REMEDIATION_LEVEL or (latest_score(sid) or 100.0) < WEAK_REMEDIATION_LEVEL)
        )
        gap_skill_ids = {g.get("skill_id") for g in gaps}

        def title_of(cid: Optional[str]) -> Optional[str]:
            return self.course_info.get(cid, {}).get("title") if cid else None

        def credits_of(cid: str, default: float = 4.0) -> float:
            return float(self.course_info.get(cid, {}).get("credits", default))

        def note_proposal(prefix: str, cid: str, reason: str, status: str = "pending_student_approval", extra: Optional[Dict[str, Any]] = None):
            pid = f"PROP_{prefix}_{cid}"
            if any(p.get("proposal_id") == pid for p in proposals):
                return
            d = {"proposal_id": pid, "course_id": cid, "title": title_of(cid) or cid,
                 "credits": credits_of(cid, 3.0), "reason": reason, "status": status}
            if extra:
                d.update(extra)
            proposals.append(d)

        # ------------------------------------------------------------------ remediation (current semester)
        def remediation_course_for(skill_id: str) -> Optional[str]:
            if "CIRCUIT" in skill_id and "EE2L001" in self.course_info:
                return "EE2L001"
            cands = sorted(self.skill_courses.get(skill_id, []))
            own = self.programme_course_ids(prog_id)
            done = [c for c in cands if c in completed_set]
            if done:
                return done[0]
            mine = [c for c in cands if c in own]
            if mine:
                return mine[0]
            if cands:
                return cands[0]
            return "ML2L002" if prog_id == "BTECH_MM" and "ML2L002" in self.course_info else None

        remediated: Set[str] = set()

        def add_remediation(skill_id: str, why: str, intent: str):
            if skill_id in remediated:
                return
            remediated.add(skill_id)
            rcid = remediation_course_for(skill_id)
            res = self.resource_repo.get_primary_resource_for_course(rcid) if rcid else None
            items.append(PlanItem(
                item_id=f"ITEM_REM_PREREQ_{skill_id}_S{current_sem}",
                item_type="remediation",
                course_id=rcid,
                resource_id=res.resource_id if res else None,
                url=res.url if res else None,
                title=f"Remedial foundation: {self.skill_names.get(skill_id, skill_id)}" + (f" (revise {rcid} {title_of(rcid)})" if rcid else ""),
                semester_number=current_sem,
                estimated_hours=4.0,
                phase=p1_label,
                prep_hours_weekly=REMEDIATION_HOURS_WEEKLY,
                planning_status="current",
                reason=StructuredReason(
                    intent=intent,
                    target_skills=[skill_id],
                    why_this=why,
                    prerequisite_for=[goal.name],
                    rule_compliance=["Academic load managed; prerequisite gap resolved before advanced topics",
                                     "Evidence basis: assessed (strong) evidence"]
                )
            ))

        if mismatch:
            ms = mismatch["missing_prerequisite"]
            add_remediation(ms, mismatch["explanation"], f"[{p1_label}] Address Interest vs. Evidence Gap in {ms}")
        for sid in weak_skills:
            if sid in gap_skill_ids or not gaps:
                lvl = min(assessed_level(sid), latest_score(sid) if latest_score(sid) is not None else 100.0)
                add_remediation(
                    sid,
                    (f"REMEDIAL PREREQUISITE INJECTED: assessed evidence puts {self.skill_names.get(sid, sid)} at {lvl:.1f}% "
                     f"(< {WEAK_REMEDIATION_LEVEL:.0f}%). A foundation block is scheduled first; advanced items that depend on it keep "
                     f"their place but are paced after this block."),
                    f"[{p1_label}] Weak assessed result: remedial prerequisite for {sid}",
                )

        # ------------------------------------------------------------------ semester loop
        semesters = list(range(current_sem, FINAL_SEMESTER + 1)) if multi else [current_sem]
        sem_credits: Dict[int, float] = {}
        carry_over: List[str] = []          # mandatory courses deferred by the student's hard credit cap
        deferred_log: List[Dict[str, Any]] = []
        prog_ids_all = self.programme_course_ids(prog_id)
        future_mandatory: Set[str] = set()
        for s in range(current_sem, FINAL_SEMESTER + 1):
            future_mandatory.update((r.get("course_id") or "").strip() for r in self.mandatory_courses(prog_id, s, fy_track, include_assumed=True))
        minor_id = "MINOR_DS" if goal.goal_id in ("GOAL_TRACK_DA", "GOAL_TRACK_AIML") and "MINOR_DS" in self.minor_courses else "MINOR_CSE"
        minor_done = 0
        minor_pool = {c for cs in self.minor_courses.values() for c in cs}
        gaps_dict = {g["skill_id"]: float(g.get("gap", 0.0) or 0.0) for g in gaps if g.get("skill_id")}

        def interest_boost(cid: str) -> Tuple[float, Optional[str]]:
            if not interests:
                return 0.0, None
            text = (title_of(cid) or "").lower() + " " + " ".join(self.skill_names.get(s, s).lower() for s in self.course_skills.get(cid, []))
            best, best_topic = 0.0, None
            for it in interests:
                topic = str(it.get("topic", "")).lower()
                toks = [t for t in topic.replace("&", " ").replace("/", " ").split() if len(t) > 3]
                if toks and any(t in text for t in toks):
                    w = min(1.0, float(it.get("weight", 1.0) or 1.0)) * INTEREST_BOOST_MAX
                    if w > best:
                        best, best_topic = w, str(it.get("topic"))
            return round(best, 2), best_topic

        for sem in semesters:
            is_current = (sem == current_sem)
            status = "current" if is_current else "planned"
            ph_core = p1_label if is_current else f"Semester {sem} (planned core)"
            ph_elec = p2_label if is_current else f"Semester {sem} (planned electives)"
            credits = 0.0
            sem_course_ids: List[str] = []

            def add_course(cid: str, item_prefix: str, intent: str, why: str, compliance: List[str],
                           phase: str, prereq_for: Optional[List[str]] = None, with_practice: bool = True):
                nonlocal credits
                cr = credits_of(cid)
                credits += cr
                assigned.add(cid)
                sem_course_ids.append(cid)
                skills = self.course_skills.get(cid, [])
                items.append(PlanItem(
                    item_id=f"ITEM_{item_prefix}_{cid}_S{sem}",
                    item_type="course", course_id=cid, title=title_of(cid), credits=cr,
                    semester_number=sem, estimated_hours=4.0, phase=phase,
                    prep_hours_weekly=round(cr * SELF_STUDY_HOURS_PER_CREDIT, 1),
                    planning_status=status,
                    reason=StructuredReason(intent=intent, target_skills=skills, why_this=why,
                                            prerequisite_for=prereq_for or [], rule_compliance=compliance)
                ))
                if with_practice:
                    tested = bool(skills) and all(s in tested_out_skills for s in skills)
                    if tested:
                        return  # strong assessed evidence: practice set tested out (plan shortened)
                    items.append(PlanItem(
                        item_id=f"ITEM_EX_{cid}_S{sem}",
                        item_type="exercise", course_id=cid, title=f"Practice set: {title_of(cid) or cid}",
                        semester_number=sem, estimated_hours=2.0, phase=phase,
                        prep_hours_weekly=PRACTICE_HOURS_PER_COURSE, planning_status=status,
                        reason=StructuredReason(
                            intent=f"{'Core Course' if item_prefix in ('CORE', 'BACKLOG', 'PREREQ') else 'Elective'} Practice: {cid}",
                            target_skills=skills,
                            why_this=f"Active problem solving and concept mastery for {'core' if item_prefix != 'ELEC' else 'elective'} course {cid}.",
                            prerequisite_for=[], rule_compliance=[])
                    ))

            def fits_student_cap(cr: float) -> bool:
                return student_cap is None or (credits + cr) <= student_cap + 1e-9

            def schedule_missing_prereqs(dependent_cid: str):
                """Uncleared prerequisites of a mandatory course are cleared first (deepest first)."""
                for pid in self._get_prereq_chain(dependent_cid):
                    if pid in assigned:
                        continue
                    p_title = title_of(pid) or pid
                    add_course(
                        pid, "PREREQ", f"Prerequisite Clearance for {dependent_cid}",
                        f"PREREQUISITE NOT CLEARED: {pid} ({p_title}) is required before {dependent_cid} and has not been completed. Scheduled ahead of {dependent_cid}.",
                        ["Satisfies prerequisite chain"], ph_core, prereq_for=[dependent_cid])

            # ---------------- PHASE 0: backlog clearance (current semester only) ----------------
            if is_current and current_sem > 1 and student.backlogs > 0:
                for s in range(1, current_sem):
                    for r in self.mandatory_courses(prog_id, s, fy_track):
                        c = (r.get("course_id") or "").strip()
                        if not c or c in assigned:
                            continue
                        if any(alt in completed_set for alt in self.first_year_alternates.get(c, ())):
                            continue
                        schedule_missing_prereqs(c)
                        if c in assigned:
                            continue
                        deps = self._dependents_of(c, future_mandatory)
                        add_course(
                            c, "BACKLOG", "Backlog Core Clearance Prioritized",
                            (f"PRIORITIZED BACKLOG: Mandatory core course {c} ({title_of(c) or c}) from Semester {s} was uncompleted. "
                             f"Prioritized for clearance before advanced electives"
                             + (f"; it also unlocks {', '.join(deps)}." if deps else ".")
                             + " Re-registration is subject to the course being offered this semester - confirm with the Academic Section."),
                            ["Academic standing rule: Prioritize uncompleted core backlog courses"],
                            ph_core, prereq_for=deps)

            # ---------------- PHASE A: mandatory courses (+ carry-over from capped semesters) ----------------
            include_assumed = (sem <= 2)
            raw_core: List[str] = list(carry_over)
            carry_over = []
            core_rows: Dict[str, Dict[str, Any]] = {}
            for r in self.mandatory_courses(prog_id, sem, fy_track, include_assumed=include_assumed):
                cid = (r.get("course_id") or "").strip()
                if cid in assigned or cid in raw_core:
                    continue
                if any(alt in assigned for alt in self.first_year_alternates.get(cid, ())):
                    continue
                raw_core.append(cid)
                core_rows[cid] = r

            for cid in self._topological_sort_courses(raw_core):
                if cid in assigned:
                    continue
                cr = credits_of(cid)
                # a course whose prerequisite was just deferred must wait with it (never ahead of its prerequisite)
                blocked = any(pq in carry_over for pq in self._get_prereq_chain(cid))
                if multi and (blocked or not fits_student_cap(cr)) and sem < FINAL_SEMESTER:
                    # Student's own credit cap is HARD: defer the mandatory course instead of breaching it.
                    carry_over.append(cid)
                    deferred_log.append({"course_id": cid, "from_semester": sem, "credits": cr})
                    continue
                schedule_missing_prereqs(cid)
                if cid in assigned:
                    continue
                req_row = core_rows.get(cid, {})
                slot_name = req_row.get("slot_name", "Core Degree Course")
                rel_score, rel_rationale = self.relevance_engine.get_relevance(cid, goal.goal_id)
                c_title = title_of(cid) or cid
                why = f"Mandatory major/core requirement for {prog_id} Semester {sem} ({slot_name}: {c_title})."
                compliance = ["Mandatory branch curriculum requirement", "Fixed core selection"]
                if rel_score > 0:
                    why += f" Contributes foundational competencies to {goal.name} (Relevance {rel_score}/3: {rel_rationale})."
                if (req_row.get("status") or "") == "assumed_common_first_year":
                    why += (" [ASSUMED: institute common first-year core taken from the EE curriculum document; the MME document "
                            "omits Sem I-II - confirm with the Academic Section.]")
                    compliance.append("[WARNING: draft_for_review] First-year common core assumed for MME (source gap)")
                if any(d["course_id"] == cid for d in deferred_log):
                    origin = next(d["from_semester"] for d in deferred_log if d["course_id"] == cid)
                    why += f" Deferred from Semester {origin} to respect your stated credit limit of {student_cap:.1f}."
                    compliance.append("Deferred to honour student-stated credit cap (hard constraint)")
                c_skills = self.course_skills.get(cid, [])
                if any(s in conflicted_skills for s in c_skills):
                    why += " [CONFLICT: Interest vs Evidence] Student has high interest/aspiration, but diagnostic evidence indicates foundational gaps (<40). Scheduled foundational bridge before advanced coursework."
                add_course(cid, "CORE", f"Branch Core Degree Requirement ({prog_id})", why, compliance, ph_core)

            # ---------------- PHASE B: elective slots ----------------
            for r in self.slot_rows(prog_id, sem):
                slot_id = (r.get("slot_id") or "").strip()
                slot_type = (r.get("slot_type") or "elective").strip().lower()
                slot_name = r.get("slot_name", slot_id)
                breadth_note = ""
                is_breadth_slot = False
                candidates = list(self.slot_options.get(slot_id, []))
                if not candidates:
                    if "breadth" in slot_type or "breadth" in slot_id.lower():
                        is_breadth_slot = True
                        candidates = sorted(
                            c for c in self.course_info
                            if c not in assigned and not c.startswith(prog_id[-2:])
                            and (c not in prog_ids_all or c in minor_pool)
                            and len(c) > 3 and c[2].isdigit() and int(c[2]) >= 2
                            and c[3] not in NON_BREADTH_KINDS
                        )
                        breadth_note = (" [NOTE: the institute breadth pool is not enumerated in the source curriculum; "
                                        "candidate drawn from other-department catalogue courses - confirm availability with the Academic Section.]")
                    else:
                        candidates = [c for g in gaps for c in self.skill_courses.get(g["skill_id"], []) if c not in assigned]

                allowed: List[str] = []
                for c in candidates:
                    if c in avoid_courses:
                        note_proposal("AVOID", c, "Matches student-stated avoid constraint. Placed in optional proposal requiring student approval.")
                        continue
                    if any(c in pair and any(x in assigned for x in (pair - {c})) for pair in not_together_pairs):
                        note_proposal("NOT_TOGETHER", c, "Conflicts with student-stated not-together constraint. Placed in optional proposal requiring student approval.")
                        continue
                    allowed.append(c)

                ranked = self.relevance_engine.rank_electives(
                    candidate_course_ids=allowed, goal_id=goal.goal_id, skill_gaps=gaps,
                    completed_course_ids=list(assigned), prereq_map=self.rule_engine.prereqs)
                if interests and ranked:
                    for rk in ranked:
                        b, topic = interest_boost(rk["course_id"])
                        rk["interest_boost"], rk["interest_topic"] = b, topic
                        rk["total_rank"] = round(rk["total_rank"] + b, 2)
                    ranked.sort(key=lambda d: (-d["total_rank"], -d["base_relevance"], d["course_id"]))
                if is_breadth_slot and (not ranked or ranked[0]["base_relevance"] < 2):
                    # The source curriculum does not enumerate the breadth pool and no catalogue course outside the
                    # student's department is clearly relevant to the goal: keep the slot OPEN instead of guessing a course.
                    slot_cr = float(r.get("min_credits") or 3.0)
                    if student_cap is not None and (credits + slot_cr > student_cap + 1e-9):
                        proposals.append({"proposal_id": f"PROP_OVERLOAD_{slot_id}", "course_id": None, "title": slot_name, "credits": slot_cr,
                                          "reason": (f"Exceeds student-stated credit limit ({student_cap:.1f} credits). Total would be {credits + slot_cr:.1f} credits. "
                                                     f"Placed in optional proposal requiring student approval."),
                                          "status": "pending_student_approval", "semester_number": sem, "slot_id": slot_id})
                        continue
                    credits += slot_cr
                    hint = ", ".join(f"{x['course_id']} ({x['base_relevance']}/3)" for x in ranked[:3] if x["base_relevance"] >= 1)
                    items.append(PlanItem(
                        item_id=f"ITEM_SLOT_{slot_id}_S{sem}", item_type="course", course_id=None,
                        title=f"{slot_name} (open slot - choose from the institute breadth pool)", credits=slot_cr,
                        semester_number=sem, estimated_hours=4.0, phase=ph_elec,
                        prep_hours_weekly=round(slot_cr * SELF_STUDY_HOURS_PER_CREDIT, 1), planning_status=status,
                        reason=StructuredReason(
                            intent=f"Open Breadth Slot ({slot_name})", target_skills=[],
                            why_this=(f"{slot_name} is a degree requirement of {slot_cr:.0f} credits. The institute breadth pool is not enumerated "
                                      f"in the source curriculum, and no other-department course in the knowledge base is clearly relevant to "
                                      f"{goal.name}, so no specific course is recommended (nothing is guessed). Credits are reserved in your load."
                                      + (f" Loosely related catalogue options: {hint}." if hint else "")
                                      + " Confirm the offered pool with the Academic Section."),
                            prerequisite_for=[], rule_compliance=["Degree slot credits reserved", "[WARNING: draft_for_review] Breadth pool not in source data"])))
                    continue
                if not ranked:
                    continue
                top = ranked[0]
                ecid = top["course_id"]
                ecr = credits_of(ecid, 3.0)
                if student_cap is not None and (credits + ecr > student_cap + 1e-9):
                    note_proposal(
                        "OVERLOAD", ecid,
                        f"Exceeds student-stated credit limit ({student_cap:.1f} credits). Total would be {credits + ecr:.1f} credits. Placed in optional proposal requiring student approval.",
                        extra={"semester_number": sem, "slot_id": slot_id})
                    continue
                exceeds = (credits + ecr > institute_cap)
                gap_part = max(0.0, round(top["total_rank"] - top["base_relevance"] - top.get("interest_boost", 0.0), 2))
                why = (f"Selected for slot {slot_id} based on career relevance to {goal.name} (Score: {top['base_relevance']}/3: {top['rationale']} "
                       f"[Status: {top.get('status', 'draft_for_review')}, Source: {top.get('source_id', 'DESIGN_TEAM')}]) and skill gap alignment.")
                if gap_part > 0:
                    why += f" Assessed skill-gap boost +{gap_part} (strong evidence)."
                if top.get("interest_boost"):
                    why += f" Interest boost +{top['interest_boost']} for '{top['interest_topic']}' (self-declared, weak evidence)."
                if len(ranked) > 1:
                    why += f" Next best option: {ranked[1]['course_id']} (rank {ranked[1]['total_rank']})."
                why += breadth_note
                comp = ["Prerequisites verified satisfied", "Complies with curriculum slot options"]
                if exceeds:
                    why += f" [WARNING: unsourced_baseline] Total semester credits exceed {institute_cap:.1f} baseline credit cap."
                    comp.append(f"[WARNING: unsourced_baseline] Exceeds {institute_cap:.1f} baseline credit cap ({institute_rule})")
                add_course(ecid, "ELEC", f"Recommended Elective ({slot_name})", why, comp, ph_elec)

            # ---------------- PHASE C: minor (optional, eligibility gated) ----------------
            if sem >= 5:
                minor_candidates = [c for c in self.minor_courses.get(minor_id, []) if c not in assigned]
                for c in list(minor_candidates):
                    if c in avoid_courses:
                        note_proposal("AVOID", c, "Matches student-stated avoid constraint. Placed in optional proposal requiring student approval.")
                        minor_candidates.remove(c)
                eligible = self.rule_engine.check_minor_eligibility(student)
                if minor_candidates and eligible and (is_current or minor_done < 6):
                    ranked_minor = self.relevance_engine.rank_electives(
                        candidate_course_ids=minor_candidates, goal_id=goal.goal_id, skill_gaps=gaps,
                        completed_course_ids=list(assigned), prereq_map=self.rule_engine.prereqs)
                    if ranked_minor:
                        tm = ranked_minor[0]
                        mcid = tm["course_id"]
                        mcr = credits_of(mcid, 3.0)
                        if any(mcid in pair and any(x in assigned for x in (pair - {mcid})) for pair in not_together_pairs):
                            note_proposal("NOT_TOGETHER", mcid, "Conflicts with student-stated not-together constraint. Placed in optional proposal requiring student approval.")
                        elif student_cap is not None and (credits + mcr > student_cap + 1e-9):
                            note_proposal(
                                "OVERLOAD", mcid,
                                f"Exceeds student-stated credit limit ({student_cap:.1f} credits). Total would be {credits + mcr:.1f} credits. Placed in optional proposal requiring student approval.",
                                extra={"semester_number": sem})
                        elif (not is_current) and (credits + mcr > institute_cap):
                            pass  # future semesters: do not plan an optional minor course beyond the baseline cap
                        else:
                            exceeds = (credits + mcr > institute_cap)
                            m_why = (f"Student satisfies minor eligibility (Sem {student.current_semester} >= 5, CGPA {student.cgpa} >= 8.0). "
                                     f"Course {mcid} selected for CSE/DS Minor to accelerate {goal.name} (Relevance {tm['base_relevance']}/3: {tm['rationale']} "
                                     f"[Status: {tm.get('status', 'draft_for_review')}]).")
                            m_comp = ["Satisfies minor eligibility rules [draft_for_review data]"]
                            if exceeds:
                                m_why += f" [WARNING: unsourced_baseline] Total semester credits exceed {institute_cap:.1f} baseline credit cap."
                                m_comp.append(f"[WARNING: unsourced_baseline] Exceeds {institute_cap:.1f} baseline credit cap ({institute_rule})")
                            add_course(mcid, "MIN", "Approved Minor Course Track", m_why, m_comp, ph_elec, with_practice=False)
                            minor_done += 1
                elif minor_candidates and not eligible and is_current:
                    cg = f"{student.cgpa:.2f}" if student.cgpa is not None else "not provided"
                    proposals.append({
                        "proposal_id": "PROP_MINOR_INELIGIBLE",
                        "reason": (f"Student CGPA ({cg}) is below the required 8.00 cutoff or has active backlogs ({student.backlogs}). "
                                   f"Ineligible for Minor in Computer Science per academic regulations."
                                   + (f" You are {8.0 - student.cgpa:.2f} grade points short of the cutoff; the minor is re-evaluated automatically if your CGPA is updated."
                                      if student.cgpa is not None and student.backlogs == 0 and student.cgpa < 8.0 else "")),
                        "status": "ineligible_explanation"
                    })

            sem_credits[sem] = round(credits, 1)
            if multi and sem == FINAL_SEMESTER and carry_over:
                for cid in carry_over:
                    note_proposal(
                        "BEYOND_HORIZON", cid,
                        (f"Mandatory course {cid} cannot be placed by Semester {FINAL_SEMESTER} within your stated credit limit of {student_cap:.1f}. "
                         f"Raise the cap for one semester or discuss an extended timeline with your Faculty Advisor."),
                        status="unachievable_explanation")

        # Fallback for programmes with no curriculum rows at all: plan from skill gaps
        if not any(self.prog_requirements.get((prog_id, s)) for s in range(1, FINAL_SEMESTER + 1)):
            for g in gaps:
                if g.get("gap", 0) <= 0:
                    continue
                sid = g["skill_id"]
                for cid in self.skill_courses.get(sid, []):
                    if cid in assigned:
                        continue
                    for pid in self._get_prereq_chain(cid):
                        if pid not in assigned:
                            assigned.add(pid)
                            items.append(PlanItem(
                                item_id=f"ITEM_C_{pid}_S{current_sem}", item_type="course", course_id=pid, title=title_of(pid),
                                semester_number=current_sem, estimated_hours=4.0,
                                reason=StructuredReason(intent=f"Prerequisite foundation for {cid}",
                                                        target_skills=self.course_skills.get(pid, [sid]),
                                                        why_this=f"Required prerequisite foundation before taking {cid}.",
                                                        prerequisite_for=[cid], rule_compliance=["Satisfies prerequisite chain"])))
                    assigned.add(cid)
                    items.append(PlanItem(
                        item_id=f"ITEM_C_{cid}_S{current_sem}", item_type="course", course_id=cid, title=title_of(cid),
                        semester_number=current_sem, estimated_hours=4.0,
                        reason=StructuredReason(intent=f"Close gap in {sid}", target_skills=[sid],
                                                why_this=f"Addresses priority gap ({g['gap']} points) in {sid} required for {goal.name}.",
                                                prerequisite_for=[], rule_compliance=["Complies with offering and credit limits"])))
                    break

        if deferred_log:
            advisories.append(
                f"Your stated credit limit of {student_cap:.1f} is below the mandatory load in "
                f"{len({d['from_semester'] for d in deferred_log})} semester(s); {len(deferred_log)} mandatory course(s) were moved to later "
                f"semesters instead of breaching the limit.")

        # ------------------------------------------------------------------ goal preparation layer
        track = self.track_repo.for_goal(goal.goal_id)
        track_summary: Optional[Dict[str, Any]] = None
        if track:
            track_summary = self._plan_track(track, goal, student, items, sem_credits, weekly_cap,
                                             state_map, semesters, multi, advisories, gaps)

        # Open courseware for goal skills with no course coverage in the plan
        for g in gaps:
            sid = g.get("skill_id")
            courses_for_sid = self.skill_courses.get(sid, [])
            if not courses_for_sid or not any(c in assigned for c in courses_for_sid):
                for r_obj in self.resource_repo.get_resources_for_skill(sid):
                    items.append(PlanItem(
                        item_id=f"ITEM_RES_{r_obj.resource_id}_S{current_sem}", item_type="resource",
                        resource_id=r_obj.resource_id, title=r_obj.title, url=r_obj.url,
                        semester_number=current_sem, estimated_hours=3.0, phase=p2_label, prep_hours_weekly=1.0,
                        planning_status="current",
                        reason=StructuredReason(
                            intent=f"Open Courseware Resource: {sid}", target_skills=[sid],
                            why_this=f"Addresses competency requirement in {sid} using verified open courseware ({r_obj.title}, Provider: {r_obj.provider}) as no departmental course exists in the institute curriculum.",
                            prerequisite_for=[], rule_compliance=["Self-paced open resource study"])))

        if goal.goal_id == "GOAL_UPSC_COMPETITIVE":
            items.append(PlanItem(
                item_id=f"ITEM_MS_UPSC_GS_S{current_sem}", item_type="milestone", title="UPSC General Studies preparation",
                semester_number=current_sem, estimated_hours=8.0, phase=p2_label, prep_hours_weekly=2.0, planning_status="current",
                reason=StructuredReason(
                    intent="UPSC General Studies Preparation",
                    target_skills=["SKILL_RESEARCH_WRITING", "SKILL_ENGINEERING_MATH"],
                    why_this="The institutional course catalogue contains zero General Studies (GS) coverage (History, Polity, Economy, Geography, Ethics). UPSC Civil Services preparation must be pursued via structured roadmap milestones and open educational resources alongside degree requirements.",
                    prerequisite_for=[], rule_compliance=["Non-curricular competitive exam preparation"])))

        items.append(PlanItem(
            item_id=f"ITEM_MS_SEM_TARGET_S{current_sem}", item_type="milestone", title=f"Semester {current_sem} target milestone",
            semester_number=current_sem, estimated_hours=0.0, phase=p3_label, prep_hours_weekly=0.5, planning_status="current",
            reason=StructuredReason(
                intent="Semester Target Milestone",
                target_skills=[g["skill_id"] for g in gaps if g.get("gap", 0) > 0] if gaps else [],
                why_this=f"Core milestone for goal {goal.name}.", prerequisite_for=[], rule_compliance=[])))

        # ------------------------------------------------------------------ persona hooks
        persona_pkg = None
        try:
            from app.personas.registry import persona_registry
            persona_pkg = persona_registry.for_goal(goal.goal_id)
            if persona_pkg is not None:
                if getattr(persona_pkg.policy, "enable_plan_adjustment", False):
                    items = persona_pkg.policy.adjust_plan_items(student, items, gaps=gaps)
                try:
                    advisories.extend(persona_pkg.policy.get_advisories(student) or [])
                except Exception:  # advisories are best-effort
                    logger.debug("persona advisories unavailable", exc_info=True)
                if multi:
                    items = self._add_persona_milestones(persona_pkg, goal, student, items, current_sem)
        except Exception as e:
            logger.error("Error adjusting plan items for persona '%s' (goal '%s'): %s",
                         persona_pkg.spec.persona_id if persona_pkg is not None else "unknown", goal.goal_id, e, exc_info=True)

        # ------------------------------------------------------------------ weekly-hours budget (HARD)
        budget = self._apply_weekly_budget(items, current_sem, weekly_cap, advisories)
        items = budget.pop("items")

        horizon_info: Dict[str, Any] = {
            "mode": "degree" if multi else "semester",
            "semesters_planned": semesters,
            "credits_by_semester": {str(k): v for k, v in sem_credits.items()},
            "student_credit_cap": student_cap,
            "institute_credit_cap": institute_cap,
            "institute_credit_cap_rule": institute_rule,
            "weekly_hours_cap": weekly_cap,
            "weekly_budget": budget,
            "deferred_mandatory": deferred_log,
            "track": track_summary,
            "tested_out_skills": sorted(tested_out_skills & (gap_skill_ids or tested_out_skills)),
            "remediated_skills": sorted(remediated),
            "assumptions": {
                "self_study_hours_per_credit": SELF_STUDY_HOURS_PER_CREDIT,
                "practice_hours_per_course": PRACTICE_HOURS_PER_COURSE,
                "teaching_weeks_per_semester": TEACHING_WEEKS_PER_SEMESTER,
                "status": "design_default (not an institute rule)",
            },
        }

        return Plan(
            plan_id=f"PLAN_{student.student_id}_{uuid.uuid4().hex[:8]}",
            student_id=student.student_id,
            goal_id=goal.goal_id,
            version=version,
            items=items,
            conflict_flag=plan_conflict_flag,
            optional_overload_proposals=proposals,
            mismatch_warning=mismatch,
            evidence_summary=self.summarise_evidence(gaps, skill_states, evidence, interests),
            horizon=horizon_info,
            advisories=list(dict.fromkeys(a for a in advisories if a)),
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )

    create_plan = generate_plan

    # ======================================================================= career-track pacing
    def track_phase_status(self, track: Dict[str, Any], state_map: Dict[str, SkillState]) -> List[Dict[str, Any]]:
        """A phase is `demonstrated` only on assessed evidence for every mapped skill (never on self-declaration)."""
        out = []
        blocked = False
        for ph in track["phases"]:
            reqs = ph.get("kb_skills", [])
            met, detail = bool(reqs), []
            for r in reqs:
                st = state_map.get(r["skill_id"])
                lvl = st.estimated_level if (st and st.confidence > 0.2) else None
                ok = lvl is not None and lvl >= r["required_level"]
                detail.append({"skill_id": r["skill_id"], "required_level": r["required_level"], "assessed_level": lvl, "met": ok})
                met = met and ok
            if met and not blocked:
                status = "demonstrated"
            else:
                status = "in_progress" if not blocked else "upcoming"
                blocked = True
            out.append({"phase_id": ph["phase_id"], "order": ph["order"], "name": ph["name"], "status": status, "skills": detail})
        return out

    def _plan_track(self, track, goal, student, items, sem_credits, weekly_cap, state_map, semesters, multi, advisories, gaps) -> Dict[str, Any]:
        tid = track["track_id"]
        statuses = self.track_phase_status(track, state_map)
        status_by_id = {s["phase_id"]: s for s in statuses}
        pending = [ph for ph in track["phases"] if status_by_id[ph["phase_id"]]["status"] != "demonstrated"]
        done = [ph for ph in track["phases"] if status_by_id[ph["phase_id"]]["status"] == "demonstrated"]
        cap = weekly_cap if weekly_cap is not None else DEFAULT_WEEKLY_HOURS
        current_sem = student.current_semester

        def goal_hours(sem: int) -> float:
            academic = sem_credits.get(sem, 0.0) * SELF_STUDY_HOURS_PER_CREDIT
            return max(0.0, round(cap - academic, 1))

        schedule: List[Dict[str, Any]] = []
        if multi:
            idx, remaining = 0, (pending[0]["est_hours"] if pending else 0.0)
            start_sem = semesters[0] if semesters else current_sem
            for sem in semesters:
                avail = goal_hours(sem) * TEACHING_WEEKS_PER_SEMESTER
                while idx < len(pending) and avail > 0:
                    use = min(avail, remaining)
                    avail -= use
                    remaining -= use
                    if remaining <= 1e-6:
                        schedule.append({"phase": pending[idx], "start": start_sem, "end": sem, "status": "planned"})
                        idx += 1
                        start_sem = sem
                        remaining = pending[idx]["est_hours"] if idx < len(pending) else 0.0
                    else:
                        break
            left_hours = remaining + sum(p["est_hours"] for p in pending[idx + 1:]) if idx < len(pending) else 0.0
            for ph in pending[idx:]:
                schedule.append({"phase": ph, "start": None, "end": None, "status": "beyond_horizon"})
            if idx < len(pending):
                weeks_left = max(1, len(semesters)) * TEACHING_WEEKS_PER_SEMESTER
                total_pending = sum(p["est_hours"] for p in pending)
                need = round(total_pending / weeks_left + sum(sem_credits.get(s, 0.0) for s in semesters) / max(1, len(semesters)) * SELF_STUDY_HOURS_PER_CREDIT, 1)
                advisories.append(
                    f"Honest pacing note: at your weekly cap of {cap:.0f} h, {len(pending) - idx} of {len(pending)} remaining "
                    f"{track['name']} phase(s) (~{left_hours:.0f} h) do not fit before Semester {FINAL_SEMESTER}. Reaching the full roadmap in "
                    f"term time would need about {need:.0f} h/week, or use of semester breaks (not counted in this plan).")
        else:
            if pending:
                schedule.append({"phase": pending[0], "start": current_sem, "end": current_sem, "status": "current"})

        for sc in schedule:
            ph = sc["phase"]
            beyond = sc["status"] == "beyond_horizon"
            sem = sc["end"] if not beyond else FINAL_SEMESTER
            is_now = (not beyond) and sc["start"] == current_sem
            skills = [s["skill_id"] for s in ph.get("kb_skills", [])]
            span = (f"Semester {sc['start']}" if sc["start"] == sc["end"] else f"Semesters {sc['start']}-{sc['end']}") if not beyond else "after graduation / breaks"
            phase_label = f"Track Phase {ph['order']}: {ph['name']}"
            cp = ph["checkpoints"][0]["text"] if ph.get("checkpoints") else "Phase checkpoint at >= 70%"
            hours_note = "" if ph.get("hours_basis") == "source" else " (hours are a design default; not stated in the source roadmap)"
            items.append(PlanItem(
                item_id=f"ITEM_TRACK_{tid.upper()}_{ph['phase_id']}",
                item_type="milestone", title=f"{track['name']} - {phase_label}",
                track_id=tid, track_phase_id=ph["phase_id"], semester_number=sem,
                estimated_hours=float(ph["est_hours"]), phase=phase_label,
                planning_status="beyond_horizon" if beyond else ("current" if is_now else "planned"),
                reason=StructuredReason(
                    intent=f"Career Track Phase ({track['name']})",
                    target_skills=skills,
                    why_this=(f"{ph.get('objective') or ph['name']} Estimated {ph['est_hours']:.0f} h{hours_note}; paced for {span} "
                              f"inside your weekly-hours cap after degree coursework. Demonstrate with: {cp}."),
                    prerequisite_for=[p["name"] for p in track["phases"] if p["order"] == ph["order"] + 1],
                    rule_compliance=["Non-credit career preparation; never displaces mandatory degree courses",
                                     "Completion requires assessed evidence (checkpoint), not self-declaration"])))
            if beyond or not (is_now or not multi):
                continue
            # Current phase: one starting resource (KB link) and one active-practice item
            res = next((r for r in ph["resources"] if (r.get("tier") or "") in ("A", "primary", "Code-First")), None) or (ph["resources"][0] if ph["resources"] else None)
            if res:
                items.append(PlanItem(
                    item_id=f"ITEM_TRACKRES_{res['resource_id']}", item_type="resource", resource_id=res["resource_id"],
                    title=res["title"], url=res.get("url"), track_id=tid, track_phase_id=ph["phase_id"],
                    semester_number=current_sem, estimated_hours=float(res.get("est_hours") or 6.0), phase=phase_label,
                    planning_status="current",
                    reason=StructuredReason(
                        intent=f"Track Learning Resource: {res.get('topic') or ph['name']}",
                        target_skills=skills,
                        why_this=(f"Start-here resource for {ph['name']} from the {track['name']} knowledge base "
                                  f"({res.get('provider') or 'source not stated'}). Link not yet health-checked (link_verified=false)."),
                        prerequisite_for=[], rule_compliance=["Resource row exists in the track knowledge base"])))
            items.append(PlanItem(
                item_id=f"ITEM_TRACKEX_{tid.upper()}_{ph['phase_id']}", item_type="exercise",
                title=f"Checkpoint practice: {ph['name']}", track_id=tid, track_phase_id=ph["phase_id"],
                semester_number=current_sem, estimated_hours=4.0, phase=phase_label, planning_status="current",
                reason=StructuredReason(
                    intent=f"Active practice for {ph['name']}",
                    target_skills=skills,
                    why_this=f"Timed practice towards the phase checkpoint: {cp}.",
                    prerequisite_for=[], rule_compliance=[])))

        # Goal skills not mapped to any pending phase still need an explicit item (covered-or-explained rule)
        covered = {s for it in items for s in it.reason.target_skills}
        for g in gaps:
            sid = g.get("skill_id")
            if sid and sid not in covered and float(g.get("gap", 0) or 0) > 0:
                items.append(PlanItem(
                    item_id=f"ITEM_TRACKGAP_{tid.upper()}_{sid}", item_type="exercise",
                    title=f"Skill check: {self.skill_names.get(sid, sid)}", track_id=tid,
                    semester_number=current_sem, estimated_hours=2.0, phase=f"Track: {track['name']}", planning_status="current",
                    reason=StructuredReason(intent=f"Active practice for {sid}", target_skills=[sid],
                                            why_this=f"Goal skill {sid} has an open gap of {g.get('gap')} and is checked with a short timed quiz.",
                                            prerequisite_for=[], rule_compliance=[])))
                covered.add(sid)

        return {
            "track_id": tid, "track_name": track["name"],
            "phase_status": statuses,
            "demonstrated_phases": [p["phase_id"] for p in done],
            "highest_completed_phase_order": max([p["order"] for p in done], default=0),
            "schedule": [{"phase_id": s["phase"]["phase_id"], "name": s["phase"]["name"], "est_hours": s["phase"]["est_hours"],
                          "start_semester": s["start"], "end_semester": s["end"], "status": s["status"]} for s in schedule],
            "weekly_goal_hours_by_semester": {str(s): goal_hours(s) for s in semesters},
        }

    # ======================================================================= persona milestones
    def _add_persona_milestones(self, pkg, goal, student, items: List[PlanItem], current_sem: int) -> List[PlanItem]:
        out = list(items)
        existing = {it.item_id for it in out}
        for i, m in enumerate(pkg.milestones or []):
            if not isinstance(m, dict) or not m.get("title"):
                continue
            target = int(m.get("semester_target") or current_sem)
            late = target < current_sem
            sem = max(target, current_sem)
            if sem > FINAL_SEMESTER:
                continue
            iid = f"ITEM_PMS_{pkg.spec.persona_id}_{i:02d}"
            if iid in existing:
                continue
            why = str(m.get("description", "")).strip()
            if late:
                why += f" [Catch-up: originally targeted for Semester {target}; you joined this goal later, so it is scheduled now.]"
            out.append(PlanItem(
                item_id=iid, item_type="milestone", title=str(m["title"]), semester_number=sem,
                estimated_hours=0.0, phase=f"Goal Roadmap - Semester {sem}",
                planning_status="current" if sem == current_sem else "planned",
                reason=StructuredReason(
                    intent=f"Goal Milestone ({pkg.spec.persona_id})", target_skills=[],
                    why_this=why or f"Roadmap milestone for {goal.name}.",
                    prerequisite_for=[], rule_compliance=["Persona roadmap milestone [draft_for_review]"])))
        return out

    # ======================================================================= weekly budget
    def _apply_weekly_budget(self, items: List[PlanItem], current_sem: int, weekly_cap: Optional[float], advisories: List[str]) -> Dict[str, Any]:
        """
        Fits the CURRENT semester's weekly self-study into the student's weekly-hours cap (hard).
        Priority: mandatory academics > remediation > practice > goal preparation.
        """
        def is_now(it: PlanItem) -> bool:
            return (it.semester_number or current_sem) == current_sem and (it.planning_status in (None, "current"))

        academic = [it for it in items if is_now(it) and it.item_type == "course"]
        remed = [it for it in items if is_now(it) and it.item_type == "remediation"]
        practice = [it for it in items if is_now(it) and it.item_type == "exercise" and not it.track_id and (it.course_id or "").strip()]
        goal_prep = [it for it in items if is_now(it) and it not in academic and it not in remed and it not in practice]

        for it in academic:
            if it.prep_hours_weekly is None:
                object.__setattr__(it, "prep_hours_weekly", round((it.credits or 4.0) * SELF_STUDY_HOURS_PER_CREDIT, 1))
        need_academic = sum(it.prep_hours_weekly or 0.0 for it in academic)
        need_remed = sum(it.prep_hours_weekly or REMEDIATION_HOURS_WEEKLY for it in remed)
        need_practice = sum(it.prep_hours_weekly or PRACTICE_HOURS_PER_COURSE for it in practice)
        cap = weekly_cap if weekly_cap is not None else None

        scale_acad = scale_rem = scale_prac = 1.0
        if cap is not None:
            left = cap
            if need_academic > left and need_academic > 0:
                scale_acad = left / need_academic
            left = max(0.0, left - need_academic * scale_acad)
            if need_remed > left and need_remed > 0:
                scale_rem = left / need_remed
            left = max(0.0, left - need_remed * scale_rem)
            if need_practice > left and need_practice > 0:
                scale_prac = left / need_practice
            left = max(0.0, left - need_practice * scale_prac)
            goal_pool = left
        else:
            goal_pool = max(0.0, DEFAULT_WEEKLY_HOURS - need_academic - need_remed - need_practice)

        def scaled(it: PlanItem, base: float, scale: float) -> float:
            return int(base * scale * 10) / 10.0  # floor to 0.1 h so the total never exceeds the cap

        new_hours: Dict[str, float] = {}
        for it in academic:
            new_hours[it.item_id] = scaled(it, it.prep_hours_weekly or 0.0, scale_acad)
        for it in remed:
            new_hours[it.item_id] = scaled(it, it.prep_hours_weekly or REMEDIATION_HOURS_WEEKLY, scale_rem)
        for it in practice:
            new_hours[it.item_id] = scaled(it, it.prep_hours_weekly or PRACTICE_HOURS_PER_COURSE, scale_prac)
        if goal_prep:
            per = int((goal_pool / len(goal_prep)) * 10) / 10.0
            for it in goal_prep:
                new_hours[it.item_id] = per

        out_items: List[PlanItem] = []
        for it in items:
            if it.item_id in new_hours and is_now(it):
                out_items.append(it.model_copy(update={"prep_hours_weekly": new_hours[it.item_id]}))
            else:
                out_items.append(it)

        total = round(sum(new_hours.values()), 1)
        compressed = (scale_acad < 1.0 or scale_rem < 1.0 or scale_prac < 1.0)
        if cap is not None and compressed:
            advisories.append(
                f"Tight weekly-hours cap: recommended self-study for this semester is "
                f"{need_academic + need_remed + need_practice:.1f} h/week but you stated {cap:.1f} h/week. Mandatory courses are kept "
                f"(they cannot be dropped); hours were compressed to fit your cap and goal preparation is deferred to semester breaks. "
                f"Consider raising the cap or reducing an optional course.")
        elif cap is not None and goal_prep and goal_pool < 2.0:
            advisories.append(
                f"After degree coursework only {goal_pool:.1f} h/week remain for goal preparation inside your {cap:.1f} h cap; "
                f"goal milestones are paced slowly and semester breaks are recommended for catch-up.")
        return {
            "items": out_items,
            "cap_hours": cap,
            "recommended_hours": round(need_academic + need_remed + need_practice, 1),
            "allocated_hours": total,
            "academic_hours": round(sum(new_hours[it.item_id] for it in academic), 1),
            "remediation_hours": round(sum(new_hours[it.item_id] for it in remed), 1),
            "practice_hours": round(sum(new_hours[it.item_id] for it in practice), 1),
            "goal_prep_hours": round(sum(new_hours[it.item_id] for it in goal_prep), 1),
            "compressed": compressed,
            "within_cap": (cap is None) or (total <= cap + 1e-6),
        }
