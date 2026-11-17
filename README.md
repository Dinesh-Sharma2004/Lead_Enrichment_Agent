<div align="center">

# Autonomous Lead Enrichment Agent

**An enterprise-grade, asynchronous corporate intelligence platform powered by Next.js 14, FastAPI, Playwright web automation, BeautifulSoup DOM cleaning, Groq AI extraction, and SerpAPI enrichment.**

[![Next.js 14](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-v0.110-009688.svg)](https://fastapi.tiangolo.com/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Groq API](https://img.shields.io/badge/Groq-openai%2Fgpt--oss--120b-orange.svg)](https://groq.com/)
[![SerpAPI](https://img.shields.io/badge/SerpAPI-Search--Enrichment-purple.svg)](https://serpapi.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.6-red.svg)](https://docs.pydantic.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-v3.4-38bdf8.svg)](https://tailwindcss.com/)

</div>

---

## 📌 Overview

The **Autonomous Lead Enrichment Agent** accepts target company domains, autonomously crawls and navigates websites (via headless Chromium or high-speed HTTP fallback), discovers key subpages (`/about`, `/team`, `/pricing`, `/careers`, `/contact`), extracts cleaned content payloads, and leverages Groq LLMs to produce structured, evidence-grounded corporate intelligence.

If key information (such as executive leadership) is missing from the website, the agent conditionally triggers external Google/LinkedIn search enrichment via **SerpAPI**, validating search results before merging.

### Interfaces
- **🖥️ Next.js Web Dashboard (`frontend/`):** Modern SaaS application featuring real-time Server-Sent Events (SSE) streaming, interactive evidence inspection, dual confidence scores, and instant JSON/CSV exports.
- **⚡ FastAPI Backend (`backend/`):** High-performance ASGI microservice serving health checks, interactive Swagger documentation (`/api/docs`), and the SSE streaming enrichment engine (`/api/enrich/stream`).
- **💻 Command-Line Interface (`main.py`):** Batch CLI processing with tabular CSV and structured JSON output.

---

## 🏛️ Target Architecture & Monorepo Structure

The project is structured as a Vercel Services monorepo containing a Next.js frontend and a FastAPI backend deployed together under a single Vercel deployment URL:

```text
Lead_Enrichment_Agent/
│
├── frontend/                     # Next.js App Router (TypeScript, Tailwind, Lucide)
│   ├── app/
│   │   ├── layout.tsx            # Global layout & metadata
│   │   ├── page.tsx              # Primary SaaS dashboard interface
│   │   └── globals.css           # Tailwind base styles & custom scrollbars
│   ├── components/
│   │   ├── DomainInput.tsx       # Multi-domain input with client validation
│   │   ├── ProcessingStatus.tsx  # Live progress tracking with Cancel (AbortController)
│   │   ├── CompanyCard.tsx       # Collapsible company intelligence cards
│   │   ├── CompanyDetails.tsx    # Comprehensive breakdown of all extracted entities
│   │   ├── ConfidenceIndicator.tsx# Visual dual-engine confidence badge (LLM vs Heuristic)
│   │   ├── EvidenceLinks.tsx     # Verified source URLs & grounding indicators
│   │   └── ExportResults.tsx     # Client-side JSON & RFC 4180 CSV downloads
│   ├── lib/
│   │   ├── api.ts                # Backend health check & API utilities
│   │   ├── sse.ts                # Chunk-buffered Server-Sent Events reader
│   │   ├── csv.ts                # Client-side RFC 4180 CSV generation & download
│   │   └── types.ts              # Canonical TypeScript interfaces matching Pydantic
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.mjs
│   └── tailwind.config.js
│
├── backend/                      # Python FastAPI Microservice
│   ├── main.py                   # FastAPI app (SSE streaming, security validations, SSRF guards)
│   ├── requirements.txt          # Python dependencies
│   └── src/                      # Core agent implementation modules
│       ├── __init__.py
│       ├── agent.py              # Orchestration workflow
│       ├── browser.py            # Playwright browser manager & aiohttp HTTP fallback
│       ├── config.py             # Environment configuration & runtime thresholds
│       ├── discovery.py          # Heuristic link scoring & subpage discovery
│       ├── extraction.py         # BeautifulSoup HTML cleaning & DOM stripping
│       ├── llm.py                # Groq LLM extraction & schema validation
│       ├── logger.py             # Structured logging setup
│       ├── schemas.py            # Pydantic models (CompanyIntelligence)
│       └── search.py             # SerpAPI leadership fallback search
│
├── tests/                        # Comprehensive Pytest test suite (26 passing tests)
│   ├── conftest.py               # Shared test fixtures & sys.path configuration
│   ├── test_api.py               # Backend endpoint, validation, SSRF, & SSE tests
│   ├── test_discovery.py         # URL discovery heuristics tests
│   ├── test_extraction.py        # HTML boilerplate cleaning tests
│   └── test_llm.py               # LLM schema & confidence score tests
│
├── docs/                         # Detailed architecture and tuning guides
├── main.py                       # Root CLI backward-compatibility entry point
├── requirements.txt              # Root testing and CLI dependencies
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore rules (node_modules, .next, .env)
├── .vercelignore                 # Deployment bundle exclusion rules
└── vercel.json                   # Vercel Services configuration
```

---

## 🌐 API Endpoints

The backend registers its endpoints with the `/api` prefix, seamlessly routed by Vercel Services:

| Method | Endpoint | Responsibility |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Returns backend availability, version, and environment configuration flags (no secrets leaked). |
| `GET` | `/api/docs` | Interactive Swagger UI documentation. |
| `GET` | `/api/openapi.json` | OpenAPI schema definition. |
| `POST` | `/api/enrich/stream` | Validates domains, executes enrichment pipeline, and streams results via Server-Sent Events (SSE). |

### Request Format (`POST /api/enrich/stream`)
```json
{
  "domains": ["stripe.com", "linear.app"]
}
```

### Server-Sent Events (SSE) Protocol
- `event: started` — Initial payload with total domains to process.
- `event: domain_started` — Notification that crawler and extraction have begun for a domain.
- `event: domain_completed` — Emitted immediately when a domain finishes with the complete `CompanyIntelligence` object.
- `event: domain_failed` — Emitted if a domain encounters an error, including a safe error message and fallback data.
- `event: completed` — Final summary event containing total, success, and failure counts.

---

## 🚀 Local Development

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ (tested on v26)
- npm 9+

### 2. Environment Setup
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your API credentials:
```env
GROQ_API_KEY=your_groq_api_key_here
SERPAPI_API_KEY=your_serpapi_api_key_here
ENABLE_SERPAPI=True
```

### 3. Install Dependencies
```bash
# Backend / root dependencies
pip install -r requirements.txt

# (Optional) Install Playwright Chromium for local full-browser rendering
playwright install chromium

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 4. Running Locally

#### Option A: Running with Vercel CLI (Recommended)
From the repository root:
```bash
vercel dev
```
Both the Next.js frontend and FastAPI backend will start concurrently under one local port (default: `http://localhost:3000`).

#### Option B: Running Services Individually
Terminal 1 (Backend):
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```
Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```
Visit `http://localhost:3000` in your browser. (The Next.js dev server automatically proxies `/api/*` to `http://127.0.0.1:8000/api/*`).

#### Option C: Command Line Interface (CLI)
```bash
python main.py domains.txt
```
Generates `output.json` and `output.csv`.

---

## ☁️ Vercel Deployment Guide

Deploying to Vercel requires zero complex setup thanks to Vercel Services.

### 1. `vercel.json` Configuration
The root `vercel.json` is configured using the official Vercel Services syntax:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "services": {
    "frontend": {
      "root": "frontend/",
      "framework": "nextjs"
    },
    "backend": {
      "root": "backend/",
      "framework": "fastapi",
      "entrypoint": "main:app"
    }
  },
  "rewrites": [
    {
      "source": "/api",
      "destination": { "service": "backend" }
    },
    {
      "source": "/api/(.*)",
      "destination": { "service": "backend" }
    },
    {
      "source": "/(.*)",
      "destination": { "service": "frontend" }
    }
  ]
}
```

### 2. Deployment Steps
1. Push your repository to GitHub.
2. Go to [vercel.com](https://vercel.com/new) and import your repository.
3. In Project Settings, add the following Environment Variables:
   - `GROQ_API_KEY` (Required): Your Groq API key.
   - `SERPAPI_API_KEY` (Optional): Your SerpAPI key.
   - `ENABLE_SERPAPI`: `True` (or `False`).
   - `MAX_DOMAINS_PER_REQUEST`: `3`
   - `BATCH_TIMEOUT_SECONDS`: `55`
4. Click **Deploy**.

---

## 🛡️ Playwright vs. HTTP Scraper Fallback

- **Local Development:** When Playwright Chromium binaries are installed (`playwright install chromium`), `BrowserManager` launches headless Chromium, enabling full client-side JavaScript execution, dynamic hydration waiting, and simulated user scrolling.
- **Vercel Serverless Environment:** Serverless environments cannot package large 300MB+ Chromium binaries or Linux C libraries (`libnss3`, `libasound2`). `BrowserManager` automatically detects the serverless context and gracefully falls back to `aiohttp` HTTP scraping with custom browser user-agents, redirect following, and connection pooling.
- **Transparency on Limitations:** Heavily obfuscated Single Page Applications (SPAs) that require client-side JavaScript execution to render basic text will yield less content under the HTTP fallback scraper. For 100% JavaScript-rendered web applications, deploy with full Playwright on a Docker/VPS server or utilize a headless browser service.

---

## 🔒 Security & Reliability

- **SSRF & Private IP Protection:** The backend strictly rejects `localhost`, loopback addresses (`127.0.0.1`, `::1`), private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local IPs (`169.254.0.0/16`), and cloud metadata services (`metadata.google.internal`).
- **Domain Whitelisting & FQDN Validation:** Rejects arbitrary schemas, port injection, and invalid domain structures.
- **Batch Execution Budget:** Enforces a bounded execution timeout per request (`BATCH_TIMEOUT_SECONDS = 55`) with safety buffers to prevent hanging functions.
- **Client Disconnection Handling:** The SSE streaming generator inspects `request.is_disconnected()` between domain steps, terminating pending tasks and releasing browser/network resources if the user leaves or clicks Cancel.
- **API Key Secrecy:** Neither `GROQ_API_KEY` nor `SERPAPI_API_KEY` are ever exposed to the client, logged, or returned via health checks.

---

## 🧪 Running Automated Tests

```bash
# Run backend test suite (26 unit & integration tests)
pytest tests/

# Run frontend production build & TypeScript validation
cd frontend
npm run build
```

---

## 📜 License

Distributed under the MIT License.
