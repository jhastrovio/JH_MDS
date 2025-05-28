# Check Market Data Service Status
# Quick script to monitor the real-time data ingestion service

Write-Host "🔍 Checking Market Data Service Status..." -ForegroundColor Green

# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Check service status via API
Write-Host "📡 Checking service via API..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/service/status" -Method GET
    
    Write-Host ""
    Write-Host "Service Status:" -ForegroundColor White
    Write-Host "  Status: $($response.service_status)" -ForegroundColor $(if ($response.is_healthy) { "Green" } else { "Red" })
    Write-Host "  Healthy: $($response.is_healthy)" -ForegroundColor $(if ($response.is_healthy) { "Green" } else { "Red" })
    Write-Host "  Restart Count: $($response.restart_count)" -ForegroundColor Yellow
    Write-Host "  Last Update: $($response.last_update)" -ForegroundColor Gray
    
    if ($response.heartbeat_age_seconds -ne $null) {
        $heartbeatAge = [math]::Round($response.heartbeat_age_seconds, 1)
        Write-Host "  Heartbeat Age: ${heartbeatAge}s" -ForegroundColor Gray
    }
    
    Write-Host "  Symbols: $($response.symbols_monitored -join ', ')" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Could not reach API endpoint. Is the backend running?" -ForegroundColor Red
    Write-Host "   Start backend with: .\start-servers.ps1" -ForegroundColor Gray
}

Write-Host ""

# Check Redis directly
Write-Host "🔍 Checking Redis directly..." -ForegroundColor Yellow
try {
    $redisStatus = & python -c "
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path('backend')))
from storage.redis_client import get_redis
import json

async def check_redis():
    redis = get_redis()
    try:
        # Check service keys
        status = await redis.get('service:market_data:status')
        heartbeat = await redis.get('service:market_data:heartbeat')
        
        # Check data keys
        fx_keys = []
        async for key in redis.scan_iter(match='fx:*'):
            fx_keys.append(key)
        
        print(f'Service Status in Redis: {status}')
        print(f'Last Heartbeat: {heartbeat}')
        print(f'FX Data Keys: {len(fx_keys)} symbols')
        
        # Sample latest data
        if fx_keys:
            sample_key = fx_keys[0]
            sample_data = await redis.get(sample_key)
            if sample_data:
                data = json.loads(sample_data)
                print(f'Latest {sample_key}: {data[\"bid\"]}/{data[\"ask\"]} at {data[\"timestamp\"]}')
        
    except Exception as e:
        print(f'Redis check failed: {e}')
    finally:
        await redis.close()

asyncio.run(check_redis())
"
} catch {
    Write-Host "❌ Could not check Redis directly" -ForegroundColor Red
}

Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Cyan
Write-Host "  • Start service: .\start-market-data-service.ps1" -ForegroundColor Gray
Write-Host "  • Start backend: .\start-servers.ps1" -ForegroundColor Gray
Write-Host "  • View logs: Get-Content market_data_service.log -Tail 20" -ForegroundColor Gray 