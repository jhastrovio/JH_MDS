# Vercel Deployment Checklist - Fix OAuth "Invalid state parameter"

## 🚨 Immediate Action Items

### 1. Set Up External Redis (CRITICAL)
Your OAuth state storage needs Redis. On Vercel, you can't use local Redis.

**Quick Setup with Upstash (Free):**
1. Go to [console.upstash.com](https://console.upstash.com)
2. Sign up/login
3. Create new Redis database
4. Copy the `REDIS_URL` (starts with `rediss://`)

### 2. Configure Vercel Environment Variables

**Backend Project Environment Variables:**
```bash
SAXO_APP_KEY=your-saxo-app-key
SAXO_APP_SECRET=your-saxo-app-secret  
SAXO_REDIRECT_URI=https://your-backend.vercel.app/api/auth/callback
REDIS_URL=rediss://your-upstash-redis-url
```

**Frontend Project Environment Variables:**
```bash
NEXT_PUBLIC_API_BASE_URL=https://your-backend.vercel.app
```

### 3. Update SaxoBank Developer Portal
1. Login to [SaxoBank Developer Portal](https://www.developer.saxo/)
2. Update your app's redirect URI to: `https://your-backend.vercel.app/api/auth/callback`
3. **Must be exact match with HTTPS**

### 4. Deploy and Test

**Deploy Backend:**
```bash
cd backend
vercel --prod
```

**Deploy Frontend:**
```bash
cd frontend  
vercel --prod
```

**Test Redis Connection:**
```bash
curl https://your-backend.vercel.app/api/debug/redis-connection
```

**Test OAuth Configuration:**
```bash
curl https://your-backend.vercel.app/api/auth/debug
```

## 🔍 Troubleshooting Steps

### Step 1: Verify Redis Connection
```bash
curl https://your-backend.vercel.app/api/debug/redis-connection
```

**Expected Response:**
```json
{
  "status": "success",
  "redis_ping": "ok", 
  "oauth_state_storage": "ok",
  "message": "Redis connection and OAuth state storage working correctly"
}
```

**If Failed:** Check `REDIS_URL` in Vercel environment variables

### Step 2: Check OAuth Configuration  
```bash
curl https://your-backend.vercel.app/api/auth/debug
```

**Expected Response:**
```json
{
  "status": "ok",
  "oauth_available": true,
  "environment_vars": {
    "SAXO_APP_KEY": "SET",
    "SAXO_APP_SECRET": "SET", 
    "REDIS_URL": "SET"
  }
}
```

**If Failed:** Add missing environment variables in Vercel dashboard

### Step 3: Test OAuth Flow
```bash
curl https://your-backend.vercel.app/api/auth/login
```

**Expected Response:**
```json
{
  "auth_url": "https://live.logonvalidation.net/authorize?...",
  "state": "some-random-state-string",
  "message": "Visit auth_url to complete authentication"
}
```

### Step 4: Complete OAuth in Browser
1. Visit the `auth_url` from Step 3
2. Complete SaxoBank authentication
3. Should redirect to success page (not error)

## 🛠️ Common Issues & Fixes

### Issue: "Redis connection failed"
**Cause:** No external Redis configured
**Fix:** 
1. Set up Upstash Redis (free tier available)
2. Add `REDIS_URL` to Vercel environment variables
3. Redeploy backend

### Issue: "OAuth not configured"  
**Cause:** Missing environment variables
**Fix:**
1. Add all required env vars in Vercel dashboard
2. Redeploy after adding variables

### Issue: "Redirect URI mismatch"
**Cause:** SaxoBank redirect URI doesn't match Vercel URL
**Fix:**
1. Update SaxoBank app settings
2. Use exact URL: `https://your-backend.vercel.app/api/auth/callback`

### Issue: "Invalid state parameter" (Still happening)
**Cause:** State not being stored/retrieved from Redis
**Fix:**
1. Verify Redis connection test passes
2. Check Vercel function logs: `vercel logs --follow`
3. Ensure Redis URL uses `rediss://` (with SSL)

## 📋 Environment Variables Reference

### Backend (Required)
```bash
SAXO_APP_KEY=your-app-key-from-saxo-developer-portal
SAXO_APP_SECRET=your-app-secret-from-saxo-developer-portal
SAXO_REDIRECT_URI=https://your-backend.vercel.app/api/auth/callback
REDIS_URL=rediss://your-redis-provider-url
```

### Frontend (Required)
```bash
NEXT_PUBLIC_API_BASE_URL=https://your-backend.vercel.app
```

### Optional
```bash
JWT_SECRET=your-random-secret-for-internal-auth
FRONTEND_URL=https://your-custom-frontend-domain.com
```

## 🚀 Quick Commands

```bash
# Check what's deployed
vercel ls

# View logs
vercel logs --follow

# Check environment variables
vercel env ls

# Redeploy
vercel --prod

# Test endpoints
curl https://your-backend.vercel.app/api/auth/health
curl https://your-backend.vercel.app/api/debug/redis-connection
curl https://your-backend.vercel.app/api/auth/debug
```

## ✅ Success Indicators

- [ ] Redis connection test returns "success"
- [ ] OAuth debug shows all environment variables "SET"
- [ ] OAuth login returns valid auth_url and state
- [ ] Completing OAuth flow shows success page (not error)
- [ ] Can access market data with OAuth token

## 🆘 Still Having Issues?

1. **Check Vercel Function Logs:**
   ```bash
   vercel logs --follow
   ```

2. **Verify Redis Service:**
   - Login to your Redis provider (Upstash/Redis Cloud)
   - Check if database is active and accessible

3. **Test Locally First:**
   - Set up local Redis: `redis-server`
   - Test OAuth flow locally with same environment variables
   - If local works but Vercel doesn't, it's a deployment issue

4. **Common Vercel Issues:**
   - Environment variables not saved properly
   - Function timeout (upgrade Vercel plan)
   - Redis connection from different regions

## 📞 Next Steps

After completing this checklist:
1. Test the full OAuth flow end-to-end
2. Verify market data API calls work with OAuth token
3. Test frontend integration with OAuth
4. Monitor Vercel function logs for any errors 