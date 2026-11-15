"""Deterministic retrieval and scoring for EBuddy Recommender.

Includes a lightweight rule-based tokenizer, stopword filtering, goal term expansion,
and 70/30 skill-vs-title/syllabus scoring. Pure Python with no heavy ML dependencies.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

from app.recommender.kb import get_courses, get_course_skills, get_skills

# Common English stopwords and academic noise words to ignore
STOPWORDS: Set[str] = {
    "a", "about", "above", "advanced", "after", "again", "against", "all", "am", "an", "analysis", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "course", "courses", "design", "did", "do", "does", "doing", "down", "during", "each", "engineering",
    "few", "for", "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "introduction", "is", "it", "its", "itself",
    "learn", "learning", "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off",
    "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own",
    "role", "same", "semester", "she", "should", "so", "some", "student", "study", "studying", "such",
    "system", "systems", "take", "taking", "technology", "technologies", "than", "that", "the", "their", "theirs", "them", "themselves", "then",
    "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "want", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "will", "with", "would", "you", "your", "yours", "yourself", "yourselves",
}

# Domain and goal term expansion rules
GOAL_EXPANSION: Dict[str, List[str]] = {
    "software": [
        "software", "programming", "data structures", "algorithms", "database",
        "embedded", "machine learning", "coding", "python", "oop",
        "artificial intelligence", "intelligence", "computing", "development"
    ],
    "ai": [
        "artificial intelligence", "intelligence", "machine learning", "deep learning",
        "pattern recognition", "neural networks", "heuristics", "reasoning", "agents"
    ],
    "machine learning": [
        "machine learning", "deep learning", "neural networks", "pattern recognition",
        "statistics", "data science", "classification", "clustering", "algorithms"
    ],
    "data science": [
        "data science", "machine learning", "pattern recognition", "statistics",
        "probability", "artificial intelligence", "data mining", "algorithms", "python"
    ],
    "vlsi": [
        "vlsi", "cmos", "semiconductor", "verilog", "digital logic", "circuit",
        "microelectronics", "asic", "fpga", "chip"
    ],
    "embedded": [
        "embedded", "microcontrollers", "microprocessors", "real time", "computing",
        "robotics", "interfacing", "firmware", "iot"
    ],
    "power": [
        "power", "grid", "electrical machines", "energy", "high voltage",
        "converters", "drives", "transmission", "renewable"
    ],
    "signal": [
        "signal", "signals", "signal processing", "dsp", "linear",
        "filtering", "communication", "image processing"
    ],
    "material": [
        "materials", "metallurgy", "thermodynamics", "nanomaterials", "alloys",
        "ceramics", "polymers", "crystallography", "solidification", "composite"
    ],
    "research": [
        "research", "higher studies", "thesis", "modeling",
        "simulation", "experimental", "theory", "project"
    ],
    "gate": [
        "gate", "core", "theory", "fundamentals", "mathematics",
        "machines", "signals", "control"
    ],
}


def light_stem(word: str) -> str:
    """Apply rule-based suffix stemming to normalize words without heavy libraries."""
    w = word.lower()
    if len(w) <= 3:
        return w

    for suffix in ("ations", "ation", "ction", "ting", "ling", "ning", "ring", "ing", "ies", "es", "s", "ed", "ment", "ness", "ity", "al", "ic"):
        if w.endswith(suffix) and len(w) - len(suffix) >= 3:
            return w[:-len(suffix)]
    return w


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase, stripped, stemmed tokens, filtering out stopwords."""
    if not text or not isinstance(text, str):
        return []

    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    tokens: List[str] = []
    for w in words:
        if w not in STOPWORDS and len(w) > 1:
            tokens.append(light_stem(w))
    return tokens


def intent_terms(text: Optional[str]) -> List[str]:
    """Extract and expand intent terms from query or profile goal text."""
    if not text or not isinstance(text, str):
        return []

    clean_text = text.strip()
    if not clean_text:
        return []

    terms_set: Set[str] = set()

    # 1. Base tokens from raw text
    for t in tokenize(clean_text):
        terms_set.add(t)

    # 2. Match against expansion categories
    text_lower = clean_text.lower()
    for category, expansions in GOAL_EXPANSION.items():
        # Match category keyword as substring or token
        if category in text_lower:
            for exp in expansions:
                for t in tokenize(exp):
                    terms_set.add(t)

    # Return sorted list for determinism
    return sorted(terms_set)


def score_courses(
    course_ids: List[str],
    terms: List[str],
    kb: Any = None,
) -> Dict[str, Dict[str, Any]]:
    """Score courses based on 70% skill overlap + 30% title/syllabus overlap.

    Formula:
    0.7 * best skill score (3 term hits = full score, multiplied by course_skill weight)
    + 0.3 * title/syllabus overlap (3 term hits = full score).

    Returns a dict mapping course_id -> {score, matched_skills, matched_terms}.
    """
    results: Dict[str, Dict[str, Any]] = {}
    if not course_ids:
        return results

    terms_set = set(terms)
    courses_df = get_courses()
    course_skills_df = get_course_skills()
    skills_df = get_skills()

    # Pre-index skills by skill_id
    skills_by_id = {}
    for _, s_row in skills_df.iterrows():
        sid = s_row["skill_id"]
        text = f"{s_row.get('name', '')} {s_row.get('domain', '')} {s_row.get('description', '')}"
        skills_by_id[sid] = {
            "name": str(s_row.get("name", "") or ""),
            "tokens": set(tokenize(text)),
        }

    # Pre-index course skills by course_id
    course_skills_map: Dict[str, List[Tuple[str, float]]] = {}
    for _, cs_row in course_skills_df.iterrows():
        cid = cs_row["course_id"]
        sid = cs_row["skill_id"]
        w = float(cs_row.get("weight", 1.0))
        course_skills_map.setdefault(cid, []).append((sid, w))

    # Pre-index course title and syllabus by course_id
    courses_map = {}
    for _, c_row in courses_df.iterrows():
        cid = c_row["course_id"]
        title = str(c_row.get("title", "") or "")
        syllabus = str(c_row.get("syllabus_text", "") or "")
        objectives = str(c_row.get("learning_objectives", "") or "")
        full_text = f"{title} {syllabus} {objectives}"
        courses_map[cid] = {
            "title": title,
            "tokens": set(tokenize(full_text)),
        }

    for cid in course_ids:
        course_matched_terms: Set[str] = set()
        course_matched_skills: List[str] = []

        # 1. Skill scoring (70%)
        best_skill_score = 0.0
        linked_skills = course_skills_map.get(cid, [])
        for sid, weight in linked_skills:
            if sid in skills_by_id:
                s_info = skills_by_id[sid]
                hits = s_info["tokens"].intersection(terms_set)
                if hits:
                    course_matched_terms.update(hits)
                    course_matched_skills.append(s_info["name"])
                    # 3 hits = full 1.0, weighted by course_skill weight
                    skill_hit_ratio = min(1.0, len(hits) / 3.0)
                    s_score = skill_hit_ratio * weight
                    if s_score > best_skill_score:
                        best_skill_score = s_score

        # 2. Title & syllabus scoring (30%)
        title_syllabus_score = 0.0
        c_info = courses_map.get(cid)
        if c_info:
            hits = c_info["tokens"].intersection(terms_set)
            if hits:
                course_matched_terms.update(hits)
                title_syllabus_score = min(1.0, len(hits) / 3.0)

        # Combined weighted score
        final_score = round(0.7 * best_skill_score + 0.3 * title_syllabus_score, 4)

        results[cid] = {
            "score": final_score,
            "matched_skills": sorted(set(course_matched_skills)),
            "matched_terms": sorted(course_matched_terms),
        }

    return results
