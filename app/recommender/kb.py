"""Knowledge Base loaders and slot mapping utilities for EBuddy Recommender.

Loads and caches seed KB data (CSV/JSON) and branch curriculum semester tables.
"""

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger("ebuddy.recommender.kb")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SEED_KB_DIR = DATA_DIR / "seed" / "kb"
RAW_DATA_DIR = DATA_DIR / "raw"

# Explicit assumption mapping for Metallurgical & Materials Engineering (MME) slots.
# NOTE: Verify against the MME PDF. MME slot options carry no semester numbers in slot_option.csv.
MME_SLOT_SEMESTER_MAP: Dict[str, int] = {
    "MM_LATERAL_1": 4,
    "MM_LATERAL_2": 5,
    "MM_LATERAL_3": 6,
    "MM_ELECTIVE_1": 7,
    "MM_ELECTIVE_2": 7,
    "MM_ELECTIVE_3": 8,
    "MM_ELECTIVE_4": 8,
    "MM_ELECTIVE_5": 8,
}


@lru_cache(maxsize=1)
def get_courses() -> pd.DataFrame:
    """Load course catalog dataframe."""
    path = SEED_KB_DIR / "course.csv"
    df = pd.read_csv(path, dtype=str)
    # Cast boolean columns
    if "is_placeholder" in df.columns:
        df["is_placeholder"] = df["is_placeholder"].astype(str).str.lower().isin(["true", "1", "t"])
    if "code_conflict" in df.columns:
        df["code_conflict"] = df["code_conflict"].astype(str).str.lower().isin(["true", "1", "t"])
    if "in_semester_table" in df.columns:
        df["in_semester_table"] = df["in_semester_table"].astype(str).str.lower().isin(["true", "1", "t"])
    return df


@lru_cache(maxsize=1)
def get_course_offerings() -> pd.DataFrame:
    """Load course offering semester and parity information."""
    path = SEED_KB_DIR / "course_offering.csv"
    df = pd.read_csv(path, dtype=str)
    if "semester_number" in df.columns:
        df["semester_number"] = pd.to_numeric(df["semester_number"], errors="coerce")
    return df


@lru_cache(maxsize=1)
def get_course_prerequisites() -> pd.DataFrame:
    """Load course prerequisites relations."""
    path = SEED_KB_DIR / "course_prerequisite.csv"
    return pd.read_csv(path, dtype=str)


@lru_cache(maxsize=1)
def get_course_skills() -> pd.DataFrame:
    """Load course-to-skill mappings with weights."""
    path = SEED_KB_DIR / "course_skill.csv"
    df = pd.read_csv(path, dtype=str)
    if "weight" in df.columns:
        df["weight"] = pd.to_numeric(df["weight"], errors="coerce").fillna(1.0)
    if "level_taught" in df.columns:
        df["level_taught"] = pd.to_numeric(df["level_taught"], errors="coerce").fillna(0.0)
    return df


@lru_cache(maxsize=1)
def get_skills() -> pd.DataFrame:
    """Load skill definitions catalog."""
    path = SEED_KB_DIR / "skill.csv"
    return pd.read_csv(path, dtype=str)


@lru_cache(maxsize=1)
def get_slot_options() -> pd.DataFrame:
    """Load slot option mappings."""
    path = SEED_KB_DIR / "slot_option.csv"
    return pd.read_csv(path, dtype=str)


@lru_cache(maxsize=1)
def get_resources() -> pd.DataFrame:
    """Load educational learning resources."""
    path = SEED_KB_DIR / "resource.csv"
    return pd.read_csv(path, dtype=str)


@lru_cache(maxsize=1)
def get_resource_courses() -> pd.DataFrame:
    """Load mappings between courses and resources."""
    path = SEED_KB_DIR / "resource_course.csv"
    return pd.read_csv(path, dtype=str)


@lru_cache(maxsize=1)
def get_academic_rules() -> List[Dict[str, Any]]:
    """Load baseline academic rules (credit caps, probation, overload)."""
    path = SEED_KB_DIR / "academic_rule.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=2)
def get_curriculum_table(branch: str) -> pd.DataFrame:
    """Load curriculum semester table for specified branch (EE or MME)."""
    branch_key = branch.strip().lower()
    if branch_key in ["ee", "electrical"]:
        path = RAW_DATA_DIR / "ee" / "curriculum_semester_table.csv"
    elif branch_key in ["mme", "metallurgical", "metallurgy"]:
        path = RAW_DATA_DIR / "mme" / "curriculum_semester_table.csv"
    else:
        raise ValueError(f"Unsupported branch '{branch}'. Must be 'EE' or 'MME'.")

    return pd.read_csv(path, dtype=str)


def slot_semester(slot_id: str) -> Optional[int]:
    """Determine the semester number for a slot identifier."""
    if not slot_id or not isinstance(slot_id, str):
        return None
    slot = slot_id.strip()

    # MME slot assumption dictionary
    if slot in MME_SLOT_SEMESTER_MAP:
        return MME_SLOT_SEMESTER_MAP[slot]

    # EE slot naming convention (e.g. SLOT_SEM4_LATERAL_1, SLOT_SEM7_ELECTIVE_2)
    match = re.search(r"SLOT_SEM(\d)_", slot, re.IGNORECASE)
    if match:
        return int(match.group(1))

    return None


def slot_branch(slot_id: str) -> str:
    """Determine the academic branch for a slot identifier (MME or EE)."""
    if not slot_id or not isinstance(slot_id, str):
        return "EE"
    slot = slot_id.strip().upper()
    if slot.startswith("MM_"):
        return "MME"
    return "EE"


def resolve_course_id(code: str, is_core: bool = False) -> str:
    """Resolve a course code to its canonical course_id in course.csv.

    Specifically handles duplicate code conflicts (e.g. ML4L001-ML4L003 in MME),
    mapping Sem VII core rows to `*_CORE` and slot/elective rows to `*_ELEC`.
    """
    clean_code = code.strip()
    courses_df = get_courses()

    # Check for exact course_id first
    if clean_code in courses_df["course_id"].values:
        return clean_code

    # Check if there is a code conflict flag for this code
    conflicts = courses_df[
        (courses_df["course_code"] == clean_code) & (courses_df["code_conflict"] == True)
    ]
    if not conflicts.empty:
        target_suffix = "_CORE" if is_core else "_ELEC"
        for cid in conflicts["course_id"].values:
            if cid.endswith(target_suffix):
                return cid
        logger.warning(
            "Code conflict for %s (is_core=%s) but no matching %s found; using %s",
            clean_code,
            is_core,
            target_suffix,
            conflicts["course_id"].iloc[0],
        )
        return conflicts["course_id"].iloc[0]

    # Standard non-conflict mapping: return the matching course_id
    matches = courses_df[courses_df["course_code"] == clean_code]
    if not matches.empty:
        return matches["course_id"].iloc[0]

    return clean_code


def get_primary_resource(course_id: str) -> Optional[Dict[str, str]]:
    """Retrieve primary learning resource for a course if available."""
    rc_df = get_resource_courses()
    primary_rc = rc_df[(rc_df["course_id"] == course_id) & (rc_df["role"] == "primary")]
    if primary_rc.empty:
        return None

    res_id = primary_rc["resource_id"].iloc[0]
    res_df = get_resources()
    res = res_df[res_df["resource_id"] == res_id]
    if res.empty:
        return None

    row = res.iloc[0]
    return {
        "title": str(row.get("title", "") or ""),
        "url": str(row.get("url", "") or ""),
        "provider": str(row.get("provider", "") or ""),
    }
