"""Recommendation engine pipeline for EBuddy Recommender.

Deterministic course recommendation based on credit budget, prerequisites,
parity offering, eligibility, and keyword/skill relevance scoring.
"""

import math
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

from app.recommender.credits import (
    core_courses,
    credit_limit,
    open_slot_info,
    parse_credit,
    semester_credit_total,
)
from app.recommender.kb import (
    get_academic_rules,
    get_course_offerings,
    get_course_prerequisites,
    get_courses,
    get_curriculum_table,
    get_primary_resource,
    get_slot_options,
    slot_branch,
    slot_semester,
)
from app.recommender.retrieval import intent_terms, score_courses

# Minimum relevance threshold for strong match
MIN_RELEVANCE: float = 0.2


def recommend(student: Dict[str, Any], query: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
    """Recommend validated courses for a student in a specific branch and semester.

    Pipeline:
    1. Determine intent: query text if present and containing topical terms; fallback to profile goal.
    2. Compute credit limit, core credits, headroom = limit - core_credits, and open slot budget.
    3. Determine completed courses (inferred from earlier semesters union explicit, minus backlogs).
    4. Find candidate courses from slot options matching branch and semester.
    5. Deterministically filter and reject invalid candidates (prerequisites, parity, credits, avoid list).
    6. Score survivors and rank with stable sort (tie-break by course_id).
    7. Retrieve future elective options from later semesters.
    """
    branch = str(student.get("branch", "EE")).strip().upper()
    semester = int(student.get("semester", 1))
    cgpa = float(student.get("cgpa", 8.0))
    overload_approved = bool(student.get("overload_approved", False))
    profile_goal = str(student.get("goal", "") or "").strip()

    # 1. Intent determination with fallback if query has no topic terms
    query_text = (query or "").strip()
    query_terms = intent_terms(query_text) if query_text else []
    query_had_topic = len(query_terms) > 0

    if query_had_topic:
        intent_source = "query"
        intent_text = query_text
        terms = query_terms
    elif profile_goal:
        intent_source = "profile_goal"
        intent_text = profile_goal
        terms = intent_terms(profile_goal)
    else:
        intent_source = "none"
        intent_text = ""
        terms = []

    # 2. Curriculum, core credits, headroom, and open slots
    curriculum_df = get_curriculum_table(branch)
    rules = get_academic_rules()
    sem_total = semester_credit_total(curriculum_df, semester)
    limit, rule_used = credit_limit(cgpa, sem_total, overload_approved, rules)

    cores = core_courses(curriculum_df, semester)
    core_credits_sum = sum(c["credits"] for c in cores if not math.isnan(c["credits"]))
    headroom = round(limit - core_credits_sum, 2)

    slot_info = open_slot_info(curriculum_df, semester)
    open_slots = slot_info["open_slots"]
    min_needed = slot_info["min_credits_needed"]
    max_needed = slot_info["max_credits_needed"]

    if open_slots == 0:
        slot_credit_status = "none"
    elif headroom < min_needed:
        slot_credit_status = "insufficient"
    elif headroom < max_needed:
        slot_credit_status = "tight"
    else:
        slot_credit_status = "sufficient"

    credit_budget = {
        "limit": limit,
        "rule": rule_used,
        "core_credits": core_credits_sum,
        "headroom": headroom,
        "core_courses": [c["course_id"] for c in cores],
        "open_slots": open_slots,
        "min_credits_needed": min_needed,
        "max_credits_needed": max_needed,
        "slot_credit_status": slot_credit_status,
    }

    # 3. Completed courses: inferred from all earlier semesters UNION explicit list MINUS backlogs
    inferred: Set[str] = set()
    for prev_sem in range(1, semester):
        for c in core_courses(curriculum_df, prev_sem):
            inferred.add(c["course_id"])
            if c.get("course_code"):
                inferred.add(c["course_code"])

    explicit: Set[str] = set(str(c).strip() for c in (student.get("completed") or []))
    backlogs: Set[str] = set(str(b).strip() for b in (student.get("backlogs") or []))

    completed = (inferred | explicit) - backlogs
    avoid_list: Set[str] = set(str(a).strip() for a in student.get("avoid", []))

    # 4. Candidates from slot options
    slot_df = get_slot_options()
    matching_slots: List[str] = []
    for _, row in slot_df.iterrows():
        s_id = str(row.get("slot_id", "") or "").strip()
        s_branch = slot_branch(s_id)
        s_sem = slot_semester(s_id)
        if s_branch == branch and s_sem == semester:
            matching_slots.append(str(row.get("course_id", "") or "").strip())

    # Preserve order and deduplicate
    candidate_ids: List[str] = list(dict.fromkeys([cid for cid in matching_slots if cid]))

    # Load lookup tables for filtering
    courses_df = get_courses()
    course_map = {row["course_id"]: row for _, row in courses_df.iterrows()}
    offerings_df = get_course_offerings()
    prereqs_df = get_course_prerequisites()

    semester_parity = "odd" if semester % 2 != 0 else "even"

    survivors: List[str] = []
    rejected: List[Dict[str, str]] = []

    # 5. Deterministic validation and rejection
    for cid in candidate_ids:
        c_info = course_map.get(cid)
        code = str(c_info.get("course_code", cid)) if c_info is not None else cid

        # Check if already completed
        if cid in completed or code in completed:
            rejected.append({"course_id": cid, "reason": "Already completed by student"})
            continue

        # Check avoid list
        if cid in avoid_list or code in avoid_list:
            rejected.append({"course_id": cid, "reason": "Course is in student's avoid list"})
            continue

        # Check if placeholder
        if c_info is not None and bool(c_info.get("is_placeholder", False)):
            rejected.append({"course_id": cid, "reason": "Course is marked as a placeholder"})
            continue

        # Check semester parity offering (only if rows exist for this course in course_offering.csv)
        course_offs = offerings_df[offerings_df["course_id"] == cid]
        if not course_offs.empty:
            parity_matches = course_offs[course_offs["parity"].str.lower() == semester_parity]
            if parity_matches.empty:
                offered_parities = ", ".join(course_offs["parity"].str.lower().unique())
                rejected.append({
                    "course_id": cid,
                    "reason": f"Not offered in {semester_parity} semester parity (only offered in: {offered_parities})",
                })
                continue

        # Check required prerequisites
        course_prs = prereqs_df[(prereqs_df["course_id"] == cid) & (prereqs_df["relation"].str.lower() == "required")]
        missing_prereqs: List[str] = []
        for _, pr_row in course_prs.iterrows():
            req_id = str(pr_row.get("prereq_id", "")).strip()
            if req_id and (req_id not in completed):
                missing_prereqs.append(req_id)

        if missing_prereqs:
            rejected.append({
                "course_id": cid,
                "reason": f"Missing required prerequisite(s): {', '.join(sorted(missing_prereqs))}",
            })
            continue

        # Check credits unknown or exceeding headroom
        c_credits = parse_credit(c_info.get("credits")) if c_info is not None else float("nan")
        if math.isnan(c_credits):
            rejected.append({"course_id": cid, "reason": "Course credits unknown (NaN)"})
            continue

        if c_credits > headroom:
            rejected.append({
                "course_id": cid,
                "reason": f"Credits ({c_credits}) exceed remaining credit headroom ({headroom})",
            })
            continue

        survivors.append(cid)

    # 6. Rank survivors
    scored_map = score_courses(survivors, terms)

    survivor_items: List[Dict[str, Any]] = []
    for cid in survivors:
        c_row = course_map.get(cid)
        sc_data = scored_map.get(cid, {"score": 0.0, "matched_skills": [], "matched_terms": []})
        c_credits = parse_credit(c_row.get("credits")) if c_row is not None else 3.0
        c_code = str(c_row.get("display_code", "") or c_row.get("course_code", cid)) if c_row is not None else cid
        c_title = str(c_row.get("title", "") or "") if c_row is not None else cid

        survivor_items.append({
            "course_id": cid,
            "course_code": c_code,
            "title": c_title,
            "credits": c_credits,
            "score": sc_data["score"],
            "matched_skills": sc_data["matched_skills"],
            "matched_terms": sc_data["matched_terms"],
            "primary_resource": get_primary_resource(cid),
        })

    # Stable sort: score descending, tie-break by course_id ascending
    survivor_items.sort(key=lambda x: (-x["score"], x["course_id"]))

    recommendations = survivor_items[:top_k]

    best_score = recommendations[0]["score"] if recommendations else 0.0
    no_direct_match = len(recommendations) == 0 or all(r["score"] == 0.0 for r in recommendations)
    weak_match = len(recommendations) == 0 or best_score < MIN_RELEVANCE

    # 7. Future options from later semesters' slots
    future_slot_candidates: List[Tuple[str, int]] = []
    for _, row in slot_df.iterrows():
        s_id = str(row.get("slot_id", "") or "").strip()
        s_b = slot_branch(s_id)
        s_sem = slot_semester(s_id)
        if s_b == branch and s_sem is not None and s_sem > semester:
            cid = str(row.get("course_id", "") or "").strip()
            if cid:
                future_slot_candidates.append((cid, s_sem))

    future_cids_map: Dict[str, int] = {}
    for cid, s_sem in future_slot_candidates:
        if cid not in future_cids_map or s_sem < future_cids_map[cid]:
            future_cids_map[cid] = s_sem

    future_valid_cids: List[str] = []
    for cid in future_cids_map:
        c_info = course_map.get(cid)
        code = str(c_info.get("course_code", cid)) if c_info is not None else cid
        if cid in completed or code in completed or cid in avoid_list or code in avoid_list:
            continue
        if c_info is not None and bool(c_info.get("is_placeholder", False)):
            continue
        future_valid_cids.append(cid)

    future_scored = score_courses(future_valid_cids, terms)
    future_items: List[Dict[str, Any]] = []
    for cid in future_valid_cids:
        c_row = course_map.get(cid)
        sc = future_scored.get(cid, {"score": 0.0, "matched_skills": [], "matched_terms": []})
        c_credits = parse_credit(c_row.get("credits")) if c_row is not None else 3.0
        c_code = str(c_row.get("display_code", "") or c_row.get("course_code", cid)) if c_row is not None else cid
        c_title = str(c_row.get("title", "") or "") if c_row is not None else cid

        # Find missing prerequisites against current student completed
        course_prs = prereqs_df[(prereqs_df["course_id"] == cid) & (prereqs_df["relation"].str.lower() == "required")]
        missing_pr = [
            str(r.get("prereq_id", "")).strip()
            for _, r in course_prs.iterrows()
            if str(r.get("prereq_id", "")).strip() and str(r.get("prereq_id", "")).strip() not in completed
        ]

        future_items.append({
            "course_id": cid,
            "course_code": c_code,
            "title": c_title,
            "credits": c_credits,
            "semester": future_cids_map[cid],
            "score": sc["score"],
            "matched_skills": sc["matched_skills"],
            "matched_terms": sc["matched_terms"],
            "missing_prerequisites": sorted(set(missing_pr)),
        })

    # Sort: score descending, then semester ascending, then course_id ascending
    future_items.sort(key=lambda x: (-x["score"], x["semester"], x["course_id"]))
    future_options = future_items[:3]

    return {
        "intent": {
            "source": intent_source,
            "text": intent_text,
            "terms": terms,
            "query_had_topic": query_had_topic,
        },
        "credit_budget": credit_budget,
        "no_direct_match": no_direct_match,
        "weak_match": weak_match,
        "recommendations": recommendations,
        "rejected": rejected,
        "future_options": future_options,
    }
