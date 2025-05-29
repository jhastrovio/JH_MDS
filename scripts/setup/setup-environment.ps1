# JH-MDS Environment Setup Script
# Run this to configure environment variables for real market data

Write-Host "🔧 Setting up JH-MDS Environment Variables..." -ForegroundColor Green

# Backend Environment Variables
Write-Host "📝 Creating backend .env.local file..." -ForegroundColor Yellow

$backendEnv = @"
# JH Market Data Service - Backend Environment Variables

# API Configuration
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-jwt-secret-key-change-this-in-production

# SaxoBank API Configuration
# Replace with your actual SaxoBank API token from https://www.developer.saxo/
SAXO_API_TOKEN=your-saxo-api-token-here

# Microsoft OneDrive Integration (optional for now)
ONE_DRIVE_CLIENT_ID=your-onedrive-client-id
ONE_DRIVE_CLIENT_SECRET=your-onedrive-client-secret

# Development Settings
NODE_ENV=development
"@

$backendEnv | Out-File -FilePath ".env.local" -Encoding UTF8

# Frontend Environment Variables  
Write-Host "📝 Creating frontend .env.local file..." -ForegroundColor Yellow

$frontendEnv = @"
# JH Market Data Service - Frontend Environment Variables

# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NODE_ENV=development
"@

$frontendEnv | Out-File -FilePath "frontend/.env.local" -Encoding UTF8

Write-Host "✅ Environment files created!" -ForegroundColor Green
Write-Host ""
Write-Host "🔑 IMPORTANT: Update your SaxoBank API token!" -ForegroundColor Cyan
Write-Host "1. Get your API token from https://www.developer.saxo/" -ForegroundColor White
Write-Host "2. Edit .env.local and replace 'your-saxo-api-token-here'" -ForegroundColor White
Write-Host "3. Save the file" -ForegroundColor White
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Start Redis server (or use Upstash Redis cloud)" -ForegroundColor White
Write-Host "2. Run .\start-servers.ps1 to start both servers" -ForegroundColor White
Write-Host "3. Start the market data ingestion service" -ForegroundColor White 