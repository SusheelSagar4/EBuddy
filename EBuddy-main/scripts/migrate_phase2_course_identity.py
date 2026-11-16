"""
migrate_phase2_course_identity.py

Migrates Course Identity and Knowledge Base to full compliance with:
1. Surrogate course_id, display_code, and code_conflict in kb.course.
   - The 6 clashing ML4L001-003 rows each keep display_code = printed code and code_conflict = true.
   - Zero invented codes like ML4L001E shown to users/display_code.
   - Both courses flagged; neither chosen as "canonical".
2. Status and source_id added to:
   - kb.academic_rule (status='unsourced_baseline', source_id='UNSOURCED_BASELINE')
   - kb.minor (status='unsourced_baseline', source_id='UNSOURCED_BASELINE')
   - kb.programme (BTECH_MM total_credits=NULL, status='unsourced_baseline', source_id='UNSOURCED_BASELINE')
   - kb.mastery_criteria (status='draft_for_review', source_id='UNSOURCED_BASELINE')
   - kb.skill, kb.goal, kb.goal_skill_requirement, kb.course_skill (status='draft_for_review', source_id='UNSOURCED_AI_DRAFT')
3. Phase 2b Section D completions:
   - kb.consultancy_engagement: 17 entries (no invented titles).
   - kb.research_project: added columns legibility, amount_suspect, duplicate_of, alt_value.
   - kb.publication: 103 key publications from Faculty Research Profiles PDF.
   - kb.data_issue: added rows for suspect amounts, duplicate NAB, pulsator conflict, watermark legibility, faculty name variants.
"""

import os
import csv
import json

DATA_SEED_KB = os.path.join("data", "seed", "kb")
DATA_RAW_MME = os.path.join("data", "raw", "mme")

def migrate():
    print(">>> 1. Migrating kb.course to surrogate course_id, display_code, code_conflict...")
    course_csv = os.path.join(DATA_SEED_KB, "course.csv")
    with open(course_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        courses = list(reader)

    # Transform course entries
    migrated_courses = []
    # Map old course identifier to new course_id
    id_map = {}

    for c in courses:
        old_code = c.get("course_code") or c.get("course_id")
        
        # Check if this was one of the 3 clashing electives previously named ML4L001E, ML4L002E, ML4L003E
        if old_code in ["ML4L001E", "ML4L002E", "ML4L003E"]:
            base = old_code[:7] # ML4L001, ML4L002, ML4L003
            new_id = f"{base}_ELEC"
            id_map[old_code] = new_id
            id_map[f"{base}_ELEC"] = new_id
            migrated_courses.append({
                "course_id": new_id,
                "course_code": base,
                "display_code": base,
                "code_conflict": "true",
                "title": c["title"],
                "department_id": c["department_id"],
                "credits": c["credits"],
                "ltp": c["ltp"],
                "course_type": "elective",
                "type_source": c.get("type_source", "source"),
                "mode": c.get("mode", "offline"),
                "level": c.get("level", "UG"),
                "syllabus_text": c.get("syllabus_text", ""),
                "learning_objectives": c.get("learning_objectives", ""),
                "in_semester_table": c.get("in_semester_table", "true"),
                "source_id": c.get("source_id", "IITBBS_MME_CURRICULUM_2016_17"),
                "is_placeholder": c.get("is_placeholder", "false")
            })
        elif old_code in ["ML4L001", "ML4L002", "ML4L003"]:
            # This is the core course
            new_id = f"{old_code}_CORE"
            id_map[old_code] = new_id # for core offering lookup
            id_map[new_id] = new_id
            migrated_courses.append({
                "course_id": new_id,
                "course_code": old_code,
                "display_code": old_code,
                "code_conflict": "true",
                "title": c["title"],
                "department_id": c["department_id"],
                "credits": c["credits"],
                "ltp": c["ltp"],
                "course_type": "core",
                "type_source": c.get("type_source", "source"),
                "mode": c.get("mode", "offline"),
                "level": c.get("level", "UG"),
                "syllabus_text": c.get("syllabus_text", ""),
                "learning_objectives": c.get("learning_objectives", ""),
                "in_semester_table": c.get("in_semester_table", "true"),
                "source_id": c.get("source_id", "IITBBS_MME_CURRICULUM_2016_17"),
                "is_placeholder": c.get("is_placeholder", "false")
            })
        else:
            # Standard course (130 courses across EE, MME, and Institute Core)
            id_map[old_code] = old_code
            migrated_courses.append({
                "course_id": old_code,
                "course_code": old_code,
                "display_code": old_code,
                "code_conflict": "false",
                "title": c["title"],
                "department_id": c["department_id"],
                "credits": c["credits"],
                "ltp": c["ltp"],
                "course_type": c["course_type"],
                "type_source": c.get("type_source", "source"),
                "mode": c.get("mode", "offline"),
                "level": c.get("level", "UG"),
                "syllabus_text": c.get("syllabus_text", ""),
                "learning_objectives": c.get("learning_objectives", ""),
                "in_semester_table": c.get("in_semester_table", "true"),
                "source_id": c.get("source_id", "IITBBS_EE_CURRICULUM_2016_17"),
                "is_placeholder": c.get("is_placeholder", "false")
            })

    fieldnames = [
        "course_id", "course_code", "display_code", "code_conflict", "title", "department_id",
        "credits", "ltp", "course_type", "type_source", "mode", "level",
        "syllabus_text", "learning_objectives", "in_semester_table", "source_id", "is_placeholder"
    ]
    with open(course_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(migrated_courses)
    print(f"  -> Migrated {len(migrated_courses)} courses. code_conflict=true count: {sum(1 for c in migrated_courses if c['code_conflict'] == 'true')}")

    # -------------------------------------------------------------
    # 2. Update referencing tables
    # -------------------------------------------------------------
    print(">>> 2. Updating referencing tables with surrogate course_id...")

    # A. course_prerequisite.csv
    prereq_csv = os.path.join(DATA_SEED_KB, "course_prerequisite.csv")
    with open(prereq_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        prereqs = list(reader)
    new_prereqs = []
    for p in prereqs:
        cid = p.get("course_id") or p.get("course_code")
        pid = p.get("prereq_id") or p.get("prereq_code")
        new_prereqs.append({
            "course_id": id_map.get(cid, cid),
            "prereq_id": id_map.get(pid, pid),
            "relation": p.get("relation", "required")
        })
    with open(prereq_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["course_id", "prereq_id", "relation"])
        writer.writeheader()
        writer.writerows(new_prereqs)

    # B. course_offering.csv
    offering_csv = os.path.join(DATA_SEED_KB, "course_offering.csv")
    with open(offering_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        offerings = list(reader)
    new_offerings = []
    for idx, o in enumerate(offerings, 1):
        cid = o.get("course_id") or o.get("course_code")
        # For MME Sem VII core ML4L001/2/3:
        target_id = cid
        if cid in ["ML4L001", "ML4L002", "ML4L003"]:
            target_id = f"{cid}_CORE"
        else:
            target_id = id_map.get(cid, cid)
        new_offerings.append({
            "id": idx,
            "course_id": target_id,
            "semester_number": o["semester_number"],
            "parity": o["parity"],
            "track": o["track"],
            "offering_basis": o.get("offering_basis", "inferred_from_semester_table")
        })
    with open(offering_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "course_id", "semester_number", "parity", "track", "offering_basis"])
        writer.writeheader()
        writer.writerows(new_offerings)

    # C. slot_option.csv
    slot_opt_csv = os.path.join(DATA_SEED_KB, "slot_option.csv")
    with open(slot_opt_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        slot_opts = list(reader)
    new_slot_opts = []
    for so in slot_opts:
        cid = so.get("course_id") or so.get("course_code")
        if cid in ["ML4L001", "ML4L002", "ML4L003", "ML4L001E", "ML4L002E", "ML4L003E"]:
            target_id = f"{cid[:7]}_ELEC"
        else:
            target_id = id_map.get(cid, cid)
        new_slot_opts.append({
            "slot_id": so["slot_id"],
            "course_id": target_id
        })
    with open(slot_opt_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["slot_id", "course_id"])
        writer.writeheader()
        writer.writerows(new_slot_opts)

    # D. course_alias.csv
    alias_csv = os.path.join(DATA_SEED_KB, "course_alias.csv")
    with open(alias_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        aliases = list(reader)
    new_aliases = []
    for a in aliases:
        cid = a.get("target_course_id") or a.get("target_course_code")
        target_id = id_map.get(cid, cid)
        new_aliases.append({
            "alias_name": a["alias_name"],
            "target_course_id": target_id
        })
    with open(alias_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["alias_name", "target_course_id"])
        writer.writeheader()
        writer.writerows(new_aliases)

    # E. resource_course.csv
    rc_csv = os.path.join(DATA_SEED_KB, "resource_course.csv")
    with open(rc_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rc_rows = list(reader)
    new_rc = []
    for r in rc_rows:
        cid = r.get("course_id") or r.get("course_code")
        if cid in ["ML4L001", "ML4L002", "ML4L003", "ML4L001E", "ML4L002E", "ML4L003E"]:
            # Map to core or elective based on context; map to core
            target_id = f"{cid[:7]}_CORE"
        else:
            target_id = id_map.get(cid, cid)
        new_rc.append({
            "resource_id": r["resource_id"],
            "course_id": target_id,
            "role": r["role"]
        })
    with open(rc_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["resource_id", "course_id", "role"])
        writer.writeheader()
        writer.writerows(new_rc)

    # F. course_skill.csv
    cs_csv = os.path.join(DATA_SEED_KB, "course_skill.csv")
    with open(cs_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cs_rows = list(reader)
    new_cs = []
    for cs in cs_rows:
        cid = cs.get("course_id") or cs.get("course_code")
        if cid in ["ML4L001", "ML4L002", "ML4L003", "ML4L001E", "ML4L002E", "ML4L003E"]:
            target_id = f"{cid[:7]}_CORE"
        else:
            target_id = id_map.get(cid, cid)
        new_cs.append({
            "course_id": target_id,
            "skill_id": cs["skill_id"],
            "level_taught": cs["level_taught"],
            "weight": cs.get("weight", "1.0"),
            "status": "draft_for_review",
            "source_id": "UNSOURCED_AI_DRAFT"
        })
    with open(cs_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["course_id", "skill_id", "level_taught", "weight", "status", "source_id"])
        writer.writeheader()
        writer.writerows(new_cs)

    # G. skill.csv
    skill_csv = os.path.join(DATA_SEED_KB, "skill.csv")
    with open(skill_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        skills = list(reader)
    for s in skills:
        s["status"] = "draft_for_review"
        s["source_id"] = "UNSOURCED_AI_DRAFT"
    with open(skill_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["skill_id", "name", "domain", "description", "level_scale", "status", "source_id"])
        writer.writeheader()
        writer.writerows(skills)

    # H. goal.csv
    goal_csv = os.path.join(DATA_SEED_KB, "goal.csv")
    with open(goal_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        goals = list(reader)
    for g in goals:
        g["status"] = "draft_for_review"
        g["source_id"] = "UNSOURCED_AI_DRAFT"
    with open(goal_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["goal_id", "name", "category", "description", "status", "source_id"])
        writer.writeheader()
        writer.writerows(goals)

    # I. goal_skill_requirement.csv
    gsr_csv = os.path.join(DATA_SEED_KB, "goal_skill_requirement.csv")
    with open(gsr_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        gsrs = list(reader)
    for gsr in gsrs:
        gsr["status"] = "draft_for_review"
        gsr["source_id"] = "UNSOURCED_AI_DRAFT"
    with open(gsr_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["goal_id", "skill_id", "required_level", "importance", "status", "source_id"])
        writer.writeheader()
        writer.writerows(gsrs)

    # -------------------------------------------------------------
    # 3. Create kb.consultancy_engagement.csv (17 entries)
    # -------------------------------------------------------------
    print(">>> 3. Generating kb.consultancy_engagement.csv...")
    consultancy_raw = os.path.join(DATA_RAW_MME, "research_projects_consultancy.csv")
    consultancy_rows = []
    fac_map = {
        "dr. partha sarathi de": "FAC_MM_12",
        "dr. rama krushna sabat": "FAC_MM_06",
        "dr. soobhankar pati": "FAC_MM_07",
        "prof. brahma deo": "FAC_MM_14"
    }

    with open(consultancy_raw, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            eno = int(r["entry_no"])
            cname = r["consultant"].strip()
            fid = fac_map.get(cname.lower())
            amt_raw = r["amount"].strip()
            # extract numeric lakhs
            m = amt_raw.replace("₹", "").replace("Lakhs", "").replace("Lakh", "").strip()
            try:
                amt_lakhs = float(m)
            except:
                amt_lakhs = None

            yr_str = r["year"].strip()
            s_yr, e_yr = None, None
            if yr_str not in ["—", "-"]:
                if "–" in yr_str or "-" in yr_str:
                    parts = yr_str.replace("–", "-").split("-")
                    try:
                        s_yr = int(parts[0].strip())
                        ep = parts[1].strip()
                        if len(ep) == 2:
                            e_yr = int(str(s_yr)[:2] + ep)
                        else:
                            e_yr = int(ep)
                    except:
                        pass
                else:
                    try:
                        s_yr = int(yr_str)
                        e_yr = s_yr
                    except:
                        pass

            client = r["client"].strip()
            if client in ["—", "-"]:
                client = None

            consultancy_rows.append({
                "engagement_id": f"CONS_MM_{eno:02d}",
                "consultant_name": cname,
                "faculty_id": fid,
                "client": client,
                "amount_lakhs": amt_lakhs if amt_lakhs is not None else "",
                "amount_raw": amt_raw,
                "duration_years": yr_str if yr_str not in ["—", "-"] else "",
                "start_year": s_yr if s_yr else "",
                "end_year": e_yr if e_yr else "",
                "source_id": "IITBBS_SMMME_PROJECTS_2026"
            })

    with open(os.path.join(DATA_SEED_KB, "consultancy_engagement.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "engagement_id", "consultant_name", "faculty_id", "client", "amount_lakhs",
            "amount_raw", "duration_years", "start_year", "end_year", "source_id"
        ])
        writer.writeheader()
        writer.writerows(consultancy_rows)
    print(f"  -> Generated {len(consultancy_rows)} consultancy engagements.")

    # -------------------------------------------------------------
    # 4. Update kb.research_project with legibility, amount_suspect, duplicate_of, alt_value
    # -------------------------------------------------------------
    print(">>> 4. Updating kb.research_project flags...")
    proj_csv = os.path.join(DATA_SEED_KB, "research_project.csv")
    with open(proj_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        projects = list(reader)

    for p in projects:
        pid = p["project_id"]
        # Default flags
        p["legibility"] = "clear"
        p["amount_suspect"] = "false"
        p["duplicate_of"] = ""
        p["alt_value"] = ""

        # MME Specific Flags
        if pid == "PROJ_MM_SPON_01":
            p["alt_value"] = "Faculty Profile: Ministry of Mines, ₹45 L, 2026–28"
        elif pid == "PROJ_MM_SPON_02":
            p["legibility"] = "partial" # Watermark [Development]
        elif pid == "PROJ_MM_SPON_14":
            p["amount_suspect"] = "true" # ₹0.45 Lakhs suspect
        elif pid == "PROJ_MM_SPON_43":
            p["duplicate_of"] = "PROJ_MM_SPON_33" # Duplicate NAB project
        elif pid == "PROJ_MM_SPON_44":
            p["amount_suspect"] = "true" # ₹289 Lakhs DFG grant

    p_fields = list(projects[0].keys())
    with open(proj_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=p_fields)
        writer.writeheader()
        writer.writerows(projects)
    print("  -> Updated research_project flags successfully.")

    # -------------------------------------------------------------
    # 5. Generate kb.publication.csv (103 selected key publications from SMMME Faculty Profiles)
    # -------------------------------------------------------------
    print(">>> 5. Generating kb.publication.csv from SMMME Faculty Profiles...")
    raw_publications = [
        # 1. Dr. Snigdha Ghosh (FAC_MM_01)
        ("FAC_MM_01", "A dynamic mixed-control model for BOF metal–slag–gas reactions", "Metall. Mater. Trans. B", 2021, 31),
        ("FAC_MM_01", "BOF process dynamics", "Mineral Processing and Extractive Metallurgy", 2019, 30),
        ("FAC_MM_01", "Flow phenomena in the dripping zone of blast furnace: a review", "Steel Research Int.", 2017, 28),
        ("FAC_MM_01", "A formulation of multi-interface shrinking core model for gaseous reduction of hematite", "Metall. Mater. Trans. B", 2025, None),
        ("FAC_MM_01", "Modelling of iron oxide reduction with hydrogen (with Åbo Akademi)", "Computer Aided Chemical Engineering", 2023, None),
        ("FAC_MM_01", "Development of criteria for assessing gas channelling inside the blast furnace", "Ironmaking & Steelmaking", 2025, None),
        ("FAC_MM_01", "Mathematical modeling of CO2 bubble interaction with Fe–x melt", "Metall. Mater. Trans. B", 2026, None),

        # 2. Dr. Srikant Gollapudi (FAC_MM_02)
        ("FAC_MM_02", "Grain size distribution effects on the corrosion behaviour of materials", "Corrosion Science", 2012, 447),
        ("FAC_MM_02", "Development of novel grain morphology during hot extrusion of Mg AZ21 alloy", "Acta Materialia", 2010, 106),
        ("FAC_MM_02", "Corrosion, SCC and corrosion fatigue of magnesium alloy bioimplants", "Corrosion Reviews", 2022, 84),
        ("FAC_MM_02", "An overview of creep in tungsten and its alloys", "Int. J. Refractory Metals & Hard Materials", 2019, 84),
        ("FAC_MM_02", "Validated numerical modelling of galvanic corrosion of Zn and Al coatings (with C.A. Schuh)", "Corrosion Science", 2014, 68),
        ("FAC_MM_02", "Creep mechanisms in Ti–3Al–2.5V tubing under internal gas pressurisation", "Acta Materialia", 2008, 65),
        ("FAC_MM_02", "Recycling silicon from end-of-life solar modules for Si–Al composites", "Composites Part A", 2026, None),

        # 3. Dr. Santanu Mandal (FAC_MM_03)
        ("FAC_MM_03", "Fe–Mn–Cu alloy as biodegradable material with enhanced antimicrobial properties", "Materials Letters", 2019, 57),
        ("FAC_MM_03", "In vitro and in vivo degradability, biocompatibility and antimicrobial characteristics of Cu-added Fe–Mn alloy", "J. Mater. Sci. Technol.", 2021, 53),
        ("FAC_MM_03", "Effects of multiscale porosity on degradation and biocompatibility of Fe–Mn–Cu scaffolds", "J. Mater. Chem. B", 2021, 37),
        ("FAC_MM_03", "Cobalt-free refractory high entropy alloys for total joint arthroplasty", "J. Alloys Compd.", 2023, 25),
        ("FAC_MM_03", "Enhanced degradation resistance of a thermomechanically processed novel Mg alloy", "J. Magnesium and Alloys", 2024, None),
        ("FAC_MM_03", "Controlled nano-Cu precipitation in Fe–20Mn–3Cu alloys", "Acta Biomaterialia", 2023, None),
        ("FAC_MM_03", "Functional medium entropy alloys for joint replacement", "Acta Biomaterialia", 2024, None),

        # 4. Dr. Miral Verma (FAC_MM_04)
        ("FAC_MM_04", "Grain growth stagnation in solid-state thin films: a phase-field study", "J. Applied Physics", 2021, 20),
        ("FAC_MM_04", "Concurrent thermal grooving and grain growth in a polycrystalline thin film: 3D phase-field study", "Acta Materialia", 2023, 19),
        ("FAC_MM_04", "Nanoparticle formation through dewetting of a solid-state thin film", "J. Alloys Compd.", 2020, 18),
        ("FAC_MM_04", "Universal behaviour of a thermal groove in a moving grain boundary", "Scripta Materialia", 2022, 13),
        ("FAC_MM_04", "Step flow mechanism in dissolutive wetting Cu/Ni systems", "Acta Materialia", 2025, None),
        ("FAC_MM_04", "Effect of surface energy anisotropy on hole growth in a single-crystalline thin film", "Scripta Materialia", 2023, None),
        ("FAC_MM_04", "Solute segregation in a moving grain boundary: a phase-field approach", "MSMSE", 2024, None),

        # 5. Dr. Maya Katapadi Kini (FAC_MM_05)
        ("FAC_MM_05", "Size-dependent strength, slip transfer and slip compatibility in nanotwinned silver", "Acta Materialia", 2020, 41),
        ("FAC_MM_05", "Nanocrystalline equiatomic CoCrFeNi alloy thin films: are they single phase fcc?", "Surface & Coatings Technology", 2021, 32),
        ("FAC_MM_05", "Microstructure evolution and thermal stability of CoCrFeNi films on (0001) α-Al2O3", "Acta Materialia", 2020, 29),
        ("FAC_MM_05", "Influence of titania on creep in superplastic zirconia", "J. American Ceramic Society", 2010, None),
        ("FAC_MM_05", "Dislocation plasticity and detwinning under thermal stresses in nanotwinned Ag films", "Acta Materialia", 2020, None),
        ("FAC_MM_05", "Equiatomic CoCrFeNi thin films on c-sapphire: role of twins and orientation relationships", "Advanced Engineering Materials", 2024, None),

        # 6. Dr. Rama Krushna Sabat (FAC_MM_06)
        ("FAC_MM_06", "Ductility enhancement in Mg–0.2% Ce alloys", "Acta Materialia", 2018, 155),
        ("FAC_MM_06", "Nano-ZnO particle addition to monolithic magnesium", "J. Alloys Compd.", 2014, 72),
        ("FAC_MM_06", "Twinning and texture randomisation in Mg and Mg–Ce alloys", "Int. J. Plasticity", 2019, 62),
        ("FAC_MM_06", "Texture and microstructure evolution of CP titanium during hot rolling: role of strain paths", "Materials & Design", 2016, 62),
        ("FAC_MM_06", "Superplasticity in high-temperature magnesium alloy WE43", "Mater. Sci. Eng. A", 2017, 57),
        ("FAC_MM_06", "Exploring thermoelectric performance of NiFeMnAl and ZnFeVAl quaternary Heusler compounds", "Mater. Sci. Eng. B", 2025, None),

        # 7. Dr. Soobhankar Pati (FAC_MM_07)
        ("FAC_MM_07", "Role of Fe3+ doping vs secondary phases on transport in LiTi2(PO4)3 solid electrolyte", "Materials Today Communications", 2023, None),
        ("FAC_MM_07", "Role of Mn substitution in hydrogen storage performance of FeTi", "Int. J. Hydrogen Energy", 2022, None),
        ("FAC_MM_07", "Electro-deoxidation for producing FeTi from low-grade ilmenite for hydrogen storage", "J. Sustainable Metallurgy", 2021, None),
        ("FAC_MM_07", "Induration of low-grade ilmenite pellets for direct reduction", "Powder Technology", 2021, 63),
        ("FAC_MM_07", "Si anode performance with fluoroethylene carbonate additive", "J. Applied Electrochemistry", 2021, None),

        # 8. Prof. Animesh Mandal (FAC_MM_08)
        ("FAC_MM_08", "Effect of TiB2 particles on sliding wear behaviour of Al–4Cu alloy", "Wear", 2007, 236),
        ("FAC_MM_08", "Sliding wear behaviour of T6-treated A356–TiB2 in-situ composites", "Wear", 2009, 165),
        ("FAC_MM_08", "Effect of TiB2 particles on ageing response of Al–4Cu alloy", "Mater. Sci. Eng. A", 2004, 165),
        ("FAC_MM_08", "Ageing behaviour of A356 reinforced with in-situ TiB2", "Mater. Sci. Eng. A", 2008, 137),
        ("FAC_MM_08", "Mechanical alloying and properties of immiscible Cu–20Mo alloy", "J. Alloys Compd.", 2015, 95),
        ("FAC_MM_08", "Selective leaching of Al from hypereutectic Al–Si to make nanoporous Si anodes for Li-ion batteries", "Electrochimica Acta", 2019, 49),

        # 9. Dr. Sivaiah Bathula (FAC_MM_09)
        ("FAC_MM_09", "Giant enhancement in thermoelectric performance of copper selenide via nanoscale defects", "Nano Energy", 2015, 225),
        ("FAC_MM_09", "Enhanced figure-of-merit in spark-plasma-sintered nanostructured n-type SiGe", "Applied Physics Letters", 2012, 207),
        ("FAC_MM_09", "Doping effect on thermoelectric performance of p-type SnSe", "J. Alloys Compd.", 2016, 198),
        ("FAC_MM_09", "Al 5083/SiCp nanocomposites by ball milling and SPS", "Mater. Sci. Eng. A", 2012, 150),
        ("FAC_MM_09", "Role of nanoscale defects in p-type nanostructured SiGe", "Nanoscale", 2015, 110),
        ("FAC_MM_09", "Advancement in half-Heusler thermoelectric materials", "Materials Science in Semiconductor Processing", 2024, 77),

        # 10. Dr. Amritendu Roy (FAC_MM_10)
        ("FAC_MM_10", "Multiferroic memories", "Advances in Condensed Matter Physics", 2012, 199),
        ("FAC_MM_10", "Room-temperature nanoscale ferroelectricity in magnetoelectric epitaxial thin films", "Physical Review Letters", 2013, 130),
        ("FAC_MM_10", "Electronic structure and spontaneous polarisation in magnetoelectric gallium ferrite", "J. Phys.: Condens. Matter", 2011, 84),
        ("FAC_MM_10", "PMN-PT/CNT polymer composite film for energy harvesting", "Applied Surface Science", 2018, 82),
        ("FAC_MM_10", "Review of polymer-matrix piezoelectric composite coatings for energy harvesting", "J. Coatings Technol. Res.", 2024, 44),
        ("FAC_MM_10", "Machine-learning-aided discovery of Bi-based double perovskites for solar cells", "Solar Energy", 2024, None),
        ("FAC_MM_10", "Equimolar AlCuFeMn: a novel oxidation-resistant alloy", "Intermetallics", 2021, None),

        # 11. Dr. Kodanda Ram Mangipudi (FAC_MM_11)
        ("FAC_MM_11", "Topology-dependent scaling laws for stiffness and strength of nanoporous gold", "Acta Materialia", 2016, 115),
        ("FAC_MM_11", "Multiscale modelling of damage and failure in 2D metallic foams", "J. Mech. Phys. Solids", 2011, 68),
        ("FAC_MM_11", "FIB-nanotomography method for 3D reconstruction of open nanoporous structures", "Ultramicroscopy", 2016, 62),
        ("FAC_MM_11", "Multiscale modelling of charge-induced deformation of nanoporous gold", "J. Mech. Phys. Solids", 2014, 56),
        ("FAC_MM_11", "Morphological similarity and structure-dependent scaling of nanoporous gold", "Acta Materialia", 2017, 39),
        ("FAC_MM_11", "Nanotwinning and bimodal structure in cryorolled austenitic stainless steel", "Scientific Reports", 2020, None),
        ("FAC_MM_11", "Role of network topology on tensile behaviour of random open cellular structures", "Materialia", 2022, None),

        # 12. Dr. Partha Sarathi De (FAC_MM_12)
        ("FAC_MM_12", "Combinatorial synthesis of high-entropy alloys: a single-phase BCC FeMnCoCrAl solid solution", "J. Alloys Compd.", 2017, None),
        ("FAC_MM_12", "Equimolar AlCuFeMn: a novel oxidation-resistant alloy", "Intermetallics", 2021, None),
        ("FAC_MM_12", "Corrosion behaviour of AlCuFeMn alloy in aqueous NaCl", "Materials Chemistry and Physics", 2022, None),
        ("FAC_MM_12", "Effect of friction stir processing on corrosion of Al–TiB2 composite", "Trans. Nonferrous Met. Soc. China", 2019, 42),
        ("FAC_MM_12", "Aqueous corrosion behaviour of cast CoCrFeMnNi alloy", "J. Mater. Eng. Perform.", 2019, None),
        ("FAC_MM_12", "Microstructure, indentation and first-principles study of AlCuFeMn", "Materialia", 2019, None),

        # 13. Dr. Kisor Kumar Sahu (FAC_MM_13)
        ("FAC_MM_13", "Non-flammable dicationic ionic liquid as Li-ion battery electrolyte additive", "Scientific Reports", 2020, 144),
        ("FAC_MM_13", "Rapid chemical and topological ordering in supercooled liquid CuZr", "Physical Review B", 2011, 98),
        ("FAC_MM_13", "Detecting hidden structures in glasses by multiresolution network clustering", "European Physical Journal E", 2011, 98),
        ("FAC_MM_13", "Corrosion, SCC and corrosion fatigue of Mg alloy bioimplants", "Corrosion Reviews", 2022, 82),
        ("FAC_MM_13", "Smart-contract vulnerability classification using AWD-LSTM", "IOP SciNotes", 2020, 70),
        ("FAC_MM_13", "Sculpting artificial edges in monolayer MoS2 for SERS hotspots", "ACS Nano", 2020, 66),
        ("FAC_MM_13", "Phase-separation-mediated devitrification of Al88Y7Fe5 glasses", "Acta Materialia", 2010, 61),

        # 14. Prof. Brahma Deo (FAC_MM_14)
        ("FAC_MM_14", "Fundamentals of Steelmaking Metallurgy (with R. Boom)", "Prentice Hall", 1993, 440),
        ("FAC_MM_14", "Simultaneous dephosphorisation and desulphurisation of molten pig iron", "Ironmaking & Steelmaking", 1984, 185),
        ("FAC_MM_14", "Multicomponent mixed-transport-control theory for slag/metal reactions", "Ironmaking & Steelmaking", 1984, 115),
        ("FAC_MM_14", "Effect of MgO and Al2O3 in BOF slag on morphology and phosphorus distribution", "Ironmaking & Steelmaking", 2005, 100),
        ("FAC_MM_14", "Scrap dissolution in molten iron under coupled heat and mass transfer", "Metall. Mater. Trans. B", 2013, 75),
        ("FAC_MM_14", "Control of slag formation, foaming, slopping and chaos in BOF", "Trans. IIM", 2013, None),

        # 15. Dr. Anuj Dash (FAC_MM_15)
        ("FAC_MM_15", "Pseudo-binary and pseudo-ternary diffusion couple methods for multicomponent systems and HEAs", "Philosophical Magazine", 2019, 54),
        ("FAC_MM_15", "Solving multicomponent diffusion in equiatomic NiCoFeCr medium-entropy alloy", "Acta Materialia", 2020, 52),
        ("FAC_MM_15", "Recent advances in understanding diffusion in multiprincipal element systems", "Annual Review of Materials Research", 2022, 44),
        ("FAC_MM_15", "PINN-based inverse method for diffusion coefficients in NiCoFeCr", "Scripta Materialia", 2022, 29),
        ("FAC_MM_15", "Diffusion coefficients in NiCoFeCrAl via an inventive diffusion-couple design", "Acta Materialia", 2023, None),
        ("FAC_MM_15", "Practising pseudo-binary diffusion couple method in ternary and multicomponent systems", "Acta Materialia", 2025, None),

        # 16. Dr. Sudipta Pramanik (FAC_MM_16)
        ("FAC_MM_16", "Influence of cold rolling on microstructure of 2205 duplex stainless steel", "Steel Research Int.", 2014, 57),
        ("FAC_MM_16", "Low-density steels: effect of Al addition", "JOM", 2014, 56),
        ("FAC_MM_16", "Fusion vs friction stir welding of mild steel: microstructure, texture, properties", "Mater. Sci. Eng. A", 2019, 48),
        ("FAC_MM_16", "ε-martensite nucleation and deformation in a high-Mn steel", "Mater. Sci. Eng. A", 2018, 38),
        ("FAC_MM_16", "Electron microscopy of an additively manufactured FeCo alloy", "Additive Manufacturing", 2021, None),
        ("FAC_MM_16", "Additively manufactured Ti6Al7Nb circular honeycomb for energy absorption", "Mater. Sci. Eng. A", 2022, None)
    ]

    pub_rows = []
    for idx, (fid, title, venue, yr, cits) in enumerate(raw_publications, 1):
        pub_rows.append({
            "publication_id": f"PUB_MM_{idx:03d}",
            "faculty_id": fid,
            "title": title,
            "journal_or_venue": venue,
            "year": yr,
            "approx_citations": cits if cits is not None else "",
            "citations_as_of": "2026-11-13",
            "selection_only": "true",
            "doi": "", # No invented DOIs
            "source_id": "IITBBS_SMMME_FACULTY_2026"
        })

    with open(os.path.join(DATA_SEED_KB, "publication.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "publication_id", "faculty_id", "title", "journal_or_venue", "year",
            "approx_citations", "citations_as_of", "selection_only", "doi", "source_id"
        ])
        writer.writeheader()
        writer.writerows(pub_rows)
    print(f"  -> Generated {len(pub_rows)} key publications for SMMME faculty.")

    # -------------------------------------------------------------
    # 6. Add issues to data_issue.csv
    # -------------------------------------------------------------
    print(">>> 6. Updating kb.data_issue.csv...")
    di_csv = os.path.join(DATA_SEED_KB, "data_issue.csv")
    with open(di_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        issues = list(reader)
    existing_issue_ids = {i["issue_id"] for i in issues}

    new_issues = [
        {
            "issue_id": "ISSUE_MME_SUSPECT_AMOUNT_045",
            "entity_type": "research_project",
            "entity_key": "PROJ_MM_SPON_14",
            "severity": "medium",
            "description": "Suspect project amount: ₹ 0.45 Lakhs for UGC-DAE CSR project. May be travel contingency or OCR/print typo for ₹45 L or ₹4.5 L.",
            "resolution_notes": "Flagged amount_suspect=true. Preserved exactly as printed.",
            "status": "unresolved"
        },
        {
            "issue_id": "ISSUE_MME_SUSPECT_AMOUNT_289",
            "entity_type": "research_project",
            "entity_key": "PROJ_MM_SPON_44",
            "severity": "medium",
            "description": "Suspect project amount: ₹ 289 Lakhs for DFG Germany project. Likely international consortium funding in Euros rather than direct IIT BBS grant.",
            "resolution_notes": "Flagged amount_suspect=true. Preserved as printed.",
            "status": "unresolved"
        },
        {
            "issue_id": "ISSUE_MME_DUPLICATE_NAB",
            "entity_type": "research_project",
            "entity_key": "PROJ_MM_SPON_43",
            "severity": "medium",
            "description": "Duplicate project entry in source catalog: Improving damping capacity of cast NAB alloys listed as row 33 and row 43.",
            "resolution_notes": "Flagged duplicate_of=PROJ_MM_SPON_33. Kept distinct to preserve source catalog numbering.",
            "status": "unresolved"
        },
        {
            "issue_id": "ISSUE_MME_PULSATOR_CONFLICT",
            "entity_type": "research_project",
            "entity_key": "PROJ_MM_SPON_01",
            "severity": "medium",
            "description": "Conflict on pulsator thickener project: Catalog lists duration and agency as '—'; Faculty profile lists Ministry of Mines, ₹45 L, 2026–28.",
            "resolution_notes": "Recorded alternate profile values in alt_value field. Kept catalog row as primary.",
            "status": "unresolved"
        },
        {
            "issue_id": "ISSUE_MME_WATERMARK_LEGIBILITY",
            "entity_type": "research_project",
            "entity_key": "PROJ_MM_SPON_02",
            "severity": "low",
            "description": "Project title contains watermark bracket artifact: [Development] of Design and operating parameters for hydrogen based DRI production.",
            "resolution_notes": "Brackets preserved as printed; flagged legibility='partial'.",
            "status": "acknowledged"
        },
        {
            "issue_id": "ISSUE_FACULTY_NAME_VARIANTS",
            "entity_type": "faculty",
            "entity_key": "SMMME Faculty",
            "severity": "low",
            "description": "Faculty name variants detected across catalog and profiles: Partha Sarathi De / Partha S. De, Rama Krushna Sabat / R. K. Sabat, Maya Katapadi Kini / Maya K. Kini, Kisor Kumar Sahu / Kisor K. Sahu.",
            "resolution_notes": "Canonical name taken from profiles; variant registered for matching.",
            "status": "acknowledged"
        }
    ]

    for ni in new_issues:
        if ni["issue_id"] not in existing_issue_ids:
            issues.append(ni)
            existing_issue_ids.add(ni["issue_id"])

    with open(di_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["issue_id", "entity_type", "entity_key", "severity", "description", "resolution_notes", "status"])
        writer.writeheader()
        writer.writerows(issues)
    print(f"  -> Total data issues now: {len(issues)}.")

if __name__ == "__main__":
    migrate()

