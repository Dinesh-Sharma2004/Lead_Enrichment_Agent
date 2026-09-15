# System Architecture & Workflow

The Autonomous Lead Enrichment Agent utilizes a hybrid asynchronous pipeline combining Streamlit Web UI, CLI execution, headless Chromium browser automation, heuristic link discovery, DOM cleaning, Groq LLM extraction, and conditional SerpAPI fallback search.

## Hybrid Pipeline Diagram

```mermaid
flowchart TD
    UI[Streamlit Web UI app.py] -->|Enter domains or use domains.txt| B[Async Domain Processing Loop]
    CLI[main.py domains.txt] -->|File Input| B
    
    B --> C[Playwright Headless Browser]
    C -->|Navigate Homepage| D[Discover & Score Links]
    D -->|Prioritize /about, /team, /pricing, /careers| E[Crawl Subpages concurrently]
    E --> F[BeautifulSoup DOM Cleaning]
    F -->|Strip scripts, styles, nav, boilerplate| G[Cleaned Content Payload]
    G --> H[Groq LLM Extraction]
    H --> I[JSON Pre-normalization & Pydantic Validation]
    I --> J{Leadership Present?}
    J -- Yes --> L[Final Data Structure]
    J -- No & SerpAPI Enabled --> K[SerpAPI LinkedIn Fallback Search]
    K -->|Validate & Deduplicate| L
    L --> M[Streamlit UI Display & Export output.json / output.csv]
```

## Modular System Components

### 1. Streamlit Web UI (`app.py`)
- Provides an interactive web interface for batch domain input.
- Automatically falls back to reading `domains.txt` if input is left empty.
- Displays metrics, data tables, expandable JSON cards, and offers instant JSON/CSV downloads.

### 2. Command Line Interface (`main.py`)
- CLI entrypoint for batch processing (`python main.py domains.txt`).
- Exports results to `output.json` and `output.csv`.

### 3. Browser Manager (`src/browser.py`)
- Launches headless Chromium contexts asynchronously using Playwright.
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
