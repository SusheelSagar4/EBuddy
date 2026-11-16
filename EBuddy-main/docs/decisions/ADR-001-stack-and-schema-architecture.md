# ADR-001: Architecture, Technology Stack & PostgreSQL Schema Partitioning

## Context
The Adobe "Personalised Learning Buddy" requires an adaptive, verifiable academic planning platform covering B.Tech Electrical Engineering and B.Tech Metallurgical Engineering at IIT Bhubaneswar. The system must adhere to strict non-negotiable rules:
- Single-command startup (`docker compose up`) under 5 GB image size on `linux/amd64` without GPU dependencies.
- Zero secrets or hardcoded models.
- Air-gap / zero outbound traffic except to the configured model provider.
- Complete data control via REST API, Admin UI, and bundled Adminer database viewer, with automatic re-processing triggered on direct database edits.
- Clear separation between deterministic logic (rule engine, planning, validation) and probabilistic LLM reasoning.

## Decision
1. **Tech Stack:**
   - **Backend:** Python 3.12 + FastAPI + SQLAlchemy 2.0 / psycopg3.
   - **Database:** PostgreSQL 16 Alpine + official Adminer container on port 8080.
   - **LLM Gateway:** `litellm` library with enforced local cost mapping (`LITELLM_LOCAL_MODEL_COST_MAP=True`) and disabled telemetry.
   - **Testing:** Python `unittest` suite split into DB-free (offline, fast) and DB-dependent (integration) tests with strict socket timeouts.
2. **PostgreSQL Multi-Schema Organization:**
   - Partition tables into 4 dedicated schemas: `kb`, `student`, `plan`, and `ops`.
   - Use snake_case naming, foreign keys across all relational boundaries, and an explicit `source_id` on every knowledge-base record.
3. **Reactive Re-processing:**
   - Use native PostgreSQL triggers and `pg_notify` to catch direct SQL modifications in Adminer or external tools, pushing to `ops.reprocess_queue` for async buddy re-planning.

## Alternatives Considered
- *Single-schema SQLite:* Incompatible with simultaneous multi-container access (FastAPI + Adminer concurrency locking) and lacks native asynchronous notification triggers (`LISTEN`/`NOTIFY`).
- *Direct ORM hooks for re-processing:* Misses modifications made directly in Adminer via SQL queries.
- *Local HuggingFace / PyTorch models:* Violates the < 5 GB image size constraint and introduces heavy GPU/CUDA driver dependencies.

## Consequences
- **Positive:** Zero chance of container bloat (total footprint < 1.5 GB), clean separation of concerns, instantaneous re-planning even on manual Adminer edits, robust air-gapped testability.
- **Negative:** Requires running PostgreSQL service for DB-dependent integration tests; mitigated by separating DB-free offline tests from DB-dependent tests with connection timeouts.

