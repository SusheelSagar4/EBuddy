import os
import re
import csv
import openpyxl

# ----------------------------------------------------
# Configuration & Metadata
# ----------------------------------------------------
def resolve_file(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for p in [
        os.path.join(script_dir, '..', 'data', filename),
        os.path.join(script_dir, 'data', filename),
        os.path.join(os.getcwd(), 'aiml', 'data', filename),
        os.path.join(os.getcwd(), 'data', filename),
        os.path.join(os.getcwd(), filename),
        os.path.join(script_dir, filename)
    ]:
        if os.path.exists(p):
            return os.path.abspath(p)
    return filename

EXCEL_FILE = resolve_file("AI_ML_Learning_Roadmap_KnowledgeBase-v2.xlsx")
SHEET_NAME = "AI_ML_Learning_Roadmap"
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output"))

PHASE_ORDER = [
    "0_Foundations",
    "1_Classical_ML",
    "2_Deep_Learning",
    "3_Projects",
    "4_Specialization",
    "5_Research"
]

PHASE_METADATA = {
    "0_Foundations": {
        "phase_order": 1,
        "phase_name": "Foundations",
        "phase_objective": "Build essential mathematical and computational foundations covering Python programming, data manipulation, developer environments, linear algebra, multivariable calculus, and probability.",
        "learner_outcome": "The learner can write idiomatic Python, manipulate tabular arrays and datasets, navigate collaborative developer tools, and apply multivariable calculus, linear algebra, and probability to computational modeling.",
        "recommended_next_phase": "1_Classical_ML"
    },
    "1_Classical_ML": {
        "phase_order": 2,
        "phase_name": "Classical Machine Learning",
        "phase_objective": "Master classical supervised and unsupervised machine learning algorithms, ensemble architectures, mathematical learning theory, and production-ready Scikit-Learn pipelines.",
        "learner_outcome": "The learner can develop, evaluate, and tune classical machine learning models including regressions, decision trees, boosting ensembles, and clustering algorithms on real-world datasets.",
        "recommended_next_phase": "2_Deep_Learning"
    },
    "2_Deep_Learning": {
        "phase_order": 3,
        "phase_name": "Deep Learning",
        "phase_objective": "Understand deep neural network mechanics, backpropagation calculus, and architectural paradigms while building vision models and transformers from scratch and using PyTorch.",
        "learner_outcome": "The learner can train, evaluate, and debug deep convolutional networks, recurrent architectures, and foundational transformer models using PyTorch and custom autograd engines.",
        "recommended_next_phase": "3_Projects"
    },
    "3_Projects": {
        "phase_order": 4,
        "phase_name": "Projects & Applied Benchmarks",
        "phase_objective": "Execute end-to-end machine learning and computer vision projects on benchmark datasets while integrating disciplined experiment tracking and MLOps tooling.",
        "learner_outcome": "The learner can build end-to-end benchmarked ML/CV pipelines, compare results against state-of-the-art baselines, and manage experiment artifacts using Weights & Biases.",
        "recommended_next_phase": "4_Specialization"
    },
    "4_Specialization": {
        "phase_order": 5,
        "phase_name": "Specialization: NLP, GenAI, RL & MLOps",
        "phase_objective": "Acquire advanced specialization across natural language processing, LLM pretraining and fine-tuning (PEFT/LoRA), generative AI agents, deep reinforcement learning, and production engineering.",
        "learner_outcome": "The learner can pretrain and parameter-efficiently fine-tune large language models, construct agentic RAG workflows, implement reinforcement learning agents, and deploy containerized ML systems with FastAPI and Docker.",
        "recommended_next_phase": "5_Research"
    },
    "5_Research": {
        "phase_order": 6,
        "phase_name": "Research & Advanced Frontiers",
        "phase_objective": "Engage with top-tier peer-reviewed AI conference literature, track daily preprint breakthroughs, study deep technical blogs, and prepare for high-level technical interviews and research roles.",
        "learner_outcome": "The learner can critically evaluate state-of-the-art AI research publications, synthesize frontier developments in foundation models, and formulate answers to advanced machine learning system design questions.",
        "recommended_next_phase": "END"
    }
}

RESOURCE_FORMAT_GROUP_MAP = {
    # Video
    "Video Lecture": "Video",
    "Video Summaries": "Video",
    "Video + Taxonomy Guide": "Video",

    # Video Series
    "Video Series": "Video Series",
    "Video Series + Code": "Video Series",
    "Video Series + Notes": "Video Series",
    "Video + Code": "Video Series",

    # Course
    "Specialization": "Course",
    "Short Courses": "Course",
    "University Lectures": "Course",
    "Course + GitHub": "Course",
    "Course + Notebooks": "Course",
    "Web Course + Study Notes": "Course",

    # Documentation
    "Tutorial & Docs": "Documentation",
    "Docs + Code": "Documentation",
    "Docs + Notebooks": "Documentation",

    # Book
    "Textbook + GitHub": "Book",
    "Book + Video Series + Code": "Book",

    # Interactive
    "Interactive Course": "Interactive",
    "Interactive Roadmap": "Interactive",
    "Interactive Web + Video": "Interactive",
    "Interactive Docs": "Interactive",
    "Interactive Essays": "Interactive",

    # College Course
    "College Course": "College Course",

    # Project/Dataset
    "Datasets & Notebooks": "Project/Dataset",
    "Guided Projects": "Project/Dataset",
    "Benchmark Hub": "Project/Dataset",

    # Reading/Blog/Papers
    "Conference Papers": "Reading/Blog/Papers",
    "Technical Articles": "Reading/Blog/Papers",
    "Research Feed": "Reading/Blog/Papers",

    # Curated List
    "Curated Directory": "Curated List",
    "Course Review / Guide": "Curated List",
    "GitHub Study Guide": "Curated List",

    # Other
    "Platform / Tooling": "Other",
}

HIGH_SCHOOL_MATH_TOPICS = [
    {
        "topic": "Sets, Relations and Functions",
        "detail": "Class 11 - Sets, Relations and Functions: sets, relations, functions, domain/range"
    },
    {
        "topic": "Trigonometric Functions",
        "detail": "Class 11 - Trigonometric Functions: identities, graphs, radian measure"
    },
    {
        "topic": "Sequences and Series",
        "detail": "Class 11 - Sequences and Series: AP, GP"
    },
    {
        "topic": "Straight Lines and Conic Sections",
        "detail": "Class 11 - Straight Lines and Conic Sections: coordinate geometry, equations of lines, circles, parabola, ellipse, hyperbola"
    },
    {
        "topic": "Introduction to 3D Geometry",
        "detail": "Class 11 - Introduction to 3D Geometry: points and distance in 3D"
    },
    {
        "topic": "Limits and Derivatives",
        "detail": "Class 11 - Limits and Derivatives: basic limits, derivative rules"
    },
    {
        "topic": "Permutations and Combinations; Binomial Theorem",
        "detail": "Class 11 - Permutations and Combinations; Binomial Theorem"
    },
    {
        "topic": "Statistics",
        "detail": "Class 11 - Statistics: mean, variance, standard deviation"
    },
    {
        "topic": "Probability",
        "detail": "Class 11 - Probability: sample space, events, basic probability"
    },
    {
        "topic": "Relations and Functions; Inverse Trigonometric Functions",
        "detail": "Class 12 - Relations and Functions; Inverse Trigonometric Functions"
    },
    {
        "topic": "Matrices and Determinants",
        "detail": "Class 12 - Matrices and Determinants: operations, inverse, determinant (needed for linear algebra)"
    },
    {
        "topic": "Continuity and Differentiability; Application of Derivatives",
        "detail": "Class 12 - Continuity and Differentiability; Application of Derivatives (maxima/minima, needed for gradient descent)"
    },
    {
        "topic": "Integrals and Application of Integrals",
        "detail": "Class 12 - Integrals and Application of Integrals"
    },
    {
        "topic": "Differential Equations (basic)",
        "detail": "Class 12 - Differential Equations (basic)"
    },
    {
        "topic": "Vector Algebra and Three Dimensional Geometry",
        "detail": "Class 12 - Vector Algebra and Three Dimensional Geometry: dot/cross product, planes, lines in 3D"
    },
    {
        "topic": "Probability",
        "detail": "Class 12 - Probability: conditional probability, Bayes' theorem, random variables, distributions"
    },
]

def build():
    print("=" * 70)
    print("Building Knowledge Base CSVs for eBuddy")
    print("=" * 70)
    
    # Print resource format group mapping as required
    print("\n[Resource Format Group Mapping]")
    for src_type, target_group in sorted(RESOURCE_FORMAT_GROUP_MAP.items()):
        print(f"  {src_type:<30} -> {target_group}")
    print()

    # Load Excel
    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=False)
    if SHEET_NAME not in wb.sheetnames:
        raise ValueError(f"Sheet '{SHEET_NAME}' not found in {EXCEL_FILE}. Found: {wb.sheetnames}")
    ws = wb[SHEET_NAME]

    expected_headers = [
        "Resource ID", "Milestone Stage", "Domain / Sub-Track", "Resource Title",
        "Platform / Author", "Resource Type", "Learning Style", "Cost Model",
        "Est. Hours", "Prerequisites", "Key Concepts & Skills Covered",
        "Direct URL / Access Reference"
    ]
    actual_headers = [str(c.value).strip() if c.value is not None else "" for c in ws[6][:12]]
    if actual_headers != expected_headers:
        raise ValueError(f"Header mismatch!\nExpected: {expected_headers}\nActual:   {actual_headers}")

    raw_resources = []
    excel_total_hours = 0
    row_idx = 6

    for row in ws.iter_rows(min_row=7, max_row=ws.max_row, values_only=False):
        row_idx += 1
        vals = [c.value for c in row[:12]]
        # Skip completely blank rows
        if all(v is None or str(v).strip() == "" for v in vals):
            continue

        rid = str(vals[0]).strip()
        phase_id = str(vals[1]).strip()
        domain = str(vals[2]).strip()
        title = str(vals[3]).strip()
        platform = str(vals[4]).strip()
        rtype = str(vals[5]).strip()
        lstyle = str(vals[6]).strip()
        cmodel = str(vals[7]).strip()
        hours = int(vals[8])
        prereqs = str(vals[9]).strip() if vals[9] is not None else "None"
        key_concepts = str(vals[10]).strip()
        url = str(vals[11]).strip()

        excel_total_hours += hours

        if phase_id not in PHASE_METADATA:
            raise ValueError(f"Unexpected phase_id: {phase_id} at row {row_idx}")
        if rtype not in RESOURCE_FORMAT_GROUP_MAP:
            raise ValueError(f"Unmapped resource_type: '{rtype}' at row {row_idx}")

        raw_resources.append({
            "excel_row": row_idx,
            "resource_id": rid,
            "phase_id": phase_id,
            "phase_order": PHASE_METADATA[phase_id]["phase_order"],
            "domain_sub_track": domain,
            "resource_title": title,
            "platform_author": platform,
            "resource_type": rtype,
            "resource_format_group": RESOURCE_FORMAT_GROUP_MAP[rtype],
            "learning_style": lstyle,
            "cost_model": cmodel,
            "estimated_hours": hours,
            "prerequisites_raw": prereqs,
            "key_concepts_and_skills": key_concepts,
            "url_or_access_reference": url
        })

    # Sort raw_resources by phase_order, then excel_row
    resources_sorted = sorted(raw_resources, key=lambda x: (x["phase_order"], x["excel_row"]))

    # Index resources by ID
    resource_by_id = {r["resource_id"]: r for r in resources_sorted}

    # ----------------------------------------------------
    # FILE 1: 01_roadmap.csv
    # ----------------------------------------------------
    roadmap_rows = []
    for phase_id in PHASE_ORDER:
        meta = PHASE_METADATA[phase_id]
        phase_res = [r for r in resources_sorted if r["phase_id"] == phase_id]
        
        # Unique domains in order of first appearance
        seen_domains = []
        for r in phase_res:
            d = r["domain_sub_track"]
            if d not in seen_domains:
                seen_domains.append(d)
        topics_covered = " | ".join(seen_domains)
        total_hours = sum(r["estimated_hours"] for r in phase_res)

        roadmap_rows.append({
            "phase_order": meta["phase_order"],
            "phase_id": phase_id,
            "phase_name": meta["phase_name"],
            "phase_objective": meta["phase_objective"],
            "topics_covered": topics_covered,
            "learner_outcome": meta["learner_outcome"],
            "total_estimated_hours": total_hours,
            "recommended_next_phase": meta["recommended_next_phase"]
        })

    # ----------------------------------------------------
    # FILE 2: 02_phase_resources.csv
    # ----------------------------------------------------
    resources_rows = []
    for r in resources_sorted:
        resources_rows.append({
            "phase_order": r["phase_order"],
            "phase_id": r["phase_id"],
            "domain_sub_track": r["domain_sub_track"],
            "resource_id": r["resource_id"],
            "resource_title": r["resource_title"],
            "platform_author": r["platform_author"],
            "resource_type": r["resource_type"],
            "resource_format_group": r["resource_format_group"],
            "learning_style": r["learning_style"],
            "cost_model": r["cost_model"],
            "estimated_hours": r["estimated_hours"],
            "key_concepts_and_skills": r["key_concepts_and_skills"],
            "url_or_access_reference": r["url_or_access_reference"]
        })

    # ----------------------------------------------------
    # FILE 3: 03_prerequisites.csv
    # ----------------------------------------------------
    prereq_rows = []
    dq_notes = []

    for r in resources_sorted:
        p_raw = r["prerequisites_raw"]
        parts = [p.strip() for p in p_raw.split(",") if p.strip()]

        if not parts or (len(parts) == 1 and parts[0] == "None"):
            prereq_rows.append({
                "phase_order": r["phase_order"],
                "phase_id": r["phase_id"],
                "resource_id": r["resource_id"],
                "resource_title": r["resource_title"],
                "prerequisite_kind": "NONE",
                "prerequisite_resource_id": "",
                "prerequisite_title": "No prerequisites",
                "prerequisite_phase_id": "",
                "prerequisite_detail": "",
                "data_quality_note": ""
            })
            continue

        for part in parts:
            if part == "High School Math":
                for hsm in HIGH_SCHOOL_MATH_TOPICS:
                    prereq_rows.append({
                        "phase_order": r["phase_order"],
                        "phase_id": r["phase_id"],
                        "resource_id": r["resource_id"],
                        "resource_title": r["resource_title"],
                        "prerequisite_kind": "HIGH_SCHOOL_MATH",
                        "prerequisite_resource_id": "",
                        "prerequisite_title": hsm["topic"],
                        "prerequisite_phase_id": "",
                        "prerequisite_detail": hsm["detail"],
                        "data_quality_note": ""
                    })
            elif re.match(r"^AIML-\d{3}$", part):
                dq_note = ""
                if part not in resource_by_id:
                    p_title = "NOT FOUND IN SOURCE"
                    p_phase = ""
                    dq_note = f"Prerequisite ID {part} not found in source sheet"
                    dq_notes.append({
                        "resource_id": r["resource_id"],
                        "prerequisite": part,
                        "note": dq_note
                    })
                else:
                    target = resource_by_id[part]
                    p_title = target["resource_title"]
                    p_phase = target["phase_id"]

                    notes = []
                    if target["phase_order"] > r["phase_order"]:
                        notes.append("forward dependency")
                    if r["resource_id"] == part:
                        notes.append("self dependency")
                    if notes:
                        dq_note = "; ".join(notes)
                        dq_notes.append({
                            "resource_id": r["resource_id"],
                            "prerequisite": part,
                            "note": dq_note
                        })

                prereq_rows.append({
                    "phase_order": r["phase_order"],
                    "phase_id": r["phase_id"],
                    "resource_id": r["resource_id"],
                    "resource_title": r["resource_title"],
                    "prerequisite_kind": "RESOURCE",
                    "prerequisite_resource_id": part,
                    "prerequisite_title": p_title,
                    "prerequisite_phase_id": p_phase,
                    "prerequisite_detail": "",
                    "data_quality_note": dq_note
                })
            else:
                # Other free-text prerequisite
                prereq_rows.append({
                    "phase_order": r["phase_order"],
                    "phase_id": r["phase_id"],
                    "resource_id": r["resource_id"],
                    "resource_title": r["resource_title"],
                    "prerequisite_kind": "OTHER",
                    "prerequisite_resource_id": "",
                    "prerequisite_title": part,
                    "prerequisite_phase_id": "",
                    "prerequisite_detail": "",
                    "data_quality_note": ""
                })

    # ----------------------------------------------------
    # Write CSVs
    # ----------------------------------------------------
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    file1_path = os.path.join(OUTPUT_DIR, "01_roadmap.csv")
    file2_path = os.path.join(OUTPUT_DIR, "02_phase_resources.csv")
    file3_path = os.path.join(OUTPUT_DIR, "03_prerequisites.csv")

    # File 1
    file1_cols = [
        "phase_order", "phase_id", "phase_name", "phase_objective",
        "topics_covered", "learner_outcome", "total_estimated_hours",
        "recommended_next_phase"
    ]
    with open(file1_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=file1_cols, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(roadmap_rows)

    # File 2
    file2_cols = [
        "phase_order", "phase_id", "domain_sub_track", "resource_id",
        "resource_title", "platform_author", "resource_type",
        "resource_format_group", "learning_style", "cost_model",
        "estimated_hours", "key_concepts_and_skills", "url_or_access_reference"
    ]
    with open(file2_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=file2_cols, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(resources_rows)

    # File 3
    file3_cols = [
        "phase_order", "phase_id", "resource_id", "resource_title",
        "prerequisite_kind", "prerequisite_resource_id", "prerequisite_title",
        "prerequisite_phase_id", "prerequisite_detail", "data_quality_note"
    ]
    with open(file3_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=file3_cols, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(prereq_rows)

    # Also sync to inner EBuddy-main/output if directory exists
    inner_output_dir = os.path.join("EBuddy-main", "output")
    if os.path.isdir("EBuddy-main"):
        os.makedirs(inner_output_dir, exist_ok=True)
        for fname in ["01_roadmap.csv", "02_phase_resources.csv", "03_prerequisites.csv"]:
            src = os.path.join(OUTPUT_DIR, fname)
            dst = os.path.join(inner_output_dir, fname)
            with open(src, "rb") as sf, open(dst, "wb") as df:
                df.write(sf.read())

    # ----------------------------------------------------
    # Assertions
    # ----------------------------------------------------
    print("=" * 70)
    print("RUNNING VALIDATION ASSERTIONS")
    print("=" * 70)

    # 1. 02_phase_resources.csv has exactly 55 rows, unique IDs
    assert len(resources_rows) == 55, f"Expected 55 rows in 02, got {len(resources_rows)}"
    unique_ids = set(r["resource_id"] for r in resources_rows)
    assert len(unique_ids) == 55, f"Expected 55 unique IDs, got {len(unique_ids)}"
    print("[PASS] 02_phase_resources.csv has exactly 55 rows and all resource_ids are unique.")

    # 2. Per-phase resource counts match Excel file (table)
    print("\n[Per-Phase Resource Counts & Hours Table]")
    print(f"{'Phase ID':<20} | {'Phase Name':<30} | {'Count':<6} | {'Hours':<6}")
    print("-" * 72)
    for rmap in roadmap_rows:
        pid = rmap["phase_id"]
        pname = rmap["phase_name"]
        p_count = sum(1 for r in resources_rows if r["phase_id"] == pid)
        p_hours = rmap["total_estimated_hours"]
        print(f"{pid:<20} | {pname:<30} | {p_count:<6} | {p_hours:<6}")
    print("-" * 72)
    print(f"{'TOTAL':<20} | {'':<30} | {len(resources_rows):<6} | {sum(r['total_estimated_hours'] for r in roadmap_rows):<6}\n")

    # 3. Every resource_id in 02 appears at least once in 03
    prereq_res_ids = set(r["resource_id"] for r in prereq_rows)
    for rid in unique_ids:
        assert rid in prereq_res_ids, f"Resource {rid} missing from 03_prerequisites.csv"
    print("[PASS] Every resource_id in 02 appears at least once in 03_prerequisites.csv.")

    # 4. Sum of estimated_hours in 02 equals sum in Excel
    sum_hours_02 = sum(r["estimated_hours"] for r in resources_rows)
    assert sum_hours_02 == excel_total_hours, f"Sum of hours mismatch: 02={sum_hours_02}, Excel={excel_total_hours}"
    print(f"[PASS] Sum of estimated_hours in 02 ({sum_hours_02}) equals Excel data rows ({excel_total_hours}).")

    # 5. 01_roadmap.csv has exactly 6 rows and total_estimated_hours equals sum from 02
    assert len(roadmap_rows) == 6, f"Expected 6 rows in 01, got {len(roadmap_rows)}"
    sum_hours_01 = sum(r["total_estimated_hours"] for r in roadmap_rows)
    assert sum_hours_01 == sum_hours_02, f"Hours mismatch between 01 ({sum_hours_01}) and 02 ({sum_hours_02})"
    print(f"[PASS] 01_roadmap.csv has exactly 6 rows and total hours ({sum_hours_01}) matches 02_phase_resources.csv.")

    # 6. Print every data_quality_note raised
    print("\n[Data Quality Notes Raised]")
    if dq_notes:
        for dq in dq_notes:
            print(f"  Resource {dq['resource_id']} -> Prerequisite '{dq['prerequisite']}': {dq['note']}")
    else:
        print("  None raised.")
    print("=" * 70)

if __name__ == "__main__":
    build()
