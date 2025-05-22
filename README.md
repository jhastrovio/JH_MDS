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
