# ==============================================================================
# EBuddy UI Smoke Test (scripts/ui_smoke.ps1)
# Verifies container/server health, loads roadmap for profiles, asserts PASS/FAIL
# ==============================================================================
$ErrorActionPreference = "Stop"

$baseUrl = "http://localhost:8000"
Write-Host "=== EBuddy Web UI Smoke Verification ===" -ForegroundColor Cyan
Write-Host "Target Base URL: $baseUrl" -ForegroundColor Gray

# 1. Health Probe
Write-Host "`n1. Probing $baseUrl/api/health..." -ForegroundColor Yellow
$retries = 15
$healthy = $false

for ($i = 1; $i -le $retries; $i++) {
    try {
        $healthRes = Invoke-RestMethod -Uri "$baseUrl/api/health" -Method Get -TimeoutSec 3
        if ($healthRes.database -eq "connected" -or $healthRes.status -eq "healthy") {
            Write-Host "  -> Health Status: $($healthRes.status)" -ForegroundColor Green
            Write-Host "  -> Database: $($healthRes.database)" -ForegroundColor Green
            Write-Host "  -> LLM Configured: $($healthRes.llm_configured)" -ForegroundColor Green
            $healthy = $true
            break
        }
    } catch {
        Write-Host "  Waiting for server on $baseUrl (attempt $i/$retries)..." -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if (-not $healthy) {
    Write-Host "[FAIL] Server at $baseUrl failed health check." -ForegroundColor Red
    exit 1
}

# 2. EE Student Roadmap Generation
Write-Host "`n2. Requesting Roadmap for EE Profile (CONF_STU_EE_POWER_01)..." -ForegroundColor Yellow
try {
    $bodyEE = @{
        student_id = "CONF_STU_EE_POWER_01"
        goal_id = "GOAL_EE_CORE_POWER"
    } | ConvertTo-Json

    $resEE = Invoke-RestMethod -Uri "$baseUrl/api/roadmap/generate" -Method Post -Body $bodyEE -ContentType "application/json" -TimeoutSec 10
    if ($resEE.items.Count -gt 0 -and $resEE.student_id -eq "CONF_STU_EE_POWER_01") {
        Write-Host "  -> EE Roadmap Plan ID: $($resEE.plan_id)" -ForegroundColor Green
        Write-Host "  -> Version: $($resEE.version)" -ForegroundColor Green
        Write-Host "  -> Total Items Planned: $($resEE.total_items)" -ForegroundColor Green
        Write-Host "  -> Total Planned Credits: $($resEE.total_credits)" -ForegroundColor Green
    } else {
        throw "EE roadmap response had zero items or invalid payload."
    }
} catch {
    Write-Host "[FAIL] EE Roadmap generation failed: $_" -ForegroundColor Red
    exit 1
}

# 3. MME Student Roadmap Generation
Write-Host "`n3. Requesting Roadmap for MME Profile (CONF_STU_MME_PROCESS_01)..." -ForegroundColor Yellow
try {
    $bodyMM = @{
        student_id = "CONF_STU_MME_PROCESS_01"
        goal_id = "GOAL_MM_PROCESS_ENGINEER"
    } | ConvertTo-Json

    $resMM = Invoke-RestMethod -Uri "$baseUrl/api/roadmap/generate" -Method Post -Body $bodyMM -ContentType "application/json" -TimeoutSec 10
    if ($resMM.items.Count -gt 0 -and $resMM.student_id -eq "CONF_STU_MME_PROCESS_01") {
        Write-Host "  -> MME Roadmap Plan ID: $($resMM.plan_id)" -ForegroundColor Green
        Write-Host "  -> Version: $($resMM.version)" -ForegroundColor Green
        Write-Host "  -> Total Items Planned: $($resMM.total_items)" -ForegroundColor Green
        Write-Host "  -> Total Planned Credits: $($resMM.total_credits)" -ForegroundColor Green
    } else {
        throw "MME roadmap response had zero items or invalid payload."
    }
} catch {
    Write-Host "[FAIL] MME Roadmap generation failed: $_" -ForegroundColor Red
    exit 1
}

# 4. Summary
Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "[PASS] UI Smoke Test Completed Successfully!" -ForegroundColor Green
Write-Host "Stack is healthy and roadmap generated for EE and MME." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
exit 0
