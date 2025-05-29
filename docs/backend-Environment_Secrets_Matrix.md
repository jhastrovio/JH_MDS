# Environment & Secrets Matrix

This matrix lists all environment variables and secrets used by JH Market Data, where they are configured (development vs. production), and their rotation policies.

| **Variable**                  | **Description**                                | **Dev Location**                     | **Prod Location**                    | **Rotation Policy**  |
| ----------------------------- | ---------------------------------------------- | ------------------------------------ | ------------------------------------ | -------------------- |
| NODE\_ENV                     | Node.js environment mode                       | `.env.local`                         | Vercel Environment Variables         | N/A (static)         |
| NEXT\_PUBLIC\_API\_BASE\_URL  | Front-end base URL for API calls               | `.env.local`                         | Vercel Preview & Production Env Vars | Review quarterly     |
| API\_BASE\_URL                | Back-end internal API base URL                 | `.env.local`                         | Vercel Environment Variables         | Review quarterly     |
| REDIS\_URL                    | Upstash Redis connection string                | Local secret manager or `.env.local` | Vercel Environment Variables         | Rotate every 30 days |
| ONE\_DRIVE\_CLIENT\_ID        | OAuth Client ID for Microsoft Graph (OneDrive) | Developer vault or `.env.local`      | Vercel Environment Variables         | Rotate annually      |
| ONE\_DRIVE\_CLIENT\_SECRET    | OAuth Client Secret for Microsoft Graph        | Developer vault                      | Vercel Environment Variables         | Rotate annually      |
| SAXO\_API\_TOKEN              | Token for Saxo Bank market data ingest         | Developer vault                      | Vercel Environment Variables         | Rotate every 90 days |
| JWT\_SECRET                   | Secret key for signing JWTs                    | `.env.local`                         | Vercel Environment Variables         | Rotate every 90 days |
| GITHUB\_OAUTH\_CLIENT\_ID     | OAuth Client ID for GitHub integration         | Developer vault                      | Vercel Environment Variables         | Rotate annually      |
| GITHUB\_OAUTH\_CLIENT\_SECRET | OAuth Client Secret for GitHub integration     | Developer vault                      | Vercel Environment Variables         | Rotate annually      |

**Notes:**

* *Dev Location*: Typically stored in each developer’s local `.env.local` file or a team-shared secret store (e.g., 1Password, AWS Secrets Manager).
* *Prod Location*: Managed securely in Vercel (or equivalent) env vars and/or Vercel Environment Variables; never committed to source.
* *Rotation Policy*: Defines cadence for credential refresh; tracked centrally in our Security SOP.

Let me know if you’d like to include additional vars, adjust locations, or update rotation schedules!
