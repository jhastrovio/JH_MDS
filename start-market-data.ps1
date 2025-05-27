# Start Market Data Ingestion Service
# This script starts the SaxoBank WebSocket client to pull real market data

Write-Host "📊 Starting Market Data Ingestion Service..." -ForegroundColor Green

# Check if environment is set up
if (-not (Test-Path ".env")) {
    Write-Host "❌ Environment not configured! Run .\setup-environment.ps1 first" -ForegroundColor Red
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

# Create a simple market data ingestion script
$ingestScript = @"
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from ingest.saxo_ws import stream_quotes
from storage.redis_client import get_redis

# FX symbols to stream
FX_SYMBOLS = [
    'EUR-USD', 'GBP-USD', 'USD-JPY', 'AUD-USD', 
    'USD-CHF', 'USD-CAD', 'NZD-USD'
]

async def main():
    print("🔗 Connecting to SaxoBank WebSocket...")
    print(f"📊 Streaming symbols: {', '.join(FX_SYMBOLS)}")
    
    redis = get_redis()
    try:
        await stream_quotes(FX_SYMBOLS, redis)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Check your SAXO_API_TOKEN in .env")
    finally:
        await redis.close()

if __name__ == "__main__":
    asyncio.run(main())
"@

# Write the ingestion script
$ingestScript | Out-File -FilePath "run_market_data.py" -Encoding UTF8

Write-Host "🚀 Starting market data ingestion..." -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Run the market data ingestion
python run_market_data.py 