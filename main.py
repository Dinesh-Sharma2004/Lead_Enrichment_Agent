import asyncio
import sys
import json
import csv
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.browser import BrowserManager
from src.agent import process_domain
from src.logger import get_logger
from src.config import MAX_CONCURRENT_DOMAINS

logger = get_logger("main")

# Top-level FastAPI application instance exported for Vercel serverless deployment
app = FastAPI(
    title="Autonomous Lead Enrichment Agent API",
    description="Asynchronous corporate intelligence engine API",
    version="1.0.0"
)

class EnrichRequest(BaseModel):
    domains: List[str]

from fastapi.responses import HTMLResponse

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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Autonomous Lead Enrichment Engine</h1>
            <p>Asynchronous corporate intelligence web discovery & Groq AI extraction</p>
        </div>
        
        <div class="card">
            <label for="domains">Target Domains</label>
            <textarea id="domains" placeholder="e.g.&#10;stripe.com&#10;supabase.com&#10;postman.com"></textarea>
            <div class="hint">💡 Leave blank to automatically process default domains from <code>domains.txt</code></div>
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
                            <th>Domain</th>
                            <th>Company Name</th>
                            <th>Overview</th>
                            <th>Leadership</th>
                            <th>Contacts</th>
                            <th>Status</th>
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
                domainsList = raw.split(/[\n,]+/).map(d => d.trim().replace(/^https?:\\\/\\\//, '').split('/')[0]).filter(Boolean);
            }
            
            if (domainsList.length === 0) {
                const resDef = await fetch('/api/default-domains');
                const defData = await resDef.json();
                domainsList = defData.domains || [];
            }
            
            if (domainsList.length === 0) {
                alert('No domains found or domains.txt is empty.');
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
                
                tr.innerHTML = `
                    <td><strong>${item.domain}</strong></td>
                    <td>${item.company_name || 'N/A'}</td>
                    <td>${item.company_overview || 'N/A'}</td>
                    <td>${leaders}</td>
                    <td>${contacts}</td>
                    <td><span style="color:${item.confidence_score > 0.7 ? '#4ade80' : '#facc15'}">${item.extraction_status}</span></td>
                `;
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

@app.get("/api/default-domains")
async def get_default_domains():
    file_path = Path("domains.txt")
    if file_path.exists():
        with open(file_path, "r") as f:
            domains = [line.strip() for line in f if line.strip()]
        return {"domains": domains}
    return {"domains": []}

@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/enrich")
async def enrich_domains_endpoint(request: EnrichRequest):
    if not request.domains:
        raise HTTPException(status_code=400, detail="Domain list cannot be empty")
    
    try:
        browser_manager = BrowserManager(max_concurrent=MAX_CONCURRENT_DOMAINS)
        await browser_manager.start()
        
        try:
            tasks = [process_domain(d, browser_manager) for d in request.domains]
            results = await asyncio.gather(*tasks)
        finally:
            await browser_manager.stop()
            
        return [res.model_dump() for res in results]
    except Exception as e:
        logger.error(f"Error executing enrichment: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Enrichment failed: {str(e)}. Note: Playwright Chromium requires system browser dependencies."
        )


async def cli_main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <domains_file.txt>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        logger.error(f"Input file {input_file} not found.")
        sys.exit(1)

    with open(input_file, 'r') as f:
        domains = [line.strip() for line in f if line.strip()]

    logger.info(f"Loaded {len(domains)} domains from {input_file}")

    browser_manager = BrowserManager(max_concurrent=MAX_CONCURRENT_DOMAINS)
    await browser_manager.start()

    tasks = [process_domain(domain, browser_manager) for domain in domains]
    
    try:
        # Run all domain processing concurrently
        results = await asyncio.gather(*tasks)
    finally:
        await browser_manager.stop()

    # Save to JSON
    json_data = [res.model_dump() for res in results]
    with open("output.json", "w") as f:
        json.dump(json_data, f, indent=2)
    logger.info("Saved results to output.json")

    # Save to CSV (flattening somewhat for tabular format)
    csv_rows = []
    for res in results:
        row = res.model_dump()
        # Simplify lists to strings for CSV
        row['products_services'] = "; ".join([p['name'] for p in row['products_services']])
        row['contact_points'] = "; ".join([f"{c['type']}: {c['value']}" for c in row['contact_points']])
        row['leadership'] = "; ".join([f"{l['name']} ({l['role']})" for l in row['leadership']])
        row['all_processed_urls'] = ", ".join(row['all_processed_urls'])
        csv_rows.append(row)
        
    if PANDAS_AVAILABLE:
        df = pd.DataFrame(csv_rows)
        df.to_csv("output.csv", index=False)
    else:
        if csv_rows:
            with open("output.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
                writer.writeheader()
                writer.writerows(csv_rows)
    logger.info("Saved results to output.csv")


if __name__ == "__main__":
    asyncio.run(cli_main())

