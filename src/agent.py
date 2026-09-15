import asyncio
from typing import Dict, List, Set
from collections import deque
from .browser import BrowserManager, PageResult
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
    Orchestrates automated link discovery, layered subpage crawling, content cleaning,
    LLM structured extraction, and conditional SerpAPI search for a single domain.
    """
    logger.info(f"Starting processing for {domain}")
    
    # Normalize domain
    if not domain.startswith("http"):
        base_url = f"https://{domain}"
    else:
        base_url = domain
        domain = domain.replace("https://", "").replace("http://", "")

    collected_text: Dict[str, str] = {}
    all_mailto_emails: Set[str] = set()
    visited_urls: Set[str] = set()
    
    # 1. Visit homepage
    home_res: PageResult = await browser_manager.get_page_content(base_url)
    visited_urls.add(base_url)

    if not home_res.html:
        logger.error(f"Could not load homepage for {domain} (Status: {home_res.status})")
        status_msg = "Failed - Homepage unreachable"
        if home_res.status >= 500:
            status_msg = "Timeout - retries exhausted on homepage"
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
            llm_confidence_score=0.0,
            heuristic_confidence_score=0.0,
            confidence_rationale="Homepage unreachable.",
            extraction_status=status_msg,
            all_processed_urls=[]
        )

    home_text = clean_html(home_res.html)
    collected_text[home_res.final_url] = home_text
    visited_urls.add(home_res.final_url)
    
    # Extract links & mailto emails from homepage
    page_links, mailtos = discover_links(home_res.final_url, home_res.html)
    all_mailto_emails.update(mailtos)

    # Queue for visiting subpages (including bounded second-hop discovery)
    link_queue: deque[str] = deque(page_links)
    visited_count = 1

    while link_queue and visited_count < MAX_PAGES_PER_DOMAIN:
        link = link_queue.popleft()
        if link in visited_urls:
            continue

        visited_urls.add(link)
        sub_res: PageResult = await browser_manager.get_page_content(link)
        if sub_res.html:
            sub_text = clean_html(sub_res.html)
            if sub_text:
                collected_text[sub_res.final_url] = sub_text
                visited_count += 1

                # Second-hop discovery: discover new priority links from priority subpages
                sub_links, sub_mailtos = discover_links(sub_res.final_url, sub_res.html)
                all_mailto_emails.update(sub_mailtos)
                for sl in sub_links:
                    if sl not in visited_urls and sl not in link_queue:
                        link_queue.append(sl)

    logger.info(f"Collected text from {visited_count} pages for {domain}. Sending to LLM...")

    # 4. Extract structured data via LLM
    intel = await extract_structured_data(domain, collected_text, list(all_mailto_emails))

    # Flag bot block status if homepage was blocked
    if home_res.blocked:
        intel.extraction_status = f"Blocked - Bot block detected on homepage | {intel.extraction_status}"

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
            intel.heuristic_confidence_score = max(0.1, round(intel.heuristic_confidence_score - 0.1, 2))
            intel.confidence_score = min(intel.llm_confidence_score, intel.heuristic_confidence_score)

    logger.info(f"Finished processing {domain}. Status: {intel.extraction_status}")
    return intel
