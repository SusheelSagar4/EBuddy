"""
Team decisions on the official-curriculum discrepancies:
  * ML4L001-ML4L003 name two different courses each (Sem VII core and an elective): all six are kept, codes are
    never treated as unique, and every place a student sees them shows the duplicate-code warning.
  * EE6L007's prerequisite is EE3L010; the official wording is kept and shown as a note.
  * Other discrepancies keep the first-listed value and show a note; nothing is silently changed.
"""
import csv
import os

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.kb.course_notes import course_notes, CODE_CLASH_WARNING
from app.kb.repositories import CourseRepo

client = TestClient(app)
SEED_KB = os.path.join("data", "seed", "kb")
CLASH = {
    "ML4L001": {"ML4L001_CORE": "Light metals and alloys", "ML4L001_ELEC": "Joining of metals and alloys"},
    "ML4L002": {"ML4L002_CORE": "Elements of electroceramics", "ML4L002_ELEC": "Solidification of metals and alloys"},
    "ML4L003": {"ML4L003_CORE": "Polymers and nanocomposites", "ML4L003_ELEC": "Electrochemical methods in metallurgy"},
}
BOTH_IN_ONE_SEMESTER = "CONF_STU_UPSC_02"  # its plan has ML4L001_CORE and ML4L001_ELEC in Semester 7


def rows(name):
    with open(os.path.join(SEED_KB, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.fixture(autouse=True)
def clean_state():
    client.post("/api/admin/reset")
    yield
    client.post("/api/admin/reset")


# ----------------------------------------------------------------------------- duplicate codes ML4L001-ML4L003
def test_all_six_clashing_courses_are_kept_as_separate_records():
    courses = {r["course_id"]: r for r in rows("course.csv")}
    for code, members in CLASH.items():
        for cid, title in members.items():
            c = courses[cid]
            assert c["display_code"] == code and c["title"] == title
            assert (c["ltp"], float(c["credits"])) == ("3-0-0", 3.0)
            assert c["code_conflict"] == "True"


def test_code_lookups_return_every_course_with_that_code():
    repo = CourseRepo()
    for code, members in CLASH.items():
        assert sorted(course_notes.resolve(code)) == sorted(members)
        assert sorted(c.course_id for c in repo.get_by_code(code)) == sorted(members)
    # internal ids stay exact
    assert course_notes.resolve("ML4L001_ELEC") == ["ML4L001_ELEC"]


def test_every_clashing_course_carries_the_exact_warning():
    for members in CLASH.values():
        for cid in members:
            texts = [n["text"] for n in course_notes.notes_for(cid) if n["type"] == "code_conflict"]
            assert texts == [CODE_CLASH_WARNING]
    assert CODE_CLASH_WARNING == "The official curriculum uses this code for two different courses. Please confirm with the department."


def test_roadmap_shows_printed_code_and_warning_for_both_courses():
    plan = client.post(f"/api/v2/students/{BOTH_IN_ONE_SEMESTER}/select").json() and \
        client.get(f"/api/v2/students/{BOTH_IN_ONE_SEMESTER}/plan").json()
    rows_by_id = {c["course_id"]: c for s in plan["semesters"] for c in s["courses"]}
    assert {"ML4L001_CORE", "ML4L001_ELEC"} <= set(rows_by_id)
    for cid in ("ML4L001_CORE", "ML4L001_ELEC"):
        row = rows_by_id[cid]
        assert row["display_code"] == "ML4L001"
        assert CODE_CLASH_WARNING in [n["text"] for n in row["course_notes"]]
    # a course without a discrepancy has no notes
    plain = next(c for c in rows_by_id.values() if not c["course_id"].startswith("ML4L00"))
    assert plain["course_notes"] == [] or all(n["type"] != "code_conflict" for n in plain["course_notes"])


def test_learn_cards_and_legacy_roadmap_show_the_warning():
    from app.services.onboarding_service import onboarding_service
    sem7 = next(s for s in onboarding_service.get_all_synthetic_students()
                if s["programme_id"] == "BTECH_MM" and s["current_semester"] == 7)
    learn = client.get(f"/api/v2/students/{sem7['student_id']}/learn").json()
    clash_cards = [c for c in learn["courses"] if c["course_id"] in CLASH["ML4L001"] | CLASH["ML4L002"] | CLASH["ML4L003"]]
    assert clash_cards, "a Sem VII MME student should study at least one ML4L00x course"
    assert all(CODE_CLASH_WARNING in [n["text"] for n in c["course_notes"]] for c in clash_cards)
    legacy = client.get(f"/api/roadmap/{BOTH_IN_ONE_SEMESTER}").json()
    items = [it for s in legacy["semesters"].values() for it in s] if isinstance(legacy.get("semesters"), dict) \
        else [it for s in legacy.get("semesters", []) for it in s.get("items", [])]
    ml = [it for it in items if it.get("course_id") == "ML4L001_CORE" and it.get("item_type") == "course"]
    assert ml and ml[0]["kb_code"] == "ML4L001"
    assert CODE_CLASH_WARNING in [n["text"] for n in ml[0]["course_notes"]]


def test_chat_describes_both_courses_behind_a_code():
    from app.services.chat_service import chat_service
    from app.services.onboarding_service import onboarding_service
    onboarding_service.ensure_student_onboarded(BOTH_IN_ONE_SEMESTER)
    text = chat_service.handle_side_question(BOTH_IN_ONE_SEMESTER, "What is ML4L001?", {"plan_version": 1})
    assert "Light metals and alloys" in text and "Joining of metals and alloys" in text
    assert text.count(CODE_CLASH_WARNING) == 2


def test_why_is_this_course_on_my_roadmap_finds_clashing_codes():
    """Agent 4 compared the typed code with internal ids, so ML4L001 was always 'not in your roadmap'."""
    client.post(f"/api/v2/students/{BOTH_IN_ONE_SEMESTER}/select")
    r = client.post(f"/api/student/{BOTH_IN_ONE_SEMESTER}/chat", json={"message": "Why is ML4L001 on my roadmap?"}).json()
    assert "not in your current roadmap" not in r["response"]
    assert "Light metals and alloys" in r["response"] and "Joining of metals and alloys" in r["response"]
    assert CODE_CLASH_WARNING in r["response"]


def test_chat_shows_notes_for_a_course_that_is_not_in_the_plan():
    """EE6L007 is in no seed plan; asking about it in chat must still show the official-wording note."""
    sid = "SYN_EE_S5_057"
    client.post(f"/api/v2/students/{sid}/select")
    r = client.post(f"/api/student/{sid}/chat", json={"message": "What is EE6L007?"}).json()
    assert "Measurement and Electronic Instruments" in r["response"] and "EE3L010" in r["response"]


def test_ambiguous_code_is_refused_when_creating_a_student():
    base = {"name": "Code Test", "programme_id": "BTECH_MM", "current_semester": 8, "goal_id": "GOAL_TRACK_SDE"}
    r = client.post("/api/v2/students", json={**base, "student_id": "CODE_TEST_1", "completed_course_ids": ["ML4L001"]})
    assert r.status_code == 400
    assert "ML4L001_CORE" in r.json()["detail"] and "ML4L001_ELEC" in r.json()["detail"]
    ok = client.post("/api/v2/students", json={**base, "student_id": "CODE_TEST_2", "completed_course_ids": ["ML4L001_ELEC"]})
    assert ok.status_code == 200
    from app.services.onboarding_service import onboarding_service
    assert onboarding_service.completed_courses["CODE_TEST_2"] == ["ML4L001_ELEC"]


# ----------------------------------------------------------------------------- EE6L007 prerequisite
def test_ee6l007_requires_ee3l010_and_keeps_the_official_wording():
    prereqs = [(r["course_id"], r["prereq_id"]) for r in rows("course_prerequisite.csv")]
    assert ("EE6L007", "EE3L010") in prereqs
    notes = [n["text"] for n in course_notes.notes_for("EE6L007")]
    assert any("Measurement and Electronic Instruments" in t and "EE3L010" in t for t in notes)
    from app.services.plan_service import plan_service
    assert "EE3L010" in plan_service.planner.rule_engine.prereqs.get("EE6L007", []) or \
        "EE3L010" in [p for p in plan_service.validator.prereqs.get("EE6L007", [])]


def test_validator_rejects_ee6l007_without_ee3l010():
    """No seed plan happens to pick EE6L007, so the rule is checked on a plan that includes it explicitly."""
    from app.services.onboarding_service import onboarding_service
    from app.services.plan_service import plan_service
    sid = "SYN_EE_S5_057"
    student = onboarding_service.ensure_student_onboarded(sid)
    plan = plan_service.get_or_create(sid)
    template = next(it for it in plan.items if it.item_type == "course")
    elective = template.model_copy(update={"item_id": "TEST_EE6L007", "course_id": "EE6L007", "semester_number": 7,
                                           "title": "Industrial Instrumentation"})
    without = [it for it in plan.items if it.course_id != "EE3L010"] + [elective]
    done = [c for c in onboarding_service.completed_courses.get(sid, []) if c != "EE3L010"]

    report = plan_service.validator.validate_plan(plan.model_copy(update={"items": without}), student, completed_course_ids=done)
    check = next(c for c in report.checks if c.check_name == "prerequisites")
    assert not check.passed and "EE6L007 requires EE3L010" in check.message

    report = plan_service.validator.validate_plan(plan.model_copy(update={"items": without}), student,
                                                  completed_course_ids=done + ["EE3L010"])
    assert all("EE6L007" not in c.message for c in report.checks if c.check_name == "prerequisites" and not c.passed)
    assert plan_service.planner.rule_engine.check_prerequisites("EE6L007", ["EE3L010"])
    assert not plan_service.planner.rule_engine.check_prerequisites("EE6L007", [])


# ----------------------------------------------------------------------------- other discrepancies
@pytest.mark.parametrize("course_id,field,value,phrase", [
    ("EE2L003", "title", "Electric Machines", "EE3L001"),
    ("EE3L003", "credits", "4.0", "3 credits"),
    ("EE4L005", "credits", "3.0", "4 credits"),
    ("EE4L006", "credits", "3.0", "4 credits"),
    ("EC6L002", "credits", "4.0", "3 credits"),
    ("EC4L003", "title", "VLSI Design", "Introduction to VLSI Design"),
    ("EC6L023", "title", "Adaptive Signal Processing", "Adaptive Digital Signal Processing"),
    ("ID2L003", "course_id", "ID2L003", "ID3L003"),
])
def test_discrepancies_keep_the_first_value_and_carry_a_note(course_id, field, value, phrase):
    course = {r["course_id"]: r for r in rows("course.csv")}[course_id]
    assert course[field] == value
    assert any(phrase in n["text"] for n in course_notes.notes_for(course_id))


def test_other_official_names_and_codes_resolve_to_the_chosen_course():
    assert course_notes.resolve("Introduction to VLSI Design") == ["EC4L003"]
    assert course_notes.resolve("Adaptive Digital Signal Processing") == ["EC6L023"]
    assert course_notes.resolve("EE3L001") == ["EE2L003"]
    assert course_notes.resolve("ID3L003") == ["ID2L003"]


def test_course_notes_reference_real_courses_and_sources():
    course_ids = {r["course_id"] for r in rows("course.csv")}
    source_ids = {r["source_id"] for r in rows("source.csv")}
    note_rows = rows("course_note.csv")
    assert len({r["note_id"] for r in note_rows}) == len(note_rows)
    for r in note_rows:
        assert r["course_id"] in course_ids, r["note_id"]
        assert r["source_id"] in source_ids, r["note_id"]
        assert r["note_text"].strip()
    # every course flagged code_conflict in course.csv has an explicit note row
    flagged = {r["course_id"] for r in rows("course.csv") if r["code_conflict"] == "True"}
    assert flagged == {r["course_id"] for r in note_rows if r["note_type"] == "code_conflict"}
