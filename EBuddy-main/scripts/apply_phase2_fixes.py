import os
import csv

def run_fixes():
    seed_kb = os.path.join("data", "seed", "kb")
    
    # -------------------------------------------------------------
    # 1. Update source.csv with DESIGN_TEAM
    # -------------------------------------------------------------
    source_path = os.path.join(seed_kb, "source.csv")
    with open(source_path, "r", encoding="utf-8") as f:
        sources = list(csv.DictReader(f))
    
    source_ids = {s["source_id"] for s in sources}
    if "DESIGN_TEAM" not in source_ids:
        sources.append({
            "source_id": "DESIGN_TEAM",
            "title": "Inter-IIT Ebuddy Design Team Draft Curriculum & Taxonomy",
            "url": "https://internal.design_team",
            "publisher": "Design Team",
            "licence": "Internal Working Draft",
            "retrieved_on": "2026-11-14",
            "doc_type": "taxonomy",
            "reliability": "draft_for_review",
            "academic_year": "2026",
            "notes": "Draft skills, goals, and course associations provided by design team"
        })
        with open(source_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(sources[0].keys()))
            writer.writeheader()
            writer.writerows(sources)
        print("Added DESIGN_TEAM to source.csv")

    # -------------------------------------------------------------
    # 2. Fix 1: Skills attribution
    # -------------------------------------------------------------
    skill_path = os.path.join(seed_kb, "skill.csv")
    with open(skill_path, "r", encoding="utf-8") as f:
        skills = list(csv.DictReader(f))

    ee_skill_ids = [
        "SKILL_CIRCUIT_ANALYSIS", "SKILL_SIGNALS_SYSTEMS", "SKILL_ANALOG_ELECTRONICS",
        "SKILL_DIGITAL_LOGIC", "SKILL_POWER_ELECTRONICS", "SKILL_POWER_SYSTEMS",
        "SKILL_POWER_GRID_CONTROL", "SKILL_ELECTRIC_MACHINES", "SKILL_CONTROL_SYSTEMS",
        "SKILL_EM_FIELDS", "SKILL_DSP", "SKILL_VLSI_DESIGN", "SKILL_EMBEDDED_SYSTEMS",
        "SKILL_PROGRAMMING_DS", "SKILL_PROBABILITY_STATS", "SKILL_AI_ML",
        "SKILL_RENEWABLE_ENERGY", "SKILL_INSTRUMENTATION", "SKILL_HIGH_VOLTAGE"
    ]
    
    updated_skills = []
    for s in skills:
        sk_id = s["skill_id"]
        if sk_id in ee_skill_ids:
            s["source_id"] = "DESIGN_TEAM"
            s["status"] = "draft_for_review"
        else:
            s["source_id"] = "UNSOURCED_AI_DRAFT"
            s["status"] = "draft_for_review"
        updated_skills.append(s)

    with open(skill_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(skills[0].keys()))
        writer.writeheader()
        writer.writerows(updated_skills)
    print(f"Updated {len(updated_skills)} skills: {len(ee_skill_ids)} from DESIGN_TEAM, {len(updated_skills)-len(ee_skill_ids)} from UNSOURCED_AI_DRAFT")

    # -------------------------------------------------------------
    # 3. Fix 1: Course-Skill mapping_method and attribution
    # -------------------------------------------------------------
    cs_path = os.path.join(seed_kb, "course_skill.csv")
    with open(cs_path, "r", encoding="utf-8") as f:
        course_skills = list(csv.DictReader(f))

    fieldnames = ["course_id", "skill_id", "level_taught", "weight", "mapping_method", "status", "source_id"]
    updated_cs = []
    for cs in course_skills:
        cid = cs["course_id"]
        # Determine source
        if cid.startswith("ML") or cid.startswith("MM"):
            src = "UNSOURCED_AI_DRAFT"
        else:
            src = "DESIGN_TEAM"
        updated_cs.append({
            "course_id": cs["course_id"],
            "skill_id": cs["skill_id"],
            "level_taught": cs["level_taught"],
            "weight": cs.get("weight", "1.0"),
            "mapping_method": "inferred_from_course_title",
            "status": "draft_for_review",
            "source_id": src
        })

    with open(cs_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_cs)
    print(f"Updated {len(updated_cs)} course_skills with mapping_method='inferred_from_course_title'")

    # -------------------------------------------------------------
    # 4. Fix 2: Remove 17 consultancy entries from research_project
    # -------------------------------------------------------------
    proj_path = os.path.join(seed_kb, "research_project.csv")
    with open(proj_path, "r", encoding="utf-8") as f:
        projects = list(csv.DictReader(f))

    clean_projects = [p for p in projects if not p["project_id"].startswith("PROJ_MM_CONS_")]
    removed_pids = {p["project_id"] for p in projects if p["project_id"].startswith("PROJ_MM_CONS_")}

    with open(proj_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(projects[0].keys()))
        writer.writeheader()
        writer.writerows(clean_projects)
    
    smmme_count = sum(1 for p in clean_projects if p["source_id"] == "IITBBS_SMMME_PROJECTS_2026")
    print(f"Research projects: removed {len(removed_pids)} consultancy rows. Total = {len(clean_projects)}, SMMME = {smmme_count}")

    # Clean project_faculty and project_keyword
    pf_path = os.path.join(seed_kb, "project_faculty.csv")
    with open(pf_path, "r", encoding="utf-8") as f:
        pf_rows = list(csv.DictReader(f))
    clean_pf = [r for r in pf_rows if r["project_id"] not in removed_pids]
    with open(pf_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(pf_rows[0].keys()))
        writer.writeheader()
        writer.writerows(clean_pf)

    pk_path = os.path.join(seed_kb, "project_keyword.csv")
    with open(pk_path, "r", encoding="utf-8") as f:
        pk_rows = list(csv.DictReader(f))
    clean_pk = [r for r in pk_rows if r["project_id"] not in removed_pids]
    with open(pk_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(pk_rows[0].keys()))
        writer.writeheader()
        writer.writerows(clean_pk)

    # -------------------------------------------------------------
    # 5. Fix 4: Library subsets classification_method = 'school_field'
    # -------------------------------------------------------------
    for lib_f in ["publications_electrical.csv", "publications_metallurgy.csv"]:
        fpath = os.path.join("data", "raw", "library", lib_f)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                r = csv.DictReader(f)
                rows = list(r)
                fnames = r.fieldnames
            if "classification_method" in fnames:
                for row in rows:
                    row["classification_method"] = "school_field"
            else:
                fnames.append("classification_method")
                for row in rows:
                    row["classification_method"] = "school_field"
            with open(fpath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"Updated {lib_f} classification_method to 'school_field'")

    # -------------------------------------------------------------
    # 6. Fix 5: Move course_type from kb.course to programme_requirement
    # -------------------------------------------------------------
    course_path = os.path.join(seed_kb, "course.csv")
    with open(course_path, "r", encoding="utf-8") as f:
        courses = list(csv.DictReader(f))

    # Keep course details for building programme requirements
    course_lookup = {c["course_id"]: c for c in courses}

    # Clean course.csv: remove course_type and type_source
    course_fields = [
        "course_id", "course_code", "display_code", "code_conflict", "title",
        "department_id", "credits", "ltp", "mode", "level",
        "syllabus_text", "learning_objectives", "in_semester_table", "source_id", "is_placeholder"
    ]
    cleaned_courses = []
    for c in courses:
        row = {k: c.get(k, "") for k in course_fields}
        cleaned_courses.append(row)

    with open(course_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=course_fields)
        writer.writeheader()
        writer.writerows(cleaned_courses)
    print(f"Cleaned course.csv: removed course_type and type_source from {len(cleaned_courses)} courses")

    # Read existing slots
    prog_req_path = os.path.join(seed_kb, "programme_requirement.csv")
    with open(prog_req_path, "r", encoding="utf-8") as f:
        existing_reqs = list(csv.DictReader(f))

    req_fields = [
        "slot_id", "programme_id", "semester_number", "slot_name", "slot_type",
        "min_credits", "max_credits", "option_pool", "course_id", "course_type", "status", "source_id"
    ]

    all_programme_requirements = []

    # 1. Preserve existing 25 slot rows
    for r in existing_reqs:
        # Check if already migrated
        slot_type = r.get("slot_type", "")
        all_programme_requirements.append({
            "slot_id": r["slot_id"],
            "programme_id": r["programme_id"],
            "semester_number": r["semester_number"],
            "slot_name": r["slot_name"],
            "slot_type": slot_type,
            "min_credits": r["min_credits"],
            "max_credits": r["max_credits"],
            "option_pool": r.get("option_pool", ""),
            "course_id": "",
            "course_type": slot_type.lower(),
            "status": "verified",
            "source_id": "IITBBS_EE_CURRICULUM_2016_17" if r["programme_id"] == "BTECH_EE" else "IITBBS_MME_CURRICULUM_2016_17"
        })

    # 2. Add EE Course Requirements
    # EE semester table
    ee_sem_csv = os.path.join("data", "raw", "ee", "curriculum_semester_table.csv")
    with open(ee_sem_csv, "r", encoding="utf-8") as f:
        ee_sem_rows = list(csv.DictReader(f))

    ee_added = set()
    for row in ee_sem_rows:
        ccode = row.get("Course Code", "").strip()
        ctype = row.get("Course Type", "").strip() or "core"
        sem_str = row.get("Semester", "").strip()
        if ccode and ccode in course_lookup and ccode not in ["(see options)", "(no code in source)"]:
            sem_num = ""
            for token in sem_str.split():
                if token in ["I", "1"]: sem_num = "1"
                elif token in ["II", "2"]: sem_num = "2"
                elif token in ["III", "3"]: sem_num = "3"
                elif token in ["IV", "4"]: sem_num = "4"
                elif token in ["V", "5"]: sem_num = "5"
                elif token in ["VI", "6"]: sem_num = "6"
                elif token in ["VII", "7"]: sem_num = "7"
                elif token in ["VIII", "8"]: sem_num = "8"
            
            cinfo = course_lookup[ccode]
            req_id = f"REQ_EE_{ccode}"
            if req_id not in ee_added:
                ee_added.add(req_id)
                all_programme_requirements.append({
                    "slot_id": req_id,
                    "programme_id": "BTECH_EE",
                    "semester_number": sem_num,
                    "slot_name": cinfo["title"],
                    "slot_type": "core" if "core" in ctype.lower() else ctype.lower(),
                    "min_credits": cinfo["credits"],
                    "max_credits": cinfo["credits"],
                    "option_pool": "",
                    "course_id": ccode,
                    "course_type": ctype,
                    "status": "verified",
                    "source_id": "IITBBS_EE_CURRICULUM_2016_17"
                })

    # Add EE Syllabus-only courses (EC2L005, EC6L004)
    ee_syll_csv = os.path.join("data", "raw", "ee", "curriculum_syllabus_only.csv")
    with open(ee_syll_csv, "r", encoding="utf-8") as f:
        ee_syll_rows = list(csv.DictReader(f))
    for row in ee_syll_rows:
        ccode = row.get("Course Code", "").strip()
        ctype = row.get("Course Type", "").strip()
        if ccode in course_lookup:
            cinfo = course_lookup[ccode]
            req_id = f"REQ_EE_{ccode}"
            if req_id not in ee_added:
                ee_added.add(req_id)
                all_programme_requirements.append({
                    "slot_id": req_id,
                    "programme_id": "BTECH_EE",
                    "semester_number": "",
                    "slot_name": cinfo["title"],
                    "slot_type": "common_core" if "common core" in ctype.lower() else "elective",
                    "min_credits": cinfo["credits"],
                    "max_credits": cinfo["credits"],
                    "option_pool": "",
                    "course_id": ccode,
                    "course_type": ctype, # 'Common Core' for EC2L005, 'Vertical Elective' for EC6L004
                    "status": "verified",
                    "source_id": "IITBBS_EE_CURRICULUM_2016_17"
                })

    # 3. Add MME Course Requirements
    # Sem III-VIII Core courses + EC2L005 (Common Core)
    mme_core_courses = [
        ("EC2L005", "3", "Common Core"), # Explicit: Common Core for MME
        ("ML2L001", "3", "core"),
        ("ML2L002", "3", "core"),
        ("ML2L003", "3", "core"),
        ("ML2P001", "3", "core"),
        ("ML2P002", "3", "core"),
        ("ML2L004", "4", "core"),
        ("ML2L005", "4", "core"),
        ("ML2L006", "4", "core"),
        ("ML2P003", "4", "core"),
        ("ML2P004", "4", "core"),
        ("ML3L001", "5", "core"),
        ("ML3L002", "5", "core"),
        ("ML3L003", "5", "core"),
        ("ML3P001", "5", "core"),
        ("ML3P002", "5", "core"),
        ("ML3L004", "6", "core"),
        ("ML3L005", "6", "core"),
        ("ML3L006", "6", "core"),
        ("ML3P003", "6", "core"),
        ("ML3P004", "6", "core"),
        ("ML4L001_CORE", "7", "core"),
        ("ML4L002_CORE", "7", "core"),
        ("ML4L003_CORE", "7", "core"),
        ("ML4P001", "7", "core"),
        ("ML4P002", "7", "core"),
        ("ML4P003", "7", "core"),
        ("ML4P004", "8", "core")
    ]
    for cid, sem, ctype in mme_core_courses:
        if cid in course_lookup:
            cinfo = course_lookup[cid]
            all_programme_requirements.append({
                "slot_id": f"REQ_MM_{cid}",
                "programme_id": "BTECH_MM",
                "semester_number": sem,
                "slot_name": cinfo["title"],
                "slot_type": "common_core" if ctype == "Common Core" else "core",
                "min_credits": cinfo["credits"],
                "max_credits": cinfo["credits"],
                "option_pool": "",
                "course_id": cid,
                "course_type": ctype, # 'Common Core' for EC2L005
                "status": "verified",
                "source_id": "IITBBS_MME_CURRICULUM_2016_17"
            })

    # Also MME Elective options
    mme_electives = [
        "ML4L001_ELEC", "ML4L002_ELEC", "ML4L003_ELEC", "ML4L004", "ML4L005",
        "ML4L006", "ML4L007", "ML4L008", "ML4L009", "ML4L010",
        "ML4L011", "ML4L012", "ML4L013", "ML4L014", "ML4L015"
    ]
    for cid in mme_electives:
        if cid in course_lookup:
            cinfo = course_lookup[cid]
            all_programme_requirements.append({
                "slot_id": f"REQ_MM_{cid}",
                "programme_id": "BTECH_MM",
                "semester_number": "7" if "ML4L001" in cid or "ML4L002" in cid or "ML4L003" in cid else "8",
                "slot_name": cinfo["title"],
                "slot_type": "elective",
                "min_credits": cinfo["credits"],
                "max_credits": cinfo["credits"],
                "option_pool": "mme_elective_pool",
                "course_id": cid,
                "course_type": "elective",
                "status": "verified",
                "source_id": "IITBBS_MME_CURRICULUM_2016_17"
            })

    # MME Lateral options (ID2L001, ID2L002, ID2L003)
    for cid in ["ID2L001", "ID2L002", "ID2L003"]:
        if cid in course_lookup:
            cinfo = course_lookup[cid]
            all_programme_requirements.append({
                "slot_id": f"REQ_MM_{cid}",
                "programme_id": "BTECH_MM",
                "semester_number": "4",
                "slot_name": cinfo["title"],
                "slot_type": "lateral",
                "min_credits": cinfo["credits"],
                "max_credits": cinfo["credits"],
                "option_pool": "mme_lateral_pool",
                "course_id": cid,
                "course_type": "lateral",
                "status": "verified",
                "source_id": "IITBBS_MME_CURRICULUM_2016_17"
            })

    with open(prog_req_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=req_fields)
        writer.writeheader()
        writer.writerows(all_programme_requirements)
    print(f"Updated programme_requirement.csv: {len(all_programme_requirements)} total rows (25 slots + course requirements per programme)")

if __name__ == "__main__":
    run_fixes()

