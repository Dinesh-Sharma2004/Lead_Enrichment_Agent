# Troubleshooting Guide

Common issues, edge cases, and resolution steps for running the Lead Enrichment Agent.

## 1. Groq API Authorization Error (`401 Invalid API Key`)
- **Cause:** Missing or invalid `GROQ_API_KEY` in `.env`.
- **Fix:** Update your `.env` file with a valid key from [Groq Console](https://console.groq.com/).

## 2. SerpAPI Search Error (`401 Unauthorized`)
- **Cause:** Invalid `SERPAPI_API_KEY`.
- **Fix:** Provide a valid key in `.env`, or disable SerpAPI search by setting `ENABLE_SERPAPI=False`.

## 3. Playwright Linux/WSL Browser Dependencies
- **Cause:** Missing OS-level Chromium dependencies when running on Linux, Ubuntu, or WSL.
- **Fix:** Run the Playwright OS dependency installer:
  ```bash
  playwright install-deps chromium
  ```

## 4. Timeout or Blocked Websites
- **Cause:** Some enterprise websites block automated traffic or take >30s to load JS assets.
- **Fix:** Increase `TIMEOUT_SECONDS=45` in `.env`. The agent will automatically proceed with partial content if some subpages timeout.
