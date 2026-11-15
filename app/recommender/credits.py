"""Deterministic credit budget, limit, and core course calculations for EBuddy Recommender.

Handles curriculum semester table parsing, credit caps, probation limits, and headroom math.
"""

import math
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.recommender.kb import get_courses, get_curriculum_table, resolve_course_id

ROMAN_SEMESTER_MAP: Dict[str, int] = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
}


def parse_credit(val: Any) -> float:
    """Parse credit string into float.

    Handles upper-bound taking for slot rows (e.g. '3 / 4' -> 4.0),
    header totals (e.g. '24/25' -> 25.0), and extra activity removal
    (e.g. '22/23 + 1' -> 23.0).
    """
    if val is None or pd.isna(val):
        return float("nan")
    if isinstance(val, (int, float)):
        return float(val)

    s = str(val).strip()
    if not s:
        return float("nan")

    # Ignore extra-activity parts after '+'
    if "+" in s:
        s = s.split("+")[0].strip()

    # Find all numeric patterns (integers or decimals)
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]
    if not nums:
        return float("nan")

    return max(nums)


def first_code(val: Any) -> Optional[str]:
    """Extract the first course code matching `[A-Z]{2}\\d[A-Z]\\d{3}`.

    Returns None for entries like '(see options)' or '(no code in source)'.
    """
    if val is None or pd.isna(val):
        return None
    s = str(val).strip()
    match = re.search(r"([A-Z]{2}\d[A-Z]\d{3})", s)
    return match.group(1) if match else None


def _extract_sem_number(sem_str: Any) -> Optional[int]:
    """Parse semester number from header or row semester text."""
    if sem_str is None or pd.isna(sem_str):
        return None
    s = str(sem_str).strip()
    # Match patterns like 'SEMESTER – IV', 'SEMESTER - 4', 'Sem IV', 'Sem 4'
    match = re.search(r"Sem(?:ester)?\s*[–-]?\s*([IVXLCDM]+|\d+)", s, re.IGNORECASE)
    if not match:
        return None

    token = match.group(1).upper()
    if token in ROMAN_SEMESTER_MAP:
        return ROMAN_SEMESTER_MAP[token]
    if token.isdigit():
        return int(token)
    return None


def semester_credit_total(curriculum_df: pd.DataFrame, sem: int) -> float:
    """Extract the total credit limit stated in the curriculum header row for the semester."""
    for _, row in curriculum_df.iterrows():
        sem_cell = str(row.get("Semester", "") or "")
        if "SEMESTER" in sem_cell:
            sem_idx = _extract_sem_number(sem_cell)
            if sem_idx == sem:
                match = re.search(r"Total credits:\s*([^|]+)", sem_cell, re.IGNORECASE)
                if match:
                    parsed = parse_credit(match.group(1))
                    if not math.isnan(parsed):
                        return parsed

    # Common first-year fallback: MME table starts at Sem III; Sem I & II are common first-year
    if sem in [1, 2]:
        ee_df = get_curriculum_table("EE")
        return semester_credit_total(ee_df, sem)

    return 24.0


def core_courses(curriculum_df: pd.DataFrame, sem: int) -> List[Dict[str, Any]]:
    """Return all fixed core courses for a given semester in the curriculum table.

    Rows with Course Type starting with 'Lateral', 'Breadth' or 'Elective' are slot rows,
    not fixed core. All other rows with a valid course code are treated as core.
    """
    # If MME and sem is 1 or 2, use common first-year table
    if sem in [1, 2] and len(curriculum_df[curriculum_df["Semester"].astype(str).str.contains("Sem I", na=False)]) == 0:
        curriculum_df = get_curriculum_table("EE")

    courses_cat = get_courses()
    course_cat_map = {row["course_id"]: row for _, row in courses_cat.iterrows()}

    core_list: List[Dict[str, Any]] = []

    for _, row in curriculum_df.iterrows():
        row_sem = _extract_sem_number(row.get("Semester"))
        if row_sem != sem:
            continue

        raw_code = row.get("Course Code")
        code = first_code(raw_code)
        if not code:
            continue

        course_type = str(row.get("Course Type", "") or "").strip()
        if course_type.startswith(("Lateral", "Breadth", "Elective")):
            continue

        # Resolve duplicate code conflicts (e.g. ML4L001-ML4L003 in MME as core)
        cid = resolve_course_id(code, is_core=True)

        parsed_cr = parse_credit(row.get("Credits"))
        if math.isnan(parsed_cr) and cid in course_cat_map:
            parsed_cr = parse_credit(course_cat_map[cid].get("credits"))
        if math.isnan(parsed_cr):
            parsed_cr = 3.0

        title = str(row.get("Course Name", "") or "").strip()
        if not title and cid in course_cat_map:
            title = str(course_cat_map[cid].get("title", "") or "")

        core_list.append({
            "course_id": cid,
            "course_code": code,
            "title": title,
            "credits": parsed_cr,
            "course_type": course_type,
        })

    return core_list


def credit_limit(
    cgpa: float,
    curriculum_total: float,
    overload_approved: bool = False,
    rules: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[float, str]:
    """Calculate the student's credit limit for the current semester and return (limit, rule_id).

    Logic:
    - CGPA < 6.0: probation cap (18 credits) -> RULE_SEM_CREDIT_CAP_PROBATION
    - overload_approved and CGPA >= 8.5: overload cap (30 credits) -> RULE_SEM_CREDIT_CAP_REGULAR
    - otherwise: min(26.0, curriculum_total) -> RULE_SEM_CREDIT_CAP_REGULAR
    """
    probation_cap = 18.0
    regular_cap = 26.0
    overload_cap = 30.0

    if rules:
        for r in rules:
            rid = r.get("rule_id")
            params = r.get("parameters", {})
            if rid == "RULE_SEM_CREDIT_CAP_PROBATION":
                probation_cap = float(params.get("max_credits", probation_cap))
            elif rid == "RULE_SEM_CREDIT_CAP_REGULAR":
                regular_cap = float(params.get("max_credits", regular_cap))
                overload_cap = float(params.get("max_overload_credits", overload_cap))

    if cgpa < 6.0:
        return probation_cap, "RULE_SEM_CREDIT_CAP_PROBATION"

    if overload_approved and cgpa >= 8.5:
        return overload_cap, "RULE_SEM_CREDIT_CAP_REGULAR"

    return min(regular_cap, float(curriculum_total)), "RULE_SEM_CREDIT_CAP_REGULAR"


def open_slot_info(curriculum_df: pd.DataFrame, sem: int) -> Dict[str, Any]:
    """Calculate the number of open slots and the min/max credit budget needed for the semester.

    Identifies slot definition rows (Lateral, Breadth, Elective) where no concrete course code
    is assigned. Returns dict with open_slots count, min_credits_needed, and max_credits_needed.
    """
    if sem in [1, 2] and len(curriculum_df[curriculum_df["Semester"].astype(str).str.contains("Sem I", na=False)]) == 0:
        curriculum_df = get_curriculum_table("EE")

    slots: List[Dict[str, Any]] = []
    for _, row in curriculum_df.iterrows():
        row_sem = _extract_sem_number(row.get("Semester"))
        if row_sem != sem:
            continue

        ct = str(row.get("Course Type", "") or "").strip()
        code = first_code(row.get("Course Code"))
        if ct.startswith(("Lateral", "Breadth", "Elective")) and not code:
            c_text = str(row.get("Credits", "") or "").split("+")[0]
            nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", c_text)]
            min_c = min(nums) if nums else 3.0
            max_c = max(nums) if nums else 3.0
            slots.append({
                "name": str(row.get("Course Name", "") or "").strip(),
                "type": ct,
                "min_credits": min_c,
                "max_credits": max_c,
            })

    open_slots = len(slots)
    min_needed = sum(s["min_credits"] for s in slots)
    max_needed = sum(s["max_credits"] for s in slots)

    return {
        "open_slots": open_slots,
        "min_credits_needed": min_needed,
        "max_credits_needed": max_needed,
        "slots": slots,
    }
