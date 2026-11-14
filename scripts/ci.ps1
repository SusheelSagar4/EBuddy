# ==============================================================================
# CI Pipeline Script for Personalised Learning Buddy (PowerShell)
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "=== Step 1: Validating Clean Architecture Import Boundaries ===" -ForegroundColor Cyan
python -m pytest tests/unit/test_import_boundaries.py -q
if ($LASTEXITCODE -ne 0) {
    Write-Error "Import boundary check failed! Dependency hierarchy or litellm isolation violated."
    exit 1
}

Write-Host "=== Step 2: Running Automated Test Suites (Unit, Integration, Conformance) ===" -ForegroundColor Cyan
python -m pytest tests -q
if ($LASTEXITCODE -ne 0) {
    Write-Error "Test suite execution failed!"
    exit 1
}

Write-Host "=== Step 3: Running Persona Conformance Matrix ===" -ForegroundColor Cyan
python scripts/run_conformance.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Persona conformance checks failed!"
    exit 1
}

Write-Host "=== Step 4: Knowledge-Base Integrity and Provenance Check ===" -ForegroundColor Cyan
python scripts/check_data.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Data integrity verification failed!"
    exit 1
}

Write-Host "=== Step 5: Secret & Hard-Coded Credential Scan ===" -ForegroundColor Cyan
$forbidden_patterns = @("sk-proj-", "AIzaSy", "ghp_", "AKIA")
$violating_files = @()
Get-ChildItem -Recurse -File -Exclude "*.pyc", "*.log", "*.git*", "*.png", "*.jpg", "*.xlsx", "*.xls", "*.pdf", "ci.ps1", "ci.sh" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
    if ($content) {
        foreach ($pat in $forbidden_patterns) {
            if ($content.Contains($pat)) {
                $violating_files += "$($_.FullName) (contains $pat)"
            }
        }
    }
}
if ($violating_files.Count -gt 0) {
    Write-Error "Potential secrets detected in codebase: $($violating_files -join ', ')"
    exit 1
}
Write-Host "Secret scan passed cleanly. No API keys or tokens committed." -ForegroundColor Green

Write-Host "=== Step 5B: Hard-Coded Model Name Scan ===" -ForegroundColor Cyan
$model_violators = @()
Get-ChildItem -Path "app" -Recurse -Filter "*.py" | ForEach-Object {
    if ($_.FullName -notmatch "config\.py") {
        $content = Get-Content $_.FullName -Raw
        if ($content -match '"gpt-4' -or $content -match '"gemini-1' -or $content -match '"claude-3') {
            $model_violators += $_.FullName
        }
    }
}
if ($model_violators.Count -gt 0) {
    Write-Error "Hardcoded model names detected outside app/config.py: $($model_violators -join ', ')"
    exit 1
}
Write-Host "Hard-coded model scan passed cleanly. All model names configured strictly via environment." -ForegroundColor Green

Write-Host "=== Step 6: Zero-Outbound Network Code Audit ===" -ForegroundColor Cyan
# Ensure no requests or urllib or http socket calls outside app/llm/client.py
$network_violators = @()
Get-ChildItem -Path "app" -Recurse -Filter "*.py" | ForEach-Object {
    if ($_.FullName -notmatch "client\.py") {
        $content = Get-Content $_.FullName -Raw
        if ($content -match "import requests" -or $content -match "from requests" -or $content -match "urllib\.request" -or $content -match "import socket") {
            $network_violators += $_.FullName
        }
    }
}
if ($network_violators.Count -gt 0) {
    Write-Error "Network access code detected outside app/llm/client.py: $($network_violators -join ', ')"
    exit 1
}
Write-Host "Airgap scan passed cleanly. All network I/O strictly isolated to app/llm/client.py." -ForegroundColor Green

Write-Host "`n✅ ALL CI PIPELINE CHECKS PASSED SUCCESSFULLY!" -ForegroundColor Green
exit 0
