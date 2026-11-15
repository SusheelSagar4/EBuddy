import pytest
from datetime import date
from app.engine.mba_date_parser import parse_mba_date_field, project_future_exam_milestone

def test_parse_exact_date():
    p = parse_mba_date_field("2026-11-29", reference_date=date(2026, 11, 15))
    assert p.start_date == date(2026, 11, 29)
    assert not p.is_range
    assert not p.is_past
    assert not p.is_expected
    assert p.status_badge == "verified"

def test_parse_past_date():
    p = parse_mba_date_field("2026-08-03", reference_date=date(2026, 11, 15))
    assert p.start_date == date(2026, 8, 3)
    assert p.is_past
    assert p.status_badge == "past"
    assert "Completed Cycle" in p.display_label

def test_parse_expected_date():
    p = parse_mba_date_field("Expected around 2026-12-20", reference_date=date(2026, 11, 15))
    assert p.start_date == date(2026, 12, 20)
    assert p.is_expected
    assert p.status_badge == "expected"
    assert "Expected:" in p.display_label

def test_parse_both_ends_of_range():
    # Window format
    p1 = parse_mba_date_field("Window 2026-11-02 to 2026-12-20", reference_date=date(2026, 11, 15))
    assert p1.start_date == date(2026, 11, 2)
    assert p1.end_date == date(2026, 12, 20)
    assert p1.is_range
    assert not p1.is_past # Ends in future
    assert "2026-11-02 to 2026-12-20" in p1.display_label

    # Semicolon-delimited list format
    p2 = parse_mba_date_field("2026-12-13; 2026-12-19; 2026-12-26", reference_date=date(2026, 11, 15))
    assert p2.start_date == date(2026, 12, 13)
    assert p2.end_date == date(2026, 12, 26)
    assert p2.is_range

def test_parse_non_date_rolling():
    p = parse_mba_date_field("Rolling / Year-round", reference_date=date(2026, 11, 15))
    assert p.start_date is None
    assert p.is_indicative
    assert p.status_badge == "indicative"
    assert "Indicative" in p.display_label

def test_project_future_exam_milestone():
    p = project_future_exam_milestone("MBA-EX-CAT", target_year=2028, base_cycle_exam_date=date(2026, 11, 29), reference_date=date(2026, 11, 15))
    assert p.is_projected
    assert p.is_indicative
    assert p.status_badge == "projected_indicative"
    assert p.display_label == "Projected, Indicative (Nov 2028)"
    assert p.start_date.year == 2028
