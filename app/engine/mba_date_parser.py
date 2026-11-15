import re
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

CURRENT_SYSTEM_DATE = date(2026, 11, 15)

class ParsedDateResult(BaseModel):
    raw_text: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_range: bool = False
    is_expected: bool = False
    is_past: bool = False
    is_projected: bool = False
    is_indicative: bool = False
    status_badge: str = "verified" # verified, expected, past, projected_indicative, indicative
    display_label: str = ""

def parse_mba_date_field(
    text: Optional[str],
    reference_date: date = CURRENT_SYSTEM_DATE
) -> ParsedDateResult:
    """
    Parses date fields from kb.mba_exam_cycle and milestones:
    - Parses both ends of ranges (e.g. 'Window 2026-11-02 to 2026-12-20' or '2026-12-13; 2026-12-19; 2026-12-26').
    - Labels 'Expected ...' or tentative dates as expected.
    - Never treats past dates/cycles as upcoming.
    - For non-date/relative strings ('Rolling', 'Year-round'), returns labelled indicative items.
    """
    if not text or not text.strip():
        return ParsedDateResult(
            raw_text="",
            is_indicative=True,
            status_badge="indicative",
            display_label="Dates TBA (Indicative)"
        )

    raw = text.strip()
    is_expected = bool(re.search(r'\b(expected|tentative|approx|around)\b', raw, re.IGNORECASE))
    
    # Extract all ISO date occurrences (YYYY-MM-DD)
    date_matches = re.findall(r'\b(\d{4}-\d{2}-\d{2})\b', raw)
    parsed_dates: List[date] = []
    for d_str in date_matches:
        try:
            dt = datetime.strptime(d_str, "%Y-%m-%d").date()
            parsed_dates.append(dt)
        except ValueError:
            pass

    if not parsed_dates:
        # Non-parseable or rolling text
        return ParsedDateResult(
            raw_text=raw,
            is_indicative=True,
            status_badge="indicative",
            display_label=f"{raw} (Indicative)"
        )

    start_d = parsed_dates[0]
    end_d = parsed_dates[-1] if len(parsed_dates) > 1 else None
    is_range = end_d is not None and start_d != end_d

    # Determine past vs upcoming
    final_bound = end_d if end_d else start_d
    is_past = final_bound < reference_date

    # Determine status badge and display label
    if is_past:
        badge = "past"
        lbl = f"Completed Cycle: {raw}"
    elif is_expected:
        badge = "expected"
        lbl = f"Expected: {start_d.isoformat()}" + (f" to {end_d.isoformat()}" if is_range and end_d else "")
    else:
        badge = "verified"
        if is_range and end_d:
            lbl = f"{start_d.isoformat()} to {end_d.isoformat()}"
        else:
            lbl = start_d.isoformat()

    return ParsedDateResult(
        raw_text=raw,
        start_date=start_d,
        end_date=end_d,
        is_range=is_range,
        is_expected=is_expected,
        is_past=is_past,
        is_projected=False,
        is_indicative=is_expected,
        status_badge=badge,
        display_label=lbl
    )

def project_future_exam_milestone(
    exam_id: str,
    target_year: int,
    base_cycle_exam_date: Optional[date] = None,
    reference_date: date = CURRENT_SYSTEM_DATE
) -> ParsedDateResult:
    """
    For far-future targets, projects from the latest known cycle and labels
    'projected, indicative'. Never presents a projected date as real.
    """
    if target_year <= reference_date.year:
        raise ValueError(f"Target year {target_year} is not in the future relative to {reference_date.year}")

    # Project month/day from base known date (e.g. late Nov for CAT)
    if not base_cycle_exam_date:
        base_cycle_exam_date = date(2026, 11, 29) # Default base CAT

    try:
        # Project same month and approximate last week
        projected = date(target_year, base_cycle_exam_date.month, base_cycle_exam_date.day)
    except ValueError:
        # Leap year handling or 31/30 adjustment
        projected = date(target_year, base_cycle_exam_date.month, 28)

    return ParsedDateResult(
        raw_text=f"Projected from cycle {base_cycle_exam_date.year} for target {target_year}",
        start_date=projected,
        end_date=None,
        is_range=False,
        is_expected=True,
        is_past=False,
        is_projected=True,
        is_indicative=True,
        status_badge="projected_indicative",
        display_label=f"Projected, Indicative ({projected.strftime('%b %Y')})"
    )
