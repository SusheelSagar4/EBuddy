"""
build_da_csvs.py
eBuddy Data Analyst (DA) Knowledge Base Builder
Inter IIT Tech Meet 15.0 - Adobe Personalised Learning Buddy

Ingests:
  Data_Analyst_Roadmap.xlsx (9 sheets)

Outputs (UTF-8 with BOM):
  output/01_da_roadmap_overview.csv
  output/02_phase_modules_resources.csv
  output/03_skills_catalog.csv
  output/04_phase_summary_readiness_checkpoints.csv
  output/05_projects.csv
  output/06_project_rubric_items.csv
  output/07_pacing_templates.csv
  output/08_milestones.csv
  output/09_learning_methods.csv
  (mirrored to da/output/)
"""

import os
import sys
import csv
import re
import openpyxl

# Reconfigure stdout for Windows console UTF-8 support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ----------------------------------------------------
# 1. Human-Reviewable Dictionaries (Derived Texts & Maps)
# ----------------------------------------------------

PHASE_OBJECTIVES_DERIVED = {
    "DA-PH1": "Build quantitative and technical data foundations across spreadsheets, descriptive statistics, probability rules, and basic SQL retrieval. Learn to organize tabular data, compute statistical distributions, summarize datasets with formulas and pivot tables, and query relational databases.",
    "DA-PH2": "Master intermediate SQL querying techniques including multi-table joins and aggregation alongside foundational Python programming and pandas DataFrame wrangling. Establish disciplined version control workflows using Git and GitHub for project tracking and portfolio publishing.",
    "DA-PH3": "Develop end-to-end data auditing, cleaning, and exploratory data analysis capabilities using Python. Learn to diagnose data quality anomalies, conduct systematic univariate and bivariate analyses, and build communicative charts using matplotlib, seaborn, and clear visual design principles.",
    "DA-PH4": "Advance into complex data analysis by constructing analytical SQL subqueries, CTEs, and window functions alongside dimensional BI data modeling in Power BI or Looker Studio. Master inferential statistical hypothesis testing, A/B experiment evaluation, and core commercial business KPIs.",
    "DA-PH5": "Synthesize analytical competencies into predictive modeling intuition, executive data storytelling, and timed technical interview performance. Learn to fit and interpret regression models, translate quantitative findings into strategic business recommendations, and solve analytics case studies under time pressure."
}

LEARNER_OUTCOMES_DERIVED = {
    "DA-PH1": "The learner can manipulate and summarize spreadsheet datasets with advanced lookups, compute descriptive statistics and probability distributions, and execute baseline SQL queries to extract and filter records.",
    "DA-PH2": "The learner can combine and aggregate multi-table SQL databases, write modular Python scripts to clean and reshape tabular data in pandas, and version-control analytics projects on GitHub.",
    "DA-PH3": "The learner can identify and remediate data quality defects, conduct comprehensive exploratory data analyses on raw datasets, and produce publication-ready statistical visualizations.",
    "DA-PH4": "The learner can write complex analytical SQL with window functions, build interactive dimensional BI dashboards with calculated measures, design and evaluate A/B experiments, and compute business funnel metrics.",
    "DA-PH5": "The learner can interpret regression relationships, deliver compelling data presentations to stakeholders, and successfully solve product analytics cases and timed SQL technical interviews."
}

PHASE_SUMMARY_DERIVED = {
    "DA-PH1": "You have completed foundational training in spreadsheets, descriptive statistics, probability distributions, and basic SQL retrieval. You are now prepared to advance to Phase 2 to master multi-table relational joins, Python scripting, and pandas DataFrame wrangling.",
    "DA-PH2": "You have mastered multi-table SQL joins and aggregations, Python programming fundamentals, pandas DataFrame manipulation, and GitHub version control. Next, you will progress to Phase 3 to clean raw datasets, perform exploratory data analysis, and build your first portfolio project.",
    "DA-PH3": "You have acquired comprehensive skills in data cleaning, exploratory data analysis, chart design principles, and statistical plotting in Python, culminating in your first published portfolio project (DA-P01). You are ready for Phase 4 to construct BI dashboards and design inferential statistical experiments.",
    "DA-PH4": "You have delivered advanced SQL window queries, interactive business dashboards in Power BI or Looker Studio, inferential statistical A/B tests, and core commercial KPIs, validated by your second portfolio project (DA-P02). Proceed to Phase 5 for regression modeling, stakeholder storytelling, and interview preparation.",
    "DA-PH5": "Congratulations! You have completed regression modeling, stakeholder data storytelling, and timed case interview preparation alongside your capstone portfolio project (DA-P03). Your Data Analyst learning journey is complete, and active applications for analyst internships and full-time roles begin now."
}

CHECKPOINT_TYPE_MAP = {
    "DA-PH1": ("QUIZ", 70, ""),
    "DA-PH2": ("TIMED_TEST_PLUS_EXERCISE", 70, ""),
    "DA-PH3": ("PROJECT_RUBRIC", None, "DA-P01"),
    "DA-PH4": ("PROJECT_PLUS_QUIZ", 70, "DA-P02"),
    "DA-PH5": ("PROJECT_PLUS_MOCK_INTERVIEW", None, "DA-P03")
}

KEY_CONCEPTS_BY_MODULE = {
    "DA-M01": "Write relative and absolute cell references; Apply basic spreadsheet formulas; Format numerical and tabular data; Execute workbook calculations",
    "DA-M02": "Sort multi-column tabular data; Filter records using criteria; Configure data validation rules; Restrict invalid user data entry",
    "DA-M03": "Execute VLOOKUP searches across tables; Apply modern XLOOKUP functions; Implement two-way lookups with INDEX-MATCH; Combine data from disparate tables",
    "DA-M04": "Apply conditional aggregation using SUMIFS; Count records conditionally using COUNTIFS; Summarise tabular data across multiple criteria; Build conditional summary reports",
    "DA-M05": "Construct interactive pivot tables; Group data by categorical dimensions; Generate summary pivot charts; Aggregate numerical metrics across categories",
    "DA-M06": "Compute arithmetic mean, median, and mode; Calculate measures of spread including variance and standard deviation; Interpret centre versus dispersion in data; Compare symmetric and skewed distributions",
    "DA-M07": "Describe data distribution shapes; Calculate percentiles and quartiles; Compute and interpret standardized z-scores; Identify relative position within distributions",
    "DA-M08": "Calculate Pearson correlation coefficients; Measure strength of linear associations; Interpret correlation directions; Distinguish correlation from causation",
    "DA-M09": "Apply probability addition and multiplication rules; Compute conditional probabilities; Evaluate independent and dependent events; Calculate probabilities using Bayes' intuition",
    "DA-M10": "Model discrete outcomes with binomial distributions; Work with continuous normal distributions; Calculate probabilities under the standard normal curve; Apply empirical distribution rules",
    "DA-M11": "Retrieve database records with SELECT; Filter table rows using WHERE clauses; Sort query results using ORDER BY; Constrain result sets using LIMIT",
    "DA-M12": "Apply string manipulation functions in SQL; Perform date parsing and date arithmetic; Construct conditional logic with CASE statements; Transform column values dynamically in queries",
    "DA-M13": "Combine tables using INNER JOIN; Execute LEFT and RIGHT outer joins; Implement FULL outer joins; Resolve relational keys and handle null matches",
    "DA-M14": "Aggregate data using GROUP BY clauses; Filter grouped results using HAVING; Compute summary metrics with SUM, AVG, COUNT, MIN, and MAX; Analyze grouped segments",
    "DA-M15": "Write nested scalar and correlated subqueries; Construct Common Table Expressions (CTEs); Break complex multi-step queries into modular blocks; Improve query readability and maintenance",
    "DA-M16": "Compute row rankings using ROW_NUMBER, RANK, and DENSE_RANK; Calculate cumulative running totals with OVER clauses; Retrieve boundary values with LAG and LEAD; Partition window calculations across related row subsets",
    "DA-M17": "Master Python fundamental syntax; Work with core data types (int, float, str, bool); Implement control flow using if-elif-else statements; Construct while and for loops",
    "DA-M18": "Define reusable Python functions; Manage structured data in lists and dictionaries; Apply list and dictionary comprehensions; Organize data structures and business logic modularly",
    "DA-M19": "Read CSV and Excel files into Python; Navigate and execute interactive Jupyter Notebook cells; Inspect tabular data structures in memory; Export processed outputs from Jupyter",
    "DA-M20": "Initialize pandas DataFrames; Select specific columns and row subsets; Filter DataFrame rows using boolean indexing; Sort tabular data by multiple column values",
    "DA-M21": "Aggregate DataFrames using groupby; Merge and join relational DataFrames; Reshape data using pivot and melt; Compute group-level statistical summaries",
    "DA-M22": "Parse and format date-time strings in pandas; Set DatetimeIndex for time-series analysis; Resample time-series data across periods; Calculate rolling and shifting period metrics",
    "DA-M23": "Identify and impute missing values; Detect and eliminate duplicate records; Verify and cast structural column data types; Audit baseline DataFrame integrity",
    "DA-M24": "Clean and standardize text columns with string methods; Identify anomalous values and numerical outliers; Perform rule-based data validation checks; Document data cleaning transformations",
    "DA-M25": "Structure an exploratory data analysis plan; Frame investigative business questions around datasets; Formulate exploration hypotheses; Document systematic exploratory workflows",
    "DA-M26": "Conduct univariate distribution analysis; Analyze bivariate relationships between variables; Identify cross-variable correlations and patterns; Document exploratory findings visually and statistically",
    "DA-M27": "Map analytical questions to optimal chart types; Choose between bar, line, scatter, and histogram representations; Align chart choices with data scales; Avoid deceptive or unsuitable chart formats",
    "DA-M28": "Eliminate visual chart clutter; Apply intentional color palettes for emphasis; Formulate descriptive chart titles, axis labels, and annotations; Ensure visual accessibility and instant readability",
    "DA-M29": "Create basic plots using matplotlib; Customize figure size, titles, labels, and ticks; Plot line charts, scatter plots, and histograms; Save high-resolution figure outputs",
    "DA-M30": "Generate statistical distribution plots in seaborn; Build relational and categorical scatter and box plots; Customize seaborn themes and color palettes; Visualize multi-variable relationships",
    "DA-M31": "Design dimensional star schema data models; Differentiate fact tables from dimension tables; Establish one-to-many dimensional relationships; Optimize schema structures for BI queries",
    "DA-M32": "Connect data sources in Power BI or Looker Studio; Build interactive charts, KPI cards, and slicers; Configure drill-downs and cross-filtering; Publish accessible stakeholder dashboards",
    "DA-M33": "Write basic DAX calculated measures; Differentiate calculated columns from measures; Utilize CALCULATE, SUM, and RELATED functions; Construct measures responsive to dashboard filter context",
    "DA-M34": "Understand sampling distributions and the Central Limit Theorem; Compute standard errors of point estimates; Construct confidence intervals for means and proportions; Interpret margin of error and uncertainty",
    "DA-M35": "Formulate null and alternative hypotheses; Compute test statistics and p-values; Make statistical decisions using significance thresholds; Avoid Type I and Type II statistical errors",
    "DA-M36": "Design randomized controlled A/B experiments; Calculate required sample sizes and statistical power; Evaluate A/B experiment conversion lifts and significance; Formulate data-driven product decisions",
    "DA-M37": "Fit simple and multiple linear regression models; Interpret regression slope coefficients and intercepts; Evaluate model goodness-of-fit using R-squared; Recognize linear regression assumptions and limitations",
    "DA-M38": "Understand logistic regression intuition for binary outcomes; Interpret odds ratios and predicted probabilities; Model yes/no classification decisions; Differentiate linear from logistic modeling contexts",
    "DA-M39": "Define and compute user funnel conversion rates; Measure customer retention across cohorts; Calculate user churn rates; Track core commercial engagement metrics",
    "DA-M40": "Translate analytical findings into actionable recommendations; Structure business narratives around executive decisions; Quantify trade-offs and projected impacts; Align evidence with decision-maker priorities",
    "DA-M41": "Deliver concise, compelling data presentations; Design effective 5-slide executive presentation decks; Communicate complex findings without excessive technical jargon; Field stakeholder questions with data evidence",
    "DA-M42": "Initialize Git repositories and commit analysis history; Create branches and manage merge requests; Push projects to GitHub repositories; Write comprehensive project README documentation",
    "DA-M43": "Structure responses to open-ended metric case questions; Diagnose root causes of metric shifts; Formulate framework-driven product recommendations; Communicate structured business reasoning",
    "DA-M44": "Write accurate SQL queries under timed interview pressure; Solve complex analytical case questions live; Demonstrate problem-solving thought processes to interviewers; Perform effectively under technical interview constraints"
}

# ----------------------------------------------------
# 2. Path Resolution Helper
# ----------------------------------------------------

def resolve_file(filename):
    """Finds input file across candidate local directories."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, filename),
        os.path.join(script_dir, "..", "data", filename),
        os.path.join(script_dir, "data", filename),
        os.path.join(os.getcwd(), filename),
        os.path.join(os.getcwd(), "data", filename),
        os.path.join(os.getcwd(), "da", "data", filename),
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    return filename

# ----------------------------------------------------
# 3. Main Builder Execution
# ----------------------------------------------------

def build():
    print("=" * 80)
    print("Building Data Analyst (DA) Knowledge Base CSVs for eBuddy")
    print("=" * 80)

    excel_file = resolve_file("Data_Analyst_Roadmap.xlsx")
    if not os.path.exists(excel_file):
        raise FileNotFoundError(f"Missing required workbook: {excel_file}")
    print(f"Loading workbook: {excel_file}")

    wb = openpyxl.load_workbook(excel_file, data_only=True)

    # 3.1 Load Sheets
    ws_roles = wb["roles"]
    ws_skills = wb["skills"]
    ws_mods = wb["modules"]
    ws_rt = wb["roadmap_templates"]
    ws_tp = wb["template_phases"]
    ws_proj = wb["projects"]
    ws_res = wb["resources"]
    ws_ms = wb["milestones"]
    ws_lm = wb["learning_methods"]

    # Roles
    role_row = [ws_roles.cell(2, c).value for c in range(1, 5)]
    role_id, role_name, role_desc, role_timeline = role_row

    # Roadmap Templates
    templates_meta = {}
    for r in range(2, ws_rt.max_row + 1):
        vals = [ws_rt.cell(r, c).value for c in range(1, 7)]
        if not any(vals): continue
        tid, rid, speed, weekly, p_sum, r_rule = vals
        templates_meta[tid] = {
            "role_id": rid,
            "speed_months": int(speed),
            "weekly_hours": int(weekly),
            "phases_summary": str(p_sum).strip(),
            "readiness_rule": str(r_rule).strip()
        }

    # Template Phases & Phase Identity Check
    templates_phases_data = {}
    for r in range(2, ws_tp.max_row + 1):
        vals = [ws_tp.cell(r, c).value for c in range(1, 7)]
        if not any(vals): continue
        tid, order, name, share, sids, cp = vals
        templates_phases_data.setdefault(tid, []).append({
            "order": int(order),
            "name": str(name).strip(),
            "share_of_weeks": float(share),
            "skill_ids": str(sids).strip(),
            "checkpoint": str(cp).strip()
        })

    # Assert Phase Identity across DA-12, DA-6, DA-3
    assert "DA-12" in templates_phases_data and "DA-6" in templates_phases_data and "DA-3" in templates_phases_data
    da12_p = [(p["order"], p["name"], p["skill_ids"], p["checkpoint"]) for p in templates_phases_data["DA-12"]]
    da6_p = [(p["order"], p["name"], p["skill_ids"], p["checkpoint"]) for p in templates_phases_data["DA-6"]]
    da3_p = [(p["order"], p["name"], p["skill_ids"], p["checkpoint"]) for p in templates_phases_data["DA-3"]]
    assert da12_p == da6_p, "Phase mismatch between DA-12 and DA-6!"
    assert da12_p == da3_p, "Phase mismatch between DA-12 and DA-3!"
    print("[PASS] Template Phase Identity: DA-12, DA-6, and DA-3 share IDENTICAL phases, skill_ids, and checkpoints.")

    # Assert Readiness Rule Identity across templates
    da12_rr = templates_meta["DA-12"]["readiness_rule"]
    da6_rr = templates_meta["DA-6"]["readiness_rule"]
    da3_rr = templates_meta["DA-3"]["readiness_rule"]
    assert da12_rr == da6_rr == da3_rr, "readiness_rule mismatch across templates!"
    print("[PASS] Readiness Rule Identity: All 3 templates share the exact same readiness_rule text.")

    # Canonical Phases (from DA-12)
    canonical_phases = []
    skill_to_phase = {}
    phase_skills_map = {}
    for p in templates_phases_data["DA-12"]:
        p_order = p["order"]
        p_id = f"DA-PH{p_order}"
        p_name = p["name"]
        sids = [s.strip() for s in p["skill_ids"].split(";")]
        canonical_phases.append({
            "phase_order": p_order,
            "phase_id": p_id,
            "phase_name": p_name,
            "share_of_weeks": p["share_of_weeks"],
            "skill_ids": sids,
            "skill_ids_raw": p["skill_ids"],
            "checkpoint": p["checkpoint"]
        })
        phase_skills_map[p_id] = sids
        for idx, sid in enumerate(sids):
            assert sid not in skill_to_phase, f"Skill {sid} belongs to multiple phases!"
            skill_to_phase[sid] = (p_order, p_id, p_name, idx)

    # Skills Sheet
    skills_catalog = {}
    for r in range(2, ws_skills.max_row + 1):
        vals = [ws_skills.cell(r, c).value for c in range(1, 7)]
        if not any(vals): continue
        sid, sname, cat, desc, lvl, prereqs = vals
        prereq_list = [p.strip() for p in str(prereqs).split(";") if p and str(p).strip() != ""] if prereqs else []
        skills_catalog[str(sid).strip()] = {
            "name": str(sname).strip(),
            "category": str(cat).strip(),
            "description": str(desc).strip(),
            "level": str(lvl).strip(),
            "prerequisite_ids_raw": str(prereqs).strip() if prereqs else "",
            "prerequisites": prereq_list
        }

    assert len(skills_catalog) == 20, f"Expected 20 skills, got {len(skills_catalog)}"
    assert len(skill_to_phase) == 20, f"Expected 20 mapped skills, got {len(skill_to_phase)}"
    print("[PASS] Skill Partitioning: Every one of the 20 skills belongs to exactly one canonical phase.")

    # Resources Sheet
    resources_list = []
    skill_to_resources = {sid: [] for sid in skills_catalog}
    res_by_url = {}
    for r in range(2, ws_res.max_row + 1):
        vals = [ws_res.cell(r, c).value for c in range(1, 8)]
        if not any(vals): continue
        rid, rtitle, rurl, rprov, rtype, rsids, rfree = vals
        rid_str = str(rid).strip()
        rurl_str = str(rurl).strip()
        rtype_str = str(rtype).strip()
        free_str = "TRUE" if str(rfree).strip().upper() == "TRUE" else "FALSE"
        
        # resource role
        rrole = "DATASET" if rtype_str.startswith("Dataset") else "LEARNING"
        
        res_obj = {
            "resource_id": rid_str,
            "resource_title": str(rtitle).strip(),
            "resource_url": rurl_str,
            "resource_provider": str(rprov).strip(),
            "resource_type": rtype_str,
            "skill_ids": [s.strip() for s in str(rsids).split(";")],
            "is_free": free_str,
            "resource_role": rrole
        }
        resources_list.append(res_obj)
        res_by_url[rurl_str] = rid_str
        for sid in res_obj["skill_ids"]:
            if sid in skill_to_resources:
                skill_to_resources[sid].append(res_obj)

    # Modules Sheet
    modules_list = []
    for r in range(2, ws_mods.max_row + 1):
        vals = [ws_mods.cell(r, c).value for c in range(1, 7)]
        if not any(vals): continue
        mid, sid, morder, mtitle, mobj, mhours = vals
        modules_list.append({
            "module_id": str(mid).strip(),
            "skill_id": str(sid).strip(),
            "module_order": int(morder),
            "module_title": str(mtitle).strip(),
            "objective": str(mobj).strip(),
            "est_hours": int(mhours)
        })
    assert len(modules_list) == 44, f"Expected 44 modules, got {len(modules_list)}"

    # Sort modules: by phase_order, skill position within phase, module_order
    def module_sort_key(m):
        p_order, p_id, p_name, s_pos = skill_to_phase[m["skill_id"]]
        return (p_order, s_pos, m["module_order"], m["module_id"])

    sorted_modules = sorted(modules_list, key=module_sort_key)

    # Modules per skill map and hours
    skill_modules_map = {sid: [] for sid in skills_catalog}
    skill_hours_map = {sid: 0 for sid in skills_catalog}
    for m in sorted_modules:
        skill_modules_map[m["skill_id"]].append(m)
        skill_hours_map[m["skill_id"]] += m["est_hours"]

    # ----------------------------------------------------
    # FILE 1: 01_da_roadmap_overview.csv
    # ----------------------------------------------------
    file1_rows = []
    for idx, cp in enumerate(canonical_phases):
        p_order = cp["phase_order"]
        p_id = cp["phase_id"]
        p_name = cp["phase_name"]
        skills_in_phase = [skills_catalog[sid]["name"] for sid in cp["skill_ids"]]
        next_pid = f"DA-PH{p_order + 1}" if p_order < 5 else "END"

        file1_rows.append({
            "phase_order": p_order,
            "phase_id": p_id,
            "phase_name": p_name,
            "skills_in_order": " | ".join(skills_in_phase),
            "number_of_skills": len(skills_in_phase),
            "phase_objective_derived": PHASE_OBJECTIVES_DERIVED[p_id],
            "learner_outcome_derived": LEARNER_OUTCOMES_DERIVED[p_id],
            "next_phase_id": next_pid
        })

    # ----------------------------------------------------
    # FILE 2: 02_phase_modules_resources.csv
    # ----------------------------------------------------
    file2_rows = []
    expected_f2_rows = 0
    for m in sorted_modules:
        sid = m["skill_id"]
        res_list = skill_to_resources[sid]
        expected_f2_rows += max(1, len(res_list))

        p_order, p_id, p_name, s_pos = skill_to_phase[sid]
        sk_info = skills_catalog[sid]
        key_concepts = KEY_CONCEPTS_BY_MODULE.get(m["module_id"], "")

        if len(res_list) == 0:
            file2_rows.append({
                "phase_order": p_order,
                "phase_id": p_id,
                "phase_name": p_name,
                "skill_id": sid,
                "skill_name": sk_info["name"],
                "skill_category": sk_info["category"],
                "skill_level": sk_info["level"],
                "module_id": m["module_id"],
                "module_order": m["module_order"],
                "module_title": m["module_title"],
                "what_to_learn_objective": m["objective"],
                "module_est_hours": m["est_hours"],
                "skill_description": sk_info["description"],
                "key_concepts_and_skills_derived": key_concepts,
                "resource_id": "NO_RESOURCE_IN_SOURCE",
                "resource_title": "",
                "resource_type": "",
                "resource_provider": "",
                "resource_url": "",
                "is_free": "",
                "resource_role": "",
                "resource_scope": "skill-level; source does not map resources to individual modules",
                "data_quality_note": "No resource listed in source for this skill"
            })
        else:
            sorted_res = sorted(res_list, key=lambda r: r["resource_id"])
            for res in sorted_res:
                file2_rows.append({
                    "phase_order": p_order,
                    "phase_id": p_id,
                    "phase_name": p_name,
                    "skill_id": sid,
                    "skill_name": sk_info["name"],
                    "skill_category": sk_info["category"],
                    "skill_level": sk_info["level"],
                    "module_id": m["module_id"],
                    "module_order": m["module_order"],
                    "module_title": m["module_title"],
                    "what_to_learn_objective": m["objective"],
                    "module_est_hours": m["est_hours"],
                    "skill_description": sk_info["description"],
                    "key_concepts_and_skills_derived": key_concepts,
                    "resource_id": res["resource_id"],
                    "resource_title": res["resource_title"],
                    "resource_type": res["resource_type"],
                    "resource_provider": res["resource_provider"],
                    "resource_url": res["resource_url"],
                    "is_free": res["is_free"],
                    "resource_role": res["resource_role"],
                    "resource_scope": "skill-level; source does not map resources to individual modules",
                    "data_quality_note": ""
                })

    # ----------------------------------------------------
    # FILE 3: 03_skills_catalog.csv
    # ----------------------------------------------------
    file3_rows = []
    # Preserve exact order of skills sheet
    for r in range(2, ws_skills.max_row + 1):
        vals = [ws_skills.cell(r, c).value for c in range(1, 7)]
        if not any(vals): continue
        sid = str(vals[0]).strip()
        sk = skills_catalog[sid]
        p_order, p_id, p_name, s_pos = skill_to_phase[sid]
        
        prereq_names = [skills_catalog[p]["name"] for p in sk["prerequisites"]]
        
        notes = []
        for p in sk["prerequisites"]:
            p_prereq_order, p_prereq_id, _, p_pos = skill_to_phase[p]
            if p_prereq_order > p_order:
                notes.append(f"Prerequisite skill is in a LATER phase ({p_prereq_id})")
            elif p_prereq_order == p_order and p_pos > s_pos:
                notes.append("Prerequisite is in the same phase but later in order")

        file3_rows.append({
            "skill_id": sid,
            "skill_name": sk["name"],
            "category": sk["category"],
            "description": sk["description"],
            "level": sk["level"],
            "prerequisite_skill_ids": sk["prerequisite_ids_raw"],
            "prerequisite_skill_names": " | ".join(prereq_names),
            "phase_id": p_id,
            "phase_order": p_order,
            "number_of_modules": len(skill_modules_map[sid]),
            "total_module_hours": skill_hours_map[sid],
            "number_of_resources": len(skill_to_resources[sid]),
            "data_quality_note": "; ".join(notes)
        })

    # ----------------------------------------------------
    # FILE 4: 04_phase_summary_readiness_checkpoints.csv
    # ----------------------------------------------------
    # Milestones mapping
    milestones_by_phase = {i: [] for i in range(1, 6)}
    for r in range(2, ws_ms.max_row + 1):
        vals = [ws_ms.cell(r, c).value for c in range(1, 6)]
        if not any(vals): continue
        mid, m_role, m_name, m_timing, m_dep = vals
        timing_str = str(m_timing).strip()
        # Parse phase number from timing
        m_phase = re.search(r"phase\s+(\d+)", timing_str, re.IGNORECASE)
        if m_phase:
            target_phase_num = int(m_phase.group(1))
            milestones_by_phase[target_phase_num].append(f"{str(m_name).strip()} ({timing_str})")

    file4_rows = []
    for cp in canonical_phases:
        p_order = cp["phase_order"]
        p_id = cp["phase_id"]
        p_name = cp["phase_name"]
        
        skills_names = [skills_catalog[sid]["name"] for sid in cp["skill_ids"]]
        tot_phase_hours = sum(skill_hours_map[sid] for sid in cp["skill_ids"])
        
        cp_type, pass_pct, proj_id = CHECKPOINT_TYPE_MAP[p_id]
        
        # Readiness rule for phase derived
        core_adv_skills = [skills_catalog[sid]["name"] for sid in cp["skill_ids"] if skills_catalog[sid]["level"] in ["core", "advanced"]]
        if len(core_adv_skills) > 0:
            rule_derived = f"Mastery probability of at least 0.85 on: {', '.join(core_adv_skills)}; {cp['checkpoint']}"
        else:
            rule_derived = f"No mastery threshold is stated for foundation skills in the source; the phase checkpoint is the readiness test; {cp['checkpoint']}"
        
        if p_order == 5:
            rule_derived += "; Overall final readiness: timed SQL test of at least 70%, all projects passing rubrics, mock interview passed"

        file4_rows.append({
            "phase_order": p_order,
            "phase_id": p_id,
            "phase_name": p_name,
            "share_of_weeks": cp["share_of_weeks"],
            "skill_ids": cp["skill_ids_raw"],
            "skill_names": " | ".join(skills_names),
            "total_module_hours": tot_phase_hours,
            "checkpoint_text": cp["checkpoint"],
            "checkpoint_type_derived": cp_type,
            "checkpoint_pass_threshold_pct": str(pass_pct) if pass_pct is not None else "",
            "checkpoint_project_ids": proj_id,
            "milestones_reached": " | ".join(milestones_by_phase[p_order]),
            "phase_summary_after_completion_derived": PHASE_SUMMARY_DERIVED[p_id],
            "readiness_rule_for_phase_derived": rule_derived,
            "overall_readiness_rule_ref": da12_rr
        })

    # ----------------------------------------------------
    # FILE 5: 05_projects.csv & FILE 6: 06_project_rubric_items.csv
    # ----------------------------------------------------
    file5_rows = []
    file6_rows = []
    
    # Phase checkpoints text map for linking
    cp_by_project = {
        "DA-P01": templates_phases_data["DA-12"][2]["checkpoint"],
        "DA-P02": templates_phases_data["DA-12"][3]["checkpoint"],
        "DA-P03": templates_phases_data["DA-12"][4]["checkpoint"]
    }

    diff_order_map = {"beginner": 1, "intermediate": 2, "advanced": 3}

    for r in range(2, ws_proj.max_row + 1):
        vals = [ws_proj.cell(r, c).value for c in range(1, 11)]
        if not any(vals): continue
        pid, ptitle, pbrief, psids, pdurl, pdlic, pdeliv, pdiff, phours, prubric = vals
        pid_str = str(pid).strip()
        pdurl_str = str(pdurl).strip()
        pdiff_str = str(pdiff).strip()
        
        proj_sids = [s.strip() for s in str(psids).split(";")]
        for sid in proj_sids:
            assert sid in skills_catalog, f"Project skill {sid} not in skills!"
            
        proj_snames = [skills_catalog[sid]["name"] for sid in proj_sids]
        
        # Skill phase map & latest phase
        sp_map_entries = []
        max_p_order = 1
        latest_pid = "DA-PH1"
        for sid in proj_sids:
            po, pi, pn, _ = skill_to_phase[sid]
            sp_map_entries.append(f"{sid}:{pi}")
            if po > max_p_order:
                max_p_order = po
                latest_pid = pi
        skill_phase_map_str = "; ".join(sp_map_entries)

        # Rubric criteria
        criteria_list = [c.strip() for c in str(prubric).split(";") if c and str(c).strip() != ""]
        num_criteria = len(criteria_list)
        
        # Matched dataset resource id
        matched_res_id = res_by_url.get(pdurl_str, "")

        file5_rows.append({
            "project_id": pid_str,
            "title": str(ptitle).strip(),
            "brief": str(pbrief).strip(),
            "difficulty": pdiff_str,
            "est_hours": int(phours),
            "deliverable": str(pdeliv).strip(),
            "rubric": str(prubric).strip(),
            "number_of_rubric_criteria": num_criteria,
            "dataset_url": pdurl_str,
            "dataset_licence": str(pdlic).strip(),
            "dataset_resource_id": matched_res_id,
            "skill_ids": str(psids).strip(),
            "skill_names": " | ".join(proj_snames),
            "skill_phase_map": skill_phase_map_str,
            "recommended_after_phase_id": latest_pid,
            "linked_phase_checkpoint": cp_by_project.get(pid_str, ""),
            "data_quality_note": "",
            "recommendation_order": diff_order_map.get(pdiff_str.lower(), 99)
        })

        for c_idx, crit in enumerate(criteria_list, 1):
            file6_rows.append({
                "project_id": pid_str,
                "criterion_number": c_idx,
                "criterion_text": crit,
                "recommended_after_phase_id": latest_pid
            })

    # Sort file5 by recommendation_order
    file5_rows = sorted(file5_rows, key=lambda x: x["recommendation_order"])

    # ----------------------------------------------------
    # FILE 7: 07_pacing_templates.csv
    # ----------------------------------------------------
    file7_rows = []
    # Loop over templates in order DA-12, DA-6, DA-3
    for tid in ["DA-12", "DA-6", "DA-3"]:
        t_meta = templates_meta[tid]
        t_phases = templates_phases_data[tid]
        for p in t_phases:
            p_order = p["order"]
            p_id = f"DA-PH{p_order}"
            share = p["share_of_weeks"]
            approx_weeks = round(float(share) * float(t_meta["speed_months"]) * 52.0 / 12.0, 1)
            approx_hours = int(round(approx_weeks * float(t_meta["weekly_hours"])))

            file7_rows.append({
                "template_id": tid,
                "speed_months": t_meta["speed_months"],
                "weekly_hours": t_meta["weekly_hours"],
                "phases_summary": t_meta["phases_summary"],
                "phase_order": p_order,
                "phase_id": p_id,
                "phase_name": p["name"],
                "share_of_weeks": share,
                "approx_weeks_derived": approx_weeks,
                "approx_hours_derived": approx_hours,
                "overall_readiness_rule": t_meta["readiness_rule"],
                "role_typical_timeline": role_timeline
            })

    # ----------------------------------------------------
    # FILE 8: 08_milestones.csv
    # ----------------------------------------------------
    file8_rows = []
    for r in range(2, ws_ms.max_row + 1):
        vals = [ws_ms.cell(r, c).value for c in range(1, 6)]
        if not any(vals): continue
        mid, m_role, m_name, m_timing, m_dep = vals
        timing_str = str(m_timing).strip()
        
        m_phase = re.search(r"phase\s+(\d+)", timing_str, re.IGNORECASE)
        p_num = int(m_phase.group(1)) if m_phase else 1
        mapped_pid = f"DA-PH{p_num}"

        if "from mid" in timing_str.lower():
            pos = "FROM_MID_PHASE"
        elif "mid" in timing_str.lower():
            pos = "MID_PHASE"
        else:
            pos = "END_OF_PHASE"

        file8_rows.append({
            "milestone_id": str(mid).strip(),
            "name": str(m_name).strip(),
            "typical_timing": timing_str,
            "depends_on": str(m_dep).strip() if m_dep else "",
            "mapped_phase_id": mapped_pid,
            "timing_position": pos
        })

    # ----------------------------------------------------
    # FILE 9: 09_learning_methods.csv
    # ----------------------------------------------------
    file9_rows = []
    for r in range(2, ws_lm.max_row + 1):
        vals = [ws_lm.cell(r, c).value for c in range(1, 5)]
        if not any(vals): continue
        lid, lname, lwhen, lhow = vals
        file9_rows.append({
            "method_id": str(lid).strip(),
            "name": str(lname).strip(),
            "when_to_use": str(lwhen).strip(),
            "how": str(lhow).strip()
        })

    # ----------------------------------------------------
    # 4. Writing Output CSV Files (BOM utf-8-sig)
    # ----------------------------------------------------
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate_dirs = []
    if os.path.basename(script_dir) == "scripts":
        pkg_root = os.path.dirname(script_dir)
        repo_root = os.path.dirname(pkg_root)
        candidate_dirs.extend([
            os.path.join(pkg_root, "output"),
            os.path.join(repo_root, "output")
        ])
    else:
        candidate_dirs.extend([
            os.path.join(script_dir, "output"),
            os.path.join(script_dir, "da", "output")
        ])

    candidate_dirs.extend([
        os.path.join(os.getcwd(), "output"),
        os.path.join(os.getcwd(), "da", "output")
    ])

    # Deduplicate and filter out any invalid paths
    unique_out_dirs = []
    for d in candidate_dirs:
        norm_d = os.path.abspath(d)
        if "scripts" in os.path.basename(norm_d) or norm_d.endswith(os.path.join("scripts", "output")):
            continue
        if norm_d not in unique_out_dirs:
            unique_out_dirs.append(norm_d)

    for out_d in unique_out_dirs:
        os.makedirs(out_d, exist_ok=True)

        datasets = [
            ("01_da_roadmap_overview.csv", file1_rows),
            ("02_phase_modules_resources.csv", file2_rows),
            ("03_skills_catalog.csv", file3_rows),
            ("04_phase_summary_readiness_checkpoints.csv", file4_rows),
            ("05_projects.csv", file5_rows),
            ("06_project_rubric_items.csv", file6_rows),
            ("07_pacing_templates.csv", file7_rows),
            ("08_milestones.csv", file8_rows),
            ("09_learning_methods.csv", file9_rows)
        ]

        for fname, rows in datasets:
            fpath = os.path.join(out_d, fname)
            with open(fpath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                writer.writerows(rows)

    print("[SUCCESS] All 9 Data Analyst CSV knowledge base files written successfully.")

    # ----------------------------------------------------
    # 5. Validation Assertions & Verification Checks
    # ----------------------------------------------------
    print("\n" + "=" * 80)
    print("RUNNING VALIDATION ASSERTIONS")
    print("=" * 80)

    # 5.1 Row count assertions
    assert len(file1_rows) == 5, f"Expected 5 rows in 01, got {len(file1_rows)}"
    assert len(file3_rows) == 20, f"Expected 20 rows in 03, got {len(file3_rows)}"
    assert len(file4_rows) == 5, f"Expected 5 rows in 04, got {len(file4_rows)}"
    assert len(file5_rows) == 3, f"Expected 3 rows in 05, got {len(file5_rows)}"
    assert len(file6_rows) == sum(p["number_of_rubric_criteria"] for p in file5_rows), "06 rows != sum of criteria!"
    assert len(file7_rows) == 15, f"Expected 15 rows in 07, got {len(file7_rows)}"
    assert len(file8_rows) == 6, f"Expected 6 rows in 08, got {len(file8_rows)}"
    assert len(file9_rows) == 6, f"Expected 6 rows in 09, got {len(file9_rows)}"
    print("[PASS] Fixed Row Counts Verified: 01 (5), 03 (20), 04 (5), 05 (3), 06 (12), 07 (15), 08 (6), 09 (6).")

    # 5.2 02_phase_modules_resources checks
    assert len(file2_rows) == expected_f2_rows, f"Expected {expected_f2_rows} rows in 02, got {len(file2_rows)}"
    f2_mids = set(r["module_id"] for r in file2_rows)
    assert len(f2_mids) == 44, f"Expected 44 distinct modules in 02, got {len(f2_mids)}"
    for r in file2_rows:
        assert r["key_concepts_and_skills_derived"], f"Missing key concepts in module {r['module_id']}"
    print(f"[PASS] File 02 Verified: Exactly {len(file2_rows)} rows matching expected count ({expected_f2_rows}), covering all 44 modules.")

    # 5.3 Skills with no resource report
    skills_without_resources = [sid for sid in skills_catalog if len(skill_to_resources[sid]) == 0]
    print(f"\n[Skills with NO Resource in Source]: {len(skills_without_resources)} skills found")
    for sid in skills_without_resources:
        print(f"  • {sid}: {skills_catalog[sid]['name']} (Category: {skills_catalog[sid]['category']})")

    # 5.4 Dataset resources with projects report
    print("\n[Dataset Resources & Linked Projects]:")
    for p in file5_rows:
        print(f"  • Project {p['project_id']} ({p['title']}) -> Resource {p['dataset_resource_id']} | URL: {p['dataset_url']} | Licence: {p['dataset_licence']}")

    # 5.5 Estimated hours comparison
    total_mod_hours = sum(m["est_hours"] for m in modules_list)
    total_proj_hours = sum(p["est_hours"] for p in file5_rows)
    print("\n[Estimated Hours Comparison Report]:")
    print(f"  • Total Modules Estimated Hours : {total_mod_hours} hours")
    print(f"  • Total Projects Estimated Hours: {total_proj_hours} hours")
    print(f"  • Combined Curriculum Hours     : {total_mod_hours + total_proj_hours} hours")
    print(f"  • Role Typical Timeline Text    : \"{role_timeline}\"")

    # 5.6 Exact cell preservation verification against source
    # Check skills sheet
    for r in range(2, ws_skills.max_row + 1):
        vals = [ws_skills.cell(r, c).value for c in range(1, 7)]
        if not any(vals): continue
        sid = str(vals[0]).strip()
        sk = skills_catalog[sid]
        assert sk["name"] == str(vals[1]).strip()
        assert sk["category"] == str(vals[2]).strip()
        assert sk["description"] == str(vals[3]).strip()
        assert sk["level"] == str(vals[4]).strip()
        if vals[5]:
            assert sk["prerequisite_ids_raw"] == str(vals[5]).strip()

    # Check modules sheet
    for r in range(2, ws_mods.max_row + 1):
        vals = [ws_mods.cell(r, c).value for c in range(1, 7)]
        if not any(vals): continue
        mid = str(vals[0]).strip()
        matching_m = [m for m in modules_list if m["module_id"] == mid][0]
        assert matching_m["skill_id"] == str(vals[1]).strip()
        assert matching_m["module_order"] == int(vals[2])
        assert matching_m["module_title"] == str(vals[3]).strip()
        assert matching_m["objective"] == str(vals[4]).strip()
        assert matching_m["est_hours"] == int(vals[5])

    # Check projects sheet
    for r in range(2, ws_proj.max_row + 1):
        vals = [ws_proj.cell(r, c).value for c in range(1, 11)]
        if not any(vals): continue
        pid = str(vals[0]).strip()
        matching_p = [p for p in file5_rows if p["project_id"] == pid][0]
        assert matching_p["title"] == str(vals[1]).strip()
        assert matching_p["brief"] == str(vals[2]).strip()
        assert matching_p["skill_ids"] == str(vals[3]).strip()
        assert matching_p["dataset_url"] == str(vals[4]).strip()
        assert matching_p["dataset_licence"] == str(vals[5]).strip()
        assert matching_p["deliverable"] == str(vals[6]).strip()
        assert matching_p["difficulty"] == str(vals[7]).strip()
        assert matching_p["est_hours"] == int(vals[8])
        assert matching_p["rubric"] == str(vals[9]).strip()

    print("[PASS] Exact Cell Preservation: All source columns strictly match original Excel cell values.")
    print("ALL VALIDATION ASSERTIONS PASSED (100% compliant)!")

    # ----------------------------------------------------
    # 6. Print First 3 Rows of Each CSV
    # ----------------------------------------------------
    print("\n" + "=" * 80)
    print("PREVIEW: FIRST 3 ROWS OF EACH CSV FILE")
    print("=" * 80)

    for fname, rows in datasets:
        print("\n" + "-" * 70)
        print(f"FILE: {fname} (Total Rows: {len(rows)})")
        print("-" * 70)
        fieldnames = list(rows[0].keys())
        print("HEADER: " + ", ".join(fieldnames))
        for i, row in enumerate(rows[:3], 1):
            vals_str = [str(row[k]) for k in fieldnames]
            print(f"ROW {i} : " + " | ".join(vals_str[:8]))
            if len(vals_str) > 8:
                print(f"       + {len(vals_str) - 8} more columns: " + " | ".join(vals_str[8:14]))

if __name__ == "__main__":
    build()
