import csv
import re
import json

def parse_curriculum():
    with open("data/raw/ee/curriculum_semester_table.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    courses = {} # code -> dict
    slots = []   # list of slot dicts
    slot_options = [] # (slot_id, course_code)
    current_sem = None
    current_pool = None
    semester_totals = []

    # Alias map for resolving prerequisite names to course codes
    alias_map = {
        "none": None,
        "—": None,
        "": None,
        "mathematics – 1": "MA1L001",
        "mathematics - 1": "MA1L001",
        "mathematics-1": "MA1L001",
        "mathematics – 2": "MA1L002",
        "mathematics - 2": "MA1L002",
        "electrical technology": "EE1L001",
        "introduction to programing and data structures": "CS1L001",
        "introduction to programming and data structures": "CS1L001",
        "introduction to electronics": "EC2L001",
        "signals and systems": "EC2L002",
        "signals & systems": "EC2L002",
        "network theory": "EE2L001",
        "electric machines": "EE2L003",
        "digital electronics and microprocessor": "EC2L006",
        "digital electronics and microprocessors": "EC2L006",
        "power electronics": "EE3L004",
        "electrical power transmission and distribution": "EE3L007",
        "measurement and instrumentation": "EE3L010",
        "electromagnetic field theory": "EE3L011",
        "control systems": "EE3L003",
        "digital signal processing": "EC3L003",
        "power system operation and control": "EE3L012",
        "semiconductor devices": "EC4L001",
        "image and video processing": "EC6L002",
        "image & video processing": "EC6L002",
        "high voltage engineering": "EE6L009",
        "renewable energy systems": "EE4L006",
        "probability statistics and stochastic processes": "MA2L003",
        "probability and statistics processes": "MA2L003",
        "probability and stochastic processes": "MA2L003",
    }

    raw_prereq_tokens = [] # (course_code, raw_token)
    
    # Track semester header lines for min/max credits
    for r in rows:
        if not r or not any(r):
            continue
        col0 = r[0].strip()
        col1 = r[1].strip() if len(r) > 1 else ""
        col2 = r[2].strip() if len(r) > 2 else ""

        # Check for semester header
        if col0.startswith("SEMESTER –"):
            # e.g. SEMESTER – I      |      Total credits: 22/23 + 1      |      Total contact hours: 25/26 + 3
            m = re.search(r"SEMESTER – ([IVXLCDM]+)\s+\|\s+Total credits:\s*([^|]+)", col0)
            if m:
                sem_roman = m.group(1)
                credits_str = m.group(2).strip()
                semester_totals.append((sem_roman, credits_str))
            continue

        if col0.startswith("▸"):
            current_pool = col0
            continue

        # Regular or pool row
        sem = col0
        course_name = col1
        course_code = col2
        ltp = r[3].strip() if len(r) > 3 else ""
        credits_val = r[4].strip() if len(r) > 4 else ""
        contact_hours = r[5].strip() if len(r) > 5 else ""
        course_type = r[6].strip() if len(r) > 6 else ""
        prereqs = r[7].strip() if len(r) > 7 else ""
        text_books = r[8].strip() if len(r) > 8 else ""
        ref_books = r[9].strip() if len(r) > 9 else ""
        notes = r[10].strip() if len(r) > 10 else ""

        # Slot row detection
        is_slot = False
        if course_code in ["(no code in source)", "(see options)", "(see pool)"] or "Lateral –" in course_name or "Breadth –" in course_name or "Elective –" in course_name:
            if not current_pool: # It's a slot definition in the semester table
                is_slot = True

        if is_slot:
            slot_id = f"{sem}_{course_name}".replace(" ", "_").replace("–", "-").replace("(", "").replace(")", "").replace("/", "_")
            slots.append({
                "slot_id": slot_id,
                "semester": sem,
                "slot_name": course_name,
                "credits": credits_val,
                "contact_hours": contact_hours,
                "course_type": course_type
            })
            continue

        # If it's a paired row (e.g. Physics / Chemistry, PH1L001 / CY1L001)
        if " / " in course_code:
            codes = [c.strip() for c in course_code.split(" / ")]
            names = [n.strip() for n in course_name.split(" / ")]
            ltps = [l.strip() for l in ltp.split(" / ")]
            creds = [c.strip() for c in credits_val.split(" / ")]
            contacts = [ch.strip() for ch in contact_hours.split(" / ")]

            # Handle HS1L001 or HS1L002
            # Let's see: codes may contain 'or'
            sub_pairs = []
            for i, c in enumerate(codes):
                name = names[i] if i < len(names) else names[-1]
                l = ltps[i] if i < len(ltps) else ltps[-1]
                cr = creds[i] if i < len(creds) else creds[-1]
                ch = contacts[i] if i < len(contacts) else contacts[-1]
                if " or " in c:
                    sub_c = [sc.strip() for sc in c.split(" or ")]
                    sub_n = [sn.strip() for sn in name.split(" or ")]
                    sub_l = [sl.strip() for sl in l.split(" or ")]
                    sub_ch = [sch.strip() for sch in ch.split(" or ")]
                    for j, sc in enumerate(sub_c):
                        sn = sub_n[j] if j < len(sub_n) else sub_n[-1]
                        sl = sub_l[j] if j < len(sub_l) else sub_l[-1]
                        sch = sub_ch[j] if j < len(sub_ch) else sub_ch[-1]
                        sub_pairs.append((sc, sn, sl, cr, sch, course_type, sem, prereqs, text_books, ref_books, notes))
                else:
                    sub_pairs.append((c, name, l, cr, ch, course_type, sem, prereqs, text_books, ref_books, notes))

            for c, name, l, cr, ch, ctype, s, pr, tb, rb, nt in sub_pairs:
                if c not in courses:
                    courses[c] = {
                        "course_code": c,
                        "title": name,
                        "ltp": l,
                        "credits": cr,
                        "contact_hours": ch,
                        "course_type": ctype,
                        "semesters": [s],
                        "prereqs": pr,
                        "text_books": tb,
                        "ref_books": rb,
                        "notes": nt,
                        "in_semester_table": True,
                        "pool": current_pool
                    }
                else:
                    if s not in courses[c]["semesters"]:
                        courses[c]["semesters"].append(s)
            continue

        # Single course row
        c = course_code.strip()
        if c:
            if c not in courses:
                courses[c] = {
                    "course_code": c,
                    "title": course_name,
                    "ltp": ltp,
                    "credits": credits_val,
                    "contact_hours": contact_hours,
                    "course_type": course_type,
                    "semesters": [sem],
                    "prereqs": prereqs,
                    "text_books": text_books,
                    "ref_books": ref_books,
                    "notes": notes,
                    "in_semester_table": True,
                    "pool": current_pool
                }
            else:
                if sem not in courses[c]["semesters"]:
                    courses[c]["semesters"].append(sem)

    # Now add syllabus only courses
    with open("data/raw/ee/curriculum_syllabus_only.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            c = r["Course Code"].strip()
            courses[c] = {
                "course_code": c,
                "title": r["Course Name"].strip(),
                "ltp": r["L-T-P"].strip(),
                "credits": r["Credits"].strip(),
                "contact_hours": r["Contact Hours"].strip(),
                "course_type": r["Course Type"].strip(),
                "semesters": [],
                "prereqs": r["Prerequisites"].strip(),
                "text_books": r["Text Books"].strip(),
                "ref_books": r["Reference Books"].strip(),
                "notes": r["Notes"].strip(),
                "in_semester_table": False,
                "pool": "Syllabus-only"
            }

    # Extract and resolve prerequisites
    prereq_resolved = []
    prereq_unresolved = []

    for c, cdata in courses.items():
        raw_pr = cdata["prereqs"]
        if not raw_pr or raw_pr in ["—", "None"]:
            continue
        
        # Check if prereqs are structured with [CODE] or prefix like "EE1P001: Electrical Technology"
        lines = [line.strip() for line in raw_pr.split("\n") if line.strip()]
        for line in lines:
            if ":" in line and not line.startswith("http"):
                prefix, reqs = line.split(":", 1)
                prefix = prefix.strip()
                # If prefix is another course code or this course code
                target_code = prefix if prefix in courses else c
                for token in reqs.split(","):
                    tok = token.strip()
                    if not tok or tok in ["None", "—"]:
                        continue
                    clean_tok = tok.lower()
                    resolved = alias_map.get(clean_tok)
                    if resolved:
                        prereq_resolved.append((target_code, tok, resolved))
                    else:
                        prereq_unresolved.append((target_code, tok))
            else:
                for token in line.split(","):
                    tok = token.strip()
                    if not tok or tok in ["None", "—"]:
                        continue
                    clean_tok = tok.lower()
                    resolved = alias_map.get(clean_tok)
                    if resolved:
                        prereq_resolved.append((c, tok, resolved))
                    else:
                        prereq_unresolved.append((c, tok))

    return courses, slots, prereq_resolved, prereq_unresolved, semester_totals

def parse_playlists():
    with open("data/raw/ee/video_playlists.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    status_counts = {}
    for r in rows:
        cov = r["Coverage"].strip()
        status_counts[cov] = status_counts.get(cov, 0) + 1
    return len(rows), status_counts

def parse_projects():
    with open("data/raw/ee/research_projects_all.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    with open("data/raw/ee/research_projects_v2.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        v2_rows = list(reader)

    # v2 has 68 full projects
    # all has 138 projects
    # title_only = 138 - 68 = 70
    
    # Parse faculty from v2
    faculty_persons = set()
    faculty_groups = set()
    faculty_raw_entries = []

    group_keywords = ["Group", "Team", "Consortium", "Interdisciplinary", "SECS Power Group", "SECS Control/Power Team", "SECS Comm. Group", "Power Electronics Group", "SECS IoT/VLSI Team", "SECS Faculty Team"]

    for r in v2_rows:
        prof_col = r["Prof. Name (PI / Co-PI)"].strip()
        # split on '&', '/', 'and'
        parts = re.split(r"&|/|\band\b", prof_col)
        for p in parts:
            p = p.strip()
            if not p:
                continue
            # clean suffixes
            p_clean = re.sub(r"\(PI\)", "", p)
            p_clean = re.sub(r"\(Co-PI\)", "", p_clean)
            p_clean = re.sub(r"\(IITBBS Lead\)", "", p_clean)
            p_clean = re.sub(r"\(Co-PI, with [^)]+\)", "", p_clean)
            p_clean = p_clean.strip()
            if not p_clean:
                continue

            is_group = any(gk.lower() in p_clean.lower() for gk in group_keywords)
            if is_group:
                faculty_groups.add(p_clean)
            else:
                faculty_persons.add(p_clean)
            faculty_raw_entries.append((p_clean, is_group))

    return len(all_rows), len(v2_rows), len(all_rows) - len(v2_rows), len(faculty_persons), len(faculty_groups), faculty_persons, faculty_groups

if __name__ == "__main__":
    courses, slots, prereq_resolved, prereq_unresolved, semester_totals = parse_curriculum()
    print(f"Total Unique Courses: {len(courses)}")
    print(f"Total Slots: {len(slots)}")
    print(f"Prerequisites Resolved: {len(prereq_resolved)}")
    print(f"Prerequisites Unresolved: {len(prereq_unresolved)}")
    if prereq_unresolved:
        print(f"  Unresolved list: {prereq_unresolved}")
    
    total_resources, status_counts = parse_playlists()
    print(f"\nTotal Playlists/Resources: {total_resources}")
    print(f"Resource status counts: {status_counts}")

    total_all, total_v2, title_only, n_persons, n_groups, persons, groups = parse_projects()
    print(f"\nTotal Projects (all): {total_all}")
    print(f"  Detail level 'full' (from v2): {total_v2}")
    print(f"  Detail level 'title_only' (from all): {title_only}")
    print(f"Faculty Persons ({n_persons}): {sorted(list(persons))}")
    print(f"Faculty Groups ({n_groups}): {sorted(list(groups))}")

