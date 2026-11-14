import os
import re
import csv
import sys
import openpyxl

# Set UTF-8 encoding for standard output if supported
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REFERENCE_DATE = "2026-11-14"
FILE_A = "top7_iit_fests_26-27.xlsx"
FILE_B = "ai_ml_hackathons_and_top7_iit_fests_2026-2027.xlsx"
OUTPUT_DIR = "output"

# Competition rules
COMP_PLATFORMS = {"Kaggle", "Zindi", "DrivenData", "Codabench / Synapse"}
COMP_PREFIXES = [
    "Analytics Vidhya DataHack Sprints",
    "MachineHack MLDS Enterprise AI Sprints",
    "Amazon ML Challenge India",
    "Flipkart GRiD & HackOn with Amazon",
    "Microsoft Imagine Cup 2027",
    "Google Solution Challenge",
    "IndiaAI Innovation Challenge",
    "QuikCPQ AI Innovation Challenge 2027"
]

# Timeline parser mappings
TIMELINE_PARSER_MAP = {
    # Fests
    "Dec 16–18, 2026": ("Dec 2026", "2026-12", "2026-12", "EVENT_WINDOW"),
    "Dec 16-18, 2026": ("Dec 2026", "2026-12", "2026-12", "EVENT_WINDOW"),
    "Jan 2–6, 2027": ("Jan 2027", "2027-01", "2027-01", "EVENT_WINDOW"),
    "Jan 2-6, 2027": ("Jan 2027", "2027-01", "2027-01", "EVENT_WINDOW"),
    "Mid-January 2027": ("Jan 2027", "2027-01", "2027-01", "APPROXIMATE"),
    "Jan 28–31, 2027": ("Jan 2027", "2027-01", "2027-01", "EVENT_WINDOW"),
    "Jan 28-31, 2027": ("Jan 2027", "2027-01", "2027-01", "EVENT_WINDOW"),
    "Late Feb – Early Mar 2027": ("Feb – Mar 2027", "2027-02", "2027-03", "APPROXIMATE"),
    "Late Feb - Early Mar 2027": ("Feb – Mar 2027", "2027-02", "2027-03", "APPROXIMATE"),
    "Mid-March 2027": ("Mar 2027", "2027-03", "2027-03", "APPROXIMATE"),
    "Late August 2027": ("Aug 2027", "2027-08", "2027-08", "APPROXIMATE"),

    # Hackathons & Competitions
    "Deadline: Jan 5, 2027": ("Deadline in Jan 2027", "", "2027-01", "DEADLINE"),
    "Through Jan 2027": ("Open now – Jan 2027", "", "2027-01", "ONGOING_UNTIL"),
    "Merger: Jan 6 | Final: Jan 13, 2027": ("Jan 2027", "2027-01", "2027-01", "MILESTONES"),
    "Mid-December 2026": ("Dec 2026", "2026-12", "2026-12", "APPROXIMATE"),
    "Milestones: Jan & Apr 2027 | Final: Jul 18, 2027": ("Jan – Jul 2027 (milestones Jan & Apr, final Jul 18)", "2027-01", "2027-07", "MILESTONES"),
    "Early 2027": ("Jan – Mar 2027", "2027-01", "2027-03", "APPROXIMATE"),
    "Through Dec 2026": ("Open now – Dec 2026", "", "2026-12", "ONGOING_UNTIL"),
    "Dec 2026 – Q1 2027": ("Dec 2026 – Mar 2027", "2026-12", "2027-03", "APPROXIMATE"),
    "Dec 2026 - Q1 2027": ("Dec 2026 – Mar 2027", "2026-12", "2027-03", "APPROXIMATE"),
    "Through Feb 2027": ("Open now – Feb 2027", "", "2027-02", "ONGOING_UNTIL"),
    "Early Dec 2026": ("Dec 2026", "2026-12", "2026-12", "APPROXIMATE"),
    "Deadline: Dec 3, 2026": ("Deadline in Dec 2026", "", "2026-12", "DEADLINE"),
    "Dec 2026 – Q2 2027": ("Dec 2026 – Jun 2027", "2026-12", "2027-06", "APPROXIMATE"),
    "Dec 2026 - Q2 2027": ("Dec 2026 – Jun 2027", "2026-12", "2027-06", "APPROXIMATE"),
    "Deadline: Dec 22, 2026": ("Deadline in Dec 2026", "", "2026-12", "DEADLINE"),
    "Deadline: Dec 11, 2026": ("Deadline in Dec 2026", "", "2026-12", "DEADLINE"),
    "Deadline: Dec 15, 2026": ("Deadline in Dec 2026", "", "2026-12", "DEADLINE"),
    "Dec 5–6, 2026": ("Dec 2026", "2026-12", "2026-12", "EVENT_WINDOW"),
    "Dec 5-6, 2026": ("Dec 2026", "2026-12", "2026-12", "EVENT_WINDOW"),
    "Nov 29 – Dec 6, 2026": ("Nov – Dec 2026", "2026-11", "2026-12", "EVENT_WINDOW"),
    "Nov 29 - Dec 6, 2026": ("Nov – Dec 2026", "2026-11", "2026-12", "EVENT_WINDOW"),
    "Deadline: Dec 7, 2026": ("Deadline in Dec 2026", "", "2026-12", "DEADLINE"),
    "Deadline: Dec 2, 2026": ("Deadline in Dec 2026", "", "2026-12", "DEADLINE"),
    "Deadline: Dec 26, 2026": ("Deadline in Dec 2026", "", "2026-12", "DEADLINE"),
    "Through Mid-Dec 2026": ("Open now – Dec 2026", "", "2026-12", "ONGOING_UNTIL"),
    "Evaluation: Early 2027": ("Jan – Mar 2027", "2027-01", "2027-03", "APPROXIMATE"),
    "December 2026": ("Dec 2026", "2026-12", "2026-12", "EVENT_WINDOW"),
    "Dec 2026 – Jan 2027": ("Dec 2026 – Jan 2027", "2026-12", "2027-01", "EVENT_WINDOW"),
    "Dec 2026 - Jan 2027": ("Dec 2026 – Jan 2027", "2026-12", "2027-01", "EVENT_WINDOW"),
    "Jan 2027": ("Jan 2027", "2027-01", "2027-01", "EVENT_WINDOW"),
    "Opens Dec 1, 2026": ("Opens Dec 2026", "2026-12", "", "OPENS"),
    "Opens Dec 15, 2026": ("Opens Dec 2026", "2026-12", "", "OPENS"),
    "Q1 2027": ("Jan – Mar 2027", "2027-01", "2027-03", "APPROXIMATE"),
    "Dec 2026 – Feb 2027": ("Dec 2026 – Feb 2027", "2026-12", "2027-02", "EVENT_WINDOW"),
    "Dec 2026 - Feb 2027": ("Dec 2026 – Feb 2027", "2026-12", "2027-02", "EVENT_WINDOW"),
    "Feb 11–12, 2027": ("Feb 2027", "2027-02", "2027-02", "EVENT_WINDOW"),
    "Feb 11-12, 2027": ("Feb 2027", "2027-02", "2027-02", "EVENT_WINDOW"),
    "Opens Feb 15, 2027": ("Opens Feb 2027", "2027-02", "", "OPENS"),
    "Feb – Mar 2027": ("Feb – Mar 2027", "2027-02", "2027-03", "EVENT_WINDOW"),
    "Feb - Mar 2027": ("Feb – Mar 2027", "2027-02", "2027-03", "EVENT_WINDOW"),
    "Mar 12–13, 2027": ("Mar 2027", "2027-03", "2027-03", "EVENT_WINDOW"),
    "Mar 12-13, 2027": ("Mar 2027", "2027-03", "2027-03", "EVENT_WINDOW"),
    "Regionals: Jan – Mar 2027": ("Jan – Mar 2027", "2027-01", "2027-03", "EVENT_WINDOW"),
    "Regionals: Jan - Mar 2027": ("Jan – Mar 2027", "2027-01", "2027-03", "EVENT_WINDOW"),
    "Jan – Mar 2027": ("Jan – Mar 2027", "2027-01", "2027-03", "EVENT_WINDOW"),
    "Jan - Mar 2027": ("Jan – Mar 2027", "2027-01", "2027-03", "EVENT_WINDOW"),
    "Apr – Jun 2027": ("Apr – Jun 2027", "2027-04", "2027-06", "EVENT_WINDOW"),
    "Apr - Jun 2027": ("Apr – Jun 2027", "2027-04", "2027-06", "EVENT_WINDOW"),
    "Mid 2027": ("Jun – Jul 2027", "2027-06", "2027-07", "APPROXIMATE"),
    "Mid – Late 2027": ("Jun – Sep 2027", "2027-06", "2027-09", "APPROXIMATE"),
    "Mid - Late 2027": ("Jun – Sep 2027", "2027-06", "2027-09", "APPROXIMATE"),
    "Late 2027 (Dec)": ("Dec 2027", "2027-12", "2027-12", "APPROXIMATE"),
}

# Previous year parser mappings
PREV_YEAR_PARSER_MAP = {
    # New editions
    "New Series (2026–27)": ("No previous edition (new)", True),
    "New Series (2026-27)": ("No previous edition (new)", True),
    "New Series (2026)": ("No previous edition (new)", True),
    "New Edition (2026)": ("No previous edition (new)", True),
    "New 9-Month Track": ("No previous edition (new)", True),

    # Fests
    "Dec 16–18, 2025": ("Dec 2025", False),
    "Dec 16-18, 2025": ("Dec 2025", False),
    "Jan 3–7, 2026": ("Jan 2026", False),
    "Jan 3-7, 2026": ("Jan 2026", False),
    "Jan 16–18, 2026": ("Jan 2026", False),
    "Jan 16-18, 2026": ("Jan 2026", False),
    "Jan 29 – Feb 1, 2026": ("Jan – Feb 2026", False),
    "Jan 29 - Feb 1, 2026": ("Jan – Feb 2026", False),
    "Feb 27 – Mar 1, 2026": ("Feb – Mar 2026", False),
    "Feb 27 - Mar 1, 2026": ("Feb – Mar 2026", False),
    "Mar 13–15, 2026": ("Mar 2026", False),
    "Mar 13-15, 2026": ("Mar 2026", False),
    "Aug 28–30, 2026": ("Aug 2026", False),
    "Aug 28-30, 2026": ("Aug 2026", False),

    # Hackathons
    "Oct 2025 – Jan 2026": ("Oct 2025 – Jan 2026", False),
    "Oct 2025 - Jan 2026": ("Oct 2025 – Jan 2026", False),
    "Late 2025": ("Oct – Dec 2025", False),
    "Early 2026": ("Jan – Mar 2026", False),
    "Jan 2026": ("Jan 2026", False),
    "Nov – Dec 2025": ("Nov – Dec 2025", False),
    "Nov - Dec 2025": ("Nov – Dec 2025", False),
    "Dec 2025": ("Dec 2025", False),
    "Oct – Dec 2025": ("Oct – Dec 2025", False),
    "Oct - Dec 2025": ("Oct – Dec 2025", False),
    "Quarterly (2025–26)": ("Quarterly through 2025–26", False),
    "Quarterly (2025-26)": ("Quarterly through 2025–26", False),
    "Jan – Feb 2026": ("Jan – Feb 2026", False),
    "Jan - Feb 2026": ("Jan – Feb 2026", False),
    "December 2025": ("Dec 2025", False),
    "Feb 2026": ("Feb 2026", False),
    "Feb – Mar 2026": ("Feb – Mar 2026", False),
    "Feb - Mar 2026": ("Feb – Mar 2026", False),
    "Mar 2026": ("Mar 2026", False),
    "Jan – Mar 2026": ("Jan – Mar 2026", False),
    "Jan - Mar 2026": ("Jan – Mar 2026", False),
    "Apr – Jun 2026": ("Apr – Jun 2026", False),
    "Apr - Jun 2026": ("Apr – Jun 2026", False),
    "Mid 2026": ("Jun – Jul 2026", False),
    "Jul – Sep 2026": ("Jul – Sep 2026", False),
    "Jul - Sep 2026": ("Jul – Sep 2026", False),
    "Dec 2026": ("Dec 2026", False),
}

# Domain & Phase mapping for 04_domain_to_phase_map.csv
# Structure: key = (category, event_name)
DOMAIN_MAP_METADATA = {
    # Fests
    ("FEST", "Techfest"): ("Robotics & Physical AI", "0_Foundations", False, "Features international robotics competitions, robowars, and AI/ML hackathons for broad student exposure."),
    ("FEST", "Shaastra"): ("General AI/ML & Full-Stack", "0_Foundations", False, "Offers data science challenges, quant and coding contests, and flagship tech summit exposure."),
    ("FEST", "Kshitij (KTJ)"): ("Robotics & Physical AI", "0_Foundations", False, "Showcases autonomous robotics events and student AI/ML engineering exhibitions."),
    ("FEST", "Techkriti"): ("Robotics & Physical AI", "0_Foundations", False, "Includes algorithmic and ML competitions alongside IARC robotics and aeromodelling challenges."),
    ("FEST", "Tryst"): ("Generative AI & LLMs", "0_Foundations", False, "Focuses on generative AI and deep tech hackathons for campus innovation."),
    ("FEST", "Cognizance"): ("General AI/ML & Full-Stack", "0_Foundations", False, "Provides data analytics, FinTech, and flagship AI/ML hackathon exposure."),
    ("FEST", "Techniche"): ("Robotics & Physical AI", "0_Foundations", False, "Features flagship Escalade robotics and artificial intelligence student competitions."),

    # Kaggle
    ("COMPETITION", "Google – Agent Harness on Physical-Engineering's Last Exam"): ("Agents", "2_Deep_Learning", False, "Requires autonomous agent frameworks applied to complex physical engineering benchmark examinations."),
    ("COMPETITION", "Optimise Quantum Circuits (Google Quantum AI)"): ("Quantum & Optimisation", "2_Deep_Learning", False, "Involves quantum circuit optimization utilizing agentic artificial intelligence techniques."),
    ("COMPETITION", "NFL Big Data Bowl 2027"): ("Time-Series & Forecasting", "1_Classical_ML", False, "Requires tracking data analysis and predictive modeling using player sensor metrics."),
    ("COMPETITION", "Name That LLM"): ("Generative AI & LLMs", "2_Deep_Learning", False, "Focuses on black-box LLM auditing and output distribution provenance classification."),
    ("COMPETITION", "Predict 2D Chemical Structures From Mass Spectra (Enveda)"): ("Healthcare & Bio", "1_Classical_ML", False, "Applies ranking algorithms and computational chemistry to mass spectrometry data."),
    ("COMPETITION", "Squares in Squares (Optimal Square Packing)"): ("Quantum & Optimisation", "2_Deep_Learning", False, "Combines reinforcement learning and mathematical optimization to solve optimal square packing."),
    ("COMPETITION", "ISU-Challenge 2027 (ICSE 2027)"): ("Computer Vision", "2_Deep_Learning", False, "Involves vision-language multimodal models for in-cabin vehicle scene understanding."),
    ("COMPETITION", "RetailAction Challenge (PRAW @ WACV 2027)"): ("Computer Vision", "2_Deep_Learning", False, "Focuses on spatio-temporal video action detection using deep computer vision."),

    # Zindi
    ("COMPETITION", "GenAI for Good Challenge: Cities Edition (Phase 1)"): ("Generative AI & LLMs", "2_Deep_Learning", False, "Applies generative AI models to solve civic and urban sustainability challenges."),
    ("COMPETITION", "TelcoRetrieve Challenge"): ("RAG & NLP", "2_Deep_Learning", False, "Requires retrieval-augmented generation architectures grounded in telecommunications technical specifications."),
    ("COMPETITION", "AI Agents for RAN Challenge"): ("Agents", "2_Deep_Learning", False, "Develops autonomous decision-making AI agents for radio access network optimization."),
    ("COMPETITION", "AMD Global Physical AI Behavioral Safety Challenge"): ("Robotics & Physical AI", "2_Deep_Learning", False, "Models physical AI behavioral safety and simulation control for hardware acceleration."),
    ("COMPETITION", "Green Rising Methane Innovation Challenge"): ("Climate & Sustainability", "1_Classical_ML", False, "Applies predictive machine learning to model environmental methane emissions and mitigation."),
    ("COMPETITION", "Build Speech Recognition Systems for Caribbean Voices"): ("Speech & Audio", "2_Deep_Learning", False, "Constructs acoustic and language models for accented regional speech recognition."),
    ("COMPETITION", "Underwater Vessel Noise Challenge"): ("Speech & Audio", "2_Deep_Learning", False, "Analyzes underwater hydrophone acoustics using signal processing and deep neural representations."),

    # DrivenData
    ("COMPETITION", "GEMS Prize Challenge (U.S. Dept. of Energy)"): ("Climate & Sustainability", "1_Classical_ML", False, "Builds data-driven predictive models for energy grid resilience and earth systems."),
    ("COMPETITION", "Mozilla Data Collective Series (Challenges 2 & 3)"): ("Social Impact & Governance", "2_Deep_Learning", False, "Focuses on open multilingual datasets and public-interest artificial intelligence applications."),

    # Devpost
    ("HACKATHON", "Codegeist 2026: Build with Context (Atlassian)"): ("Enterprise/Cloud AI", "2_Deep_Learning", False, "Builds enterprise AI integrations and contextual productivity apps on Atlassian Forge."),
    ("HACKATHON", "AWS MSP AI Hackathon"): ("Enterprise/Cloud AI", "2_Deep_Learning", False, "Develops cloud-native enterprise AI architectures leveraging managed cloud AI services."),
    ("HACKATHON", "QNX Global Hackathon"): ("Robotics & Physical AI", "2_Deep_Learning", False, "Integrates edge AI inference into real-time automotive embedded operating systems."),
    ("HACKATHON", "Hack AI x Stan"): ("General AI/ML & Full-Stack", "2_Deep_Learning", False, "Builds full-stack consumer AI products in a competitive weekend hackathon format."),
    ("HACKATHON", "The Dawn of Superintelligence | Kaya AI Grand Challenge"): ("Generative AI & LLMs", "2_Deep_Learning", False, "Explores frontier applied intelligence and multimodal generative models for real-world tasks."),
    ("HACKATHON", "AI for Medicine: A Global Student Hackathon"): ("Healthcare & Bio", "1_Classical_ML", True, "Student hackathon focused on developing accessible machine learning solutions for medicine."),
    ("HACKATHON", "ML Empowerment Build Challenge 4.0"): ("General AI/ML & Full-Stack", "1_Classical_ML", True, "Student challenge designed for building introductory applied machine learning applications."),
    ("HACKATHON", "Terminal 3 Build+Scale Agent Micro Grant"): ("Agents", "2_Deep_Learning", False, "Funds development and scaling of autonomous agentic AI workflows and tools."),

    # Codabench / Synapse
    ("COMPETITION", "CrunchDAO – Predict Cross-sectional Equity Returns"): ("Quant Finance", "1_Classical_ML", False, "Applies statistical modeling and tabular ML to forecast cross-sectional stock returns."),
    ("COMPETITION", "Domain-Specific Question Answering with LLMs (IEEE CIS)"): ("RAG & NLP", "2_Deep_Learning", False, "Evaluates LLM domain-specific question answering and retrieval-augmented verification methods."),
    ("COMPETITION", "PhyRC 2027: Robot-Assisted Dressing in Simulation (ICRA)"): ("Robotics & Physical AI", "2_Deep_Learning", False, "Combines 3D spatial vision, physics simulation, and robotic manipulation trajectory control."),
    ("COMPETITION", "SemEval-2027 Task 2: DiCo-NLI"): ("RAG & NLP", "2_Deep_Learning", False, "Involves natural language inference and semantic reasoning across multilingual textual datasets."),
    ("COMPETITION", "Predict Cognitive Outcomes from Digital Clock Drawings (ISMB)"): ("Healthcare & Bio", "1_Classical_ML", False, "Predicts cognitive impairment using digital pen stroke time-series and tabular features."),

    # India Circuit / National
    ("HACKATHON", "Smart India Hackathon (SIH) 2026 Grand Finale"): ("Social Impact & Governance", "1_Classical_ML", False, "National hackathon addressing public sector challenges and governance software with AI."),
    ("HACKATHON", "GreenMind Sustainable AI Hackathon 2.0"): ("Climate & Sustainability", "1_Classical_ML", False, "Builds sustainable machine learning algorithms to solve environmental and resource challenges."),
    ("HACKATHON", "Homingo Hack Days"): ("Agents", "2_Deep_Learning", False, "Sprint focused on rapid prototyping of agentic systems and LLM applications."),
    ("HACKATHON", "CyberPeace ISR Innovation Hackathon (IIT Madras)"): ("Cybersecurity", "1_Classical_ML", False, "Develops AI algorithms for anomaly detection, cyber defense, and online information resilience."),
    ("HACKATHON", "VBYLD 2027: Hack for Social Cause (MoYAS & IIT Bombay)"): ("Social Impact & Governance", "1_Classical_ML", False, "Applies artificial intelligence to grassroots national development and social welfare causes."),
    ("HACKATHON", "Health Hackathon 3.0 (VIT Bhopal × Johns Hopkins)"): ("Healthcare & Bio", "2_Deep_Learning", False, "Develops deep learning and biomedical engineering solutions for clinical diagnostic support."),
    ("HACKATHON", "Defy'27 (VIT Chennai)"): ("Web3 & AI", "1_Classical_ML", False, "Explores decentralized protocols and applied machine learning integration at campus scale."),
    ("HACKATHON", "CODERAVE 2.0 (Devfolio)"): ("General AI/ML & Full-Stack", "1_Classical_ML", False, "Full-stack developer hackathon emphasizing rapid deployment of applied artificial intelligence."),
    ("HACKATHON", "DevNexus Vidisha (Devfolio)"): ("General AI/ML & Full-Stack", "1_Classical_ML", False, "Regional buildathon focusing on production software engineering infused with intelligent workflows."),
    ("HACKATHON", "IDEATHON – FutureX (Unstop)"): ("General AI/ML & Full-Stack", "1_Classical_ML", True, "Ideation challenge for conceptualizing novel artificial intelligence use cases and architectures."),
    ("COMPETITION", "QuikCPQ AI Innovation Challenge 2027 (Unstop)"): ("Enterprise/Cloud AI", "1_Classical_ML", False, "Solves enterprise CPQ and commercial workflow optimization using applied AI models."),
    ("COMPETITION", "MachineHack MLDS Enterprise AI Sprints"): ("Enterprise/Cloud AI", "1_Classical_ML", False, "Competitive enterprise sprints testing tabular feature engineering and generative AI integrations."),
    ("HACKATHON", "HackIndia Chennai Overdrive 2027"): ("Web3 & AI", "2_Deep_Learning", False, "Builds next-generation decentralized infrastructure powered by multimodal generative AI models."),
    ("HACKATHON", "ECLIPSE 7.0 (Devfolio)"): ("General AI/ML & Full-Stack", "1_Classical_ML", False, "Encourages student teams to hack on frontier artificial intelligence and emerging technologies."),
    ("HACKATHON", "HackNITR 8.0 (NIT Rourkela)"): ("General AI/ML & Full-Stack", "1_Classical_ML", True, "Flagship student hackathon providing mentorship for building introductory and advanced AI projects."),
    ("COMPETITION", "Analytics Vidhya DataHack Sprints"): ("General AI/ML & Full-Stack", "1_Classical_ML", False, "Fast-paced competitive data science sprints evaluating predictive modeling and feature craftsmanship."),
    ("COMPETITION", "IndiaAI Innovation Challenge & BHASHINI Tracks (MeitY)"): ("RAG & NLP", "2_Deep_Learning", False, "National challenge building Indic large language models and public sector speech systems."),
    ("COMPETITION", "Google Solution Challenge – India Edition (Build with AI)"): ("Generative AI & LLMs", "2_Deep_Learning", False, "Leverages Gemini and Vertex AI to address UN Sustainable Development Goals."),
    ("HACKATHON", "Mailam Builds '27"): ("General AI/ML & Full-Stack", "1_Classical_ML", False, "Hands-on buildathon challenging participants to deploy end-to-end machine learning services."),
    ("COMPETITION", "Microsoft Imagine Cup 2027 (India / Global)"): ("Enterprise/Cloud AI", "2_Deep_Learning", True, "Global student competition empowering teams to build and pitch viable AI-first startups."),
    ("HACKATHON", "Google Girl Hackathon 2027"): ("General AI/ML & Full-Stack", "1_Classical_ML", False, "Promotes women engineers through competitive programming and applied artificial intelligence challenges."),
    ("COMPETITION", "Flipkart GRiD & HackOn with Amazon (2027 Editions)"): ("Enterprise/Cloud AI", "1_Classical_ML", False, "Tests large-scale algorithmic problem solving and practical machine learning for e-commerce."),
    ("HACKATHON", "ET AI Hackathon (Economic Times × Unstop)"): ("Enterprise/Cloud AI", "2_Deep_Learning", False, "Solves complex corporate and commercial challenges using enterprise agentic generative AI."),
    ("COMPETITION", "Amazon ML Challenge India"): ("Computer Vision", "2_Deep_Learning", False, "Tackles large-scale multimodal entity extraction and product categorization machine learning."),
    ("HACKATHON", "ETHIndia 2027"): ("Web3 & AI", "2_Deep_Learning", False, "Explores synergies between autonomous intelligent agents and decentralized on-chain infrastructure."),
}

def parse_location_and_mode(region, raw_mode):
    """
    Parses and standardizes location and mode according to specification.
    Mode: Online | In-Person | Hybrid | Online / Hybrid | Hybrid / In-Person
    """
    city_from_mode = None
    if "/" in raw_mode:
        parts = [p.strip() for p in raw_mode.split("/")]
        if parts[0] == "Hybrid" and parts[1] not in ["In-Person", "Online"]:
            city_from_mode = parts[1]
            norm_mode = "Hybrid"
        elif raw_mode == "Online / Hybrid":
            norm_mode = "Online / Hybrid"
        elif raw_mode == "Hybrid / In-Person":
            norm_mode = "Hybrid / In-Person"
        else:
            norm_mode = raw_mode
    else:
        norm_mode = raw_mode

    if norm_mode == "Online":
        loc = f"Online ({region})"
    else:
        m_city = re.match(r"^India \((.+)\)$", region)
        if m_city and m_city.group(1) not in ["National", "All-India"]:
            loc = f"{m_city.group(1)}, India"
        elif city_from_mode:
            loc = f"{city_from_mode}, India"
        elif region in ["India", "India (National)", "India (All-India)", "India / Global"]:
            loc = "India (specific city not stated in source)"
        else:
            loc = region

    return loc, norm_mode

def build():
    print("=" * 80)
    print("Building Events & Competitions Knowledge Base for eBuddy")
    print("=" * 80)

    # 1. Compare File A and File B hackathons sheets
    wb_a = openpyxl.load_workbook(FILE_A, data_only=False)
    wb_b = openpyxl.load_workbook(FILE_B, data_only=False)

    ws_a_hack = wb_a["AI & ML Hackathons"]
    ws_b_hack = wb_b["AI & ML Hackathons"]

    diffs = []
    max_r = max(ws_a_hack.max_row, ws_b_hack.max_row)
    max_c = max(ws_a_hack.max_column, ws_b_hack.max_column)

    for r in range(1, max_r + 1):
        for c in range(1, max_c + 1):
            v_a = ws_a_hack.cell(row=r, column=c).value
            v_b = ws_b_hack.cell(row=r, column=c).value
            if v_a != v_b:
                diffs.append((r, c, v_a, v_b))

    if not diffs:
        print("[Sheet Comparison] File A & File B 'AI & ML Hackathons' sheets: IDENTICAL")
    else:
        print(f"[Sheet Comparison] Differences found: {len(diffs)}")
        for d in diffs:
            print("  ", d)
        raise ValueError("File A and File B hackathon sheets are not identical!")

    # 2. Extract Fests from File A
    ws_fests = wb_a["Top 7 IIT Tech Fests"]
    events_master = []
    fest_idx = 1
    review_table = []

    for r in range(5, 12):
        row = [ws_fests.cell(row=r, column=c).value for c in range(1, 9)]
        if all(v is None or str(v).strip() == "" for v in row):
            continue

        institute = str(row[2]).strip()
        city_state = str(row[3]).strip()
        fest_name = str(row[4]).strip()
        timeline_raw = str(row[5]).strip()
        prev_dates_raw = str(row[6]).strip()
        highlights = str(row[7]).strip()

        event_id = f"FEST-{fest_idx:02d}"
        fest_idx += 1
        category = "FEST"

        # Host region
        state_part = city_state.split(",")[1].strip() if "," in city_state else city_state
        host_region = f"India ({state_part})"
        location = city_state
        mode = "In-Person (inferred; not stated in source)"

        # Prize
        prize_pool_listed = "Not listed in source"
        prize_pool_usd_est = ""

        # Timeline parsing
        if timeline_raw not in TIMELINE_PARSER_MAP:
            raise ValueError(f"Unparsed fest timeline: '{timeline_raw}' at row {r}")
        exp_range, start_m, end_m, tl_type = TIMELINE_PARSER_MAP[timeline_raw]

        # Prev year parsing
        if prev_dates_raw not in PREV_YEAR_PARSER_MAP:
            raise ValueError(f"Unparsed fest prev dates: '{prev_dates_raw}' at row {r}")
        prev_range, is_new = PREV_YEAR_PARSER_MAP[prev_dates_raw]

        # Data quality note
        dq_notes = [
            "Mode not in source; inferred for campus fest",
            "No monetary prize quantified"
        ]
        dq_note_str = "; ".join(dq_notes)

        review_table.append({
            "event_id": event_id,
            "raw": timeline_raw,
            "expected_range": exp_range,
            "start": start_m,
            "end": end_m,
            "type": tl_type,
            "dq_note": dq_note_str
        })

        events_master.append({
            "event_id": event_id,
            "category": category,
            "event_name": fest_name,
            "organizer_or_platform": institute,
            "host_region": host_region,
            "location": location,
            "mode": mode,
            "domain": highlights,
            "prize_pool_listed": prize_pool_listed,
            "prize_pool_usd_est": prize_pool_usd_est,
            "expected_month_range": exp_range,
            "start_month": start_m,
            "end_month": end_m,
            "timeline_type": tl_type,
            "timeline_raw": timeline_raw,
            "previous_year_occurrence_raw": prev_dates_raw,
            "previous_year_month_range": prev_range,
            "is_new_edition": "TRUE" if is_new else "FALSE",
            "tracking_status": "",
            "min_phase_required": "NONE",
            "data_quality_note": dq_note_str,
            "source_sheet": "Top 7 IIT Tech Fests",
            "source_row": r
        })

    # 3. Extract Hackathons and Competitions
    hack_idx = 1
    comp_idx = 1

    for r in range(5, 60):
        row = [ws_a_hack.cell(row=r, column=c).value for c in range(1, 12)]
        if all(v is None or str(v).strip() == "" for v in row):
            continue

        platform = str(row[1]).strip()
        event_name = str(row[2]).strip()
        host_region = str(row[3]).strip()
        domain = str(row[4]).strip()
        prize_listed = str(row[5]).strip()
        prize_usd_raw = row[6]
        timeline_raw = str(row[7]).strip()
        prev_year_raw = str(row[8]).strip()
        raw_mode = str(row[9]).strip()
        tracking_status = str(row[10]).strip()

        # Category determination
        is_comp = False
        if platform in COMP_PLATFORMS:
            is_comp = True
        else:
            for prefix in COMP_PREFIXES:
                if event_name.startswith(prefix):
                    is_comp = True
                    break

        if is_comp:
            category = "COMPETITION"
            event_id = f"COMP-{comp_idx:03d}"
            comp_idx += 1
            min_phase = "1_Classical_ML"
        else:
            category = "HACKATHON"
            event_id = f"HACK-{hack_idx:03d}"
            hack_idx += 1
            min_phase = "1_Classical_ML"

        # Location & Mode
        location, norm_mode = parse_location_and_mode(host_region, raw_mode)

        # Prize pool USD est
        # If 0, leave empty
        if prize_usd_raw is None or prize_usd_raw == "" or int(prize_usd_raw) == 0:
            prize_usd_est = ""
        else:
            prize_usd_est = str(int(prize_usd_raw))

        # Timeline parsing
        if timeline_raw not in TIMELINE_PARSER_MAP:
            raise ValueError(f"Unparsed hackathon timeline: '{timeline_raw}' at row {r}")
        exp_range, start_m, end_m, tl_type = TIMELINE_PARSER_MAP[timeline_raw]

        # Previous year parsing
        if prev_year_raw not in PREV_YEAR_PARSER_MAP:
            raise ValueError(f"Unparsed hackathon prev year: '{prev_year_raw}' at row {r}")
        prev_range, is_new = PREV_YEAR_PARSER_MAP[prev_year_raw]

        # Data quality flags
        dq_flags = []

        # Check for unquantified prize
        unquantified_keywords = [
            "TBA", "Conference / Publication", "Publication Track",
            "Conference Track", "Student Prizes", "Micro Grants"
        ]
        if any(k in prize_listed for k in unquantified_keywords) or prize_usd_est == "":
            dq_flags.append("No monetary prize quantified")

        # Check for currency conversion
        if any(curr in prize_listed for curr in ["EUR", "CAD", "INR", "₹", "€"]):
            dq_flags.append("Est. USD converted in source")

        # Check for previous-year inconsistency (later than reference date 2026-11-14)
        if "Dec 2026" in prev_year_raw and event_name == "ETHIndia 2027":
            dq_flags.append("Previous-year window looks inconsistent with reference date; verify")

        # Check for restricted region
        if "USA (Restricted)" in host_region:
            dq_flags.append("Eligibility restricted to USA")

        dq_note_str = "; ".join(dq_flags)

        review_table.append({
            "event_id": event_id,
            "raw": timeline_raw,
            "expected_range": exp_range,
            "start": start_m,
            "end": end_m,
            "type": tl_type,
            "dq_note": dq_note_str
        })

        events_master.append({
            "event_id": event_id,
            "category": category,
            "event_name": event_name,
            "organizer_or_platform": platform,
            "host_region": host_region,
            "location": location,
            "mode": norm_mode,
            "domain": domain,
            "prize_pool_listed": prize_listed,
            "prize_pool_usd_est": prize_usd_est,
            "expected_month_range": exp_range,
            "start_month": start_m,
            "end_month": end_m,
            "timeline_type": tl_type,
            "timeline_raw": timeline_raw,
            "previous_year_occurrence_raw": prev_year_raw,
            "previous_year_month_range": prev_range,
            "is_new_edition": "TRUE" if is_new else "FALSE",
            "tracking_status": tracking_status,
            "min_phase_required": min_phase,
            "data_quality_note": dq_note_str,
            "source_sheet": "AI & ML Hackathons",
            "source_row": r
        })

    # 4. Generate File 2: 02_phase_eligibility.csv
    eligibility_rows = [
        {
            "highest_completed_phase_id": "NONE_YET",
            "highest_completed_phase_order": 0,
            "fests_unlocked": "TRUE",
            "hackathons_unlocked": "FALSE",
            "competitions_unlocked": "FALSE",
            "max_fests_per_recommendation": 3,
            "max_hackathons_per_recommendation": 0,
            "max_competitions_per_recommendation": 0,
            "message_to_user": "Explore top tech fests for inspiration; hackathons and competitions will unlock after you finish Phase 1 (Classical ML)."
        },
        {
            "highest_completed_phase_id": "0_Foundations",
            "highest_completed_phase_order": 1,
            "fests_unlocked": "TRUE",
            "hackathons_unlocked": "FALSE",
            "competitions_unlocked": "FALSE",
            "max_fests_per_recommendation": 3,
            "max_hackathons_per_recommendation": 0,
            "max_competitions_per_recommendation": 0,
            "message_to_user": "Great progress on foundations; continue to Phase 1 (Classical ML) to unlock hands-on hackathons and competitive challenges!"
        },
        {
            "highest_completed_phase_id": "1_Classical_ML",
            "highest_completed_phase_order": 2,
            "fests_unlocked": "TRUE",
            "hackathons_unlocked": "TRUE",
            "competitions_unlocked": "TRUE",
            "max_fests_per_recommendation": 2,
            "max_hackathons_per_recommendation": 2,
            "max_competitions_per_recommendation": 2,
            "message_to_user": "Congratulations on completing Classical ML! Hackathons and machine learning competitions are now fully unlocked."
        },
        {
            "highest_completed_phase_id": "2_Deep_Learning",
            "highest_completed_phase_order": 3,
            "fests_unlocked": "TRUE",
            "hackathons_unlocked": "TRUE",
            "competitions_unlocked": "TRUE",
            "max_fests_per_recommendation": 2,
            "max_hackathons_per_recommendation": 2,
            "max_competitions_per_recommendation": 2,
            "message_to_user": "Deep learning unlocked! You are now well-prepared for computer vision, audio, and neural network challenges."
        },
        {
            "highest_completed_phase_id": "3_Projects",
            "highest_completed_phase_order": 4,
            "fests_unlocked": "TRUE",
            "hackathons_unlocked": "TRUE",
            "competitions_unlocked": "TRUE",
            "max_fests_per_recommendation": 2,
            "max_hackathons_per_recommendation": 2,
            "max_competitions_per_recommendation": 2,
            "message_to_user": "With project benchmarks complete, test your skills in production buildathons and competitive Kaggle/Zindi circuits."
        },
        {
            "highest_completed_phase_id": "4_Specialization",
            "highest_completed_phase_order": 5,
            "fests_unlocked": "TRUE",
            "hackathons_unlocked": "TRUE",
            "competitions_unlocked": "TRUE",
            "max_fests_per_recommendation": 2,
            "max_hackathons_per_recommendation": 2,
            "max_competitions_per_recommendation": 2,
            "message_to_user": "Specialization mastered! You can tackle advanced Generative AI, agentic LLM, and reinforcement learning hackathons."
        },
        {
            "highest_completed_phase_id": "5_Research",
            "highest_completed_phase_order": 6,
            "fests_unlocked": "TRUE",
            "hackathons_unlocked": "TRUE",
            "competitions_unlocked": "TRUE",
            "max_fests_per_recommendation": 2,
            "max_hackathons_per_recommendation": 2,
            "max_competitions_per_recommendation": 2,
            "message_to_user": "Full research capability unlocked! Compete in top-tier conference benchmark tracks and frontier AI challenges."
        }
    ]

    # 5. Generate File 3: 03_recommendation_rules.csv
    rules_rows = [
        {
            "rule_id": "R01",
            "rule_name": "MIN_PHASE_FOR_HACKATHON",
            "rule_description": "Learner must complete at least Phase 1 (Classical ML) to unlock hackathons",
            "applies_to_category": "HACKATHON",
            "parameter": "min_phase_id",
            "value": "1_Classical_ML"
        },
        {
            "rule_id": "R02",
            "rule_name": "MIN_PHASE_FOR_COMPETITION",
            "rule_description": "Learner must complete at least Phase 1 (Classical ML) to unlock leaderboard competitions",
            "applies_to_category": "COMPETITION",
            "parameter": "min_phase_id",
            "value": "1_Classical_ML"
        },
        {
            "rule_id": "R03",
            "rule_name": "FEST_ALWAYS_ELIGIBLE",
            "rule_description": "Technical fests are unlocked for learners at all stages for exposure and inspiration",
            "applies_to_category": "FEST",
            "parameter": "min_phase_id",
            "value": "NONE"
        },
        {
            "rule_id": "R04",
            "rule_name": "RECOMMENDATION_SET_SIZE",
            "rule_description": "Total events recommended: 6 when all categories unlocked, 3 fests when hackathons/competitions locked",
            "applies_to_category": "ALL",
            "parameter": "set_size_unlocked / set_size_locked",
            "value": "6 / 3"
        },
        {
            "rule_id": "R05",
            "rule_name": "CATEGORY_MIX",
            "rule_description": "Recommendation sets must include at least one event from each currently unlocked category",
            "applies_to_category": "ALL",
            "parameter": "min_events_per_unlocked_category",
            "value": "1"
        },
        {
            "rule_id": "R06",
            "rule_name": "MAX_SAME_PLATFORM_PER_SET",
            "rule_description": "Maximum events allowed from the same platform or organizer in a single recommendation set",
            "applies_to_category": "ALL",
            "parameter": "max_same_platform",
            "value": "2"
        },
        {
            "rule_id": "R07",
            "rule_name": "EXCLUDE_ENDED_EVENTS",
            "rule_description": "Filter out events whose scheduled end month is strictly prior to the current reference month",
            "applies_to_category": "ALL",
            "parameter": "filter_condition",
            "value": "end_month < current_month"
        },
        {
            "rule_id": "R08",
            "rule_name": "PREFER_UPCOMING_WINDOW",
            "rule_description": "Prioritize events starting within the next 1 to 4 months from the reference date before later events",
            "applies_to_category": "ALL",
            "parameter": "preferred_upcoming_window_months",
            "value": "1-4"
        },
        {
            "rule_id": "R09",
            "rule_name": "REQUIRED_FIELDS_IN_EVERY_RECOMMENDATION",
            "rule_description": "Fields that must be displayed in every card: name, category, location, mode, prize, region, domain, expected window, and previous year occurrence",
            "applies_to_category": "ALL",
            "parameter": "required_fields",
            "value": "event_name, category, location, mode, prize_pool_listed, host_region, domain, expected_month_range, previous_year_month_range"
        },
        {
            "rule_id": "R10",
            "rule_name": "SHOW_DATA_CAVEATS",
            "rule_description": "Display caveats clearly: denote approximate timelines as expected, show placeholder text when mode/prize unquantified, never fabricate missing values",
            "applies_to_category": "ALL",
            "parameter": "enforce_caveats",
            "value": "TRUE"
        },
        {
            "rule_id": "R11",
            "rule_name": "DOMAIN_MATCH",
            "rule_description": "Prioritize events whose domain matches the topics in the learner's current or completed phase per 04_domain_to_phase_map.csv",
            "applies_to_category": "ALL",
            "parameter": "domain_mapping_file",
            "value": "04_domain_to_phase_map.csv"
        }
    ]

    # 6. Generate File 4: 04_domain_to_phase_map.csv
    domain_map_rows = []
    for ev in events_master:
        key = (ev["category"], ev["event_name"])
        if key not in DOMAIN_MAP_METADATA:
            raise ValueError(f"Missing domain mapping for event: {key}")
        tag, after_phase, beg_friendly, reasoning = DOMAIN_MAP_METADATA[key]
        domain_map_rows.append({
            "event_id": ev["event_id"],
            "event_name": ev["event_name"],
            "category": ev["category"],
            "primary_domain_tag(assigned)": tag,
            "recommended_after_phase_id": after_phase,
            "beginner_friendly": "TRUE" if beg_friendly else "FALSE",
            "reasoning_short": reasoning
        })

    # 7. Write CSVs with UTF-8 BOM
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    file1_path = os.path.join(OUTPUT_DIR, "01_events_master.csv")
    file2_path = os.path.join(OUTPUT_DIR, "02_phase_eligibility.csv")
    file3_path = os.path.join(OUTPUT_DIR, "03_recommendation_rules.csv")
    file4_path = os.path.join(OUTPUT_DIR, "04_domain_to_phase_map.csv")

    file1_cols = [
        "event_id", "category", "event_name", "organizer_or_platform",
        "host_region", "location", "mode", "domain", "prize_pool_listed",
        "prize_pool_usd_est", "expected_month_range", "start_month",
        "end_month", "timeline_type", "timeline_raw",
        "previous_year_occurrence_raw", "previous_year_month_range",
        "is_new_edition", "tracking_status", "min_phase_required",
        "data_quality_note", "source_sheet", "source_row"
    ]
    with open(file1_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=file1_cols, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(events_master)

    file2_cols = [
        "highest_completed_phase_id", "highest_completed_phase_order",
        "fests_unlocked", "hackathons_unlocked", "competitions_unlocked",
        "max_fests_per_recommendation", "max_hackathons_per_recommendation",
        "max_competitions_per_recommendation", "message_to_user"
    ]
    with open(file2_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=file2_cols, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(eligibility_rows)

    file3_cols = [
        "rule_id", "rule_name", "rule_description",
        "applies_to_category", "parameter", "value"
    ]
    with open(file3_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=file3_cols, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rules_rows)

    file4_cols = [
        "event_id", "event_name", "category",
        "primary_domain_tag(assigned)", "recommended_after_phase_id",
        "beginner_friendly", "reasoning_short"
    ]
    with open(file4_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=file4_cols, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(domain_map_rows)

    # Sync to inner EBuddy-main/output if directory exists
    inner_output_dir = os.path.join("EBuddy-main", "output")
    if os.path.isdir("EBuddy-main"):
        os.makedirs(inner_output_dir, exist_ok=True)
        for fname in ["01_events_master.csv", "02_phase_eligibility.csv", "03_recommendation_rules.csv", "04_domain_to_phase_map.csv"]:
            src = os.path.join(OUTPUT_DIR, fname)
            dst = os.path.join(inner_output_dir, fname)
            with open(src, "rb") as sf, open(dst, "wb") as df:
                df.write(sf.read())

    # 8. Assertions
    print("\n" + "=" * 80)
    print("RUNNING VALIDATION ASSERTIONS")
    print("=" * 80)

    # 8.1 01_events_master.csv has 62 rows, unique event_id, counts 7 / 25 / 30
    assert len(events_master) == 62, f"Expected 62 events, got {len(events_master)}"
    u_ids = set(e["event_id"] for e in events_master)
    assert len(u_ids) == 62, f"Expected 62 unique event_ids, got {len(u_ids)}"
    cnt_fest = sum(1 for e in events_master if e["category"] == "FEST")
    cnt_hack = sum(1 for e in events_master if e["category"] == "HACKATHON")
    cnt_comp = sum(1 for e in events_master if e["category"] == "COMPETITION")
    assert cnt_fest == 7, f"Expected 7 fests, got {cnt_fest}"
    assert cnt_hack == 25, f"Expected 25 hackathons, got {cnt_hack}"
    assert cnt_comp == 30, f"Expected 30 competitions, got {cnt_comp}"
    print(f"[PASS] 01_events_master.csv: 62 rows, unique IDs (FEST: {cnt_fest}, HACKATHON: {cnt_hack}, COMPETITION: {cnt_comp})")

    # 8.2 Non-empty required columns
    for ev in events_master:
        for field in ["location", "mode", "host_region", "domain", "prize_pool_listed", "expected_month_range", "previous_year_month_range"]:
            val = str(ev[field]).strip()
            assert val != "", f"Field {field} is empty for {ev['event_id']} ({ev['event_name']})"
    print("[PASS] Every event has non-empty location, mode, host_region, domain, prize_pool_listed, expected_month_range, and previous_year_month_range.")

    # 8.3 Month format checks & end_month >= start_month
    month_regex = re.compile(r"^\d{4}-\d{2}$")
    for ev in events_master:
        sm = ev["start_month"]
        em = ev["end_month"]
        if sm:
            assert month_regex.match(sm), f"Invalid start_month: {sm} in {ev['event_id']}"
        if em:
            assert month_regex.match(em), f"Invalid end_month: {em} in {ev['event_id']}"
        if sm and em:
            assert em >= sm, f"end_month {em} < start_month {sm} in {ev['event_id']}"
    print("[PASS] All start_month and end_month match ^\\d{4}-\\d{2}$ or empty, and end_month >= start_month.")

    # 8.4 File 2 has 7 rows
    assert len(eligibility_rows) == 7, f"Expected 7 rows in 02_phase_eligibility, got {len(eligibility_rows)}"
    print("[PASS] 02_phase_eligibility.csv has exactly 7 rows.")

    # 8.5 File 4 has 62 rows and no HACK/COMP has phase earlier than 1_Classical_ML
    assert len(domain_map_rows) == 62, f"Expected 62 rows in 04_domain_to_phase_map, got {len(domain_map_rows)}"
    disallowed_phases = {"NONE_YET", "0_Foundations"}
    for d in domain_map_rows:
        if d["category"] in ["HACKATHON", "COMPETITION"]:
            assert d["recommended_after_phase_id"] not in disallowed_phases, f"Event {d['event_id']} has premature recommended_after_phase_id: {d['recommended_after_phase_id']}"
    print("[PASS] 04_domain_to_phase_map.csv has 62 rows and all HACKATHON/COMPETITION events require >= 1_Classical_ML.")

    # 9. Print Review Table
    print("\n" + "=" * 80)
    print("TIMELINE PARSING & DATA QUALITY AUDIT TABLE")
    print("=" * 80)
    print(f"{'Event ID':<9} | {'Raw Timeline Text':<38} | {'Parsed Range':<28} | {'Start':<7} | {'End':<7} | {'Type':<13} | {'Data Quality Flags'}")
    print("-" * 140)
    for row in review_table:
        print(f"{row['event_id']:<9} | {row['raw']:<38} | {row['expected_range']:<28} | {row['start']:<7} | {row['end']:<7} | {row['type']:<13} | {row['dq_note']}")
    print("-" * 140)
    print("[DONE] Successfully generated all 4 events knowledge base files.")

if __name__ == "__main__":
    build()
