# Start Market Data Service - Improved Real-time Data Ingestion
# This script starts the enhanced market data service with health monitoring

Write-Host "🚀 Starting Enhanced Market Data Service..." -ForegroundColor Green

# Check if environment is set up
if (-not (Test-Path ".env")) {
    Write-Host "❌ Environment not configured! Run .\setup-environment.ps1 first" -ForegroundColor Red
    exit 1
}

# Check if Redis is running
Write-Host "🔍 Checking Redis connection..." -ForegroundColor Yellow
try {
    $redisTest = & .\.venv\Scripts\python.exe -c "
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path('backend')))
from storage.redis_client import get_redis
import asyncio

async def test_redis():
    redis = get_redis()
    try:
        await redis.ping()
        print('Redis connection: OK')
        return True
    except Exception as e:
        print(f'Redis connection failed: {e}')
        return False
    finally:
        await redis.close()

result = asyncio.run(test_redis())
"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Redis connection failed! Make sure Redis is running." -ForegroundColor Red
        Write-Host "   Run .\setup-redis.ps1 to start Redis" -ForegroundColor Gray
        exit 1
    }
} catch {
    Write-Host "❌ Failed to test Redis connection" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "📦 Activating Python virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Check if SaxoBank API token is configured
$envContent = Get-Content ".env" -Raw
if ($envContent -match "SAXO_API_TOKEN=your-saxo-api-token-here") {
    Write-Host "⚠️  WARNING: SaxoBank API token not configured!" -ForegroundColor Yellow
    Write-Host "   Edit .env and add your real API token from https://www.developer.saxo/" -ForegroundColor Gray
    Write-Host "   The service will fail until you provide a valid token." -ForegroundColor Gray
    Write-Host ""
}

# Create log directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

Write-Host "🔗 Starting enhanced market data service..." -ForegroundColor Green
Write-Host "   Features:" -ForegroundColor Gray
Write-Host "   • Automatic reconnection on failures" -ForegroundColor Gray
Write-Host "   • Health monitoring and status tracking" -ForegroundColor Gray
Write-Host "   • Service logs in market_data_service.log" -ForegroundColor Gray
Write-Host "   • Graceful shutdown handling" -ForegroundColor Gray
Write-Host ""
Write-Host "   Press Ctrl+C to stop the service" -ForegroundColor Yellow
Write-Host ""

# Start the service
try {
    python backend/ingest/market_data_service.py
} catch {
    Write-Host "❌ Service failed to start: $_" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "📊 Market Data Service stopped" -ForegroundColor Yellow
    
    # Show service status
    Write-Host "🔍 Checking final service status..." -ForegroundColor Gray
    try {
        $statusCheck = & .\.venv\Scripts\python.exe -c "
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path('backend')))
from storage.redis_client import get_redis

async def check_status():
    redis = get_redis()
    try:
        status = await redis.get('service:market_data:status')
        heartbeat = await redis.get('service:market_data:heartbeat')
        print(f'Final status: {status}')
        print(f'Last heartbeat: {heartbeat}')
    finally:
        await redis.close()

asyncio.run(check_status())
"
    } catch {
        Write-Host "Could not retrieve final status" -ForegroundColor Gray
    }
} 