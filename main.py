import asyncio
import sys
import json
import pandas as pd
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

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Autonomous Lead Enrichment Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "enrich": "POST /enrich"
        }
    }

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
        
    df = pd.DataFrame(csv_rows)
    df.to_csv("output.csv", index=False)
    logger.info("Saved results to output.csv")

if __name__ == "__main__":
    asyncio.run(cli_main())

