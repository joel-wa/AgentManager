#!/usr/bin/env pwsh
# Build script for AgentManager production deployment

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Agent Manager - Production Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$rootDir = $PSScriptRoot

# 1. Build Frontend
Write-Host "[1/4] Building Frontend..." -ForegroundColor Green
Push-Location (Join-Path $rootDir "frontend")
if (-not (Test-Path "node_modules")) {
    Write-Host "  Installing frontend dependencies..." -ForegroundColor Gray
    npm install
}
npm run build
Pop-Location
Write-Host "✓ Frontend built to frontend/dist" -ForegroundColor Green
Write-Host ""

# 2. Rebuild Rust Binary (to include static file serving)
Write-Host "[2/4] Rebuilding Rust Binary..." -ForegroundColor Green
Push-Location (Join-Path $rootDir "rust-core")
cargo build --release
Pop-Location
Write-Host "✓ Rust binary rebuilt with static serving" -ForegroundColor Green
Write-Host ""

# 3. Install Python Dependencies
Write-Host "[3/4] Checking Python Dependencies..." -ForegroundColor Green

# Main Agent
Push-Location (Join-Path $rootDir "python-services\main_agent")
if (Test-Path "requirements.txt") {
    Write-Host "  Installing main_agent dependencies..." -ForegroundColor Gray
    pip install -r requirements.txt -q
}
Pop-Location

# Embeddings
Push-Location (Join-Path $rootDir "python-services\embeddings")
if (Test-Path "requirements.txt") {
    Write-Host "  Installing embeddings dependencies..." -ForegroundColor Gray
    pip install -r requirements.txt -q
}
Pop-Location

Write-Host "✓ Python dependencies installed" -ForegroundColor Green
Write-Host ""

# 4. Verify build
Write-Host "[4/4] Verifying build..." -ForegroundColor Green
$rustBinary = Join-Path $rootDir "rust-core\target\release\agent-workspace-core.exe"
$frontendDist = Join-Path $rootDir "frontend\dist\index.html"

if ((Test-Path $rustBinary) -and (Test-Path $frontendDist)) {
    Write-Host "OK All components ready" -ForegroundColor Green
} else {
    Write-Host "ERROR Build incomplete" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Architecture:" -ForegroundColor White
Write-Host "  Frontend served from: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API accessible at: http://localhost:8000/api" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the application, run:" -ForegroundColor White
Write-Host "  .\start-app.ps1" -ForegroundColor Yellow
Write-Host ""
