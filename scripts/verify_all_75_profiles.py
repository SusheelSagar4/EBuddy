#!/usr/bin/env python3
"""
Proves that every one of the 75 synthetic profiles gets a valid, constraint-compliant,
multi-semester plan with zero hallucinated course codes or resource ids.

    python scripts/verify_all_75_profiles.py          # exit code 0 only if every check passes for every profile

Runs fully offline (seed files, deterministic engine, no LLM, no database) and writes
docs/evaluation/verify_75_profiles_report.md and .json.

Checks per profile (independent re-computation - it does not just trust the validator)
  C01 plan built and validator hard checks passed
  C02 every course_id in the plan exists in data/seed/kb/course.csv            (zero hallucinated course codes)
  C03 every resource_id exists in the KB / track KB / persona resource files    (zero hallucinated resources)
  C04 prerequisites: completed before, or scheduled in an earlier-or-same semester ahead of the dependent
  C05 no completed course re-assigned and no course scheduled twice
  C06 the plan is multi-semester: covers every remaining semester up to Semester 8
  C07 student-stated credit cap respected in EVERY planned semester (hard)
  C08 student-stated weekly-hours cap respected in the current semester (hard)
  C09 institute credit baseline: any semester above it carries a labelled warning (never silent)
  C10 planning is deterministic (two runs give the same structure)
  C11 edge case ACTIVE_BACKLOG: each backlog course is scheduled, in the current semester, before electives
  C12 edge case CGPA cutoffs: minor offered iff CGPA >= cutoff, Sem >= 5, no backlog; otherwise explained
  C13 edge case INTEREST_EVIDENCE_CLASH: mismatch flagged AND a remedial item injected
  C14 edge case MID_DEGREE_GOAL_SWITCH: switching back to the previous goal yields a PlanDiff and keeps all evidence
  C15 edge cases TIGHT_WEEKLY_HOURS / TIGHT_CREDIT_CAP: cap honoured and the trade-off is explained to the student
  C16 goal coverage: every goal skill with a gap is targeted by some plan item (covered or explained)
"""
import os
import sys
import csv
import json
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
os.environ["EBUDDY_DB_SYNC"] = "off"      # hermetic: seed files only
os.environ["LLM_MODEL"] = "fake"

from app.services.onboarding_service import onboarding_service  # noqa: E402
from app.services.diagnostic_service import diagnostic_service  # noqa: E402
from app.services.plan_service import plan_service  # noqa: E402

CHECKS = ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10", "C11", "C12", "C13", "C14", "C15", "C16"]
NAMES = {
    "C01": "validator passed", "C02": "course codes exist", "C03": "resource ids exist", "C04": "prerequisites",
    "C05": "no duplicates", "C06": "multi-semester", "C07": "credit cap", "C08": "weekly hours cap",
    "C09": "baseline warning labelled", "C10": "deterministic", "C11": "backlog first", "C12": "CGPA cutoffs",
    "C13": "interest vs evidence", "C14": "goal switch", "C15": "tight caps explained", "C16": "goal skills covered",
}


def structure(plan):
    return [(it.item_type, it.course_id, it.resource_id, it.track_phase_id, it.semester_number, tuple(it.reason.target_skills)) for it in plan.items]


def main() -> int:
    planner, validator = plan_service.planner, plan_service.validator
    with open(os.path.join("data", "seed", "kb", "course.csv"), encoding="utf-8") as f:
        catalogue = {r["course_id"]: float(r["credits"]) for r in csv.DictReader(f)}
    prereqs = {}
    with open(os.path.join("data", "seed", "kb", "course_prerequisite.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            prereqs.setdefault(r["course_id"], []).append(r["prereq_id"])

    students = onboarding_service.get_all_synthetic_students()
    rows, failures = [], []
    totals = {"plans": 0, "course_items": 0, "distinct_courses": set(), "resource_items": 0, "semesters": 0}

    for s in students:
        sid = s["student_id"]
        tags = set(s["edge_case_tags"])
        res = {c: "n/a" for c in CHECKS}
        notes = []

        def fail(c, msg):
            res[c] = "FAIL"
            notes.append(f"{c}: {msg}")
            failures.append((sid, c, msg))

        try:
            onboarding_service.ensure_student_onboarded(sid)
            plan_service.create_or_update_plan(sid, trigger="initial")
            plan = plan_service.get_plan(sid)
        except Exception as e:  # a crash is a failure of everything
            for c in CHECKS:
                res[c] = "FAIL"
            failures.append((sid, "C01", f"exception: {e}"))
            rows.append((s, res, [f"exception: {e}"], None))
            continue

        st = onboarding_service.students[sid]
        completed = set(onboarding_service.completed_courses.get(sid, []))
        cons = planner.parse_constraints(onboarding_service.constraints.get(sid, []))
        cur = st.current_semester
        courses = [it for it in plan.items if it.item_type == "course" and it.course_id]
        courses_sorted = sorted(enumerate(courses), key=lambda p: ((p[1].semester_number or cur), p[0]))
        totals["plans"] += 1
        totals["course_items"] += len(courses)
        totals["distinct_courses"].update(it.course_id for it in courses)
        totals["resource_items"] += sum(1 for it in plan.items if it.resource_id)

        # C01
        res["C01"] = "PASS" if (plan.validation_report and plan.validation_report.passed and len(plan.items) > 0) else "FAIL"
        if res["C01"] == "FAIL":
            fail("C01", "; ".join(plan.validation_report.messages) if plan.validation_report else "no report")
        # C02 / C03
        bad = sorted({it.course_id for it in plan.items if it.course_id and it.course_id not in catalogue})
        res["C02"] = "PASS" if not bad else "FAIL"
        if bad:
            fail("C02", f"unknown course codes {bad}")
        badr = sorted({it.resource_id for it in plan.items if it.resource_id and it.resource_id not in validator.valid_resources})
        res["C03"] = "PASS" if not badr else "FAIL"
        if badr:
            fail("C03", f"unknown resource ids {badr}")
        # C04
        have = set(completed)
        if st.backlogs == 0 and cur > 1:   # same inference rule as the engine: no backlog => earlier semesters cleared
            for sem in range(1, cur):
                have.update((r.get("course_id") or "").strip() for r in planner.requirement_rows(planner_prog(st), sem, st.first_year_track))
        viol = []
        for _i, it in courses_sorted:
            for p in prereqs.get(it.course_id, []):
                if p not in have:
                    viol.append(f"{it.course_id} needs {p}")
            have.add(it.course_id)
        res["C04"] = "PASS" if not viol else "FAIL"
        if viol:
            fail("C04", "; ".join(viol[:4]))
        # C05
        ids = [it.course_id for it in courses]
        dup = sorted({c for c in ids if ids.count(c) > 1} | (set(ids) & completed))
        res["C05"] = "PASS" if not dup else "FAIL"
        if dup:
            fail("C05", f"duplicate or already-completed {dup}")
        # C06
        sems = sorted({it.semester_number for it in plan.items if it.semester_number})
        want = list(range(cur, 9))
        totals["semesters"] += len(want)
        have_course_sems = {it.semester_number for it in plan.items if it.item_type == "course"}
        res["C06"] = "PASS" if all(x in have_course_sems for x in want) and max(sems) <= 8 else "FAIL"
        if res["C06"] == "FAIL":
            fail("C06", f"planned semesters {sorted(have_course_sems)} but expected {want}")
        # credits per semester (independent sum; open slots carry their own reserved credits)
        sem_credits = {}
        for it in plan.items:
            if it.item_type != "course":
                continue
            cr = catalogue[it.course_id] if it.course_id in catalogue else float(it.credits or 0.0)
            sem_credits[it.semester_number or cur] = sem_credits.get(it.semester_number or cur, 0.0) + cr
        # C07
        if cons["credit_cap"] is not None:
            cap = cons["credit_cap"] - cons["headroom"]
            over = {k: v for k, v in sem_credits.items() if v > cap + 1e-9}
            res["C07"] = "PASS" if not over else "FAIL"
            if over:
                fail("C07", f"credit cap {cap} exceeded: {over}")
        # C08
        if cons["weekly_hours"] is not None:
            used = round(sum((it.prep_hours_weekly or 0.0) for it in plan.items
                             if (it.semester_number or cur) == cur and it.planning_status in (None, "current")), 1)
            res["C08"] = "PASS" if used <= cons["weekly_hours"] + 0.05 else "FAIL"
            if res["C08"] == "FAIL":
                fail("C08", f"{used} h > cap {cons['weekly_hours']} h")
        # C09
        inst = (plan.horizon or {}).get("institute_credit_cap", 26.0)
        over_inst = [k for k, v in sem_credits.items() if v > inst + 1e-9]
        if over_inst:
            labelled = any(c.severity == "warning" and "CREDIT_CAP" in c.check_name for c in plan.validation_report.checks)
            res["C09"] = "PASS" if labelled else "FAIL"
            if not labelled:
                fail("C09", f"semesters {over_inst} exceed the institute baseline without a labelled warning")
        # C10
        goal = onboarding_service.goals[sid]
        states = diagnostic_service.skill_states.get(sid, [])
        ev = diagnostic_service.evidence_ledger.get(sid, [])
        gaps = plan_service.gap_analyzer.analyze_gaps(goal, plan_service.requirements_for(goal.goal_id), states, evidence=ev)
        kw = dict(student=st, goal=goal, gaps=gaps, constraints=onboarding_service.constraints.get(sid, []), preferences=[],
                  completed_course_ids=list(completed), skill_states=states, aims_text=onboarding_service.aims_and_aspirations.get(sid),
                  horizon="degree", evidence=ev, interests=onboarding_service.interests.get(sid, []))
        res["C10"] = "PASS" if structure(planner.generate_plan(**kw)) == structure(planner.generate_plan(**kw)) == structure(plan) else "FAIL"
        if res["C10"] == "FAIL":
            fail("C10", "two runs produced different plans")
        # C11
        if "ACTIVE_BACKLOG" in tags:
            ok = True
            for b in s["backlog_courses"]:
                item = next((it for it in courses if it.course_id == b), None)
                first_elec = next((i for i, it in enumerate(courses) if it.item_id.startswith("ITEM_ELEC_") and it.semester_number == cur), 10 ** 6)
                if item is None or item.semester_number != cur or "Backlog" not in item.reason.intent or courses.index(item) > first_elec:
                    ok = False
            res["C11"] = "PASS" if ok and s["backlog_courses"] else "FAIL"
            if res["C11"] == "FAIL":
                fail("C11", f"backlog {s['backlog_courses']} not prioritised in the current semester")
        # C12
        if tags & {"CGPA_ON_MINOR_CUTOFF", "CGPA_ON_OVERLOAD_CUTOFF"}:
            cutoff = planner.rule_engine.minor_cutoff()
            eligible = (st.cgpa or 0) >= cutoff and cur >= 5 and st.backlogs == 0
            minor_items = [it for it in plan.items if "Minor" in it.reason.intent]
            explained = any(p.get("status") == "ineligible_explanation" for p in plan.optional_overload_proposals)
            if cur >= 5:
                ok = (not minor_items and explained) if not eligible else True
                if eligible and not minor_items:
                    # allowed only when the minor course was withheld for a stated reason (cap / avoid / already taken)
                    ok = any("credit limit" in (p.get("reason") or "") or p.get("proposal_id", "").startswith(("PROP_AVOID", "PROP_NOT_TOGETHER"))
                             for p in plan.optional_overload_proposals) or all(c in completed or c in ids for c in planner.minor_courses.get("MINOR_CSE", []))
            else:
                ok = not minor_items
            res["C12"] = "PASS" if ok else "FAIL"
            if not ok:
                fail("C12", f"cgpa {st.cgpa} cutoff {cutoff}: minor_items={len(minor_items)} explained={explained}")
        # C13
        if "INTEREST_EVIDENCE_CLASH" in tags:
            mm = plan.mismatch_warning
            rem = [it for it in plan.items if it.item_type == "remediation"]
            ok = bool(mm and mm.get("mismatch_detected")) and bool(rem)
            res["C13"] = "PASS" if ok else "FAIL"
            if not ok:
                fail("C13", f"mismatch={bool(mm)} remediation_items={len(rem)}")
        # C15 (before C14, which changes the plan)
        if tags & {"TIGHT_WEEKLY_HOURS", "TIGHT_CREDIT_CAP"}:
            wb = (plan.horizon or {}).get("weekly_budget", {})
            explained = bool(plan.advisories) or bool(plan.optional_overload_proposals) or bool((plan.horizon or {}).get("deferred_mandatory"))
            ok = wb.get("within_cap", True) and explained and res["C07"] != "FAIL" and res["C08"] != "FAIL"
            res["C15"] = "PASS" if ok else "FAIL"
            if not ok:
                fail("C15", "tight cap not honoured or not explained")
        # C16
        covered = {sk for it in plan.items for sk in it.reason.target_skills}
        missing = [g["skill_id"] for g in gaps if g["gap"] > 0 and g["skill_id"] not in covered]
        res["C16"] = "PASS" if not missing else "FAIL"
        if missing:
            fail("C16", f"goal skills without any plan item: {missing}")
        # C14
        if "MID_DEGREE_GOAL_SWITCH" in tags and s["previous_goal_ids"]:
            n_ev = len(diagnostic_service.evidence_ledger.get(sid, []))
            n_done = len(onboarding_service.completed_courses.get(sid, []))
            v0 = plan.version
            onboarding_service.switch_goal(sid, s["previous_goal_ids"][0], persist=False)
            out = plan_service.create_or_update_plan(sid, trigger="verify:goal_switch")
            p2 = plan_service.get_plan(sid)
            ok = (p2.version == v0 + 1 and p2.plan_diff is not None and p2.validation_report.passed
                  and len(diagnostic_service.evidence_ledger.get(sid, [])) == n_ev
                  and len(onboarding_service.completed_courses.get(sid, [])) == n_done
                  and any("Goal changed" in r for r in p2.plan_diff.reasons)
                  and not [it.course_id for it in p2.items if it.course_id and it.course_id not in catalogue])
            res["C14"] = "PASS" if ok else "FAIL"
            if not ok:
                fail("C14", "goal switch did not produce a valid, explained diff with evidence preserved")
            onboarding_service.switch_goal(sid, s["goal_id"], persist=False)
            plan_service.create_or_update_plan(sid, trigger="verify:restore_goal")

        rows.append((s, res, notes, {"credits": {k: round(v, 1) for k, v in sorted(sem_credits.items())}, "items": len(plan.items)}))

    # ------------------------------------------------------------------ report
    ok_profiles = sum(1 for _s, r, _n, _x in rows if "FAIL" not in r.values())
    per_check = {c: {"pass": sum(1 for _s, r, _n, _x in rows if r[c] == "PASS"), "fail": sum(1 for _s, r, _n, _x in rows if r[c] == "FAIL"),
                     "na": sum(1 for _s, r, _n, _x in rows if r[c] == "n/a")} for c in CHECKS}
    out_dir = os.path.join("docs", "evaluation")
    os.makedirs(out_dir, exist_ok=True)
    summary = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "profiles": len(rows), "profiles_all_checks_passed": ok_profiles, "failures": len(failures),
        "plans_built": totals["plans"], "course_items_checked": totals["course_items"],
        "distinct_course_codes_used": len(totals["distinct_courses"]), "hallucinated_course_codes": per_check["C02"]["fail"],
        "resource_items_checked": totals["resource_items"], "semesters_planned": totals["semesters"],
        "per_check": {c: dict(per_check[c], name=NAMES[c]) for c in CHECKS},
        "failed": [{"student_id": a, "check": b, "detail": c} for a, b, c in failures],
    }
    with open(os.path.join(out_dir, "verify_75_profiles_report.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    md = ["# Verification of all 75 student profiles", "",
          f"**Run:** {summary['generated_at']} - offline, deterministic engine, no LLM, no database  ",
          f"**Result:** {ok_profiles} / {len(rows)} profiles pass every applicable check; {len(failures)} failed check(s).  ",
          f"**Scope:** {totals['plans']} multi-semester plans, {totals['semesters']} planned semesters, {totals['course_items']} course placements "
          f"({len(totals['distinct_courses'])} distinct course codes, all present in `kb.course`), {totals['resource_items']} resource references.", "",
          "## Checks", "", "| Check | What is verified | Pass | Fail | Not applicable |", "|---|---|---|---|---|"]
    for c in CHECKS:
        md.append(f"| {c} | {NAMES[c]} | {per_check[c]['pass']} | {per_check[c]['fail']} | {per_check[c]['na']} |")
    md += ["", "`Not applicable` means the profile does not have that constraint or edge case (for example C07 applies only to students who stated a credit cap).",
           "", "## Per profile", "", "| Student | Prog | Sem | CGPA | Goal | Edge cases | Credits per planned semester | " + " | ".join(CHECKS) + " |",
           "|---|---|---|---|---|---|---|" + "---|" * len(CHECKS)]
    for s, r, _n, x in rows:
        cred = " ".join(f"S{k}:{v}" for k, v in (x or {}).get("credits", {}).items())
        cells = " | ".join({"PASS": "ok", "FAIL": "**FAIL**", "n/a": "-"}[r[c]] for c in CHECKS)
        md.append(f"| `{s['student_id']}` | {s['programme_id'][-2:]} | {s['current_semester']} | {s['cgpa']:.2f} | {s['goal_id'].replace('GOAL_', '')} | "
                  f"{', '.join(s['edge_case_tags']) or '-'} | {cred} | {cells} |")
    if failures:
        md += ["", "## Failures", ""] + [f"- `{a}` {b}: {c}" for a, b, c in failures]
    with open(os.path.join(out_dir, "verify_75_profiles_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    print(f"Profiles verified            : {len(rows)}")
    print(f"All applicable checks passed : {ok_profiles} / {len(rows)}")
    print(f"Course placements checked    : {totals['course_items']} ({len(totals['distinct_courses'])} distinct codes, hallucinated: {per_check['C02']['fail']})")
    for c in CHECKS:
        print(f"  {c} {NAMES[c]:28s} pass={per_check[c]['pass']:3d} fail={per_check[c]['fail']:3d} n/a={per_check[c]['na']:3d}")
    for a, b, c in failures[:25]:
        print(f"  FAIL {a} {b}: {c}")
    print("Report: docs/evaluation/verify_75_profiles_report.md")
    return 0 if not failures and len(rows) == 75 else 1


def planner_prog(st) -> str:
    p = (st.programme_id or "").upper()
    return "BTECH_MM" if p in ("BTECH_MME", "MME", "MM") else p


if __name__ == "__main__":
    sys.exit(main())
