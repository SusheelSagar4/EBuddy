"""Explanation generation and hallucination guard for EBuddy Recommender.

Wraps LLM calls via app.llm.client.llm_client, enforces strict system prompt rules,
and provides a deterministic template fallback on failure, timeout, or hallucination.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Set

from app.llm.client import llm_client

logger = logging.getLogger("ebuddy.recommender.explain")

COURSE_CODE_PATTERN = re.compile(r"\b([A-Z]{2}\d[A-Z]\d{3})\b")


def build_deterministic_explanation(result: Dict[str, Any]) -> str:
    """Build a reliable, deterministic explanation template from recommendation results."""
    budget = result.get("credit_budget", {})
    limit = budget.get("limit", 0.0)
    rule = budget.get("rule", "RULE_SEM_CREDIT_CAP_REGULAR")
    core_cr = budget.get("core_credits", 0.0)
    headroom = budget.get("headroom", 0.0)

    recs = result.get("recommendations", [])
    no_direct = result.get("no_direct_match", False)
    rejected = result.get("rejected", [])

    lines: List[str] = []
    lines.append(
        f"Credit Summary: Your semester limit is {limit:.1f} credits under {rule}. "
        f"Core courses require {core_cr:.1f} credits, leaving {headroom:.1f} credits of headroom for electives."
    )

    if not recs:
        lines.append(
            "No elective courses could be recommended for your profile this semester."
        )
        if rejected:
            reasons_sample = [f"- **{r['course_id']}**: {r['reason']}" for r in rejected[:5]]
            lines.append("Rejection details:\n" + "\n".join(reasons_sample))
        lines.append(
            "You may consider consulting your Faculty Advisor regarding prerequisite clearance or credit overload."
        )
        return "\n\n".join(lines)

    if no_direct:
        lines.append(
            "Note: No direct skill or keyword matches were found for your query. "
            "Here are the available elective courses for this semester:"
        )
    else:
        lines.append("Here are your recommended courses:")

    for r in recs:
        cid = r["course_id"]
        code = r["course_code"]
        title = r["title"]
        cr = r["credits"]
        matched_skills = r.get("matched_skills", [])
        matched_terms = r.get("matched_terms", [])
        primary_res = r.get("primary_resource")

        reasons = []
        if matched_skills:
            reasons.append(f"teaches skills in {', '.join(matched_skills)}")
        elif matched_terms:
            reasons.append(f"covers relevant topics ({', '.join(matched_terms)})")
        else:
            reasons.append("eligible elective matching semester slot criteria")

        reason_str = "; ".join(reasons)
        res_str = ""
        if primary_res and primary_res.get("title"):
            res_str = f" Resource: {primary_res['title']} ({primary_res.get('provider', 'Online')})."

        lines.append(
            f"- **{cid}** ({code} – {title}, {cr:.1f} credits): Fits within your {headroom:.1f} credit headroom. "
            f"This course {reason_str}.{res_str}"
        )

    if no_direct:
        lines.append("What specific topics or elective areas would you prefer to focus on?")

    return "\n\n".join(lines)


def explain(result: Dict[str, Any], student: Optional[Dict[str, Any]] = None) -> str:
    """Generate human-readable explanation using LLM, with fallback and hallucination guard.

    Uses LiteLLM via app.llm.client.llm_client reading dynamic config from env vars:
    LLM_MODEL, LLM_API_KEY, LLM_API_BASE. Never hard-codes model names.
    """
    # 1. Check if model is configured in environment
    model = os.getenv("LLM_MODEL", "").strip()
    if not model or model.lower() in ["fake", "test", "mock", "none"]:
        return build_deterministic_explanation(result)

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
        "rejected": result.get("rejected", [])[:8],
        "no_direct_match": result.get("no_direct_match", False),
    }

    system_prompt = (
        "You are EBuddy's academic advisor for IIT Bhubaneswar students.\n"
        "STRICT RULES:\n"
        "1. Recommend ONLY courses present in the recommendations shortlist and cite each exact course_id.\n"
        "2. Provide a 1-2 sentence reason for each course using matched_skills and matched_terms.\n"
        "3. State the credit math once: the limit, core credits, and remaining headroom.\n"
        "4. If no_direct_match is true, clearly state that no direct match was found and ask the student what they want to focus on.\n"
        "5. If the recommendations list is empty, explain using the rejected reasons and suggest what could change.\n"
        "6. NEVER invent or mention any course codes, credits, or prerequisites not present in the payload."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Here is the verified course recommendation data:\n{json.dumps(payload, indent=2)}"},
    ]

    try:
        reply = llm_client.completion(
            messages=messages,
            temperature=0.2,
            timeout=30,
            num_retries=2,
            purpose="course_recommendation_explanation",
        )
    except Exception as e:
        logger.warning(f"LLM call failed or timed out: {e}")
        return build_deterministic_explanation(result)

    if not reply or not reply.strip():
        return build_deterministic_explanation(result)

    # 4. Hallucination guard: verify that any course code cited in the reply exists in the shortlist/payload
    cited_codes = COURSE_CODE_PATTERN.findall(reply)
    for code in cited_codes:
        if code not in allowed_identifiers:
            logger.warning(
                f"Hallucination guard triggered: code '{code}' cited in LLM output but not in valid shortlist {allowed_identifiers}. Falling back."
            )
            return build_deterministic_explanation(result)

    return reply.strip()
