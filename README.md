# Autonomous Lead Enrichment Agent

A production-ready Python agent that autonomously navigates company websites using Playwright, extracts and cleans content, discovers subpages, and uses Groq (LLM) to generate structured company intelligence. SerpAPI is integrated as an optional external search tool for missing information.

## Architecture & Features
- **Browser Automation:** Headless Chromium via `playwright` handles JavaScript, redirects, and timeouts.
- **URL Discovery & Prioritization:** Heuristics automatically prioritize `/about`, `/team`, `/pricing`, etc.
- **Content Cleaning:** `BeautifulSoup` strips boilerplate (`<nav>`, `<footer>`, `<script>`, `<style>`) to minimize LLM token usage.
- **Structured Extraction:** `groq` LLM enforces strict JSON Schema (`pydantic` models) for predictable output.
- **Fallback Search:** `aiohttp` + SerpAPI conditionally search for missing leadership data and validate against LinkedIn.
- **Resilience:** Async execution with `asyncio.Semaphore` for concurrency control, timeouts, and graceful fallbacks for failed domains.

## Setup Instructions

1. **Install Dependencies:**
   Ensure you have Python 3.10+ installed.
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Configure Environment:**
   Copy `.env.example` to `.env` and fill in your API keys.
   ```bash
   cp .env.example .env
   ```
   *Note: `GROQ_API_KEY` is required. `SERPAPI_API_KEY` is optional.*

3. **Input File:**
   Create a `domains.txt` file with one domain per line.
   ```
   postman.com
   supabase.com
   vapi.ai
   ```

## Execution

Run the agent via the CLI:
```bash
python main.py domains.txt
```

### Outputs
- `output.json`: Full structured Pydantic models containing extracted intelligence, source URLs, confidence scores, and status.
- `output.csv`: Flattened tabular format for easy viewing.

## Running Tests
Unit tests cover the core URL discovery heuristics and HTML cleaning logic.
```bash
pytest tests/
```
