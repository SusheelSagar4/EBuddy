"""Explanation generation and hallucination guard for EBuddy Recommender.

Wraps LLM calls via app.llm.client.llm_client, enforces strict system prompt rules,
and provides a clean, deterministic template fallback on failure, timeout, or hallucination.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.llm.client import llm_client

logger = logging.getLogger("ebuddy.recommender.explain")

COURSE_CODE_PATTERN = re.compile(r"\b([A-Z]{2}\d[A-Z]\d{3})\b")


def format_resource_string(primary_res: Optional[Dict[str, str]]) -> str:
    """Format primary resource title and provider without duplicate names or stray punctuation."""
    if not primary_res or not primary_res.get("title"):
        return ""
    r_title = primary_res["title"].strip().rstrip(" :;,.")
    r_prov = str(primary_res.get("provider", "NPTEL")).strip()
    if r_prov and r_prov.lower() not in r_title.lower():
        return f" Resource: {r_title} ({r_prov})."
    return f" Resource: {r_title}."


def build_deterministic_explanation(result: Dict[str, Any]) -> str:
    """Build a reliable, deterministic explanation template from recommendation results."""
    budget = result.get("credit_budget", {})
    limit = budget.get("limit", 0.0)
    rule = budget.get("rule", "RULE_SEM_CREDIT_CAP_REGULAR")
    core_cr = budget.get("core_credits", 0.0)
    headroom = budget.get("headroom", 0.0)
    open_slots = budget.get("open_slots", 0)
    min_needed = budget.get("min_credits_needed", 0.0)
    max_needed = budget.get("max_credits_needed", 0.0)
    slot_status = budget.get("slot_credit_status", "none")

    recs = result.get("recommendations", [])
    other_eligible = result.get("other_eligible", [])
    no_direct = result.get("no_direct_match", False)
    weak_match = result.get("weak_match", False)
    rejected = result.get("rejected", [])
    future_options = result.get("future_options", [])

    intent = result.get("intent", {})
    intent_source = intent.get("source", "query")
    intent_text = str(intent.get("text", "") or "").strip()

    if intent_source == "profile_goal":
        target_desc = f"your goal ({intent_text})" if intent_text else "your goal"
        other_heading = "Other eligible electives, not matched to your goal:"
    else:
        target_desc = "your query"
        other_heading = "Other eligible electives, not matched to your query:"

    lines: List[str] = []

    # 1. Credit math and slot summary
    if open_slots > 0:
        slot_desc = (
            f"Core courses require {core_cr:.1f} credits, leaving {headroom:.1f} credits of headroom "
            f"for {open_slots} open slot(s) (requires at least {min_needed:.1f} credits)."
        )
    else:
        slot_desc = (
            f"Core courses require {core_cr:.1f} credits, leaving {headroom:.1f} credits of headroom for electives."
        )

    lines.append(f"Credit Summary: Your semester limit is {limit:.1f} credits under {rule}. {slot_desc}")

    if slot_status == "tight":
        lines.append(
            f"Note: Credit headroom is tight ({headroom:.1f} credits available for {open_slots} open slots, "
            f"which may require up to {max_needed:.1f} credits); selecting multiple higher-credit electives may exceed your headroom."
        )
    elif slot_status == "insufficient":
        lines.append(
            f"Warning: Remaining headroom of {headroom:.1f} credits cannot fulfill the minimum {min_needed:.1f} credits "
            f"needed for {open_slots} open slots. You may need Faculty Advisor approval for a credit overload."
        )

    # 2. Recommendations list and other eligible
    if not recs and not other_eligible:
        lines.append("No elective courses could be recommended for your profile this semester.")
        if rejected:
            reasons_sample = [f"- **{r['course_id']}**: {r['reason']}" for r in rejected[:5]]
            lines.append("Rejection details:\n" + "\n".join(reasons_sample))
        lines.append(
            "You may consider consulting your Faculty Advisor regarding prerequisite clearance or credit overload."
        )
        return "\n\n".join(lines)

    if recs:
        lines.append("Here are your recommended courses:")
        for r in recs:
            cid = r["course_id"]
            code = r["course_code"]
            title = r["title"]
            cr = r["credits"]
            matched_skills = r.get("matched_skills", [])
            matched_terms = r.get("matched_terms", [])
            res_str = format_resource_string(r.get("primary_resource"))

            if matched_skills:
                reason_str = f"teaches {', '.join(matched_skills)}"
            elif matched_terms:
                reason_str = f"covers topics in {', '.join(matched_terms)}"
            else:
                reason_str = "recommended elective"

            disp_code = f"{cid}" if code == cid else f"{cid} ({code})"
            lines.append(f"- **{disp_code}**: {title} ({cr:.1f} cr) – {reason_str}.{res_str}")
    else:
        # No courses met MIN_RELEVANCE
        if no_direct:
            lines.append(f"Note: No direct matches were found for {target_desc}.")
        elif weak_match:
            lines.append(
                f"Note: No slot courses strongly match {target_desc} (relevance scores below 0.20)."
            )

    # 2b. Other eligible electives (neutral listing for courses not matching goal)
    if other_eligible:
        lines.append(other_heading)
        for r in other_eligible:
            cid = r["course_id"]
            code = r["course_code"]
            title = r["title"]
            cr = r["credits"]
            res_str = format_resource_string(r.get("primary_resource"))
            disp_code = f"{cid}" if code == cid else f"{cid} ({code})"
            lines.append(f"- **{disp_code}**: {title} ({cr:.1f} cr).{res_str}")

    # 3. Future options from later semesters
    if future_options:
        lines.append("Upcoming Electives in Later Semesters:")
        for fo in future_options:
            f_cid = fo["course_id"]
            f_code = fo.get("course_code", f_cid)
            f_title = fo["title"]
            f_sem = fo["semester"]
            f_cr = fo["credits"]
            f_missing = fo.get("missing_prerequisites", [])
            pr_note = f" (Prerequisites needed: {', '.join(f_missing)})" if f_missing else ""
            f_disp = f_cid if f_code == f_cid else f"{f_cid} ({f_code})"
            lines.append(f"- **{f_disp}**: {f_title} [Sem {f_sem}, {f_cr:.1f} cr]{pr_note}")

    if not recs or no_direct:
        lines.append("What specific topics or elective areas would you prefer to focus on?")

    return "\n\n".join(lines)


def explain(
    result: Dict[str, Any],
    student: Optional[Dict[str, Any]] = None,
) -> Tuple[str, bool, Optional[str]]:
    """Generate human-readable explanation using LLM, with fallback and hallucination guard.

    Returns:
        (answer, llm_used, llm_error)
    """
    # 1. Check if model is configured in environment
    model = os.getenv("LLM_MODEL", "").strip()
    if not model or model.lower() in ["fake", "test", "mock", "none"]:
        return build_deterministic_explanation(result), False, "LLM_MODEL not configured"

    # 2. Extract allowed course codes for the hallucination guard
    allowed_identifiers: Set[str] = set()
    for r in result.get("recommendations", []):
        cid = r.get("course_id", "")
        code = r.get("course_code", "")
        if cid:
            allowed_identifiers.add(cid)
            m = COURSE_CODE_PATTERN.search(cid)
            if m:
                allowed_identifiers.add(m.group(1))
        if code:
            allowed_identifiers.add(code)
            m = COURSE_CODE_PATTERN.search(code)
            if m:
                allowed_identifiers.add(m.group(1))

    for r in result.get("other_eligible", []):
        cid = r.get("course_id", "")
        code = r.get("course_code", "")
        if cid:
            allowed_identifiers.add(cid)
            m = COURSE_CODE_PATTERN.search(cid)
            if m:
                allowed_identifiers.add(m.group(1))
        if code:
            allowed_identifiers.add(code)
            m = COURSE_CODE_PATTERN.search(code)
            if m:
                allowed_identifiers.add(m.group(1))

    for fo in result.get("future_options", []):
        cid = fo.get("course_id", "")
        code = fo.get("course_code", "")
        if cid:
            allowed_identifiers.add(cid)
            m = COURSE_CODE_PATTERN.search(cid)
            if m:
                allowed_identifiers.add(m.group(1))
        if code:
            allowed_identifiers.add(code)
            m = COURSE_CODE_PATTERN.search(code)
            if m:
                allowed_identifiers.add(m.group(1))

    for rej in result.get("rejected", [])[:8]:
        cid = rej.get("course_id", "")
        if cid:
            allowed_identifiers.add(cid)
            m = COURSE_CODE_PATTERN.search(cid)
            if m:
                allowed_identifiers.add(m.group(1))

    # 3. Construct slim JSON payload
    student_summary = {
        "branch": student.get("branch") if student else "Unknown",
        "semester": student.get("semester") if student else None,
        "cgpa": student.get("cgpa") if student else None,
    }
    budget_slim = {
        k: v for k, v in result.get("credit_budget", {}).items() if k != "core_courses"
    }

    payload = {
        "student": student_summary,
        "intent": result.get("intent", {}),
        "credit_budget": budget_slim,
        "recommendations": result.get("recommendations", []),
        "other_eligible": result.get("other_eligible", []),
        "future_options": result.get("future_options", []),
        "rejected": result.get("rejected", [])[:8],
        "no_direct_match": result.get("no_direct_match", False),
        "weak_match": result.get("weak_match", False),
    }

    system_prompt = (
        "You are EBuddy's academic advisor for IIT Bhubaneswar students.\n"
        "STRICT RULES:\n"
        "1. Recommend ONLY courses present in recommendations and cite each exact course_id.\n"
        "2. Provide a 1-2 sentence reason for each recommended course using matched_skills and matched_terms.\n"
        "3. Never describe courses in other_eligible as recommended or matched to the student's goal; present them neutrally under 'Other eligible electives, not matched to your goal'.\n"
        "4. When intent.source is profile_goal, refer to 'your goal (<goal text>)' instead of 'your query'.\n"
        "5. State the credit math once: the limit, core credits, open slots, and remaining headroom.\n"
        "6. If no_direct_match or weak_match is true, clearly state that no courses strongly matched the student's goal and ask what they want to focus on.\n"
        "7. Mention any relevant upcoming electives from future_options.\n"
        "8. If recommendations is empty, explain neutrally using other_eligible and suggest what could change.\n"
        "9. NEVER invent or mention any course codes, credits, or prerequisites not present in the payload."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Here is the verified course recommendation data:\n{json.dumps(payload, indent=2)}"},
    ]

    try:
        reply = llm_client.completion(
            messages=messages,
            temperature=0.2,
            timeout=45,
            num_retries=2,
            purpose="course_recommendation_explanation",
        )
    except Exception as e:
        logger.warning(f"LLM call failed or timed out: {e}")
        llm_err = getattr(llm_client, "last_error", None) or f"LLM call failed: {type(e).__name__}"
        return build_deterministic_explanation(result), False, llm_err

    if not reply or not reply.strip():
        logger.warning("LLM returned empty reply, falling back to deterministic explanation")
        llm_err = getattr(llm_client, "last_error", None) or "Empty LLM response"
        return build_deterministic_explanation(result), False, llm_err

    # 4. Hallucination guard: verify that any course code cited in the reply exists in the allowed identifiers
    cited_codes = COURSE_CODE_PATTERN.findall(reply)
    for code in cited_codes:
        if code not in allowed_identifiers:
            logger.warning(
                f"Hallucination guard triggered: code '{code}' cited in LLM output but not in valid shortlist {allowed_identifiers}. Falling back."
            )
            return build_deterministic_explanation(result), False, f"Hallucination guard: uncited code {code}"

    return reply.strip(), True, None
