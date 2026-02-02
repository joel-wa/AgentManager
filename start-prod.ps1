#!/usr/bin/env pwsh
# Simple production launcher with web server for frontend

$ErrorActionPreference = "Stop"

Write-Host "Starting Agent Manager..." -ForegroundColor Cyan

$rootDir = $PSScriptRoot

# Start services in background
Write-Host "Starting services..." -ForegroundColor Green

# Main Agent
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootDir\python-services\main_agent'; python main.py" -WindowStyle Minimized

# Embeddings  
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootDir\python-services\embeddings'; python main.py" -WindowStyle Minimized

Start-Sleep -Seconds 3

# Rust Core
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootDir\rust-core'; .\target\release\agent-workspace-core.exe" -WindowStyle Minimized

Start-Sleep -Seconds 2

# Serve frontend
Write-Host "Starting frontend..." -ForegroundColor Green
Set-Location "$rootDir\frontend"

# Check if dist exists
if (-not (Test-Path "dist")) {
    Write-Host "Building frontend first..." -ForegroundColor Yellow
    npm run build
}

# Serve with http-server or vite preview
npm run preview

Write-Host "`nApplication stopped." -ForegroundColor Yellow
