"""
Vercel serverless entrypoint for the Lead Enrichment Agent FastAPI application.

Key design decisions for Vercel compatibility:
- All heavy / optional imports (Playwright, BrowserManager, pandas) are deferred
  to inside the endpoint functions so a cold-start import never crashes.
- `src.*` modules are imported lazily inside request handlers, never at module level.
- The FastAPI `app` object is the ASGI callable that Vercel's Python runtime serves.
- CLI execution path in main.py is preserved untouched.
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from typing import List

# ---------------------------------------------------------------------------
# Ensure the repository root is on sys.path so `src.*` imports resolve.
# This is critical in the Vercel serverless environment where the working
# directory may differ from the function file location.
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# FastAPI application — this is the ASGI object Vercel looks for.
# NOTE: Do NOT import anything from `src.*` here at module level.
#       Playwright and other heavy deps would crash the cold-start.
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Autonomous Lead Enrichment Agent API",
    description="Asynchronous corporate intelligence engine — powered by Groq AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


class EnrichRequest(BaseModel):
    domains: List[str]


# ---------------------------------------------------------------------------
# Favicon endpoint (handles browser icon requests cleanly without 404)
# ---------------------------------------------------------------------------
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Root endpoint — HTML dashboard (mirrors main.py's @app.get("/"))
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Lead Enrichment Engine</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: #0f172a; color: #f8fafc; min-height: 100vh; padding: 2rem; }
        .container { max-width: 1100px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 2rem; }
        .header h1 { font-size: 2.2rem; font-weight: 700; background: linear-gradient(to right, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header p { color: #94a3b8; font-size: 1rem; margin-top: 0.5rem; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
        label { display: block; font-weight: 600; margin-bottom: 0.5rem; color: #cbd5e1; }
        textarea { width: 100%; height: 120px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: #f8fafc; padding: 0.8rem; font-size: 0.95rem; resize: vertical; }
        textarea:focus { outline: none; border-color: #6366f1; }
        .hint { font-size: 0.85rem; color: #64748b; margin-top: 0.4rem; }
        button { background: #6366f1; color: white; border: none; padding: 0.8rem 1.6rem; font-size: 1rem; font-weight: 600; border-radius: 8px; cursor: pointer; transition: all 0.2s; margin-top: 1rem; width: 100%; }
        button:hover { background: #4f46e5; }
        button:disabled { background: #475569; cursor: not-allowed; }
        .spinner { display: none; text-align: center; margin: 1.5rem 0; color: #38bdf8; font-weight: 500; }
        .results-section { display: none; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
        .metric-card { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 1rem; text-align: center; }
        .metric-value { font-size: 1.6rem; font-weight: 700; color: #38bdf8; }
        .metric-label { font-size: 0.85rem; color: #94a3b8; margin-top: 0.2rem; }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: #0f172a; border-radius: 8px; overflow: hidden; }
        th, td { padding: 0.8rem 1rem; text-align: left; border-bottom: 1px solid #334155; font-size: 0.9rem; }
        th { background: #1e293b; color: #94a3b8; font-weight: 600; }
        tr:hover { background: #1e293b; }
        .btn-group { display: flex; gap: 1rem; margin-top: 1rem; }
        .btn-secondary { background: #334155; color: white; flex: 1; text-align: center; text-decoration: none; padding: 0.6rem; border-radius: 6px; font-weight: 500; cursor: pointer; }
        .btn-secondary:hover { background: #475569; }
        .api-links { display: flex; gap: 1rem; flex-wrap: wrap; justify-content: center; margin-top: 1.5rem; }
        .api-link { background: #1e293b; border: 1px solid #334155; color: #38bdf8; padding: 0.5rem 1.2rem; border-radius: 6px; text-decoration: none; font-size: 0.9rem; }
        .api-link:hover { border-color: #38bdf8; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Autonomous Lead Enrichment Engine</h1>
            <p>Asynchronous corporate intelligence web discovery &amp; Groq AI extraction</p>
            <div class="api-links">
                <a class="api-link" href="/docs">📖 API Docs</a>
                <a class="api-link" href="/health">❤️ Health</a>
                <a class="api-link" href="/redoc">📋 ReDoc</a>
            </div>
        </div>

        <div class="card">
            <label for="domains">Target Domains</label>
            <textarea id="domains" placeholder="e.g.&#10;stripe.com&#10;supabase.com&#10;postman.com"></textarea>
            <div class="hint">💡 One domain per line. Leave blank to process default domains from <code>domains.txt</code></div>
            <button id="submitBtn" onclick="runEnrichment()">🚀 Start Lead Enrichment</button>
        </div>

        <div id="spinner" class="spinner">
            ⏳ Crawling subpages, parsing content, and extracting Groq AI lead intelligence...
        </div>

        <div id="resultsSection" class="results-section card">
            <h2>📊 Enriched Lead Results</h2>
            <div class="metrics-grid">
                <div class="metric-card"><div id="metricTotal" class="metric-value">0</div><div class="metric-label">Processed Domains</div></div>
                <div class="metric-card"><div id="metricSuccess" class="metric-value">0</div><div class="metric-label">Complete Extractions</div></div>
                <div class="metric-card"><div id="metricConfidence" class="metric-value">0%</div><div class="metric-label">Avg Confidence Score</div></div>
            </div>
            <div style="overflow-x: auto;">
                <table id="resultsTable">
                    <thead>
                        <tr>
                            <th>Domain</th><th>Company Name</th><th>Overview</th>
                            <th>Leadership</th><th>Contacts</th><th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody"></tbody>
                </table>
            </div>
            <div class="btn-group">
                <a id="downloadJson" class="btn-secondary">📥 Download JSON</a>
                <a id="downloadCsv" class="btn-secondary">📥 Download CSV</a>
            </div>
        </div>
    </div>

    <script>
        async function runEnrichment() {
            const raw = document.getElementById('domains').value.trim();
            let domainsList = [];
            if (raw) {
                domainsList = raw.split(/[\\n,]+/).map(d => d.trim().replace(/^https?:\\/\\//, '').split('/')[0]).filter(Boolean);
            }
            if (domainsList.length === 0) {
                try {
                    const resDef = await fetch('/api/default-domains');
                    const defData = await resDef.json();
                    domainsList = defData.domains || [];
                } catch(e) { domainsList = []; }
            }
            if (domainsList.length === 0) {
                alert('No domains found. Enter at least one domain above.');
                return;
            }
            document.getElementById('submitBtn').disabled = true;
            document.getElementById('spinner').style.display = 'block';
            document.getElementById('resultsSection').style.display = 'none';
            try {
                const res = await fetch('/enrich', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ domains: domainsList })
                });
                if (!res.ok) throw new Error(await res.text());
                const data = await res.json();
                renderResults(data);
            } catch (err) {
                alert('Enrichment failed: ' + err.message);
            } finally {
                document.getElementById('submitBtn').disabled = false;
                document.getElementById('spinner').style.display = 'none';
            }
        }
        function renderResults(data) {
            document.getElementById('resultsSection').style.display = 'block';
            document.getElementById('metricTotal').innerText = data.length;
            const successCount = data.filter(d => (d.extraction_status || '').includes('Complete')).length;
            document.getElementById('metricSuccess').innerText = successCount + '/' + data.length;
            const avgConf = data.reduce((acc, d) => acc + (d.confidence_score || 0), 0) / (data.length || 1);
            document.getElementById('metricConfidence').innerText = Math.round(avgConf * 100) + '%';
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';
            data.forEach(item => {
                const tr = document.createElement('tr');
                const leaders = (item.leadership || []).map(l => l.name + ' (' + l.role + ')').join(', ') || 'N/A';
                const contacts = (item.contact_points || []).map(c => c.value).join(', ') || 'N/A';
                tr.innerHTML = `<td><strong>${item.domain}</strong></td><td>${item.company_name || 'N/A'}</td><td>${item.company_overview || 'N/A'}</td><td>${leaders}</td><td>${contacts}</td><td><span style="color:${item.confidence_score > 0.7 ? '#4ade80' : '#facc15'}">${item.extraction_status}</span></td>`;
                tbody.appendChild(tr);
            });
            const jsonStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
            document.getElementById('downloadJson').setAttribute("href", jsonStr);
            document.getElementById('downloadJson').setAttribute("download", "output.json");
            let csvContent = "data:text/csv;charset=utf-8,Domain,Company Name,Overview,Confidence Score,Status\\n";
            data.forEach(d => {
                const row = [d.domain, d.company_name, d.company_overview, d.confidence_score, d.extraction_status]
                    .map(v => '"' + String(v || '').replace(/"/g, '""') + '"').join(',');
                csvContent += row + "\\n";
            });
            document.getElementById('downloadCsv').setAttribute("href", encodeURI(csvContent));
            document.getElementById('downloadCsv').setAttribute("download", "output.csv");
        }
    </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Returns API health status and environment readiness."""
    groq_key_set = bool(os.environ.get("GROQ_API_KEY"))
    serpapi_key_set = bool(os.environ.get("SERPAPI_API_KEY"))

    # Lazy-check whether src modules are importable (don't actually import Playwright)
    try:
        import importlib.util
        src_ok = importlib.util.find_spec("src.config") is not None
    except Exception:
        src_ok = False

    try:
        import groq  # noqa: F401
        groq_ok = True
    except ImportError:
        groq_ok = False

    return {
        "status": "ok",
        "environment": {
            "GROQ_API_KEY_set": groq_key_set,
            "SERPAPI_API_KEY_set": serpapi_key_set,
            "groq_package_installed": groq_ok,
            "src_modules_importable": src_ok,
        }
    }


# ---------------------------------------------------------------------------
# Default domains helper endpoint
# ---------------------------------------------------------------------------
@app.get("/api/default-domains")
async def get_default_domains():
    """Returns domains listed in domains.txt if it exists."""
    file_path = ROOT_DIR / "domains.txt"
    if file_path.exists():
        with open(file_path, "r") as f:
            domains = [line.strip() for line in f if line.strip()]
        return {"domains": domains}
    return {"domains": []}


# ---------------------------------------------------------------------------
# Core enrichment endpoint — ALL heavy imports are deferred to inside the
# function body so a Playwright import failure never crashes the cold-start.
# ---------------------------------------------------------------------------
@app.post("/enrich")
async def enrich_domains_endpoint(request: EnrichRequest):
    """
    Enriches a list of company domains with structured intelligence.

    Accepts JSON body: {"domains": ["stripe.com", "notion.so"]}
    Returns a list of CompanyIntelligence objects.

    Note: On Vercel serverless, Playwright Chromium binaries are unavailable.
    The BrowserManager automatically falls back to aiohttp HTTP scraping,
    which covers the majority of public company sites.
    """
    if not request.domains:
        raise HTTPException(status_code=400, detail="Domain list cannot be empty.")

    # ----- Lazy imports (never at module level) -----
    try:
        from src.browser import BrowserManager
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"BrowserManager module could not be loaded: {exc}. "
                   "Ensure src/ is present in the deployment package."
        )

    try:
        from src.agent import process_domain
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Agent module could not be loaded: {exc}."
        )

    try:
        from src.config import MAX_CONCURRENT_DOMAINS
    except ImportError:
        MAX_CONCURRENT_DOMAINS = 2  # safe serverless default

    try:
        from src.logger import get_logger
        logger = get_logger("api.index")
    except ImportError:
        import logging
        logger = logging.getLogger("api.index")

    # ----- Execute enrichment pipeline -----
    try:
        # Vercel functions run in a single-threaded event loop; cap concurrency
        # to avoid memory pressure inside the 1 GB limit.
        effective_concurrency = min(MAX_CONCURRENT_DOMAINS, 2)
        browser_manager = BrowserManager(max_concurrent=effective_concurrency)

        # BrowserManager.start() gracefully falls back to HTTP if Playwright
        # binaries are absent (which they always are on Vercel).
        await browser_manager.start()

        try:
            tasks = [process_domain(domain, browser_manager) for domain in request.domains]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            await browser_manager.stop()

        # Filter out any exceptions that slipped through gather
        output = []
        for domain, result in zip(request.domains, results):
            if isinstance(result, Exception):
                logger.error(f"Domain {domain} failed: {result}")
                # Return a minimal failed record instead of crashing the whole response
                output.append({
                    "domain": domain,
                    "company_name": domain.split(".")[0].capitalize(),
                    "company_overview": "",
                    "overview_source_url": "",
                    "target_audience": "",
                    "target_audience_source_url": "",
                    "products_services": [],
                    "contact_points": [],
                    "leadership": [],
                    "confidence_score": 0.0,
                    "extraction_status": f"Failed - {str(result)[:200]}",
                    "all_processed_urls": [],
                })
            else:
                output.append(result.model_dump())

        return output

    except Exception as exc:
        logger.error(f"Enrichment pipeline error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=(
                f"Enrichment failed: {str(exc)}. "
                "On Vercel, Playwright Chromium is unavailable — the HTTP fallback scraper "
                "is used automatically. For full browser rendering, deploy to a VPS/Docker environment."
            )
        )


# ---------------------------------------------------------------------------
# Allow `python api/index.py` for local testing (uvicorn is still preferred)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.index:app", host="0.0.0.0", port=8000, reload=True)