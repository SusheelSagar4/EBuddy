"""
build_da_events_csvs.py
eBuddy Data Analyst (DA) Events & Hackathons Knowledge Base Builder
Inter IIT Tech Meet 15.0 - Adobe Personalised Learning Buddy

Ingests:
  Data_Analytics_Hackathons.xlsx (Sheet: 'All India Data Hackathons')
Reference Date: 2026-11-15

Outputs (UTF-8 with BOM):
  01_events_master.csv (alias: 01_da_events_master.csv)
  02_phase_eligibility.csv (alias: 02_da_phase_eligibility.csv)
  03_recommendation_rules.csv (alias: 03_da_recommendation_rules.csv)
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
# 1. Constants & Dictionaries
# ----------------------------------------------------

REFERENCE_DATE = "2026-11-15"
REFERENCE_YEAR_MONTH = "2026-11"

MONTH_MAP = {
    'january': '01', 'jan': '01',
    'february': '02', 'feb': '02',
    'march': '03', 'mar': '03',
    'april': '04', 'apr': '04',
    'may': '05',
    'june': '06', 'jun': '06',
    'july': '07', 'jul': '07',
    'august': '08', 'aug': '08',
    'september': '09', 'sept': '09', 'sep': '09',
    'october': '10', 'oct': '10',
    'november': '11', 'nov': '11',
    'december': '12', 'dec': '12'
}

MONTH_SHORT = {
    '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
    '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
    '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
}

DA_SKILLS = {
    'DA-S01': ('Spreadsheet fundamentals', 'DA-PH1'),
    'DA-S02': ('Descriptive statistics', 'DA-PH1'),
    'DA-S03': ('Probability basics', 'DA-PH1'),
    'DA-S04': ('SQL basics', 'DA-PH1'),
    'DA-S19': ('Spreadsheet analysis', 'DA-PH1'),
    'DA-S05': ('SQL joins and aggregation', 'DA-PH2'),
    'DA-S07': ('Python basics', 'DA-PH2'),
    'DA-S08': ('pandas data wrangling', 'DA-PH2'),
    'DA-S18': ('Git and version control', 'DA-PH2'),
    'DA-S09': ('Data cleaning and quality', 'DA-PH3'),
    'DA-S10': ('Exploratory data analysis', 'DA-PH3'),
    'DA-S11': ('Data visualisation principles', 'DA-PH3'),
    'DA-S12': ('Python visualisation', 'DA-PH3'),
    'DA-S06': ('Advanced SQL', 'DA-PH4'),
    'DA-S13': ('BI dashboards', 'DA-PH4'),
    'DA-S14': ('Inferential statistics and A/B testing', 'DA-PH4'),
    'DA-S16': ('Business metrics and KPIs', 'DA-PH4'),
    'DA-S15': ('Regression basics', 'DA-PH5'),
    'DA-S17': ('Data storytelling', 'DA-PH5'),
    'DA-S20': ('Analytics case interviews', 'DA-PH5'),
}

PHASE_ORDER = {
    'DA-PH1': 1,
    'DA-PH2': 2,
    'DA-PH3': 3,
    'DA-PH4': 4,
    'DA-PH5': 5,
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
        os.path.join(os.path.dirname(script_dir), "da", "data", filename),
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    return filename

# ----------------------------------------------------
# 3. Helper Parsing Functions
# ----------------------------------------------------

def derive_event_type(name, category):
    """HACKATHON if name or category contains hackathon, datathon, or data-thon; else COMPETITION."""
    text = f"{name} {category}".lower()
    if any(k in text for k in ['hackathon', 'datathon', 'data-thon']):
        return 'HACKATHON'
    return 'COMPETITION'

def derive_organiser_type(organiser, category):
    """IIT | NIT | BITS/IIM/B-School | Corporate | Government/Ministry | Community platform | Other"""
    org_lower = organiser.lower()
    cat_lower = category.lower()
    
    # IIT (checked before UN/Corporate co-sponsors e.g. IIT Bombay & UN-APCTT)
    if 'iit' in org_lower or 'inter-iit' in org_lower or 'iit' in cat_lower:
        return 'IIT'
        
    # NIT
    if 'nit' in org_lower or 'nit' in cat_lower:
        return 'NIT'
        
    # Government / Ministry
    if any(k in org_lower for k in ['ministry', 'aicte', 'my bharat', 'un-apctt']):
        return 'Government/Ministry'
    if 'govt' in cat_lower:
        return 'Government/Ministry'
        
    # BITS / IIM / B-School
    if any(k in org_lower for k in ['bits', 'iim', 'praxis business school']):
        return 'BITS/IIM/B-School'
    if any(k in cat_lower for k in ['bits', 'iim', 'b-school']):
        return 'BITS/IIM/B-School'
        
    # Community platform
    if 'analytics vidhya' in org_lower or 'community' in cat_lower:
        return 'Community platform'
        
    # Corporate
    if any(k in org_lower for k in [
        'rajasthan royals', 'zs associates', 'american express', 'flipkart',
        'tvs credit', 'ubs', 'credit suisse', 'optum', 'amazon', 'wells fargo',
        'goldman sachs'
    ]) or 'corporate' in cat_lower or 'sports' in cat_lower:
        return 'Corporate'
        
    return 'Other'

def derive_mode(mode_venue_raw):
    """Online | Hybrid | Hybrid / Offline from leading words"""
    raw = mode_venue_raw.strip()
    if raw.startswith("Hybrid / Offline") or raw.startswith("Hybrid/Offline"):
        return "Hybrid / Offline"
    if raw.startswith("Hybrid"):
        return "Hybrid"
    if raw.startswith("Online"):
        return "Online"
    return "Other"

def derive_finale_venue(mode_venue_raw, mode_derived):
    """Derives offline round / finale location if named, Virtual (online) for Online, else empty."""
    if mode_derived == "Online":
        return "Virtual (online)", None
        
    raw = mode_venue_raw.strip()
    # Explicit mapping based on exact source phrases
    if "IIT Bombay Powai" in raw:
        return "IIT Bombay Powai", None
    if "IIT Bombay Campus" in raw:
        return "IIT Bombay Campus", None
    if "IIT Bombay" in raw:
        return "IIT Bombay", None
    if "Mumbai & Goa" in raw:
        return "Mumbai & Goa", None
    if "Host IIT in Dec" in raw:
        return "Host IIT", None
    if "IIT Kharagpur" in raw:
        return "IIT Kharagpur", None
    if "IIT Madras" in raw:
        return "IIT Madras", None
    if "IIT Jodhpur" in raw:
        return "IIT Jodhpur", None
    if "IIT Kanpur" in raw:
        return "IIT Kanpur", None
    if "IIT Bhubaneswar Campus" in raw:
        return "IIT Bhubaneswar Campus", None
    if "IIT Bhubaneswar" in raw:
        return "IIT Bhubaneswar", None
    if "IIT BHU" in raw:
        return "IIT BHU", None
    if "NIT Tiruchirappalli Campus" in raw:
        return "NIT Tiruchirappalli Campus", None
    if "IIT Delhi" in raw:
        return "IIT Delhi", None
    if "IIT Roorkee" in raw:
        return "IIT Roorkee", None
    if "BITS Pilani Campus" in raw:
        return "BITS Pilani Campus", None
    if "Kolkata" in raw:
        return "Kolkata", None
    if "ZS India Offices/Virtual" in raw:
        return "ZS India Offices/Virtual", None
    if "Gurugram / Virtual" in raw:
        return "Gurugram / Virtual", None
    if "Bengaluru" in raw:
        return "Bengaluru", None
    if "IIM Bangalore Campus" in raw:
        return "IIM Bangalore Campus", None
    if "IIT Guwahati" in raw:
        return "IIT Guwahati", None
    if "COEP Pune" in raw:
        return "COEP Pune", None
    if "NIT Warangal" in raw:
        return "NIT Warangal", None
    if "IIT ISM Dhanbad" in raw:
        return "IIT ISM Dhanbad", None
    if "IIT Patna / IIT Gandhinagar" in raw:
        return "IIT Patna / IIT Gandhinagar", None
        
    # Venue not specifically named in raw text (e.g. SIH nodal centers, MY Bharat state-level)
    return "", "VENUE_NOT_NAMED"

def parse_target_window(raw):
    """
    Parses Target Date / Window into expected_month_range, start_month, end_month,
    next_cycle_note, date_wording, registration_note_derived, and quality notes.
    """
    raw_str = str(raw).strip()
    next_cycle = ""
    reg_note = ""
    quality_notes = []
    date_wording = "TENTATIVE" if "tentative" in raw_str.lower() else "EXPECTED"
    
    # Registration note extraction
    m_reg = re.search(r'\(reg(?:istration)?\s+open\s+([^)]+)\)', raw_str, re.I)
    if m_reg:
        reg_note = f"Registration opens {m_reg.group(1).strip()}"
        
    # Next cycle / secondary cycle extraction
    if "(Also Dec 2027)" in raw_str:
        next_cycle = "Dec 2027"
    elif "(Also Nov–Dec 2027 cycle)" in raw_str or "(Also Nov-Dec 2027 cycle)" in raw_str:
        next_cycle = "Nov – Dec 2027"
    elif "& Bi-Monthly throughout 2027" in raw_str or "& Bi-monthly throughout 2027" in raw_str:
        next_cycle = "Bi-monthly throughout 2027"
    elif "& Nov–Dec 2027" in raw_str or "& Nov-Dec 2027" in raw_str:
        next_cycle = "Nov – Dec 2027"
    elif "& December 2027" in raw_str:
        next_cycle = "Dec 2027"
    elif "(and Dec 2027 – Jan 2028 cycle)" in raw_str or "(and Dec 2027 - Jan 2028 cycle)" in raw_str:
        next_cycle = "Dec 2027 – Jan 2028"
    elif "(and Jan 2028 cycle)" in raw_str:
        next_cycle = "Jan 2028"
        
    # Isolate primary window
    primary = raw_str
    # Split on '&' if secondary cycle
    primary = re.split(r'\s+&\s+', primary)[0]
    # Remove parentheticals
    primary = re.sub(r'\(.*?\)', '', primary).strip()
    
    # Pattern A: Month D-D, YYYY e.g. December 16–18, 2026 or March 5–7, 2027
    m1 = re.search(r'([A-Za-z]+)\s+\d+[–\-]\d+,\s*(\d{4})', primary)
    # Pattern B: Month D – Month D, YYYY e.g. Nov 5 – Dec 7, 2026
    m2 = re.search(r'([A-Za-z]+)\s+\d+\s*[–\-]\s*([A-Za-z]+)\s+\d+,\s*(\d{4})', primary)
    # Pattern C: Month – Month YYYY e.g. January – March 2027 or Feb – Mar 2027
    m3 = re.search(r'([A-Za-z]+)\s*[–\-]\s*([A-Za-z]+)\s+(\d{4})', primary)
    # Pattern D: Month YYYY e.g. February 2027
    m4 = re.search(r'([A-Za-z]+)\s+(\d{4})', primary)
    
    if m2:
        m_start_txt = m2.group(1).lower()
        m_end_txt = m2.group(2).lower()
        yr = m2.group(3)
        s_m = MONTH_MAP[m_start_txt]
        e_m = MONTH_MAP[m_end_txt]
        start_month = f"{yr}-{s_m}"
        end_month = f"{yr}-{e_m}"
        exp_range = f"{MONTH_SHORT[s_m]} – {MONTH_SHORT[e_m]} {yr}"
    elif m1:
        m_txt = m1.group(1).lower()
        yr = m1.group(2)
        m_num = MONTH_MAP[m_txt]
        start_month = f"{yr}-{m_num}"
        end_month = f"{yr}-{m_num}"
        exp_range = f"{MONTH_SHORT[m_num]} {yr}"
    elif m3:
        m_start_txt = m3.group(1).lower()
        m_end_txt = m3.group(2).lower()
        yr = m3.group(3)
        s_m = MONTH_MAP[m_start_txt]
        e_m = MONTH_MAP[m_end_txt]
        start_month = f"{yr}-{s_m}"
        end_month = f"{yr}-{e_m}"
        exp_range = f"{MONTH_SHORT[s_m]} – {MONTH_SHORT[e_m]} {yr}"
    elif m4:
        m_txt = m4.group(1).lower()
        yr = m4.group(2)
        m_num = MONTH_MAP[m_txt]
        start_month = f"{yr}-{m_num}"
        end_month = f"{yr}-{m_num}"
        exp_range = f"{MONTH_SHORT[m_num]} {yr}"
    else:
        start_month = ""
        end_month = ""
        exp_range = ""
        quality_notes.append("UNRECOGNIZED_TARGET_WINDOW_PATTERN")
        
    return exp_range, start_month, end_month, next_cycle, date_wording, reg_note, quality_notes

def parse_last_held(raw):
    """
    Parses Last Time Held into last_held_year, last_held_month_range, edition_note,
    and quality notes.
    """
    raw_str = str(raw).strip()
    edition_note = ""
    quality_notes = []
    
    # Edition note extraction in parenthetical
    m_ed = re.search(r'\(([^)]+)\)', raw_str)
    if m_ed:
        edition_note = m_ed.group(1).strip()
        
    # Check multiple years: e.g. "November 2026 / November 2025"
    if "/" in raw_str and "2026" in raw_str and "2025" in raw_str:
        latest_year = "2026"
        month_range = "Nov 2026 and Nov 2025"
        quality_notes.append("MULTIPLE_YEARS_IN_SOURCE")
        return latest_year, month_range, edition_note, quality_notes
        
    # Clean parentheticals for date parsing
    cleaned = re.sub(r'\(.*?\)', '', raw_str).strip()
    years = re.findall(r'\b(20\d\d)\b', cleaned)
    latest_year = years[0] if years else ""
    
    # Pattern A: Month D-D, YYYY e.g. December 22–24, 2025 or January 5–18, 2026
    m1 = re.search(r'([A-Za-z]+)\s+\d+[–\-]\d+,\s*(\d{4})', cleaned)
    # Pattern B: Month D – Month D, YYYY e.g. Feb 27 – Mar 1, 2026
    m2 = re.search(r'([A-Za-z]+)\s+\d+\s*[–\-]\s*([A-Za-z]+)\s+\d+,\s*(\d{4})', cleaned)
    # Pattern C: Month – Month YYYY e.g. Nov – Dec 2025 or June 25 – August 2026
    m3 = re.search(r'([A-Za-z]+)(?:\s+\d+)?\s*[–\-]\s*([A-Za-z]+)(?:\s+\d+)?(?:,)?\s+(\d{4})', cleaned)
    # Pattern D: Late Month YYYY e.g. Late August 2026
    m4 = re.search(r'Late\s+([A-Za-z]+)\s+(\d{4})', cleaned, re.I)
    # Pattern E: Month YYYY e.g. December 2025
    m5 = re.search(r'([A-Za-z]+)\s+(\d{4})', cleaned)
    
    if m2:
        m_s = MONTH_SHORT[MONTH_MAP[m2.group(1).lower()]]
        m_e = MONTH_SHORT[MONTH_MAP[m2.group(2).lower()]]
        yr = m2.group(3)
        month_range = f"{m_s} – {m_e} {yr}"
    elif m1:
        m_s = MONTH_SHORT[MONTH_MAP[m1.group(1).lower()]]
        yr = m1.group(2)
        month_range = f"{m_s} {yr}"
    elif m3:
        m_s = MONTH_SHORT[MONTH_MAP[m3.group(1).lower()]]
        m_e = MONTH_SHORT[MONTH_MAP[m3.group(2).lower()]]
        yr = m3.group(3)
        month_range = f"{m_s} – {m_e} {yr}"
    elif m4:
        m_s = MONTH_SHORT[MONTH_MAP[m4.group(1).lower()]]
        yr = m4.group(2)
        month_range = f"Late {m_s} {yr}"
    elif m5:
        m_s = MONTH_SHORT[MONTH_MAP[m5.group(1).lower()]]
        yr = m5.group(2)
        month_range = f"{m_s} {yr}"
    else:
        month_range = cleaned
        
    return latest_year, month_range, edition_note, quality_notes

def parse_eligibility(raw):
    """
    Derives eligibility_group_derived, restriction_flags_derived, and team_size_text.
    """
    raw_str = str(raw).strip()
    low = raw_str.lower()
    
    # 1. Team size text
    team_size = ""
    team_patterns = [
        r'(?:individual\s+or\s+teams\s+of\s+[\d–\-]+(?:\s*members)?)',
        r'(?:individual\s+or\s+teams\s+of\s+up\s+to\s+\d+)',
        r'(?:teams\s+of\s+[\d–\-]+(?:\s*members)?)',
        r'(?:cross-college\s+teams\s+permitted\s*\([\d–\-]+\s*members\))',
        r'(?:solo\s+or\s+teams\s+of\s+\d+)',
        r'(?:individual\s+participation)',
        r'(?:6-member\s+team(?:\s+with\s+[^;]+)?)',
        r'(?:individual\s+or\s+teams\s+of\s+\d+)'
    ]
    for tp in team_patterns:
        m_team = re.search(tp, raw_str, re.I)
        if m_team:
            team_size = m_team.group(0).strip()
            break
            
    # 2. Restriction flags
    flags = []
    if 'strictly for students enrolled across the 23 iits' in low or 'iit' in low and 'strictly' in low:
        flags.append('IIT_ONLY')
    if 'pre-final and final-year' in low or 'final-year' in low:
        flags.append('FINAL_YEARS_ONLY')
    if '2nd, 3rd, and 4th-year' in low or '2nd, 3rd' in low or 'batches 2028' in low or 'graduating batches' in low:
        flags.append('YEAR_RANGE_RESTRICTED')
    if 'aged 35 or younger' in low or 'age' in low and '35' in low:
        flags.append('AGE_LIMIT')
    if 'full-time' in low:
        flags.append('FULL_TIME_ONLY')
    if any(k in low for k in ['engineering', 'b.tech', 'm.tech', 'mba', 'b.sc', 'm.sc', 'commerce', 'management', 'technical, analytics, or quantitative']):
        # If specific degrees or branches are listed
        if not ('open to all college students' in low and 'discipline' not in low):
            flags.append('BRANCH_RESTRICTED')
    if any(k in low for k in ['female member', 'internal institute trials', 'valid institutional id', 'accredited']):
        flags.append('ADDITIONAL_CRITERIA_IN_TEXT')
        
    # 3. Eligibility group derived
    if 'aged 35' in low:
        group = 'Age-limited'
    elif 'strictly for students enrolled across the 23 iits' in low:
        group = 'IIT-enrolled only'
    elif 'pre-final and final-year' in low or '2nd, 3rd, and 4th-year' in low:
        group = 'Year-of-study restricted'
    elif 'students and early professionals' in low or 'data enthusiasts' in low or 'indian youth' in low:
        group = 'Students & early professionals'
    elif any(k in low for k in ['b.tech/b.e.', 'engineering, commerce, science', 'technical, analytics']):
        group = 'Degree/branch restricted'
    elif 'undergraduate and postgraduate' in low or 'ug/pg' in low:
        group = 'UG/PG students'
    elif 'open to all college students' in low or 'all students in' in low or 'college students' in low:
        group = 'Open to all college students'
    else:
        group = 'Check text'
        
    return group, ";".join(flags), team_size

def split_skills_proper(raw_text):
    """
    Splits skills on comma, semicolon, or ' & ' but NEVER inside parentheses.
    """
    tokens = []
    current = []
    paren_depth = 0
    i = 0
    n = len(raw_text)
    while i < n:
        c = raw_text[i]
        if c == '(':
            paren_depth += 1
            current.append(c)
            i += 1
        elif c == ')':
            paren_depth = max(0, paren_depth - 1)
            current.append(c)
            i += 1
        elif paren_depth == 0:
            if c in (',', ';'):
                tokens.append(''.join(current))
                current = []
                i += 1
            elif raw_text[i:i+3] == ' & ':
                tokens.append(''.join(current))
                current = []
                i += 3
            else:
                current.append(c)
                i += 1
        else:
            current.append(c)
            i += 1
    if current:
        tokens.append(''.join(current))
    
    cleaned_tokens = []
    seen = set()
    for t in tokens:
        cleaned = t.strip().rstrip('.').strip()
        if not cleaned: continue
        low = cleaned.lower()
        if low not in seen:
            seen.add(low)
            cleaned_tokens.append(cleaned)
    return cleaned_tokens

def match_skill_item(phrase):
    """
    Maps a single skill item to DA roadmap skill IDs with match_type EXACT or NEAREST.
    """
    p = phrase.lower().strip()
    matched = []
    
    # Excel / Spreadsheet
    if 'excel' in p or 'spreadsheet' in p:
        matched.append(('DA-S01', 'EXACT'))
        matched.append(('DA-S19', 'EXACT'))
        
    # SQL
    if re.search(r'\bsql\b', p):
        matched.append(('DA-S04', 'EXACT'))
        matched.append(('DA-S05', 'EXACT'))
        if any(k in p for k in ['subquery', 'cte', 'window']):
            matched.append(('DA-S06', 'EXACT'))
            
    # Python
    if 'python' in p:
        matched.append(('DA-S07', 'EXACT'))
        if 'pandas' in p:
            matched.append(('DA-S08', 'EXACT'))
            
    # Pandas alone
    if 'pandas' in p and not any(sid == 'DA-S08' for sid, _ in matched):
        matched.append(('DA-S08', 'EXACT'))
        
    # Probability
    if 'probability' in p or 'stochastic' in p:
        matched.append(('DA-S03', 'EXACT'))
        
    # Statistics / Statistical
    if 'statistics' in p or 'statistical' in p or 'statistical analysis' in p or 'statistical modeling' in p:
        matched.append(('DA-S02', 'NEAREST'))
        if 'inference' in p or 'inferential' in p:
            matched.append(('DA-S14', 'EXACT'))
            
    # Data Cleaning / Preprocessing / Wrangling / Outlier
    if any(k in p for k in ['data cleaning', 'cleaning', 'preprocessing', 'wrangling', 'outlier', 'data pipeline']):
        matched.append(('DA-S09', 'EXACT'))
        if 'wrangling' in p:
            matched.append(('DA-S08', 'NEAREST'))
            
    # EDA / Exploratory Data Analysis
    if 'eda' in p or 'exploratory data analysis' in p:
        matched.append(('DA-S10', 'EXACT'))
        
    # Dashboards / BI / Tableau / Power BI
    if any(k in p for k in ['dashboard', 'dashboarding', 'power bi', 'tableau', 'streamlit']):
        matched.append(('DA-S13', 'EXACT'))
        matched.append(('DA-S11', 'NEAREST'))
        
    # Visualization / Visualisation
    if 'visual' in p and not any(sid == 'DA-S11' for sid, _ in matched):
        matched.append(('DA-S11', 'EXACT'))
        if 'python' in p or 'streamlit' in p:
            matched.append(('DA-S12', 'EXACT'))
            
    # Regression
    if 'regression' in p:
        matched.append(('DA-S15', 'EXACT'))
        
    # Storytelling / Presentation / Pitch / Deck / Report / Defense
    if any(k in p for k in ['storytelling', 'presentation', 'pitch', 'deck', 'report', 'defense']):
        matched.append(('DA-S17', 'EXACT' if 'storytelling' in p else 'NEAREST'))
        
    # Case interview / Business case
    if any(k in p for k in ['case study', 'business case', 'consulting case', 'case analytics', 'case deck']):
        matched.append(('DA-S20', 'EXACT'))
        
    # Business metrics / KPIs / Segmentation
    if any(k in p for k in ['metrics', 'kpi', 'rfm', 'profitability', 'valuation', 'optimization', 'p&l', 'growth']):
        matched.append(('DA-S16', 'NEAREST'))
        
    return matched

# ----------------------------------------------------
# 4. Main Build Execution
# ----------------------------------------------------

def build():
    print("=" * 80)
    print("Building Data Analyst Events Knowledge Base CSVs for eBuddy")
    print(f"Reference Date: {REFERENCE_DATE}")
    print("=" * 80)
    
    excel_file = resolve_file("Data_Analytics_Hackathons.xlsx")
    if not os.path.exists(excel_file):
        raise FileNotFoundError(f"Missing required workbook: {excel_file}")
    print(f"Loading workbook: {excel_file}")
    
    wb = openpyxl.load_workbook(excel_file, data_only=True)
    ws = wb["All India Data Hackathons"]
    
    # Track counters for event_id
    hack_counter = 1
    comp_counter = 1
    
    file1_rows = []
    
    for r in range(4, 39):
        vals = [ws.cell(r, c).value for c in range(1, 10)]
        if not any(vals):
            continue
            
        sno, name_raw, cat_raw, org_raw, mode_venue_raw, elig_raw, skills_raw, target_raw, last_held_raw = vals
        sno = int(sno)
        name_str = str(name_raw).strip()
        cat_str = str(cat_raw).strip()
        org_str = str(org_raw).strip()
        mode_venue_str = str(mode_venue_raw).strip()
        elig_str = str(elig_raw).strip()
        skills_str = str(skills_raw).strip()
        target_str = str(target_raw).strip()
        last_held_str = str(last_held_raw).strip()
        
        # 1. Event Type & Event ID
        event_type = derive_event_type(name_str, cat_str)
        if event_type == "HACKATHON":
            event_id = f"HACK-{hack_counter:02d}"
            hack_counter += 1
        else:
            event_id = f"COMP-{comp_counter:02d}"
            comp_counter += 1
            
        # 2. Organiser Type & Home Campus
        org_type = derive_organiser_type(org_str, cat_str)
        is_home_campus = "TRUE" if "IIT Bhubaneswar" in org_str else "FALSE"
        
        # 3. Mode & Finale Venue
        mode_derived = derive_mode(mode_venue_str)
        finale_venue, venue_note = derive_finale_venue(mode_venue_str, mode_derived)
        
        # 4. Target Window Parsing
        exp_range, start_m, end_m, next_cycle, date_wording, reg_note_w, tw_notes = parse_target_window(target_str)
        
        # Registration note: from window or venue
        reg_note = reg_note_w
        if not reg_note:
            if "Online Qualifiers Oct–Nov" in mode_venue_str:
                reg_note = "Online Qualifiers Oct–Nov"
            elif "Online Model Freeze Nov 2026" in mode_venue_str:
                reg_note = "Online Model Freeze Nov 2026"
            elif "Internal IIT Selection Sept–Nov" in mode_venue_str:
                reg_note = "Internal IIT Selection Sept–Nov"
                
        # 5. Last Held Parsing
        last_year, last_month_range, edition_note, lh_notes = parse_last_held(last_held_str)
        
        # 6. Eligibility Parsing
        elig_group, restriction_flags, team_size = parse_eligibility(elig_str)
        
        # 7. Skills Splitting & Matching
        skills_items = split_skills_proper(skills_str)
        skills_list_str = " | ".join(skills_items)
        
        matched_sids = []
        other_skills = []
        for it in skills_items:
            m = match_skill_item(it)
            if m:
                for sid, _ in m:
                    if sid not in matched_sids:
                        matched_sids.append(sid)
            else:
                other_skills.append(it)
                
        matched_sids.sort(key=lambda s: (PHASE_ORDER[DA_SKILLS[s][1]], s))
        da_skill_ids_str = ";".join(matched_sids)
        da_skill_names_str = " | ".join([DA_SKILLS[s][0] for s in matched_sids])
        
        if matched_sids:
            latest_phase_sid = max(matched_sids, key=lambda s: PHASE_ORDER[DA_SKILLS[s][1]])
            readiness_phase = DA_SKILLS[latest_phase_sid][1]
        else:
            readiness_phase = "DA-PH1"
            
        other_skills_str = " | ".join(other_skills)
        
        # 8. Data Quality Notes Consolidation
        all_notes = []
        if venue_note:
            all_notes.append(venue_note)
        all_notes.extend(tw_notes)
        all_notes.extend(lh_notes)
        dq_note_str = ";".join(all_notes)
        
        file1_rows.append({
            "event_id": event_id,
            "source_sno": sno,
            "event_name": name_str,
            "event_type_derived": event_type,
            "category_track": cat_str,
            "organiser_host": org_str,
            "organiser_type_derived": org_type,
            "is_home_campus_event": is_home_campus,
            "mode_derived": mode_derived,
            "mode_and_venue_raw": mode_venue_str,
            "finale_venue_derived": finale_venue,
            "target_window_raw": target_str,
            "expected_month_range": exp_range,
            "start_month": start_m,
            "end_month": end_m,
            "next_cycle_note": next_cycle,
            "date_wording": date_wording,
            "registration_note_derived": reg_note,
            "last_held_raw": last_held_str,
            "last_held_year": last_year,
            "last_held_month_range": last_month_range,
            "edition_note": edition_note,
            "eligibility_raw": elig_str,
            "eligibility_group_derived": elig_group,
            "restriction_flags_derived": restriction_flags,
            "team_size_text": team_size,
            "skills_required_raw": skills_str,
            "skills_list": skills_list_str,
            "da_skill_ids_matched": da_skill_ids_str,
            "da_skill_names_matched": da_skill_names_str,
            "skill_readiness_phase_derived": readiness_phase,
            "other_skills_not_in_roadmap": other_skills_str,
            "min_phase_required": "DA-PH1",
            "data_quality_note": dq_note_str,
            "source_row": r
        })
        
    assert len(file1_rows) == 35, f"Expected 35 rows, got {len(file1_rows)}"
    print(f"[PASS] File 1 generated: {len(file1_rows)} events ({hack_counter - 1} HACKATHON, {comp_counter - 1} COMPETITION).")

    # ----------------------------------------------------
    # Build File 2: 02_phase_eligibility.csv
    # ----------------------------------------------------
    file2_rows = [
        {
            "highest_completed_phase_id": "NONE_YET",
            "highest_completed_phase_order": 0,
            "hackathons_unlocked": "FALSE",
            "competitions_unlocked": "FALSE",
            "max_hackathons_per_recommendation": 0,
            "max_competitions_per_recommendation": 0,
            "total_recommended_set_size": 0,
            "message_to_user": "Build your data foundations in spreadsheets, descriptive statistics, and SQL basics; data analytics hackathons and competitions will unlock after completing Phase 1 (DA-PH1 Foundations)."
        },
        {
            "highest_completed_phase_id": "DA-PH1",
            "highest_completed_phase_order": 1,
            "hackathons_unlocked": "TRUE",
            "competitions_unlocked": "TRUE",
            "max_hackathons_per_recommendation": 2,
            "max_competitions_per_recommendation": 2,
            "total_recommended_set_size": 4,
            "message_to_user": "Foundations complete! You can now participate in beginner-friendly spreadsheet challenges, data wrangling contests, and campus tech fest analytics tracks."
        },
        {
            "highest_completed_phase_id": "DA-PH2",
            "highest_completed_phase_order": 2,
            "hackathons_unlocked": "TRUE",
            "competitions_unlocked": "TRUE",
            "max_hackathons_per_recommendation": 3,
            "max_competitions_per_recommendation": 3,
            "total_recommended_set_size": 6,
            "message_to_user": "Core SQL and Python mastered! Target multi-table relational querying challenges, pandas wrangling hackathons, and corporate analytics qualifiers."
        },
        {
            "highest_completed_phase_id": "DA-PH3",
            "highest_completed_phase_order": 3,
            "hackathons_unlocked": "TRUE",
            "competitions_unlocked": "TRUE",
            "max_hackathons_per_recommendation": 3,
            "max_competitions_per_recommendation": 3,
            "total_recommended_set_size": 6,
            "message_to_user": "Cleaning, EDA and visualization skills unlocked! Compete in national datathons, exploratory data analysis sprints, and statistical visualization contests."
        },
        {
            "highest_completed_phase_id": "DA-PH4",
            "highest_completed_phase_order": 4,
            "hackathons_unlocked": "TRUE",
            "competitions_unlocked": "TRUE",
            "max_hackathons_per_recommendation": 3,
            "max_competitions_per_recommendation": 3,
            "total_recommended_set_size": 6,
            "message_to_user": "BI modeling and advanced SQL unlocked! Ready for corporate decision science challenges, interactive KPI dashboard competitions, and A/B testing hackathons."
        },
        {
            "highest_completed_phase_id": "DA-PH5",
            "highest_completed_phase_order": 5,
            "hackathons_unlocked": "TRUE",
            "competitions_unlocked": "TRUE",
            "max_hackathons_per_recommendation": 3,
            "max_competitions_per_recommendation": 3,
            "total_recommended_set_size": 6,
            "message_to_user": "Full portfolio and storytelling readiness unlocked! Target flagship corporate hiring challenges, national hackathon grand finales, and executive analytics presentations."
        }
    ]
    print(f"[PASS] File 2 generated: {len(file2_rows)} stage-wise eligibility gating rules.")

    # ----------------------------------------------------
    # Build File 3: 03_recommendation_rules.csv
    # ----------------------------------------------------
    file3_rows = [
        {
            "rule_id": "R01",
            "rule_name": "MIN_PHASE_FOR_HACKATHON",
            "rule_description": "Learner must have completed at least Phase 1 (DA-PH1 Foundations) or any subsequent phase to receive hackathon recommendations.",
            "applies_to_category": "HACKATHON",
            "parameter": "min_phase_id",
            "value": "DA-PH1"
        },
        {
            "rule_id": "R02",
            "rule_name": "MIN_PHASE_FOR_COMPETITION",
            "rule_description": "Learner must have completed at least Phase 1 (DA-PH1 Foundations) or any subsequent phase to receive data competition recommendations.",
            "applies_to_category": "COMPETITION",
            "parameter": "min_phase_id",
            "value": "DA-PH1"
        },
        {
            "rule_id": "R03",
            "rule_name": "RECOMMENDATION_SET_SIZE",
            "rule_description": "eBuddy recommends a small curated set of 4 to 6 events per interaction once unlocked (0 when locked).",
            "applies_to_category": "ALL",
            "parameter": "set_size",
            "value": "4_TO_6"
        },
        {
            "rule_id": "R04",
            "rule_name": "CATEGORY_MIX",
            "rule_description": "Recommendation sets should mix hackathons and competitions where events are available in the upcoming window.",
            "applies_to_category": "ALL",
            "parameter": "mix_categories",
            "value": "TRUE"
        },
        {
            "rule_id": "R05",
            "rule_name": "EXCLUDE_ENDED_EVENTS",
            "rule_description": "Filter out events whose scheduled end month is strictly prior to the current reference month (2026-11).",
            "applies_to_category": "ALL",
            "parameter": "end_month_cutoff",
            "value": "CURRENT_MONTH"
        },
        {
            "rule_id": "R06",
            "rule_name": "PREFER_UPCOMING",
            "rule_description": "Prioritize events occurring within the next 1 to 4 months before recommending events further out in the season.",
            "applies_to_category": "ALL",
            "parameter": "upcoming_window_months",
            "value": "1-4"
        },
        {
            "rule_id": "R07",
            "rule_name": "PREFER_HOME_CAMPUS",
            "rule_description": "Boost IIT Bhubaneswar home campus events (Wissenaire, TechZephyr) for local learners.",
            "applies_to_category": "ALL",
            "parameter": "home_campus_preference",
            "value": "BOOST_HOME_CAMPUS"
        },
        {
            "rule_id": "R08",
            "rule_name": "SKILL_READINESS_MATCH",
            "rule_description": "Use skill_readiness_phase_derived as a soft recommendation hint to align events with learner's current or completed phase.",
            "applies_to_category": "ALL",
            "parameter": "soft_hint",
            "value": "skill_readiness_phase_derived"
        },
        {
            "rule_id": "R09",
            "rule_name": "MANDATORY_DISPLAY_FIELDS",
            "rule_description": "Mandatory fields in event recommendation card: event_name, category_track, expected_month_range, date_wording, last_held_month_range, eligibility_raw, mode_derived, skills_required_raw.",
            "applies_to_category": "ALL",
            "parameter": "mandatory_fields",
            "value": "event_name,category_track,expected_month_range,date_wording,last_held_month_range,eligibility_raw,mode_derived,skills_required_raw"
        },
        {
            "rule_id": "R10",
            "rule_name": "DATE_WORDING_CAVEAT",
            "rule_description": "Explicitly display EXPECTED or TENTATIVE wording in event cards since source dates are forward-looking schedules.",
            "applies_to_category": "ALL",
            "parameter": "date_wording_display",
            "value": "ENFORCE_CAVEAT"
        },
        {
            "rule_id": "R11",
            "rule_name": "DIVERSITY_QUOTA",
            "rule_description": "Cap recommendations at a maximum of 2 events from the same organizer in any single recommendation set.",
            "applies_to_category": "ALL",
            "parameter": "max_same_organiser",
            "value": "2"
        },
        {
            "rule_id": "R12",
            "rule_name": "ELIGIBILITY_COMPLIANCE",
            "rule_description": "Filter out events whose restriction_flags_derived or eligibility_group conflicts with learner's institutional profile.",
            "applies_to_category": "ALL",
            "parameter": "eligibility_filter",
            "value": "PROFILE_COMPLIANT"
        }
    ]
    print(f"[PASS] File 3 generated: {len(file3_rows)} machine-readable recommendation engine rules.")

    # ----------------------------------------------------
    # 5. Writing Output CSV Files (BOM utf-8-sig)
    # ----------------------------------------------------
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Single canonical destination: da/output/events/
    unique_out_dirs = [os.path.join(os.path.dirname(script_dir), "output", "events")]

    for out_d in unique_out_dirs:
        os.makedirs(out_d, exist_ok=True)
        
        # Primary file names
        datasets = [
            ("01_events_master.csv", file1_rows),
            ("02_phase_eligibility.csv", file2_rows),
            ("03_recommendation_rules.csv", file3_rows),
        ]
        
        for fname, rows in datasets:
            fpath = os.path.join(out_d, fname)
            with open(fpath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                writer.writerows(rows)

    print(f"[SUCCESS] All DA events CSV knowledge base files written to {len(unique_out_dirs)} output locations.")

    # ----------------------------------------------------
    # 6. Validation Assertions
    # ----------------------------------------------------
    print("\n" + "=" * 80)
    print("RUNNING VALIDATION ASSERTIONS")
    print("=" * 80)
    
    assert len(file1_rows) == 35, f"Expected 35 rows in File 1, got {len(file1_rows)}"
    assert len(file2_rows) == 6, f"Expected 6 rows in File 2, got {len(file2_rows)}"
    assert len(file3_rows) == 12, f"Expected 12 rows in File 3, got {len(file3_rows)}"
    
    # Assert every row has expected_month_range
    for r in file1_rows:
        assert r["expected_month_range"], f"Row {r['source_sno']} has empty expected_month_range"
        assert r["start_month"], f"Row {r['source_sno']} has empty start_month"
        assert r["end_month"], f"Row {r['source_sno']} has empty end_month"
        assert r["min_phase_required"] == "DA-PH1", f"Row {r['source_sno']} min_phase != DA-PH1"
        assert r["event_type_derived"] in ("HACKATHON", "COMPETITION")
        assert r["organiser_type_derived"] in ("IIT", "NIT", "BITS/IIM/B-School", "Corporate", "Government/Ministry", "Community platform", "Other")
        assert r["mode_derived"] in ("Online", "Hybrid", "Hybrid / Offline")
        assert r["date_wording"] in ("EXPECTED", "TENTATIVE")
        assert r["is_home_campus_event"] in ("TRUE", "FALSE")
        
    # Check exact cell preservation against original Excel
    for r in range(4, 39):
        sno = ws.cell(r, 1).value
        matching = [x for x in file1_rows if x["source_sno"] == sno][0]
        assert matching["event_name"] == str(ws.cell(r, 2).value).strip()
        assert matching["category_track"] == str(ws.cell(r, 3).value).strip()
        assert matching["organiser_host"] == str(ws.cell(r, 4).value).strip()
        assert matching["mode_and_venue_raw"] == str(ws.cell(r, 5).value).strip()
        assert matching["eligibility_raw"] == str(ws.cell(r, 6).value).strip()
        assert matching["skills_required_raw"] == str(ws.cell(r, 7).value).strip()
        assert matching["target_window_raw"] == str(ws.cell(r, 8).value).strip()
        assert matching["last_held_raw"] == str(ws.cell(r, 9).value).strip()
        assert matching["source_row"] == r
        
    print("[PASS] Exact Cell Preservation: 100% of raw Excel cell values preserved.")
    print("ALL VALIDATION ASSERTIONS PASSED (100% compliant)!")

    # ----------------------------------------------------
    # 7. Print First 3 Rows Preview
    # ----------------------------------------------------
    print("\n" + "=" * 80)
    print("PREVIEW: FIRST 3 ROWS OF EACH CSV FILE")
    print("=" * 80)
    
    preview_datasets = [
        ("01_events_master.csv", file1_rows),
        ("02_phase_eligibility.csv", file2_rows),
        ("03_recommendation_rules.csv", file3_rows)
    ]
    
    for fname, rows in preview_datasets:
        print("\n" + "-" * 70)
        print(f"FILE: {fname} (Total Rows: {len(rows)})")
        print("-" * 70)
        fieldnames = list(rows[0].keys())
        print("HEADER: " + ", ".join(fieldnames))
        for i, row in enumerate(rows[:3], 1):
            vals_str = [str(row[k]) for k in fieldnames]
            print(f"ROW {i} : " + " | ".join(vals_str[:8]))
            if len(vals_str) > 8:
                print(f"       + {len(vals_str) - 8} more columns: " + " | ".join(vals_str[8:16]))

if __name__ == "__main__":
    build()
