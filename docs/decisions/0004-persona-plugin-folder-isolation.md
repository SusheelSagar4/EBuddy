# ADR-0004: Persona Plugin System & Autonomous Folder Isolation

## Status
Accepted (2026-11-14)

## Context
Multiple team members will develop different student profiles and career goals (Power Systems, VLSI, GATE, Metallurgy Extractive, Metallurgy Materials Design). Modifying a central configuration file or shared database seeds would cause perpetual merge conflicts.

## Decision
1. Each persona is implemented as a self-contained folder:
   - Specification & blueprints: `app/personas/<persona_id>/`
   - Synthetic seed data: `data/seed/personas/<persona_id>/`
2. A lightweight `PersonaRegistry` automatically discovers persona folders without editing any central configuration.
3. Adding a new persona is completely decoupled: teammates run `new_persona` scaffold, fill in YAML blueprints, and verify against `tests/conformance/`.

## Consequences
### Positive
- Zero git merge conflicts between teammates working on different career pathways.
- Standardized conformance test suite automatically evaluates all registered personas.

### Negative
- Requires maintaining YAML schemas across persona folders.

