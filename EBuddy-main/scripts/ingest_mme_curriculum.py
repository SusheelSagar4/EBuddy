"""
Ingest Metallurgical and Materials Engineering (MME) curriculum, playlists, 
research projects, and faculty profiles into data/seed/kb/.
Reproducible, non-destructive, merges cleanly with EE data.
"""

import os
import csv
import re

DATA_RAW_MME = os.path.join("data", "raw", "mme")
DATA_SEED_KB = os.path.join("data", "seed", "kb")

def clean_money_lakhs(val):
    if not val or val.strip() in ["—", "-", ""]:
        return None
    # match patterns like "₹ 54 Lakhs", "₹ 85.9 Lakhs", "₹ 2[0] Lakhs", "₹ 0.45 Lakhs"
    val = val.replace("[", "").replace("]", "")
    m = re.search(r"(\d+(?:\.\d+)?)", val)
    if m:
        return float(m.group(1))
    return None

def clean_duration_years(val):
    if not val or val.strip() in ["—", "-", ""]:
        return None, None
    val = val.replace("[", "").replace("]", "").replace("–", "-").strip()
    m = re.search(r"(\d{4})\s*-\s*(\d{2,4})", val)
    if m:
        start_yr = int(m.group(1))
        end_part = m.group(2)
        if len(end_part) == 2:
            end_yr = int(str(start_yr)[:2] + end_part)
        else:
            end_yr = int(end_part)
        return start_yr, end_yr
    m_single = re.search(r"(\d{4})", val)
    if m_single:
        yr = int(m_single.group(1))
        return yr, yr
    return None, None

def run():
    print(">>> Ingesting MME (Metallurgical and Materials Engineering) data...")

    # 1. Update kb.source
    source_file = os.path.join(DATA_SEED_KB, "source.csv")
    with open(source_file, encoding="utf-8") as f:
        sources = list(csv.DictReader(f))
    existing_src_ids = {s["source_id"] for s in sources}
    
    new_sources = [
        {
            "source_id": "IITBBS_MME_CURRICULUM_2016_17",
            "title": "IIT Bhubaneswar B.Tech Metallurgical and Materials Engineering Curriculum (Sem III-VIII)",
            "url": "https://www.iitbbs.ac.in/mme-curriculum/",
            "publisher": "IIT Bhubaneswar SMMME",
            "licence": "Public Academic Curriculum",
            "retrieved_on": "2026-11-14",
            "doc_type": "curriculum_pdf",
            "reliability": "official",
            "academic_year": "2016-17",
            "notes": "Official semester table and elective/lateral lists for B.Tech MME Sem III-VIII"
        },
        {
            "source_id": "IITBBS_MME_PLAYLISTS_2026",
            "title": "IIT Bhubaneswar MME Course Video Playlists (NPTEL & Open Courseware)",
            "url": "https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",
            "publisher": "NPTEL / SMMME",
            "licence": "CC-BY / Public",
            "retrieved_on": "2026-11-14",
            "doc_type": "oer",
            "reliability": "compiled_secondary",
            "academic_year": "2026",
            "notes": "Curated video playlist directory for MME courses"
        },
        {
            "source_id": "IITBBS_SMMME_PROJECTS_2026",
            "title": "Projects Portfolio — School of Minerals, Metallurgical and Materials Engineering (SMMME)",
            "url": "https://www.iitbbs.ac.in/smmme-projects/",
            "publisher": "SMMME IIT Bhubaneswar",
            "licence": "Public Institutional Record",
            "retrieved_on": "2026-11-14",
            "doc_type": "course_page",
            "reliability": "official",
            "academic_year": "2026",
            "notes": "Consolidated record of Sponsored, Consultancy, and Seed Grant Projects"
        },
        {
            "source_id": "IITBBS_SMMME_FACULTY_2026",
            "title": "SMMME IIT Bhubaneswar — Faculty Research Profiles & Citations Catalog",
            "url": "https://www.iitbbs.ac.in/smmme-faculty/",
            "publisher": "SMMME IIT Bhubaneswar",
            "licence": "Public Institutional Profile",
            "retrieved_on": "2026-11-14",
            "doc_type": "course_page",
            "reliability": "compiled_secondary",
            "academic_year": "2026",
            "notes": "Profiles of the 16 current SMMME faculty members and citations"
        }
    ]
    for ns in new_sources:
        if ns["source_id"] not in existing_src_ids:
            sources.append(ns)
            existing_src_ids.add(ns["source_id"])
    
    with open(source_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(sources[0].keys()))
        writer.writeheader()
        writer.writerows(sources)

    # 2. Ingest Faculty (faculty.csv)
    faculty_file = os.path.join(DATA_SEED_KB, "faculty.csv")
    with open(faculty_file, encoding="utf-8") as f:
        faculty_rows = list(csv.DictReader(f))
    existing_fac_ids = {r["faculty_id"] for r in faculty_rows}

    raw_faculty_file = os.path.join(DATA_RAW_MME, "faculty_profiles.csv")
    mme_fac_map = {} # normalized_name -> faculty_id
    with open(raw_faculty_file, encoding="utf-8") as f:
        raw_fac = list(csv.DictReader(f))
        for rf in raw_fac:
            fac_id = rf["faculty_id"]
            mme_fac_map[rf["normalized_name"].lower()] = fac_id
            mme_fac_map[rf["full_name"].lower()] = fac_id
            if fac_id not in existing_fac_ids:
                faculty_rows.append({
                    "faculty_id": fac_id,
                    "display_name": rf["full_name"],
                    "title": rf["designation"],
                    "group_name": "SMMME",
                    "is_person": "true"
                })
                existing_fac_ids.add(fac_id)

    with open(faculty_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(faculty_rows[0].keys()))
        writer.writeheader()
        writer.writerows(faculty_rows)

    # 3. Ingest Research Areas (research_area.csv)
    area_file = os.path.join(DATA_SEED_KB, "research_area.csv")
    with open(area_file, encoding="utf-8") as f:
        areas = list(csv.DictReader(f))
    existing_areas = {a["area_id"] for a in areas}
    
    new_areas = [
        {"area_id": "AREA_MM_PROC", "name": "Process Metallurgy & Iron/Steelmaking"},
        {"area_id": "AREA_MM_PHYS", "name": "Physical Metallurgy, Thin Films & High Entropy Alloys"},
        {"area_id": "AREA_MM_MECH", "name": "Mechanical Metallurgy & Additive Manufacturing"},
        {"area_id": "AREA_MM_BIO", "name": "Biomaterials & Tissue Scaffold Engineering"},
        {"area_id": "AREA_MM_ENG", "name": "Energy Materials, Batteries & Thermoelectrics"},
        {"area_id": "AREA_MM_MIN", "name": "Mineral Processing, Recycling & Corrosion"}
    ]
    for na in new_areas:
        if na["area_id"] not in existing_areas:
            areas.append(na)
            existing_areas.add(na["area_id"])

    with open(area_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(areas[0].keys()))
        writer.writeheader()
        writer.writerows(areas)

    # 4. Ingest Research Projects (research_project.csv, project_faculty.csv, project_keyword.csv)
    proj_file = os.path.join(DATA_SEED_KB, "research_project.csv")
    with open(proj_file, encoding="utf-8") as f:
        projects = list(csv.DictReader(f))
    existing_proj_ids = {p["project_id"] for p in projects}

    proj_fac_file = os.path.join(DATA_SEED_KB, "project_faculty.csv")
    with open(proj_fac_file, encoding="utf-8") as f:
        proj_fac_links = list(csv.DictReader(f))

    proj_kw_file = os.path.join(DATA_SEED_KB, "project_keyword.csv")
    with open(proj_kw_file, encoding="utf-8") as f:
        proj_kw_links = list(csv.DictReader(f))

    def map_to_area(title, pi_name):
        t_low = title.lower()
        if any(k in t_low for k in ["iron", "steel", "dri", "blast furnace", "bof", "midrex", "smelting", "forging", "slag", "thickener"]):
            return "AREA_MM_PROC"
        if any(k in t_low for k in ["bio", "implant", "bone", "scaffold", "fibrin", "bioactive"]):
            return "AREA_MM_BIO"
        if any(k in t_low for k in ["battery", "thermoelectric", "energy", "photovoltaic", "hydrogen", "perovskite", "solar", "fuel", "lithium"]):
            return "AREA_MM_ENG"
        if any(k in t_low for k in ["additive", "semisolid", "fdm", "creep", "deformation", "formability", "fatigue", "metamaterials"]):
            return "AREA_MM_MECH"
        if any(k in t_low for k in ["corrosion", "mineral", "tailing", "recycling", "zircon", "leaching", "silicon"]):
            return "AREA_MM_MIN"
        return "AREA_MM_PHYS"

    def find_faculty_id(pi_string):
        pi_clean = pi_string.replace("Dr.", "").replace("Prof.", "").replace("[", "").replace("]", "").strip().lower()
        # Direct check
        if pi_clean in mme_fac_map:
            return mme_fac_map[pi_clean]
        # Partial match
        for k, v in mme_fac_map.items():
            if pi_clean in k or k in pi_clean:
                return v
        return "FAC_MM_01" # fallback

    # A. Sponsored projects
    with open(os.path.join(DATA_RAW_MME, "research_projects_sponsored.csv"), encoding="utf-8") as f:
        spon_reader = csv.DictReader(f)
        for r in spon_reader:
            pid = f"PROJ_MM_SPON_{int(r['entry_no']):02d}"
            if pid not in existing_proj_ids:
                title = r["project_title"]
                pi = r["pi"]
                grant_lakhs = clean_money_lakhs(r["amount"])
                sy, ey = clean_duration_years(r["duration"])
                area = map_to_area(title, pi)
                projects.append({
                    "project_id": pid,
                    "area_id": area,
                    "title": title,
                    "funding_agency": r["funding_agency"] if r["funding_agency"] not in ["—", ""] else "SMMME / Industry",
                    "grant_lakhs": grant_lakhs if grant_lakhs is not None else "",
                    "start_year": sy if sy is not None else "",
                    "end_year": ey if ey is not None else "",
                    "scope_text": f"Sponsored project by {pi}. Funding: {r['funding_agency']}.",
                    "source_id": "IITBBS_SMMME_PROJECTS_2026",
                    "detail_level": "full",
                    "verified": "false",
                    "source_confidence": "official_primary"
                })
                existing_proj_ids.add(pid)
                fac_id = find_faculty_id(pi)
                proj_fac_links.append({"project_id": pid, "faculty_id": fac_id, "role": "PI"})
                proj_kw_links.append({"project_id": pid, "keyword": area})
                proj_kw_links.append({"project_id": pid, "keyword": "sponsored_research"})

    # B. Consultancy projects
    with open(os.path.join(DATA_RAW_MME, "research_projects_consultancy.csv"), encoding="utf-8") as f:
        cons_reader = csv.DictReader(f)
        for r in cons_reader:
            pid = f"PROJ_MM_CONS_{int(r['entry_no']):02d}"
            if pid not in existing_proj_ids:
                consultant = r["consultant"]
                client = r["client"]
                amount_str = r["amount"]
                year_str = r["year"]
                grant_lakhs = clean_money_lakhs(amount_str)
                sy, ey = clean_duration_years(year_str)
                title = f"Industrial Consultancy: {client} ({consultant}, {year_str})"
                area = map_to_area(title + " " + client, consultant)
                projects.append({
                    "project_id": pid,
                    "area_id": area,
                    "title": title,
                    "funding_agency": client if client not in ["—", ""] else "Industry Client",
                    "grant_lakhs": grant_lakhs if grant_lakhs is not None else "",
                    "start_year": sy if sy is not None else "",
                    "end_year": ey if ey is not None else "",
                    "scope_text": f"Consultancy service by {consultant} for {client}.",
                    "source_id": "IITBBS_SMMME_PROJECTS_2026",
                    "detail_level": "full",
                    "verified": "false",
                    "source_confidence": "official_primary"
                })
                existing_proj_ids.add(pid)
                fac_id = find_faculty_id(consultant)
                proj_fac_links.append({"project_id": pid, "faculty_id": fac_id, "role": "Consultant"})
                proj_kw_links.append({"project_id": pid, "keyword": area})
                proj_kw_links.append({"project_id": pid, "keyword": "consultancy"})

    # C. Seed grant projects
    with open(os.path.join(DATA_RAW_MME, "research_projects_seed.csv"), encoding="utf-8") as f:
        seed_reader = csv.DictReader(f)
        for r in seed_reader:
            pid = f"PROJ_MM_SEED_{int(r['entry_no']):02d}"
            if pid not in existing_proj_ids:
                title = r["project_title"]
                pi = r["pi"]
                grant_lakhs = clean_money_lakhs(r["amount"])
                sy, ey = clean_duration_years(r["duration"])
                area = map_to_area(title, pi)
                projects.append({
                    "project_id": pid,
                    "area_id": area,
                    "title": title,
                    "funding_agency": "IIT Bhubaneswar (Seed Grant)",
                    "grant_lakhs": grant_lakhs if grant_lakhs is not None else "",
                    "start_year": sy if sy is not None else "",
                    "end_year": ey if ey is not None else "",
                    "scope_text": f"Internal seed grant project by {pi}.",
                    "source_id": "IITBBS_SMMME_PROJECTS_2026",
                    "detail_level": "full",
                    "verified": "false",
                    "source_confidence": "official_primary"
                })
                existing_proj_ids.add(pid)
                fac_id = find_faculty_id(pi)
                proj_fac_links.append({"project_id": pid, "faculty_id": fac_id, "role": "PI"})
                proj_kw_links.append({"project_id": pid, "keyword": area})
                proj_kw_links.append({"project_id": pid, "keyword": "seed_grant"})

    with open(proj_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(projects[0].keys()))
        writer.writeheader()
        writer.writerows(projects)

    with open(proj_fac_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(proj_fac_links[0].keys()))
        writer.writeheader()
        writer.writerows(proj_fac_links)

    with open(proj_kw_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(proj_kw_links[0].keys()))
        writer.writeheader()
        writer.writerows(proj_kw_links)

    # 5. Ingest Courses, Aliases, Offerings, Programme Requirements, Slot Options
    course_file = os.path.join(DATA_SEED_KB, "course.csv")
    with open(course_file, encoding="utf-8") as f:
        course_rows = list(csv.DictReader(f))
    course_dict = {c["course_code"]: c for c in course_rows}

    alias_file = os.path.join(DATA_SEED_KB, "course_alias.csv")
    with open(alias_file, encoding="utf-8") as f:
        aliases = list(csv.DictReader(f))
    existing_aliases = {a["alias_name"]: a["target_course_code"] for a in aliases}

    offering_file = os.path.join(DATA_SEED_KB, "course_offering.csv")
    with open(offering_file, encoding="utf-8") as f:
        offerings = list(csv.DictReader(f))
    existing_offerings = {(o["course_code"], int(o["semester_number"]), o["track"]) for o in offerings}

    req_file = os.path.join(DATA_SEED_KB, "programme_requirement.csv")
    with open(req_file, encoding="utf-8") as f:
        req_rows = list(csv.DictReader(f))
    existing_slots = {s["slot_id"] for s in req_rows}

    slot_opt_file = os.path.join(DATA_SEED_KB, "slot_option.csv")
    with open(slot_opt_file, encoding="utf-8") as f:
        slot_opts = list(csv.DictReader(f))
    existing_slot_opts = {(so["slot_id"], so["course_code"]) for so in slot_opts}

    # Add MME Slots
    mme_slots = [
        {"slot_id": "MM_BREADTH_1", "programme_id": "BTECH_MM", "semester_number": "3", "slot_name": "Breadth – I", "slot_type": "Breadth", "min_credits": "3.0", "max_credits": "4.0", "option_pool": "institute_breadth_pool"},
        {"slot_id": "MM_BREADTH_2", "programme_id": "BTECH_MM", "semester_number": "4", "slot_name": "Breadth – II", "slot_type": "Breadth", "min_credits": "3.0", "max_credits": "4.0", "option_pool": "institute_breadth_pool"},
        {"slot_id": "MM_LATERAL_1", "programme_id": "BTECH_MM", "semester_number": "4", "slot_name": "Lateral – 1", "slot_type": "Lateral", "min_credits": "3.0", "max_credits": "4.0", "option_pool": "mme_lateral_pool"},
        {"slot_id": "MM_BREADTH_3", "programme_id": "BTECH_MM", "semester_number": "5", "slot_name": "Breadth – III", "slot_type": "Breadth", "min_credits": "3.0", "max_credits": "4.0", "option_pool": "institute_breadth_pool"},
        {"slot_id": "MM_LATERAL_2", "programme_id": "BTECH_MM", "semester_number": "5", "slot_name": "Lateral – II", "slot_type": "Lateral", "min_credits": "3.0", "max_credits": "4.0", "option_pool": "mme_lateral_pool"},
        {"slot_id": "MM_BREADTH_4", "programme_id": "BTECH_MM", "semester_number": "6", "slot_name": "Breadth – IV", "slot_type": "Breadth", "min_credits": "3.0", "max_credits": "4.0", "option_pool": "institute_breadth_pool"},
        {"slot_id": "MM_LATERAL_3", "programme_id": "BTECH_MM", "semester_number": "6", "slot_name": "Lateral – III", "slot_type": "Lateral", "min_credits": "3.0", "max_credits": "4.0", "option_pool": "mme_lateral_pool"},
        {"slot_id": "MM_ELECTIVE_1", "programme_id": "BTECH_MM", "semester_number": "7", "slot_name": "Elective – I", "slot_type": "Elective", "min_credits": "3.0", "max_credits": "3.0", "option_pool": "mme_elective_pool"},
        {"slot_id": "MM_ELECTIVE_2", "programme_id": "BTECH_MM", "semester_number": "8", "slot_name": "Elective – II", "slot_type": "Elective", "min_credits": "3.0", "max_credits": "3.0", "option_pool": "mme_elective_pool"},
        {"slot_id": "MM_ELECTIVE_3", "programme_id": "BTECH_MM", "semester_number": "8", "slot_name": "Elective – III", "slot_type": "Elective", "min_credits": "3.0", "max_credits": "3.0", "option_pool": "mme_elective_pool"},
        {"slot_id": "MM_ELECTIVE_4", "programme_id": "BTECH_MM", "semester_number": "8", "slot_name": "Elective – IV", "slot_type": "Elective", "min_credits": "3.0", "max_credits": "3.0", "option_pool": "mme_elective_pool"},
        {"slot_id": "MM_ELECTIVE_5", "programme_id": "BTECH_MM", "semester_number": "8", "slot_name": "Elective – V", "slot_type": "Elective", "min_credits": "3.0", "max_credits": "3.0", "option_pool": "mme_elective_pool"}
    ]
    for ms in mme_slots:
        if ms["slot_id"] not in existing_slots:
            req_rows.append(ms)
            existing_slots.add(ms["slot_id"])

    # Parse curriculum courses
    with open(os.path.join(DATA_RAW_MME, "curriculum_semester_table.csv"), encoding="utf-8") as f:
        curr_reader = csv.DictReader(f)
        for r in curr_reader:
            code = r["Course Code"].strip()
            name = r["Course Name"].strip()
            sem_str = r["Semester"].strip()
            ltp = r["L-T-P"].strip()
            credits_str = r["Credits"].strip()
            ctype = r["Course Type"].strip()

            if not code or code.startswith("SEMESTER") or code.startswith("▸") or code == "(not given)":
                continue
            if code in ["(no code in source)", "ML4LXXX"]:
                # slot handled separately
                continue

            # Code clash disambiguation for electives
            is_elective_clash = False
            effective_code = code
            if "Elective" in ctype and code in ["ML4L001", "ML4L002", "ML4L003"]:
                effective_code = f"{code}E"
                is_elective_clash = True

            # Credits
            cr_val = 3.0
            if credits_str.isdigit():
                cr_val = float(credits_str)
            elif " / " in credits_str:
                cr_val = 3.5

            dept_id = "MM"
            if effective_code.startswith("EC"):
                dept_id = "EC"
            elif effective_code.startswith("MA"):
                dept_id = "BS"
            elif effective_code.startswith("ID"):
                dept_id = "COMMON"

            course_level = "UG"
            mapped_type = "core" if "Core" in ctype else ("elective" if "Elective" in ctype else ("lateral" if "Lateral" in ctype else "core"))

            if effective_code not in course_dict:
                course_dict[effective_code] = {
                    "course_code": effective_code,
                    "title": name,
                    "department_id": dept_id,
                    "ltp": ltp if ltp not in ["—", ""] else "3-0-0",
                    "credits": cr_val,
                    "course_type": mapped_type,
                    "type_source": "source",
                    "mode": "offline",
                    "level": course_level,
                    "in_semester_table": "true",
                    "source_id": "IITBBS_MME_CURRICULUM_2016_17",
                    "is_placeholder": "false"
                }
            else:
                # Update existing (e.g. EC2L005) to be in semester table
                course_dict[effective_code]["in_semester_table"] = "true"

            # Aliases
            clean_name_key = name.lower().strip()
            if clean_name_key not in existing_aliases:
                aliases.append({"alias_name": clean_name_key, "target_course_code": effective_code})
                existing_aliases[clean_name_key] = effective_code
            if is_elective_clash:
                alias_clash_key = f"{code} (elective)".lower()
                if alias_clash_key not in existing_aliases:
                    aliases.append({"alias_name": alias_clash_key, "target_course_code": effective_code})
                    existing_aliases[alias_clash_key] = effective_code

            # Semester offering
            sem_nums = []
            if "Sem III" in sem_str and "IV" not in sem_str:
                sem_nums = [3]
            elif "Sem IV" in sem_str and "VI" not in sem_str:
                sem_nums = [4]
            elif "Sem V" in sem_str:
                sem_nums = [5]
            elif "Sem VI" in sem_str:
                sem_nums = [6]
            elif "Sem VII" in sem_str and "VIII" not in sem_str:
                sem_nums = [7]
            elif "Sem VIII" in sem_str:
                sem_nums = [8]

            for snum in sem_nums:
                parity = "odd" if snum % 2 == 1 else "even"
                off_key = (effective_code, snum, "A")
                if off_key not in existing_offerings:
                    offerings.append({
                        "course_code": effective_code,
                        "semester_number": str(snum),
                        "parity": parity,
                        "track": "A",
                        "offering_basis": "inferred_from_semester_table"
                    })
                    existing_offerings.add(off_key)

            # Slot options
            if "Lateral" in ctype:
                for lslot in ["MM_LATERAL_1", "MM_LATERAL_2", "MM_LATERAL_3"]:
                    if (lslot, effective_code) not in existing_slot_opts:
                        slot_opts.append({"slot_id": lslot, "course_code": effective_code})
                        existing_slot_opts.add((lslot, effective_code))

            if "Elective" in ctype:
                for eslot in ["MM_ELECTIVE_1", "MM_ELECTIVE_2", "MM_ELECTIVE_3", "MM_ELECTIVE_4", "MM_ELECTIVE_5"]:
                    if (eslot, effective_code) not in existing_slot_opts:
                        slot_opts.append({"slot_id": eslot, "course_code": effective_code})
                        existing_slot_opts.add((eslot, effective_code))

    # Write back courses, aliases, offerings, reqs, slot_opts
    with open(course_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(course_rows[0].keys()))
        writer.writeheader()
        writer.writerows(course_dict.values())

    with open(alias_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(aliases[0].keys()))
        writer.writeheader()
        writer.writerows(aliases)

    with open(offering_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(offerings[0].keys()))
        writer.writeheader()
        writer.writerows(offerings)

    with open(req_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(req_rows[0].keys()))
        writer.writeheader()
        writer.writerows(req_rows)

    with open(slot_opt_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(slot_opts[0].keys()))
        writer.writeheader()
        writer.writerows(slot_opts)

    # 6. Ingest Resources & Resource-Course Links
    res_file = os.path.join(DATA_SEED_KB, "resource.csv")
    with open(res_file, encoding="utf-8") as f:
        resource_rows = list(csv.DictReader(f))
    existing_res_ids = {r["resource_id"] for r in resource_rows}

    rc_file = os.path.join(DATA_SEED_KB, "resource_course.csv")
    with open(rc_file, encoding="utf-8") as f:
        rc_links = list(csv.DictReader(f))
    existing_rc_links = {(r["resource_id"], r["course_code"], r["role"]) for r in rc_links}

    with open(os.path.join(DATA_RAW_MME, "video_playlists.csv"), encoding="utf-8") as f:
        pl_reader = csv.DictReader(f)
        for i, r in enumerate(pl_reader, 1):
            raw_code = r["Code"].strip()
            course_name = r["Course"].strip()
            cov = r["Coverage"].strip()
            notes = r["Notes"].strip()

            def extract_mme_res(val, role_name):
                if not val or not val.strip():
                    return None
                lines = [l.strip() for l in val.split("\n") if l.strip()]
                title = lines[0]
                url = lines[1] if len(lines) > 1 else lines[0]
                if not url.startswith("http"):
                    url = "https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw"
                
                provider = "NPTEL"
                if "MIT" in title or "MIT OCW" in title:
                    provider = "MIT OCW"
                elif "third-party" in title or "non-NPTEL" in title:
                    provider = "third-party"

                res_type = "playlist"
                if "single video" in notes or "single video" in title or "Lec " in title:
                    res_type = "single_video"
                elif cov == "Not confirmed":
                    res_type = "channel_search"
                elif cov == "No video applicable":
                    res_type = "none"

                clean_token = raw_code if raw_code not in ["(no code)", "(see Laterals)", "ML4LXXX"] else course_name
                clean_token = clean_token.replace(" ", "_").replace("–", "-").replace("/", "_").replace("(", "").replace(")", "")
                res_id = f"RES_MM_{clean_token}_{role_name}"

                return {
                    "resource_id": res_id,
                    "title": title,
                    "url": url,
                    "provider": provider,
                    "resource_type": res_type,
                    "coverage_status": cov,
                    "link_verified": "false",
                    "source_id": "IITBBS_MME_PLAYLISTS_2026"
                }

            def link_mme_res_course(res_id, role_name):
                # find matching course
                target_code = raw_code
                if target_code in ["ML4L001", "ML4L002", "ML4L003"] and "Elective" in r["Semester / Group"]:
                    target_code = f"{target_code}E"
                if target_code in course_dict:
                    if (res_id, target_code, role_name) not in existing_rc_links:
                        rc_links.append({"resource_id": res_id, "course_code": target_code, "role": role_name})
                        existing_rc_links.add((res_id, target_code, role_name))

            p_res = extract_mme_res(r["Primary: NPTEL"], "PRIMARY")
            if p_res and p_res["resource_id"] not in existing_res_ids:
                resource_rows.append(p_res)
                existing_res_ids.add(p_res["resource_id"])
                link_mme_res_course(p_res["resource_id"], "primary")

            b1_res = extract_mme_res(r["Backup 1"], "BACKUP1")
            if b1_res and b1_res["resource_id"] not in existing_res_ids:
                resource_rows.append(b1_res)
                existing_res_ids.add(b1_res["resource_id"])
                link_mme_res_course(b1_res["resource_id"], "backup1")

            b2_res = extract_mme_res(r["Backup 2"], "BACKUP2")
            if b2_res and b2_res["resource_id"] not in existing_res_ids:
                resource_rows.append(b2_res)
                existing_res_ids.add(b2_res["resource_id"])
                link_mme_res_course(b2_res["resource_id"], "backup2")

    with open(res_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(resource_rows[0].keys()))
        writer.writeheader()
        writer.writerows(resource_rows)

    with open(rc_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rc_links[0].keys()))
        writer.writeheader()
        writer.writerows(rc_links)

    # 7. Ingest Data Issues (data_issue.csv)
    issue_file = os.path.join(DATA_SEED_KB, "data_issue.csv")
    with open(issue_file, encoding="utf-8") as f:
        issues = list(csv.DictReader(f))
    existing_issue_ids = {iss["issue_id"] for iss in issues}

    with open(os.path.join(DATA_RAW_MME, "curriculum_notes_discrepancies.csv"), encoding="utf-8") as f:
        iss_reader = csv.DictReader(f)
        for r in iss_reader:
            iss_id = f"ISSUE_MME_CURR_{int(r['item_no']):02d}"
            severity = "medium"
            if r["item_no"] == "3":
                severity = "high"
            if iss_id not in existing_issue_ids:
                issues.append({
                    "issue_id": iss_id,
                    "entity_type": "curriculum",
                    "entity_key": r["item"],
                    "severity": severity,
                    "description": r["issue_found"],
                    "resolution_notes": r["how_shown"],
                    "status": "acknowledged"
                })
                existing_issue_ids.add(iss_id)

    # Add duplicate project #43 issue
    if "ISSUE_MME_PROJECT_DUP_43" not in existing_issue_ids:
        issues.append({
            "issue_id": "ISSUE_MME_PROJECT_DUP_43",
            "entity_type": "research_project",
            "entity_key": "PROJ_MM_SPON_43",
            "severity": "low",
            "description": "Improving damping capacity of cast Nickel aluminum Bronze (NAB) alloys is listed twice in source portfolio (#33 and #43).",
            "resolution_notes": "Preserved both entries with duplicate marker in raw portfolio; mapped to Dr. Partha Sarathi De.",
            "status": "acknowledged"
        })
        existing_issue_ids.add("ISSUE_MME_PROJECT_DUP_43")

    with open(issue_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(issues[0].keys()))
        writer.writeheader()
        writer.writerows(issues)

    print(">>> MME data successfully ingested and merged into data/seed/kb/!")

if __name__ == "__main__":
    run()
