import re
from typing import Dict, Any, List, Optional, Tuple
from app.contracts.goal import canonicalize_goal_id

KEYWORD_RULES: List[Tuple[List[str], str, float]] = [
    # MBA / CAT
    (["mba", "cat", "iim", "xat", "management", "business school", "gmat", "snap", "nmat"], "GOAL_CORE_TO_MBA", 0.95),
    # UPSC / Civil Services
    (["upsc", "civil services", "cse", "ias", "ips", "ifs", "governance", "public service"], "GOAL_UPSC_CSE", 0.95),
    # Startup / Entrepreneurship
    (["startup", "founder", "entrepreneur", "venture", "incubation", "mvp", "pitch"], "GOAL_STARTUP_FOUNDER", 0.95),
    # SDE / Software / Data Science
    (["sde", "software", "coding", "data science", "cs minor", "developer", "machine learning", "swe"], "GOAL_CROSS_SDE_DATA", 0.90),
    # EE VLSI
    (["vlsi", "semiconductor", "chip design", "fpga", "asic", "hardware design", "ic design"], "GOAL_EE_CORE_VLSI", 0.92),
    # EE Power
    (["power", "grid", "renewable", "smart grid", "power systems", "ev drivetrain", "substation"], "GOAL_EE_CORE_POWER", 0.92),
    # Higher Studies / Research
    (["mtech", "ms", "phd", "higher studies", "research lab", "fellowship", "gate"], "GOAL_EE_RES_HIGHER_STUDIES", 0.88),
    # Metallurgy Process
    (["steel", "metallurgy", "ironmaking", "process engineer", "smelting", "blast furnace", "jsw", "tata steel"], "GOAL_MM_PROCESS_ENGINEER", 0.92),
    # Advanced Materials
    (["advanced materials", "aerospace", "drdo", "isro", "high entropy", "superalloys", "defense materials"], "GOAL_MM_ADVANCED_MATERIALS", 0.92),
    # Biomaterials
    (["biomaterials", "medical devices", "orthopedic", "implants", "bone scaffold"], "GOAL_MM_BIOMATERIALS", 0.92),
    # Energy Materials
    (["battery", "energy materials", "solid electrolyte", "lithium-ion", "fuel cell"], "GOAL_MM_ENERGY_MATERIALS", 0.92),
]

def keyword_fallback_route_goal(
    user_text: str,
    programme_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Deterministic keyword router fallback when LLM is offline or not configured.
    Returns matched goal_id, confidence, and alternatives.
    """
    text_lower = (user_text or "").lower()
    
    # Check exact keyword matches
    best_goal = None
    best_conf = 0.0
    matched_keywords = []

    for keywords, gid, conf in KEYWORD_RULES:
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                matched_keywords.append(kw)
                if conf > best_conf:
                    best_conf = conf
                    best_goal = gid

    # Contextual refinement by branch if higher studies
    if best_goal == "GOAL_EE_RES_HIGHER_STUDIES" and programme_id and ("MM" in programme_id.upper()):
        best_goal = "GOAL_MM_RES_HIGHER_STUDIES"

    # Contextual refinement for generic "core company"
    if not best_goal and "core" in text_lower:
        if programme_id and "MM" in programme_id.upper():
            best_goal = "GOAL_MM_PROCESS_ENGINEER"
            best_conf = 0.75
        else:
            best_goal = "GOAL_EE_CORE_POWER"
            best_conf = 0.75

    # If completely unmatched or nonsense string
    if not best_goal:
        # Provide default branch career fallback with low confidence
        if programme_id and "MM" in programme_id.upper():
            best_goal = "GOAL_MM_PROCESS_ENGINEER"
        else:
            best_goal = "GOAL_EE_CORE_POWER"
        best_conf = 0.20

    canonical_id = canonicalize_goal_id(best_goal)

    # Pick 2-3 distinct alternatives
    candidate_alts = [
        "GOAL_CORE_TO_MBA",
        "GOAL_CROSS_SDE_DATA",
        "GOAL_UPSC_CSE",
        "GOAL_STARTUP_FOUNDER",
        "GOAL_EE_CORE_VLSI" if not (programme_id and "MM" in programme_id.upper()) else "GOAL_MM_ADVANCED_MATERIALS"
    ]
    alternatives = [a for a in candidate_alts if a != canonical_id][:3]

    return {
        "goal_id": canonical_id,
        "confidence": best_conf,
        "matched_keywords": matched_keywords,
        "alternatives": alternatives
    }
