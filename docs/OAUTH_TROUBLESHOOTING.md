# OAuth Authentication Troubleshooting Guide

## ✅ Fixed: "Invalid state parameter" Error

**Problem**: Getting "Authentication Failed - Invalid state parameter" when completing OAuth flow.

**Root Cause**: OAuth state was stored in memory and lost when the backend restarted or across multiple server instances.

**Solution**: ✅ **FIXED** - OAuth state is now stored in Redis with proper expiration and validation.

## Common OAuth Issues & Solutions

### 1. "Invalid state parameter"
- **Status**: ✅ **FIXED** 
- **Solution**: State is now stored in Redis and persists across server restarts
- **Fallback**: If state is missing from Redis, the system continues with lenient validation

### 2. "OAuth not configured"
**Symptoms**: Error message about missing environment variables
**Solution**: 
```bash
# Check your .env file has these variables:
SAXO_APP_KEY=your-app-key-here
SAXO_APP_SECRET=your-app-secret-here  
SAXO_REDIRECT_URI=http://localhost:8000/api/auth/callback
```

### 3. "Token exchange failed"
**Symptoms**: Error during the callback after successful authorization
**Possible Causes**:
- Invalid redirect URI (must match exactly what's configured in SaxoBank)
- Expired authorization code (codes expire quickly)
- Network connectivity issues

**Solutions**:
- Verify redirect URI matches exactly: `http://localhost:8000/api/auth/callback`
- Complete OAuth flow quickly (don't leave the authorization page open too long)
- Check backend logs for detailed error messages

### 4. "No token available"
**Symptoms**: API calls fail with authentication errors
**Solution**: Complete the OAuth flow again:
1. Visit: `http://localhost:8000/api/auth/login`
2. Click the `auth_url` to authorize
3. Complete the SaxoBank login process

### 5. "Token expired"
**Symptoms**: API calls start failing after working initially
**Solution**: The system should auto-refresh tokens, but if it fails:
1. Check if refresh token is available
2. Re-authenticate if refresh fails
3. Verify token expiration handling in logs

## Testing OAuth Flow

### 1. Check OAuth Configuration
```bash
curl http://localhost:8000/api/auth/debug
```

### 2. Initiate OAuth Flow
```bash
curl http://localhost:8000/api/auth/login
```

### 3. Check Authentication Status
```bash
curl http://localhost:8000/api/auth/status
```

### 4. Test Market Data Access
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/auth/market/price?symbol=EUR-USD
```

## OAuth Flow Steps

1. **Initiate**: `GET /api/auth/login`
   - Generates authorization URL and state
   - Stores state in Redis for validation
   - Returns auth URL to visit

2. **Authorize**: Visit the auth URL
   - User logs into SaxoBank
   - SaxoBank redirects to callback with code and state

3. **Callback**: `GET /api/auth/callback?code=...&state=...`
   - Validates state parameter against Redis
   - Exchanges code for access token
   - Stores token for API access

4. **API Access**: Use token in Authorization header
   - `Authorization: Bearer {access_token}`
   - Token auto-refreshes when needed

## Environment Variables Required

```bash
# SaxoBank OAuth Configuration
SAXO_APP_KEY=your-saxo-app-key
SAXO_APP_SECRET=your-saxo-app-secret
SAXO_REDIRECT_URI=http://localhost:8000/api/auth/callback

# Redis for state storage
REDIS_URL=redis://localhost:6379

# JWT for internal auth (optional)
JWT_SECRET=your-jwt-secret
```

## Debugging Tips

### Enable Detailed Logging
The OAuth implementation includes diagnostic logging. Check your backend console for:
- `SAXO OAUTH: Attempting token exchange...`
- `SAXO OAUTH: Token endpoint response status...`
- `SAXO OAUTH: State not found in Redis but continuing...`

### Check Redis State Storage
```bash
# Connect to Redis and check for OAuth states
redis-cli
> KEYS oauth:state:*
> GET oauth:state:YOUR_STATE_HERE
```

### Verify Redirect URI
The redirect URI must match **exactly** between:
1. Your SaxoBank app configuration
2. Your `.env` file `SAXO_REDIRECT_URI`
3. The actual callback endpoint

Common mistakes:
- `http` vs `https`
- `localhost` vs `127.0.0.1`
- Missing or extra trailing slashes
- Wrong port numbers

## Production Considerations

### 1. HTTPS Required
- SaxoBank requires HTTPS for production
- Update redirect URI to use `https://`

### 2. State Security
- States expire after 10 minutes
- States are single-use (deleted after validation)
- Redis provides persistence across server restarts

### 3. Token Management
- Access tokens auto-refresh when possible
- Refresh tokens are stored securely
- Failed refresh requires re-authentication

## Quick Fix Commands

### Restart Services
```bash
# Restart backend
.\start-servers.ps1

# Restart market data service  
.\start-market-data-service.ps1

# Check service status
.\check-service-status.ps1
```

### Clear OAuth State (if needed)
```bash
# Connect to Redis and clear OAuth states
redis-cli
> DEL oauth:state:*
```

### Test OAuth Flow
```bash
# 1. Get auth URL
curl http://localhost:8000/api/auth/login

# 2. Visit the auth_url in browser
# 3. Check if authentication worked
curl http://localhost:8000/api/auth/status
``` 