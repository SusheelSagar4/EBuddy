# Technical Architecture — Personalised Learning Buddy (IIT Bhubaneswar)

**Phase:** Phase F (Foundation Complete)  
**Target Institute:** Indian Institute of Technology Bhubaneswar  
**Programmes:** B.Tech Electrical Engineering (EE) & B.Tech Metallurgical and Materials Engineering (MME)

---

## 1. Architectural Principles

1. **Deterministic Core:** Prerequisite checking, curriculum schedule validation, slot constraints, and mastery evaluation run strictly deterministically in Python without non-deterministic LLM hallucinations.
2. **Four-Agent Architecture & Single-Writer Rule:**
   - **Agent 1 (Roadmap Planner):** Sole designated writer for roadmap versions and 7-day weekly task plans. Enforces student weekly hours budgets, prunes tasks to fit, and records deferred tasks.
   - **Agent 2 (Learning Resource Agent):** Recommends daily courseware and backup alternatives; emits `ChangeProposal` records.
   - **Agent 3 (Assessment & Quiz Agent):** Grades submissions against mastery criteria and emits remediation proposals for weak mastery. Runs adaptive diagnostics with dynamic difficulty scaling (50 baseline, +/-15 adjustments, terminating between 5-8 items upon reaching confidence threshold >= 0.85).
   - **Agent 4 (Query Adaptation Agent):** Handles student conversation, prompt injection defense, rolling long-term memory summaries (`ops.memory_summary`), and workload adaptation proposals.
   - **Single Writer:** Agents 2, 3, and 4 cannot modify the roadmap. Only student approval triggers Agent 1 to deterministically commit Version $N+1$.
3. **Student Constraints vs Institutional Baseline Rules:**
   - Student constraints (`credit_cap`, `headroom`, `weekly_hours`, `avoid_course`, `not_together`) are hard constraints. The default plan strictly respects student bounds, routing any overload or excluded courses into `plan.optional_overload_proposals` awaiting explicit student approval.
   - Institutional baseline rules (`RULE_SEM_CREDIT_CAP_REGULAR`, `RULE_MINOR_MIN_CGPA`) originating from unverified baseline sources emit non-blocking warnings (`[WARNING: unsourced_baseline]`).
4. **Layered Interfaces:** Modules adhere to strict dependency direction:
   ```
   FastAPI Web & API Routers (app/api/, web/)
         ↓
   Orchestration Services (app/services/) & Agents (app/agents/)
         ↓
   Core Engine (app/engine/) | LLM Gateway (app/llm/) | Repositories (app/kb/)
         ↓
   Frozen Contracts & Schemas (app/contracts/ v1.2.0)
   ```
5. **LiteLLM Gateway Isolation:** Only `app/llm/client.py` imports `litellm`. All other components interact through structured task interfaces (`IntentRouter`, `Explainer`, `Grader`). Tests run against `FakeLLM` with zero outbound network calls.
6. **Persona Plugin Modularity:** Each persona is an autonomous directory in `app/personas/<id>/` and `data/seed/personas/<id>/`. Conformance test suite iterates over every registered persona and every profile in `data/seed/personas/<id>/students.csv`.
7. **Strict Provenance & Zero Fabrication:** Knowledge-base rows carry `status` (`verified`, `draft_for_review`, `unsourced_baseline`) and `source_id`. The buddy never asserts regulatory dates, cut-offs, or fees unless verified.

---

## 2. Directory Structure

```
Ebuddy/
├── app/
│   ├── contracts/          # F1: Frozen Pydantic models (version 1.0.0)
│   ├── kb/                 # F2: Read-only KB repositories
│   ├── engine/             # F2: Deterministic rule, planning & mastery engines
│   ├── llm/                # F2: LiteLLM gateway, FakeLLM, task runners & prompts
│   ├── services/           # F5: Orchestration services (onboard, plan, adapt, chat)
│   ├── api/                # F5: FastAPI routers (student, simulator, admin)
│   └── personas/           # F3: Discovered persona plugins (ee_power_core, ...)
├── web/                    # F6: Zero-CDN responsive frontend shell
│   ├── src/design/         # Design tokens (tokens.json, tokens.css, style.css)
│   ├── src/api/            # Typed API client (client.js)
│   └── src/screens/        # Persona-agnostic screens (onboarding, plan, chat, etc.)
├── data/
│   ├── raw/                # Official source files & PDF extraction
│   └── seed/kb/            # Canonical CSV seeds with provenance metadata
├── tests/
│   ├── unit/               # Boundary and unit tests
│   ├── integration/        # Walking skeleton end-to-end integration tests
│   ├── conformance/        # F4: 8-check automated persona conformance suite
│   └── fixtures/           # F8: Isolated TEST_* fixtures for CI
└── docs/                   # Contracts, decisions (ADRs), evaluation, team tooling
```

---

## 3. Walking Skeleton Vertical Slice

The Phase F walking skeleton verifies the complete end-to-end flow:
1. **Assess:** Student onboarding with constraints and adaptive baseline diagnostic.
2. **Personalise:** Planner resolves prerequisite DAGs recursively to schedule courses for the target goal.
3. **Learn & Practise:** Curated lecture series + interactive exercises with immediate feedback.
4. **Demonstrate Mastery:** Distinguishes between completed course credits and verified competency evidence.
5. **Adapt:** Simulator endpoint triggers performance shock (strong vs weak quiz) and returns a validated `PlanDiff`.
6. **Chat:** Intent router classifies questions, binds context card, and generates grounded responses.

