# Vercel Deployment Script for JH Market Data Service
# Run this script to deploy to production

param(
    [switch]$Backend,
    [switch]$Frontend,
    [switch]$All
)

Write-Host "🚀 JH Market Data Service - Vercel Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Check if Vercel CLI is installed
try {
    vercel --version | Out-Null
    Write-Host "✅ Vercel CLI detected" -ForegroundColor Green
} catch {
    Write-Host "❌ Vercel CLI not found. Install with: npm i -g vercel" -ForegroundColor Red
    exit 1
}

# Function to deploy backend
function Publish-Backend {
    Write-Host "`n🔧 Deploying Backend to Vercel..." -ForegroundColor Yellow
    
    Set-Location "c:\Users\JamesHassett\dev\JH-MDS\backend"
    
    Write-Host "📋 Backend deployment checklist:" -ForegroundColor Cyan
    Write-Host "  1. Environment variables configured in Vercel dashboard" -ForegroundColor White
    Write-Host "  2. REDIS_URL from Upstash configured" -ForegroundColor White
    Write-Host "  3. SAXO OAuth credentials configured" -ForegroundColor White
    Write-Host "  4. JWT_SECRET generated and configured" -ForegroundColor White
    
    $confirm = Read-Host "`nHave you configured all environment variables in Vercel dashboard? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "❌ Please configure environment variables first. See .env.production.template" -ForegroundColor Red
        return
    }
    
    Write-Host "`n🚀 Deploying backend..." -ForegroundColor Green
    vercel --prod
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Backend deployed successfully!" -ForegroundColor Green
        Write-Host "🔍 Test your deployment:" -ForegroundColor Cyan
        Write-Host "  Health check: curl https://your-backend-url.vercel.app/api/auth/health/simple" -ForegroundColor White
        Write-Host "  Full status: curl https://your-backend-url.vercel.app/api/auth/deployment/readiness" -ForegroundColor White
    } else {
        Write-Host "❌ Backend deployment failed!" -ForegroundColor Red
    }
}

# Function to deploy frontend
function Deploy-Frontend {
    Write-Host "`n🎨 Deploying Frontend to Vercel..." -ForegroundColor Yellow
    
    Set-Location "c:\Users\JamesHassett\dev\JH-MDS\frontend"
    
    Write-Host "📋 Frontend deployment checklist:" -ForegroundColor Cyan
    Write-Host "  1. NEXT_PUBLIC_API_BASE_URL configured in Vercel dashboard" -ForegroundColor White
    Write-Host "  2. Backend deployment URL obtained" -ForegroundColor White
    
    $backendUrl = Read-Host "`nEnter your backend Vercel URL (e.g., https://your-backend.vercel.app)"
    if (-not $backendUrl) {
        Write-Host "❌ Backend URL required for frontend deployment" -ForegroundColor Red
        return
    }
    
    Write-Host "`n🚀 Deploying frontend..." -ForegroundColor Green
    vercel --prod --env NEXT_PUBLIC_API_BASE_URL=$backendUrl --env NODE_ENV=production
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Frontend deployed successfully!" -ForegroundColor Green
        Write-Host "🌐 Visit your application at the provided URL" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Frontend deployment failed!" -ForegroundColor Red
    }
}

# Function to run post-deployment tests
function Test-Deployment {
    param([string]$BackendUrl)
    
    Write-Host "`n🧪 Running Post-Deployment Tests..." -ForegroundColor Yellow
    
    if (-not $BackendUrl) {
        $BackendUrl = Read-Host "Enter your backend URL for testing"
    }
    
    Write-Host "Testing health endpoints..." -ForegroundColor Cyan
    
    try {
        # Test simple health check
        $response = Invoke-WebRequest -Uri "$BackendUrl/api/auth/health/simple" -Method GET
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Simple health check: PASSED" -ForegroundColor Green
        }
        
        # Test comprehensive health check
        $response = Invoke-WebRequest -Uri "$BackendUrl/api/auth/health/comprehensive" -Method GET
        $healthData = $response.Content | ConvertFrom-Json
        
        if ($healthData.status -eq "healthy") {
            Write-Host "✅ Comprehensive health check: PASSED" -ForegroundColor Green
        } elseif ($healthData.status -eq "degraded") {
            Write-Host "⚠️ Comprehensive health check: DEGRADED" -ForegroundColor Yellow
            Write-Host "   Check Redis connectivity and OAuth configuration" -ForegroundColor Yellow
        }
        
        # Test deployment readiness
        $response = Invoke-WebRequest -Uri "$BackendUrl/api/auth/deployment/readiness" -Method GET
        $readiness = $response.Content | ConvertFrom-Json
        
        if ($readiness.deployment_ready -eq $true) {
            Write-Host "✅ Deployment readiness: READY" -ForegroundColor Green
        } else {
            Write-Host "❌ Deployment readiness: NOT READY" -ForegroundColor Red
            Write-Host "   Recommendations: $($readiness.recommendations -join ', ')" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "❌ Deployment tests failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Main execution logic
if ($All -or ($Backend -and $Frontend)) {
    Publish-Backend
    $backendUrl = Read-Host "`nEnter your deployed backend URL for frontend configuration"
    Deploy-Frontend
    Test-Deployment -BackendUrl $backendUrl
} elseif ($Backend) {
    Publish-Backend
    $backendUrl = Read-Host "`nEnter your deployed backend URL for testing (optional)"
    if ($backendUrl) {
        Test-Deployment -BackendUrl $backendUrl
    }
} elseif ($Frontend) {
    Deploy-Frontend
} else {
    Write-Host "`n📖 Usage:" -ForegroundColor Cyan
    Write-Host "  .\deploy-vercel.ps1 -Backend    # Deploy backend only" -ForegroundColor White
    Write-Host "  .\deploy-vercel.ps1 -Frontend   # Deploy frontend only" -ForegroundColor White
    Write-Host "  .\deploy-vercel.ps1 -All        # Deploy both backend and frontend" -ForegroundColor White
    Write-Host "`n🔧 Prerequisites:" -ForegroundColor Cyan
    Write-Host "  1. Install Vercel CLI: npm i -g vercel" -ForegroundColor White
    Write-Host "  2. Login to Vercel: vercel login" -ForegroundColor White
    Write-Host "  3. Configure environment variables using .env.production.template" -ForegroundColor White
    Write-Host "  4. Ensure Upstash Redis is configured and REDIS_URL is set" -ForegroundColor White
    Write-Host "  5. Configure SaxoBank OAuth with production redirect URI" -ForegroundColor White
}

Write-Host "`n🎯 Next Steps After Deployment:" -ForegroundColor Cyan
Write-Host "  1. Test OAuth login flow" -ForegroundColor White
Write-Host "  2. Verify market data endpoints" -ForegroundColor White
Write-Host "  3. Monitor logs in Vercel dashboard" -ForegroundColor White
Write-Host "  4. Set up uptime monitoring" -ForegroundColor White
Write-Host "  5. Configure custom domain (optional)" -ForegroundColor White
