# Definition of Done (DoD) — Personalised Learning Buddy

A pull request or task is considered **Done** only when all applicable criteria below are satisfied.

---

## 1. Code Quality & Architecture Boundaries
- [ ] **Contract Integrity:** No contracts in `app/contracts/` modified without team review and a version bump in `app/contracts/VERSION`.
- [ ] **Import Boundary Compliance:**
  - `app/engine/` and `app/kb/` contain NO imports from `app/llm/` or `app/api/`.
  - Only `app/llm/client.py` imports `litellm`.
  - Dependency hierarchy is strictly: `api` → `services` → (`engine`, `llm`, `kb`) → `contracts`.
- [ ] **Zero-Outbound Airgap:** No network calls occur in tests or engine logic. All tests use `FakeLLM`.
- [ ] **Lint & Format:** Code passes formatting standards (`ruff` / `black` / `flake8`).

---

## 2. Institutional Provenance & Data Integrity
- [ ] **No Fabricated Facts:** No dates, fees, cut-offs, or regulatory credit ceilings are asserted unless backed by an official row in `data/seed/kb/`.
- [ ] **Provenance Flagging:** Any non-official baseline is tagged `unsourced_baseline` or `draft_for_review`.
- [ ] **Data Check Green:** `.\scripts\dev.ps1 check-data` passes with 0 blocking errors.
- [ ] **Synthetic Labeling:** All test student profiles are explicitly marked `is_synthetic = true`.

---

## 3. Conformance & Test Suite
- [ ] **Unit Tests:** All unit tests in `tests/unit/` pass.
- [ ] **Integration Tests:** Walking skeleton tests in `tests/integration/` pass.
- [ ] **Persona Conformance:** All 8 checks in `tests/conformance/` pass for every registered persona.
- [ ] **Idempotence:** Database reset (`.\scripts\dev.ps1 reset`) executes cleanly and idempotently.

---

## 4. Documentation & Traceability
- [ ] Relevant documentation updated (`README.md`, `docs/technical/contracts.md`, `docs/product/ux_design.md`).
- [ ] Architectural decisions documented in `docs/decisions/` (ADR).
- [ ] Release changes logged in `CHANGELOG.md`.

