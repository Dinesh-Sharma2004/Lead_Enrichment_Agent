# Configuration Reference Guide

All runtime settings and API credentials are managed using environment variables defined in `.env`.

## Environment Variables Reference

| Environment Variable | Default Value | Required? | Description |
| :--- | :--- | :--- | :--- |
| `GROQ_API_KEY` | *(None)* | **Yes** | Groq API Key for LLM extraction. |
| `SERPAPI_API_KEY` | *(None)* | **No** | SerpAPI Key for Google/LinkedIn leadership enrichment. |
| `ENABLE_SERPAPI` | `True` | **No** | Toggle external search fallback (`True`/`False`). |
| `MAX_CONCURRENT_DOMAINS` | `3` | **No** | Number of domains processed concurrently in parallel. |
| `MAX_PAGES_PER_DOMAIN` | `5` | **No** | Maximum subpages navigated per domain (Homepage + 4). |
| `TIMEOUT_SECONDS` | `30` | **No** | Per-page navigation timeout in seconds. |
| `LLM_MODEL` | `openai/gpt-oss-120b` | **No** | Groq LLM model name. |

## Application Modes

### 1. Streamlit Web UI
Launch the interactive Streamlit dashboard:
```bash
streamlit run app.py
```
- **Custom input:** Pass domains via the multi-line text input.
- **Default fallback:** Leaving the input empty defaults to reading `domains.txt`.

### 2. Command Line Interface (CLI)
Run batch domain processing from terminal:
```bash
python main.py domains.txt
```

## Concurrency & Performance Tuning

- **High-throughput servers:** Increase `MAX_CONCURRENT_DOMAINS` to `5` or `10` if running on machines with sufficient CPU and network capacity.
- **Slow/Heavy Websites:** Increase `TIMEOUT_SECONDS` to `45` or `60` for SPA websites with slow initial JavaScript renders.
