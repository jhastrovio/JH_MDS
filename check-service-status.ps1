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
    
    if ($null -ne $response.heartbeat_age_seconds) {
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
    # Correctly invoke python interpreter to run the script block
    # The entire python script is passed as a single string argument to python -c
    # Ensure the here-string is correctly formatted and there are no PS parsing issues.
    $pythonScript = @"
import asyncio
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path('backend')))
from storage.redis_client import get_redis

async def check_redis():
    redis = None # Initialize redis to None
    try:
        redis = get_redis()
        # Check service keys
        status = await redis.get('service:market_data:status')
        heartbeat = await redis.get('service:market_data:heartbeat')
        
        # Check data keys
        fx_keys = []
        # scan_iter returns bytes, decode them
        async for key_bytes in redis.scan_iter(match='fx:*'):
            fx_keys.append(key_bytes.decode('utf-8'))
        
        print(f'Service Status in Redis: {status}')
        print(f'Last Heartbeat: {heartbeat}')
        print(f'FX Data Keys: {len(fx_keys)} symbols')
        
        # Sample latest data
        if fx_keys:
            sample_key = fx_keys[0] # Get the first key as a sample
            # redis.get with decode_responses=True (default in get_redis) should return str
            sample_data_str = await redis.get(sample_key) 
            if sample_data_str:
                data = json.loads(sample_data_str)
                print(f'Latest {sample_key}: {data["bid"]}/{data["ask"]} at {data["timestamp"]}')
            else:
                print(f'No data found for sample key: {sample_key}')
        else:
            print('No FX data keys found in Redis.')
        
    except Exception as e:
        print(f'Redis check failed: {e}')
        # For more detailed debugging:
        # import traceback
        # traceback.print_exc()
    finally:
        if redis: # Ensure redis client exists before trying to close
            await redis.close()

asyncio.run(check_redis())
"@
    python -c "$pythonScript"
} catch {
    Write-Host "❌ Could not check Redis directly" -ForegroundColor Red
    Write-Host $_.Exception.Message # Print the actual error message
}

Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Cyan
Write-Host "  • Start service: .\start-market-data-service.ps1" -ForegroundColor Gray
Write-Host "  • Start backend: .\start-servers.ps1" -ForegroundColor Gray
Write-Host "  • View logs: Get-Content market_data_service.log -Tail 20" -ForegroundColor Gray