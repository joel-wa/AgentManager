#!/usr/bin/env pwsh
# AgentManager Application Launcher
# Starts all required services

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Agent Manager - Starting Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$rootDir = $PSScriptRoot

# Check if release binary exists
$rustBinary = Join-Path $rootDir "rust-core\target\release\agent-workspace-core.exe"
if (-not (Test-Path $rustBinary)) {
    Write-Host "ERROR: Rust binary not found at $rustBinary" -ForegroundColor Red
    Write-Host "Please run: cargo build --release" -ForegroundColor Yellow
    exit 1
}

# Check if frontend is built
$frontendDist = Join-Path $rootDir "frontend\dist"
if (-not (Test-Path $frontendDist)) {
    Write-Host "Frontend not built. Building now..." -ForegroundColor Yellow
    Push-Location (Join-Path $rootDir "frontend")
    npm run build
    Pop-Location
}

# Array to track background jobs
$jobs = @()

# Function to cleanup on exit
function Cleanup {
    Write-Host "`n`nShutting down services..." -ForegroundColor Yellow
    foreach ($job in $jobs) {
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        Remove-Job -Job $job -ErrorAction SilentlyContinue
    }
    Write-Host "All services stopped." -ForegroundColor Green
}

# Register cleanup on Ctrl+C
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Cleanup }

try {
    # Start Main Agent Service
    Write-Host "[1/4] Starting Main Agent Service (port 8001)..." -ForegroundColor Green
    $mainAgentJob = Start-Job -ScriptBlock {
        Set-Location $using:rootDir\python-services\main_agent
        python main.py
    }
    $jobs += $mainAgentJob
    Start-Sleep -Seconds 2

    # Start Maintenance Agent Service
    Write-Host "[2/4] Starting Maintenance Agent Service (port 8002)..." -ForegroundColor Green
    $maintenanceJob = Start-Job -ScriptBlock {
        Set-Location $using:rootDir\python-services\maintenance_agent
        python main.py
    }
    $jobs += $maintenanceJob
    Start-Sleep -Seconds 2

    # Start Embeddings Service
    Write-Host "[3/4] Starting Embeddings Service (port 8003)..." -ForegroundColor Green
    $embeddingsJob = Start-Job -ScriptBlock {
        Set-Location $using:rootDir\python-services\embeddings
        python main.py
    }
    $jobs += $embeddingsJob
    Start-Sleep -Seconds 2

    # Start Rust Core (serves frontend + API)
    Write-Host "[4/4] Starting Rust Core (Frontend + API on port 8000)..." -ForegroundColor Green
    $rustJob = Start-Job -ScriptBlock {
        Set-Location $using:rootDir\rust-core
        & .\target\release\agent-workspace-core.exe
    }
    $jobs += $rustJob
    Start-Sleep -Seconds 3

    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "   Application Started Successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Open your browser:" -ForegroundColor White
    Write-Host "  http://localhost:8000" -ForegroundColor Cyan -NoNewline
    Write-Host " (Frontend + API)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Backend Services:" -ForegroundColor White
    Write-Host "  Main Agent:     http://localhost:8001/health" -ForegroundColor Gray
    Write-Host "  Maintenance:    http://localhost:8002/health" -ForegroundColor Gray
    Write-Host "  Embeddings:     http://localhost:8003/health" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
    Write-Host ""

    # Keep script running and show logs
    while ($true) {
        Start-Sleep -Seconds 1
        
        # Check if any job failed
        foreach ($job in $jobs) {
            if ($job.State -eq "Failed") {
                Write-Host "`nERROR: Service $($job.Name) failed!" -ForegroundColor Red
                Receive-Job -Job $job
                throw "Service failed"
            }
        }
    }
}
catch {
    Write-Host "`nError occurred: $_" -ForegroundColor Red
}
finally {
    Cleanup
}
