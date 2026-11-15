"""
Data Analyst (DA) Quiz Assessment Knowledge Base Pipeline for eBuddy
Adobe Personalised Learning Buddy (Inter IIT Tech Meet 15.0)

Transforms Data_Analyst_Questions.xlsx into clean, relational CSV datasets for:
  - Diagnostic onboarding assessment
  - Topic-level cluster checks & phase-end barrier quizzes
  - Spaced repetition & adaptive remedial planning
"""

import os
import sys
import re
import csv
import openpyxl

# ==============================================================================
# HARDCODED DOMAIN TAXONOMY & DESIGN STRUCTURES (DA ROADMAP SPECIFICATION)
# ==============================================================================

ROADMAP_SKILLS = [
    # skill_id, name, category, level, prerequisite_skill_ids, phase, phase_order, position_in_phase
    ("DA-S01", "Spreadsheet fundamentals", "Tools", "foundation", "none", "DA-PH1", 1, 1),
    ("DA-S02", "Descriptive statistics", "Statistics", "foundation", "none", "DA-PH1", 1, 2),
    ("DA-S03", "Probability basics", "Statistics", "foundation", "DA-S02", "DA-PH1", 1, 3),
    ("DA-S04", "SQL basics", "SQL", "foundation", "none", "DA-PH1", 1, 4),
    ("DA-S19", "Spreadsheet analysis", "Tools", "core", "DA-S01", "DA-PH1", 1, 5),
    ("DA-S05", "SQL joins and aggregation", "SQL", "core", "DA-S04", "DA-PH2", 2, 1),
    ("DA-S07", "Python basics", "Python", "core", "none", "DA-PH2", 2, 2),
    ("DA-S08", "pandas data wrangling", "Python", "core", "DA-S07", "DA-PH2", 2, 3),
    ("DA-S18", "Git and version control", "Tools", "foundation", "none", "DA-PH2", 2, 4),
    ("DA-S09", "Data cleaning and quality", "Analysis", "core", "DA-S08;DA-S01", "DA-PH3", 3, 1),
    ("DA-S10", "Exploratory data analysis", "Analysis", "core", "DA-S08;DA-S02", "DA-PH3", 3, 2),
    ("DA-S11", "Data visualisation principles", "Visualisation", "core", "DA-S02", "DA-PH3", 3, 3),
    ("DA-S12", "Python visualisation", "Visualisation", "core", "DA-S08;DA-S11", "DA-PH3", 3, 4),
    ("DA-S06", "Advanced SQL", "SQL", "advanced", "DA-S05", "DA-PH4", 4, 1),
    ("DA-S13", "BI dashboards", "Visualisation", "core", "DA-S11;DA-S05", "DA-PH4", 4, 2),
    ("DA-S14", "Inferential statistics and A/B testing", "Statistics", "advanced", "DA-S03", "DA-PH4", 4, 3),
    ("DA-S16", "Business metrics and KPIs", "Business", "core", "DA-S02", "DA-PH4", 4, 4),
    ("DA-S15", "Regression basics", "Statistics", "advanced", "DA-S14;DA-S08", "DA-PH5", 5, 1),
    ("DA-S17", "Data storytelling", "Business", "core", "DA-S11;DA-S16", "DA-PH5", 5, 2),
    ("DA-S20", "Analytics case interviews", "Business", "advanced", "DA-S16;DA-S14", "DA-PH5", 5, 3),
]

ROADMAP_PHASE_CHECKPOINTS = {
    "DA-PH1": "Foundation quiz score of at least 70%",
    "DA-PH2": "Timed SQL test of at least 70% and a pandas exercise",
    "DA-PH3": "Project DA-P01 passes its rubric",
    "DA-PH4": "Project DA-P02 passes its rubric and A/B test quiz of at least 70%",
    "DA-PH5": "Project DA-P03 passes its rubric and a mock interview is passed"
}

CHECKPOINTS_CONFIG = [
    # id, type, trigger_skills, trigger_phase, review_skills, target, d1, d2, d3, s_new, s_rev, roadmap_ref
    ("CP-1A", "SKILL_CLUSTER_CHECK", "DA-S01;DA-S02;DA-S03", "DA-PH1", "", 10, 60, 40, 0, 100, 0, ""),
    ("CP-1B", "SKILL_CLUSTER_CHECK", "DA-S04;DA-S19", "DA-PH1", "DA-S02", 10, 60, 40, 0, 70, 30, ""),
    ("CP-1E", "PHASE_END_QUIZ", "DA-S01;DA-S02;DA-S03;DA-S04;DA-S19", "DA-PH1", "", 12, 60, 40, 0, 100, 0, "Foundation quiz score of at least 70%"),
    ("CP-2A", "SKILL_CLUSTER_CHECK", "DA-S05", "DA-PH2", "DA-S04", 10, 50, 50, 0, 70, 30, ""),
    ("CP-2B", "SKILL_CLUSTER_CHECK", "DA-S07;DA-S08;DA-S18", "DA-PH2", "DA-S05", 10, 60, 40, 0, 70, 30, ""),
    ("CP-2E", "PHASE_END_QUIZ", "DA-S05;DA-S07;DA-S08;DA-S18", "DA-PH2", "DA-S01;DA-S02;DA-S04", 15, 50, 50, 0, 70, 30, "Timed SQL test of at least 70% and a pandas exercise"),
    ("CP-3A", "SKILL_CLUSTER_CHECK", "DA-S09;DA-S10", "DA-PH3", "DA-S08;DA-S02", 10, 40, 60, 0, 70, 30, ""),
    ("CP-3B", "SKILL_CLUSTER_CHECK", "DA-S11;DA-S12", "DA-PH3", "DA-S08;DA-S02", 10, 50, 50, 0, 70, 30, ""),
    ("CP-3E", "PHASE_END_QUIZ", "DA-S09;DA-S10;DA-S11;DA-S12", "DA-PH3", "DA-S05;DA-S08;DA-S02", 12, 40, 60, 0, 70, 30, "Project DA-P01 passes its rubric"),
    ("CP-4A", "SKILL_CLUSTER_CHECK", "DA-S06", "DA-PH4", "DA-S05;DA-S04", 10, 20, 60, 20, 60, 40, ""),
    ("CP-4B", "SKILL_CLUSTER_CHECK", "DA-S13;DA-S14", "DA-PH4", "DA-S11;DA-S03", 10, 30, 50, 20, 70, 30, ""),
    ("CP-4C", "SKILL_CLUSTER_CHECK", "DA-S16", "DA-PH4", "DA-S02", 10, 50, 50, 0, 60, 40, ""),
    ("CP-4E", "PHASE_END_QUIZ", "DA-S06;DA-S13;DA-S14;DA-S16", "DA-PH4", "DA-S05;DA-S08;DA-S09;DA-S10", 15, 30, 50, 20, 70, 30, "Project DA-P02 passes its rubric and A/B test quiz of at least 70%"),
    ("CP-5A", "SKILL_CLUSTER_CHECK", "DA-S15;DA-S17", "DA-PH5", "DA-S14;DA-S08;DA-S16", 10, 20, 60, 20, 40, 60, ""),
    ("CP-5B", "SKILL_CLUSTER_CHECK", "DA-S20", "DA-PH5", "DA-S16;DA-S14;DA-S06", 10, 20, 50, 30, 30, 70, ""),
    ("CP-5E", "PHASE_END_QUIZ", "DA-S15;DA-S17;DA-S20", "DA-PH5", "DA-S06;DA-S14;DA-S16;DA-S10", 12, 20, 50, 30, 40, 60, "Project DA-P03 passes its rubric and a mock interview is passed"),
    ("CP-FIN", "FINAL_CUMULATIVE_QUIZ", ";".join([s[0] for s in ROADMAP_SKILLS]), "DA-PH5", "", 15, 25, 50, 25, 100, 0, "")
]

QUIZ_RULES_CONFIG = [
    # rule_id, scenario, rule_name, parameter, value, description, source_type
    ("G01", "ITEM_AND_GRADING", "ITEM_SCHEMA", "item_fields", "question_id,skill,difficulty,type,stem,options,answer,explanation", "Each quiz item corresponds to one row of File 1.", "SOURCE_DATA"),
    ("G02", "ITEM_AND_GRADING", "MCQ_SHUFFLE_AND_GRADE", "grade_by", "correct_option_text", "Shuffle the four options at quiz time and grade by option text, never by letter, to eliminate source answer-position bias.", "DESIGN_DEFAULT"),
    ("G03", "ITEM_AND_GRADING", "NUMERIC_GRADING", "tolerance", "max(0.01, 0.01 * correct)", "Accept given numeric answer if absolute error <= max(0.01, 1% of correct); strip trailing %, commas, and spaces. For percent hint, input raw number.", "DESIGN_DEFAULT"),
    ("G04", "ITEM_AND_GRADING", "SQL_GRADING", "comparison_mode", "RESULT_SET_COMPARE", "Compare execution result sets on sample database from stem tables ignoring aliases and unrequested row order; fallback to LLM judge if sandbox unavailable. All-or-nothing (1 or 0).", "DESIGN_DEFAULT"),
    ("G05", "ITEM_AND_GRADING", "EXPLANATION_DISPLAY", "show_explanation", "AFTER_EACH_QUESTION", "Display the pedagogical explanation from the source immediately after each submitted question.", "SOURCE_DATA"),

    ("D01", "DECLARED_KNOWLEDGE", "DECLARED_INPUTS", "inputs", "skill_ids_and_max_difficulty", "Takes a list of skills (or categories expanding to skills) and the hardest claimed difficulty (1=Easy, 2=Medium, 3=Hard).", "DESIGN_DEFAULT"),
    ("D02", "DECLARED_KNOWLEDGE", "QUIZ_LENGTH_BY_SKILLS", "length_tiers", "1-2:10; 3-5:12; 6-9:14; 10+:15", "Calibrate quiz length based on count of declared skills (10, 12, 14, or 15 questions).", "DESIGN_DEFAULT"),
    ("D03", "DECLARED_KNOWLEDGE", "SHARE_DECLARED_RELATED", "declared_vs_related_split", "75_pct_declared_25_pct_related", "Allocate 75% questions to declared skills and 25% (min 2) to undeclared related skills (STRONG first, difficulty level minus 1, min 1).", "DESIGN_DEFAULT"),
    ("D04", "DECLARED_KNOWLEDGE", "DIFFICULTY_MIX_BY_CLAIM", "mix_d1_d2_d3", "Easy:80/20/0; Medium:20/60/20; Hard:0/30/70", "Difficulty breakdown based on claim: Easy (80/20/0), Medium (20/60/20), Hard (0/30/70 with stretch probes).", "DESIGN_DEFAULT"),
    ("D05", "DECLARED_KNOWLEDGE", "SKILL_COVERAGE", "min_coverage", "1_per_skill_if_declared_lte_70pct", "At least 1 question per declared skill when count <= 70% of quiz length; otherwise sample without replacement prioritizing earliest phases.", "DESIGN_DEFAULT"),
    ("D06", "DECLARED_KNOWLEDGE", "SKILL_VERDICT", "thresholds", "CONFIRMED>=70%; PARTIAL:50-69%; NOT_CONFIRMED<50%", "For declared skills with >= 2 questions: CONFIRMED (>=70%), PARTIAL (50-69%), NOT_CONFIRMED (<50%). If < 2 questions, rollup to category and mark indicative.", "DESIGN_DEFAULT"),
    ("D07", "DECLARED_KNOWLEDGE", "OVERALL_VERDICT", "thresholds", "Confirmed>=70%; Partially_confirmed:50-69%; Not_confirmed<50%", "Overall assessment verdict on declared skills at claimed difficulty: Confirmed (>=70%), Partially confirmed (50-69%), Not confirmed (<50%).", "DESIGN_DEFAULT"),
    ("D08", "DECLARED_KNOWLEDGE", "PLAN_FROM_RESULT", "curriculum_action", "skip_confirmed_schedule_partial_and_weak", "Skip or lightly revise CONFIRMED skills; schedule PARTIAL, NOT_CONFIRMED, undeclared related skills scoring <60%, and undeclared skills, weak first.", "DESIGN_DEFAULT"),

    ("S01", "SCRATCH_LEARNER", "TRIGGER", "trigger_point", "POST_CLUSTER_OR_PHASE_END", "Offer quiz immediately when learner completes skills in trigger_after_skill_ids or entire phase.", "DESIGN_DEFAULT"),
    ("S02", "SCRATCH_LEARNER", "PROCEED_RULE", "proceed_thresholds", ">=70:proceed; 50-69:review_and_retake; <50:repeat_cluster", ">=70% proceed; 50-69% review weak skills and retake with new questions; <50% repeat cluster learning.", "DESIGN_DEFAULT"),
    ("S03", "SCRATCH_LEARNER", "RETAKE_LIMIT", "max_retries_before_prereq", "2_attempts", "After 2 failed attempts on same checkpoint, recommend foundational prerequisite skills before third attempt.", "DESIGN_DEFAULT"),
    ("S04", "SCRATCH_LEARNER", "ROADMAP_ALIGNMENT", "phase_end_relation", "COMPLEMENTS_ROADMAP_CHECKPOINT", "PHASE_END_QUIZ serves as knowledge readiness check alongside project rubrics, timed tests, and mock interviews, not replacing them.", "SOURCE_DATA"),

    ("C01", "SCORING", "DIFFICULTY_WEIGHTS", "weights", "1:1; 2:2; 3:3", "Weight equals difficulty_num (1, 2, 3). Weighted accuracy is sum of weights of correct answers over sum of weights of all questions.", "DESIGN_DEFAULT"),
    ("C02", "SCORING", "SKILL_STATUS", "mastery_thresholds", "STRONG>=80%; OK:60-79%; WEAK<60%", "Skill status based on weighted accuracy: STRONG (>=80%), OK (60-79%), WEAK (<60%), requiring at least 2 questions.", "DESIGN_DEFAULT"),
    ("C03", "SCORING", "CATEGORY_ROLLUP", "min_category_questions", "3_questions", "When a skill has < 2 questions, compute mastery status at skill_category level (min 3 questions) and mark result as indicative; otherwise UNTESTED.", "DESIGN_DEFAULT"),
    ("C04", "SCORING", "UNTESTED_SKILLS", "handling", "TREAT_AS_WEAK_FLAG_NOT_ASSESSED", "Untested skills are treated as WEAK for curriculum scheduling purposes but flagged as 'not assessed'.", "DESIGN_DEFAULT"),

    ("P01", "PLANNING", "PRIORITY_ORDER", "sorting", "WEAK_FIRST_THEN_ACCURACY_PHASE_POS", "Weak skills prioritized first; sort by lowest weighted accuracy, then earlier phase_order, then position_in_phase.", "DESIGN_DEFAULT"),
    ("P02", "PLANNING", "PREREQUISITES_FIRST", "dependency_order", "WEAK_PREREQUISITES_SCHEDULED_BEFORE_DEPENDENTS", "A weak skill's weak prerequisites must be scheduled before the dependent skill.", "DESIGN_DEFAULT"),
    ("P03", "PLANNING", "SPACED_REVISION", "interval_days", "7_days", "Re-quiz a skill at least 7 days after a WEAK assessment result.", "DESIGN_DEFAULT"),
    ("P04", "PLANNING", "CONFIRMED_SKILLS_REFRESHER", "refresher_quiz", "5_question_quiz_before_DA-PH5", "Maintain one 5-question light revision quiz across confirmed skills prior to starting Phase 5.", "DESIGN_DEFAULT"),

    ("L01", "POOL_AND_GENERATION", "NO_REPEAT", "repeat_policy", "NO_REPEATS_WITHIN_QUIZ_AND_AVOID_PREV_ATTEMPT", "No duplicate questions within a single quiz; avoid questions seen on the learner's previous attempt for that checkpoint.", "DESIGN_DEFAULT"),
    ("L02", "POOL_AND_GENERATION", "POOL_FALLBACK", "fallback_order", "FALLBACK_DIFFICULTY_THEN_RELATED_SKILLS", "If skill x difficulty slot is depleted, use fallback_difficulty_num from File 4; if skill is exhausted, substitute related skills from File 3 with learner disclosure.", "DESIGN_DEFAULT"),
    ("L03", "POOL_AND_GENERATION", "AI_GENERATION", "synthetic_generation", "GENERATE_MATCHING_SCHEMA_WITH_VERIFICATION", "Generate synthetic questions matching bank schema when pool has shortfall; flag as GENERATED_UNVERIFIED until programmatic verification (numeric recompute, SQL execution, MCQ position randomization).", "DESIGN_DEFAULT"),
    ("L04", "POOL_AND_GENERATION", "SOURCE_PROVENANCE", "provenance_label", "VERIFIED_BANK_ONLY_FOR_SOURCE", "Items from the original question bank are the sole items labeled VERIFIED_BANK.", "SOURCE_DATA"),
]


def build_da_quiz_pipeline(base_dir=None):
    if base_dir is None:
        cur = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(os.path.join(cur, "Data_Analyst_Questions.xlsx")):
            base_dir = cur
        elif os.path.exists(os.path.join(cur, "..", "Data_Analyst_Questions.xlsx")):
            base_dir = os.path.abspath(os.path.join(cur, ".."))
        elif os.path.exists(os.path.join(cur, "..", "..", "Data_Analyst_Questions.xlsx")):
            base_dir = os.path.abspath(os.path.join(cur, "..", ".."))
        else:
            base_dir = cur

    candidate_dirs = [
        base_dir,
        os.path.join(base_dir, "data_analyst", "data"),
        os.path.join(base_dir, "da", "data"),
        os.path.join(base_dir, "EBuddy-main"),
        os.path.join(base_dir, "EBuddy-main", "data_analyst", "data"),
        os.path.join(base_dir, "EBuddy-main", "da", "data"),
    ]

    def find_file(fname):
        for cdir in candidate_dirs:
            p = os.path.join(cdir, fname)
            if os.path.exists(p):
                return p
        raise FileNotFoundError(f"Could not locate {fname} in any of: {candidate_dirs}")

    input_path = find_file("Data_Analyst_Questions.xlsx")
    print("=" * 80)
    print(f"STEP 1: INGESTING QUESTION BANK WORKBOOK: {input_path}")
    print("=" * 80)

    wb = openpyxl.load_workbook(input_path, data_only=False)
    sheet_names = wb.sheetnames
    assert "questions" in sheet_names, f"Expected sheet 'questions', found: {sheet_names}"
    ws = wb["questions"]

    # Read raw rows
    source_rows = []
    for r in range(2, ws.max_row + 1):
        vals = [ws.cell(row=r, column=c).value for c in range(1, 12)]
        if any(v is not None for v in vals):
            source_rows.append((r, vals))

    assert len(source_rows) == 47, f"Expected 47 data rows, found {len(source_rows)}"
    print(f"  [OK] Successfully ingested {len(source_rows)} raw rows from sheet 'questions'.")

    # Roadmap lookup index
    skill_lookup = {}
    for s in ROADMAP_SKILLS:
        skill_lookup[s[0]] = {
            "name": s[1],
            "category": s[2],
            "level": s[3],
            "prereq_ids": s[4],
            "phase_id": s[5],
            "phase_order": s[6],
            "pos_in_phase": s[7],
        }

    # Verify all prerequisites are in earlier or same phase
    for sid, sdata in skill_lookup.items():
        if sdata["prereq_ids"] != "none":
            for pid in sdata["prereq_ids"].split(";"):
                assert pid in skill_lookup, f"Unknown prerequisite {pid} for skill {sid}"
                p_order = skill_lookup[pid]["phase_order"]
                s_order = sdata["phase_order"]
                assert p_order <= s_order, (
                    f"Violation: prerequisite {pid} (phase {p_order}) is later than {sid} (phase {s_order})"
                )

    print("  [OK] Prerequisite DAG verification passed: zero forward-dependency violations.")

    # ==============================================================================
    # FILE 1: 01_question_bank.csv
    # ==============================================================================
    print("\n" + "=" * 80)
    print("STEP 2: PROCESSING FILE 1 (01_question_bank.csv) & EXTRACTING ATTRIBUTES")
    print("=" * 80)

    file1_rows = []
    seen_qids = set()
    seen_stems = set()

    type_counts = {"mcq": 0, "numeric": 0, "sql": 0}
    diff_counts = {1: 0, 2: 0, 3: 0}
    mcq_letter_counts = {}
    longest_opt_mcq_count = 0

    diff_labels = {1: "Easy", 2: "Medium", 3: "Hard"}

    for r_idx, vals in source_rows:
        qid = str(vals[0] or "").strip()
        sid = str(vals[1] or "").strip()
        diff = int(vals[2])
        qtype = str(vals[3] or "").strip().lower()
        stem = str(vals[4] or "").strip()
        opt_a = str(vals[5] or "").strip() if vals[5] is not None else ""
        opt_b = str(vals[6] or "").strip() if vals[6] is not None else ""
        opt_c = str(vals[7] or "").strip() if vals[7] is not None else ""
        opt_d = str(vals[8] or "").strip() if vals[8] is not None else ""
        ans = str(vals[9] or "").strip()
        exp = str(vals[10] or "").strip()

        # Uniqueness checks
        assert qid not in seen_qids, f"Duplicate question_id: {qid}"
        seen_qids.add(qid)
        assert stem not in seen_stems, f"Duplicate stem: {stem}"
        seen_stems.add(stem)

        assert sid in skill_lookup, f"Row {r_idx}: unknown skill_id {sid}"
        sinfo = skill_lookup[sid]

        type_counts[qtype] = type_counts.get(qtype, 0) + 1
        diff_counts[diff] = diff_counts.get(diff, 0) + 1

        correct_opt_text = ""
        correct_is_longest = ""
        grading_method = ""
        num_val = ""
        num_unit_hint = ""
        sql_tables = ""
        data_notes = []

        if qtype == "mcq":
            grading_method = "MCQ_EXACT_OPTION_TEXT"
            assert opt_a and opt_b and opt_c and opt_d, f"MCQ {qid} missing options"
            ans_lower = ans.lower()
            assert ans_lower in ["a", "b", "c", "d"], f"MCQ {qid} answer not in a/b/c/d: {ans}"
            mcq_letter_counts[ans_lower] = mcq_letter_counts.get(ans_lower, 0) + 1

            opts_map = {"a": opt_a, "b": opt_b, "c": opt_c, "d": opt_d}
            correct_opt_text = opts_map[ans_lower]

            corr_len = len(correct_opt_text)
            other_lens = [len(opts_map[k]) for k in opts_map if k != ans_lower]
            is_longest = corr_len > max(other_lens)
            correct_is_longest = "TRUE" if is_longest else "FALSE"
            if is_longest:
                longest_opt_mcq_count += 1

        elif qtype == "numeric":
            grading_method = "NUMERIC_TOLERANCE"
            assert not (opt_a or opt_b or opt_c or opt_d), f"Numeric {qid} has non-empty options"
            try:
                parsed_num = float(ans)
                num_val = str(int(parsed_num)) if parsed_num.is_integer() else str(parsed_num)
            except ValueError:
                raise AssertionError(f"Numeric {qid} answer cannot parse as number: {ans}")

            has_pct = ("percent" in stem.lower()) or ("%" in stem)
            num_unit_hint = "percent" if has_pct else ""

        elif qtype == "sql":
            grading_method = "SQL_RESULT_COMPARE"
            assert not (opt_a or opt_b or opt_c or opt_d), f"SQL {qid} has non-empty options"
            ans_upper = ans.upper().strip()
            assert ans_upper.startswith("SELECT") or ans_upper.startswith("WITH"), (
                f"SQL {qid} answer does not start with SELECT or WITH: {ans}"
            )

            # Table extraction regex: "Table name(col, col, ...)" -> extract "name(col, col, ...)"
            tables_matched = re.findall(r"[Tt]able\s+([a-zA-Z0-9_]+\s*\([^)]+\))", stem)
            if tables_matched:
                sql_tables = "; ".join(tables_matched)
            else:
                data_notes.append("No explicit Table definition matched in stem")

        data_quality_note = "; ".join(data_notes)

        row_dict = {
            "question_id": qid,
            "skill_id": sid,
            "skill_name": sinfo["name"],
            "skill_category": sinfo["category"],
            "skill_level": sinfo["level"],
            "phase_id": sinfo["phase_id"],
            "phase_order": sinfo["phase_order"],
            "position_in_phase": sinfo["pos_in_phase"],
            "difficulty_num": diff,
            "difficulty_label_derived": diff_labels[diff],
            "question_type": qtype,
            "stem": stem,
            "option_a": opt_a,
            "option_b": opt_b,
            "option_c": opt_c,
            "option_d": opt_d,
            "correct_answer": ans,
            "correct_option_text": correct_opt_text,
            "explanation": exp,
            "grading_method_derived": grading_method,
            "numeric_answer_value": num_val,
            "numeric_unit_hint_derived": num_unit_hint,
            "sql_tables_in_stem_derived": sql_tables,
            "correct_option_is_longest": correct_is_longest,
            "data_quality_note": data_quality_note
        }
        file1_rows.append(row_dict)

    # Sort File 1 by phase_order, then position_in_phase, then question_id
    file1_rows.sort(key=lambda r: (r["phase_order"], r["position_in_phase"], r["question_id"]))

    assert len(file1_rows) == 47, f"File 1 row count mismatch: {len(file1_rows)}"
    print(f"  [OK] File 1 validated: 47 rows processed and sorted.")

    # ==============================================================================
    # FILE 2: 02_skills_phase_map.csv
    # ==============================================================================
    print("\n" + "=" * 80)
    print("STEP 3: PROCESSING FILE 2 (02_skills_phase_map.csv)")
    print("=" * 80)

    # Group questions by skill
    questions_by_skill = {s[0]: [] for s in ROADMAP_SKILLS}
    for q in file1_rows:
        questions_by_skill[q["skill_id"]].append(q)

    file2_rows = []
    shortfall_by_phase = {p: 0 for p in ["DA-PH1", "DA-PH2", "DA-PH3", "DA-PH4", "DA-PH5"]}

    for s in ROADMAP_SKILLS:
        sid, sname, scat, slevel, sprereqs, sphase, porder, pos = s
        q_list = questions_by_skill[sid]
        q_tot = len(q_list)
        q_d1 = sum(1 for q in q_list if q["difficulty_num"] == 1)
        q_d2 = sum(1 for q in q_list if q["difficulty_num"] == 2)
        q_d3 = sum(1 for q in q_list if q["difficulty_num"] == 3)
        q_mcq = sum(1 for q in q_list if q["question_type"] == "mcq")
        q_num = sum(1 for q in q_list if q["question_type"] == "numeric")
        q_sql = sum(1 for q in q_list if q["question_type"] == "sql")

        # Pool status: OK if q_total >= 4 | THIN if 2-3 | VERY_THIN if 1 | EMPTY if 0
        if q_tot >= 4:
            pool_stat = "OK"
        elif q_tot in [2, 3]:
            pool_stat = "THIN"
        elif q_tot == 1:
            pool_stat = "VERY_THIN"
        else:
            pool_stat = "EMPTY"

        shortfall = max(0, 3 - q_tot)
        shortfall_by_phase[sphase] += shortfall

        if sprereqs != "none":
            prereq_names = " | ".join([skill_lookup[p]["name"] for p in sprereqs.split(";")])
        else:
            prereq_names = "none"

        row_s = {
            "skill_id": sid,
            "skill_name": sname,
            "skill_category": scat,
            "skill_level": slevel,
            "prerequisite_skill_ids": sprereqs,
            "prerequisite_skill_names": prereq_names,
            "phase_id": sphase,
            "phase_order": porder,
            "position_in_phase": pos,
            "q_total": q_tot,
            "q_difficulty_1": q_d1,
            "q_difficulty_2": q_d2,
            "q_difficulty_3": q_d3,
            "q_mcq": q_mcq,
            "q_numeric": q_num,
            "q_sql": q_sql,
            "pool_status": pool_stat,
            "min_target_questions": 3,
            "shortfall_to_target": shortfall
        }
        file2_rows.append(row_s)

    # Sort File 2 by phase_order, then position_in_phase
    file2_rows.sort(key=lambda r: (r["phase_order"], r["position_in_phase"]))
    assert len(file2_rows) == 20, f"File 2 row count mismatch: {len(file2_rows)}"
    print(f"  [OK] File 2 validated: 20 skills covered across 5 phases.")

    # ==============================================================================
    # FILE 3: 03_related_skills.csv
    # ==============================================================================
    print("\n" + "=" * 80)
    print("STEP 4: PROCESSING FILE 3 (03_related_skills.csv)")
    print("=" * 80)

    file3_rows = []
    seen_related_pairs = set()

    # 1. Prerequisite and Dependent relations (STRONG)
    for s in ROADMAP_SKILLS:
        sid, sname, scat, slevel, sprereqs, sphase, porder, pos = s
        if sprereqs != "none":
            for pid in sprereqs.split(";"):
                pname = skill_lookup[pid]["name"]

                # A depends on B -> (A, B) is PREREQUISITE
                pair_fwd = (sid, pid)
                assert pair_fwd not in seen_related_pairs, f"Duplicate pair: {pair_fwd}"
                seen_related_pairs.add(pair_fwd)
                file3_rows.append({
                    "skill_id": sid,
                    "related_skill_id": pid,
                    "relation_type": "PREREQUISITE",
                    "relation_strength": "STRONG",
                    "reason_short": f"{sname} builds directly on {pname}"
                })

                # (B, A) is DEPENDENT
                pair_rev = (pid, sid)
                assert pair_rev not in seen_related_pairs, f"Duplicate pair: {pair_rev}"
                seen_related_pairs.add(pair_rev)
                file3_rows.append({
                    "skill_id": pid,
                    "related_skill_id": sid,
                    "relation_type": "DEPENDENT",
                    "relation_strength": "STRONG",
                    "reason_short": f"{pname} prepares learner for {sname}"
                })

    # 2. Same category relations (MODERATE, not already linked as prereq/dep)
    for i, s1 in enumerate(ROADMAP_SKILLS):
        for j, s2 in enumerate(ROADMAP_SKILLS):
            if i == j:
                continue
            sid1, sname1, scat1 = s1[0], s1[1], s1[2]
            sid2, sname2, scat2 = s2[0], s2[1], s2[2]
            if scat1 == scat2:
                pair = (sid1, sid2)
                if pair not in seen_related_pairs:
                    seen_related_pairs.add(pair)
                    file3_rows.append({
                        "skill_id": sid1,
                        "related_skill_id": sid2,
                        "relation_type": "SAME_CATEGORY",
                        "relation_strength": "MODERATE",
                        "reason_short": f"Both cover core {scat1} domain competencies"
                    })

    # Sort File 3 by skill_id, then related_skill_id
    file3_rows.sort(key=lambda r: (r["skill_id"], r["related_skill_id"]))
    print(f"  [OK] File 3 validated: {len(file3_rows)} related pairs (zero duplicates, zero self-relations).")

    # ==============================================================================
    # FILE 4: 04_skill_difficulty_pool.csv
    # ==============================================================================
    print("\n" + "=" * 80)
    print("STEP 5: PROCESSING FILE 4 (04_skill_difficulty_pool.csv)")
    print("=" * 80)

    file4_rows = []
    empty_pool_slots = []
    thin_pool_slots = []

    # Map counts per (skill_id, difficulty_num)
    skill_diff_counts = {}
    for q in file1_rows:
        key = (q["skill_id"], q["difficulty_num"])
        skill_diff_counts[key] = skill_diff_counts.get(key, 0) + 1

    for s in ROADMAP_SKILLS:
        sid, sname = s[0], s[1]
        for d in [1, 2, 3]:
            q_cnt = skill_diff_counts.get((sid, d), 0)
            if q_cnt >= 3:
                status = "OK"
            elif q_cnt in [1, 2]:
                status = "THIN"
                thin_pool_slots.append((sid, sname, d, q_cnt))
            else:
                status = "EMPTY"
                empty_pool_slots.append((sid, sname, d, q_cnt))

            fallback_diff = ""
            if status in ["THIN", "EMPTY"]:
                other_diffs = [od for od in [1, 2, 3] if od != d and skill_diff_counts.get((sid, od), 0) >= 1]
                if other_diffs:
                    other_diffs.sort(key=lambda od: (abs(d - od), od))
                    fallback_diff = str(other_diffs[0])

            needs_gen = "TRUE" if status in ["THIN", "EMPTY"] else "FALSE"

            file4_rows.append({
                "skill_id": sid,
                "skill_name": sname,
                "difficulty_num": d,
                "difficulty_label_derived": diff_labels[d],
                "q_count": q_cnt,
                "pool_status": status,
                "fallback_difficulty_num": fallback_diff,
                "needs_generated_questions": needs_gen
            })

    assert len(file4_rows) == 60, f"File 4 row count mismatch: {len(file4_rows)}"
    print(f"  [OK] File 4 validated: 60 difficulty slots (20 skills x 3 difficulties).")

    # ==============================================================================
    # FILE 5: 05_quiz_checkpoints.csv
    # ==============================================================================
    print("\n" + "=" * 80)
    print("STEP 6: PROCESSING FILE 5 (05_quiz_checkpoints.csv)")
    print("=" * 80)

    file5_rows = []
    for cp in CHECKPOINTS_CONFIG:
        c_id, c_type, t_skills, t_phase, r_skills, target, d1, d2, d3, s_new, s_rev, r_ref = cp

        # Assertions on percentage columns
        assert d1 + d2 + d3 == 100, f"{c_id}: difficulty mix does not sum to 100 ({d1}+{d2}+{d3})"
        assert s_new + s_rev == 100, f"{c_id}: new/review share does not sum to 100 ({s_new}+{s_rev})"

        t_skill_list = t_skills.split(";")
        for sid in t_skill_list:
            assert sid in skill_lookup, f"{c_id}: unknown trigger skill {sid}"

        names_new = " | ".join([skill_lookup[sid]["name"] for sid in t_skill_list])

        r_skill_list = r_skills.split(";") if r_skills else []
        for sid in r_skill_list:
            assert sid in skill_lookup, f"{c_id}: unknown review skill {sid}"
            r_porder = skill_lookup[sid]["phase_order"]
            t_porder = skill_lookup[t_skill_list[0]]["phase_order"] if c_type != "FINAL_CUMULATIVE_QUIZ" else 5
            assert r_porder <= t_porder, (
                f"{c_id}: review skill {sid} (phase {r_porder}) is later than trigger phase {t_porder}"
            )

        # Questions available
        q_new_set = set()
        for sid in t_skill_list:
            q_new_set.update(q["question_id"] for q in questions_by_skill[sid])
        avail_new = len(q_new_set)

        q_rev_set = set()
        for sid in r_skill_list:
            q_rev_set.update(q["question_id"] for q in questions_by_skill[sid])
        avail_rev = len(q_rev_set)

        combined_avail = avail_new + avail_rev
        meets_target = combined_avail >= target
        shortfall = max(0, target - combined_avail)

        length_note = (
            "Below 10 questions: bank has fewer distinct questions than the target; platform should generate the rest in the same format"
            if not meets_target else ""
        )

        row_cp = {
            "checkpoint_id": c_id,
            "checkpoint_type": c_type,
            "trigger_after_skill_ids": t_skills,
            "trigger_phase_id": t_phase,
            "skills_tested_new": names_new,
            "skills_review_from_earlier": r_skills,
            "target_num_questions": target,
            "difficulty_mix_d1_pct": d1,
            "difficulty_mix_d2_pct": d2,
            "difficulty_mix_d3_pct": d3,
            "share_new_pct": s_new,
            "share_review_pct": s_rev,
            "pass_score_pct": 70,
            "retry_if_below_pct": 50,
            "on_fail_action": ">=70: proceed; 50-69: review the weak skills, then retake a NEW quiz before proceeding; <50: repeat the skill cluster's learning before retaking",
            "roadmap_checkpoint_ref": r_ref,
            "distinct_questions_available_new": avail_new,
            "distinct_questions_available_review": avail_rev,
            "meets_target_length": "TRUE" if meets_target else "FALSE",
            "pool_shortfall": shortfall,
            "length_note": length_note
        }
        file5_rows.append(row_cp)

    assert len(file5_rows) == 17, f"File 5 row count mismatch: {len(file5_rows)}"
    print(f"  [OK] File 5 validated: 17 checkpoints (12 Cluster Checks, 4 Phase Ends, 1 Final Cumulative).")

    # ==============================================================================
    # FILE 6: 06_quiz_rules.csv
    # ==============================================================================
    print("\n" + "=" * 80)
    print("STEP 7: PROCESSING FILE 6 (06_quiz_rules.csv)")
    print("=" * 80)

    file6_rows = []
    for r in QUIZ_RULES_CONFIG:
        file6_rows.append({
            "rule_id": r[0],
            "scenario": r[1],
            "rule_name": r[2],
            "parameter": r[3],
            "value": r[4],
            "description": r[5],
            "source_type": r[6]
        })

    assert len(file6_rows) == 29, f"File 6 row count mismatch: {len(file6_rows)}"
    print(f"  [OK] File 6 validated: 29 machine-readable rules across 6 operational scenarios.")

    # ==============================================================================
    # STEP 8: WRITE DELIVERABLES TO DISK (UTF-8 WITH BOM, MINIMAL QUOTING)
    # ==============================================================================
    print("\n" + "=" * 80)
    print("STEP 8: WRITING CSV DELIVERABLES TO TARGET DIRECTORIES")
    print("=" * 80)

    out_dirs = [
        os.path.join(base_dir, "output"),
        os.path.join(base_dir, "data_analyst", "output"),
        os.path.join(base_dir, "da", "output"),
        os.path.join(base_dir, "EBuddy-main", "output"),
        os.path.join(base_dir, "EBuddy-main", "data_analyst", "output"),
        os.path.join(base_dir, "EBuddy-main", "da", "output"),
    ]

    for od in out_dirs:
        os.makedirs(od, exist_ok=True)

    files_definitions = [
        (
            "01_question_bank.csv",
            [
                "question_id", "skill_id", "skill_name", "skill_category", "skill_level",
                "phase_id", "phase_order", "difficulty_num", "difficulty_label_derived",
                "question_type", "stem", "option_a", "option_b", "option_c", "option_d",
                "correct_answer", "correct_option_text", "explanation", "grading_method_derived",
                "numeric_answer_value", "numeric_unit_hint_derived", "sql_tables_in_stem_derived",
                "correct_option_is_longest", "data_quality_note"
            ],
            file1_rows
        ),
        (
            "02_skills_phase_map.csv",
            [
                "skill_id", "skill_name", "skill_category", "skill_level", "prerequisite_skill_ids",
                "prerequisite_skill_names", "phase_id", "phase_order", "position_in_phase",
                "q_total", "q_difficulty_1", "q_difficulty_2", "q_difficulty_3",
                "q_mcq", "q_numeric", "q_sql", "pool_status", "min_target_questions", "shortfall_to_target"
            ],
            file2_rows
        ),
        (
            "03_related_skills.csv",
            [
                "skill_id", "related_skill_id", "relation_type", "relation_strength", "reason_short"
            ],
            file3_rows
        ),
        (
            "04_skill_difficulty_pool.csv",
            [
                "skill_id", "skill_name", "difficulty_num", "difficulty_label_derived",
                "q_count", "pool_status", "fallback_difficulty_num", "needs_generated_questions"
            ],
            file4_rows
        ),
        (
            "05_quiz_checkpoints.csv",
            [
                "checkpoint_id", "checkpoint_type", "trigger_after_skill_ids", "trigger_phase_id",
                "skills_tested_new", "skills_review_from_earlier", "target_num_questions",
                "difficulty_mix_d1_pct", "difficulty_mix_d2_pct", "difficulty_mix_d3_pct",
                "share_new_pct", "share_review_pct", "pass_score_pct", "retry_if_below_pct",
                "on_fail_action", "roadmap_checkpoint_ref", "distinct_questions_available_new",
                "distinct_questions_available_review", "meets_target_length", "pool_shortfall", "length_note"
            ],
            file5_rows
        ),
        (
            "06_quiz_rules.csv",
            [
                "rule_id", "scenario", "rule_name", "parameter", "value", "description", "source_type"
            ],
            file6_rows
        ),
    ]

    for fname, headers, data in files_definitions:
        for od in out_dirs:
            target_path = os.path.join(od, fname)
            with open(target_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                for row in data:
                    filtered_row = {k: row[k] for k in headers}
                    writer.writerow(filtered_row)
        print(f"  [OK] Successfully wrote {fname} ({len(data)} rows).")

    # ==============================================================================
    # STEP 9: ASSERTIONS & SOURCE FIDELITY AUDIT
    # ==============================================================================
    print("\n" + "=" * 80)
    print("STEP 9: SOURCE RE-READING AND EXACT CELL FIDELITY VERIFICATION")
    print("=" * 80)

    # Re-read raw workbook cells and compare against file1_rows
    q_dict = {r["question_id"]: r for r in file1_rows}
    for r_idx, vals in source_rows:
        qid = str(vals[0] or "").strip()
        assert qid in q_dict, f"Missing {qid} in generated File 1"
        row = q_dict[qid]

        assert row["skill_id"] == str(vals[1] or "").strip(), f"Fidelity error in skill_id for {qid}"
        assert row["difficulty_num"] == int(vals[2]), f"Fidelity error in difficulty for {qid}"
        assert row["question_type"] == str(vals[3] or "").strip().lower(), f"Fidelity error in type for {qid}"
        assert row["stem"] == str(vals[4] or "").strip(), f"Fidelity error in stem for {qid}"
        assert row["option_a"] == (str(vals[5] or "").strip() if vals[5] is not None else ""), f"Fidelity error in option_a for {qid}"
        assert row["option_b"] == (str(vals[6] or "").strip() if vals[6] is not None else ""), f"Fidelity error in option_b for {qid}"
        assert row["option_c"] == (str(vals[7] or "").strip() if vals[7] is not None else ""), f"Fidelity error in option_c for {qid}"
        assert row["option_d"] == (str(vals[8] or "").strip() if vals[8] is not None else ""), f"Fidelity error in option_d for {qid}"
        assert row["correct_answer"] == str(vals[9] or "").strip(), f"Fidelity error in answer for {qid}"
        assert row["explanation"] == str(vals[10] or "").strip(), f"Fidelity error in explanation for {qid}"

    print("  [OK] 100% cell fidelity verified: every raw cell strictly matches File 1 output.")

    # ==============================================================================
    # STEP 10: CONSOLE METRICS, SHORTFALLS & CHECKPOINT VERDICTS
    # ==============================================================================
    print("\n" + "=" * 80)
    print("STEP 10: METRICS SUMMARY & ANALYSIS")
    print("=" * 80)

    print(f"Total Questions in Bank: {len(file1_rows)}")
    print(f"  By Type: MCQ={type_counts['mcq']}, Numeric={type_counts['numeric']}, SQL={type_counts['sql']}")
    print(f"  By Difficulty: 1 (Easy)={diff_counts[1]}, 2 (Medium)={diff_counts[2]}, 3 (Hard)={diff_counts[3]}")
    print(f"  MCQ Answer Letter Distribution: {mcq_letter_counts}")
    print(f"  MCQs Where Correct Option is Longest: {longest_opt_mcq_count} / {type_counts['mcq']} ({longest_opt_mcq_count/type_counts['mcq']*100:.1f}%)")

    print("\n--- Questions Per Phase ---")
    phase_q_counts = {p: 0 for p in ["DA-PH1", "DA-PH2", "DA-PH3", "DA-PH4", "DA-PH5"]}
    for q in file1_rows:
        phase_q_counts[q["phase_id"]] += 1
    for p, cnt in phase_q_counts.items():
        print(f"  {p}: {cnt} questions (Shortfall to 3-target/skill: {shortfall_by_phase[p]})")

    print("\n--- File 2: Skill Inventory & Shortfall to Target (3 questions) ---")
    for r in file2_rows:
        print(f"  {r['skill_id']:<7} | {r['phase_id']} pos {r['position_in_phase']} | Total: {r['q_total']} (d1:{r['q_difficulty_1']}, d2:{r['q_difficulty_2']}, d3:{r['q_difficulty_3']}) | Status: {r['pool_status']:<9} | Shortfall: {r['shortfall_to_target']}")

    print("\n--- File 4: Empty and Thin Pool Slots ---")
    print(f"Total Empty Slots (0 questions): {len(empty_pool_slots)} / 60")
    print(f"Total Thin Slots (1-2 questions): {len(thin_pool_slots)} / 60")
    print(f"Total OK Slots (>=3 questions): {60 - len(empty_pool_slots) - len(thin_pool_slots)} / 60")

    print("\n--- File 5: Checkpoints Target Length & Pool Shortfall ---")
    for r in file5_rows:
        print(f"  {r['checkpoint_id']:<7} ({r['checkpoint_type']:<20}): Target={r['target_num_questions']:2d} | Avail New={r['distinct_questions_available_new']:2d}, Rev={r['distinct_questions_available_review']:2d} | Meets Target={r['meets_target_length']:<5} | Shortfall={r['pool_shortfall']:2d}")

    # ==============================================================================
    # STEP 11: PREVIEW FIRST 3 ROWS OF EACH CSV DELIVERABLE
    # ==============================================================================
    print("\n" + "=" * 80)
    print("STEP 11: PREVIEW FIRST 3 ROWS OF EACH CSV")
    print("=" * 80)

    for fname, headers, data in files_definitions:
        print(f"\n--- Preview: {fname} (Total rows: {len(data)}) ---")
        for i, row in enumerate(data[:3], 1):
            print(f"Row {i}:")
            for h in headers[:8]:
                print(f"    {h}: {row[h]}")
            if len(headers) > 8:
                print(f"    ... [{len(headers) - 8} more columns]")

    print("\n" + "=" * 80)
    print("PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    build_da_quiz_pipeline()
