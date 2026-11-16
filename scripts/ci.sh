#!/usr/bin/env bash
# ==============================================================================
# CI Pipeline Script for Personalised Learning Buddy (Bash)
# ==============================================================================
set -euo pipefail

echo "=== Step 1: Validating Clean Architecture Import Boundaries ==="
python -m pytest tests/unit/test_import_boundaries.py -q

echo "=== Step 2: Running Automated Test Suites (Unit, Integration, Conformance) ==="
python -m pytest tests -q

echo "=== Step 3: Running Persona Conformance Matrix ==="
python scripts/run_conformance.py

echo "=== Step 4: Knowledge-Base Integrity and Provenance Check ==="
python scripts/check_data.py

echo "=== Step 5: Secret & Hard-Coded Credential Scan ==="
# ci.sh / ci.ps1 contain the patterns themselves and must not match (ci.ps1 already excludes both).
if grep -rnEI "sk-proj-|AIzaSy|ghp_|AKIA" --exclude-dir={.git,.pytest_cache,node_modules} --exclude=ci.sh --exclude=ci.ps1 .; then
    echo "ERROR: Potential secrets detected in codebase!"
    exit 1
fi
echo "Secret scan passed cleanly."

echo "=== Step 6: Zero-Outbound Network Code Audit ==="
VIOLATORS=$(grep -rnEI "import requests|from requests|urllib\.request|import socket" app/ | grep -v "app/llm/client.py" || true)
if [ -n "$VIOLATORS" ]; then
    echo "ERROR: Network access code detected outside app/llm/client.py:"
    echo "$VIOLATORS"
    exit 1
fi
echo "Airgap scan passed cleanly. All network I/O strictly isolated to app/llm/client.py."

echo "✅ ALL CI PIPELINE CHECKS PASSED SUCCESSFULLY!"
exit 0

