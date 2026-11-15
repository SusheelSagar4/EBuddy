"""
Foreign Key Orphan Detector & Integrity Checker.

Reads docker/init.sql to extract declared foreign key constraints,
parses all seed files in data/seed/ (including personas), and checks
whether foreign key references exist in target tables.

Prints full list of orphans with:
  file, row, column, value, referenced table (and referenced column).
Does not load anything into the database.
"""

import os
import sys
import csv
import json
import re
import glob
from typing import Dict, List, Tuple, Any, Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INIT_SQL_PATH = os.path.join(BASE_DIR, "docker", "init.sql")
SEED_DIR = os.path.join(BASE_DIR, "data", "seed")

def parse_init_sql_fks(init_sql_path: str = INIT_SQL_PATH) -> Tuple[Dict[str, List[str]], Dict[str, List[Tuple[str, str, str]]]]:
    """
    Parses docker/init.sql to discover:
    1. Primary key columns per table: table_name -> [pk_col, ...]
    2. Foreign key constraints per table: table_name -> [(column, ref_table, ref_column), ...]
    """
    if not os.path.exists(init_sql_path):
        raise FileNotFoundError(f"init.sql not found at {init_sql_path}")

    with open(init_sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    table_re = re.compile(r'CREATE TABLE IF NOT EXISTS\s+([a-zA-Z0-9_\.]+)\s*\((.*?)\);', re.DOTALL | re.IGNORECASE)
    pk_table_re = re.compile(r'PRIMARY KEY\s*\(([a-zA-Z0-9_,\s]+)\)', re.IGNORECASE)
    fk_col_re = re.compile(r'^\s*([a-zA-Z0-9_]+)\s+.*?REFERENCES\s+([a-zA-Z0-9_\.]+)\s*(?:\(([a-zA-Z0-9_]+)\))?', re.MULTILINE | re.IGNORECASE)
    fk_table_re = re.compile(r'FOREIGN KEY\s*\(([a-zA-Z0-9_,\s]+)\)\s*REFERENCES\s+([a-zA-Z0-9_\.]+)\s*(?:\(([a-zA-Z0-9_,\s]+)\))?', re.IGNORECASE)

    table_pks: Dict[str, List[str]] = {}
    table_fks: Dict[str, List[Tuple[str, str, str]]] = {}

    for m in table_re.finditer(sql):
        tname = m.group(1).lower().strip()
        body = m.group(2)
        pks: List[str] = []
        fks: List[Tuple[str, str, str]] = []

        # Check inline PRIMARY KEY
        for line in body.split('\n'):
            line_str = line.strip()
            if 'PRIMARY KEY' in line_str.upper() and not line_str.upper().startswith(('PRIMARY', 'CONSTRAINT')):
                parts = line_str.split()
                if parts:
                    pks.append(parts[0].lower())

            # Inline REFERENCES
            col_m = fk_col_re.search(line)
            if col_m:
                col = col_m.group(1).lower().strip()
                ref_t = col_m.group(2).lower().strip()
                ref_c = (col_m.group(3) or 'id').lower().strip()
                if not col.startswith(('foreign', 'constraint')):
                    fks.append((col, ref_t, ref_c))

        # Table-level PRIMARY KEY
        for pkm in pk_table_re.finditer(body):
            cols = [c.strip().lower() for c in pkm.group(1).split(',')]
            pks.extend(cols)

        # Table-level FOREIGN KEY
        for tfk in fk_table_re.finditer(body):
            cols = [c.strip().lower() for c in tfk.group(1).split(',')]
            ref_t = tfk.group(2).lower().strip()
            ref_cols = [c.strip().lower() for c in tfk.group(3).split(',')] if tfk.group(3) else ['id']
            for c, rc in zip(cols, ref_cols):
                fks.append((c, ref_t, rc))

        table_pks[tname] = pks
        table_fks[tname] = fks

    return table_pks, table_fks


def get_seed_file_mappings(base_dir: str = BASE_DIR) -> Dict[str, str]:
    """
    Returns explicit mapping of seed file relative paths to database tables.
    """
    return {
        # kb schema
        os.path.join("data", "seed", "kb", "source.csv"): "kb.source",
        os.path.join("data", "seed", "kb", "department.csv"): "kb.department",
        os.path.join("data", "seed", "kb", "programme.csv"): "kb.programme",
        os.path.join("data", "seed", "kb", "course.csv"): "kb.course",
        os.path.join("data", "seed", "kb", "course_alias.csv"): "kb.course_alias",
        os.path.join("data", "seed", "kb", "course_prerequisite.csv"): "kb.course_prerequisite",
        os.path.join("data", "seed", "kb", "course_offering.csv"): "kb.course_offering",
        os.path.join("data", "seed", "kb", "programme_requirement.csv"): "kb.programme_requirement",
        os.path.join("data", "seed", "kb", "slot_option.csv"): "kb.slot_option",
        os.path.join("data", "seed", "kb", "minor.csv"): "kb.minor",
        os.path.join("data", "seed", "kb", "minor_course.csv"): "kb.minor_course",
        os.path.join("data", "seed", "kb", "academic_rule.json"): "kb.academic_rule",
        os.path.join("data", "seed", "kb", "skill.csv"): "kb.skill",
        os.path.join("data", "seed", "kb", "skill_prerequisite.csv"): "kb.skill_prerequisite",
        os.path.join("data", "seed", "kb", "course_skill.csv"): "kb.course_skill",
        os.path.join("data", "seed", "kb", "module.csv"): "kb.module",
        os.path.join("data", "seed", "kb", "module_skill.csv"): "kb.module_skill",
        os.path.join("data", "seed", "kb", "resource.csv"): "kb.resource",
        os.path.join("data", "seed", "kb", "resource_skill.csv"): "kb.resource_skill",
        os.path.join("data", "seed", "kb", "resource_course.csv"): "kb.resource_course",
        os.path.join("data", "seed", "kb", "exercise.csv"): "kb.exercise",
        os.path.join("data", "seed", "kb", "goal.csv"): "kb.goal",
        os.path.join("data", "seed", "kb", "goal_skill_requirement.csv"): "kb.goal_skill_requirement",
        os.path.join("data", "seed", "kb", "goal_milestone.csv"): "kb.goal_milestone",
        os.path.join("data", "seed", "kb", "mastery_criteria.json"): "kb.mastery_criteria",
        os.path.join("data", "seed", "kb", "research_area.csv"): "kb.research_area",
        os.path.join("data", "seed", "kb", "faculty.csv"): "kb.faculty",
        os.path.join("data", "seed", "kb", "research_project.csv"): "kb.research_project",
        os.path.join("data", "seed", "kb", "consultancy_engagement.csv"): "kb.consultancy_engagement",
        os.path.join("data", "seed", "kb", "publication.csv"): "kb.publication",
        os.path.join("data", "seed", "kb", "project_faculty.csv"): "kb.project_faculty",
        os.path.join("data", "seed", "kb", "project_keyword.csv"): "kb.project_keyword",
        os.path.join("data", "seed", "kb", "keyword_skill.csv"): "kb.keyword_skill",
        os.path.join("data", "seed", "kb", "data_issue.csv"): "kb.data_issue",

        # core_to_core
        os.path.join("data", "seed", "core_to_core", "academic_calendar.csv"): "kb.academic_calendar",
        os.path.join("data", "seed", "core_to_core", "area_skills.csv"): "kb.area_skill",
        os.path.join("data", "seed", "core_to_core", "faculty_areas.csv"): "kb.faculty_area",
        os.path.join("data", "seed", "core_to_core", "papers.csv"): "kb.paper",
        os.path.join("data", "seed", "core_to_core", "paper_authors.csv"): "kb.paper_author",
        os.path.join("data", "seed", "core_to_core", "paper_chunks.csv"): "kb.paper_chunk",
        os.path.join("data", "seed", "core_to_core", "paper_skills.csv"): "kb.paper_skill",
        os.path.join("data", "seed", "core_to_core", "taster_tasks.csv"): "kb.taster_task",
        os.path.join("data", "seed", "core_to_core", "industry_milestones.csv"): "kb.industry_milestone",

        # mba
        os.path.join("data", "seed", "mba", "mba_routes.csv"): "kb.mba_route",
        os.path.join("data", "seed", "mba", "mba_exams.csv"): "kb.mba_exam",
        os.path.join("data", "seed", "mba", "mba_exam_cycles.csv"): "kb.mba_exam_cycle",
        os.path.join("data", "seed", "mba", "mba_exam_sections.csv"): "kb.mba_exam_section",
        os.path.join("data", "seed", "mba", "mba_syllabus_topics.csv"): "kb.mba_syllabus_topic",
        os.path.join("data", "seed", "mba", "mba_institutions.csv"): "kb.mba_institution",
        os.path.join("data", "seed", "mba", "mba_programmes.csv"): "kb.mba_programme",
        os.path.join("data", "seed", "mba", "mba_admission_stats.csv"): "kb.mba_admission_stat",
        os.path.join("data", "seed", "mba", "mba_milestones.csv"): "kb.mba_milestone",
        os.path.join("data", "seed", "mba", "mba_prep_templates.csv"): "kb.mba_prep_template",
        os.path.join("data", "seed", "mba", "mba_template_phases.csv"): "kb.mba_template_phase",
        os.path.join("data", "seed", "mba", "mba_practice_items.csv"): "kb.mba_practice_item",
        os.path.join("data", "seed", "mba", "mba_interview_questions.csv"): "kb.mba_interview_question",
        os.path.join("data", "seed", "mba", "mba_interview_rubric.csv"): "kb.mba_interview_rubric",
        os.path.join("data", "seed", "mba", "mba_application_checklist_items.csv"): "kb.mba_application_checklist_item",
        os.path.join("data", "seed", "mba", "mba_learning_methods.csv"): "kb.mba_learning_method",
        os.path.join("data", "seed", "mba", "mba_resources.csv"): "kb.mba_resource",

        # core_to_mba
        os.path.join("data", "seed", "core_to_mba", "career_paths.csv"): "kb.career_path",
        os.path.join("data", "seed", "core_to_mba", "branch_pi_topics.csv"): "kb.branch_pi_topic",
        os.path.join("data", "seed", "core_to_mba", "branch_pi_questions.csv"): "kb.branch_pi_question",
        os.path.join("data", "seed", "core_to_mba", "profile_audit_rubric.csv"): "kb.profile_audit_rubric",
        os.path.join("data", "seed", "core_to_mba", "profile_actions.csv"): "kb.profile_action",
        os.path.join("data", "seed", "core_to_mba", "story_drafts.csv"): "student.story_draft",
        os.path.join("data", "seed", "core_to_mba", "decision_options.csv"): "student.decision_option",

        # core_to_mtech
        os.path.join("data", "seed", "core_to_mtech", "routes.csv"): "kb.route",
        os.path.join("data", "seed", "core_to_mtech", "exams.csv"): "kb.exam",
        os.path.join("data", "seed", "core_to_mtech", "exam_cycles.csv"): "kb.exam_cycle",
        os.path.join("data", "seed", "core_to_mtech", "exam_papers.csv"): "kb.exam_paper",
        os.path.join("data", "seed", "core_to_mtech", "syllabus_topics.csv"): "kb.syllabus_topic",
        os.path.join("data", "seed", "core_to_mtech", "topic_weightage.csv"): "kb.topic_weightage",
        os.path.join("data", "seed", "core_to_mtech", "course_topic_map.csv"): "kb.course_topic_map",
        os.path.join("data", "seed", "core_to_mtech", "pyq_items.csv"): "kb.pyq_item",
        os.path.join("data", "seed", "core_to_mtech", "institutions.csv"): "kb.institution",
        os.path.join("data", "seed", "core_to_mtech", "programmes.csv"): "kb.higher_programme",
        os.path.join("data", "seed", "core_to_mtech", "admission_stats.csv"): "kb.admission_stat",
        os.path.join("data", "seed", "core_to_mtech", "psus.csv"): "kb.psu",
        os.path.join("data", "seed", "core_to_mtech", "psu_cycles.csv"): "kb.psu_cycle",
        os.path.join("data", "seed", "core_to_mtech", "counselling_cycles.csv"): "kb.counselling_cycle",
        os.path.join("data", "seed", "core_to_mtech", "prep_templates.csv"): "kb.prep_template",
        os.path.join("data", "seed", "core_to_mtech", "template_phases.csv"): "kb.template_phase",
    }


def load_all_seed_tables_in_memory(base_dir: str = BASE_DIR) -> Dict[str, List[Dict[str, Any]]]:
    """
    Reads all seed files into an in-memory dictionary of table_name -> list of row dicts.
    """
    file_to_table = get_seed_file_mappings(base_dir)
    table_data: Dict[str, List[Dict[str, Any]]] = {}

    for rel_path, table_name in file_to_table.items():
        abs_path = os.path.join(base_dir, rel_path)
        if not os.path.exists(abs_path):
            continue

        if abs_path.endswith(".csv"):
            with open(abs_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = [{k.lower().strip(): (v.strip() if v is not None else "") for k, v in row.items()} for row in reader]
                table_data.setdefault(table_name, []).extend(rows)
        elif abs_path.endswith(".json"):
            with open(abs_path, "r", encoding="utf-8") as f:
                items = json.load(f)
                rows = [{k.lower().strip(): v for k, v in item.items()} for item in items]
                table_data.setdefault(table_name, []).extend(rows)

    return table_data


def check_all_foreign_keys(base_dir: str = BASE_DIR) -> List[Dict[str, Any]]:
    """
    Performs comprehensive pre-load foreign key orphan detection.
    Returns list of orphan violation dictionaries:
      [
        {
          "file": "data/seed/kb/module.csv",
          "row": 6,
          "column": "course_id",
          "value": "EE3L001",
          "referenced_table": "kb.course",
          "referenced_column": "course_id"
        },
        ...
      ]
    """
    init_sql = os.path.join(base_dir, "docker", "init.sql")
    table_pks, table_fks = parse_init_sql_fks(init_sql)
    table_data = load_all_seed_tables_in_memory(base_dir)
    file_to_table = get_seed_file_mappings(base_dir)

    orphans: List[Dict[str, Any]] = []

    # 1. Standard mapped seed files
    for rel_path, table_name in file_to_table.items():
        abs_path = os.path.join(base_dir, rel_path)
        if not os.path.exists(abs_path):
            continue

        fks = table_fks.get(table_name, [])
        if not fks:
            continue

        if abs_path.endswith(".csv"):
            with open(abs_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row_idx, row in enumerate(reader, start=2): # Line 1 is header
                    row_lower = {k.lower().strip(): (v.strip() if v is not None else "") for k, v in row.items()}
                    for col, ref_table, ref_col in fks:
                        val = row_lower.get(col)
                        if not val or val.lower() in ("none", "nan", "null"):
                            continue

                        ref_rows = table_data.get(ref_table, [])
                        ref_values = {str(r.get(ref_col, "")).strip() for r in ref_rows}
                        if val not in ref_values:
                            orphans.append({
                                "file": rel_path.replace("\\", "/"),
                                "row": row_idx,
                                "column": col,
                                "value": val,
                                "referenced_table": ref_table,
                                "referenced_column": ref_col
                            })
        elif abs_path.endswith(".json"):
            with open(abs_path, "r", encoding="utf-8") as f:
                items = json.load(f)
                for item_idx, item in enumerate(items, start=1):
                    item_lower = {k.lower().strip(): item[k] for k in item}
                    for col, ref_table, ref_col in fks:
                        val = item_lower.get(col)
                        if val is None or str(val).strip().lower() in ("", "none", "nan", "null"):
                            continue
                        val_str = str(val).strip()
                        ref_rows = table_data.get(ref_table, [])
                        ref_values = {str(r.get(ref_col, "")).strip() for r in ref_rows}
                        if val_str not in ref_values:
                            orphans.append({
                                "file": rel_path.replace("\\", "/"),
                                "row": item_idx,
                                "column": col,
                                "value": val_str,
                                "referenced_table": ref_table,
                                "referenced_column": ref_col
                            })

    # 2. Persona student seeds: data/seed/personas/*/students.csv
    persona_pattern = os.path.join(base_dir, "data", "seed", "personas", "*", "students.csv")
    for persona_file in sorted(glob.glob(persona_pattern)):
        rel_persona_path = os.path.relpath(persona_file, base_dir).replace("\\", "/")
        with open(persona_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, start=2):
                prog = row.get("programme_id", "").strip()
                if prog:
                    prog_rows = table_data.get("kb.programme", [])
                    known_progs = {str(r.get("programme_id", "")).strip() for r in prog_rows}
                    if prog not in known_progs:
                        orphans.append({
                            "file": rel_persona_path,
                            "row": row_idx,
                            "column": "programme_id",
                            "value": prog,
                            "referenced_table": "kb.programme",
                            "referenced_column": "programme_id"
                        })

                # Check completed_courses
                completed_raw = row.get("completed_courses", "")
                if completed_raw:
                    courses = [c.strip() for c in completed_raw.split(";") if c.strip()]
                    course_rows = table_data.get("kb.course", [])
                    known_courses = {str(r.get("course_id", "")).strip() for r in course_rows}
                    for c_code in courses:
                        if c_code not in known_courses:
                            orphans.append({
                                "file": rel_persona_path,
                                "row": row_idx,
                                "column": "completed_courses",
                                "value": c_code,
                                "referenced_table": "kb.course",
                                "referenced_column": "course_id"
                            })

    # 3. Persona exercise seeds: data/seed/personas/*/exercises.csv
    exercise_pattern = os.path.join(base_dir, "data", "seed", "personas", "*", "exercises.csv")
    for ex_file in sorted(glob.glob(exercise_pattern)):
        rel_ex_path = os.path.relpath(ex_file, base_dir).replace("\\", "/")
        with open(ex_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, start=2):
                sid = row.get("skill_id", "").strip()
                if sid:
                    known_skills = {str(r.get("skill_id", "")).strip() for r in table_data.get("kb.skill", [])}
                    if sid not in known_skills:
                        orphans.append({
                            "file": rel_ex_path,
                            "row": row_idx,
                            "column": "skill_id",
                            "value": sid,
                            "referenced_table": "kb.skill",
                            "referenced_column": "skill_id"
                        })
                mid = row.get("module_id", "").strip()
                if mid:
                    known_mods = {str(r.get("module_id", "")).strip() for r in table_data.get("kb.module", [])}
                    if mid not in known_mods:
                        orphans.append({
                            "file": rel_ex_path,
                            "row": row_idx,
                            "column": "module_id",
                            "value": mid,
                            "referenced_table": "kb.module",
                            "referenced_column": "module_id"
                        })

    return orphans


def main():
    print("=" * 80)
    print("Foreign Key Orphan Detection Scan (data/seed/ & docker/init.sql)")
    print("=" * 80)

    try:
        orphans = check_all_foreign_keys(BASE_DIR)
    except Exception as e:
        print(f"[FATAL] Failed to scan foreign key constraints: {e}")
        sys.exit(2)

    if not orphans:
        print("\n[OK] Clean bill of health! Zero foreign key orphans found across all seed files.")
        sys.exit(0)

    print(f"\n[ALERT] Found {len(orphans)} foreign key orphan violation(s):\n")
    print(f"{'File':<45} {'Row':<5} {'Column':<20} {'Value':<25} {'Referenced Table'}")
    print("-" * 125)
    for o in orphans:
        print(f"{o['file']:<45} {o['row']:<5} {o['column']:<20} {o['value']:<25} {o['referenced_table']}({o['referenced_column']})")

    print("-" * 125)
    print(f"Total Orphans: {len(orphans)}")
    print("\nPlease resolve all orphans prior to executing database seed loader.")
    sys.exit(1)


if __name__ == "__main__":
    main()
