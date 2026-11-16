# Test Fixtures (TEST-ONLY Dataset)

**STRICT ISOLATION NOTICE:**
This directory contains minimal, synthetic fixtures used exclusively for isolated unit testing and CI test independence.
- All entities are prefixed with `TEST_`.
- These records are **NEVER loaded into the production database** (`docker/init.sql` / `data/seed/`).
- These records are **NEVER exposed to students or displayed in production UI**.
- Real institutional curriculum data originates strictly from `data/raw/` via validated ingestion pipelines.

