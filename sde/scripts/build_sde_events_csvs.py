"""
build_sde_events_csvs.py
eBuddy SDE Events & Competitions Knowledge Base Builder
Inter IIT Tech Meet 15.0 - Adobe Personalised Learning Buddy

Ingests:
  SDE_Competitions_Hackathons_2026-27.xlsx (Sheet: Competitions, 41 events)

Outputs:
  output/01_events_master.csv
  output/02_phase_eligibility.csv
  output/03_recommendation_rules.csv
  (also mirrored to 01_sde_events_master.csv, 02_sde_phase_eligibility.csv, 03_sde_recommendation_rules.csv)

Reference Date: 2026-11-15
"""

import os
import sys
import csv
import re
from datetime import date, datetime
import openpyxl

# Reconfigure stdout for Unicode support on Windows terminals
sys.stdout.reconfigure(encoding="utf-8")

REF_DATE = date(2026, 11, 15)

MONTH_MAP = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
    'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
    'january': '01', 'february': '02', 'march': '03', 'april': '04', 'june': '06',
    'july': '07', 'august': '08', 'september': '09', 'october': '10', 'november': '11', 'december': '12'
}

def get_category(type_raw: str) -> str:
    """Categorizes events into FEST, HACKATHON, or COMPETITION based on raw Type."""
    t_lower = (type_raw or '').lower()
    if 'tech fest' in t_lower or 'tech-fest' in t_lower:
        return 'FEST'
    elif 'hackathon' in t_lower:
        return 'HACKATHON'
    else:
        return 'COMPETITION'

def get_date_confidence(date_status_raw: str) -> str:
    """Classifies date status into HIGH, MEDIUM, or LOW confidence."""
    s = (date_status_raw or '').strip()
    if s == 'Official':
        return 'HIGH'
    elif s in ['Listing', 'Listing (Unstop)', 'Listing (third-party)', 'Annual start date', 'Rolling', 'Expected']:
        return 'MEDIUM'
    elif s in ['Listing (low confidence)', 'Expected (unverified)', 'Expected (low confidence)', 'Unconfirmed', 'Not announced']:
        return 'LOW'
    else:
        raise ValueError(f"Unrecognized Date Status: {date_status_raw}")

def parse_dates(td_raw: str, period_raw: str):
    """
    Parses tentative dates into structured range, start_month, end_month, timeline_type,
    registration_deadline, and parsing-specific quality notes.
    """
    td = (td_raw or '').strip()
    notes = []
    
    # 1. TCS CodeVita
    if 'pre-qualifier 11–12 Dec 2026' in td or 'pre-qualifier 11-12 Dec 2026' in td:
        return 'Registration by Nov 2026; pre-qualifier Dec 2026', '2026-11', '2026-12', 'MULTI_STAGE', '2026-11-13', notes
        
    # 2. Shaastra Programming Contest
    if 'event window Nov 2026 – Jan 2027' in td or 'event window Nov 2026 - Jan 2027' in td:
        return 'Nov 2026 – Jan 2027', '2026-11', '2027-01', 'EVENT_WINDOW', '2026-11-28', notes
        
    # 3. Registration only patterns (Register by DD Mon YYYY; online)
    m_reg = re.match(r'Register by (\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', td)
    if m_reg:
        day, mon_str, year = m_reg.groups()
        mm = MONTH_MAP[mon_str.lower()[:3]]
        deadline = f"{year}-{mm}-{int(day):02d}"
        mon_disp = mon_str[:3].capitalize()
        return f"Register by {mon_disp} {year} (event dates not stated)", '', f"{year}-{mm}", 'REGISTRATION_ONLY', deadline, notes
        
    # 4. Techkriti
    if 'Registrations closing ~15 Nov 2026' in td:
        notes.append('Approximate registration deadline')
        return 'Registration closes ~Nov 2026 (fest dates not stated in source)', '', '2026-11', 'REGISTRATION_ONLY', '2026-11-15', notes

    # 5. Advent of Code: Starts 1 Dec 2026; 25 daily puzzles
    if 'Starts 1 Dec 2026' in td:
        return 'Dec 2026', '2026-12', '2026-12', 'EVENT_WINDOW', '', notes

    # 6. Specific single-month day windows: e.g. 10–11 Dec 2026, 16–18 Dec 2026, 1–3 Jan 2027, etc.
    m_days = re.match(r'(\d{1,2})[–-](\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', td)
    if m_days:
        d1, d2, mon_str, year = m_days.groups()
        mm = MONTH_MAP[mon_str.lower()[:3]]
        mon_disp = mon_str[:3].capitalize()
        return f"{mon_disp} {year}", f"{year}-{mm}", f"{year}-{mm}", 'EVENT_WINDOW', '', notes

    # 7. Smart India Hackathon Grand Finale: December 2026 (exact date unconfirmed)
    if 'December 2026 (exact date unconfirmed)' in td:
        return 'Dec 2026', '2026-12', '2026-12', 'APPROXIMATE', '', notes

    # 8. Microsoft Imagine Cup: Applications close 28 Feb 2027; judging Mar–Apr; World Championship May–Jun 2027
    if 'Applications close 28 Feb 2027' in td:
        return 'Feb – Jun 2027', '2027-02', '2027-06', 'MULTI_STAGE', '2027-02-28', notes

    # 9. Defy: Listing posted 12 Nov 2026; onsite round likely ~Jan 2027
    if 'onsite round likely ~Jan 2027' in td:
        return 'Jan 2027', '2027-01', '2027-01', 'APPROXIMATE', '', notes

    # 10. MLH Season Hackathons: Rolling through the season; 24–36 hours each
    if 'Rolling through the season' in td:
        return 'Nov 2026 – Mar 2027', '2026-11', '2027-03', 'ROLLING', '', notes

    # 11. Smart India Hackathon 2027: SPOC registration ~Jul 2027; internal rounds ~Aug–Sep 2027; finale likely Dec 2027
    if 'SPOC registration ~Jul 2027' in td:
        return 'Jul – Dec 2027', '2027-07', '2027-12', 'MULTI_STAGE', '', notes

    # 12. ETHIndia 2027: Expected late 2027
    if 'Expected late 2027' in td:
        notes.append('Late 2027 interpreted as Oct–Dec 2027')
        return 'Oct – Dec 2027', '2027-10', '2027-12', 'APPROXIMATE', '', notes

    # 13. HackRx (Bajaj Finserv): 2026 not announced; past editions opened Jun–Jul
    if 'past editions opened Jun–Jul' in td:
        notes.append('Dates inferred from past editions')
        return 'Jun – Jul 2027 (inferred from past editions)', '2027-06', '2027-07', 'APPROXIMATE', '', notes

    # 14. Expected month spans and single months
    m_exp_span = re.search(r'Expected\s+~?([A-Za-z]+)[–-]([A-Za-z]+)\s+(\d{4})', td)
    if m_exp_span:
        m1, m2, year = m_exp_span.groups()
        mm1 = MONTH_MAP[m1.lower()[:3]]
        mm2 = MONTH_MAP[m2.lower()[:3]]
        d1 = m1[:3].capitalize()
        d2 = m2[:3].capitalize()
        return f"{d1} – {d2} {year}", f"{year}-{mm1}", f"{year}-{mm2}", 'APPROXIMATE', '', notes

    m_exp_single = re.search(r'Expected\s+~?([A-Za-z]+)\s+(\d{4})', td)
    if m_exp_single:
        m1, year = m_exp_single.groups()
        mm1 = MONTH_MAP[m1.lower()[:3]]
        d1 = m1[:3].capitalize()
        return f"{d1} {year}", f"{year}-{mm1}", f"{year}-{mm1}", 'APPROXIMATE', '', notes

    # 15. Period window fallbacks
    if any(k in td.lower() for k in ['dates not found', 'not announced', 'schedule not found']):
        if 'Nov 2026' in period_raw:
            return f"{period_raw} (period window only; exact dates not announced)", '2026-11', '2027-03', 'PERIOD_FALLBACK', '', notes
        else:
            return f"{period_raw} (period window only; exact dates not announced)", '2027-04', '2027-11', 'PERIOD_FALLBACK', '', notes

    # Fallback default
    notes.append('Period fallback applied')
    return f"{period_raw} (period window only; exact dates not announced)", '', '', 'PERIOD_FALLBACK', '', notes

def extract_mode_and_location(td_raw: str):
    """Extracts mode and location hints strictly from tentative dates text."""
    td_lower = (td_raw or '').lower()
    mode_hint = ''
    if 'in-person' in td_lower:
        mode_hint = 'In-person'
    elif 'online' in td_lower:
        mode_hint = 'Online'

    location_hint = ''
    if 'ahmedabad' in td_lower:
        location_hint = 'Ahmedabad'
    elif 'south goa' in td_lower:
        location_hint = 'South Goa'
    elif 'delhi ncr' in td_lower:
        location_hint = 'Delhi NCR'
    elif 'india' in td_lower and 'in-person' in td_lower:
        location_hint = 'India'
    elif 'hyderabad' in td_lower:
        location_hint = 'Hyderabad'
    elif 'chennai' in td_lower:
        location_hint = 'Chennai'

    return mode_hint, location_hint

def get_eligibility_group(elig_raw: str) -> str:
    """Maps eligibility text to a closed set of 7 eligibility groups."""
    raw = (elig_raw or '').strip()
    raw_lower = raw.lower()
    
    # Check listing / not stated
    if any(p in raw_lower for p in ['check listing', 'check odoo', 'check devpost', 'check official', 'not stated in source']):
        return 'Check listing / not stated'
    # Startups
    if 'startup' in raw_lower or 'not student-only' in raw_lower:
        return 'Startups / non-student'
    # Women students only (priority over general students)
    if any(w in raw_lower for w in ['women student', 'female engineering student', 'women engineering student', 'women students']):
        return 'Women students only'
    # Students & professionals
    if 'professionals' in raw_lower or 'developers and students' in raw_lower:
        return 'Students & professionals'
    # Graduating batch restricted
    if 'graduating' in raw_lower or 'graduating batches' in raw_lower or 'pre-final and final year' in raw_lower:
        return 'Graduating-batch restricted'
    # Open to anyone
    if 'open to anyone' in raw_lower or 'open to individuals worldwide' in raw_lower or raw_lower.startswith('open via unstop'):
        return 'Open to anyone'
    # Students only
    if any(s in raw_lower for s in ['student', 'students', 'college', 'institutions', 'b.tech', 'm.tech', 'be/btech', 'same as sih']):
        return 'Students only'
    if 'teams of 4–6 (defy\'26 rules)' in raw_lower:
        return 'Check listing / not stated'
        
    return 'Check listing / not stated'

def extract_team_size(elig_raw: str) -> str:
    """Extracts team-size phrase if specified in eligibility text."""
    e = (elig_raw or '').strip()
    if 'teams of 6 incl. ≥1 woman' in e or 'teams of 6' in e:
        return 'teams of 6 incl. ≥1 woman'
    m = re.search(r'(teams of [0-9–\-]+)', e, re.IGNORECASE)
    if m:
        return m.group(1).lower()
    if 'up to 4 members' in e.lower():
        return 'up to 4 members'
    if 'individual' in e.lower():
        return 'individual'
    return ''

def get_prize_kind(prize_raw: str) -> str:
    """Categorizes prize pool into closed list of 5 kinds."""
    p_lower = (prize_raw or '').lower().strip()
    
    # Varies
    if 'varies' in p_lower:
        return 'VARIES'
    # Not found / not listed
    if any(k in p_lower for k in ['not found', 'not listed', 'no cash pool found', 'amount not found']):
        return 'NOT_FOUND'
    # Non cash only
    if any(k in p_lower for k in ['no cash prize', 'internships & mentorship', 'ppi offers / job offers', 'macbook air', 'macbook pro']):
        return 'NON_CASH_ONLY'
    # Cash plus job / internship / PPI
    if any(k in p_lower for k in ['internship', 'ppi', 'joining bonus', 'interview opportunities']):
        return 'CASH_PLUS_JOB_OR_INTERNSHIP'
    # Cash listed
    return 'CASH_LISTED'

def check_prize_is_previous_edition(prize_raw: str) -> bool:
    """Checks if prize text refers to an earlier edition."""
    p_lower = (prize_raw or '').lower()
    patterns = ['2026 edition', '2025 edition', '2021 edition', 'grid 7.0', '(2026)', '(2025)', '(2021)']
    return any(pat in p_lower for pat in patterns)

def get_hiring_status_and_detail(hiring_raw: str):
    """Determines hiring category and extracts detail from parentheses."""
    h = (hiring_raw or '').strip()
    m = re.search(r'\((.*?)\)', h)
    detail = m.group(1).strip() if m else ''
    
    if h.startswith('Yes') or h == 'Internships (NGO)':
        can_get_hired = 'YES'
        if h == 'Internships (NGO)':
            detail = 'NGO'
    elif h == 'Possible':
        can_get_hired = 'POSSIBLE'
    elif 'exposure' in h.lower():
        can_get_hired = 'EXPOSURE_ONLY'
    else:
        can_get_hired = 'NO'
        
    return can_get_hired, detail

def derive_focus_area(type_raw: str, event_name: str) -> str:
    """Maps type and event name to closed list of 12 focus areas."""
    t = (type_raw or '').lower()
    n = (event_name or '').lower()
    
    if 'tech fest' in t or 'tech-fest' in t:
        return 'Tech fest'
    if 'cybersecurity' in t or 'ctf' in t:
        return 'Cybersecurity'
    if 'web3' in t:
        return 'Web3'
    if 'ai agents' in t:
        return 'AI agents'
    if 'space-tech' in t:
        return 'Space-tech'
    if 'quant' in t or 'finance' in t:
        return 'Quant / finance coding'
    if 'puzzle' in t:
        return 'Puzzle / practice'
    if 'startup' in t:
        return 'Startup / product'
    if 'web development' in t:
        return 'Web development'
    if any(k in t for k in ['data science', 'ai/ml', 'ai hackathon', 'ml hackathon']):
        return 'AI / ML / Data Science'
    if any(k in t for k in ['competitive programming', 'team programming', 'competitive coding', 'coding challenge']):
        return 'Competitive programming'
    if 'hackathon' in t or 'hackathons' in t:
        return 'General software hackathon'
    return 'General software hackathon'

def get_min_phase_required(category: str, type_raw: str) -> str:
    """Calculates min phase required per category and type."""
    if category == 'FEST':
        return 'NONE'
    elif category == 'HACKATHON':
        return 'P1_Programming_and_Dev_Basics'
    else: # COMPETITION
        t_lower = (type_raw or '').lower()
        if 'cybersecurity' in t_lower or 'ctf' in t_lower or 'startup' in t_lower:
            return 'P1_Programming_and_Dev_Basics'
        return 'P2_DSA_Foundations'

def main():
    print("=" * 80)
    print("Building eBuddy SDE Events & Competitions Knowledge Base")
    print(f"Reference Date: {REF_DATE}")
    print("=" * 80)

    def resolve_file(filename):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for p in [
            os.path.join(script_dir, '..', 'data', filename),
            os.path.join(script_dir, 'data', filename),
            os.path.join(os.getcwd(), 'sde', 'data', filename),
            os.path.join(os.getcwd(), 'data', filename),
            os.path.join(os.getcwd(), filename),
            os.path.join(script_dir, filename)
        ]:
            if os.path.exists(p):
                return os.path.abspath(p)
        return filename

    excel_path = resolve_file("SDE_Competitions_Hackathons_2026-27.xlsx")
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Missing required Excel file: {excel_path}")

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    if 'Competitions' not in wb.sheetnames:
        raise ValueError("Sheet 'Competitions' not found in workbook!")
    ws = wb['Competitions']

    # Header in row 1, data rows 2..42
    headers = [ws.cell(1, c).value for c in range(1, 12)]
    print(f"Loaded Excel: {len(headers)} columns found.")

    source_rows = []
    for r in range(2, ws.max_row + 1):
        vals = [ws.cell(r, c).value for c in range(1, 12)]
        if any(v is not None and str(v).strip() != '' for v in vals):
            source_rows.append((r, vals))

    if len(source_rows) != 41:
        raise ValueError(f"Expected exactly 41 data rows, found {len(source_rows)}")

    cat_counters = {'FEST': 0, 'HACKATHON': 0, 'COMPETITION': 0}
    master_rows = []
    review_table = []
    mapping_hiring = {}
    mapping_date_conf = {}
    mapping_elig_group = {}

    for source_row_num, vals in source_rows:
        num = int(vals[0])
        competition = str(vals[1]).strip()
        organiser = str(vals[2]).strip()
        period = str(vals[3]).strip()
        tentative_dates = str(vals[4]).strip()
        date_status = str(vals[5]).strip()
        eligibility = str(vals[6]).strip()
        prize_pool = str(vals[7]).strip()
        type_raw = str(vals[8]).strip()
        hiring_raw = str(vals[9]).strip()
        source_verify = str(vals[10]).strip()

        # Category
        category = get_category(type_raw)
        cat_counters[category] += 1
        cat_prefix = 'FEST' if category == 'FEST' else ('HACK' if category == 'HACKATHON' else 'COMP')
        event_id = f"{cat_prefix}-{cat_counters[category]:02d}"

        # Dates & Timeline
        range_disp, sm, em, timeline_type, reg_deadline, date_notes = parse_dates(tentative_dates, period)
        
        # Registration status vs ref date
        if reg_deadline:
            dl_dt = datetime.strptime(reg_deadline, "%Y-%m-%d").date()
            if dl_dt < REF_DATE:
                reg_status = "CLOSED"
            elif 0 <= (dl_dt - REF_DATE).days <= 14:
                reg_status = "CLOSING_SOON"
            else:
                reg_status = "OPEN_OR_UNKNOWN"
        else:
            reg_status = "OPEN_OR_UNKNOWN"

        # Date Confidence & Wording
        date_conf = get_date_confidence(date_status)
        date_wording = "CONFIRMED" if date_conf == "HIGH" else "EXPECTED"
        mapping_date_conf[date_status] = date_conf

        # Mode & Location Hint
        mode_hint, location_hint = extract_mode_and_location(tentative_dates)

        # Eligibility Group & Team Size
        elig_group = get_eligibility_group(eligibility)
        mapping_elig_group[eligibility] = elig_group
        team_size = extract_team_size(eligibility)

        # Women only
        if num in [23, 25, 28]:
            women_only = "TRUE"
        else:
            women_only = "FALSE"

        # Prize Kind & Previous Edition
        prize_kind = get_prize_kind(prize_pool)
        prize_prev_ed = "TRUE" if check_prize_is_previous_edition(prize_pool) else "FALSE"

        # Hiring
        can_get_hired, hiring_detail = get_hiring_status_and_detail(hiring_raw)
        mapping_hiring[hiring_raw] = can_get_hired

        # Focus Area & Min Phase
        focus_area = derive_focus_area(type_raw, competition)
        min_phase = get_min_phase_required(category, type_raw)

        # Data Quality Notes
        quality_notes = list(date_notes)
        if reg_status == "CLOSED":
            quality_notes.append("Registration may already be closed")
        elif reg_status == "CLOSING_SOON":
            quality_notes.append("Registration closing within 14 days")
        if date_conf == "LOW":
            quality_notes.append("Date unconfirmed")
        if timeline_type == "PERIOD_FALLBACK":
            quality_notes.append("Exact 2027 dates not announced")
        if prize_prev_ed == "TRUE":
            quality_notes.append("Prize shown is from an earlier edition")
        if "sources differ" in prize_pool.lower():
            quality_notes.append("Prize figure differs across sources")
        if "2026 edition" in eligibility.lower():
            quality_notes.append("Eligibility shown is from the 2026 edition; verify for 2027")
        if "not listed" in organiser.lower() or "not named" in organiser.lower():
            quality_notes.append("Organiser not named in source")
        if "fest dates not found" in tentative_dates.lower() or num == 4:
            quality_notes.append("Fest dates not in this file; check the fests file if available")

        # Deduplicate while preserving order
        dedup_notes = []
        for n in quality_notes:
            if n not in dedup_notes:
                dedup_notes.append(n)
        quality_note_str = "; ".join(dedup_notes)

        master_rows.append({
            'event_id': event_id,
            'source_number': str(num),
            'category': category,
            'event_name': competition,
            'organiser': organiser,
            'type_raw': type_raw,
            'focus_area_derived': focus_area,
            'period_window_raw': period,
            'expected_month_range': range_disp,
            'start_month': sm,
            'end_month': em,
            'timeline_type': timeline_type,
            'tentative_dates_raw': tentative_dates,
            'registration_deadline': reg_deadline,
            'registration_status_vs_ref_date': reg_status,
            'date_status_raw': date_status,
            'date_confidence': date_conf,
            'date_wording': date_wording,
            'mode_hint': mode_hint,
            'location_hint': location_hint,
            'eligibility_raw': eligibility,
            'eligibility_group': elig_group,
            'team_size_text': team_size,
            'women_only': women_only,
            'prize_pool_raw': prize_pool,
            'prize_kind': prize_kind,
            'prize_is_previous_edition_figure': prize_prev_ed,
            'can_get_hired': can_get_hired,
            'hiring_raw': hiring_raw,
            'hiring_detail': hiring_detail,
            'min_phase_required': min_phase,
            'source_to_verify': source_verify,
            'data_quality_note': quality_note_str,
            'source_row': str(source_row_num)
        })

        review_table.append((competition, tentative_dates, range_disp, sm, em, timeline_type, date_conf))

    # Assert Category Counts
    print(f"Category counts: FEST={cat_counters['FEST']}, HACKATHON={cat_counters['HACKATHON']}, COMPETITION={cat_counters['COMPETITION']}")
    assert cat_counters['FEST'] == 2, f"Expected 2 FEST, got {cat_counters['FEST']}"
    assert cat_counters['HACKATHON'] == 26, f"Expected 26 HACKATHON, got {cat_counters['HACKATHON']}"
    assert cat_counters['COMPETITION'] == 13, f"Expected 13 COMPETITION, got {cat_counters['COMPETITION']}"

    # Period Counts
    period_p1 = sum(1 for r in master_rows if r['period_window_raw'] == 'Nov 2026 – Mar 2027')
    period_p2 = sum(1 for r in master_rows if r['period_window_raw'] == 'Apr – Nov 2027 (expected)')
    print(f"Period counts: Nov 2026 – Mar 2027={period_p1}, Apr – Nov 2027 (expected)={period_p2}")
    assert period_p1 == 27, f"Expected 27, got {period_p1}"
    assert period_p2 == 14, f"Expected 14, got {period_p2}"

    # File 2: Phase Eligibility (9 rows)
    phase_elig_rows = [
        {
            'highest_completed_phase_id': 'NONE_YET',
            'highest_completed_phase_order': '0',
            'fests_unlocked': 'TRUE',
            'hackathons_unlocked': 'FALSE',
            'competitions_unlocked': 'FALSE',
            'max_fests_per_recommendation': '2',
            'max_hackathons_per_recommendation': '0',
            'max_competitions_per_recommendation': '0',
            'message_to_user': 'Explore tech fests for inspiration and community; hackathons and technical competitions unlock once you complete Phase 1 (Programming & Dev Basics).'
        },
        {
            'highest_completed_phase_id': 'P1_Programming_and_Dev_Basics',
            'highest_completed_phase_order': '1',
            'fests_unlocked': 'TRUE',
            'hackathons_unlocked': 'TRUE',
            'competitions_unlocked': 'TRUE',
            'max_fests_per_recommendation': '2',
            'max_hackathons_per_recommendation': '2',
            'max_competitions_per_recommendation': '2',
            'message_to_user': 'Great start! Hackathons and entry-level competitions are now unlocked alongside tech fests; algorithmic competitions unlock after Phase 2 (DSA Foundations).'
        },
        {
            'highest_completed_phase_id': 'P2_DSA_Foundations',
            'highest_completed_phase_order': '2',
            'fests_unlocked': 'TRUE',
            'hackathons_unlocked': 'TRUE',
            'competitions_unlocked': 'TRUE',
            'max_fests_per_recommendation': '2',
            'max_hackathons_per_recommendation': '2',
            'max_competitions_per_recommendation': '2',
            'message_to_user': 'DSA foundations complete! Full access to competitive programming, hackathons, and tech fests is now active.'
        },
        {
            'highest_completed_phase_id': 'P3_DSA_Core_Techniques',
            'highest_completed_phase_order': '3',
            'fests_unlocked': 'TRUE',
            'hackathons_unlocked': 'TRUE',
            'competitions_unlocked': 'TRUE',
            'max_fests_per_recommendation': '2',
            'max_hackathons_per_recommendation': '2',
            'max_competitions_per_recommendation': '2',
            'message_to_user': 'With core algorithmic techniques mastered, you are well-prepared for competitive programming contests and multi-round hackathons.'
        },
        {
            'highest_completed_phase_id': 'P4_Trees_and_Graphs',
            'highest_completed_phase_order': '4',
            'fests_unlocked': 'TRUE',
            'hackathons_unlocked': 'TRUE',
            'competitions_unlocked': 'TRUE',
            'max_fests_per_recommendation': '2',
            'max_hackathons_per_recommendation': '2',
            'max_competitions_per_recommendation': '2',
            'message_to_user': 'Tree and graph proficiency unlocks competitive programming rounds and complex engineering challenges across all platforms.'
        },
        {
            'highest_completed_phase_id': 'P5_Dynamic_Programming_and_Practice',
            'highest_completed_phase_order': '5',
            'fests_unlocked': 'TRUE',
            'hackathons_unlocked': 'TRUE',
            'competitions_unlocked': 'TRUE',
            'max_fests_per_recommendation': '2',
            'max_hackathons_per_recommendation': '2',
            'max_competitions_per_recommendation': '2',
            'message_to_user': 'Advanced DSA and dynamic programming skills give you a competitive edge in national-level coding contests and high-stakes hackathons.'
        },
        {
            'highest_completed_phase_id': 'P6_CS_Core_Subjects',
            'highest_completed_phase_order': '6',
            'fests_unlocked': 'TRUE',
            'hackathons_unlocked': 'TRUE',
            'competitions_unlocked': 'TRUE',
            'max_fests_per_recommendation': '2',
            'max_hackathons_per_recommendation': '2',
            'max_competitions_per_recommendation': '2',
            'message_to_user': 'Core CS knowledge in OS, DBMS, and networks prepares you for systems hackathons, hiring challenges, and technical rounds.'
        },
        {
            'highest_completed_phase_id': 'P7_System_Design_and_Backend',
            'highest_completed_phase_order': '7',
            'fests_unlocked': 'TRUE',
            'hackathons_unlocked': 'TRUE',
            'competitions_unlocked': 'TRUE',
            'max_fests_per_recommendation': '2',
            'max_hackathons_per_recommendation': '2',
            'max_competitions_per_recommendation': '2',
            'message_to_user': 'Full-stack and system design expertise positions you to lead teams in flagship buildathons and enterprise hiring hackathons.'
        },
        {
            'highest_completed_phase_id': 'P8_Interview_Readiness',
            'highest_completed_phase_order': '8',
            'fests_unlocked': 'TRUE',
            'hackathons_unlocked': 'TRUE',
            'competitions_unlocked': 'TRUE',
            'max_fests_per_recommendation': '2',
            'max_hackathons_per_recommendation': '2',
            'max_competitions_per_recommendation': '2',
            'message_to_user': 'You are fully interview-ready; target hiring hackathons and premier competitive programming contests offering direct PPI routes.'
        }
    ]

    # File 3: Recommendation Rules (R01..R14)
    rec_rules_rows = [
        {
            'rule_id': 'R01',
            'rule_name': 'MIN_PHASE_FOR_HACKATHON',
            'rule_description': 'Learner must have completed Phase 1 (Programming & Dev Basics) or any subsequent phase to receive hackathon recommendations.',
            'applies_to_category': 'HACKATHON',
            'parameter': 'min_phase_id',
            'value': 'P1_Programming_and_Dev_Basics'
        },
        {
            'rule_id': 'R02',
            'rule_name': 'MIN_PHASE_FOR_COMPETITION',
            'rule_description': 'Competitions require either Phase 1 or Phase 2 depending on whether foundational DSA or basic programming is evaluated.',
            'applies_to_category': 'COMPETITION',
            'parameter': 'min_phase_id',
            'value': 'PER_EVENT_MIN_PHASE'
        },
        {
            'rule_id': 'R03',
            'rule_name': 'FEST_ALWAYS_ELIGIBLE',
            'rule_description': 'Tech fests are eligible for recommendation at every learner stage for orientation, exposure, and inspiration.',
            'applies_to_category': 'FEST',
            'parameter': 'min_phase_id',
            'value': 'NONE'
        },
        {
            'rule_id': 'R04',
            'rule_name': 'RECOMMENDATION_SET_SIZE',
            'rule_description': 'Total number of events recommended per prompt: 6 when all categories are unlocked, or 2 (fests only) when locked.',
            'applies_to_category': 'ALL',
            'parameter': 'set_size',
            'value': '6_OR_2'
        },
        {
            'rule_id': 'R05',
            'rule_name': 'CATEGORY_MIX',
            'rule_description': 'Every recommendation set must include at least 1 event from each unlocked category where events are available.',
            'applies_to_category': 'ALL',
            'parameter': 'min_per_unlocked_category',
            'value': '1'
        },
        {
            'rule_id': 'R06',
            'rule_name': 'EXCLUDE_ENDED_EVENTS',
            'rule_description': 'Skip events whose end_month is strictly prior to the current reference month.',
            'applies_to_category': 'ALL',
            'parameter': 'end_month_cutoff',
            'value': 'CURRENT_MONTH'
        },
        {
            'rule_id': 'R07',
            'rule_name': 'EXCLUDE_CLOSED_REGISTRATION',
            'rule_description': 'Skip events whose registration_status_vs_ref_date is CLOSED, unless timeline_type is ROLLING.',
            'applies_to_category': 'ALL',
            'parameter': 'registration_status',
            'value': 'EXCLUDE_CLOSED_EXCEPT_ROLLING'
        },
        {
            'rule_id': 'R08',
            'rule_name': 'PREFER_UPCOMING',
            'rule_description': 'Prioritize events occurring within the next 1 to 4 months before recommending events further out in the season.',
            'applies_to_category': 'ALL',
            'parameter': 'upcoming_window_months',
            'value': '1-4'
        },
        {
            'rule_id': 'R09',
            'rule_name': 'PREFER_HIRING',
            'rule_description': 'When ranking otherwise comparable events, prioritize can_get_hired = YES, then POSSIBLE, then EXPOSURE_ONLY.',
            'applies_to_category': 'ALL',
            'parameter': 'hiring_rank_order',
            'value': 'YES > POSSIBLE > EXPOSURE_ONLY > NO'
        },
        {
            'rule_id': 'R10',
            'rule_name': 'PREFER_HIGH_CONFIDENCE_DATES',
            'rule_description': 'Rank HIGH confidence dates above MEDIUM above LOW; never present LOW confidence dates as confirmed.',
            'applies_to_category': 'ALL',
            'parameter': 'confidence_rank_order',
            'value': 'HIGH > MEDIUM > LOW'
        },
        {
            'rule_id': 'R11',
            'rule_name': 'ELIGIBILITY_MATCH',
            'rule_description': 'Skip women_only events for learners who do not match; verify eligibility_group against learner profile while displaying eligibility_raw.',
            'applies_to_category': 'ALL',
            'parameter': 'eligibility_filter',
            'value': 'PROFILE_COMPLIANT'
        },
        {
            'rule_id': 'R12',
            'rule_name': 'REQUIRED_FIELDS_IN_EVERY_RECOMMENDATION',
            'rule_description': 'Mandatory metadata fields that eBuddy must display in every card: event_name, category, type_raw, expected_month_range, date_wording, eligibility_raw, prize_pool_raw, can_get_hired, hiring_detail.',
            'applies_to_category': 'ALL',
            'parameter': 'mandatory_fields',
            'value': 'event_name,category,type_raw,expected_month_range,date_wording,eligibility_raw,prize_pool_raw,can_get_hired,hiring_detail'
        },
        {
            'rule_id': 'R13',
            'rule_name': 'SHOW_CAVEATS',
            'rule_description': 'Use expected wording when date_wording = EXPECTED; surface critical data quality flags (closed registration, past prize figure, unannounced dates) clearly.',
            'applies_to_category': 'ALL',
            'parameter': 'caveat_display',
            'value': 'SURFACE_QUALITY_FLAGS'
        },
        {
            'rule_id': 'R14',
            'rule_name': 'MAX_SAME_ORGANISER_PER_SET',
            'rule_description': 'Cap recommendations at a maximum of 2 events from the same organizer in any single recommendation set to maintain ecosystem diversity.',
            'applies_to_category': 'ALL',
            'parameter': 'max_same_organiser',
            'value': '2'
        }
    ]

    # Write files to both output locations
    dest_dirs = [
        "c:/Users/Dhaval/Downloads/EBuddy-main/output",
        "c:/Users/Dhaval/Downloads/EBuddy-main/EBuddy-main/output"
    ]

    for d in dest_dirs:
        os.makedirs(d, exist_ok=True)
        
        # File 1: 01_events_master.csv (and 01_sde_events_master.csv)
        f1_names = [os.path.join(d, "01_events_master.csv"), os.path.join(d, "01_sde_events_master.csv")]
        for f1_path in f1_names:
            with open(f1_path, mode="w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(fp, fieldnames=list(master_rows[0].keys()), quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                writer.writerows(master_rows)

        # File 2: 02_phase_eligibility.csv (and 02_sde_phase_eligibility.csv)
        f2_names = [os.path.join(d, "02_phase_eligibility.csv"), os.path.join(d, "02_sde_phase_eligibility.csv")]
        for f2_path in f2_names:
            with open(f2_path, mode="w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(fp, fieldnames=list(phase_elig_rows[0].keys()), quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                writer.writerows(phase_elig_rows)

        # File 3: 03_recommendation_rules.csv (and 03_sde_recommendation_rules.csv)
        f3_names = [os.path.join(d, "03_recommendation_rules.csv"), os.path.join(d, "03_sde_recommendation_rules.csv")]
        for f3_path in f3_names:
            with open(f3_path, mode="w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(fp, fieldnames=list(rec_rules_rows[0].keys()), quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                writer.writerows(rec_rules_rows)

    print("All CSV files written successfully.")

    # VALIDATION ASSERTIONS
    # 1. Row counts & uniqueness
    assert len(master_rows) == 41
    event_ids = [r['event_id'] for r in master_rows]
    assert len(set(event_ids)) == 41

    # 2. Non-empty mandatory fields
    for r in master_rows:
        assert r['expected_month_range'], f"Missing expected_month_range in {r['event_id']}"
        assert r['eligibility_raw'], f"Missing eligibility_raw in {r['event_id']}"
        assert r['prize_pool_raw'], f"Missing prize_pool_raw in {r['event_id']}"
        assert r['type_raw'], f"Missing type_raw in {r['event_id']}"
        assert r['can_get_hired'], f"Missing can_get_hired in {r['event_id']}"
        assert r['min_phase_required'], f"Missing min_phase_required in {r['event_id']}"
        assert r['date_confidence'], f"Missing date_confidence in {r['event_id']}"

    # 3. Regex checks on start_month / end_month
    for r in master_rows:
        sm = r['start_month']
        em = r['end_month']
        if sm:
            assert re.match(r'^\d{4}-\d{2}$', sm), f"Invalid start_month {sm}"
        if em:
            assert re.match(r'^\d{4}-\d{2}$', em), f"Invalid end_month {em}"
        if sm and em:
            assert em >= sm, f"end_month {em} < start_month {sm} in {r['event_id']}"

    # 4. Exact column preservation against source
    for idx, (source_row_num, vals) in enumerate(source_rows):
        m = master_rows[idx]
        assert m['source_number'] == str(vals[0]), f"Mismatch source_number row {source_row_num}"
        assert m['event_name'] == str(vals[1]).strip(), f"Mismatch event_name row {source_row_num}"
        assert m['organiser'] == str(vals[2]).strip(), f"Mismatch organiser row {source_row_num}"
        assert m['period_window_raw'] == str(vals[3]).strip(), f"Mismatch period row {source_row_num}"
        assert m['tentative_dates_raw'] == str(vals[4]).strip(), f"Mismatch tentative dates row {source_row_num}"
        assert m['date_status_raw'] == str(vals[5]).strip(), f"Mismatch date status row {source_row_num}"
        assert m['eligibility_raw'] == str(vals[6]).strip(), f"Mismatch eligibility row {source_row_num}"
        assert m['prize_pool_raw'] == str(vals[7]).strip(), f"Mismatch prize pool row {source_row_num}"
        assert m['type_raw'] == str(vals[8]).strip(), f"Mismatch type row {source_row_num}"
        assert m['hiring_raw'] == str(vals[9]).strip(), f"Mismatch hiring row {source_row_num}"
        assert m['source_to_verify'] == str(vals[10]).strip(), f"Mismatch source verify row {source_row_num}"

    # 5. File 2 and File 3 size / rules check
    assert len(phase_elig_rows) == 9
    assert len(rec_rules_rows) == 14
    for i in range(1, 15):
        assert any(r['rule_id'] == f"R{i:02d}" for r in rec_rules_rows)

    print("ALL VALIDATION ASSERTIONS PASSED (100% compliant)!")

    # PRINT REVIEW TABLE
    print("\n" + "=" * 120)
    print("REVIEW TABLE: All 41 Events (Name | Tentative Dates -> Range | Start | End | Timeline Type | Confidence)")
    print("=" * 120)
    for row in review_table:
        name, td, r_disp, sm, em, tt, conf = row
        print(f"{name[:32]:32s} | {td[:32]:32s} -> {r_disp[:28]:28s} | {sm:7s} | {em:7s} | {tt:16s} | {conf:6s}")

    # PRINT MAPPING TABLES
    print("\n" + "=" * 80)
    print("MAPPING TABLE: Hiring Link -> can_get_hired")
    print("=" * 80)
    for raw_val, mapped_val in sorted(mapping_hiring.items()):
        print(f"{raw_val:45s} -> {mapped_val}")

    print("\n" + "=" * 80)
    print("MAPPING TABLE: Date Status -> date_confidence")
    print("=" * 80)
    for raw_val, mapped_val in sorted(mapping_date_conf.items()):
        print(f"{raw_val:35s} -> {mapped_val}")

    print("\n" + "=" * 80)
    print("MAPPING TABLE: Eligibility Sample -> eligibility_group")
    print("=" * 80)
    for raw_val, mapped_val in sorted(mapping_elig_group.items())[:15]:
        print(f"{raw_val[:45]:45s} -> {mapped_val}")

    print("\n" + "=" * 80)
    print("DATA QUALITY NOTES BY EVENT")
    print("=" * 80)
    for r in master_rows:
        if r['data_quality_note']:
            print(f"[{r['event_id']}] {r['event_name'][:30]:30s} : {r['data_quality_note']}")

if __name__ == "__main__":
    main()
