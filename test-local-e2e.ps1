# JH Market Data Service - Full End-to-End Local Testing
# This script tests the complete system locally before production deployment

param(
    [switch]$StartServices,
    [switch]$TestEndpoints,
    [switch]$TestOAuth,
    [switch]$TestMarketData,
    [switch]$All,
    [switch]$StopServices
)

$script:BackendPID = $null
$script:FrontendPID = $null
$script:RedisPID = $null

Write-Host "🧪 JH Market Data Service - Local End-to-End Testing" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# Function to start Redis locally
function Start-LocalRedis {
    Write-Host "`n🔴 Starting Local Redis..." -ForegroundColor Yellow
    
    # Check if Redis is already running
    $redisProcess = Get-Process -Name "redis-server" -ErrorAction SilentlyContinue
    if ($redisProcess) {
        Write-Host "✅ Redis already running (PID: $($redisProcess.Id))" -ForegroundColor Green
        return
    }
    
    # Try to start Redis using existing script
    if (Test-Path ".\start-redis.ps1") {
        Write-Host "Using existing Redis startup script..." -ForegroundColor Cyan
        .\start-redis.ps1
    } else {
        Write-Host "⚠️ Redis startup script not found. Please start Redis manually or install Redis." -ForegroundColor Yellow
        Write-Host "   Download Redis: https://github.com/tporadowski/redis/releases" -ForegroundColor White
        Write-Host "   Or use Docker: docker run -d -p 6379:6379 redis:alpine" -ForegroundColor White
    }
}

# Function to start backend server
function Start-BackendServer {
    Write-Host "`n⚙️ Starting Backend Server..." -ForegroundColor Yellow
    
    # Check if backend is already running
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/health/simple" -Method GET -TimeoutSec 2
        Write-Host "✅ Backend already running and healthy" -ForegroundColor Green
        return
    } catch {
        # Backend not running, start it
    }
    
    Set-Location "c:\Users\JamesHassett\dev\JH-MDS\backend"
    
    Write-Host "Starting FastAPI server..." -ForegroundColor Cyan
    $backendJob = Start-Job -ScriptBlock {
        Set-Location "c:\Users\JamesHassett\dev\JH-MDS\backend"
        python -m uvicorn app.app:app --host 0.0.0.0 --port 8000 --reload
    }
    
    Write-Host "⏳ Waiting for backend to start..." -ForegroundColor Cyan
    Start-Sleep -Seconds 5
    
    # Test if backend started successfully
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/health/simple" -Method GET -TimeoutSec 10
        Write-Host "✅ Backend server started successfully" -ForegroundColor Green
        $script:BackendPID = $backendJob.Id
    } catch {
        Write-Host "❌ Backend failed to start. Check logs." -ForegroundColor Red
        Receive-Job $backendJob
        Remove-Job $backendJob
    }
}

# Function to start frontend server
function Start-FrontendServer {
    Write-Host "`n🎨 Starting Frontend Server..." -ForegroundColor Yellow
    
    # Check if frontend is already running
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 2
        Write-Host "✅ Frontend already running" -ForegroundColor Green
        return
    } catch {
        # Frontend not running, start it
    }
    
    Set-Location "c:\Users\JamesHassett\dev\JH-MDS\frontend"
    
    # Check if dependencies are installed
    if (-not (Test-Path "node_modules")) {
        Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Cyan
        npm install
    }
    
    Write-Host "Starting Next.js development server..." -ForegroundColor Cyan
    $frontendJob = Start-Job -ScriptBlock {
        Set-Location "c:\Users\JamesHassett\dev\JH-MDS\frontend"
        npm run dev
    }
    
    Write-Host "⏳ Waiting for frontend to start..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10
    
    # Test if frontend started successfully
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 10
        Write-Host "✅ Frontend server started successfully" -ForegroundColor Green
        $script:FrontendPID = $frontendJob.Id
    } catch {
        Write-Host "❌ Frontend failed to start. Check logs." -ForegroundColor Red
        Receive-Job $frontendJob
        Remove-Job $frontendJob
    }
}

# Function to test all health endpoints
function Test-HealthEndpoints {
    Write-Host "`n🏥 Testing Health Endpoints..." -ForegroundColor Yellow
    
    $baseUrl = "http://localhost:8000/api/auth"
    
    # Test simple health check
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/health/simple" -Method GET
        $data = $response.Content | ConvertFrom-Json
        Write-Host "✅ Simple Health Check: $($data.status)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Simple Health Check: FAILED" -ForegroundColor Red
    }
    
    # Test comprehensive health check
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/health/comprehensive" -Method GET
        $data = $response.Content | ConvertFrom-Json
        $color = if ($data.status -eq "healthy") { "Green" } else { "Yellow" }
        Write-Host "✅ Comprehensive Health: $($data.status)" -ForegroundColor $color
        
        if ($data.details) {
            Write-Host "   Memory Usage: $($data.details.memory.usage_percent)%" -ForegroundColor White
            Write-Host "   Redis Status: $($data.details.redis.status)" -ForegroundColor White
            Write-Host "   OAuth Status: $($data.details.oauth.configured)" -ForegroundColor White
        }
    } catch {
        Write-Host "❌ Comprehensive Health Check: FAILED" -ForegroundColor Red
    }
    
    # Test security validation
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/security/validate" -Method GET
        $data = $response.Content | ConvertFrom-Json
        Write-Host "✅ Security Validation: $($data.overall_security_status)" -ForegroundColor Green
        Write-Host "   Security Score: $($data.production_config.security_score)%" -ForegroundColor White
    } catch {
        Write-Host "❌ Security Validation: FAILED" -ForegroundColor Red
    }
    
    # Test deployment readiness
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/deployment/readiness" -Method GET
        $data = $response.Content | ConvertFrom-Json
        $color = if ($data.deployment_ready) { "Green" } else { "Yellow" }
        Write-Host "✅ Deployment Readiness: $($data.deployment_ready)" -ForegroundColor $color
        
        if ($data.recommendations) {
            Write-Host "   Recommendations:" -ForegroundColor Yellow
            $data.recommendations | ForEach-Object { Write-Host "     - $_" -ForegroundColor White }
        }
    } catch {
        Write-Host "❌ Deployment Readiness: FAILED" -ForegroundColor Red
    }
}

# Function to test OAuth flow
function Test-OAuthFlow {
    Write-Host "`n🔐 Testing OAuth Flow..." -ForegroundColor Yellow
    
    try {
        # Test OAuth status endpoint
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/status" -Method GET
        $data = $response.Content | ConvertFrom-Json
        Write-Host "✅ OAuth Status Endpoint: Working" -ForegroundColor Green
        Write-Host "   Authenticated: $($data.authenticated)" -ForegroundColor White
        
        # Test OAuth login endpoint (should redirect)
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/login" -Method GET -MaximumRedirection 0
        } catch {
            if ($_.Exception.Response.StatusCode -eq 302) {
                Write-Host "✅ OAuth Login Redirect: Working" -ForegroundColor Green
                $location = $_.Exception.Response.Headers.Location
                if ($location -like "*saxobank*") {
                    Write-Host "   Redirects to: SaxoBank OAuth" -ForegroundColor White
                } else {
                    Write-Host "   Redirects to: $location" -ForegroundColor White
                }
            } else {
                Write-Host "❌ OAuth Login: Unexpected response" -ForegroundColor Red
            }
        }
        
    } catch {
        Write-Host "❌ OAuth Flow Test: FAILED" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Function to test market data endpoints
function Test-MarketDataEndpoints {
    Write-Host "`n📈 Testing Market Data Endpoints..." -ForegroundColor Yellow
    
    $baseUrl = "http://localhost:8000/api"
    
    # Test price endpoint (without auth - should fail gracefully)
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/price/EURUSD" -Method GET
        Write-Host "⚠️ Price Endpoint: Accessible without auth" -ForegroundColor Yellow
    } catch {
        if ($_.Exception.Response.StatusCode -eq 401 -or $_.Exception.Response.StatusCode -eq 403) {
            Write-Host "✅ Price Endpoint: Properly protected (401/403)" -ForegroundColor Green
        } else {
            Write-Host "❌ Price Endpoint: Unexpected error ($($_.Exception.Response.StatusCode))" -ForegroundColor Red
        }
    }
    
    # Test ticks endpoint (without auth - should fail gracefully)
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/ticks/EURUSD" -Method GET
        Write-Host "⚠️ Ticks Endpoint: Accessible without auth" -ForegroundColor Yellow
    } catch {
        if ($_.Exception.Response.StatusCode -eq 401 -or $_.Exception.Response.StatusCode -eq 403) {
            Write-Host "✅ Ticks Endpoint: Properly protected (401/403)" -ForegroundColor Green
        } else {
            Write-Host "❌ Ticks Endpoint: Unexpected error ($($_.Exception.Response.StatusCode))" -ForegroundColor Red
        }
    }
    
    # Test snapshot endpoint (without auth - should fail gracefully)
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/snapshot/EURUSD" -Method GET
        Write-Host "⚠️ Snapshot Endpoint: Accessible without auth" -ForegroundColor Yellow
    } catch {
        if ($_.Exception.Response.StatusCode -eq 401 -or $_.Exception.Response.StatusCode -eq 403) {
            Write-Host "✅ Snapshot Endpoint: Properly protected (401/403)" -ForegroundColor Green
        } else {
            Write-Host "❌ Snapshot Endpoint: Unexpected error ($($_.Exception.Response.StatusCode))" -ForegroundColor Red
        }
    }
}

# Function to stop all services
function Stop-AllServices {
    Write-Host "`n🛑 Stopping All Services..." -ForegroundColor Yellow
    
    # Stop background jobs
    Get-Job | Where-Object { $_.State -eq "Running" } | ForEach-Object {
        Write-Host "Stopping job: $($_.Name)" -ForegroundColor Cyan
        Stop-Job $_
        Remove-Job $_
    }
    
    # Stop any uvicorn processes
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*uvicorn*"
    } | ForEach-Object {
        Write-Host "Stopping backend process (PID: $($_.Id))" -ForegroundColor Cyan
        Stop-Process $_ -Force
    }
    
    Write-Host "✅ All services stopped" -ForegroundColor Green
}

# Function to open browser to local services
function Open-LocalServices {
    Write-Host "`n🌐 Opening Local Services..." -ForegroundColor Yellow
    
    Start-Process "http://localhost:3000"  # Frontend
    Start-Process "http://localhost:8000/docs"  # Backend API docs
    
    Write-Host "✅ Opened frontend and API documentation" -ForegroundColor Green
}

# Main execution logic
if ($StopServices) {
    Stop-AllServices
    exit 0
}

if ($StartServices -or $All) {
    Write-Host "`n🚀 Starting All Services..." -ForegroundColor Cyan
    Start-LocalRedis
    Start-BackendServer
    Start-FrontendServer
    
    Write-Host "`n⏳ Allowing services to fully initialize..." -ForegroundColor Cyan
    Start-Sleep -Seconds 5
}

if ($TestEndpoints -or $All) {
    Test-HealthEndpoints
}

if ($TestOAuth -or $All) {
    Test-OAuthFlow
}

if ($TestMarketData -or $All) {
    Test-MarketDataEndpoints
}

if ($All -or $StartServices) {
    Write-Host "`n📊 Local Service Status:" -ForegroundColor Cyan
    Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
    Write-Host "  Backend API: http://localhost:8000" -ForegroundColor White
    Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  Health Check: http://localhost:8000/api/auth/health/simple" -ForegroundColor White
    
    $openBrowser = Read-Host "`nOpen services in browser? (Y/n)"
    if ($openBrowser -ne "n" -and $openBrowser -ne "N") {
        Open-LocalServices
    }
    
    Write-Host "`n🎯 Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Test OAuth login flow manually in browser" -ForegroundColor White
    Write-Host "  2. Verify market data endpoints after authentication" -ForegroundColor White
    Write-Host "  3. Check all functionality works as expected" -ForegroundColor White
    Write-Host "  4. Run: .\test-local-e2e.ps1 -StopServices when done" -ForegroundColor White
    Write-Host "  5. Deploy to production with: .\deploy-vercel.ps1 -All" -ForegroundColor White
}

if (-not ($StartServices -or $TestEndpoints -or $TestOAuth -or $TestMarketData -or $All -or $StopServices)) {
    Write-Host "`n📖 Usage:" -ForegroundColor Cyan
    Write-Host "  .\test-local-e2e.ps1 -All              # Start services and run all tests" -ForegroundColor White
    Write-Host "  .\test-local-e2e.ps1 -StartServices    # Start all services only" -ForegroundColor White
    Write-Host "  .\test-local-e2e.ps1 -TestEndpoints    # Test health endpoints" -ForegroundColor White
    Write-Host "  .\test-local-e2e.ps1 -TestOAuth        # Test OAuth flow" -ForegroundColor White
    Write-Host "  .\test-local-e2e.ps1 -TestMarketData   # Test market data endpoints" -ForegroundColor White
    Write-Host "  .\test-local-e2e.ps1 -StopServices     # Stop all running services" -ForegroundColor White
    
    Write-Host "`n🔧 Prerequisites:" -ForegroundColor Cyan
    Write-Host "  1. Redis running locally (or Docker)" -ForegroundColor White
    Write-Host "  2. Python environment with dependencies installed" -ForegroundColor White
    Write-Host "  3. Node.js and npm for frontend" -ForegroundColor White
    Write-Host "  4. Environment variables configured (see .env.production.template)" -ForegroundColor White
}
