# Core FX, Rates & Equity Indices Market Data Viewer – Scope & Requirements

## 1 – Objective

Design and build a lightweight web application that lets traders view, analyse and act on live FX, fixed‑income (sovereign rates & selected futures) and major equity‑index prices in a single, responsive dashboard, leveraging existing Saxo Bank credentials plus free/low‑cost market‑data APIs.

## 2 – Target Users & Use‑Cases

| Persona            | Use‑Case                                                    |
| ------------------ | ----------------------------------------------------------- |
| Proprietary trader | Glanceable real‑time prices & charting during trading hours |
| Portfolio manager  | Cross‑asset correlation checks before allocation shifts     |

## 3 – Data Sources

| Asset class                          | Primary feed                                                   | Fallback/Aux feed            | Notes                                  |
| ------------------------------------ | -------------------------------------------------------------- | ---------------------------- | -------------------------------------- |
| FX spot & forwards                   | **Saxo Bank OpenAPI** (streaming)                              | Yahoo Finance REST (polling) | Requires OAuth; throttle ~200 req/min |
| Government bond yields & futures     | Investing.com unofficial API (HTML scrape or RapidAPI wrapper) | Treasury.gov CSV (US)        | Latency tolerant (refresh 1–5 min)     |
| Equity indices (SPX, NDX, DAX, STI…) | Yahoo Finance streaming websocket (public)                     | Saxo Bank where available    | Free tier supports 2s updates          |

> **Caching strategy**: Redis in‑memory cache (15–30 s TTL) to smooth rate limits.

## 4 – Functional Requirements

### 4.1 Market Coverage (MVP)

* **FX Majors & EM CCYs**: Up to 30 pairs (e.g., EUR‑USD, USD‑JPY, GBP‑USD, AUD‑USD, USD‑CHF, USD‑CAD, NZD‑USD)
* **Rates**: UST 2y, 10y, 30y; Bund 10y; Gilt 10y; JGB 10y; AUD 3y & 10y; SGD & INR benchmarks
* **Equity Indices**: S&P 500, Nasdaq 100, Nikkei 225, EuroStoxx 50, DAX 30, FTSE 100, Hang Seng, STI

### 4.2 Dashboards & Views

1. **Watchlist** – live tick table with colour‑coded change & sparkline
2. **Daily Movers** – ranked FX & index %‑move heat‑map
3. **AI‑generated Dashboard Scaffolds** – use [v0.dev](https://v0.dev) (Vercel's AI UI generator) to quickly prototype and iterate Tailwind/React dashboard components, ensuring consistent design tokens across views.

### 4.4 Export / Integrations

* CSV snapshot download
* Webhook or email on alert fire

## 5 – Non‑Functional Requirements

| Category     | Target                                             |
| ------------ | -------------------------------------------------- |
| Latency (FX) | <5  second tick‑to‑screen                          |
| Availability | 99.5 % monthly                                     |
| Security     | OAuth2 for Saxo, encrypted secrets in Vercel KV    |
| Compliance   | Read‑only market‑data usage; abide by vendor terms |

## 6 – Technical Architecture

```
+-------------------------------+        +-------------------+        +---------------------+
|    Front‑end (Next.js 14)     | <---> |  API Gateway (Py) | <---> |  Data Ingest Layer  |
| Tailwind UI via v0.dev        |        |  FastAPI @/api    |        |  Saxo / YF / Inv    |
| Vercel Frontend Project       |        |  Vercel Backend   |        |  Serverless         |
+-------------------------------+        |  Project          |        +---------------------+
          |                                   |                            |
          |  Vercel Edge Functions            |  Serverless (Vercel)       |
          +-----------------------------------+----------------------------+
                                   |
                           +-------------------+
                           |  Redis (Upstash)  |
                           +-------------------+
```

* **Language**: Python 3.12
* **Frameworks & UI**: 
  * Backend: FastAPI (Python 3.12)
  * Frontend: Next.js 14 + Tailwind CSS
  * **v0.dev** to auto‑generate and refactor React/Tailwind components for dashboards
* **Deployment**: 
  * Separate Vercel projects for frontend and backend
  * Frontend: Next.js app router with Edge functions
  * Backend: FastAPI serverless functions
  * GitHub Actions CI/CD for both projects
* **Cache**: Upstash Redis (15–30 s TTL) for near‑real‑time ticks
* **Persistent Storage**: OneDrive / SharePoint (via Microsoft Graph API) – store CSV/Parquet snapshots and user preferences; no dedicated server‑side DB to keep footprint light
* **Monitoring**: Vercel Analytics, Sentry

## 8 – Deployment & DevOps

* **Environments**: 
  * Frontend: `dev`, `prod` Vercel projects (both can leverage v0.dev preview URLs)
  * Backend: Separate `dev`, `prod` Vercel projects
* **Secrets**: 
  * Vercel encrypted environment variables; rotate quarterly
  * Frontend: `NEXT_PUBLIC_API_BASE_URL` for backend connection
* **Testing**: 
  * Backend: PyTest + Requests for API testing
  * Frontend: Next.js testing utilities
  * PR previews for both projects
* **Observability**: Simple Redis‑heartbeat email alert via SendGrid (optional)

  * Full observability stack moved to Future Enhancements

## 10 – Success Metrics

* <500 ms median tick‑to‑chart latency for FX
* ≤1 s page first contentful paint (desktop)
* ≤0.1 % alert false positives per month
* 0 post‑launch Sev‑1 incidents in first 30 days

## 11 – Future Enhancements

* Options & volatility surface viewer
* Trade blotter + execution via Saxo OpenAPI
* Mobile‑optimised PWA
* Full observability stack: Logtail, Grafana Cloud dashboards, Slack/Grafana OnCall alerts
* News & macro calendar
* AI‑generated market commentary email at EOD
* **OpenAI / GenAI roadmap**:

  * Natural‑language "Chat‑with‑the‑market" query interface (GPT‑4o)
  * Headline/news summariser widget
  * Alert explanation generator (why did an alert fire?)

---

**Last updated:** 22 May 2025
