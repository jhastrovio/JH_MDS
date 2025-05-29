#!/usr/bin/env powershell
# Production Deployment Script for JH Market Data Service

param(
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$DryRun,
    [string]$Environment = "production"
)

Write-Host "🚀 JH Market Data Service - Production Deployment" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Check prerequisites
function Test-Prerequisites {
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow
    
    # Check Vercel CLI
    try {
        $vercelVersion = vercel --version
        Write-Host "✅ Vercel CLI: $vercelVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Vercel CLI not found. Install with: npm i -g vercel" -ForegroundColor Red
        exit 1
    }
    
    # Check Node.js
    try {
        $nodeVersion = node --version
        Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Node.js not found" -ForegroundColor Red
        exit 1
    }
    
    # Check Python
    try {
        $pythonVersion = python --version
        Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Python not found" -ForegroundColor Red
        exit 1
    }
}

function Test-EnvironmentVariables {
    Write-Host "🔧 Validating environment configuration..." -ForegroundColor Yellow
    
    $requiredBackendVars = @(
        "SAXO_APP_KEY",
        "SAXO_APP_SECRET", 
        "SAXO_REDIRECT_URI",
        "REDIS_URL"
    )
    
    $requiredFrontendVars = @(
        "NEXT_PUBLIC_API_BASE_URL"
    )
    
    Write-Host "Backend environment variables to configure:" -ForegroundColor Cyan
    foreach ($var in $requiredBackendVars) {
        Write-Host "  - $var" -ForegroundColor White
    }
    
    Write-Host "Frontend environment variables to configure:" -ForegroundColor Cyan
    foreach ($var in $requiredFrontendVars) {
        Write-Host "  - $var" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "⚠️  Ensure these are configured in Vercel dashboard before proceeding!" -ForegroundColor Yellow
    
    if (-not $DryRun) {
        $proceed = Read-Host "Continue with deployment? (y/N)"
        if ($proceed -ne "y" -and $proceed -ne "Y") {
            Write-Host "Deployment cancelled." -ForegroundColor Yellow
            exit 0
        }
    }
}

function Deploy-Backend {
    if ($SkipBackend) {
        Write-Host "⏭️  Skipping backend deployment" -ForegroundColor Yellow
        return
    }
    
    Write-Host "🔧 Deploying backend..." -ForegroundColor Yellow
    
    Push-Location backend
    
    try {
        if ($DryRun) {
            Write-Host "DRY RUN: Would run 'vercel --prod'" -ForegroundColor Cyan
        } else {
            Write-Host "Running: vercel --prod" -ForegroundColor Cyan
            vercel --prod
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Backend deployed successfully!" -ForegroundColor Green
            } else {
                Write-Host "❌ Backend deployment failed!" -ForegroundColor Red
                exit 1
            }
        }
    } finally {
        Pop-Location
    }
}

function Deploy-Frontend {
    if ($SkipFrontend) {
        Write-Host "⏭️  Skipping frontend deployment" -ForegroundColor Yellow
        return
    }
    
    Write-Host "🎨 Deploying frontend..." -ForegroundColor Yellow
    
    Push-Location frontend
    
    try {
        if ($DryRun) {
            Write-Host "DRY RUN: Would run 'vercel --prod'" -ForegroundColor Cyan
        } else {
            Write-Host "Running: vercel --prod" -ForegroundColor Cyan
            vercel --prod
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Frontend deployed successfully!" -ForegroundColor Green
            } else {
                Write-Host "❌ Frontend deployment failed!" -ForegroundColor Red
                exit 1
            }
        }
    } finally {
        Pop-Location
    }
}

function Test-Deployment {
    Write-Host "🧪 Testing deployment..." -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "DRY RUN: Would test deployment endpoints" -ForegroundColor Cyan
        return
    }
    
    Write-Host "Please test the following endpoints manually:" -ForegroundColor Cyan
    Write-Host "1. Backend health: https://your-backend.vercel.app/api/auth/health/simple" -ForegroundColor White
    Write-Host "2. Security check: https://your-backend.vercel.app/api/auth/security/validate" -ForegroundColor White
    Write-Host "3. Readiness check: https://your-backend.vercel.app/api/auth/deployment/readiness" -ForegroundColor White
    Write-Host "4. Frontend: https://your-frontend.vercel.app" -ForegroundColor White
    
    Write-Host ""
    Write-Host "OAuth flow test:" -ForegroundColor Cyan
    Write-Host "1. GET https://your-backend.vercel.app/api/auth/login" -ForegroundColor White
    Write-Host "2. Visit the auth_url returned" -ForegroundColor White
    Write-Host "3. Complete SaxoBank authentication" -ForegroundColor White
    Write-Host "4. Check successful redirect" -ForegroundColor White
}

function Show-PostDeployment {
    Write-Host ""
    Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
    Write-Host "======================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Test all endpoints listed above" -ForegroundColor White
    Write-Host "2. Configure monitoring alerts" -ForegroundColor White
    Write-Host "3. Set up uptime monitoring" -ForegroundColor White
    Write-Host "4. Review security settings" -ForegroundColor White
    Write-Host "5. Monitor Vercel function logs" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 Important URLs:" -ForegroundColor Cyan
    Write-Host "- Backend API docs: https://your-backend.vercel.app/docs" -ForegroundColor White
    Write-Host "- Health check: https://your-backend.vercel.app/api/auth/health/comprehensive" -ForegroundColor White
    Write-Host "- Security validation: https://your-backend.vercel.app/api/auth/security/validate" -ForegroundColor White
    Write-Host ""
    Write-Host "🔍 Monitoring:" -ForegroundColor Cyan
    Write-Host "- vercel logs --follow" -ForegroundColor White
    Write-Host "- Monitor Redis usage in your provider dashboard" -ForegroundColor White
    Write-Host "- Set up alerts for function failures" -ForegroundColor White
}

# Main execution
try {
    Test-Prerequisites
    Test-EnvironmentVariables
    Deploy-Backend
    Deploy-Frontend
    Test-Deployment
    Show-PostDeployment
} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
