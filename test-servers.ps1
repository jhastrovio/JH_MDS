Write-Host "Testing JH-MDS Servers..." -ForegroundColor Green

Write-Host "Testing Backend API..." -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "http://localhost:8000/docs" -Method GET -TimeoutSec 5 | Out-Null
    Write-Host "✅ Backend API: RUNNING (http://localhost:8000)" -ForegroundColor Green
    Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Gray
} catch {
    Write-Host "❌ Backend API: NOT RESPONDING" -ForegroundColor Red
}

Write-Host "Testing Frontend..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 5 | Out-Null
    Write-Host "✅ Frontend: RUNNING (http://localhost:3000)" -ForegroundColor Green
} catch {
    Write-Host "❌ Frontend: NOT RESPONDING" -ForegroundColor Red
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "2. Open http://localhost:8000/docs for API documentation" -ForegroundColor White 