import os
import csv
import json

def generate_base_seeds():
    os.makedirs("data/seed/kb", exist_ok=True)
    os.makedirs("data/seed/student", exist_ok=True)

    # 1. kb.source
    sources = [
        ("IITBBS_EE_CURRICULUM_2016_17", "IIT Bhubaneswar B.Tech Electrical Engineering Curriculum 2016-17", "https://www.iitbbs.ac.in/electrical-engineering-curriculum/", "IIT Bhubaneswar", "Public Academic Curriculum", "2026-11-13", "curriculum_pdf", "official", "2016-17", "Official curriculum sheet"),
        ("IITBBS_EE_PLAYLISTS_2026", "IIT Bhubaneswar EE NPTEL & Open Course Playlists", "https://www.youtube.com/user/nptelhrd", "NPTEL / IITBBS", "CC-BY / Public", "2026-11-13", "oer", "compiled_secondary", "2026", "Search results compiled for NPTEL/OCW"),
        ("IITBBS_RESEARCH_ALL", "IIT Bhubaneswar SECS Research Projects Directory", "secs.iitbbs.ac.in/index.php/research-projects/", "SECS IIT Bhubaneswar", "Public Institutional Record", "2026-11-13", "course_page", "compiled_secondary", "2026", "138 SECS research projects"),
        ("IITBBS_RESEARCH_V2", "IIT Bhubaneswar SECS Research Projects Detailed Register v2", "secs.iitbbs.ac.in/index.php/research-projects/", "SECS IIT Bhubaneswar", "Public Institutional Record", "2026-11-13", "course_page", "compiled_secondary", "2026", "68 full projects with grant/scope"),
        ("PLACEHOLDER", "Unresolved or Pending Ingestion Document", "https://internal.placeholder", "IIT Bhubaneswar", "Internal", "2026-11-13", "rules", "placeholder", "2026", "Placeholder source")
    ]
    with open("data/seed/kb/source.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source_id", "title", "url", "publisher", "licence", "retrieved_on", "doc_type", "reliability", "academic_year", "notes"])
        for s in sources:
            writer.writerow(s)

    # 2. kb.department
    departments = [
        ("EE", "School of Electrical Sciences (Electrical Engineering)"),
        ("EC", "School of Electrical Sciences (Electronics & Communication Engineering)"),
        ("CS", "School of Electrical Sciences (Computer Science & Engineering)"),
        ("MM", "School of Minerals, Metallurgical and Materials Engineering (SMMME)"),
        ("ME", "School of Mechanical Sciences"),
        ("CE", "School of Infrastructure (Civil Engineering)"),
        ("BS", "School of Basic Sciences"),
        ("HSS", "School of Humanities, Social Sciences & Management")
    ]
    with open("data/seed/kb/department.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["department_id", "name"])
        for d in departments:
            writer.writerow(d)

    # 3. kb.programme
    programmes = [
        ("BTECH_EE", "B.Tech Electrical Engineering", "EE", 181.0, 8, "2016-17"),
        ("BTECH_MM", "B.Tech Metallurgical and Materials Engineering", "MM", 180.0, 8, "2016-17")
    ]
    with open("data/seed/kb/programme.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["programme_id", "name", "department_id", "total_credits_required", "duration_semesters", "curriculum_version"])
        for p in programmes:
            writer.writerow(p)

    # 4. kb.goal
    goals = [
        ("GOAL_EE_CORE_VLSI", "Core VLSI & Semiconductor Engineering", "career", "Industry core roles in IC design, FPGA/ASIC verification, semiconductor device modeling, and embedded hardware architectures."),
        ("GOAL_EE_CORE_POWER", "Power Systems, Smart Grid & Renewable Energy", "career", "Industry and utility core roles in smart grid operations, renewable energy integration, power system protection, and EV drivetrain charging."),
        ("GOAL_EE_RES_HIGHER_STUDIES", "Higher Studies & Research in Electrical Sciences", "higher_studies", "Preparation for Ph.D. / MS research tracks, funded academic lab projects, international research fellowships, and faculty lab exploration."),
        ("GOAL_CROSS_SDE_DATA", "Software Engineering & Data Science Transition", "career", "Cross-branch transition to software development, machine learning, and systems engineering leveraging CS minor courses and algorithmic electives."),
        ("GOAL_UPSC_COMPETITIVE", "Public Services & Competitive Examinations", "competitive_exam", "Preparation for UPSC CSE, IES (ESE), GATE, and PSU recruitments while maintaining steady degree completion and controlled cognitive workload."),
        ("GOAL_TECH_STARTUP", "Deep-Tech Entrepreneurship & Venture Development", "startup", "Building deep-tech hardware/software startups, prototype commercialization, and incubation balancing academic obligations.")
    ]
    with open("data/seed/kb/goal.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["goal_id", "name", "category", "description"])
        for g in goals:
            writer.writerow(g)

    # 5. kb.skill (Initial foundational skills spanning Electrical & CS domains)
    skills = [
        ("SKILL_CIRCUIT_ANALYSIS", "Circuit Theory & Network Synthesis", "Electrical Core", "Transient response, AC network analysis, two-port networks, resonance, and state equations.", "0-100"),
        ("SKILL_SIGNALS_SYSTEMS", "Signals & Linear Systems", "Signal Processing", "Continuous and discrete-time signals, LTI systems, Fourier/Laplace/Z-transforms, convolution.", "0-100"),
        ("SKILL_DIGITAL_LOGIC", "Digital Logic & Microprocessors", "Hardware Systems", "Combinational and sequential circuits, FSMs, 8086 microprocessors, timing diagrams.", "0-100"),
        ("SKILL_POWER_ELECTRONICS", "Power Electronic Converters & Drives", "Power Engineering", "DC-DC converters, inverters, rectifiers, modulation techniques, gate drivers.", "0-100"),
        ("SKILL_POWER_SYSTEMS", "Power System Analysis & Grid Operations", "Power Engineering", "Transmission lines, load flow, fault analysis, stability, economic dispatch.", "0-100"),
        ("SKILL_ELECTRIC_MACHINES", "Electrical Machines & Electromechanics", "Electrical Core", "Transformers, DC machines, induction and synchronous motors, magnetic circuits.", "0-100"),
        ("SKILL_CONTROL_SYSTEMS", "Classical & Modern Feedback Control", "Control & Systems", "Root locus, Bode/Nyquist plots, state-space representations, stability margins.", "0-100"),
        ("SKILL_EM_FIELDS", "Electromagnetics & Transmission Lines", "Electromagnetics", "Maxwell equations, plane wave propagation, boundary conditions, wave guides.", "0-100"),
        ("SKILL_DSP", "Digital Signal Processing & Filtering", "Signal Processing", "DFT, FFT, FIR/IIR filter design, multirate DSP, spectral analysis.", "0-100"),
        ("SKILL_VLSI_DESIGN", "CMOS VLSI Design & Verilog", "VLSI & Hardware", "CMOS digital circuits, ASIC flow, timing closure, layout rules, SPICE simulation.", "0-100"),
        ("SKILL_EMBEDDED_SYSTEMS", "Embedded Systems & Real-Time Computing", "Embedded Systems", "Microcontrollers, ARM architecture, RTOS, peripheral interfaces (SPI/I2C/UART).", "0-100"),
        ("SKILL_PROGRAMMING_C_DS", "Programming in C & Data Structures", "Computer Science", "Algorithms, arrays, pointers, linked lists, trees, graphs, sorting/searching.", "0-100"),
        ("SKILL_AI_ML", "Machine Learning & Pattern Recognition", "Artificial Intelligence", "Supervised/unsupervised learning, neural networks, optimization, gradient descent.", "0-100"),
        ("SKILL_RENEWABLE_ENERGY", "Renewable Energy & Microgrid Architecture", "Renewables", "Solar PV MPPT, wind generation, energy storage systems, islanded microgrids.", "0-100"),
        ("SKILL_INSTRUMENTATION", "Instrumentation, Transducers & Sensors", "Measurement", "Signal conditioning, error analysis, strain gauges, piezoelectric/thermal sensors.", "0-100")
    ]
    with open("data/seed/kb/skill.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["skill_id", "name", "domain", "description", "level_scale"])
        for sk in skills:
            writer.writerow(sk)

    # 6. kb.minor
    minors = [
        ("MINOR_CSE", "Computer Science and Engineering Minor", "CS", 8.00, 18.0, "IITBBS_EE_CURRICULUM_2016_17"),
        ("MINOR_DS", "Data Science and Artificial Intelligence Minor", "CS", 8.00, 18.0, "IITBBS_EE_CURRICULUM_2016_17")
    ]
    with open("data/seed/kb/minor.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["minor_id", "name", "offering_department", "min_cgpa", "min_credits", "source_id"])
        for m in minors:
            writer.writerow(m)

    # 7. kb.academic_rule.json (Seed JSON with machine-readable rules)
    rules = [
        {
            "rule_id": "RULE_SEM_CREDIT_CAP_REGULAR",
            "rule_type": "credit_cap",
            "parameters": {"max_credits": 26.0, "min_credits": 16.0, "min_cgpa_for_overload": 8.50, "max_overload_credits": 30.0},
            "human_text": "A student in normal academic standing may register for between 16 and 26 credits per regular semester. Students with CGPA >= 8.50 may overload up to 30 credits with Faculty Advisor approval.",
            "source_id": "IITBBS_EE_CURRICULUM_2016_17"
        },
        {
            "rule_id": "RULE_SEM_CREDIT_CAP_PROBATION",
            "rule_type": "credit_cap",
            "parameters": {"max_credits": 18.0, "min_credits": 12.0, "cgpa_threshold": 6.00},
            "human_text": "Students on academic probation or with CGPA below 6.00 are restricted to a reduced credit cap of 18 credits to facilitate backlog clearance.",
            "source_id": "IITBBS_EE_CURRICULUM_2016_17"
        },
        {
            "rule_id": "RULE_MINOR_ELIGIBILITY",
            "rule_type": "minor_eligibility",
            "parameters": {"min_cgpa": 8.00, "start_semester": 5, "total_minor_credits": 18.0},
            "human_text": "Students with CGPA >= 8.00 at the end of the 4th semester are eligible to enroll in an academic Minor (18 credits completed between Sem V and Sem VIII).",
            "source_id": "IITBBS_EE_CURRICULUM_2016_17"
        },
        {
            "rule_id": "RULE_ONLINE_CREDIT_NPTEL",
            "rule_type": "online_credit",
            "parameters": {"max_online_credits": 12.0, "approved_providers": ["NPTEL", "SWAYAM"], "min_duration_weeks": 8},
            "human_text": "A maximum of 12 credits earned through approved 8-week or 12-week NPTEL/SWAYAM courses may be transferred towards Open / Free Electives upon approval.",
            "source_id": "IITBBS_EE_CURRICULUM_2016_17"
        }
    ]
    with open("data/seed/kb/academic_rule.json", "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2)

    # 8. kb.mastery_criteria.json
    mastery = [
        {
            "criteria_id": "MASTERY_VLSI",
            "goal_id": "GOAL_EE_CORE_VLSI",
            "skill_id": None,
            "criteria": {
                "min_skill_level": 75.0,
                "required_project_milestones": 1,
                "required_timed_assessments": 2,
                "min_diagnostic_score": 70.0
            }
        },
        {
            "criteria_id": "MASTERY_POWER",
            "goal_id": "GOAL_EE_CORE_POWER",
            "skill_id": None,
            "criteria": {
                "min_skill_level": 75.0,
                "required_project_milestones": 1,
                "required_timed_assessments": 2,
                "min_diagnostic_score": 70.0
            }
        },
        {
            "criteria_id": "MASTERY_RESEARCH",
            "goal_id": "GOAL_EE_RES_HIGHER_STUDIES",
            "skill_id": None,
            "criteria": {
                "min_skill_level": 80.0,
                "required_project_milestones": 2,
                "required_timed_assessments": 2,
                "faculty_lab_mapping_required": True
            }
        }
    ]
    with open("data/seed/kb/mastery_criteria.json", "w", encoding="utf-8") as f:
        json.dump(mastery, f, indent=2)

    print("Base seed files generated successfully in data/seed/kb/.")

if __name__ == "__main__":
    generate_base_seeds()

