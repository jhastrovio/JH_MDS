# JH-MDS Server Startup Script
# Run this to start both backend and frontend servers

Write-Host "🚀 Starting JH-MDS Servers..." -ForegroundColor Green

# Activate virtual environment
Write-Host "📦 Activating Python virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Start Backend Server
Write-Host "🔧 Starting Backend API Server (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\Activate.ps1; python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000"

# Wait a moment
Start-Sleep 2

# Start Frontend Server
Write-Host "🎨 Starting Frontend Server (Port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev"

# Wait for servers to start
Write-Host "⏳ Waiting for servers to initialize..." -ForegroundColor Yellow
Start-Sleep 5

# Test connections
Write-Host "🧪 Testing server connections..." -ForegroundColor Yellow

try {
    $backendTest = Invoke-RestMethod -Uri "http://localhost:8000/api/status" -Method GET -TimeoutSec 5
    Write-Host "✅ Backend API: RUNNING (http://localhost:8000)" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend API: NOT RESPONDING" -ForegroundColor Red
    Write-Host "   Try: http://localhost:8000/docs for API documentation" -ForegroundColor Gray
}

try {
    $frontendTest = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 5
    Write-Host "✅ Frontend: RUNNING (http://localhost:3000)" -ForegroundColor Green
} catch {
    Write-Host "❌ Frontend: NOT RESPONDING" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎯 IMMEDIATE NEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "2. Open http://localhost:8000/docs for API documentation" -ForegroundColor White
Write-Host "3. Check that both servers are running in the new PowerShell windows" -ForegroundColor White

Write-Host ""
Write-Host "📋 TODO PRIORITIES:" -ForegroundColor Cyan
Write-Host "• Set up environment variables (.env files)" -ForegroundColor White
Write-Host "• Connect frontend WebSocket to backend" -ForegroundColor White
Write-Host "• Test live data ingestion from Saxo" -ForegroundColor White

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
Read-Host 