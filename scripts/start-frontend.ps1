# Start Frontend Script
Write-Host "🎨 Starting JH-MDS Frontend..." -ForegroundColor Green

# Set Node.js PATH
$env:PATH = "$PWD\node-v20.12.2-win-x64;$env:PATH"

# Navigate to frontend
cd frontend

# Check Node.js
Write-Host "📦 Node.js version: $(node --version)" -ForegroundColor Yellow
Write-Host "📦 npm version: $(npm --version)" -ForegroundColor Yellow

# Start development server
Write-Host "🚀 Starting Next.js development server..." -ForegroundColor Yellow
npm run dev 