# JH Market Data Service - Production Deployment Guide

## 🚀 Production Deployment Checklist

### Phase 1: Environment Setup

#### 1.1 External Services Setup
- [ ] **Redis (Critical)**: Set up Upstash Redis or Redis Cloud
  ```bash
  # Get Redis URL from provider (format: rediss://...)
  ```

- [ ] **SaxoBank Developer Account**: 
  - [ ] Register at https://www.developer.saxo/
  - [ ] Create application
  - [ ] Get App Key and App Secret
  - [ ] Configure redirect URI: `https://your-backend.vercel.app/api/auth/callback`

#### 1.2 Domain Setup
- [ ] Choose your domains:
  - Backend: `your-backend.vercel.app` 
  - Frontend: `your-frontend.vercel.app`

### Phase 2: Backend Deployment

#### 2.1 Environment Variables (Vercel Dashboard)
```bash
# Required
SAXO_APP_KEY=your-saxo-app-key-here
SAXO_APP_SECRET=your-saxo-app-secret-here
SAXO_REDIRECT_URI=https://your-backend.vercel.app/api/auth/callback
REDIS_URL=rediss://your-upstash-redis-url
NODE_ENV=production

# Security
JWT_SECRET=your-64-character-random-secret-here

# Optional
LOG_LEVEL=INFO
```

#### 2.2 Deploy Backend
```powershell
cd backend
vercel --prod
```

#### 2.3 Verify Backend Health
```bash
# Test health endpoints
curl https://your-backend.vercel.app/api/auth/health/simple
curl https://your-backend.vercel.app/api/auth/health/comprehensive
curl https://your-backend.vercel.app/api/auth/deployment/readiness
```

### Phase 3: Frontend Deployment

#### 3.1 Environment Variables (Vercel Dashboard)
```bash
# Required
NEXT_PUBLIC_API_BASE_URL=https://your-backend.vercel.app
NODE_ENV=production
```

#### 3.2 Deploy Frontend
```powershell
cd frontend
vercel --prod
```

### Phase 4: Production Testing

#### 4.1 Health Check Tests
```bash
# Backend health
curl https://your-backend.vercel.app/api/auth/health/simple

# Security validation
curl https://your-backend.vercel.app/api/auth/security/validate

# Deployment readiness
curl https://your-backend.vercel.app/api/auth/deployment/readiness
```

#### 4.2 OAuth Flow Test
```bash
# 1. Get auth URL
curl https://your-backend.vercel.app/api/auth/login

# 2. Visit auth_url in browser and complete OAuth
# 3. Check status
curl https://your-backend.vercel.app/api/auth/status
```

#### 4.3 API Functionality Test
```bash
# Test price endpoint (requires OAuth token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://your-backend.vercel.app/api/price?symbol=EUR-USD
```

### Phase 5: Monitoring Setup

#### 5.1 Production Monitoring
- [ ] Set up Vercel monitoring dashboard
- [ ] Configure alerts for function failures
- [ ] Monitor Redis usage and performance
- [ ] Set up uptime monitoring (e.g., UptimeRobot)

#### 5.2 Security Monitoring
- [ ] Review security headers
- [ ] Monitor for OAuth failures
- [ ] Set up rate limiting if needed
- [ ] Regular security scans

### Phase 6: Post-Deployment

#### 6.1 Performance Optimization
- [ ] Monitor function cold starts
- [ ] Optimize Redis cache TTL settings
- [ ] Review API response times
- [ ] Monitor memory usage

#### 6.2 Maintenance
- [ ] Schedule regular dependency updates
- [ ] Monitor OAuth token expiration
- [ ] Backup environment configurations
- [ ] Document rollback procedures

## 🔍 Production Readiness Indicators

### ✅ Ready for Production
- [ ] All health checks pass (`/api/auth/health/comprehensive`)
- [ ] Security validation shows no critical issues
- [ ] OAuth flow completes successfully
- [ ] Redis connectivity stable
- [ ] Environment variables properly configured
- [ ] HTTPS enforced everywhere

### ⚠️ Common Issues
1. **Redis Connection**: Ensure Redis URL uses `rediss://` (SSL)
2. **OAuth Redirect**: Must match exactly in SaxoBank portal
3. **CORS**: Frontend domain must be in allowed origins
4. **Environment Variables**: All required vars set in Vercel dashboard

## 🆘 Troubleshooting

### Check Logs
```bash
vercel logs --follow
```

### Debug Endpoints
```bash
# Comprehensive health check
curl https://your-backend.vercel.app/api/auth/health/comprehensive

# Security validation
curl https://your-backend.vercel.app/api/auth/security/validate

# OAuth debug
curl https://your-backend.vercel.app/api/auth/debug/status
```

### Redis Issues
```bash
# Test Redis connection
curl https://your-backend.vercel.app/api/debug/redis-connection
```

## 📞 Support

If you encounter issues:
1. Check the comprehensive health endpoint
2. Review Vercel function logs
3. Verify all environment variables are set
4. Test OAuth flow step by step
5. Confirm Redis connectivity

## 🎯 Success Metrics

- Uptime > 99.5%
- API response time < 500ms
- OAuth success rate > 95%
- Zero security vulnerabilities
- Health checks always green
