# FOUNDATION PHASE + TEAM PLAN — Personalised Learning Buddy (IIT Bhubaneswar)

Contents: (1) the prompt to paste into Antigravity, (2) the team split, (3) working rules.

---

# PART 1 — PROMPT FOR ANTIGRAVITY ("Phase F: Foundation")

> Paste after Phase 2 (EE knowledge-base ingestion) is approved. Same hard rules as the master prompt still apply (LiteLLM only, env-configured models, no secrets, no outbound calls except the model provider, no invented data, docker compose up, reset command, admin + Adminer, reprocessing on edits).

## Goal
Build the **base foundation** of the buddy so that several teammates can add features and personas **in parallel without touching each other's files**. When this phase ends, one thin **walking skeleton** runs end to end — Assess → Personalise → Learn → Practise → Adapt → Demonstrate Mastery — for ONE goal, with every layer behind a stable interface. Teammates then deepen layers or add personas.

Do not build deep features. Build clean boundaries, contracts, one vertical slice, tests and team tooling.

## F1. Contracts first (shared, frozen, versioned)
Create `app/contracts/` (Pydantic v2 models, no business logic). Document each in `docs/technical/contracts.md`:
- `StudentProfile`, `EvidenceItem` (source_type, score, reliability, recorded_at), `SkillState`, `Constraint`, `Preference`
- `Goal`, `GoalRequirement`, `MasteryCriteria`, `Milestone`
- `Course`, `Module`, `Resource`, `Exercise`, `AcademicRule`
- `Plan`, `PlanItem` (with `reason`: structured why), `ValidationReport` (per-check pass/fail + messages), `PlanDiff`
- `Intent`, `ChatTurn`, `ContextCard` (what the LLM sees), `Explanation`
- `PersonaSpec` (see F3)
Rules: contracts change only through a PR labelled `contract-change` with a version bump in `app/contracts/VERSION` and a CHANGELOG line. Generate JSON Schema into `docs/contracts/*.json`.

## F2. Layered modules with interfaces (one owner each)
```
app/
  contracts/          # F1
  kb/                 # repositories: read-only access to knowledge base (CourseRepo, SkillRepo, GoalRepo, ResourceRepo, RuleRepo)
  engine/             # DETERMINISTIC core
    rules.py          # RuleEngine: executes kb.academic_rule + prereq/offering/slot checks
    skill_state.py    # SkillStateUpdater: evidence ledger -> SkillState (weights by source_type, recency, attempts)
    gaps.py           # GapAnalyzer: goal requirements - skill states; interest-vs-evidence conflict flags
    planner.py        # Planner: candidate generation + constrained selection + scheduling
    validator.py      # PlanValidator: runs ALL checks on ANY plan (including LLM-proposed edits)
    mastery.py        # MasteryEvaluator: "completed" vs "demonstrated proficiency"
    diagnostic.py     # AdaptiveDiagnostic: item selection + stop rule
  llm/                # ONLY place that imports litellm
    client.py         # env-configured, timeouts, retries, cache, logging to ops.llm_call_log
    fake.py           # deterministic FakeLLM for tests (selected by LLM_MODEL=fake/test or a test fixture); zero network
    tasks/            # one file per LLM task: intent_router.py, explainer.py, grader.py, clarifier.py, question_gen.py
    prompts/          # versioned prompt templates (text files), each with a schema for structured output
  services/           # orchestration: onboarding, diagnose, plan, adapt, chat, simulate
  api/                # FastAPI routers: student, admin, simulator; OpenAPI
  worker/             # reprocess worker (DB NOTIFY listener)
  personas/           # F3
  web/                # frontend shell
tests/
  unit/ integration/ conformance/ fixtures/
```
Interface rules:
- Each engine module exposes a **Protocol/ABC** in `app/engine/interfaces.py`, a **baseline implementation**, and unit tests. Teammates may replace the implementation without changing callers.
- `engine/` and `kb/` never import `llm/` or `api/`. `llm/tasks` never touch the DB directly; they receive a `ContextCard` and return a validated schema.
- Every LLM output is schema-validated; any course code in LLM output must exist in `kb.course` or the output is rejected and retried once, then falls back to a deterministic template.
- Dependency direction: api → services → (engine, llm, kb) → contracts. Add an import-linter (or a simple test) that fails when this is violated.

## F3. Persona / goal plugin system (this is what the team will extend)
Each persona-goal is a **self-contained folder**:
```
app/personas/<persona_id>/
  persona.yaml        # PersonaSpec: id, goal_id, description, applicable programmes, eligibility notes
  requirements.yaml   # skill requirements + required levels + importance (mirrors kb.goal_skill_requirement; loader syncs)
  mastery.yaml        # mastery criteria (thresholds, project, mock tests/interviews)
  milestones.yaml     # projects, internships, exam timelines by semester
  diagnostic.yaml     # skill blueprint for the short adaptive diagnostic (which skills, item counts, difficulty range)
  policy.py           # OPTIONAL hooks: weights for planner (CGPA protection vs skill-building), conflict handling, special rules
  prompts/            # OPTIONAL persona-specific prompt snippets (tone, examples), versioned
  README.md           # who this persona is, survey evidence, decisions, trade-offs, known gaps
data/seed/personas/<persona_id>/
  students.csv        # synthetic profiles for this persona (is_synthetic=true), incl. edge cases
  exercises.json      # persona-specific exercises/mock tests (optional)
  resources.csv       # persona-specific open resources (optional)
```
- A **registry** auto-discovers folders under `app/personas/` — adding a persona must require **no edits to shared files**.
- Seed files are split per persona so teammates never edit the same CSV. Loader merges them in a deterministic order. The shared KB (courses, skills, rules) stays owned by the Data owner.
- Implement the **PersonaPolicy** interface with a sensible default so a persona with only YAML works.
- Build `scripts/new_persona.(ps1|sh) <persona_id>` that scaffolds this folder with TODOs and a README template.

## F4. Persona conformance suite (the quality gate every persona must pass)
`tests/conformance/` runs automatically for **every registered persona** and every synthetic profile of that persona, using the FakeLLM so it is free and deterministic:
1. Plan is produced and `ValidationReport.passed == true`.
2. Every cited course code exists in the KB; every prerequisite satisfied; semester offering respected; credits/slots within limits.
3. No content the student has already mastered is assigned.
4. All goal skills below target level are covered by plan items, or the plan states why not.
5. Practice is active (exercises/projects) — plan includes at least N active items per skill gap.
6. Adapt: re-running with a strong quiz result shortens/skips content; a weak result adds remediation; both plans validate.
7. Determinism: same input → same plan twice.
8. Unachievable request (e.g. exceed credit cap) → clear refusal + best valid alternative.
Report results as a table in `docs/evaluation/conformance_report.md` (persona × check × pass/fail). `make conformance` / `scripts\dev.ps1 conformance`.

## F5. Walking skeleton (vertical slice, thin but real)
Implement baseline versions so this works through the API and a minimal UI for **one** goal (use the EE software/data-role or power-sector goal, whichever has the most complete KB data):
1. Onboard a synthetic student (programme, year, completed courses, goal, constraints, preferences).
2. Short adaptive diagnostic → writes EvidenceItems → SkillState updates.
3. Gap report + plan generation + validation + "Why this?" reasons.
4. Learn/practise: show resources and exercises; submit answers; deterministic grading for MCQ/numeric; LLM grading hook behind interface for short answers.
5. Adapt: simulator endpoint `POST /api/sim/{student}/quiz` with injected scores → new plan version + PlanDiff + explanation.
6. Mastery check → "completed" vs "demonstrated proficiency" with evidence.
7. Chat: intent router → plan question / side question / goal change / off-topic; returns to plan.
All with FakeLLM in tests and real LiteLLM at runtime (env-configured).

## F6. Frontend shell
Minimal but structured app: layout, routing and **persona-agnostic screens** (Onboarding, Diagnostic, Plan, Learn/Practise, Progress/Mastery, Chat, What-changed, Admin link). Shared design tokens (`web/src/design/tokens.*`), reusable components, API client generated from OpenAPI. No CDN assets (bundle everything). Document in `docs/product/ux_design.md`.

## F7. Team workflow tooling
- `CONTRIBUTING.md`: branch naming (`feat/<area>-<short>`, `persona/<id>`, `data/<topic>`), small PRs, conventional commits, PR checklist.
- `.github/PULL_REQUEST_TEMPLATE.md` and `CODEOWNERS` with placeholders for owners per folder (`app/engine/`, `app/llm/`, `app/personas/<id>/`, `data/`, `web/`, `docs/`).
- CI script (`scripts/ci.(ps1|sh)`) runs: lint/format, import-boundary test, unit + integration + conformance tests, `check-data`, secret scan (no keys, no hard-coded model names), and fails on any outbound-network code outside `app/llm/client.py` (grep rule).
- Pre-commit hooks for formatting and secret scan.
- `docs/team/ownership.md` (who owns what), `docs/team/how_to_add_a_persona.md`, `docs/team/how_to_add_a_skill_or_exercise.md`, `docs/team/definition_of_done.md`.
- ADR template and `docs/decisions/` index.
- `scripts/dev.ps1` and `Makefile` parity: up, down, reset, test, conformance, check-data, lint, ci, new-persona.

## F8. Test fixtures (not product data)
`tests/fixtures/` may hold a tiny labelled TEST-ONLY dataset (a few courses, skills, one goal) so CI does not depend on the real seed files. These must be clearly named (`TEST_*`), never loaded into the product database, and never shown to students. Real data always comes from `data/raw` ingestion.

## F9. Acceptance for Phase F
- [ ] `docker compose up` + `.\scripts\dev.ps1 reset` works from a clean clone
- [ ] Walking skeleton runs end to end for one persona (API + minimal UI)
- [ ] Contracts documented; JSON Schemas generated
- [ ] Import-boundary test passes; only `app/llm/client.py` imports litellm
- [ ] Persona registry works; `new_persona` scaffold creates a persona that passes conformance with only YAML
- [ ] Conformance suite runs for all registered personas and profiles; report generated
- [ ] CI script green; secret and hard-coded-model scan green
- [ ] Team docs complete (CONTRIBUTING, ownership, how-to guides)
- [ ] Docs updated: architecture.md, contracts.md, CHANGELOG, ADRs
Then **stop and report**: what exists, test results, known gaps, and suggested ownership split. Wait for my approval.

---

# PART 2 — TEAM SPLIT (adjust to your team size)

Work starts after Phase F is approved and merged. Each person owns **folders**, not features, so merges stay clean.

| Role | Owns | First tasks |
|---|---|---|
| **A. Data & KB lead** | `data/raw`, `data/seed/kb`, `scripts/ingest_*`, `docs/data_*` | EE syllabus modules, skill mappings, exercises (100+), playlists verification; later Metallurgy ingestion |
| **B. Core engine** | `app/engine/` | Rule engine (academic rules), planner quality, validator completeness, time budgeting |
| **C. Adapt & mastery** | `app/engine/skill_state.py`, `mastery.py`, `diagnostic.py`, simulator | Evidence weighting, adaptive diagnostic, goal-level mastery, strong-vs-weak quiz demo |
| **D. LLM & conversation** | `app/llm/`, chat service | Intent router, clarifying questions, explanations, memory + context cards, injection/off-topic safety, caching and latency |
| **E. Frontend & UX** | `app/web/`, `docs/product/ux_design.md` | Onboarding, plan view with "Why this?", progress/mastery visuals, diff view, admin |
| **F. Product, survey & evaluation** | `docs/product/`, `docs/survey/`, `docs/evaluation/` | Run survey, personas, requirements, success metrics, evaluation checklist, demo script |
| **Persona owners (can be A–F, 1–2 each)** | `app/personas/<id>/` and `data/seed/personas/<id>/` | One goal each; see below |

## Persona assignment (one folder each → zero conflicts)
| Persona id | Goal | Notes |
|---|---|---|
| `ee_power_core` | Power-sector / core electrical role | Power systems, machines, power electronics path |
| `ee_embedded_vlsi` | Embedded / VLSI role | Electronics, embedded, VLSI electives |
| `ee_software_data` | Software / data / ML role (cross-branch) | Needs DB/OS skills from open resources or other-department electives |
| `ee_higher_studies` | MS/PhD research path | Uses research-project / faculty matching; GATE/GRE timelines |
| `ee_upsc` | Civil services | Humanities breadth electives, weekly prep plan, CGPA protection |
| `ee_startup` | Startup / venture | Entrepreneurship resources, clubs and incubation pointers (outside tracked scope) |
| `met_*` | Metallurgy goals | Added after the Metallurgy data is ingested (same folder structure) |

Each persona owner delivers: the persona folder, ≥10 synthetic profiles (incl. edge cases), exercises/mock tests, README with survey evidence and trade-offs, and a green conformance run.

---

# PART 3 — WORKING RULES FOR THE TEAM
1. Never edit another owner's folder without a PR reviewed by them.
2. Contract changes need a `contract-change` PR and everyone's heads-up.
3. Every PR: tests + docs updated + `scripts\ci` green.
4. Real data only from `data/raw` via ingestion scripts; placeholders flagged; no fabricated survey results.
5. Secrets only in the local `.env` (never committed, never pasted in chat).
6. One LLM model for tuning and testing; record it in README and `.env.example`.
7. Merge to `main` only from reviewed PRs; tag a release after every approved phase.
