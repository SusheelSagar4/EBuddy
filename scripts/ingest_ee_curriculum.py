"""
Ingestion script for IIT Bhubaneswar Electrical Engineering Curriculum & Research Data.
Parses raw files from data/raw/ee/ and outputs structured seed files in data/seed/kb/.
All transformations are deterministic and fully reproducible.
"""

import os
import csv
import re
import json

def run_ingestion():
    os.makedirs("data/seed/kb", exist_ok=True)

    # -------------------------------------------------------------
    # 1. Alias map for prerequisite name resolution
    # -------------------------------------------------------------
    alias_dict = {
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

    # Save course aliases
    with open("data/seed/kb/course_alias.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["alias_name", "target_course_code"])
        for alias, code in sorted(alias_dict.items()):
            writer.writerow([alias, code])

    # -------------------------------------------------------------
    # 2. Parse Curriculum Semester Table & Syllabus-Only
    # -------------------------------------------------------------
    courses = {}          # course_code -> dict
    course_offerings = [] # (course_code, semester_num, parity, track, offering_basis)
    slots = []            # (slot_id, programme_id, semester_num, slot_name, slot_type, min_credits, max_credits, option_pool)
    slot_options = []     # (slot_id, course_code)
    course_prereqs = []   # (course_code, prereq_code, relation)
    unresolved_prereqs = [] # (course_code, raw_name)
    programme_reqs = []   # (programme_id, semester_num, track, min_credits, max_credits)

    with open("data/raw/ee/curriculum_semester_table.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        raw_rows = list(reader)

    current_sem_num = 1
    current_pool = None

    sem_num_map = {
        "Sem I": 1, "Sem II": 2, "Sem III": 3, "Sem IV": 4,
        "Sem V": 5, "Sem VI": 6, "Sem VII": 7, "Sem VIII": 8
    }

    roman_to_int = {
        "I": 1, "II": 2, "III": 3, "IV": 4,
        "V": 5, "VI": 6, "VII": 7, "VIII": 8
    }

    for r in raw_rows:
        if not r or not any(r):
            continue
        c0 = r[0].strip()
        c1 = r[1].strip() if len(r) > 1 else ""
        c2 = r[2].strip() if len(r) > 2 else ""
        c3 = r[3].strip() if len(r) > 3 else ""
        c4 = r[4].strip() if len(r) > 4 else ""
        c5 = r[5].strip() if len(r) > 5 else ""
        c6 = r[6].strip() if len(r) > 6 else ""
        c7 = r[7].strip() if len(r) > 7 else ""
        c8 = r[8].strip() if len(r) > 8 else ""
        c9 = r[9].strip() if len(r) > 9 else ""
        c10 = r[10].strip() if len(r) > 10 else ""

        # Check for semester header
        if c0.startswith("SEMESTER –"):
            current_pool = None
            m = re.search(r"SEMESTER – ([IVXLCDM]+)\s+\|\s+Total credits:\s*([^|]+)", c0)
            if m:
                s_rom = m.group(1)
                current_sem_num = roman_to_int.get(s_rom, current_sem_num)
                cred_range = m.group(2).strip()
                # Parse credit totals like 22/23 + 1
                if "22/23 + 1" in cred_range:
                    programme_reqs.append(("BTECH_EE", current_sem_num, "A", 23, 23))
                    programme_reqs.append(("BTECH_EE", current_sem_num, "B", 24, 24))
                elif "23/22 + 1" in cred_range:
                    programme_reqs.append(("BTECH_EE", current_sem_num, "A", 24, 24))
                    programme_reqs.append(("BTECH_EE", current_sem_num, "B", 23, 23))
                elif "/" in cred_range:
                    parts = cred_range.split("/")
                    p1 = float(re.findall(r"\d+", parts[0])[0])
                    p2 = float(re.findall(r"\d+", parts[1])[0])
                    programme_reqs.append(("BTECH_EE", current_sem_num, "ALL", min(p1, p2), max(p1, p2)))
                else:
                    vals = re.findall(r"\d+", cred_range)
                    tot = float(vals[0]) if vals else 20
                    programme_reqs.append(("BTECH_EE", current_sem_num, "ALL", tot, tot))
            continue

        if c0.startswith("▸"):
            current_pool = c0.replace("▸", "").strip()
            continue

        sem_num = sem_num_map.get(c0, current_sem_num)
        parity = "odd" if sem_num % 2 == 1 else "even"

        # Check for Slot rows
        is_slot = False
        if c2 in ["(no code in source)", "(see options)", "(see pool)"] or any(
            x in c1 for x in ["Breadth –", "Lateral – 1 (", "Lateral – 2 (", "Lateral – 3 (", "Elective –"]
        ):
            if not current_pool:
                is_slot = True

        if is_slot:
            slot_name = c1.split("(")[0].strip()
            slot_id = f"SLOT_SEM{sem_num}_{slot_name.replace(' – ', '_').replace(' ', '_').upper()}"
            slot_type = "breadth" if "Breadth" in slot_name else ("lateral" if "Lateral" in slot_name else "elective")
            
            # parse credits
            min_c = 3.0
            max_c = 3.0
            if "/" in c4:
                parts = [float(x) for x in re.findall(r"\d+", c4)]
                if parts:
                    min_c = min(parts)
                    max_c = max(parts)
            elif re.findall(r"\d+", c4):
                min_c = float(re.findall(r"\d+", c4)[0])
                max_c = min_c

            pool_name = ""
            if "Lateral – 1" in slot_name:
                pool_name = "Lateral – 1 options"
            elif "Lateral – 2" in slot_name:
                pool_name = "Lateral – 2 options"
            elif "Lateral – 3" in slot_name:
                pool_name = "Lateral – 3 options"
            elif "Elective – 1" in slot_name or "Elective – 2" in slot_name:
                pool_name = "Elective – 1, 2 pool"
            elif "Elective –" in slot_name:
                pool_name = "Elective – 3, 4, 5, 6 pool"

            slots.append({
                "slot_id": slot_id,
                "programme_id": "BTECH_EE",
                "semester_number": sem_num,
                "slot_name": slot_name,
                "slot_type": slot_type,
                "min_credits": min_c,
                "max_credits": max_c,
                "option_pool": pool_name
            })
            continue

        # Option rows inside pools
        if current_pool:
            c = c2.strip()
            c_name = c1.strip()
            c_ltp = c3.strip()
            c_cr = float(c4.strip()) if c4.strip() else 3.0
            
            if c not in courses:
                courses[c] = {
                    "course_code": c,
                    "title": c_name,
                    "department_id": "EE" if c.startswith("EE") else ("EC" if c.startswith("EC") else ("CS" if c.startswith("CS") else "CORE")),
                    "ltp": c_ltp,
                    "credits": c_cr,
                    "course_type": "lateral" if "Lateral" in current_pool else "elective",
                    "type_source": "inferred",
                    "mode": "offline",
                    "level": "UG",
                    "in_semester_table": True,
                    "source_id": "IITBBS_EE_CURRICULUM_2016_17",
                    "is_placeholder": False
                }
            course_offerings.append((c, sem_num, parity, "ALL", "inferred_from_semester_table"))

            # Link to corresponding slots in this semester
            for sl in slots:
                if sl["semester_number"] == sem_num and sl["option_pool"] and (sl["option_pool"] in current_pool or current_pool in sl["option_pool"]):
                    slot_options.append((sl["slot_id"], c))

            # Parse prereq
            if c7 and c7 not in ["—", "None"]:
                for line in c7.split("\n"):
                    for tok in line.split(","):
                        tok = tok.strip()
                        if not tok or tok in ["—", "None"]:
                            continue
                        clean_tok = tok.lower()
                        res_code = alias_dict.get(clean_tok)
                        if res_code:
                            course_prereqs.append((c, res_code, "required"))
                        else:
                            unresolved_prereqs.append((c, tok))
            continue

        # Paired rows in Sem I and II
        if " / " in c2:
            parts_c = [x.strip() for x in c2.split(" / ")]
            parts_n = [x.strip() for x in c1.split(" / ")]
            parts_l = [x.strip() for x in c3.split(" / ")]
            parts_cr = [x.strip() for x in c4.split(" / ")]

            # Track pairing: Track A gets first in Sem I, Track B gets second in Sem I (and swapped in Sem II)
            # In Sem I: code[0] is Track A, code[1] is Track B
            # In Sem II: code[0] is Track B, code[1] is Track A
            sub_items = []
            for i, pc in enumerate(parts_c):
                pn = parts_n[i] if i < len(parts_n) else parts_n[-1]
                pl = parts_l[i] if i < len(parts_l) else parts_l[-1]
                pcr_val = float(parts_cr[i]) if i < len(parts_cr) and parts_cr[i].isdigit() else 4.0
                
                track = "A" if ((sem_num == 1 and i == 0) or (sem_num == 2 and i == 1)) else "B"

                if " or " in pc:
                    sub_c = [sc.strip() for sc in pc.split(" or ")]
                    sub_n = [sn.strip() for sn in pn.split(" or ")]
                    sub_l = [sl.strip() for sl in pl.split(" or ")]
                    for j, sc in enumerate(sub_c):
                        sn = sub_n[j] if j < len(sub_n) else sub_n[-1]
                        sl = sub_l[j] if j < len(sub_l) else sub_l[-1]
                        sub_items.append((sc, sn, sl, pcr_val, track))
                else:
                    sub_items.append((pc, pn, pl, pcr_val, track))

            for sc, sn, sl, scr, strack in sub_items:
                if sc not in courses:
                    courses[sc] = {
                        "course_code": sc,
                        "title": sn,
                        "department_id": "EE" if sc.startswith("EE") else ("EC" if sc.startswith("EC") else ("CS" if sc.startswith("CS") else "COMMON")),
                        "ltp": sl,
                        "credits": scr,
                        "course_type": "core",
                        "type_source": "source",
                        "mode": "offline",
                        "level": "UG",
                        "in_semester_table": True,
                        "source_id": "IITBBS_EE_CURRICULUM_2016_17",
                        "is_placeholder": False
                    }
                course_offerings.append((sc, sem_num, parity, strack, "inferred_from_semester_table"))

            # Parse prereqs for paired row
            if c7 and c7 not in ["—", "None"]:
                for line in c7.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    if ":" in line:
                        prefix, rest = line.split(":", 1)
                        target = prefix.strip()
                        for tok in rest.split(","):
                            tok = tok.strip()
                            if not tok or tok in ["—", "None"]:
                                continue
                            res_code = alias_dict.get(tok.lower())
                            if res_code:
                                course_prereqs.append((target, res_code, "required"))
                            else:
                                unresolved_prereqs.append((target, tok))
            continue

        # Normal single core / institute course row
        c = c2.strip()
        if c:
            c_cr = float(c4.strip()) if c4.strip() and re.findall(r"\d+", c4) else 3.0
            if c not in courses:
                courses[c] = {
                    "course_code": c,
                    "title": c1.strip(),
                    "department_id": "EE" if c.startswith("EE") else ("EC" if c.startswith("EC") else ("CS" if c.startswith("CS") else "INSTITUTE")),
                    "ltp": c3.strip(),
                    "credits": c_cr,
                    "course_type": "core",
                    "type_source": "source",
                    "mode": "offline",
                    "level": "UG",
                    "in_semester_table": True,
                    "source_id": "IITBBS_EE_CURRICULUM_2016_17",
                    "is_placeholder": False
                }
            course_offerings.append((c, sem_num, parity, "ALL", "inferred_from_semester_table"))

            if c7 and c7 not in ["—", "None"]:
                for line in c7.split("\n"):
                    for tok in line.split(","):
                        tok = tok.strip()
                        if not tok or tok in ["—", "None"]:
                            continue
                        clean_tok = tok.lower()
                        res_code = alias_dict.get(clean_tok)
                        if res_code:
                            course_prereqs.append((c, res_code, "required"))
                        else:
                            unresolved_prereqs.append((c, tok))

    # Add syllabus-only courses
    with open("data/raw/ee/curriculum_syllabus_only.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            c = r["Course Code"].strip()
            c_cr = float(r["Credits"].strip()) if r["Credits"].strip() else 3.0
            courses[c] = {
                "course_code": c,
                "title": r["Course Name"].strip(),
                "department_id": "EC",
                "ltp": r["L-T-P"].strip(),
                "credits": c_cr,
                "course_type": "elective",
                "type_source": "source",
                "mode": "offline",
                "level": "UG",
                "in_semester_table": False,
                "source_id": "IITBBS_EE_CURRICULUM_2016_17",
                "is_placeholder": False
            }
            # prereq
            raw_pr = r["Prerequisites"].strip()
            if raw_pr and raw_pr not in ["—", "None"]:
                for tok in raw_pr.split(","):
                    tok = tok.strip()
                    res_code = alias_dict.get(tok.lower())
                    if res_code:
                        course_prereqs.append((c, res_code, "required"))
                    else:
                        unresolved_prereqs.append((c, tok))

    # Remove duplicates from prerequisites
    course_prereqs = list(set(course_prereqs))
    slot_options = list(set(slot_options))

    # -------------------------------------------------------------
    # 3. Write out Course, Prerequisite, Slot, Offerings CSVs
    # -------------------------------------------------------------
    with open("data/seed/kb/course.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["course_code", "title", "department_id", "ltp", "credits", "course_type", "type_source", "mode", "level", "in_semester_table", "source_id", "is_placeholder"])
        for c, d in sorted(courses.items()):
            writer.writerow([
                d["course_code"], d["title"], d["department_id"], d["ltp"], d["credits"],
                d["course_type"], d["type_source"], d["mode"], d["level"],
                d["in_semester_table"], d["source_id"], d["is_placeholder"]
            ])

    with open("data/seed/kb/course_prerequisite.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["course_code", "prereq_code", "relation"])
        for c, p, r in sorted(course_prereqs):
            writer.writerow([c, p, r])

    with open("data/seed/kb/course_offering.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["course_code", "semester_number", "parity", "track", "offering_basis"])
        for item in sorted(set(course_offerings)):
            writer.writerow(item)

    with open("data/seed/kb/programme_requirement.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["slot_id", "programme_id", "semester_number", "slot_name", "slot_type", "min_credits", "max_credits", "option_pool"])
        for s in slots:
            writer.writerow([
                s["slot_id"], s["programme_id"], s["semester_number"],
                s["slot_name"], s["slot_type"], s["min_credits"], s["max_credits"], s["option_pool"]
            ])

    with open("data/seed/kb/slot_option.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["slot_id", "course_code"])
        for so in sorted(slot_options):
            writer.writerow(so)

    # -------------------------------------------------------------
    # 4. Parse Playlists / Learning Resources
    # -------------------------------------------------------------
    resources = []
    resource_courses = []
    with open("data/raw/ee/video_playlists.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, r in enumerate(reader, 1):
            code = r["Code"].strip()
            cov = r["Coverage"].strip()
            notes = r["Notes"].strip()

            # Helper to extract url and title
            def extract_res(val, role_name):
                if not val or not val.strip():
                    return None
                lines = [l.strip() for l in val.split("\n") if l.strip()]
                title = lines[0]
                url = lines[1] if len(lines) > 1 else lines[0]
                if not url.startswith("http"):
                    url = "https://www.youtube.com/user/nptelhrd"
                
                provider = "NPTEL"
                if "MIT" in title or "MIT OCW" in title:
                    provider = "MIT OCW"
                elif "third-party" in title or "non-NPTEL" in title or "third-party" in notes:
                    provider = "third-party"

                res_type = "playlist"
                if "single video" in notes or "single video" in title:
                    res_type = "single_video"
                elif cov == "Not confirmed":
                    res_type = "channel_search"
                elif cov == "No video applicable":
                    res_type = "none"

                clean_code = code if code != "(no code)" else r["Course"].strip().replace(" ", "_").replace("–", "-")
                res_id = f"RES_{clean_code}_{role_name}".replace(" ", "_").replace("/", "_")
                return {
                    "resource_id": res_id,
                    "title": title,
                    "url": url,
                    "provider": provider,
                    "resource_type": res_type,
                    "coverage_status": cov,
                    "link_verified": False,
                    "source_id": "IITBBS_EE_PLAYLISTS_2026"
                }

            def add_resource_course_links(res_id, raw_code, role_name):
                # Handle paired codes (e.g. HS1L001 / HS1L002) and skip (no code)
                candidate_codes = [c.strip() for c in raw_code.split(" / ")]
                for cc in candidate_codes:
                    if cc in courses:
                        resource_courses.append((res_id, cc, role_name))

            p_res = extract_res(r["Primary: NPTEL"], "PRIMARY")
            if p_res:
                resources.append(p_res)
                add_resource_course_links(p_res["resource_id"], code, "primary")

            b1_res = extract_res(r["Backup 1"], "BACKUP1")
            if b1_res:
                resources.append(b1_res)
                add_resource_course_links(b1_res["resource_id"], code, "backup1")

            b2_res = extract_res(r["Backup 2"], "BACKUP2")
            if b2_res:
                resources.append(b2_res)
                add_resource_course_links(b2_res["resource_id"], code, "backup2")

    with open("data/seed/kb/resource.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["resource_id", "title", "url", "provider", "resource_type", "coverage_status", "link_verified", "source_id"])
        for res in resources:
            writer.writerow([
                res["resource_id"], res["title"], res["url"], res["provider"],
                res["resource_type"], res["coverage_status"], res["link_verified"], res["source_id"]
            ])

    with open("data/seed/kb/resource_course.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["resource_id", "course_code", "role"])
        for rc in resource_courses:
            writer.writerow(rc)

    # -------------------------------------------------------------
    # 5. Parse Research Projects & Faculty
    # -------------------------------------------------------------
    # Research areas
    areas = [
        ("AREA_PWR", "Power Systems & Energy"),
        ("AREA_PED", "Power Electronics & Drives"),
        ("AREA_CSP", "Communications & Signal Processing"),
        ("AREA_RMA", "RF, Microwave & Antennas"),
        ("AREA_VLS", "VLSI, Devices & Sensors"),
        ("AREA_CTL", "Control Systems")
    ]
    with open("data/seed/kb/research_area.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["area_id", "name"])
        for a in areas:
            writer.writerow(a)

    area_name_to_id = {name: aid for aid, name in areas}

    # Faculty & Groups normalization
    faculty = {} # name -> dict (faculty_id, display_name, title, group_name, is_person)
    projects = []
    project_faculty = []
    project_keywords = []

    with open("data/raw/ee/research_projects_v2.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        v2_rows = list(reader)

    with open("data/raw/ee/research_projects_all.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    v2_by_title = {r["Project Name"].strip(): r for r in v2_rows}

    # Helper for adding faculty
    def get_faculty_id(name, is_p):
        clean_name = name.strip()
        fid = f"FAC_{re.sub(r'[^a-zA-Z0-9]', '_', clean_name).upper()}"
        fid = re.sub(r'_+', '_', fid).strip('_')
        if fid not in faculty:
            title = "Prof." if "Prof." in clean_name else ("Dr." if "Dr." in clean_name else "")
            disp = clean_name
            group_name = "" if is_p else clean_name
            faculty[fid] = {
                "faculty_id": fid,
                "display_name": disp,
                "title": title,
                "group_name": group_name,
                "is_person": is_p
            }
        return fid

    for idx, r in enumerate(all_rows, 1):
        p_title = r["Project Name"].strip()
        p_area = r["Research Area"].strip()
        p_fund = r["Funding Agency"].strip()
        area_id = area_name_to_id.get(p_area, "AREA_OTHER")

        proj_id = f"PROJ_EE_{idx:03d}"
        if p_title in v2_by_title:
            v2 = v2_by_title[p_title]
            scope = v2["Complete Project Details (Grant, Duration & Technical Scope)"].strip()
            kw_str = v2["Keywords"].strip()
            src = "compiled_secondary"

            # Parse grant prefix
            grant_lakhs = None
            start_yr = None
            end_yr = None
            m_grant = re.search(r"Grant:\s*₹?([\d.]+)\s*Lakhs", scope, re.IGNORECASE)
            if m_grant:
                grant_lakhs = float(m_grant.group(1))
            m_yr = re.search(r"\((\d{4})[–-](\d{4})\)", scope)
            if m_yr:
                start_yr = int(m_yr.group(1))
                end_yr = int(m_yr.group(2))

            projects.append({
                "project_id": proj_id,
                "area_id": area_id,
                "title": p_title,
                "funding_agency": p_fund,
                "grant_lakhs": grant_lakhs,
                "start_year": start_yr,
                "end_year": end_yr,
                "scope_text": scope,
                "source_id": "IITBBS_RESEARCH_V2",
                "detail_level": "full",
                "verified": False,
                "source_confidence": src
            })

            # Keywords
            for kw in kw_str.split(";"):
                kw = kw.strip()
                if kw:
                    project_keywords.append((proj_id, kw))

            # Faculty
            prof_raw = v2["Prof. Name (PI / Co-PI)"].strip()
            if "Interdisciplinary Team" in prof_raw:
                fid = get_faculty_id(prof_raw, False)
                project_faculty.append((proj_id, fid, "team"))
            else:
                clean = prof_raw
                if "with Prof. S. Dasgupta" in clean:
                    clean = clean.replace("(Co-PI, with Prof. S. Dasgupta)", "")
                    fid = get_faculty_id("Prof. S. Dasgupta", True)
                    project_faculty.append((proj_id, fid, "Co-PI"))

                clean = clean.replace("SECS Control/Power Team", "SECS_CONTROL_POWER_TEAM")
                clean = clean.replace("SECS IoT/VLSI Team", "SECS_IOT_VLSI_TEAM")
                parts = re.split(r"&|,|/", clean)
                for p in parts:
                    p = p.strip()
                    if not p:
                        continue
                    p = p.replace("SECS_CONTROL_POWER_TEAM", "SECS Control/Power Team")
                    p = p.replace("SECS_IOT_VLSI_TEAM", "SECS IoT/VLSI Team")
                    role = "PI" if "(PI)" in p or len(parts) == 1 else ("Co-PI" if "(Co-PI)" in p else "unspecified")
                    p = re.sub(r"\(PI\)", "", p)
                    p = re.sub(r"\(Co-PI\)", "", p)
                    p = re.sub(r"\(IITBBS Lead\)", "", p)
                    p = p.strip()
                    if not p:
                        continue
                    is_grp = any(x in p for x in ["Team", "Group", "Consortium"])
                    fid = get_faculty_id(p, not is_grp)
                    project_faculty.append((proj_id, fid, role))

        else:
            projects.append({
                "project_id": proj_id,
                "area_id": area_id,
                "title": p_title,
                "funding_agency": p_fund,
                "grant_lakhs": None,
                "start_year": None,
                "end_year": None,
                "scope_text": "",
                "source_id": "IITBBS_RESEARCH_ALL",
                "detail_level": "title_only",
                "verified": False,
                "source_confidence": "compiled_secondary"
            })

    with open("data/seed/kb/faculty.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["faculty_id", "display_name", "title", "group_name", "is_person"])
        for fid, fd in sorted(faculty.items()):
            writer.writerow([fd["faculty_id"], fd["display_name"], fd["title"], fd["group_name"], fd["is_person"]])

    with open("data/seed/kb/research_project.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["project_id", "area_id", "title", "funding_agency", "grant_lakhs", "start_year", "end_year", "scope_text", "source_id", "detail_level", "verified", "source_confidence"])
        for p in projects:
            writer.writerow([
                p["project_id"], p["area_id"], p["title"], p["funding_agency"],
                p["grant_lakhs"], p["start_year"], p["end_year"], p["scope_text"],
                p["source_id"], p["detail_level"], p["verified"], p["source_confidence"]
            ])

    with open("data/seed/kb/project_faculty.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["project_id", "faculty_id", "role"])
        for pf in project_faculty:
            writer.writerow(pf)

    with open("data/seed/kb/project_keyword.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["project_id", "keyword"])
        for pk in project_keywords:
            writer.writerow(pk)

    # -------------------------------------------------------------
    # 6. Parse and Save Data Issues
    # -------------------------------------------------------------
    data_issues = []
    with open("data/raw/ee/curriculum_notes_discrepancies.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            data_issues.append({
                "issue_id": f"ISSUE_CURR_{int(r['#']):02d}",
                "entity_type": "curriculum",
                "entity_key": r["Course / Item"].strip(),
                "severity": "medium",
                "description": r["Issue found in the source PDF"].strip(),
                "resolution_notes": r["How it is shown in this workbook"].strip(),
                "status": "acknowledged"
            })

    # Add the unresolved prerequisite issue
    for target_c, raw_name in unresolved_prereqs:
        data_issues.append({
            "issue_id": f"ISSUE_PREREQ_{target_c}",
            "entity_type": "course_prerequisite",
            "entity_key": target_c,
            "severity": "high",
            "description": f"Prerequisite '{raw_name}' matches no course name in curriculum semester table.",
            "resolution_notes": "Needs department clarification. Likely EE3L010 (Measurement and Instrumentation) or EE2L002.",
            "status": "unresolved"
        })

    # Add candidate merge variants
    data_issues.append({
        "issue_id": "ISSUE_FAC_MERGE_BHENDE_PERUMALLA",
        "entity_type": "faculty",
        "entity_key": "Dr. Chandrashekhar Narayan Bhende / Prof. C. N. Bhende / Dr. Chandrashekhar Perumalla",
        "severity": "medium",
        "description": "Potential spelling / identity variants in project PI entries: 'Dr. Chandrashekhar Narayan Bhende', 'Prof. C. N. Bhende', and 'Dr. Chandrashekhar Perumalla'.",
        "resolution_notes": "Maintained as distinct faculty entities per rule until confirmed by user.",
        "status": "unresolved"
    })

    with open("data/seed/kb/data_issue.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["issue_id", "entity_type", "entity_key", "severity", "description", "resolution_notes", "status"])
        for di in data_issues:
            writer.writerow([
                di["issue_id"], di["entity_type"], di["entity_key"], di["severity"],
                di["description"], di["resolution_notes"], di["status"]
            ])

    print("Ingestion complete. Seed files generated in data/seed/kb/.")

if __name__ == "__main__":
    run_ingestion()

