# ==============================================================================
# scripts/dev.ps1 - Windows Developer CLI for Personalised Learning Buddy
# Commands: up, down, reset, test, conformance, check-data, lint, ci, new-persona, status, logs
# ==============================================================================

param (
    [Parameter(Position=0, Mandatory=$true)]
    [ValidateSet("up", "down", "reset", "test", "conformance", "check-data", "lint", "ci", "new-persona", "status", "logs")]
    [string]$Command,

    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$AdditionalArgs
)

$ErrorActionPreference = "Stop"

function Invoke-Compose {
    param ([string[]]$Args)
    if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        & docker-compose @Args
    } elseif (Get-Command docker -ErrorAction SilentlyContinue) {
        & docker compose @Args
    } else {
        Write-Host "[ERROR] Docker is not found on PATH." -ForegroundColor Red
        exit 1
    }
}

switch ($Command) {
    "up" {
        Write-Host ">>> Starting Personalised Learning Buddy services..." -ForegroundColor Cyan
        if (-not (Test-Path ".env")) {
            Copy-Item ".env.example" ".env"
            Write-Host "Created .env from .env.example" -ForegroundColor Green
        }
        Invoke-Compose @("up", "-d", "db", "adminer")
        Write-Host "Database & Adminer services started:" -ForegroundColor Green
        Write-Host "  DB:      127.0.0.1:5432" -ForegroundColor White
        Write-Host "  Adminer: http://localhost:8080" -ForegroundColor White
    }

    "down" {
        Write-Host ">>> Stopping services..." -ForegroundColor Cyan
        Invoke-Compose @("down")
    }

    "reset" {
        Write-Host ">>> Resetting database schemas and reloading seed data..." -ForegroundColor Cyan
        python scripts/seed_loader.py --reset
        Write-Host "Database reset complete." -ForegroundColor Green
    }

    "test" {
        Write-Host ">>> Running automated test suite..." -ForegroundColor Cyan
        python -m pytest tests -v
    }

    "conformance" {
        Write-Host ">>> Running persona conformance test matrix..." -ForegroundColor Cyan
        python scripts/run_conformance.py
    }

    "check-data" {
        Write-Host ">>> Running data integrity and provenance checks..." -ForegroundColor Cyan
        python scripts/check_data.py @AdditionalArgs
    }

    "lint" {
        Write-Host ">>> Checking architectural import boundaries and formatting..." -ForegroundColor Cyan
        python -m pytest tests/unit/test_import_boundaries.py -v
    }

    "ci" {
        Write-Host ">>> Running full CI validation pipeline..." -ForegroundColor Cyan
        & ".\scripts\ci.ps1"
    }

    "new-persona" {
        if (-not $AdditionalArgs -or $AdditionalArgs.Count -eq 0) {
            Write-Host "Usage: .\scripts\dev.ps1 new-persona <persona_id>" -ForegroundColor Yellow
            exit 1
        }
        & ".\scripts\new_persona.ps1" $AdditionalArgs[0]
    }

    "status" {
        Invoke-Compose @("ps")
    }

    "logs" {
        Invoke-Compose @("logs", "-f")
    }
}
