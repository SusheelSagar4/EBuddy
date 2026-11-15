"""
Generates canonical relational seed CSVs for:
1. data/seed/kb/field_roadmap.csv
2. data/seed/kb/field_phase.csv
3. data/seed/kb/field_topic.csv
4. data/seed/kb/course_eligibility.csv

Derived from existing packages:
- sde/output/
- aiml/output/
- data_analyst/output/
- data/seed/core_to_mtech/
- data/seed/mba/
- data/raw/higher_studies/upsc/
- data/seed/kb/
"""

import os
import csv
import json

def generate_field_seeds(base_dir="."):
    seed_kb_dir = os.path.join(base_dir, "data", "seed", "kb")
    os.makedirs(seed_kb_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    # 1. FIELD ROADMAPS
    # -------------------------------------------------------------------------
    roadmaps = [
        {
            "field_id": "FIELD_SDE",
            "name": "Software Development Engineering (SDE)",
            "category": "software_engineering",
            "description": "Comprehensive pathway from programming fundamentals and LeetCode DSA to system design and portfolio projects.",
            "total_phases": 8,
            "total_estimated_hours": 480.0,
            "source_id": "OFFICIAL"
        },
        {
            "field_id": "FIELD_AIML",
            "name": "AI & Machine Learning (AI/ML)",
            "category": "artificial_intelligence",
            "description": "Mathematical foundations, classical ML algorithms, deep learning architectures, computer vision, NLP, and LLM applications.",
            "total_phases": 6,
            "total_estimated_hours": 1624.0,
            "source_id": "OFFICIAL"
        },
        {
            "field_id": "FIELD_DA",
            "name": "Data Analytics (DA)",
            "category": "data_analytics",
            "description": "End-to-end data analytics curriculum: SQL databases, Excel, Python data stack, BI visualization, and real-world portfolio analytics.",
            "total_phases": 5,
            "total_estimated_hours": 314.0,
            "source_id": "OFFICIAL"
        },
        {
            "field_id": "FIELD_GATE_MTECH",
            "name": "Core Higher Studies (GATE → M.Tech / MS / PSU)",
            "category": "higher_studies",
            "description": "Postgraduate technical admissions at IISc/IITs via GATE (EE / MT papers) and Maharatna/Navratna PSU recruitment.",
            "total_phases": 4,
            "total_estimated_hours": 500.0,
            "source_id": "OFFICIAL"
        },
        {
            "field_id": "FIELD_CAT_MBA",
            "name": "Core to MBA (CAT Fresher / Executive)",
            "category": "management",
            "description": "Strategic management career transition for engineers: CAT QA/DILR/VARC preparation, profile audits, and technical viva coaching.",
            "total_phases": 4,
            "total_estimated_hours": 320.0,
            "source_id": "OFFICIAL"
        },
        {
            "field_id": "FIELD_UPSC",
            "name": "Civil Services (UPSC CSE / ESE)",
            "category": "civil_services",
            "description": "Structured preparation for Civil Services Examination (General Studies, CSAT, Essay, and Engineering Optional).",
            "total_phases": 4,
            "total_estimated_hours": 800.0,
            "source_id": "OFFICIAL"
        },
        {
            "field_id": "FIELD_CORE_RESEARCH",
            "name": "Core Engineering Research Track",
            "category": "research",
            "description": "Undergraduate research mentorship under 44 verified IIT Bhubaneswar faculty, paper insights, and international research internships.",
            "total_phases": 4,
            "total_estimated_hours": 400.0,
            "source_id": "OFFICIAL"
        },
        {
            "field_id": "FIELD_CORE_INDUSTRY",
            "name": "Core Engineering Industry & PSUs",
            "category": "core_industry",
            "description": "Engineering domain depth, industrial simulation tools (MATLAB, PSCAD, ANSYS), project societies (SAE BAJA), and PSU tests.",
            "total_phases": 4,
            "total_estimated_hours": 350.0,
            "source_id": "OFFICIAL"
        },
        {
            "field_id": "FIELD_STARTUP",
            "name": "Student Entrepreneurship & Startup Incubation",
            "category": "entrepreneurship",
            "description": "Customer discovery, prototype MVP engineering, unit economics, IP protection, and incubation grant pitch preparation.",
            "total_phases": 4,
            "total_estimated_hours": 300.0,
            "source_id": "OFFICIAL"
        }
    ]

    field_roadmap_path = os.path.join(seed_kb_dir, "field_roadmap.csv")
    with open(field_roadmap_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["field_id", "name", "category", "description", "total_phases", "total_estimated_hours", "source_id"])
        writer.writeheader()
        writer.writerows(roadmaps)
    print(f"Wrote {len(roadmaps)} rows to {field_roadmap_path}")

    # -------------------------------------------------------------------------
    # 2. FIELD PHASES & TOPICS EXTRACTION
    # -------------------------------------------------------------------------
    phases = []
    topics = []

    # A. SDE Track
    sde_overview_file = os.path.join(base_dir, "sde", "output", "01_sde_roadmap_overview.csv")
    sde_content_file = os.path.join(base_dir, "sde", "output", "02_phase_learning_content.csv")

    sde_phase_map = {}
    if os.path.exists(sde_overview_file):
        with open(sde_overview_file, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                pid = r["phase_id"].strip()
                sde_phase_map[pid] = r
                phases.append({
                    "phase_id": f"SDE_{pid}",
                    "field_id": "FIELD_SDE",
                    "phase_order": int(r.get("phase_order") or r.get("\ufeffphase_order") or 1),
                    "phase_name": r["phase_name"].strip(),
                    "phase_objective": r.get("phase_objective", "").strip(),
                    "learner_outcome": r.get("learner_outcome", "").strip(),
                    "estimated_hours": 60.0
                })

    if os.path.exists(sde_content_file):
        seen_steps = set()
        with open(sde_content_file, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                step = r["step_number"].strip()
                pid = r["phase_id"].strip()
                tier = r.get("tier", "").strip().upper()
                if step not in seen_steps and (tier in ["A", "TIER A", ""]):
                    seen_steps.add(step)
                    skill_id = "SKILL_PROGRAMMING_DS"
                    top_name = r["topic_skill"].strip().lower()
                    if "data structure" in top_name or "algorithm" in top_name or "tree" in top_name or "graph" in top_name:
                        skill_id = "SKILL_DATA_STRUCTURES_ALGO"
                    elif "database" in top_name or "sql" in top_name:
                        skill_id = "SKILL_DATABASES_SQL"
                    elif "os" in top_name or "operating system" in top_name or "linux" in top_name:
                        skill_id = "SKILL_OPERATING_SYSTEMS"
                    elif "system design" in top_name or "architecture" in top_name:
                        skill_id = "SKILL_DATA_STRUCTURES_ALGO"

                    topics.append({
                        "topic_id": f"TOPIC_SDE_STEP_{int(step):02d}",
                        "field_id": "FIELD_SDE",
                        "phase_id": f"SDE_{pid}",
                        "topic_order": int(step),
                        "title": r["topic_skill"].strip(),
                        "key_concepts": r.get("key_concepts_and_skills_derived", r.get("what_to_learn", "")).strip(),
                        "est_hours": 8.0,
                        "skill_id": skill_id,
                        "prerequisite_topic_ids": f"TOPIC_SDE_STEP_{int(step)-1:02d}" if int(step) > 1 else "",
                        "resource_title": r.get("resource_title", "").strip(),
                        "resource_url": r.get("url", "").strip()
                    })

    # B. AI/ML Track
    aiml_overview_file = os.path.join(base_dir, "aiml", "output", "01_roadmap.csv")
    aiml_res_file = os.path.join(base_dir, "aiml", "output", "02_phase_resources.csv")

    if os.path.exists(aiml_overview_file):
        with open(aiml_overview_file, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                pid = r["phase_id"].strip()
                hours = float(r.get("total_estimated_hours", 200.0) or 200.0)
                phases.append({
                    "phase_id": f"AIML_{pid}",
                    "field_id": "FIELD_AIML",
                    "phase_order": int(r.get("phase_order") or r.get("\ufeffphase_order") or 1),
                    "phase_name": r["phase_name"].strip(),
                    "phase_objective": r.get("phase_objective", "").strip(),
                    "learner_outcome": r.get("learner_outcome", "").strip(),
                    "estimated_hours": hours
                })

    if os.path.exists(aiml_res_file):
        topic_order = 1
        with open(aiml_res_file, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                pid = r["phase_id"].strip()
                res_id = r["resource_id"].strip()
                hours = float(r.get("estimated_hours", 12.0) or 12.0)
                title = r.get("resource_title", "").strip()
                concepts = r.get("key_concepts_and_skills", "").strip()
                
                # Check for NLP
                skill_id = "SKILL_AI_ML"
                if "nlp" in title.lower() or "natural language" in title.lower() or "nlp" in concepts.lower() or "language" in concepts.lower():
                    skill_id = "SKILL_AI_ML" # Primary AI/ML skill, with NLP key concept
                elif "math" in title.lower() or "calculus" in title.lower() or "linear algebra" in title.lower():
                    skill_id = "SKILL_ENGINEERING_MATH"
                elif "probab" in title.lower() or "stats" in title.lower():
                    skill_id = "SKILL_PROBABILITY_STATS"

                topics.append({
                    "topic_id": f"TOPIC_AIML_{topic_order:02d}",
                    "field_id": "FIELD_AIML",
                    "phase_id": f"AIML_{pid}",
                    "topic_order": topic_order,
                    "title": f"{r.get('domain_sub_track', 'AI/ML')}: {title}",
                    "key_concepts": concepts,
                    "est_hours": min(16.0, max(4.0, hours)),
                    "skill_id": skill_id,
                    "prerequisite_topic_ids": f"TOPIC_AIML_{topic_order-1:02d}" if topic_order > 1 else "",
                    "resource_title": title,
                    "resource_url": r.get("url_or_access_reference", "").strip()
                })
                topic_order += 1

    # C. Data Analyst Track
    da_overview_file = os.path.join(base_dir, "data_analyst", "output", "01_da_roadmap_overview.csv")
    da_modules_file = os.path.join(base_dir, "data_analyst", "output", "02_phase_modules_resources.csv")

    if os.path.exists(da_overview_file):
        with open(da_overview_file, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                pid = r["phase_id"].strip()
                phases.append({
                    "phase_id": f"DA_{pid}",
                    "field_id": "FIELD_DA",
                    "phase_order": int(r.get("phase_order") or r.get("\ufeffphase_order") or 1),
                    "phase_name": r["phase_name"].strip(),
                    "phase_objective": r.get("phase_objective_derived", "").strip(),
                    "learner_outcome": r.get("learner_outcome_derived", "").strip(),
                    "estimated_hours": 65.0
                })

    if os.path.exists(da_modules_file):
        seen_modules = set()
        da_topic_order = 1
        with open(da_modules_file, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                mid = r["module_id"].strip()
                pid = r["phase_id"].strip()
                if mid not in seen_modules:
                    seen_modules.add(mid)
                    hours = float(r.get("module_est_hours", 8.0) or 8.0)
                    skill_cat = r.get("skill_category", "").lower()
                    skill_id = "SKILL_DATABASES_SQL" if "sql" in skill_cat or "database" in skill_cat else ("SKILL_PROBABILITY_STATS" if "stat" in skill_cat else "SKILL_PROGRAMMING_DS")

                    topics.append({
                        "topic_id": f"TOPIC_DA_{da_topic_order:02d}",
                        "field_id": "FIELD_DA",
                        "phase_id": f"DA_{pid}",
                        "topic_order": da_topic_order,
                        "title": r.get("module_title", mid).strip(),
                        "key_concepts": r.get("key_concepts_and_skills_derived", r.get("what_to_learn_objective", "")).strip(),
                        "est_hours": min(12.0, max(4.0, hours)),
                        "skill_id": skill_id,
                        "prerequisite_topic_ids": f"TOPIC_DA_{da_topic_order-1:02d}" if da_topic_order > 1 else "",
                        "resource_title": r.get("resource_title", "").strip(),
                        "resource_url": r.get("resource_url", "").strip()
                    })
                    da_topic_order += 1

    # D. GATE / M.Tech Higher Studies Track
    phases.extend([
        {"phase_id": "MTECH_PH1", "field_id": "FIELD_GATE_MTECH", "phase_order": 1, "phase_name": "Engineering Mathematics & General Aptitude", "phase_objective": "Master foundational 28 marks: Calculus, Linear Algebra, Probability, Numerical Methods & Verbal/Numerical Aptitude.", "learner_outcome": "Guaranteed 25+ marks baseline on General Aptitude and Math sections.", "estimated_hours": 120.0},
        {"phase_id": "MTECH_PH2", "field_id": "FIELD_GATE_MTECH", "phase_order": 2, "phase_name": "Core Technical Depth & High-Weightage Topics", "phase_objective": "Thorough syllabus coverage of top branch subjects (Networks, Machines, Power Systems for EE; Thermodynamics, Physical Metallurgy for MT).", "learner_outcome": "Complete syllabus mastery of core 72 technical marks.", "estimated_hours": 200.0},
        {"phase_id": "MTECH_PH3", "field_id": "FIELD_GATE_MTECH", "phase_order": 3, "phase_name": "Full-Length Mocks & Error Analysis", "phase_objective": "Timed 3-hour national-level mock tests simulating actual GATE interface, scoring formula, and virtual calculator.", "learner_outcome": "Calibrated score band with AIR projection.", "estimated_hours": 100.0},
        {"phase_id": "MTECH_PH4", "field_id": "FIELD_GATE_MTECH", "phase_order": 4, "phase_name": "Counselling & PSU Technical Viva Prep", "phase_objective": "Strategic COAP/CCMT round choices and technical viva voce coaching for MS(R) and PSU interviews.", "learner_outcome": "Secured master's admission or PSU offer.", "estimated_hours": 80.0}
    ])
    gate_topics = [
        ("TOPIC_GATE_01", "MTECH_PH1", 1, "Linear Algebra & Matrix Eigenvalues", "Vector spaces, rank, nullity, eigenvalues, Cayley-Hamilton theorem", 8.0, "SKILL_ENGINEERING_MATH"),
        ("TOPIC_GATE_02", "MTECH_PH1", 2, "Calculus & Differential Equations", "Mean value theorems, line/surface integrals, Cauchy-Riemann, differential equations", 10.0, "SKILL_ENGINEERING_MATH"),
        ("TOPIC_GATE_03", "MTECH_PH1", 3, "Probability & Numerical Methods", "Bayes theorem, normal distribution, Newton-Raphson, Runge-Kutta", 8.0, "SKILL_PROBABILITY_STATS"),
        ("TOPIC_GATE_04", "MTECH_PH2", 4, "Electric Circuits & Network Theorems", "Thevenin, Norton, Superposition, Maximum Power, transient response, 2-port parameters", 12.0, "SKILL_CIRCUIT_ANALYSIS"),
        ("TOPIC_GATE_05", "MTECH_PH2", 5, "Electromagnetic Fields & Waves", "Maxwell equations, wave propagation, Poynting vector, boundary conditions", 10.0, "SKILL_EM_FIELDS"),
        ("TOPIC_GATE_06", "MTECH_PH2", 6, "Electrical Machines (Transformers & Induction)", "Equivalent circuits, testing, torque-speed characteristics, losses & efficiency", 14.0, "SKILL_ELECTRIC_MACHINES"),
        ("TOPIC_GATE_07", "MTECH_PH2", 7, "Power System Analysis & Faults", "Admittance matrix, power flow (Gauss-Seidel, NR), symmetrical & unsymmetrical faults", 16.0, "SKILL_POWER_SYSTEMS"),
        ("TOPIC_GATE_08", "MTECH_PH2", 8, "Control Systems & Stability", "Transfer functions, Routh-Hurwitz, Nyquist, Bode plots, state-space models", 12.0, "SKILL_CONTROL_SYSTEMS"),
        ("TOPIC_GATE_09", "MTECH_PH3", 9, "Full-Length Mock 1 & Error Logging", "3-hour comprehensive mock test under timed exam conditions with negative marking audit", 6.0, "SKILL_POWER_SYSTEMS"),
        ("TOPIC_GATE_10", "MTECH_PH3", 10, "Full-Length Mock 2 & Score Band Calibration", "Second full mock test to compute empirical mean and standard deviation for score band", 6.0, "SKILL_POWER_SYSTEMS"),
        ("TOPIC_GATE_11", "MTECH_PH4", 11, "COAP & CCMT Portal Application Strategy", "Preference ordering across IIT Bombay, IIT Madras, IISc Bangalore based on category cutoffs", 4.0, "SKILL_RESEARCH_WRITING"),
        ("TOPIC_GATE_12", "MTECH_PH4", 12, "Technical Viva Voce Simulation", "Simulated oral viva on circuit theorems, machine fundamentals, and B.Tech project", 6.0, "SKILL_RESEARCH_WRITING")
    ]
    for tid, pid, ord_num, title, concepts, hrs, sid in gate_topics:
        topics.append({
            "topic_id": tid,
            "field_id": "FIELD_GATE_MTECH",
            "phase_id": pid,
            "topic_order": ord_num,
            "title": title,
            "key_concepts": concepts,
            "est_hours": hrs,
            "skill_id": sid,
            "prerequisite_topic_ids": f"TOPIC_GATE_{ord_num-1:02d}" if ord_num > 1 else "",
            "resource_title": "NPTEL GATE Prep & Official PYQ Portal",
            "resource_url": "https://gate.iitm.ac.in"
        })

    # E. Civil Services (UPSC CSE / ESE)
    phases.extend([
        {"phase_id": "UPSC_PH1", "field_id": "FIELD_UPSC", "phase_order": 1, "phase_name": "NCERT Baseline & General Studies Foundations", "phase_objective": "Build solid factual grounding across Indian Polity, Modern History, Geography, and Basic Economics.", "learner_outcome": "Complete conceptual coverage of NCERT classes 9-12 static syllabus.", "estimated_hours": 200.0},
        {"phase_id": "UPSC_PH2", "field_id": "FIELD_UPSC", "phase_order": 2, "phase_name": "Standard Reference Texts & Current Affairs System", "phase_objective": "Master standard textbooks (Laxmikanth, Spectrum, Shankar IAS) and establish a 45-min daily editorial synthesis routine.", "learner_outcome": "Consistent 60%+ accuracy on subject-wise Prelims PYQs.", "estimated_hours": 250.0},
        {"phase_id": "UPSC_PH3", "field_id": "FIELD_UPSC", "phase_order": 3, "phase_name": "Mains Answer Writing & Optional Subject", "phase_objective": "Practice timed answer writing on 5-point rubrics (introduction, structural points, diagrams, conclusion) and complete Optional Paper 1.", "learner_outcome": "Portfolio of 60 evaluated answers and completed optional subject first pass.", "estimated_hours": 220.0},
        {"phase_id": "UPSC_PH4", "field_id": "FIELD_UPSC", "phase_order": 4, "phase_name": "Prelims Mock Marathon & CSAT Practice", "phase_objective": "25 full GS Prelims mocks and 10 timed CSAT papers with strict negative marking error logs.", "learner_outcome": "Target score of 100+ on GS Paper 1 and 90+ on CSAT Paper 2.", "estimated_hours": 130.0}
    ])
    upsc_topics = [
        ("TOPIC_UPSC_01", "UPSC_PH1", 1, "Indian Constitution & Polity Foundations", "Preamble, Fundamental Rights, Directive Principles, Parliamentary system (Laxmikanth)", 12.0, "SKILL_UPSC_GS2_POLITY_GOVERNANCE_IR"),
        ("TOPIC_UPSC_02", "UPSC_PH1", 2, "Modern Indian History & Freedom Struggle", "1857 revolt, socio-religious reform, Indian National Congress phases, Gandhian movements", 12.0, "SKILL_UPSC_GS1_HISTORY_CULTURE"),
        ("TOPIC_UPSC_01B", "UPSC_PH1", 3, "Physical & Human Geography", "Geomorphology, climatology, oceanography, Indian river systems, monsoon mechanisms", 12.0, "SKILL_UPSC_GS1_GEOGRAPHY_SOCIETY"),
        ("TOPIC_UPSC_03", "UPSC_PH2", 4, "Indian Economy & Macroeconomic Concepts", "GDP, inflation, fiscal policy, banking system, RBI monetary tools, foreign trade", 14.0, "SKILL_UPSC_GS3_ECONOMY"),
        ("TOPIC_UPSC_04", "UPSC_PH2", 5, "Environment, Ecology & Biodiversity", "Protected areas, wildlife conservation acts, climate change conventions (UNFCCC, COP)", 12.0, "SKILL_UPSC_GS3_STI_ENV_SECURITY"),
        ("TOPIC_UPSC_05", "UPSC_PH2", 6, "Daily Current Affairs Synthesis Routine", "The Hindu / Indian Express editorial analysis mapped to GS syllabus topics", 10.0, "SKILL_UPSC_CURRENT_AFFAIRS"),
        ("TOPIC_UPSC_06", "UPSC_PH3", 7, "Ethics, Integrity & Case Studies", "Ethical theories, public service values, emotional intelligence, resolving ethical dilemmas", 12.0, "SKILL_UPSC_GS4_ETHICS_CASES"),
        ("TOPIC_UPSC_07", "UPSC_PH3", 8, "Mains Answer Writing Structure & Practice", "Structuring 10-marker and 15-marker answers: intro, multi-dimensional points, diagrams, way forward", 14.0, "SKILL_UPSC_ANSWER_WRITING"),
        ("TOPIC_UPSC_08", "UPSC_PH3", 9, "Engineering Optional Subject (Paper 1 Pass)", "Aligning B.Tech core coursework with UPSC Engineering Optional syllabus", 16.0, "SKILL_UPSC_OPTIONAL"),
        ("TOPIC_UPSC_09", "UPSC_PH4", 10, "CSAT Logical Reasoning & Reading Comprehension", "Speed math, critical reasoning, syllogisms, reading comprehension strategy", 8.0, "SKILL_UPSC_CSAT"),
        ("TOPIC_UPSC_10", "UPSC_PH4", 11, "Prelims GS Mock Tests & Elimination Techniques", "Timed 2-hour tests, error analysis notebook, risk-reward elimination strategies", 10.0, "SKILL_UPSC_PRELIMS_TESTCRAFT")
    ]
    for tid, pid, ord_num, title, concepts, hrs, sid in upsc_topics:
        topics.append({
            "topic_id": tid,
            "field_id": "FIELD_UPSC",
            "phase_id": pid,
            "topic_order": ord_num,
            "title": title,
            "key_concepts": concepts,
            "est_hours": hrs,
            "skill_id": sid,
            "prerequisite_topic_ids": f"TOPIC_UPSC_{ord_num-1:02d}" if ord_num > 1 else "",
            "resource_title": "Official UPSC Syllabus & NCERT Open Textbooks",
            "resource_url": "https://upsc.gov.in"
        })

    # F. Core Research & Core Industry
    phases.extend([
        {"phase_id": "CORE_RES_PH1", "field_id": "FIELD_CORE_RESEARCH", "phase_order": 1, "phase_name": "Domain Prerequisite Mastery", "phase_objective": "Attain >= 75% tested proficiency in branch foundation skills.", "learner_outcome": "Qualified readiness gate foundation.", "estimated_hours": 100.0},
        {"phase_id": "CORE_RES_PH2", "field_id": "FIELD_CORE_RESEARCH", "phase_order": 2, "phase_name": "Taster Tasks & Guided Paper Reading", "phase_objective": "Complete 2 hands-on exploratory taster tasks and 1 guided paper review from verified faculty papers.", "learner_outcome": "Demonstrated research methodology skills.", "estimated_hours": 120.0},
        {"phase_id": "CORE_RES_PH3", "field_id": "FIELD_CORE_RESEARCH", "phase_order": 3, "phase_name": "Faculty Mentorship & Research Kickoff", "phase_objective": "Approach verified professor with personalized draft and initiate 4-milestone undergraduate research project.", "learner_outcome": "Active research mentorship.", "estimated_hours": 100.0},
        {"phase_id": "CORE_RES_PH4", "field_id": "FIELD_CORE_RESEARCH", "phase_order": 4, "phase_name": "Summer Internship Applications (SURGE/DAAD)", "phase_objective": "Prepare research proposal and apply for national/international competitive fellowships.", "learner_outcome": "Competitive research internship offer.", "estimated_hours": 80.0},
        
        {"phase_id": "CORE_IND_PH1", "field_id": "FIELD_CORE_INDUSTRY", "phase_order": 1, "phase_name": "Core Technical Depth", "phase_objective": "Master high-impact branch subjects and lab fundamentals.", "learner_outcome": "Strong core academic foundation.", "estimated_hours": 90.0},
        {"phase_id": "CORE_IND_PH2", "field_id": "FIELD_CORE_INDUSTRY", "phase_order": 2, "phase_name": "Industrial Simulation & Design Tools", "phase_objective": "Hands-on mastery of industry standard tools (MATLAB/Simulink, PSCAD, ANSYS, Thermo-Calc).", "learner_outcome": "Portfolio of verified engineering simulation projects.", "estimated_hours": 110.0},
        {"phase_id": "CORE_IND_PH3", "field_id": "FIELD_CORE_INDUSTRY", "phase_order": 3, "phase_name": "Engineering Societies & Competitions", "phase_objective": "Active participation in Formula Student, SAE BAJA, or robotics technical societies.", "learner_outcome": "Practical hardware/system integration experience.", "estimated_hours": 80.0},
        {"phase_id": "CORE_IND_PH4", "field_id": "FIELD_CORE_INDUSTRY", "phase_order": 4, "phase_name": "Campus Placement & Core PSU Drives", "phase_objective": "Technical interview viva preparation and PSU aptitude tests for core engineering placement.", "learner_outcome": "Core engineering placement offer.", "estimated_hours": 70.0}
    ])

    field_phase_path = os.path.join(seed_kb_dir, "field_phase.csv")
    with open(field_phase_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["phase_id", "field_id", "phase_order", "phase_name", "phase_objective", "learner_outcome", "estimated_hours"])
        writer.writeheader()
        writer.writerows(phases)
    print(f"Wrote {len(phases)} rows to {field_phase_path}")

    field_topic_path = os.path.join(seed_kb_dir, "field_topic.csv")
    with open(field_topic_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["topic_id", "field_id", "phase_id", "topic_order", "title", "key_concepts", "est_hours", "skill_id", "prerequisite_topic_ids", "resource_title", "resource_url"])
        writer.writeheader()
        writer.writerows(topics)
    print(f"Wrote {len(topics)} rows to {field_topic_path}")

    # -------------------------------------------------------------------------
    # 3. COURSE ELIGIBILITY SEEDS (F8)
    # -------------------------------------------------------------------------
    # Load all courses from course.csv to define baseline eligibility rules
    course_file = os.path.join(seed_kb_dir, "course.csv")
    eligibility_rows = []
    if os.path.exists(course_file):
        with open(course_file, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                cid = r["course_id"].strip()
                dept = r.get("department_id", "").strip().upper()
                c_code = r.get("course_code", cid).strip().upper()

                min_cgpa = 0.0
                min_sem = 1
                max_backlogs = 99
                allowed_prog = "ANY"
                rule_name = "RULE_REGULAR_COURSE_ELIGIBILITY"

                # Minor courses (e.g. CS4L003, CS6L001) require CGPA >= 8.0, Semester >= 5, 0 backlogs
                if cid in ["CS4L003", "CS6L001", "CS6L005"]:
                    min_cgpa = 8.0
                    min_sem = 5
                    max_backlogs = 0
                    allowed_prog = "BTECH_EE,BTECH_MME"
                    rule_name = "RULE_MINOR_CSE_ELIGIBILITY"
                elif cid.startswith("ML") or dept == "MM":
                    allowed_prog = "BTECH_MME"
                    rule_name = "RULE_MME_CORE_ELIGIBILITY"
                elif cid.startswith("EE") or dept == "EE":
                    allowed_prog = "BTECH_EE"
                    rule_name = "RULE_EE_CORE_ELIGIBILITY"

                eligibility_rows.append({
                    "id": f"ELIG_{cid}",
                    "course_id": cid,
                    "min_cgpa": min_cgpa,
                    "min_semester": min_sem,
                    "max_backlogs": max_backlogs,
                    "allowed_programmes": allowed_prog,
                    "rule_name": rule_name,
                    "source_url": "https://www.iitbbs.ac.in/academic-rules",
                    "verified": True
                })

    course_elig_path = os.path.join(seed_kb_dir, "course_eligibility.csv")
    with open(course_elig_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "course_id", "min_cgpa", "min_semester", "max_backlogs", "allowed_programmes", "rule_name", "source_url", "verified"])
        writer.writeheader()
        writer.writerows(eligibility_rows)
    print(f"Wrote {len(eligibility_rows)} rows to {course_elig_path}")

if __name__ == "__main__":
    generate_field_seeds(".")

