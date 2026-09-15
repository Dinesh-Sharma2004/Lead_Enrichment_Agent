import asyncio
from typing import Dict
from .browser import BrowserManager
from .discovery import discover_links
from .extraction import clean_html
from .llm import extract_structured_data
from .search import search_leadership
from .schemas import CompanyIntelligence, Leader
from .logger import get_logger
from .config import MAX_PAGES_PER_DOMAIN, ENABLE_SERPAPI

logger = get_logger(__name__)

async def process_domain(domain: str, browser_manager: BrowserManager) -> CompanyIntelligence:
    """
    Main workflow for a single domain.
    """
    logger.info(f"Starting processing for {domain}")
    
    # Normalize domain
    if not domain.startswith("http"):
        base_url = f"https://{domain}"
    else:
        base_url = domain
        domain = domain.replace("https://", "").replace("http://", "")

    collected_text: Dict[str, str] = {}
    
    # 1. Visit homepage
    home_url, home_html = await browser_manager.get_page_content(base_url)
    if not home_html:
        logger.error(f"Could not load homepage for {domain}")
        return CompanyIntelligence(
            domain=domain,
            company_name=domain.split('.')[0].capitalize(),
            company_overview="Failed to load homepage.",
            overview_source_url="",
            target_audience="",
            target_audience_source_url="",
            products_services=[],
            contact_points=[],
            leadership=[],
            confidence_score=0.0,
            extraction_status="Failed - Homepage unreachable",
            all_processed_urls=[]
        )

    # 2. Extract and discover links
    home_text = clean_html(home_html)
    collected_text[home_url] = home_text
    
    links_to_visit = discover_links(home_url, home_html)
    logger.info(f"Discovered {len(links_to_visit)} links for {domain}. Prioritizing top {MAX_PAGES_PER_DOMAIN - 1}...")

    # 3. Visit subpages
    visited_count = 1
    for link in links_to_visit:
        if visited_count >= MAX_PAGES_PER_DOMAIN:
            break
        if link in collected_text:
            continue
            
        final_url, html = await browser_manager.get_page_content(link)
        if html:
            text = clean_html(html)
            if text:
                collected_text[final_url] = text
                visited_count += 1

    logger.info(f"Collected text from {visited_count} pages for {domain}. Sending to LLM...")

    # 4. Extract structured data via LLM
    intel = await extract_structured_data(domain, collected_text)

    # 5. Conditional SerpAPI Search
    if ENABLE_SERPAPI and len(intel.leadership) == 0:
        search_company_name = intel.company_name
        if not search_company_name or search_company_name.lower() == "unknown":
            search_company_name = domain.split('.')[0].capitalize()

        logger.info(f"No leadership found on site for {domain}. Attempting SerpAPI search for '{search_company_name}'...")
        search_results = await search_leadership(search_company_name)
        if search_results:
            for res in search_results:
                intel.leadership.append(
                    Leader(
                        name=res.name,
                        role=res.role,
                        linkedin_url=res.linkedin_url,
                        source_url="SerpAPI Search"
                    )
                )
            intel.extraction_status += " | Leadership enriched via SerpAPI"
            intel.confidence_score = max(0.1, round(intel.confidence_score - 0.1, 2))

    logger.info(f"Finished processing {domain}. Status: {intel.extraction_status}")
    return intel
