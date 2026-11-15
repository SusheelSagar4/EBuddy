"""
SDE Quiz Assessment Knowledge Base Pipeline for eBuddy
Adobe Personalised Learning Buddy (Inter IIT Tech Meet 15.0)

Converts 3 curated LeetCode DSA practice bank workbooks:
  - LeetCode_DSA_Easy.xlsx (259 problems)
  - LeetCode_DSA_Medium.xlsx (684 problems)
  - LeetCode_DSA_Hard.xlsx (576 problems)
into 3 relational, validated CSV files for eBuddy's diagnostic, topic, and spaced repetition quiz engine.

Deliverables:
  1. 01_problem_bank_raw.csv (1,519 rows across Easy, Medium, Hard)
  2. 02_problems_unique.csv (1,193 unique LeetCode problems with conflict flags)
  3. 03_topics_roadmap_map.csv (15 canonical topics mapped to SDE roadmap with readiness metrics)
"""

import os
import sys
import csv
from collections import defaultdict
import openpyxl

def build_sde_quiz_pipeline(base_dir=None):
    if base_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Potential input file locations
    candidate_dirs = [
        base_dir,
        os.path.join(base_dir, "sde", "data"),
        os.path.join(base_dir, "EBuddy-main"),
        os.path.join(base_dir, "EBuddy-main", "sde", "data")
    ]

    def find_file(fname):
        for cdir in candidate_dirs:
            p = os.path.join(cdir, fname)
            if os.path.exists(p):
                return p
        raise FileNotFoundError(f"Could not locate {fname} in any of: {candidate_dirs}")

    easy_path = find_file("LeetCode_DSA_Easy.xlsx")
    med_path = find_file("LeetCode_DSA_Medium.xlsx")
    hard_path = find_file("LeetCode_DSA_Hard.xlsx")

    files_meta = [
        ("LeetCode_DSA_Easy.xlsx", easy_path, "EASY", "Easy", 1, 259),
        ("LeetCode_DSA_Medium.xlsx", med_path, "MED", "Medium", 2, 684),
        ("LeetCode_DSA_Hard.xlsx", hard_path, "HARD", "Hard", 3, 576),
    ]

    print("=" * 80)
    print("STEP 1: VERIFYING INPUT WORKBOOKS AND TOPIC SHEET ROW COUNTS")
    print("=" * 80)

    for fname, fpath, prefix, diff_name, diff_num, expected_qi_rows in files_meta:
        wb = openpyxl.load_workbook(fpath, data_only=False)
        qi = wb["Question Index"]
        qi_row_count = qi.max_row - 1
        assert qi_row_count == expected_qi_rows, (
            f"{fname}: expected {expected_qi_rows} rows in Question Index, got {qi_row_count}"
        )

        topic_sheets = [s for s in wb.sheetnames if s not in ["Read Me", "Question Index"]]
        topic_rows_sum = sum(wb[s].max_row - 1 for s in topic_sheets)
        assert topic_rows_sum == qi_row_count, (
            f"{fname}: topic sheets row sum ({topic_rows_sum}) != Question Index rows ({qi_row_count})"
        )
        print(f"  [OK] {fname}: Question Index = {qi_row_count} rows, {len(topic_sheets)} topic sheets sum = {topic_rows_sum} (Exact Match)")

    def to_canonical(t):
        if t in ["Math", "Bit Manipulation"]:
            return "Math & Bit Manipulation"
        return t

    def get_subgroup(raw_topic):
        if raw_topic in ["Math", "Bit Manipulation", "Math & Bit Manipulation"]:
            return raw_topic
        return ""

    print("\n" + "=" * 80)
    print("STEP 2: EXTRACTING PROBLEM BANK RAW RECORDS (HYPERLINKS & METADATA)")
    print("=" * 80)

    raw_records = []
    bank_by_lc = defaultdict(list)

    for fname, fpath, prefix, diff_name, diff_num, _ in files_meta:
        wb = openpyxl.load_workbook(fpath, data_only=False)
        ws = wb["Question Index"]
        for r in range(2, ws.max_row + 1):
            s_no = ws.cell(row=r, column=1).value
            lc_num = int(ws.cell(row=r, column=2).value)
            prob_title = str(ws.cell(row=r, column=3).value or "").strip()
            top_raw = str(ws.cell(row=r, column=4).value or "").strip()
            df_raw = str(ws.cell(row=r, column=5).value or "").strip()
            link_cell = ws.cell(row=r, column=6)

            hl = link_cell.hyperlink
            hl_target = hl.target if hl else None
            cell_val = str(link_cell.value or "").strip()

            url = hl_target if hl_target else cell_val
            quality_note = ""
            if hl_target and cell_val and hl_target != cell_val:
                quality_note = "Hyperlink target differs from cell value"

            top_canon = to_canonical(top_raw)
            subgroup = get_subgroup(top_raw)
            bank_row_id = f"{prefix}-{r-1:04d}"

            rec = {
                "bank_row_id": bank_row_id,
                "source_file": fname,
                "source_row": r,
                "source_no": s_no,
                "leetcode_number": lc_num,
                "problem_title": prob_title,
                "topic_raw": top_raw,
                "topic_canonical": top_canon,
                "topic_subgroup": subgroup,
                "difficulty_raw": df_raw,
                "difficulty_level_num": diff_num,
                "problem_url": url,
                "link_verified": "FALSE",
                "data_quality_note": quality_note
            }
            raw_records.append(rec)
            bank_by_lc[lc_num].append(rec)

    assert len(raw_records) == 1519, f"Expected 1519 raw rows, got {len(raw_records)}"
    print(f"  [OK] Extracted {len(raw_records)} raw records across 3 workbooks.")

    print("\n" + "=" * 80)
    print("STEP 3: RESOLVING CONFLICTS & DEDUPLICATING CATALOG (FILE 2)")
    print("=" * 80)

    TOPIC_TO_ROADMAP = {
        "Arrays & Hashing": ("4|6", "P2_DSA_Foundations"),
        "Strings": ("5", "P2_DSA_Foundations"),
        "Two Pointers & Sliding Window": ("9|10", "P3_DSA_Core_Techniques"),
        "Binary Search & Sorting": ("7|8", "P2_DSA_Foundations"),
        "Linked List": ("11", "P3_DSA_Core_Techniques"),
        "Stack & Queue": ("12|13", "P3_DSA_Core_Techniques"),
        "Trees & BST": ("18|19", "P4_Trees_and_Graphs"),
        "Heap & Priority Queue": ("20", "P4_Trees_and_Graphs"),
        "Dynamic Programming": ("25|26", "P5_Dynamic_Programming_and_Practice"),
        "Graphs": ("22|23|24", "P4_Trees_and_Graphs"),
        "Greedy & Intervals": ("17", "P3_DSA_Core_Techniques"),
        "Backtracking": ("14|15", "P3_DSA_Core_Techniques"),
        "Trie": ("21", "P4_Trees_and_Graphs"),
        "Matrix": ("4", "P2_DSA_Foundations"),
        "Math & Bit Manipulation": ("16", "P3_DSA_Core_Techniques")
    }

    unique_problems = []
    diff_conflict_count = 0
    topic_conflict_count = 0
    overlap_count = 0

    for lc_num in sorted(bank_by_lc.keys()):
        recs = bank_by_lc[lc_num]
        if len(recs) > 1:
            overlap_count += 1

        # Highest difficulty record takes precedence for canonical title, url, primary topic
        recs_sorted = sorted(recs, key=lambda x: x["difficulty_level_num"], reverse=True)
        highest_rec = recs_sorted[0]

        diffs_distinct = sorted(
            list(set(r["difficulty_raw"] for r in recs)),
            key=lambda d: 1 if d == "Easy" else (2 if d == "Medium" else 3)
        )
        diff_conflict = len(diffs_distinct) > 1

        if diff_conflict:
            diff_conflict_count += 1
            diff_for_quiz = "AMBIGUOUS"
            diff_num_for_quiz = ""
            quiz_eligible_calibrated = "FALSE"
        else:
            diff_for_quiz = diffs_distinct[0]
            diff_num_for_quiz = str(highest_rec["difficulty_level_num"])
            quiz_eligible_calibrated = "TRUE"

        source_files_seen = []
        for r in recs:
            if r["source_file"] not in source_files_seen:
                source_files_seen.append(r["source_file"])

        raw_topics_seen = []
        for r in recs:
            if r["topic_raw"] not in raw_topics_seen:
                raw_topics_seen.append(r["topic_raw"])

        canon_topics_seen = []
        for r in recs:
            if r["topic_canonical"] not in canon_topics_seen:
                canon_topics_seen.append(r["topic_canonical"])

        topic_conflict = len(canon_topics_seen) > 1
        if topic_conflict:
            topic_conflict_count += 1

        primary_topic = highest_rec["topic_canonical"]
        subgroup = highest_rec["topic_subgroup"] if primary_topic == "Math & Bit Manipulation" else ""

        step_ids, phase_id = TOPIC_TO_ROADMAP[primary_topic]

        notes = []
        if diff_conflict:
            diff_str = "|".join(diffs_distinct)
            notes.append(f"Labelled {diff_str} across files; difficulty unreliable for calibrated assessment")
        if topic_conflict:
            top_str = "|".join(canon_topics_seen)
            notes.append(f"Multiple topics seen across files: {top_str}")
        data_quality_note = "; ".join(notes)

        unique_rec = {
            "leetcode_number": lc_num,
            "problem_title": highest_rec["problem_title"],
            "problem_url": highest_rec["problem_url"],
            "difficulty_conflict": "TRUE" if diff_conflict else "FALSE",
            "difficulties_seen": "|".join(diffs_distinct),
            "difficulty_for_quiz": diff_for_quiz,
            "difficulty_level_num_for_quiz": diff_num_for_quiz,
            "source_files_seen": "|".join(source_files_seen),
            "appearance_count": len(recs),
            "topics_raw_seen": "|".join(raw_topics_seen),
            "topics_canonical_seen": "|".join(canon_topics_seen),
            "topic_conflict": "TRUE" if topic_conflict else "FALSE",
            "primary_topic": primary_topic,
            "topic_subgroup": subgroup,
            "quiz_eligible_calibrated": quiz_eligible_calibrated,
            "quiz_eligible_topic_only": "TRUE",
            "roadmap_step_ids": step_ids,
            "roadmap_phase_id": phase_id,
            "data_quality_note": data_quality_note
        }
        unique_problems.append(unique_rec)

    assert len(unique_problems) == 1193, f"Expected 1193 unique problems, got {len(unique_problems)}"
    print(f"  [OK] Catalog unique problems: {len(unique_problems)}")
    print(f"  [OK] Overlap count (in >=2 files): {overlap_count}")
    print(f"  [OK] Difficulty conflicts: {diff_conflict_count}")
    print(f"  [OK] Canonical topic conflicts: {topic_conflict_count}")

    print("\n" + "=" * 80)
    print("STEP 4: BUILDING TOPIC TO ROADMAP MAP & READINESS VERDICTS (FILE 3)")
    print("=" * 80)

    CANONICAL_TOPICS_DEF = [
        ("T01", "Arrays & Hashing", "Arrays & Hashing", "4|6", "Arrays|Hashing", "P2_DSA_Foundations", "P2_DSA_Foundations", "FULL", "", "None"),
        ("T02", "Strings", "Strings", "5", "Strings", "P2_DSA_Foundations", "P2_DSA_Foundations", "FULL", "", "Arrays & Hashing"),
        ("T03", "Two Pointers & Sliding Window", "Two Pointers & Sliding Window", "9|10", "Two pointers|Sliding window", "P3_DSA_Core_Techniques", "P3_DSA_Core_Techniques", "FULL", "", "Arrays & Hashing|Strings"),
        ("T04", "Binary Search & Sorting", "Binary Search & Sorting", "7|8", "Sorting|Binary search", "P2_DSA_Foundations", "P2_DSA_Foundations", "FULL", "", "Arrays & Hashing"),
        ("T05", "Linked List", "Linked List", "11", "Linked lists", "P3_DSA_Core_Techniques", "P3_DSA_Core_Techniques", "FULL", "", "Arrays & Hashing"),
        ("T06", "Stack & Queue", "Stack & Queue", "12|13", "Stack|Queue & deque", "P3_DSA_Core_Techniques", "P3_DSA_Core_Techniques", "FULL", "", "Arrays & Hashing|Linked List"),
        ("T07", "Trees & BST", "Trees & BST", "18|19", "Binary trees|BST", "P4_Trees_and_Graphs", "P4_Trees_and_Graphs", "FULL", "", "Stack & Queue|Backtracking"),
        ("T08", "Heap & Priority Queue", "Heap & Priority Queue", "20", "Heaps", "P4_Trees_and_Graphs", "P4_Trees_and_Graphs", "FULL", "", "Binary Search & Sorting|Trees & BST"),
        ("T09", "Dynamic Programming", "Dynamic Programming", "25|26", "DP fundamentals|DP 2D/grids/strings", "P5_Dynamic_Programming_and_Practice", "P5_Dynamic_Programming_and_Practice", "FULL", "", "Backtracking"),
        ("T10", "Graphs", "Graphs", "22|23|24", "Graphs basics & traversal|Graphs shortest paths & MST|Union-Find", "P4_Trees_and_Graphs", "P4_Trees_and_Graphs", "FULL", "", "Stack & Queue|Trees & BST"),
        ("T11", "Greedy & Intervals", "Greedy & Intervals", "17", "Greedy", "P3_DSA_Core_Techniques", "P3_DSA_Core_Techniques", "FULL", "", "Arrays & Hashing|Binary Search & Sorting"),
        ("T12", "Backtracking", "Backtracking", "14|15", "Recursion|Backtracking", "P3_DSA_Core_Techniques", "P3_DSA_Core_Techniques", "FULL", "", "Recursion"),
        ("T13", "Trie", "Trie", "21", "Tries", "P4_Trees_and_Graphs", "P4_Trees_and_Graphs", "FULL", "", "Strings|Trees & BST"),
        ("T14", "Matrix", "Matrix", "4", "Arrays", "P2_DSA_Foundations", "P2_DSA_Foundations", "PARTIAL", "Matrix problems are covered under Step 4 (Arrays) in Phase 2", "Arrays & Hashing"),
        ("T15", "Math & Bit Manipulation", "Bit Manipulation|Math|Math & Bit Manipulation", "16", "Bit manipulation", "P3_DSA_Core_Techniques", "P3_DSA_Core_Techniques", "PARTIAL", "Covers bit manipulation from Step 16 and mathematical problem solving across foundational phases", "Arrays & Hashing")
    ]

    topic_roadmap_rows = []
    for t_id, c_top, raw_inc, s_ids, s_names, p_ids, latest_p, m_str, m_notes, prereq in CANONICAL_TOPICS_DEF:
        c_easy = sum(1 for r in raw_records if r["topic_canonical"] == c_top and r["difficulty_raw"] == "Easy")
        c_med = sum(1 for r in raw_records if r["topic_canonical"] == c_top and r["difficulty_raw"] == "Medium")
        c_hard = sum(1 for r in raw_records if r["topic_canonical"] == c_top and r["difficulty_raw"] == "Hard")
        c_total = c_easy + c_med + c_hard

        u_probs = [u for u in unique_problems if u["primary_topic"] == c_top]
        c_u_total = len(u_probs)
        c_cal_easy = sum(1 for u in u_probs if u["difficulty_for_quiz"] == "Easy")
        c_cal_med = sum(1 for u in u_probs if u["difficulty_for_quiz"] == "Medium")
        c_cal_hard = sum(1 for u in u_probs if u["difficulty_for_quiz"] == "Hard")
        c_amb = sum(1 for u in u_probs if u["difficulty_for_quiz"] == "AMBIGUOUS")

        if c_cal_med >= 15:
            status = "READY"
        elif c_cal_med >= 5:
            status = "LIMITED"
        else:
            status = "INSUFFICIENT"

        t_row = {
            "topic_id": t_id,
            "topic_canonical": c_top,
            "raw_topics_included": raw_inc,
            "roadmap_step_ids": s_ids,
            "roadmap_step_names": s_names,
            "roadmap_phase_ids": p_ids,
            "latest_phase_id": latest_p,
            "mapping_strength": m_str,
            "mapping_notes": m_notes,
            "prerequisite_topics": prereq,
            "count_raw_easy": c_easy,
            "count_raw_medium": c_med,
            "count_raw_hard": c_hard,
            "count_raw_total": c_total,
            "count_unique_problems": c_u_total,
            "count_calibrated_easy": c_cal_easy,
            "count_calibrated_medium": c_cal_med,
            "count_calibrated_hard": c_cal_hard,
            "count_ambiguous_difficulty": c_amb,
            "min_problems_for_quiz": 15,
            "quiz_readiness_status": status
        }
        topic_roadmap_rows.append(t_row)
        print(f"  {t_id} {c_top:<30}: Raw={c_total:3d} (E:{c_easy:2d}, M:{c_med:3d}, H:{c_hard:3d}) | Unique={c_u_total:3d} | Calibrated: E={c_cal_easy:2d}, M={c_cal_med:3d}, H={c_cal_hard:3d}, Amb={c_amb:3d} | Status={status}")

    assert len(topic_roadmap_rows) == 15, f"Expected 15 topics, got {len(topic_roadmap_rows)}"
    assert sum(r["count_raw_total"] for r in topic_roadmap_rows) == 1519
    assert sum(r["count_unique_problems"] for r in topic_roadmap_rows) == 1193

    # Output CSV definitions
    out_dirs = [
        os.path.join(base_dir, "sde", "output"),
        os.path.join(base_dir, "output"),
        os.path.join(base_dir, "EBuddy-main", "sde", "output"),
        os.path.join(base_dir, "EBuddy-main", "output"),
    ]

    for od in out_dirs:
        os.makedirs(od, exist_ok=True)

    files_to_write = [
        (
            "01_problem_bank_raw.csv",
            [
                "bank_row_id", "source_file", "source_row", "source_no", "leetcode_number",
                "problem_title", "topic_raw", "topic_canonical", "topic_subgroup",
                "difficulty_raw", "difficulty_level_num", "problem_url", "link_verified", "data_quality_note"
            ],
            raw_records
        ),
        (
            "02_problems_unique.csv",
            [
                "leetcode_number", "problem_title", "problem_url", "difficulty_conflict",
                "difficulties_seen", "difficulty_for_quiz", "difficulty_level_num_for_quiz",
                "source_files_seen", "appearance_count", "topics_raw_seen", "topics_canonical_seen",
                "topic_conflict", "primary_topic", "topic_subgroup", "quiz_eligible_calibrated",
                "quiz_eligible_topic_only", "roadmap_step_ids", "roadmap_phase_id", "data_quality_note"
            ],
            unique_problems
        ),
        (
            "03_topics_roadmap_map.csv",
            [
                "topic_id", "topic_canonical", "raw_topics_included", "roadmap_step_ids",
                "roadmap_step_names", "roadmap_phase_ids", "latest_phase_id", "mapping_strength",
                "mapping_notes", "prerequisite_topics", "count_raw_easy", "count_raw_medium",
                "count_raw_hard", "count_raw_total", "count_unique_problems", "count_calibrated_easy",
                "count_calibrated_medium", "count_calibrated_hard", "count_ambiguous_difficulty",
                "min_problems_for_quiz", "quiz_readiness_status"
            ],
            topic_roadmap_rows
        )
    ]

    print("\n" + "=" * 80)
    print("STEP 5: WRITING ENCODED CSV DELIVERABLES (UTF-8 WITH BOM)")
    print("=" * 80)

    for fname, headers, data_rows in files_to_write:
        for od in out_dirs:
            target_path = os.path.join(od, fname)
            with open(target_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                for row in data_rows:
                    writer.writerow(row)
        print(f"  [OK] Successfully wrote {fname} ({len(data_rows)} rows) to all target directories.")

    print("\n" + "=" * 80)
    print("STEP 6: DELIVERABLE PREVIEWS (FIRST 3 ROWS OF EACH CSV)")
    print("=" * 80)

    for fname, headers, data_rows in files_to_write:
        print(f"\n--- Preview: {fname} (Total rows: {len(data_rows)}) ---")
        for i, row in enumerate(data_rows[:3], 1):
            print(f"Row {i}:")
            for k in headers:
                print(f"    {k}: {row[k]}")

    print("\n" + "=" * 80)
    print("PIPELINE EXECUTION COMPLETE & ALL ASSERTIONS PASSED!")
    print("=" * 80)

if __name__ == "__main__":
    build_sde_quiz_pipeline()
