<#
.SYNOPSIS
  Phase 0 Exit Gate Verification Script for Urbero
.DESCRIPTION
  Executes ruff, mypy --strict, tsc --noEmit, eslint, and gitleaks/secret scan.
#>

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $false

function Invoke-Gate {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  URBERO - PHASE 0 EXIT GATE VERIFICATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Ruff check & format
Write-Host "`n[1/5] Running Ruff lint & format check on backend..." -ForegroundColor Yellow
Invoke-Gate python @("-m", "ruff", "check", "backend/")
Invoke-Gate python @("-m", "ruff", "format", "--check", "backend/")
Write-Host "✓ Ruff checks passed." -ForegroundColor Green

# 2. Mypy strict check
Write-Host "`n[2/5] Running Mypy --strict on backend/app..." -ForegroundColor Yellow
Invoke-Gate python @("-m", "mypy", "--strict", "backend/app")
Write-Host "✓ Mypy strict type checks passed." -ForegroundColor Green

# 3. TypeScript compile check
Write-Host "`n[3/5] Running TypeScript compiler check on frontend..." -ForegroundColor Yellow
Push-Location frontend
try {
    Invoke-Gate npm.cmd @("run", "typecheck")
    Write-Host "✓ TypeScript (tsc --noEmit) passed." -ForegroundColor Green

    # 4. ESLint check
    Write-Host "`n[4/5] Running ESLint on frontend..." -ForegroundColor Yellow
    Invoke-Gate npm.cmd @("run", "lint")
    Write-Host "✓ ESLint passed." -ForegroundColor Green
} finally {
    Pop-Location
}

# 5. Secret scan
Write-Host "`n[5/5] Running secret scan..." -ForegroundColor Yellow
if (Get-Command gitleaks -ErrorAction SilentlyContinue) {
    Invoke-Gate gitleaks @("detect", "--source", ".", "--config", ".gitleaks.toml", "--no-banner", "-v")
    Write-Host "✓ Gitleaks scan passed." -ForegroundColor Green
} else {
    Invoke-Gate python @("scripts/secret_scan.py")
    Write-Host "✓ Secret scan passed." -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  ALL PHASE 0 GATES PASSED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
exit 0
