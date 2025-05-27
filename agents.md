# Coding Agent Guidelines – *agents.md*

> **Audience**: Large‑language‑model coding agents (e.g. GPT‑4o‑code, OSS agents) invoked to scaffold or refactor the *Core FX, Rates & Equity Indices Market Data Viewer* project.

---

## 1. Canonical Sources

1. **`project_scope.md`** – functional & non‑functional requirements.
2. **System Architecture Diagram** (when available) – component boundaries.
3. **OpenAPI spec** (`backend/api/openapi.yaml`) – must stay authoritative.
4. **Type definitions** (`backend/market_data/models.py`, `frontend/types/*.ts`).

The agent MUST read/parse these before generating or editing code.

---

## 2. High‑Level Principles

| Principle                | Guidance                                                                                                   |
| ------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **Dual Vercel Deploy**   | Separate deployments for backend (FastAPI) and frontend (Next.js) on Vercel.                               |
| **Serverless‑first**     | Code must run on Vercel (Edge or Serverless). No long‑running processes.                                   |
| **Minimum viable infra** | Only Upstash Redis (cache) & OneDrive/SharePoint via Microsoft Graph (persistent snapshots). No other DBs. |
| **Stateless functions**  | Persist nothing locally; rely on Redis TTL ≤ 30 s for hot data.                                            |
| **Security by default**  | Fetch secrets from environment; never hard‑code. Use HTTPS/TLS everywhere.                                 |
| **Observability light**  | Emit `print()`/`console.log` for Vercel log tail; integrate Sentry SDK.                                    |
| **Idempotent deploys**   | Code must be re‑deployable with zero manual steps.                                                         |
| **Typed everywhere**     | Python 3.12 with `typing` + Pydantic v2; TypeScript strict mode in Next.js.                                |

---

## 3. Technology Stack

| Layer           | Tech                                                          | Key Conventions                                                             |
| --------------- | ------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Backend         | **FastAPI** (Python 3.12) in `/backend`                       | Located in `/backend/api`; "size‑optimised" router pattern to fit Vercel.   |
| Frontend        | **Next.js 14** (app router) in `/frontend`                    | React Server Components; fetches via `NEXT_PUBLIC_API_BASE_URL`.            |
| Realtime ingest | Async task in `backend/ingest/saxo_ws.py`                     | Uses `websockets` lib; writes to Redis via `redis.asyncio`.                 |
| Cache           | **Upstash Redis**                                             | Keys: `fx:<SYM>`, `rate:<SYM>`, `idx:<SYM>`; TTL 30 s.                      |
| Persistence     | Microsoft Graph API                                           | Wrapper in `backend/storage/on_drive.py`; saves Parquet snapshots.          |
| Styling         | Tailwind & v0.dev components                                  | Used in frontend components.                                                |
| E2E Testing     | **Requests + pytest**                                         | At least one smoke test per deployed preview.                               |

---

## 4. Output & Diff Format

The agent must reply with **Git‑style unified diffs** or complete new file contents inside fenced code blocks:

```diff
--- a/backend/api/price.py
+++ b/backend/api/price.py
@@
 def get_price(sym: str):
     ...
```

No prose outside code fences except a one‑sentence summary.

---

## 5. Mandatory Checks Before Committing

1. `pytest backend/tests/` – All unit tests pass.
2. `pytest backend/tests/api/` - API tests pass with expected responses.
3. `black --check backend/ && ruff backend/` – format & lint.
4. Bundle size of front‑end route `< 250 kB` uncompressed.

If any check fails, the agent must fix and resubmit.

---

## 6. Patterns & Anti‑patterns

* **Prefer [async def]** for IO‑bound Saxo/Yahoo calls.
* **No global mutable state**; use dependency‑injected Redis client.
* **Avoid blocking loops** in edge functions; schedule background tasks via CRON on Vercel if needed.
* **Never expose API keys** in logs or responses.
* **Keep deployments separate** - backend and frontend should be independently deployable.

---

## 7. Future‑Facing Hooks (Do Not Implement Yet)

* Placeholder `chat/` module for OpenAI NLQ—leave function stubs but no calls.
* Observability exporters (Logtail, Grafana) behind `FEATURE_OBS=false` flag.
* Volatility surface endpoints (`/api/volsurface`) under Vercel `EDGE_CONFIG` toggle.

---

## 8. Review & Merge Process

1. Agent opens PR targeting `dev` branch.
2. PR title follows Conventional‑Commits (`feat:`, `fix:`).
3. Auto‑label `needs‑human‑review`.
4. Human merge or request further agent iterations.

## Saxobank API Docs
https://www.developer.saxo/openapi/learn

---

**End of *agents.md***
