import asyncio
import sys
import json
import pandas as pd
from pathlib import Path
from src.browser import BrowserManager
from src.agent import process_domain
from src.logger import get_logger
from src.config import MAX_CONCURRENT_DOMAINS

logger = get_logger("main")

async def main():
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
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        await browser_manager.stop()

    results = []
    from src.schemas import CompanyIntelligence
    for domain, res in zip(domains, raw_results):
        if isinstance(res, Exception):
            logger.error(f"Unhandled exception processing domain {domain}: {res}")
            fallback = CompanyIntelligence(
                domain=domain,
                company_name=domain.split('.')[0].capitalize(),
                company_overview="",
                extraction_status=f"Failed - Unhandled exception: {res}",
                confidence_score=0.0,
                llm_confidence_score=0.0,
                heuristic_confidence_score=0.0
            )
            results.append(fallback)
        else:
            results.append(res)


    # Save to JSON
    json_data = [res.model_dump() for res in results]
    with open("output.json", "w") as f:
        json.dump(json_data, f, indent=2)
    logger.info("Saved results to output.json")

    # Save to CSV
    csv_rows = []
    for res in results:
        row = res.model_dump()
        row['products_services'] = "; ".join([p['name'] for p in row['products_services']])
        row['contact_points'] = "; ".join([f"{c['type']}: {c['value']}" for c in row['contact_points']])
        row['leadership'] = "; ".join([f"{l['name']} ({l['role']})" for l in row['leadership']])
        row['all_processed_urls'] = ", ".join(row['all_processed_urls'])
        csv_rows.append(row)
        
    df = pd.DataFrame(csv_rows)
    df.to_csv("output.csv", index=False)
    logger.info("Saved results to output.csv")

if __name__ == "__main__":
    asyncio.run(main())
