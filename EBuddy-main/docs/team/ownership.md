# Team Ownership Matrix — Personalised Learning Buddy

To enable seamless parallel development across multiple team members without merge collisions, ownership is partitioned strictly by **directories and files**, rather than vague feature areas.

---

## 1. Directory Ownership Breakdown

| Area / Component | Directory / Files | Primary Owner | Description & Responsibilities |
|---|---|---|---|
| **A. Data & KB Lead** | `data/raw/`<br>`data/seed/kb/`<br>`app/kb/`<br>`scripts/ingest_*`<br>`docs/data_*` | @data-lead | Owns raw curricula, syllabus module extraction, official rules, faculty profiles, video playlist ingestion, surrogate key assignment, and data issue register. |
| **B. Core Engine** | `app/engine/`<br>`app/engine/rules.py`<br>`app/engine/planner.py`<br>`app/engine/validator.py` | @core-engine-lead | Owns deterministic rule checking, topological prerequisite resolution, candidate course scheduling, slot/credit cap enforcement, and plan diffing. |
| **C. Adapt & Mastery** | `app/engine/skill_state.py`<br>`app/engine/mastery.py`<br>`app/engine/diagnostic.py`<br>`app/services/adapt_service.py` | @adapt-mastery-owner | Owns evidence ledger weighting (recency, source reliability), adaptive diagnostic item selection, and "completed coursework" vs "demonstrated proficiency" criteria. |
| **D. LLM & Conversation** | `app/llm/`<br>`app/llm/client.py`<br>`app/llm/tasks/`<br>`app/services/chat_service.py` | @llm-lead | Owns LiteLLM gateway isolation, zero-outbound airgap policy, prompt templates, structured JSON output validation, intent classification, and fake LLM for test determinism. |
| **E. Frontend Shell & UX** | `web/`<br>`docs/product/ux_design.md` | @frontend-lead | Owns zero-CDN web client, design tokens (`tokens.json`, `tokens.css`), client-side hash routing, provenance highlighting, and interactive "Why this?" UI components. |
| **F. Product & Conformance** | `docs/product/`<br>`docs/survey/`<br>`docs/evaluation/`<br>`tests/conformance/` | @eval-lead | Owns student survey evidence, user journeys, conformance test suite execution, benchmark reporting, and demo script. |
| **Shared Contracts** | `app/contracts/`<br>`docs/contracts/`<br>`docs/technical/contracts.md` | @contracts-owner | Frozen Pydantic models. Modified only via formal `contract-change` PR with version bump in `app/contracts/VERSION`. |

---

## 2. Persona Plugin Owners (Isolated Sandboxes)

Each persona is completely self-contained in its own directory:
- `app/personas/<persona_id>/`
- `data/seed/personas/<persona_id>/`

Teammates working on separate personas **never edit the same file**:

| Persona ID | Target Goal | Recommended Owner | Status |
|---|---|---|---|
| `ee_power_core` | Power Systems & Core Electrical | @persona-ee-power-owner | **Live & Conforming (Phase F Canonical)** |
| `ee_embedded_vlsi` | Embedded Systems & VLSI Engineering | @persona-ee-vlsi-owner | Ready for Scaffolding |
| `ee_gate` | GATE Electrical Engineering Focus | @persona-ee-gate-owner | Ready for Scaffolding |
| `mme_core_extractive` | Extractive & Process Metallurgy | @persona-mme-core-owner | Ready for Scaffolding |
| `mme_materials_design` | Advanced Materials & Nanotech | @persona-mme-mat-owner | Ready for Scaffolding |

---

## 3. Collaboration Golden Rules
1. **Never import `app/llm/` from `app/engine/` or `app/kb/`.**
2. **Never import `litellm` outside `app/llm/client.py`.**
3. **Never edit `app/contracts/` without a PR labeled `contract-change` and a version bump in `VERSION`.**
4. **Never make real network calls in tests or engine code.**
5. **Never commit fabricated regulatory data.**

