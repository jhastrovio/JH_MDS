# Redis Setup Script for Windows
# This script downloads and sets up Redis for the JH-MDS project

Write-Host "Setting up Redis for Windows..." -ForegroundColor Green

# Create redis directory
$redisDir = ".\redis"
if (-not (Test-Path $redisDir)) {
    New-Item -ItemType Directory -Path $redisDir
}

# Check if Redis is already downloaded
$redisExe = "$redisDir\redis-server.exe"
if (Test-Path $redisExe) {
    Write-Host "Redis already downloaded" -ForegroundColor Green
} else {
    Write-Host "Downloading Redis for Windows..." -ForegroundColor Yellow
    
    # Download Redis (using the tporadowski build which is compatible with Windows)
    $redisUrl = "https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip"
    $redisZip = "$redisDir\redis.zip"
    
    try {
        Invoke-WebRequest -Uri $redisUrl -OutFile $redisZip
        Write-Host "Redis downloaded successfully" -ForegroundColor Green
        
        # Extract Redis
        Write-Host "Extracting Redis..." -ForegroundColor Yellow
        Expand-Archive -Path $redisZip -DestinationPath $redisDir -Force
        
        # Clean up zip file
        Remove-Item $redisZip
        
        Write-Host "Redis extracted successfully" -ForegroundColor Green
    } catch {
        Write-Host "Failed to download Redis: $_" -ForegroundColor Red
        exit 1
    }
}

# Create Redis configuration file
$redisConf = "$redisDir\redis.conf"
$configContent = @"
# Redis configuration for JH-MDS
port 6379
bind 127.0.0.1
save ""
appendonly no
"@

$configContent | Out-File -FilePath $redisConf -Encoding UTF8

Write-Host "Redis configuration created" -ForegroundColor Green

# Create Redis start script
$startScript = "$redisDir\start-redis.ps1"
$startContent = @"
# Start Redis Server
Write-Host "Starting Redis Server..." -ForegroundColor Green
& "$PSScriptRoot\redis-server.exe" "$PSScriptRoot\redis.conf"
"@

$startContent | Out-File -FilePath $startScript -Encoding UTF8

Write-Host "Redis start script created" -ForegroundColor Green
Write-Host ""
Write-Host "Redis Setup Complete!" -ForegroundColor Cyan
Write-Host "To start Redis: .\redis\start-redis.ps1" -ForegroundColor White
Write-Host "To test Redis: .\redis\redis-cli.exe ping" -ForegroundColor White 