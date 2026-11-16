# Changelog of the Claude upgrade run

## 1. Overview
- End-to-end upgrade of the EBuddy repository: workspace clean-up, first-class career tracks (SDE, Data Analyst, AI/ML), 75 synthetic profiles, multi-semester planner, adaptation simulator, mastery reporting, LLM guardrails, admin re-processing, Docker stack, tests.
- Full per-file lists: [`docs/CHANGELOG_FILE_LISTS.md`](CHANGELOG_FILE_LISTS.md) (66 added, 79 modified, 116 deleted, 36 moved; compared by sha256 against the original upload).
- Follow-up pass: `docs/INTER_IIT_MASTER_SUBMISSION.md` written, `.env.example` and the `README.md` body rewritten, `pyyaml>=6.0.3` added to `requirements.txt` (fresh-venv install and persona import confirmed: 9 personas).

## 2. Pre-existing bugs fixed
- **Database reset never completed.** `scripts/seed_loader.py --reset` stopped at `kb.module` (foreign key to course codes `EE3L001`/`EE3L002`, which are not in the catalogue). Fixed the module seed, then seven further schema/seed mismatches behind it (book resources with no URL, paper chunk ids, MBA fee/date text columns, a reserved column name, core-to-core research areas and faculty never loaded, sample rows for a non-existent student). Reset now loads 8,072 rows.
- **Planner scheduled elective options as mandatory courses** (a semester-7 EE student got 17 courses and 52 credits). Pick-one slots now get exactly one course; semester 7 is 18-22 credits.
- **Web screens called endpoints that did not exist** (`/progress`, `/learn/submit`, `/plan/validate`, `/api/admin/kb-stats`) and sent mismatched payloads; `diagnostic_service.record_answer` was called but not defined.
- **Semester-2 prerequisite cases:** the planner assumed first-year courses were complete for semester-2 students, and a course could stay ahead of a prerequisite deferred by a credit cap. Both found by the verifier and fixed.
- **Profile generator** picked an elective option as a backlog course; backlogs are now mandatory courses only.
- **Weak-evidence count display:** investigated after one screenshot showed 0; the API returned the correct count, no code change was needed.
- **Duplicate track files:** root-level `.xlsx`, `build_*.py`, `output/`, `data_analyst/`, `ai_ml/` and `docsteamFOUNDATION_PROMPT.md.md` removed (all were exact duplicates). The eight build scripts now write once to `<track>/output/{curriculum,events,quiz}/`; re-running them reproduced all 36 CSVs with identical content (line endings normalised).
- `REQ_EE_EC2L005` (a syllabus-only course) is no longer treated as a mandatory EE semester-3 course. Hard-coded database connection strings removed from `app/`.

## 3. Backend APIs (new or changed)
- `app/api/buddy.py` (new, `/api/v2`): students, goals, tracks, select/create student, overview, plan, learn, practice, progress, evidence.
- `app/api/simulator.py`: `GET /api/sim/presets`, `POST /api/sim/{student_id}/preset/{strong_quiz|weak_quiz|course_rejection|goal_switch}` returning a `PlanDiff` plus reasons.
- `app/api/admin.py`: student detail and edit, evidence edit, course edit, rule edit, `POST /api/admin/reset`, re-processing log, overview. Every edit re-plans immediately.
- `app/services/plan_service.py` is the single plan store, shared with Agent 1 and the orchestrator; `reprocess_service.py` polls `ops.reprocess_queue` for direct database edits.
- `app/db/persistence.py` (new): best-effort PostgreSQL mirror, settings from the environment only.

## 4. Web screens (`web/src/screens/`)
- Rewritten: `onboarding.js` (75-profile picker with filters, goal switch, new-student form), `plan.js` (semester-by-semester roadmap with reasons, validator checks, track phases, evidence table, version history), `learn.js`, `adapt.js` (four one-click presets with diff), `progress.js` (completion and demonstrated proficiency side by side), `admin.js`, `diagnostic.js` (adaptive, one question at a time).
- `chat.js` lightly edited; `mba.js` and `mtech.js` untouched. The app is served at `/app/`; the older Jinja pages remain at `/`.
- Checked once in a headless browser across all screens with zero console or HTTP errors (before the last planner fixes; not re-run afterwards).

## 5. Personas, profiles and verifier
- Nine persona packages in `app/personas/`: the four existing ones plus `sde_career`, `da_career`, `aiml_career`, `core_higher_studies`, `core_to_mba`.
- `python scripts/generate_75_student_profiles.py` writes `data/seed/student/*.csv` and the persona rosters (41 EE, 34 MME; years 1-4); `--check` confirms files match the generator.
- Edge cases tagged: 8 active backlog, 7 CGPA on the minor cutoff, 4 on the 8.50 overload cutoff, 8 interest-vs-evidence clash, 9 goal switch, 8 tight weekly hours, 6 tight credit cap.
- `python scripts/verify_all_75_profiles.py` runs 16 checks per profile and writes `docs/evaluation/verify_75_profiles_report.md`.
- The knowledge base has no sourced honours rule; the 8.50 overload threshold stands in for it.

## 6. Other new components
- Career-track knowledge base: `app/kb/track_repo.py` over `sde/`, `da/`, `aiml/` outputs, plus `data/seed/kb/track_phase_skill.csv` and `kb.track_*` tables.
- `app/engine/planner.py` rewritten: plans every remaining semester, paces track phases inside the weekly-hours cap, keeps breadth slots open rather than guessing a course, defers courses to honour a student credit cap.
- `app/engine/validator.py`: per-semester credit checks, resource-id check, hard student caps.
- Evidence reliability tiers (strong / medium / weak) in `app/engine/skill_state.py`; the diagnostic starts from assessed evidence only.
- `app/engine/mastery.py`: course completion and demonstrated proficiency reported separately.
- `app/llm/client.py` (per-task token budgets, timeout, retries, circuit breaker, deterministic fallback) and `app/llm/guardrails.py` (injection, off-topic, integrity screening; output course-code filter).
- Contracts bumped to 1.4.0 (`app/contracts/`); `docs/contracts/*.json` schemas were not regenerated.

## 7. Test results (final run of this session)
- `python -m pytest tests -q --tb=short`: **198 passed**, 765 subtests passed (172 pre-existing tests plus 26 in `tests/test_inter_iit_upgrade.py`).
- `python scripts/verify_all_75_profiles.py`: **75 / 75** profiles pass; 2,024 course placements, 112 distinct codes, 0 unknown codes.
- `python scripts/check_data.py`: exit 0 (it reports 2 high-severity data blockers that pre-date this run); `python scripts/check_placeholders.py`: 0 placeholders.
- `pytest tests/conformance/test_persona_conformance.py tests/unit/test_import_boundaries.py`: 14 passed, 525 subtests.
- `scripts/run_conformance.py` and `scripts/evaluate_scorecard.py` passed earlier in the run (mismatch accuracy 11/11, was 6/11); not re-run after the last fixes.
- Three snapshot/assumption tests were edited to match the corrected planner (two "plan unchanged" snapshots, one credit sum).

## 8. Docker status
- Verified in this session: image builds (759 MB), `db`, `adminer` and `app` start, `/health` and `/app/` return 200, Adminer returns 200, a direct SQL edit was re-planned by the worker (v2 to v3), and the in-container reset reloaded 8,071 rows.
- The image was built with a sandbox-only certificate override for pip; the committed `docker/Dockerfile` pip line itself was not run unmodified.
- `docker-compose.yml`: `.env` optional, LLM variables passed through, Adminer pinned to 4.8.1 and bound to IPv4, health checks, `POSTGRES_HOST_PORT`.
- `docker/Dockerfile`: also copies `tests/`, `pyproject.toml` and the three track output folders. `docker/entrypoint.sh` + new `docker/wait_for_db.py`: seed when empty, `reset` argument. `Makefile`: `reset`, `verify-profiles`, `profiles`, `tracks`.
- `requirements.txt`: one line added in the follow-up pass, `pyyaml>=6.0.3`. `pyproject.toml` not changed.

## 9. HIGH CONFLICT RISK for other branches
- `app/engine/planner.py`, `app/engine/validator.py`, `app/engine/skill_state.py`, `app/engine/mastery.py` (rewritten).
- `scripts/seed_loader.py` and `docker/init.sql` (new columns and tables, changed column types).
- Track folders: files moved into `output/{curriculum,events,quiz}/`; all eight build scripts edited; `data_analyst/`, `ai_ml/`, root `output/` deleted.
- `app/personas/registry.py`, `app/contracts/*`, all `data/seed/personas/*/students.csv` (regenerated), `data/seed/kb/{goal,skill,goal_skill_requirement,relevance_tags,module,source,programme_requirement}.csv`.
- `web/` (most screens rewritten), Docker files, `Makefile`, services under `app/services/`.

## 10. Known issues and unverified items
- The survey response file has no rows, so the product rationale in the submission document rests on design hypotheses, not survey findings. README section 9 (older feature modules) was carried over without re-verification.
- No live LLM call was made; only the offline mode and a mocked provider failure were tested.
- Seed data concerns found but not changed: core-to-core faculty rows are flagged verified with no verifier and pattern-like lab names, e-mails and URLs; MBA seed rows carry a verifier name and fee figures that could not be confirmed. The loader prints warnings for the first group.
- AI/ML and SDE tracks have no auto-gradable question bank; MME semesters 1-2 use an assumed common first year; SDE phase hours are a design default.
- `docs/contracts/*.json`, `docs/DATA_DICTIONARY.md` and the Windows `.ps1` scripts were not updated.

## 11. Run locally
```bash
docker compose up
```
Web app: http://localhost:8000/app/ - Adminer: http://localhost:8080 (server `db`, user `ebuddy_user`, password `ebuddy_password`, database `ebuddy`).
```bash
pip install -r requirements.txt pyyaml
python scripts/seed_loader.py --reset
python -m uvicorn app.main:app --port 8000
python -m pytest tests -q
python scripts/verify_all_75_profiles.py
```
