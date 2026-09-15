# Troubleshooting Guide

Common issues, edge cases, and resolution steps for running the Lead Enrichment Agent.

## 1. Vercel Deployment Errors

### Issue A: `Found main.py but it does not export a top-level "app", "application", or "handler" variable`
- **Cause:** Vercel Python runtime scans root files and requires an exported ASGI/WSGI web app instance (`app`).
- **Fix:** Ensure [main.py](file:///d:/Lead_enrichment_agent/main.py) exports `app = FastAPI()` at the top level and [vercel.json](file:///d:/Lead_enrichment_agent/vercel.json) is present in the repository root.

### Issue B: Playwright Chromium Browser Launch Failure on Vercel Serverless
- **Cause:** Vercel serverless containers do not include headless Chromium binaries or Linux GUI shared libraries (`libnss3`, `libgbm`, etc.).
- **Fix:** The system automatically detects missing browser binaries and switches to the built-in **`aiohttp` HTTP fallback scraper** in `src/browser.py`, allowing the app to scrape web pages without crashing.

---

## 2. Groq API Authorization Error (`401 Invalid API Key`)
- **Cause:** Missing or invalid `GROQ_API_KEY` in `.env` or Vercel Environment Variables.
- **Fix:** Update your `.env` file or Vercel Dashboard with a valid key from [Groq Console](https://console.groq.com/).

---

## 3. SerpAPI Search Error (`401 Unauthorized`)
- **Cause:** Invalid `SERPAPI_API_KEY`.
- **Fix:** Provide a valid key in `.env`, or disable SerpAPI search by setting `ENABLE_SERPAPI=False`.

---

## 4. Playwright Linux/WSL Browser Dependencies
- **Cause:** Missing OS-level Chromium dependencies when running locally on Linux, Ubuntu, or WSL.
- **Fix:** Run the Playwright OS dependency installer:
  ```bash
  playwright install-deps chromium
  ```

---

## 5. Timeout or Blocked Websites
- **Cause:** Some enterprise websites block automated traffic or take >30s to load JS assets.
- **Fix:** Increase `TIMEOUT_SECONDS=45` in `.env`. The agent will automatically proceed with partial content if some subpages timeout.
