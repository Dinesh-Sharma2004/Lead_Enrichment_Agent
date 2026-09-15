# System Architecture & Workflow

The Autonomous Lead Enrichment Agent utilizes a hybrid asynchronous pipeline combining Streamlit Web UI, FastAPI REST endpoints, headless Chromium browser automation (with aiohttp HTTP fallback), heuristic link discovery, DOM cleaning, Groq LLM extraction, and conditional SerpAPI fallback search.

## Hybrid Pipeline Diagram

```mermaid
flowchart TD
    UI[Streamlit Web UI app.py] -->|Enter domains or use domains.txt| B[Async Domain Processing Loop]
    API[FastAPI POST /enrich] -->|JSON Request| B
    CLI[main.py domains.txt] -->|File Input| B
    
    B --> C{Playwright Installed?}
    C -- Yes --> D1[Playwright Headless Browser]
    C -- No / Serverless --> D2[aiohttp HTTP Fallback Scraper]
    
    D1 --> E[Discover & Score Links]
    D2 --> E
    
    E -->|Prioritize /about, /team, /pricing, /careers| F[Crawl Subpages concurrently]
    F --> G[BeautifulSoup DOM Cleaning]
    G -->|Strip scripts, styles, nav, boilerplate| H[Cleaned Content Payload]
    H --> I[Groq LLM Extraction]
    I --> J[JSON Pre-normalization & Pydantic Validation]
    J --> K{Leadership Present?}
    K -- Yes --> M[Final Data Structure]
    K -- No & SerpAPI Enabled --> L[SerpAPI LinkedIn Fallback Search]
    L -->|Validate & Deduplicate| M
    M --> N[Streamlit UI Display & Export output.json / output.csv]
```

## Modular System Components

### 1. Streamlit Web UI (`app.py`)
- Provides an interactive web interface for batch domain input.
- Automatically falls back to reading `domains.txt` if input is left empty.
- Displays metrics, data tables, expandable JSON cards, and offers instant JSON/CSV downloads.

### 2. FastAPI API & CLI (`main.py`)
- Exports a top-level `app` object for Vercel serverless deployment (`GET /`, `GET /health`, `POST /enrich`).
- Maintains CLI execution capability (`python main.py domains.txt`).

### 3. Browser Manager & Scraper (`src/browser.py`)
- Launches headless Chromium contexts asynchronously using Playwright.
- Includes an **automatic `aiohttp` HTTP fallback scraper** when Chromium binaries are unavailable (e.g., in Vercel serverless environments).
- Manages dynamic page load timeouts (30s default) and page scrolling for lazy-loaded DOM elements.
- Enforces max browser concurrency via `asyncio.Semaphore`.

### 4. URL Discovery Heuristics (`src/discovery.py`)
- Extracts all internal links from the homepage.
- Ranks links using keyword heuristics (`/about`, `/team`, `/company`, `/pricing`, `/contact`, `/careers`).
- Selects top prioritized URLs up to `MAX_PAGES_PER_DOMAIN`.

### 5. HTML Extraction & DOM Cleaning (`src/extraction.py`)
- Parses HTML using `BeautifulSoup`.
- Strips noise elements (`<script>`, `<style>`, `<svg>`, `<nav>`, `<footer>`, `<header>`, `<aside>`, `<iframe>`).
- Extracts deduplicated clean text, drastically reducing token overhead.

### 6. Groq LLM Integration & Schema Pre-normalization (`src/llm.py`)
- Calls Groq API (`openai/gpt-oss-120b`).
- Passes clean text alongside an explicit JSON Schema system prompt.
- Employs `normalize_llm_json()` to handle lowercasing keys, unwrapping nested objects, and computing data confidence scores (0.0 to 1.0).

### 7. SerpAPI Enrichment (`src/search.py`)
- Triggers fallback search when leadership data is missing from website pages.
- Validates target company identity before searching to avoid generic search queries.
- Merges external LinkedIn leadership data into the canonical output.
