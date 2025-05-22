# System Architecture Overview

Below is a one-page diagram of our end-to-end architecture, annotated with an in-lined legend for clarity.

```mermaid
%% Legend
%% A: Browser — Next.js front-end (React + Tailwind via v0.dev; SSR/ISR & client fetches to `/api/*`)
%% B: Vercel Edge Functions — Edge-deployed serverless layer serving both page rendering and proxying API calls
%% C: API Gateway — FastAPI routes under `/api`; handles auth, validation, cache & storage orchestration
%% D: Data Ingest Layer — Saxo WS (~2 s tick), Yahoo streaming, Investing.com polling (1–5 min)
%% E: Redis (Upstash) — In-memory cache for live ticks (TTL 15–30 s)
%% F: OneDrive / SharePoint — Persistent CSV/Parquet snapshots via Microsoft Graph

flowchart LR
    subgraph Client
      A[Browser<br/>(Next.js 14 + v0.dev)]
    end

    subgraph Edge
      B[Vercel Edge<br/>Functions]
    end

    subgraph API
      C[API Gateway<br/>(FastAPI @ `/api`)]
    end

    subgraph Ingest
      D[Data Ingest Layer<br/>(Saxo WS / Yahoo / Investing.com)]
    end

    subgraph Cache
      E[Redis (Upstash)<br/>TTL 15–30 s]
    end

    subgraph Storage
      F[OneDrive / SharePoint<br/>(Graph API)]
    end

    A -->|1. SSR/ISR & fetch `/api/*`| B
    B -->|2. Serverless Fn call| C
    C -->|3. Read/write ticks| E
    C -->|4. Write snapshots| F
    D -->|5. Stream & poll data<br/>(2 s–5 min)| E
    E -->|6. Cache hits| C
    C -->|7. JSON response| B
    B -->|8. Hydrate/UI bundle| A
```
