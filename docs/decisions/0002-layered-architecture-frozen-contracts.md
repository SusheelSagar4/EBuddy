# ADR-0002: Layered Architecture & Frozen Pydantic Contracts

## Status
Accepted (2026-11-14)

## Context
When scaling development across multiple team members, shared schemas often undergo silent breaking modifications that cause cascading integration failures across services, engine components, and the frontend.

## Decision
1. Define all data interchange models strictly in `app/contracts/` using Pydantic v2.
2. Contracts are strictly frozen: changes require a formal PR labeled `contract-change`, a version bump in `app/contracts/VERSION`, and re-exporting JSON Schemas into `docs/contracts/*.json`.
3. Strict dependency hierarchy is enforced:
   `api` → `services` → (`engine`, `llm`, `kb`) → `contracts`
4. Automated import boundary tests (`tests/unit/test_import_boundaries.py`) run in CI to prevent reverse imports.

## Consequences
### Positive
- Clear interfaces allow independent development of engine algorithms, LLM prompt engineering, and UI views.
- Contracts serve as the single source of truth for both Python backend and web client.

### Negative
- Schema modifications require extra friction (version bump and schema generation), which is intentionally desired to protect stability.

