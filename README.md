# JH_MDS

A market-data service for live prices, historical ticks, and snapshots, built with Next.js, Vercel Edge Functions, FastAPI, Redis, and OneDrive storage.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Running Locally](#running-locally)
- [API Usage](#api-usage)
- [License](#license)

## Features

- Live price fetch (`/api/price?symbol=…`)
- Historical tick streaming/polling (`/api/ticks`)
- Snapshot triggering (`/api/snapshot`)
- SSR/ISR front-end powered by Next.js

## Prerequisites

- Node.js ≥16
- Python ≥3.11
- Redis (Upstash) account
- OneDrive (Microsoft Graph) app registration
- GitHub repo access

```

## Getting Started

1. Clone this repository.
2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Install Node.js packages for the front-end:

   ```bash
   npm install
   ```

## Running Tests

Run unit tests from the repository root:

```bash
cd JH_MDS
pytest
```

If you need to run tests from another directory, set the Python path manually:

```bash
export PYTHONPATH=/path/to/JH_MDS
pytest
```
