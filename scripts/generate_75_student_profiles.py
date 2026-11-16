#!/usr/bin/env python3
"""
Deterministic generator for 75 synthetic, anonymised IIT Bhubaneswar student profiles
(B.Tech EE and B.Tech MME, Years 1-4, all goal families) - Adobe PS Section 4.

    python scripts/generate_75_student_profiles.py            # (re)write the seed files
    python scripts/generate_75_student_profiles.py --check    # verify files on disk match the generator

What it writes
--------------
data/seed/personas/<persona_id>/students.csv   one roster per persona plugin (conformance input)
data/seed/student/student.csv                  -> student.student
data/seed/student/completed_course.csv         -> student.completed_course   (transcript with grades, backlogs flagged)
data/seed/student/student_goal.csv             -> student.goal               (active goal + previous goal for switchers)
data/seed/student/interest.csv                 -> student.interest           (self-declared, reliability_tier = weak)
data/seed/student/skill_evidence.csv           -> student.skill_evidence     (reliability_tier = strong | medium | weak)
data/seed/student/constraint.csv               -> student.constraint         (weekly-hours cap, credit cap)
data/seed/student/preference.csv               -> student.preference
data/seed/student/profile_manifest.json        distribution + edge-case coverage summary

Rules
-----
* No real students: names are drawn from generic first/last-name lists and ids are synthetic.
* Every course code written here exists in data/seed/kb/course.csv (asserted before writing).
* Transcripts are complete: every mandatory course of earlier semesters appears, either passed
  (with a grade) or as an explicit backlog (grade F, is_backlog = TRUE).
* The 16 pre-existing conformance fixtures (CONF_STU_*) keep their ids, programme, semester,
  CGPA and backlog count; only their transcripts are completed and catalogue-checked.
* Fully deterministic: fixed seeds, fixed timestamps, no wall-clock, no hash().

Mandatory PS edge cases (tagged in `edge_case_tags`)
  ACTIVE_BACKLOG            uncleared mandatory course from an earlier semester
  CGPA_ON_MINOR_CUTOFF      CGPA at 7.95 / 7.99 / 8.00 / 8.01 around the 8.00 minor cutoff
  CGPA_ON_OVERLOAD_CUTOFF   CGPA at 8.49 / 8.50 around the 8.50 honours-type overload cutoff
  INTEREST_EVIDENCE_CLASH   strong self-declared interest vs weak assessed diagnostic / grades
  MID_DEGREE_GOAL_SWITCH    previous goal recorded, switched in a stated semester
  TIGHT_WEEKLY_HOURS        weekly self-study cap of 6-9 hours
  TIGHT_CREDIT_CAP          student-stated credit cap at or below the usual semester load
"""
import os
import sys
import csv
import json
import random
import argparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from app.engine.planner import Planner  # noqa: E402  (read-only use of curriculum tables)

SEED = 20261115
STUDENT_DIR = os.path.join("data", "seed", "student")
PERSONA_DIR = os.path.join("data", "seed", "personas")

GRADE_POINTS = [("EX", 10), ("A", 9), ("B", 8), ("C", 7), ("D", 6), ("P", 5)]
GP = dict(GRADE_POINTS)

FIRST = ["Aarav", "Aditi", "Akash", "Ananya", "Arjun", "Bhavna", "Chirag", "Deepa", "Dev", "Diya", "Esha", "Farhan",
         "Gauri", "Harsh", "Isha", "Jatin", "Kavya", "Kunal", "Lakshmi", "Manav", "Meera", "Naveen", "Neha", "Omkar",
         "Pooja", "Pranav", "Rhea", "Rohit", "Saanvi", "Sahil", "Tanvi", "Uday", "Varun", "Vidya", "Yash", "Zoya"]
LAST = ["Agarwal", "Behera", "Chatterjee", "Dash", "Fernandes", "Gupta", "Hegde", "Iyer", "Joshi", "Kulkarni", "Lal",
        "Mahapatra", "Nayak", "Ojha", "Panda", "Qureshi", "Rao", "Sahoo", "Tripathy", "Unni", "Verma", "Yadav"]

POWER, VLSI = "GOAL_EE_CORE_POWER", "GOAL_EE_CORE_VLSI"
MM_ADV, MM_PROC = "GOAL_MM_ADVANCED_MATERIALS", "GOAL_MM_PROCESS_ENGINEER"
SDE, DA, AIML = "GOAL_TRACK_SDE", "GOAL_TRACK_DA", "GOAL_TRACK_AIML"
HS_EE, HS_MM = "GOAL_EE_RES_HIGHER_STUDIES", "GOAL_MM_RES_HIGHER_STUDIES"
MBA, UPSC, STARTUP = "GOAL_MBA_CAT", "GOAL_UPSC_CSE", "GOAL_STARTUP_FOUNDER"

BACKLOG, MINOR_CUT, OVER_CUT = "ACTIVE_BACKLOG", "CGPA_ON_MINOR_CUTOFF", "CGPA_ON_OVERLOAD_CUTOFF"
CLASH, SWITCH, TIGHT_H, TIGHT_C = "INTEREST_EVIDENCE_CLASH", "MID_DEGREE_GOAL_SWITCH", "TIGHT_WEEKLY_HOURS", "TIGHT_CREDIT_CAP"

# Declared-interest topics per goal (self-declared = WEAK evidence)
GOAL_INTERESTS = {
    POWER: ["Power systems and smart grid", "Renewable energy integration", "Power electronics converters"],
    VLSI: ["VLSI design", "Embedded systems", "Analog electronics"],
    MM_ADV: ["High-entropy alloys", "Physical metallurgy", "Materials characterization"],
    MM_PROC: ["Iron and steelmaking", "Materials processing", "Mineral processing"],
    SDE: ["Programming and data structures", "System design", "Competitive programming"],
    DA: ["Data analytics and dashboards", "SQL databases", "Probability and statistics"],
    AIML: ["Machine learning", "Deep learning", "Artificial intelligence"],
    HS_EE: ["Research in signals and systems", "Control systems", "Power systems research"],
    HS_MM: ["Research in physical metallurgy", "Thermodynamics of materials", "Corrosion and surface engineering"],
    MBA: ["Management and consulting", "Quantitative aptitude", "Operations and supply chain"],
    UPSC: ["Polity and governance", "Economy", "Current affairs"],
    STARTUP: ["Customer discovery", "MVP building", "Pitching and fundraising"],
}
# Primary assessed skill per goal (used for diagnostics and for the interest-vs-evidence clash)
GOAL_PRIMARY_SKILLS = {
    POWER: ["SKILL_CIRCUIT_ANALYSIS", "SKILL_ELECTRIC_MACHINES", "SKILL_POWER_ELECTRONICS"],
    VLSI: ["SKILL_DIGITAL_LOGIC", "SKILL_ANALOG_ELECTRONICS", "SKILL_VLSI_DESIGN"],
    MM_ADV: ["SKILL_PHYSICAL_METALLURGY", "SKILL_THERMODYNAMICS_MAT", "SKILL_MECHANICAL_BEHAVIOR"],
    MM_PROC: ["SKILL_THERMODYNAMICS_MAT", "SKILL_MATERIALS_PROCESSING", "SKILL_IRON_STEELMAKING"],
    SDE: ["SKILL_DATA_STRUCTURES_ALGO", "SKILL_PROGRAMMING_DS", "SKILL_DATABASES_SQL"],
    DA: ["SKILL_DATA_ANALYTICS", "SKILL_DATABASES_SQL", "SKILL_PROBABILITY_STATS"],
    AIML: ["SKILL_PROBABILITY_STATS", "SKILL_PROGRAMMING_DS", "SKILL_AI_ML"],
    HS_EE: ["SKILL_CIRCUIT_ANALYSIS", "SKILL_SIGNALS_SYSTEMS", "SKILL_CONTROL_SYSTEMS"],
    HS_MM: ["SKILL_PHYSICAL_METALLURGY", "SKILL_THERMODYNAMICS_MAT", "SKILL_MATERIALS_CHAR"],
    MBA: ["SKILL_QUANT_APTITUDE", "SKILL_VERBAL_ABILITY", "SKILL_DILR"],
    UPSC: ["SKILL_UPSC_GS2_POLITY_GOVERNANCE_IR", "SKILL_UPSC_CSAT", "SKILL_UPSC_GS3_ECONOMY"],
    STARTUP: ["SKILL_STARTUP_CUSTOMER_DISCOVERY", "SKILL_STARTUP_MVP_BUILD", "SKILL_STARTUP_BUSINESS_MODEL"],
}

# (student_id, persona, programme, semester, cgpa, backlogs, goal, tags, previous_goal, name or None)
LEGACY = [
    ("CONF_STU_EE_POWER_01", "ee_power_core", "BTECH_EE", 5, 8.2, 0, POWER, [], None, "Ananya Roy"),
    ("CONF_STU_EE_POWER_02", "ee_power_core", "BTECH_EE", 4, 7.5, 0, POWER, [], None, "Karthik Nair"),
    ("CONF_STU_EE_POWER_03", "ee_power_core", "BTECH_EE", 3, 8.8, 0, POWER, [], None, "Priya Das"),
    ("CONF_STU_EE_EDGE_BACKLOG", "ee_power_core", "BTECH_EE", 5, 6.8, 1, POWER, [BACKLOG], None, "Vikram Seth"),
    ("CONF_STU_EE_EDGE_CGPA_CUTOFF", "ee_power_core", "BTECH_EE", 5, 7.95, 0, POWER, [MINOR_CUT], None, "Sneha Patel"),
    ("CONF_STU_EE_EDGE_GOAL_PIVOT", "ee_power_core", "BTECH_EE", 4, 8.4, 0, POWER, [SWITCH], VLSI, "Rahul Verma"),
    ("CONF_STU_EE_EDGE_CONFLICT", "ee_power_core", "BTECH_EE", 3, 7.6, 0, POWER, [CLASH], None, "Tanvi Sen"),
    ("CONF_STU_MME_PROCESS_01", "mme_materials_core", "BTECH_MM", 5, 8.25, 0, MM_PROC, [], None, "Rohan Sharma"),
    ("CONF_STU_MME_PROCESS_02", "mme_materials_core", "BTECH_MM", 4, 7.80, 0, MM_PROC, [], None, "Ananya Ghosh"),
    ("CONF_STU_MME_PROCESS_03", "mme_materials_core", "BTECH_MM", 3, 8.60, 0, MM_ADV, [], None, "Vikram Iyer"),
    ("CONF_STU_UPSC_01", "btech_upsc", "BTECH_EE", 3, 8.2, 0, UPSC, [], None, "Aarav Sharma"),
    ("CONF_STU_UPSC_02", "btech_upsc", "BTECH_MM", 6, 7.4, 0, UPSC, [], None, "Ananya Mishra"),
    ("CONF_STU_UPSC_03", "btech_upsc", "BTECH_EE", 8, 7.9, 0, UPSC, [], None, "Rohan Verma"),
    ("CONF_STU_STARTUP_01", "student_startup", "BTECH_EE", 3, 8.2, 0, STARTUP, [], None, "Aarav Sharma"),
    ("CONF_STU_STARTUP_02", "student_startup", "BTECH_MM", 6, 7.4, 0, STARTUP, [], None, "Ananya Mishra"),
    ("CONF_STU_STARTUP_03", "student_startup", "BTECH_EE", 8, 7.9, 0, STARTUP, [], None, "Rohan Verma"),
]
E, M = "BTECH_EE", "BTECH_MM"
NEW = [
    # ---- Core EE (+5)
    ("ee_power_core", E, 1, 8.6, POWER, [], None), ("ee_power_core", E, 2, 7.2, POWER, [TIGHT_H], None),
    ("ee_power_core", E, 6, 8.00, VLSI, [MINOR_CUT], None), ("ee_power_core", E, 7, 6.4, POWER, [BACKLOG], None),
    ("ee_power_core", E, 8, 9.1, VLSI, [], None),
    # ---- Core MME (+6)
    ("mme_materials_core", M, 1, 7.9, MM_ADV, [], None), ("mme_materials_core", M, 2, 8.4, MM_PROC, [], None),
    ("mme_materials_core", M, 6, 7.99, MM_ADV, [MINOR_CUT], None), ("mme_materials_core", M, 7, 6.1, MM_PROC, [BACKLOG, TIGHT_C], None),
    ("mme_materials_core", M, 8, 8.7, MM_ADV, [], None), ("mme_materials_core", M, 5, 7.0, MM_ADV, [CLASH], None),
    # ---- SDE (10)
    ("sde_career", E, 1, 8.9, SDE, [], None), ("sde_career", E, 3, 8.3, SDE, [CLASH], None),
    ("sde_career", E, 4, 7.6, SDE, [SWITCH], POWER), ("sde_career", E, 5, 8.00, SDE, [MINOR_CUT], None),
    ("sde_career", E, 6, 6.9, SDE, [BACKLOG], None), ("sde_career", E, 7, 8.50, SDE, [OVER_CUT, TIGHT_H], None),
    ("sde_career", M, 2, 7.4, SDE, [], None), ("sde_career", M, 4, 8.1, SDE, [SWITCH], MM_PROC),
    ("sde_career", M, 5, 7.7, SDE, [TIGHT_H], None), ("sde_career", M, 8, 8.2, SDE, [TIGHT_C], None),
    # ---- Data Analyst (8)
    ("da_career", E, 2, 7.8, DA, [TIGHT_C], None), ("da_career", E, 3, 6.7, DA, [CLASH], None),
    ("da_career", E, 5, 8.01, DA, [MINOR_CUT], None), ("da_career", E, 6, 7.3, DA, [SWITCH], VLSI),
    ("da_career", M, 3, 8.50, DA, [OVER_CUT], None), ("da_career", M, 4, 7.1, DA, [TIGHT_H], None),
    ("da_career", M, 6, 6.5, DA, [BACKLOG], None), ("da_career", M, 7, 8.3, DA, [SWITCH], MM_ADV),
    # ---- AI/ML (8)
    ("aiml_career", E, 1, 9.3, AIML, [], None), ("aiml_career", E, 4, 8.8, AIML, [], None),
    ("aiml_career", E, 5, 7.99, AIML, [MINOR_CUT, CLASH], None), ("aiml_career", E, 7, 7.5, AIML, [SWITCH, TIGHT_H], POWER),
    ("aiml_career", M, 2, 8.0, AIML, [], None), ("aiml_career", M, 3, 7.2, AIML, [CLASH], None),
    ("aiml_career", M, 5, 8.6, AIML, [TIGHT_C], None), ("aiml_career", M, 8, 6.8, AIML, [BACKLOG], None),
    # ---- Higher studies (8)
    ("core_higher_studies", E, 3, 9.0, HS_EE, [], None), ("core_higher_studies", E, 5, 8.49, HS_EE, [OVER_CUT], None),
    ("core_higher_studies", E, 6, 7.7, HS_EE, [CLASH], None), ("core_higher_studies", E, 7, 8.4, HS_EE, [TIGHT_H], None),
    ("core_higher_studies", M, 4, 8.9, HS_MM, [], None), ("core_higher_studies", M, 5, 8.00, HS_MM, [MINOR_CUT], None),
    ("core_higher_studies", M, 6, 7.4, HS_MM, [SWITCH], MM_PROC), ("core_higher_studies", M, 8, 8.1, HS_MM, [], None),
    # ---- MBA (7)
    ("core_to_mba", E, 4, 7.9, MBA, [], None), ("core_to_mba", E, 5, 8.2, MBA, [SWITCH], POWER),
    ("core_to_mba", E, 7, 7.0, MBA, [TIGHT_H], None), ("core_to_mba", E, 8, 8.6, MBA, [], None),
    ("core_to_mba", M, 3, 7.6, MBA, [CLASH], None), ("core_to_mba", M, 6, 6.6, MBA, [BACKLOG], None),
    ("core_to_mba", M, 7, 8.4, MBA, [TIGHT_C], None),
    # ---- UPSC (+4)
    ("btech_upsc", E, 1, 8.1, UPSC, [], None), ("btech_upsc", E, 5, 7.2, UPSC, [TIGHT_H], None),
    ("btech_upsc", M, 2, 7.0, UPSC, [], None), ("btech_upsc", M, 4, 6.3, UPSC, [BACKLOG], None),
    # ---- Startup (+3)
    ("student_startup", E, 5, 8.50, STARTUP, [OVER_CUT, SWITCH], SDE), ("student_startup", M, 3, 7.8, STARTUP, [TIGHT_C], None),
    ("student_startup", M, 1, 8.3, STARTUP, [], None),
]
LEGACY_BACKLOG_COURSE = {"CONF_STU_EE_EDGE_BACKLOG": "EE2L003"}


def build():
    planner = Planner()
    catalogue = planner.course_info
    course_skill_level = {}
    with open(os.path.join("data", "seed", "kb", "course_skill.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            course_skill_level[(r["course_id"], r["skill_id"])] = float(r["level_taught"])
    valid_skills = set()
    with open(os.path.join("data", "seed", "kb", "skill.csv"), encoding="utf-8") as f:
        valid_skills = {r["skill_id"] for r in csv.DictReader(f)}

    specs = []
    used_names = {l[9] for l in LEGACY}
    for sid, persona, prog, sem, cgpa, backlogs, goal, tags, prev, name in LEGACY:
        specs.append(dict(student_id=sid, persona=persona, prog=prog, sem=sem, cgpa=cgpa, backlogs=backlogs,
                          goal=goal, tags=list(tags), prev=prev, name=name, legacy=True))
    name_rng = random.Random(SEED)
    for idx, (persona, prog, sem, cgpa, goal, tags, prev) in enumerate(NEW, start=1):
        while True:
            name = f"{name_rng.choice(FIRST)} {name_rng.choice(LAST)}"
            if name not in used_names:
                used_names.add(name)
                break
        sid = f"SYN_{'EE' if prog == E else 'MM'}_S{sem}_{idx:03d}"
        specs.append(dict(student_id=sid, persona=persona, prog=prog, sem=sem, cgpa=cgpa,
                          backlogs=1 if BACKLOG in tags else 0, goal=goal, tags=list(tags), prev=prev, name=name, legacy=False))
    assert len(specs) == 75, len(specs)
    assert len({s["student_id"] for s in specs}) == 75

    out = dict(student=[], completed=[], goal=[], interest=[], evidence=[], constraint=[], preference=[], rosters={})

    for n, sp in enumerate(specs):
        rng = random.Random(SEED * 1000 + n)
        sid, prog, sem, cgpa, goal, tags = sp["student_id"], sp["prog"], sp["sem"], sp["cgpa"], sp["goal"], sp["tags"]
        fy_track = "A" if n % 3 else "B"
        if sp["legacy"]:
            fy_track = "A"

        # ---------------- transcript: all mandatory courses of earlier semesters + one option per enumerated slot
        transcript = []  # (course_id, semester)
        for s in range(1, sem):
            for r in planner.mandatory_courses(prog, s, fy_track, include_assumed=True):
                transcript.append((r["course_id"].strip(), s))
            for r in planner.slot_rows(prog, s):
                opts = sorted(planner.slot_options.get(r["slot_id"].strip(), []))
                opts = [o for o in opts if o not in {c for c, _ in transcript}
                        and all(p in {c for c, _ in transcript} for p in planner.rule_engine.prereqs.get(o, set()))]
                if opts:
                    transcript.append((rng.choice(opts), s))
        seen, uniq = set(), []
        for c, s in transcript:
            if c not in seen:
                seen.add(c)
                uniq.append((c, s))
        transcript = uniq

        backlog_courses = []
        if sp["backlogs"] > 0:
            if sid in LEGACY_BACKLOG_COURSE:
                backlog_courses = [LEGACY_BACKLOG_COURSE[sid]]
            else:
                # a theory course (code kind 'L') of an earlier, non-first-year semester whenever possible
                # backlogs are mandatory courses only (an elective option is replaced, not carried as a backlog)
                mand = {r["course_id"].strip() for s2 in range(1, sem) for r in planner.mandatory_courses(prog, s2, fy_track)}
                cands = [c for c, s in transcript if c in mand and len(c) > 3 and c[3] == "L" and s >= min(3, sem - 1)]
                cands = cands or [c for c, s in transcript if c in mand and len(c) > 3 and c[3] == "L"]
                # never pick a course that another already-passed course depends on (transcripts stay consistent)
                deps = {p for c, _ in transcript for p in planner.rule_engine.prereqs.get(c, set())}
                safe = [c for c in cands if c not in deps] or cands
                backlog_courses = [sorted(safe)[rng.randrange(len(safe))]]
            assert all(b in {c for c, _ in transcript} for b in backlog_courses), (sid, backlog_courses)

        # ---------------- grades consistent with the stated CGPA (credit-weighted mean within 0.05)
        passed = [(c, s) for c, s in transcript if c not in backlog_courses]
        points = {}
        for c, _s in passed:
            points[c] = max(5, min(10, int(round(cgpa + rng.gauss(0, 0.9)))))

        def mean_pts():
            tot = sum(catalogue[c]["credits"] for c, _ in passed) or 1.0
            return sum(points[c] * catalogue[c]["credits"] for c, _ in passed) / tot

        order = [c for c, _ in passed]
        guard = 0
        while passed and abs(mean_pts() - cgpa) > 0.05 and guard < 400:
            guard += 1
            c = order[guard % len(order)]
            if mean_pts() < cgpa and points[c] < 10:
                points[c] += 1
            elif mean_pts() > cgpa and points[c] > 5:
                points[c] -= 1
        letter = {v: k for k, v in GRADE_POINTS}
        for c, s in transcript:
            if c in backlog_courses:
                out["completed"].append(dict(student_id=sid, course_id=c, grade="F", semester=s, is_backlog="TRUE"))
            else:
                out["completed"].append(dict(student_id=sid, course_id=c, grade=letter[points[c]], semester=s, is_backlog="FALSE"))

        # ---------------- goals (active + previous for switchers)
        switch_sem = max(2, sem - 1) if sp["prev"] else None
        out["goal"].append(dict(student_id=sid, goal_id=goal, priority=1, target_date="", status="active",
                                since_semester=switch_sem or 1))
        if sp["prev"]:
            out["goal"].append(dict(student_id=sid, goal_id=sp["prev"], priority=2, target_date="", status="previous",
                                    since_semester=1))

        # ---------------- declared interests (WEAK evidence)
        topics = GOAL_INTERESTS[goal]
        k = 3 if CLASH in tags else 2
        interests = []
        for i, t in enumerate(topics[:k]):
            w = 1.0 if (i == 0 and CLASH in tags) else round(0.9 - 0.2 * i, 2)
            interests.append((t, w))
            out["interest"].append(dict(student_id=sid, topic=t, weight=w, reliability_tier="weak",
                                        declared_strength="strong" if w >= 0.9 else "moderate"))

        # ---------------- evidence ledger
        ev_n = 0

        def add_ev(skill, source, score, tier, note, day):
            nonlocal ev_n
            assert skill in valid_skills, skill
            ev_n += 1
            out["evidence"].append(dict(
                student_id=sid, skill_id=skill, source_type=source, score=round(max(0.0, min(100.0, score)), 1),
                recorded_at=f"2026-{8 + (day // 28) % 3:02d}-{1 + day % 28:02d}T09:00:00+00:00",
                reliability_tier=tier, notes=note))

        # (a) course grades -> STRONG: per skill, the highest-level passed course supersedes earlier ones
        best = {}
        for c, _s in passed:
            for (cc, sk), lvl in course_skill_level.items():
                if cc == c and (sk not in best or lvl > best[sk][0]):
                    best[sk] = (lvl, c)
        for sk in sorted(best):
            lvl, c = best[sk]
            add_ev(sk, "course_grade", lvl * points[c] / 10.0, "strong",
                   f"Grade {letter[points[c]]} in {c} (course teaches this skill up to level {lvl:.0f})", 3)

        # (b) adaptive diagnostic -> STRONG (most students from Sem 2 onward; every clash profile)
        ability = max(22.0, min(92.0, 38.0 + (cgpa - 6.0) * 13.0))
        prim = GOAL_PRIMARY_SKILLS[goal]
        took_diag = CLASH in tags or (sem >= 2 and n % 4 != 3)
        if took_diag:
            for i, sk in enumerate(prim[:2 if sem < 5 else 3]):
                if CLASH in tags and i == 0:
                    score = 24.0 + rng.random() * 12.0          # weak assessed result on the declared interest area
                else:
                    score = ability + rng.gauss(0, 7.0) - 4.0 * i
                add_ev(sk, "diagnostic", score, "strong", "Adaptive diagnostic (onboarding)", 20 + i)

        # (c) self-declared self-rating -> WEAK (never enough on its own)
        if CLASH in tags:
            add_ev(prim[0], "self_declaration", 88.0, "weak", f"Self-rated strong interest: {interests[0][0]}", 1)
        elif n % 2 == 0:
            add_ev(prim[min(1, len(prim) - 1)], "self_declaration", 65.0 + (n % 5) * 5, "weak",
                   f"Self-rating at onboarding: {interests[0][0]}", 1)

        # (d) seniors with demonstrated-proficiency evidence (timed quiz / rubric project / mock interview)
        if sem >= 6 and n % 3 == 0 and CLASH not in tags:
            add_ev(prim[0], "timed_quiz", ability + 6.0, "strong", "Timed checkpoint quiz", 40)
            add_ev(prim[0], "project_rubric", ability + 2.0, "strong", "Rubric-scored project", 55)
        if sem >= 7 and n % 4 == 0 and CLASH not in tags:
            add_ev(prim[0], "mock_interview", ability - 3.0, "strong", "Mock interview (rubric)", 70)
        # (e) untimed practice -> MEDIUM
        if sem >= 3 and n % 5 == 1:
            add_ev(prim[-1], "exercise", ability - 5.0, "medium", "Untimed practice set", 30)

        # ---------------- constraints
        if TIGHT_H in tags:
            weekly = float(6 + n % 4)                      # 6..9 h
        else:
            weekly = float(12 + (n * 7) % 12)              # 12..23 h
        out["constraint"].append(dict(student_id=sid, constraint_type="weekly_hours",
                                      parameters=json.dumps({"max_hours": weekly}, sort_keys=True)))
        credit_cap = None
        if TIGHT_C in tags:
            credit_cap = 24.0 if prog == E else 18.0
            out["constraint"].append(dict(student_id=sid, constraint_type="credit_cap",
                                          parameters=json.dumps({"max_credits": credit_cap}, sort_keys=True)))

        out["preference"].append(dict(student_id=sid,
                                      preferred_learning_mode=["video_heavy", "balanced", "project_oriented", "text_heavy"][n % 4],
                                      pace=["standard", "steady", "accelerated"][n % 3]))

        aims = f"I want to work towards {interests[0][0].lower()}."
        year = (sem + 1) // 2
        out["student"].append(dict(
            student_id=sid, programme_id=prog, year=year, current_semester=sem, cgpa=f"{cgpa:.2f}",
            is_synthetic="TRUE", persona_tag=sp["persona"], name=sp["name"], backlogs=sp["backlogs"],
            first_year_track=fy_track, edge_case_tags=";".join(tags), aims=aims))

        out["rosters"].setdefault(sp["persona"], []).append(dict(
            student_id=sid, name=sp["name"], programme_id=prog, current_semester=sem,
            cgpa=(f"{cgpa:.2f}" if not sp["legacy"] else str(cgpa)), backlogs=sp["backlogs"],
            completed_courses=";".join(c for c, _ in passed), is_synthetic="True",
            year=year, goal_id=goal, first_year_track=fy_track, weekly_hours_cap=weekly,
            credit_cap=credit_cap if credit_cap is not None else "", edge_case_tags=";".join(tags),
            interests="|".join(f"{t}:{w}" for t, w in interests), previous_goal_id=sp["prev"] or "",
            backlog_courses=";".join(backlog_courses), aims=aims))

    # ---------------- integrity: zero unknown course codes
    unknown = sorted({r["course_id"] for r in out["completed"] if r["course_id"] not in catalogue})
    assert not unknown, f"Unknown course codes in generated transcripts: {unknown}"
    return specs, out


FILES = {
    "student": ("student.csv", ["student_id", "programme_id", "year", "current_semester", "cgpa", "is_synthetic", "persona_tag",
                                "name", "backlogs", "first_year_track", "edge_case_tags", "aims"]),
    "completed": ("completed_course.csv", ["student_id", "course_id", "grade", "semester", "is_backlog"]),
    "goal": ("student_goal.csv", ["student_id", "goal_id", "priority", "target_date", "status", "since_semester"]),
    "interest": ("interest.csv", ["student_id", "topic", "weight", "reliability_tier", "declared_strength"]),
    "evidence": ("skill_evidence.csv", ["student_id", "skill_id", "source_type", "score", "recorded_at", "reliability_tier", "notes"]),
    "constraint": ("constraint.csv", ["student_id", "constraint_type", "parameters"]),
    "preference": ("preference.csv", ["student_id", "preferred_learning_mode", "pace"]),
}
ROSTER_COLS = ["student_id", "name", "programme_id", "current_semester", "cgpa", "backlogs", "completed_courses", "is_synthetic",
               "year", "goal_id", "first_year_track", "weekly_hours_cap", "credit_cap", "edge_case_tags", "interests",
               "previous_goal_id", "backlog_courses", "aims"]


def render(specs, out):
    """Returns {relative_path: text} for every file the generator owns."""
    import io
    files = {}

    def to_csv(cols, rows):
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        return buf.getvalue()

    for key, (fname, cols) in FILES.items():
        files[os.path.join(STUDENT_DIR, fname)] = to_csv(cols, out[key])
    for persona, rows in sorted(out["rosters"].items()):
        files[os.path.join(PERSONA_DIR, persona, "students.csv")] = to_csv(ROSTER_COLS, rows)

    tag_counts, by_goal, by_prog, by_year, by_persona = {}, {}, {}, {}, {}
    for sp in specs:
        for t in sp["tags"]:
            tag_counts[t] = tag_counts.get(t, 0) + 1
        by_goal[sp["goal"]] = by_goal.get(sp["goal"], 0) + 1
        by_prog[sp["prog"]] = by_prog.get(sp["prog"], 0) + 1
        y = f"year_{(sp['sem'] + 1) // 2}"
        by_year[y] = by_year.get(y, 0) + 1
        by_persona[sp["persona"]] = by_persona.get(sp["persona"], 0) + 1
    tiers = {}
    for e in out["evidence"]:
        tiers[e["reliability_tier"]] = tiers.get(e["reliability_tier"], 0) + 1
    manifest = {
        "generator": "scripts/generate_75_student_profiles.py", "seed": SEED, "total_profiles": len(specs),
        "is_synthetic": True, "contains_real_student_data": False,
        "by_programme": dict(sorted(by_prog.items())), "by_year": dict(sorted(by_year.items())),
        "by_persona": dict(sorted(by_persona.items())), "by_goal": dict(sorted(by_goal.items())),
        "edge_case_counts": dict(sorted(tag_counts.items())),
        "evidence_rows_by_reliability_tier": dict(sorted(tiers.items())),
        "rows": {k: len(v) for k, v in out.items() if k != "rosters"},
        "grading_scale_assumed": "EX=10, A=9, B=8, C=7, D=6, P=5, F=0 (design assumption; confirm with institute regulations)",
        "notes": [
            "The KB holds no sourced honours rule; the honours-type cutoff is represented by the 8.50 overload threshold "
            "of RULE_SEM_CREDIT_CAP_REGULAR (unsourced baseline).",
            "MME first-year courses are the institute common core assumed from the EE curriculum document (MME document omits Sem I-II).",
        ],
    }
    files[os.path.join(STUDENT_DIR, "profile_manifest.json")] = json.dumps(manifest, indent=2, sort_keys=False) + "\n"
    return files, manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify the files on disk match the generator output")
    args = ap.parse_args()
    specs, out = build()
    files, manifest = render(specs, out)
    if args.check:
        bad = []
        for path, text in files.items():
            if not os.path.exists(path) or open(path, encoding="utf-8", newline="").read() != text:
                bad.append(path)
        if bad:
            print("OUT OF DATE:\n  " + "\n  ".join(bad))
            return 1
        print(f"OK: {len(files)} generated files match the deterministic generator.")
        return 0
    for path, text in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    print(f"Wrote {len(files)} files for {manifest['total_profiles']} synthetic profiles.")
    print("  by programme :", manifest["by_programme"])
    print("  by year      :", manifest["by_year"])
    print("  by persona   :", manifest["by_persona"])
    print("  edge cases   :", manifest["edge_case_counts"])
    print("  evidence     :", manifest["evidence_rows_by_reliability_tier"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
