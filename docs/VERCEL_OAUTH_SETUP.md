# OAuth Setup for Vercel Deployment

## 🚀 Vercel-Specific OAuth Configuration

### Key Differences from Local Development

1. **Serverless Environment**: Each request runs on a potentially different instance
2. **No Local Redis**: Must use external Redis service (Upstash, Redis Cloud, etc.)
3. **HTTPS Required**: All URLs must use `https://` 
4. **Environment Variables**: Configured in Vercel dashboard, not `.env` files
5. **Cold Starts**: First request might be slower due to serverless cold starts

## Required External Services

### 1. Redis Service (Required for OAuth State)

**Option A: Upstash Redis (Recommended)**
1. Go to [upstash.com](https://upstash.com)
2. Create free account
3. Create new Redis database
4. Copy the Redis URL (format: `rediss://...`)

**Option B: Redis Cloud**
1. Go to [redis.com](https://redis.com)
2. Create free account  
3. Create new database
4. Get connection URL

**Option C: Railway Redis**
1. Go to [railway.app](https://railway.app)
2. Create Redis service
3. Get connection URL

## Vercel Environment Variables Setup

### 1. Backend Environment Variables
In your Vercel dashboard for the backend project, add:

```bash
# SaxoBank OAuth (REQUIRED)
SAXO_APP_KEY=your-saxo-app-key-from-developer-portal
SAXO_APP_SECRET=your-saxo-app-secret-from-developer-portal
SAXO_REDIRECT_URI=https://your-backend.vercel.app/api/auth/callback

# Redis (REQUIRED for OAuth state)
REDIS_URL=rediss://your-redis-url-from-upstash-or-other-provider

# JWT Secret (OPTIONAL)
JWT_SECRET=your-random-jwt-secret-string
```

### 2. Frontend Environment Variables  
In your Vercel dashboard for the frontend project, add:

```bash
# Backend API URL
NEXT_PUBLIC_API_BASE_URL=https://your-backend.vercel.app
```

## SaxoBank Developer Portal Configuration

### Update Redirect URI
1. Log into [SaxoBank Developer Portal](https://www.developer.saxo/)
2. Go to your application settings
3. Update redirect URI to: `https://your-backend.vercel.app/api/auth/callback`
4. **Important**: Must be exact match including `https://`

## Deployment Steps

### 1. Deploy Backend to Vercel

```bash
# From your project root
cd backend
vercel --prod

# Or link to existing project
vercel link
vercel --prod
```

### 2. Deploy Frontend to Vercel

```bash
# From your project root  
cd frontend
vercel --prod

# Or link to existing project
vercel link
vercel --prod
```

### 3. Configure Environment Variables

**Backend Variables** (in Vercel dashboard):
- `SAXO_APP_KEY`
- `SAXO_APP_SECRET` 
- `SAXO_REDIRECT_URI`
- `REDIS_URL`

**Frontend Variables** (in Vercel dashboard):
- `NEXT_PUBLIC_API_BASE_URL`

## Testing OAuth Flow on Vercel

### 1. Check Backend Health
```bash
curl https://your-backend.vercel.app/api/auth/health
```

### 2. Check OAuth Configuration
```bash
curl https://your-backend.vercel.app/api/auth/debug
```

### 3. Initiate OAuth Flow
```bash
curl https://your-backend.vercel.app/api/auth/login
```

### 4. Complete Flow in Browser
1. Visit the `auth_url` from step 3
2. Complete SaxoBank authentication
3. Should redirect to success page

## Common Vercel OAuth Issues

### 1. "Invalid state parameter" 
**Cause**: Redis not configured or unreachable
**Solution**: 
- Verify `REDIS_URL` is set in Vercel environment variables
- Test Redis connection: `redis-cli -u $REDIS_URL ping`
- Check Redis service is running and accessible

### 2. "OAuth not configured"
**Cause**: Missing environment variables
**Solution**:
- Check all required env vars are set in Vercel dashboard
- Redeploy after adding environment variables
- Use `vercel env ls` to list current variables

### 3. "Redirect URI mismatch"
**Cause**: SaxoBank redirect URI doesn't match Vercel URL
**Solution**:
- Update SaxoBank app settings to use `https://your-backend.vercel.app/api/auth/callback`
- Ensure exact match (no trailing slashes, correct subdomain)

### 4. "Function timeout"
**Cause**: Cold start or slow Redis connection
**Solution**:
- Use Redis service in same region as Vercel deployment
- Consider upgrading Vercel plan for better performance
- Add retry logic for Redis connections

### 5. "CORS errors"
**Cause**: Frontend and backend on different domains
**Solution**: Already handled in your CORS configuration, but verify:
```python
origins = [
    "https://your-frontend.vercel.app",
    "https://jh-mds-frontend.vercel.app", 
]
```

## Vercel-Specific Code Adjustments

### 1. Redis Connection Handling
The current Redis implementation should work on Vercel, but you might want to add connection pooling:

```python
# In storage/redis_client.py - consider adding connection pooling
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

def get_redis() -> redis.Redis:
    url = os.environ.get("REDIS_URL")
    if not url:
        raise RuntimeError("REDIS_URL not set")
    
    # Use connection pooling for better performance on Vercel
    pool = ConnectionPool.from_url(url, encoding="utf-8", decode_responses=True)
    return redis.Redis(connection_pool=pool)
```

### 2. Environment Variable Validation
Add validation for Vercel-specific requirements:

```python
# Add to oauth.py or create vercel_config.py
def validate_vercel_config():
    required_vars = [
        "SAXO_APP_KEY",
        "SAXO_APP_SECRET", 
        "SAXO_REDIRECT_URI",
        "REDIS_URL"
    ]
    
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        raise RuntimeError(f"Missing required environment variables for Vercel: {missing}")
    
    # Validate HTTPS URLs
    redirect_uri = os.environ.get("SAXO_REDIRECT_URI", "")
    if not redirect_uri.startswith("https://"):
        raise RuntimeError("SAXO_REDIRECT_URI must use HTTPS for Vercel deployment")
```

## Debugging on Vercel

### 1. View Function Logs
```bash
vercel logs --follow
```

### 2. Check Environment Variables
```bash
vercel env ls
```

### 3. Test Redis Connection
Create a test endpoint to verify Redis connectivity:

```python
@router.get("/debug/redis-connection")
async def test_redis_connection():
    try:
        redis = get_redis()
        await redis.ping()
        await redis.close()
        return {"status": "Redis connection successful"}
    except Exception as e:
        return {"status": "Redis connection failed", "error": str(e)}
```

## Production Checklist

- [ ] External Redis service configured (Upstash/Redis Cloud)
- [ ] All environment variables set in Vercel dashboard
- [ ] SaxoBank redirect URI updated to HTTPS Vercel URL
- [ ] Backend deployed and accessible
- [ ] Frontend deployed and accessible  
- [ ] OAuth flow tested end-to-end
- [ ] Redis state storage working
- [ ] CORS configured for frontend domain
- [ ] Function logs show no errors

## Quick Commands

```bash
# Deploy backend
cd backend && vercel --prod

# Deploy frontend  
cd frontend && vercel --prod

# Check logs
vercel logs --follow

# Test OAuth
curl https://your-backend.vercel.app/api/auth/login

# Test Redis
curl https://your-backend.vercel.app/api/debug/redis-connection
```

## Support

If you're still getting "Invalid state parameter" on Vercel:

1. **Check Redis**: Verify external Redis service is working
2. **Check Environment Variables**: Ensure all vars are set in Vercel dashboard
3. **Check Logs**: Use `vercel logs` to see detailed error messages
4. **Test Endpoints**: Use the debug endpoints to isolate the issue
5. **Redeploy**: Sometimes a fresh deployment resolves configuration issues 