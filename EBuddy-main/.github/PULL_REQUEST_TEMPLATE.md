## Summary of Changes
<!-- Provide a clear, high-level summary of what was added, changed, or fixed. -->

## Type of Change
- [ ] `feat`: New engine logic, service, or UI capability
- [ ] `persona`: New or modified persona plugin (`app/personas/<id>/`)
- [ ] `data`: Ingested or corrected knowledge-base data from `data/raw/`
- [ ] `fix`: Bug fix
- [ ] `contract-change`: Changes to `app/contracts/` (includes VERSION bump + schema re-export)
- [ ] `docs`: Documentation updates

## Compliance Verification
- [ ] **Zero Outbound Airgap:** No network calls outside `app/llm/client.py`.
- [ ] **Contracts Frozen:** No contract edits without team approval and `app/contracts/VERSION` bump.
- [ ] **Provenance:** No fabricated regulatory dates, fees, cutoffs, or credit limits.
- [ ] **Imports:** Dependency direction respected (`api` → `services` → `engine`/`kb`/`llm` → `contracts`).
- [ ] **Tests:** Unit and conformance tests run green locally (`.\scripts\dev.ps1 ci`).

## Related Issues or ADRs
<!-- Link relevant issues, tickets, or ADR numbers (e.g., ADR-002). -->

