# Contributing to Personalised Learning Buddy (IIT Bhubaneswar)

Welcome! This repository is built for multi-agent and multi-developer collaboration on the Inter IIT Tech Meet 15.0 Personalised Learning Buddy. To ensure zero conflicts and maintain strict regulatory compliance, all contributors must follow these guidelines.

---

## 1. Branch Naming Conventions

All work must be conducted on scoped branches using the following prefixes:
- `feat/<area>-<short-description>`: Engine features, services, or UI components (e.g., `feat/engine-prereq-dag`, `feat/web-mastery-view`).
- `persona/<persona_id>`: Adding or refining a persona plugin folder (e.g., `persona/ee_embedded_vlsi`, `persona/mme_core_extractive`).
- `data/<topic>`: Knowledge-base updates, raw syllabus curation, or official regulatory additions (e.g., `data/ee-electives-pool`, `data/smmme-faculty-updates`).
- `fix/<issue-description>`: Bug fixes or data discrepancy reconciliations (e.g., `fix/code-conflict-ml4l001`).
- `contract-change`: Updating contracts in `app/contracts/`. **Requires contract version bump and approval.**

---

## 2. Commit Message Standards

Use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat(engine): add topological prereq traversal in planner`
- `data(smmme): ingest consultancy catalog entries`
- `fix(contracts): add display_code and code_conflict flags to Course`
- `docs(team): add persona authoring guide`
- `test(conformance): add credit cap violation check`

---

## 3. Pull Request Checklist

Before submitting a PR, verify:
- [ ] No changes to frozen contracts in `app/contracts/` unless accompanied by a version bump in `app/contracts/VERSION` and schema re-generation via `python scripts/export_contracts_schema.py`.
- [ ] `app/engine/` and `app/kb/` contain NO imports of `litellm` or `app/llm/`.
- [ ] `app/llm/client.py` remains the SOLE importer of `litellm`.
- [ ] No hardcoded model strings or API secrets in code or commits.
- [ ] No outbound network calls exist in tests or engine logic (all tests use `FakeLLM`).
- [ ] All new data originates strictly from `data/raw/` with provenance logged; synthetic profiles are explicitly tagged `is_synthetic = true`.
- [ ] `.\scripts\dev.ps1 ci` (or `./scripts/ci.sh`) passes completely green.

---

## 4. Development Workflow & Commands

Use `scripts/dev.ps1` (PowerShell on Windows) or `make` (Linux/macOS):
```powershell
# Start database and dependencies
.\scripts\dev.ps1 up

# Reset database idempotently and seed all knowledge base tables
.\scripts\dev.ps1 reset

# Run test suite
.\scripts\dev.ps1 test

# Run persona conformance suite
.\scripts\dev.ps1 conformance

# Run data integrity and provenance check
.\scripts\dev.ps1 check-data

# Scaffold a new persona plugin
.\scripts\dev.ps1 new-persona ee_robotics_ai

# Run full CI validation pipeline
.\scripts\dev.ps1 ci
```

