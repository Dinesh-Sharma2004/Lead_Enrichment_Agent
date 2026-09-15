import asyncio
import aiohttp
from typing import List
from .schemas import SerpSearchResult
from .config import SERPAPI_API_KEY
from .logger import get_logger

logger = get_logger(__name__)

async def search_leadership(company_name: str) -> List[SerpSearchResult]:
    """
    Searches for leadership information using SerpAPI if enabled.
    Guards against searching for 'Unknown'.
    """
    if not SERPAPI_API_KEY:
        logger.warning("SerpAPI key not found. Skipping external search.")
        return []

    if not company_name or company_name.lower() in ("unknown", "none", "n/a"):
        logger.warning(f"Invalid company name '{company_name}' provided to SerpAPI. Skipping.")
        return []

    logger.info(f"Performing SerpAPI search for '{company_name}' leadership...")
    
    query = f'site:linkedin.com/in/ "{company_name}" (CEO OR Founder OR Director)'
    
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": 3
    }
    
    results = []
    try:
        async with aiohttp.ClientSession() as session:
            for attempt in range(2):
                async with session.get("https://serpapi.com/search", params=params) as response:
                    if response.status == 429 and attempt == 0:
                        retry_after = response.headers.get("Retry-After")
                        sleep_sec = float(retry_after) if (retry_after and retry_after.isdigit()) else 2.0
                        logger.warning(f"SerpAPI 429 Rate Limit encountered. Retrying in {sleep_sec}s...")
                        await asyncio.sleep(sleep_sec)
                        continue

                    if response.status == 200:
                        data = await response.json()
                        organic_results = data.get("organic_results", [])
                        
                        for res in organic_results:
                            title = res.get("title", "")
                            link = res.get("link", "")
                            
                            # Basic parsing of LinkedIn title: "Name - Role - Company"
                            parts = title.split("-")
                            if len(parts) >= 2:
                                name = parts[0].strip()
                                role = parts[1].strip()
                                results.append(SerpSearchResult(name=name, role=role, linkedin_url=link))
                        break
                    else:
                        logger.error(f"SerpAPI returned status {response.status}")
                        break
    except Exception as e:
        logger.error(f"Error during SerpAPI search: {str(e)}")
        
    return results

