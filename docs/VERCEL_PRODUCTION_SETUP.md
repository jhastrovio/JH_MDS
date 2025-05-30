# JH Market Data Service - Vercel Production Configuration & Deployment Guide

## Introduction: Vercel Deployment Considerations

Deploying to Vercel introduces specific considerations compared to local development, especially for applications with backend services, OAuth, and external dependencies like Redis.

### Key Differences from Local Development:

1.  **Serverless Environment**: Each API request might be handled by a new serverless function instance. This impacts how state is managed.
2.  **No Local Redis**: Vercel serverless functions cannot directly access a local Redis instance. An external, cloud-hosted Redis service (e.g., Upstash, Redis Cloud) is **required**, particularly for OAuth state persistence.
3.  **HTTPS Required**: All callback URLs and public-facing endpoints must use `https://`.
4.  **Environment Variables**: Configuration is managed through the Vercel project dashboard, not local `.env` files.
5.  **Cold Starts**: The first request to a serverless function after a period of inactivity might experience a "cold start," leading to slightly higher latency for that initial request.

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

### 2. Upstash Redis Configuration (Required for OAuth & Caching)

An external Redis provider is essential for Vercel deployments, primarily for:
*   **OAuth State Persistence**: Securely storing the `state` parameter during the OAuth flow.
*   **Caching**: Caching market data, tokens, or other frequently accessed information.

**Upstash is recommended due to its generous free tier and ease of integration.**

✅ **You likely already have this set up!** If not:

1.  Go to [Upstash Console](https://console.upstash.com/)
2.  Sign up or log in.
3.  Create a new Global Redis database.
4.  Copy the **Primary Connection URL (starts with `rediss://`)**. This is your `REDIS_URL`.
5.  Add this `REDIS_URL` to your Vercel project's **Production** environment variables.

**Other Redis Provider Options:**
*   **Redis Cloud**: [redis.com](https://redis.com)
*   **Railway.app Redis**: [railway.app](https://railway.app)

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

## 🚀 Deployment Process & Checklist

This section combines deployment steps with a checklist to ensure all configurations are correctly applied.

### Pre-Deployment Checklist & Configuration:

1.  **[ ] External Redis Setup (Upstash Recommended):**
    *   Ensure your Upstash (or other cloud Redis) instance is active.
    *   Verify you have the correct `REDIS_URL` (e.g., `rediss://...`).

2.  **[ ] Vercel Environment Variables (Backend Project):
    *   Navigate to your Vercel **backend** project dashboard → Settings → Environment Variables.
    *   Add/Verify the following for the **Production** environment:
        *   `SAXO_APP_KEY`: Your SaxoBank application key.
        *   `SAXO_APP_SECRET`: Your SaxoBank application secret.
        *   `SAXO_REDIRECT_URI`: `https://your-backend-deployment-url.vercel.app/api/auth/callback` (Replace `your-backend-deployment-url.vercel.app` with your actual Vercel backend URL).
        *   `REDIS_URL`: Your Upstash Redis connection string.
        *   `JWT_SECRET`: A securely generated random string (32+ characters).
        *   `NODE_ENV`: `production`.
        *   `LOG_LEVEL` (Optional): `INFO` or `DEBUG`.
        *   `LOG_FORMAT` (Optional): `json` for structured logging.

3.  **[ ] Vercel Environment Variables (Frontend Project):
    *   Navigate to your Vercel **frontend** project dashboard → Settings → Environment Variables.
    *   Add/Verify for the **Production** environment:
        *   `NEXT_PUBLIC_API_BASE_URL`: `https://your-backend-deployment-url.vercel.app` (This must point to your deployed backend).

4.  **[ ] SaxoBank Developer Portal Configuration:
    *   Log in to the [SaxoBank Developer Portal](https://www.developer.saxo/).
    *   Navigate to your application settings.
    *   Ensure the **Redirect URI** list includes your production backend callback: `https://your-backend-deployment-url.vercel.app/api/auth/callback`.
    *   **Important**: The URI must be an exact match, including `https://`.
    *   It's also good practice to keep your development callback URI (e.g., `http://localhost:8000/api/auth/callback`) in the list if you still test locally.

### Deployment Steps:

1.  **[ ] Deploy Backend to Vercel:**
    *   Ensure your `vercel.json` in the `backend` directory is correctly configured.
    *   From your project root (or backend directory):
        ```powershell
        # If in project root:
        cd backend
        vercel --prod
        cd ..
        # Or, if already in backend directory:
        # vercel --prod
        ```
    *   Note the deployment URL provided by Vercel (e.g., `your-backend-deployment-url.vercel.app`). **Ensure this matches the URLs used in environment variables and the SaxoBank portal.**

2.  **[ ] Deploy Frontend to Vercel:**
    *   Ensure your `NEXT_PUBLIC_API_BASE_URL` in the frontend's Vercel environment variables points to the *correctly deployed backend URL*.
    *   From your project root (or frontend directory):
        ```powershell
        # If in project root:
        cd frontend
        vercel --prod
        cd ..
        # Or, if already in frontend directory:
        # vercel --prod
        ```

### Post-Deployment Testing & Validation:

1.  **[ ] Test Backend Health & Configuration Endpoints:**
    *   Replace `your-backend-deployment-url.vercel.app` with your actual backend URL.
    *   **Redis Connection & OAuth State Storage:**
        ```powershell
        curl https://your-backend-deployment-url.vercel.app/api/debug/redis-connection 
        # Expected: {"status":"success","redis_ping":"ok","oauth_state_storage":"ok",...}
        ```
    *   **OAuth Configuration & Environment Variables:**
        ```powershell
        curl https://your-backend-deployment-url.vercel.app/api/auth/debug 
        # Expected: {"status":"ok","oauth_available":true,"environment_vars":{"SAXO_APP_KEY":"SET", ...}}
        ```
    *   **General Health & Readiness (as defined in your `VERCEL_PRODUCTION_SETUP.md`):
        ```powershell
        curl https://your-backend-deployment-url.vercel.app/api/auth/health/simple
        curl https://your-backend-deployment-url.vercel.app/api/auth/deployment/readiness
        # Add other relevant health/diagnostic endpoints from your main setup guide.
        ```

2.  **[ ] Test Full OAuth Flow via Frontend:**
    *   Open your deployed frontend application in a browser.
    *   Initiate the login process, which should redirect to SaxoBank.
    *   Complete the SaxoBank authentication.
    *   Verify successful redirection back to your frontend and that you are logged in.

3.  **[ ] Test Market Data Endpoints (via Frontend or `curl`):
    *   Ensure that authenticated requests to fetch market data are working.

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

## ✅ Final Production Readiness Confirmation

- [ ] Upstash Redis configured and `REDIS_URL` set and verified via endpoint.
- [ ] SaxoBank OAuth credentials configured in Vercel and verified via endpoint.
- [ ] Production redirect URI correctly set in SaxoBank portal and matches deployed backend URL.
- [ ] JWT secret generated and configured in Vercel.
- [ ] All required environment variables set in Vercel dashboard for both frontend and backend.
- [ ] Backend deployed successfully to its final production URL.
- [ ] Frontend deployed successfully, pointing to the correct production backend URL.
- [ ] All specified health and diagnostic checks returning healthy/ready status.
- [ ] Full OAuth login flow successfully tested end-to-end via the deployed frontend.
- [ ] Live market data endpoints responding correctly with data after authentication.
- [ ] Production monitoring (basic Vercel logs, uptime checks) in place.

Your JH Market Data Service is now ready for production! 🎉
