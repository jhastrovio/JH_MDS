# JH Market Data Service - Production Configuration Guide

## 🔧 Environment Variables Setup

### 1. Vercel Dashboard Configuration

Navigate to your Vercel project dashboard → Settings → Environment Variables

Add the following variables for **Production** environment:

#### Required Variables:

| Variable Name | Value | Source |
|---------------|-------|--------|
| `REDIS_URL` | `redis://default:YOUR_PASSWORD@YOUR_ENDPOINT:PORT` | Upstash Dashboard |
| `SAXO_CLIENT_ID` | Your SaxoBank client ID | SaxoBank Developer Portal |
| `SAXO_CLIENT_SECRET` | Your SaxoBank client secret | SaxoBank Developer Portal |
| `SAXO_REDIRECT_URI` | `https://your-backend.vercel.app/api/auth/callback` | Set after backend deployment |
| `JWT_SECRET` | Generate 32+ character random string | Use: `openssl rand -base64 32` |
| `NODE_ENV` | `production` | Static value |

#### Optional Variables:

| Variable Name | Value | Purpose |
|---------------|-------|---------|
| `LOG_LEVEL` | `INFO` | Production logging level |
| `LOG_FORMAT` | `json` | Structured logging for Vercel |

### 2. Upstash Redis Configuration

✅ **You already have this set up!**

1. Go to [Upstash Console](https://console.upstash.com/)
2. Select your Redis database
3. Copy the **Redis URL** (format: `redis://default:password@endpoint:port`)
4. Add this as `REDIS_URL` in Vercel environment variables

### 3. SaxoBank OAuth Production Setup

#### Update Redirect URI in SaxoBank Developer Portal:

1. Go to [SaxoBank Developer Portal](https://developer.saxobank.com)
2. Navigate to your application
3. Update redirect URIs to include:
   - `https://your-backend.vercel.app/api/auth/callback` (production)
   - `http://localhost:8000/api/auth/callback` (development - keep for testing)

#### Get OAuth Credentials:
- Copy **Client ID** → Add as `SAXO_CLIENT_ID` in Vercel
- Copy **Client Secret** → Add as `SAXO_CLIENT_SECRET` in Vercel

### 4. JWT Secret Generation

Generate a secure JWT secret:

```powershell
# PowerShell method 1:
[System.Web.Security.Membership]::GeneratePassword(32, 8)

# PowerShell method 2:
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})

# If you have OpenSSL:
openssl rand -base64 32
```

## 🚀 Deployment Process

### Step 1: Configure Environment Variables
1. Use the `.env.production.template` file as reference
2. Add all variables to Vercel dashboard under Environment Variables
3. Ensure all values are correct and secure

### Step 2: Deploy Backend
```powershell
.\deploy-vercel.ps1 -Backend
```

### Step 3: Update SaxoBank Redirect URI
After backend deployment, update SaxoBank OAuth with your production URL

### Step 4: Deploy Frontend
```powershell
.\deploy-vercel.ps1 -Frontend
```

### Step 5: Test Production Deployment
```powershell
# Test health endpoints
curl https://your-backend.vercel.app/api/auth/health/simple
curl https://your-backend.vercel.app/api/auth/deployment/readiness

# Test OAuth flow
# Visit your frontend URL and try logging in
```

## 🔍 Production Monitoring

### Health Check Endpoints
- **Simple**: `/api/auth/health/simple` - Basic availability check
- **Comprehensive**: `/api/auth/health/comprehensive` - Full system status
- **Security**: `/api/auth/security/validate` - Security configuration check
- **Readiness**: `/api/auth/deployment/readiness` - Complete deployment status

### Expected Responses
All endpoints should return status `200` with:
- Simple: `{"status":"ok"}`
- Comprehensive: `{"status":"healthy"}` (or `"degraded"` with details)
- Security: `{"overall_security_status":"READY"}`
- Readiness: `{"deployment_ready":true}`

## 🛠 Troubleshooting

### Common Issues:

1. **Redis Connection Failed**
   - Check `REDIS_URL` format and credentials
   - Verify Upstash database is active
   - Test connectivity with Upstash console

2. **OAuth Login Fails**
   - Verify redirect URI matches exactly in SaxoBank portal
   - Check `SAXO_CLIENT_ID` and `SAXO_CLIENT_SECRET`
   - Ensure production URL is correct

3. **JWT Issues**
   - Verify `JWT_SECRET` is set and secure (32+ characters)
   - Check for special characters that might need escaping

4. **Environment Variables**
   - All variables must be set in Vercel **Production** environment
   - No trailing spaces or quotes in values
   - Verify deployment picked up latest environment variables

### Debug Commands:
```powershell
# Check deployment status
curl https://your-backend.vercel.app/api/auth/deployment/readiness

# Check security configuration
curl https://your-backend.vercel.app/api/auth/security/validate

# Check system health
curl https://your-backend.vercel.app/api/auth/health/comprehensive
```

## ✅ Production Checklist

- [ ] Upstash Redis configured and `REDIS_URL` set
- [ ] SaxoBank OAuth credentials configured
- [ ] Production redirect URI added to SaxoBank portal
- [ ] JWT secret generated and configured
- [ ] All environment variables set in Vercel dashboard
- [ ] Backend deployed successfully
- [ ] Frontend deployed with correct API URL
- [ ] Health checks returning healthy status
- [ ] OAuth login flow working
- [ ] Market data endpoints responding
- [ ] Production monitoring set up

Your JH Market Data Service is now ready for production! 🎉
