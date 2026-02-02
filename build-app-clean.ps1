$ErrorActionPreference = "Stop"

Write-Host "Building Agent Manager..." -ForegroundColor Cyan

$rootDir = $PSScriptRoot

# Build Frontend
Write-Host "[1/4] Building Frontend..." -ForegroundColor Green
Push-Location (Join-Path $rootDir "frontend")
if (-not (Test-Path "node_modules")) {
    npm install
}
npm run build
Pop-Location

# Rebuild Rust
Write-Host "[2/4] Building Rust Core..." -ForegroundColor Green
Push-Location (Join-Path $rootDir "rust-core")
cargo build --release
Pop-Location

# Python deps
Write-Host "[3/4] Python Dependencies..." -ForegroundColor Green
Push-Location (Join-Path $rootDir "python-services\main_agent")
pip install -r requirements.txt -q 2>$null
Pop-Location

Push-Location (Join-Path $rootDir "python-services\embeddings")
pip install -r requirements.txt -q 2>$null
Pop-Location

# Verify
Write-Host "[4/4] Verifying..." -ForegroundColor Green
$rustBinary = Join-Path $rootDir "rust-core\target\release\agent-workspace-core.exe"
$frontendDist = Join-Path $rootDir "frontend\dist\index.html"

if ((Test-Path $rustBinary) -and (Test-Path $frontendDist)) {
    Write-Host "Build complete!" -ForegroundColor Green
    Write-Host "Run: .\start-app.ps1" -ForegroundColor Yellow
} else {
    Write-Host "Build failed" -ForegroundColor Red
    exit 1
}