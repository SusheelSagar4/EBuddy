"""
Generate unified skill framework, course-skill associations, career goals, and goal requirements
for both B.Tech Electrical Engineering and B.Tech Metallurgical and Materials Engineering at IIT Bhubaneswar.
All course codes are verified against kb.course before writing.
"""

import os
import csv

def generate_skills_and_goals():
    courses_path = "data/seed/kb/course.csv"
    with open(courses_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        valid_courses = {row[0].strip() for row in reader if row}

    # 1. Skills (EE + MME)
    skills = [
        # EE Skills
        ("SKILL_CIRCUIT_ANALYSIS", "Circuit Theory & Network Synthesis", "Electrical Core", "Transient response, AC network analysis, two-port networks, resonance, and state equations.", "0-100", "draft_for_review"),
        ("SKILL_SIGNALS_SYSTEMS", "Signals & Linear Systems", "Signal Processing", "Continuous and discrete-time signals, LTI systems, Fourier/Laplace/Z-transforms, convolution.", "0-100", "draft_for_review"),
        ("SKILL_ANALOG_ELECTRONICS", "Analog Electronics & Semiconductor Devices", "Electronics", "Diodes, BJTs, MOSFETs, op-amp circuits, small-signal amplifiers, frequency response.", "0-100", "draft_for_review"),
        ("SKILL_DIGITAL_LOGIC", "Digital Logic & Microprocessors", "Hardware Systems", "Combinational and sequential circuits, FSMs, 8086 microprocessors, timing diagrams.", "0-100", "draft_for_review"),
        ("SKILL_POWER_ELECTRONICS", "Power Electronic Converters & Drives", "Power Engineering", "DC-DC converters, inverters, rectifiers, modulation techniques, gate drivers.", "0-100", "draft_for_review"),
        ("SKILL_POWER_SYSTEMS", "Power System Analysis & Grid Operations", "Power Engineering", "Transmission lines, load flow, fault analysis, stability, economic dispatch.", "0-100", "draft_for_review"),
        ("SKILL_POWER_GRID_CONTROL", "Power System Dynamics & Grid Control", "Power Engineering", "AGC, reactive power control, FACTS, HVDC transmission, and smart grid automation.", "0-100", "draft_for_review"),
        ("SKILL_ELECTRIC_MACHINES", "Electrical Machines & Electromechanics", "Electrical Core", "Transformers, DC machines, induction and synchronous motors, magnetic circuits.", "0-100", "draft_for_review"),
        ("SKILL_CONTROL_SYSTEMS", "Classical & Modern Feedback Control", "Control & Systems", "Root locus, Bode/Nyquist plots, state-space representations, stability margins.", "0-100", "draft_for_review"),
        ("SKILL_EM_FIELDS", "Electromagnetics & Transmission Lines", "Electromagnetics", "Maxwell equations, plane wave propagation, boundary conditions, wave guides.", "0-100", "draft_for_review"),
        ("SKILL_DSP", "Digital Signal Processing & Filtering", "Signal Processing", "DFT, FFT, FIR/IIR filter design, multirate DSP, spectral analysis.", "0-100", "draft_for_review"),
        ("SKILL_VLSI_DESIGN", "CMOS VLSI Design & Verilog", "VLSI & Hardware", "CMOS digital circuits, ASIC flow, timing closure, layout rules, SPICE simulation.", "0-100", "draft_for_review"),
        ("SKILL_EMBEDDED_SYSTEMS", "Embedded Systems & Real-Time Computing", "Embedded Systems", "Microcontrollers, ARM architecture, RTOS, peripheral interfaces (SPI/I2C/UART).", "0-100", "draft_for_review"),
        ("SKILL_PROGRAMMING_DS", "Programming in C & Data Structures", "Computer Science", "Algorithms, arrays, pointers, linked lists, trees, graphs, sorting/searching.", "0-100", "draft_for_review"),
        ("SKILL_PROBABILITY_STATS", "Probability, Statistics & Stochastic Processes", "Mathematics", "Probability distributions, random variables, Markov chains, estimation, stochastic processes.", "0-100", "draft_for_review"),
        ("SKILL_AI_ML", "Machine Learning & Pattern Recognition", "Artificial Intelligence", "Supervised/unsupervised learning, neural networks, optimization, gradient descent.", "0-100", "draft_for_review"),
        ("SKILL_RENEWABLE_ENERGY", "Renewable Energy & Microgrid Architecture", "Renewables", "Solar PV MPPT, wind generation, energy storage systems, islanded microgrids.", "0-100", "draft_for_review"),
        ("SKILL_INSTRUMENTATION", "Instrumentation, Transducers & Sensors", "Measurement", "Signal conditioning, error analysis, strain gauges, piezoelectric/thermal sensors.", "0-100", "draft_for_review"),
        ("SKILL_HIGH_VOLTAGE", "High Voltage Engineering & Insulation", "Power Engineering", "Dielectric breakdown, impulse testing, surge arresters, high voltage test techniques.", "0-100", "draft_for_review"),
        
        # MME Skills
        ("SKILL_THERMODYNAMICS_MAT", "Metallurgical & Materials Thermodynamics", "Thermodynamics", "Free energy, Ellingham diagrams, phase equilibria, solution models, activity, slag equilibria.", "0-100", "draft_for_review"),
        ("SKILL_PHYSICAL_METALLURGY", "Physical Metallurgy & Phase Transformations", "Metallurgy Core", "Crystal structures, defects, diffusion, TTT/CCT diagrams, precipitation hardening, martensite.", "0-100", "draft_for_review"),
        ("SKILL_MATERIALS_PROCESSING", "Materials Processing, Casting & Solidification", "Manufacturing", "Foundry technology, mold design, ingot casting, solidification kinetics, welding metallurgy.", "0-100", "draft_for_review"),
        ("SKILL_MECHANICAL_BEHAVIOR", "Mechanical Behavior, Testing & Fracture", "Mechanical Behavior", "Tensile testing, creep, fatigue, hardness, impact toughness, fracture mechanics, dislocation theory.", "0-100", "draft_for_review"),
        ("SKILL_CORROSION_SURFACE", "Corrosion & Surface Engineering", "Degradation & Protection", "Electrochemical kinetics, Pourbaix diagrams, galvanic/pitting corrosion, coatings, cathodic protection.", "0-100", "draft_for_review"),
        ("SKILL_IRON_STEELMAKING", "Ironmaking & Steelmaking Technology", "Process Metallurgy", "Blast furnace reactions, DRI, BOF/EAF steelmaking, ladle refining, degassing, continuous casting.", "0-100", "draft_for_review"),
        ("SKILL_MATERIALS_CHAR", "Materials Characterization & Microscopy", "Characterization", "Optical microscopy, SEM, TEM, EDS, X-ray diffraction (XRD), AFM, thermal analysis (DSC/TGA).", "0-100", "draft_for_review"),
        ("SKILL_POWDER_METALLURGY", "Powder Metallurgy & Sintering", "Manufacturing", "Powder synthesis, compaction, solid/liquid state sintering, hot isostatic pressing (HIP), porous metals.", "0-100", "draft_for_review"),
        ("SKILL_BIOMATERIALS", "Biomaterials & Tissue Scaffolds", "Biomaterials", "Biocompatibility, bioimplants (Ti/Mg/Zn), bone scaffolds, 3D bioprinting, degradation mechanics.", "0-100", "draft_for_review"),
        ("SKILL_ENERGY_MATERIALS", "Energy Materials & Storage Systems", "Functional Materials", "Li-ion battery electrodes, solid electrolytes, thermoelectrics, hydrogen storage alloys, supercapacitors.", "0-100", "draft_for_review"),
        ("SKILL_COMPOSITES_NANO", "Composites & Nanostructured Materials", "Advanced Materials", "Metal matrix composites (MMCs), ceramic composites, nanocomposites, carbon nanomaterials.", "0-100", "draft_for_review"),
        ("SKILL_SIMULATION_MODELING", "Computational Materials Science & Modeling", "Computation", "Phase-field modeling, molecular dynamics, DFT calculations, finite element modeling (CPFEM/VPSC).", "0-100", "draft_for_review"),
        ("SKILL_MINERAL_PROCESSING", "Mineral Processing & Extractive Metallurgy", "Extractive Metallurgy", "Comminution, flotation, magnetic separation, hydro/pyrometallurgical extraction, tailings management.", "0-100", "draft_for_review")
    ]

    with open("data/seed/kb/skill.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["skill_id", "name", "domain", "description", "level_scale", "status"])
        for s in skills:
            writer.writerow(s)

    # 2. Course Skills
    course_skills = [
        # EE Sem I & II
        ("EE1L001", "SKILL_CIRCUIT_ANALYSIS", 35.0, 1.0, "draft_for_review"),
        ("EE1L001", "SKILL_ELECTRIC_MACHINES", 25.0, 0.8, "draft_for_review"),
        ("CS1L001", "SKILL_PROGRAMMING_DS", 45.0, 1.0, "draft_for_review"),
        ("EE1P001", "SKILL_CIRCUIT_ANALYSIS", 30.0, 0.8, "draft_for_review"),
        ("CS1P001", "SKILL_PROGRAMMING_DS", 40.0, 0.8, "draft_for_review"),
        
        # EE Sem III
        ("EC2L001", "SKILL_ANALOG_ELECTRONICS", 55.0, 1.0, "draft_for_review"),
        ("EC2P001", "SKILL_ANALOG_ELECTRONICS", 50.0, 0.8, "draft_for_review"),
        ("EC2L002", "SKILL_SIGNALS_SYSTEMS", 60.0, 1.0, "draft_for_review"),
        ("EC2P002", "SKILL_SIGNALS_SYSTEMS", 55.0, 0.8, "draft_for_review"),
        ("MA2L003", "SKILL_PROBABILITY_STATS", 65.0, 1.0, "draft_for_review"),
        
        # EE Sem IV
        ("EE2L001", "SKILL_CIRCUIT_ANALYSIS", 75.0, 1.0, "draft_for_review"),
        ("EE2L003", "SKILL_ELECTRIC_MACHINES", 70.0, 1.0, "draft_for_review"),
        ("EC2L006", "SKILL_EM_FIELDS", 70.0, 1.0, "draft_for_review"),
        ("EE2L002", "SKILL_ANALOG_ELECTRONICS", 70.0, 1.0, "draft_for_review"),
        ("EE2P003", "SKILL_ELECTRIC_MACHINES", 65.0, 0.8, "draft_for_review"),

        # EE Sem V
        ("EE3L007", "SKILL_ELECTRIC_MACHINES", 85.0, 1.0, "draft_for_review"),
        ("EE3L008", "SKILL_POWER_ELECTRONICS", 80.0, 1.0, "draft_for_review"),
        ("EE3L003", "SKILL_CONTROL_SYSTEMS", 80.0, 1.0, "draft_for_review"),
        ("EC3L003", "SKILL_DIGITAL_LOGIC", 75.0, 1.0, "draft_for_review"),
        ("EE3P006", "SKILL_POWER_ELECTRONICS", 75.0, 0.8, "draft_for_review"),
        ("EE3P002", "SKILL_CONTROL_SYSTEMS", 75.0, 0.8, "draft_for_review"),
        ("EC3P002", "SKILL_DIGITAL_LOGIC", 70.0, 0.8, "draft_for_review"),

        # EE Sem VI
        ("EE3L004", "SKILL_POWER_SYSTEMS", 85.0, 1.0, "draft_for_review"),
        ("EE3L005", "SKILL_INSTRUMENTATION", 80.0, 1.0, "draft_for_review"),
        ("EE3P004", "SKILL_POWER_SYSTEMS", 80.0, 0.8, "draft_for_review"),
        ("EE3P005", "SKILL_INSTRUMENTATION", 75.0, 0.8, "draft_for_review"),

        # EE Sem VII & VIII
        ("EE4L003", "SKILL_POWER_ELECTRONICS", 90.0, 1.0, "draft_for_review"),
        ("EE4L004", "SKILL_POWER_SYSTEMS", 90.0, 1.0, "draft_for_review"),
        ("EE4L005", "SKILL_CONTROL_SYSTEMS", 90.0, 1.0, "draft_for_review"),
        ("EE4L006", "SKILL_RENEWABLE_ENERGY", 85.0, 1.0, "draft_for_review"),
        ("EC4L003", "SKILL_VLSI_DESIGN", 85.0, 1.0, "draft_for_review"),
        ("EC6L005", "SKILL_EMBEDDED_SYSTEMS", 85.0, 1.0, "draft_for_review"),
        ("CS6L001", "SKILL_AI_ML", 85.0, 1.0, "draft_for_review"),

        # MME Sem III
        ("EC2L005", "SKILL_ANALOG_ELECTRONICS", 60.0, 1.0, "draft_for_review"),
        ("EC2P005", "SKILL_ANALOG_ELECTRONICS", 55.0, 0.8, "draft_for_review"),
        ("ID2L001", "SKILL_PHYSICAL_METALLURGY", 50.0, 0.8, "draft_for_review"),
        ("ID2L002", "SKILL_BIOMATERIALS", 40.0, 0.7, "draft_for_review"),
        ("MA2L007", "SKILL_SIMULATION_MODELING", 60.0, 0.9, "draft_for_review"),
        ("ML2L002", "SKILL_THERMODYNAMICS_MAT", 75.0, 1.0, "draft_for_review"),
        ("ML2P001", "SKILL_MATERIALS_CHAR", 55.0, 0.8, "draft_for_review"),
        
        # MME Sem IV
        ("ID2L003", "SKILL_MINERAL_PROCESSING", 50.0, 0.7, "draft_for_review"),
        ("ML2L003", "SKILL_MATERIALS_PROCESSING", 75.0, 1.0, "draft_for_review"),
        ("ML2P002", "SKILL_MATERIALS_PROCESSING", 70.0, 0.8, "draft_for_review"),
        ("ML2L004", "SKILL_THERMODYNAMICS_MAT", 75.0, 0.9, "draft_for_review"),
        ("ML2L004", "SKILL_IRON_STEELMAKING", 60.0, 0.7, "draft_for_review"),
        ("ML2L005", "SKILL_PHYSICAL_METALLURGY", 80.0, 1.0, "draft_for_review"),
        ("ML2P003", "SKILL_PHYSICAL_METALLURGY", 75.0, 0.8, "draft_for_review"),
        ("ML2P004", "SKILL_THERMODYNAMICS_MAT", 70.0, 0.8, "draft_for_review"),

        # MME Laterals
        ("ML2L006", "SKILL_COMPOSITES_NANO", 75.0, 0.9, "draft_for_review"),
        ("ML3L011", "SKILL_COMPOSITES_NANO", 75.0, 0.9, "draft_for_review"),
        ("ML3L012", "SKILL_MINERAL_PROCESSING", 75.0, 0.9, "draft_for_review"),

        # MME Sem V
        ("ML3L001", "SKILL_MINERAL_PROCESSING", 80.0, 1.0, "draft_for_review"),
        ("ML3L002", "SKILL_CORROSION_SURFACE", 80.0, 1.0, "draft_for_review"),
        ("ML3L003", "SKILL_MECHANICAL_BEHAVIOR", 80.0, 1.0, "draft_for_review"),
        ("ML3P001", "SKILL_MECHANICAL_BEHAVIOR", 75.0, 0.8, "draft_for_review"),
        ("ML3L004", "SKILL_PHYSICAL_METALLURGY", 85.0, 1.0, "draft_for_review"),
        ("ML3L005", "SKILL_IRON_STEELMAKING", 75.0, 0.9, "draft_for_review"),
        ("ML3L005", "SKILL_THERMODYNAMICS_MAT", 70.0, 0.8, "draft_for_review"),

        # MME Sem VI
        ("ML3L006", "SKILL_MATERIALS_CHAR", 85.0, 1.0, "draft_for_review"),
        ("ML3P002", "SKILL_MATERIALS_CHAR", 80.0, 0.8, "draft_for_review"),
        ("ML3L007", "SKILL_IRON_STEELMAKING", 90.0, 1.0, "draft_for_review"),
        ("ML3L008", "SKILL_MECHANICAL_BEHAVIOR", 85.0, 1.0, "draft_for_review"),
        ("ML3L009", "SKILL_SIMULATION_MODELING", 80.0, 1.0, "draft_for_review"),
        ("ML3P003", "SKILL_SIMULATION_MODELING", 75.0, 0.8, "draft_for_review"),

        # MME Sem VII & Electives
        ("ML4L001", "SKILL_PHYSICAL_METALLURGY", 80.0, 0.9, "draft_for_review"),
        ("ML4L002", "SKILL_ENERGY_MATERIALS", 75.0, 0.8, "draft_for_review"),
        ("ML4L003", "SKILL_COMPOSITES_NANO", 80.0, 1.0, "draft_for_review"),
        ("ML4P001", "SKILL_MATERIALS_CHAR", 85.0, 0.8, "draft_for_review"),
        ("ML4L001E", "SKILL_MATERIALS_PROCESSING", 85.0, 1.0, "draft_for_review"),
        ("ML4L002E", "SKILL_MATERIALS_PROCESSING", 85.0, 1.0, "draft_for_review"),
        ("ML4L003E", "SKILL_CORROSION_SURFACE", 85.0, 1.0, "draft_for_review"),
        ("ML4L004", "SKILL_POWDER_METALLURGY", 85.0, 1.0, "draft_for_review"),
        ("ML4L005", "SKILL_MECHANICAL_BEHAVIOR", 80.0, 0.8, "draft_for_review"),
        ("ML4L006", "SKILL_ENERGY_MATERIALS", 85.0, 1.0, "draft_for_review"),
        ("ML4L007", "SKILL_MATERIALS_CHAR", 90.0, 1.0, "draft_for_review"),
        ("ML4L010", "SKILL_COMPOSITES_NANO", 85.0, 1.0, "draft_for_review"),
        ("ML4L011", "SKILL_BIOMATERIALS", 90.0, 1.0, "draft_for_review"),
        ("ML4L013", "SKILL_MINERAL_PROCESSING", 85.0, 1.0, "draft_for_review"),
        ("ML4L014", "SKILL_IRON_STEELMAKING", 80.0, 0.9, "draft_for_review"),
        ("ML4L015", "SKILL_CORROSION_SURFACE", 80.0, 0.9, "draft_for_review")
    ]

    # Validate against valid_courses
    validated_course_skills = []
    for cs in course_skills:
        if cs[0] in valid_courses:
            validated_course_skills.append(cs)
        else:
            print(f"Skipping course_skill mapping for unindexed course: {cs[0]}")

    with open("data/seed/kb/course_skill.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["course_code", "skill_id", "level_taught", "weight", "status"])
        for cs in validated_course_skills:
            writer.writerow(cs)

    # 3. Goals (EE + MME)
    goals = [
        # EE Goals
        ("GOAL_EE_CORE_VLSI", "Core VLSI & Semiconductor Engineering", "career", "Industry core roles in IC design, FPGA/ASIC verification, semiconductor device modeling, and embedded hardware architectures.", "draft_for_review"),
        ("GOAL_EE_CORE_POWER", "Power Systems, Smart Grid & Renewable Energy", "career", "Industry and utility core roles in smart grid operations, renewable energy integration, power system protection, and EV drivetrain charging.", "draft_for_review"),
        ("GOAL_EE_RES_HIGHER_STUDIES", "Higher Studies & Research in Electrical Sciences", "higher_studies", "Preparation for Ph.D. / MS research tracks, funded academic lab projects, international research fellowships, and faculty lab exploration.", "draft_for_review"),
        ("GOAL_CROSS_SDE_DATA", "Software Engineering & Data Science Transition", "career", "Cross-branch transition to software development, machine learning, and systems engineering leveraging CS minor courses and algorithmic electives.", "draft_for_review"),
        ("GOAL_UPSC_COMPETITIVE", "Public Services & Competitive Examinations", "competitive_exam", "Preparation for UPSC CSE, IES (ESE), GATE, and PSU recruitments while maintaining steady degree completion and controlled cognitive workload.", "draft_for_review"),
        ("GOAL_TECH_STARTUP", "Deep-Tech Entrepreneurship & Venture Development", "startup", "Building deep-tech hardware/software startups, prototype commercialization, and incubation balancing academic obligations.", "draft_for_review"),

        # MME Goals
        ("GOAL_MM_PROCESS_ENGINEER", "Process Metallurgist (Iron & Steelmaking / Primary Metals)", "career", "Lead plant operations, DRI/H2 reduction decarbonization, and process control in integrated steelworks and metal extraction plants (Tata Steel, JSW, SAIL).", "draft_for_review"),
        ("GOAL_MM_ADVANCED_MATERIALS", "Advanced Materials R&D (Aerospace, Defense & HEAs)", "career", "R&D engineer developing high-entropy alloys, structural metamaterials, light alloy components, and high-temperature coatings (DRDO, ISRO, DMRL).", "draft_for_review"),
        ("GOAL_MM_BIOMATERIALS", "Biomaterials & Medical Device Engineer", "career", "Design biodegradable metallic orthopedic implants, bone-regeneration scaffolds, and biocompatible medical devices.", "draft_for_review"),
        ("GOAL_MM_ENERGY_MATERIALS", "Energy Materials & Battery Technologies", "career", "Design advanced materials for lithium-ion battery electrodes, solid electrolytes, thermoelectric devices, and hydrogen storage systems.", "draft_for_review"),
        ("GOAL_MM_RES_HIGHER_STUDIES", "Higher Studies & Research in Materials Science", "higher_studies", "Preparation for Ph.D. and MS research in premier international institutes and IIT laboratories in metallurgy and materials science.", "draft_for_review")
    ]
    with open("data/seed/kb/goal.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["goal_id", "name", "category", "description", "status"])
        for g in goals:
            writer.writerow(g)

    # 4. Goal Skill Requirements
    goal_skill_reqs = [
        # EE VLSI
        ("GOAL_EE_CORE_VLSI", "SKILL_VLSI_DESIGN", 80.0, 1.0, "draft_for_review"),
        ("GOAL_EE_CORE_VLSI", "SKILL_DIGITAL_LOGIC", 75.0, 0.9, "draft_for_review"),
        ("GOAL_EE_CORE_VLSI", "SKILL_ANALOG_ELECTRONICS", 70.0, 0.8, "draft_for_review"),
        ("GOAL_EE_CORE_VLSI", "SKILL_EMBEDDED_SYSTEMS", 70.0, 0.7, "draft_for_review"),

        # EE Power
        ("GOAL_EE_CORE_POWER", "SKILL_POWER_SYSTEMS", 80.0, 1.0, "draft_for_review"),
        ("GOAL_EE_CORE_POWER", "SKILL_POWER_ELECTRONICS", 80.0, 0.9, "draft_for_review"),
        ("GOAL_EE_CORE_POWER", "SKILL_POWER_GRID_CONTROL", 75.0, 0.9, "draft_for_review"),
        ("GOAL_EE_CORE_POWER", "SKILL_ELECTRIC_MACHINES", 75.0, 0.8, "draft_for_review"),
        ("GOAL_EE_CORE_POWER", "SKILL_RENEWABLE_ENERGY", 70.0, 0.7, "draft_for_review"),

        # EE Research / Higher studies
        ("GOAL_EE_RES_HIGHER_STUDIES", "SKILL_SIGNALS_SYSTEMS", 80.0, 1.0, "draft_for_review"),
        ("GOAL_EE_RES_HIGHER_STUDIES", "SKILL_CONTROL_SYSTEMS", 80.0, 0.9, "draft_for_review"),
        ("GOAL_EE_RES_HIGHER_STUDIES", "SKILL_EM_FIELDS", 75.0, 0.8, "draft_for_review"),
        ("GOAL_EE_RES_HIGHER_STUDIES", "SKILL_PROBABILITY_STATS", 75.0, 0.8, "draft_for_review"),

        # Software / Data Science Transition
        ("GOAL_CROSS_SDE_DATA", "SKILL_PROGRAMMING_DS", 85.0, 1.0, "draft_for_review"),
        ("GOAL_CROSS_SDE_DATA", "SKILL_AI_ML", 80.0, 1.0, "draft_for_review"),
        ("GOAL_CROSS_SDE_DATA", "SKILL_PROBABILITY_STATS", 75.0, 0.8, "draft_for_review"),

        # UPSC / Competitive
        ("GOAL_UPSC_COMPETITIVE", "SKILL_CIRCUIT_ANALYSIS", 75.0, 1.0, "draft_for_review"),
        ("GOAL_UPSC_COMPETITIVE", "SKILL_POWER_SYSTEMS", 75.0, 0.9, "draft_for_review"),
        ("GOAL_UPSC_COMPETITIVE", "SKILL_CONTROL_SYSTEMS", 75.0, 0.9, "draft_for_review"),
        ("GOAL_UPSC_COMPETITIVE", "SKILL_ELECTRIC_MACHINES", 75.0, 0.8, "draft_for_review"),

        # Tech Startup
        ("GOAL_TECH_STARTUP", "SKILL_EMBEDDED_SYSTEMS", 75.0, 1.0, "draft_for_review"),
        ("GOAL_TECH_STARTUP", "SKILL_POWER_ELECTRONICS", 70.0, 0.8, "draft_for_review"),
        ("GOAL_TECH_STARTUP", "SKILL_AI_ML", 70.0, 0.8, "draft_for_review"),

        # MME Process Metallurgist
        ("GOAL_MM_PROCESS_ENGINEER", "SKILL_IRON_STEELMAKING", 85.0, 1.0, "draft_for_review"),
        ("GOAL_MM_PROCESS_ENGINEER", "SKILL_THERMODYNAMICS_MAT", 80.0, 0.9, "draft_for_review"),
        ("GOAL_MM_PROCESS_ENGINEER", "SKILL_MINERAL_PROCESSING", 75.0, 0.8, "draft_for_review"),
        ("GOAL_MM_PROCESS_ENGINEER", "SKILL_MATERIALS_PROCESSING", 75.0, 0.8, "draft_for_review"),

        # MME Advanced Materials
        ("GOAL_MM_ADVANCED_MATERIALS", "SKILL_PHYSICAL_METALLURGY", 85.0, 1.0, "draft_for_review"),
        ("GOAL_MM_ADVANCED_MATERIALS", "SKILL_MECHANICAL_BEHAVIOR", 80.0, 0.9, "draft_for_review"),
        ("GOAL_MM_ADVANCED_MATERIALS", "SKILL_COMPOSITES_NANO", 80.0, 0.8, "draft_for_review"),
        ("GOAL_MM_ADVANCED_MATERIALS", "SKILL_MATERIALS_CHAR", 80.0, 0.8, "draft_for_review"),

        # MME Biomaterials
        ("GOAL_MM_BIOMATERIALS", "SKILL_BIOMATERIALS", 85.0, 1.0, "draft_for_review"),
        ("GOAL_MM_BIOMATERIALS", "SKILL_CORROSION_SURFACE", 80.0, 0.9, "draft_for_review"),
        ("GOAL_MM_BIOMATERIALS", "SKILL_MATERIALS_CHAR", 75.0, 0.8, "draft_for_review"),

        # MME Energy Materials
        ("GOAL_MM_ENERGY_MATERIALS", "SKILL_ENERGY_MATERIALS", 85.0, 1.0, "draft_for_review"),
        ("GOAL_MM_ENERGY_MATERIALS", "SKILL_THERMODYNAMICS_MAT", 80.0, 0.9, "draft_for_review"),
        ("GOAL_MM_ENERGY_MATERIALS", "SKILL_MATERIALS_CHAR", 75.0, 0.8, "draft_for_review"),

        # MME Research / Higher Studies
        ("GOAL_MM_RES_HIGHER_STUDIES", "SKILL_PHYSICAL_METALLURGY", 85.0, 1.0, "draft_for_review"),
        ("GOAL_MM_RES_HIGHER_STUDIES", "SKILL_SIMULATION_MODELING", 80.0, 0.9, "draft_for_review"),
        ("GOAL_MM_RES_HIGHER_STUDIES", "SKILL_MATERIALS_CHAR", 85.0, 0.9, "draft_for_review"),
        ("GOAL_MM_RES_HIGHER_STUDIES", "SKILL_THERMODYNAMICS_MAT", 80.0, 0.8, "draft_for_review")
    ]
    with open("data/seed/kb/goal_skill_requirement.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["goal_id", "skill_id", "required_level", "importance", "status"])
        for gsr in goal_skill_reqs:
            writer.writerow(gsr)

    print(f"Generated unified skills ({len(skills)}), course-skill links ({len(validated_course_skills)}), goals ({len(goals)}), and goal requirements ({len(goal_skill_reqs)}) with status='draft_for_review'. All validated against kb.course.")

if __name__ == "__main__":
    generate_skills_and_goals()
