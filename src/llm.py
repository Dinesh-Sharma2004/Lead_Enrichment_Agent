import json
import asyncio
from typing import Dict, Any, List, Optional
import groq
from .schemas import CompanyIntelligence, ContactPoint
from .logger import get_logger
from .config import GROQ_API_KEY, LLM_MODEL, TOTAL_CONTEXT_CHAR_BUDGET

logger = get_logger(__name__)


def repair_llm_json(raw_data: Dict[str, Any], domain: str, processed_urls: List[str]) -> Dict[str, Any]:
    """
    Fallback repair function for LLM json output structures into canonical Pydantic dict format.
    Handles nested objects, title-case keys, array wrappers, and missing fields.
    """
    normalized: Dict[str, Any] = {}
    
    key_map: Dict[str, Any] = {}
    if isinstance(raw_data, dict):
        for k, v in raw_data.items():
            clean_k = str(k).lower().replace(" ", "_").replace("-", "_")
            key_map[clean_k] = v
        
    normalized['domain'] = domain
    normalized['all_processed_urls'] = processed_urls
    
    # 1. Company Name
    normalized['company_name'] = str(key_map.get('company_name', domain.split('.')[0].capitalize()))
    if normalized['company_name'].lower() in ("unknown", "none", ""):
        normalized['company_name'] = domain.split('.')[0].capitalize()

    # 2. Company Overview & Source URL
    overview_val = key_map.get('company_overview', "")
    if isinstance(overview_val, dict):
        normalized['company_overview'] = str(overview_val.get('text', overview_val.get('description', '')))
        normalized['overview_source_url'] = str(overview_val.get('source_url', overview_val.get('url', processed_urls[0] if processed_urls else "")))
    else:
        normalized['company_overview'] = str(overview_val)
        normalized['overview_source_url'] = str(key_map.get('overview_source_url', processed_urls[0] if processed_urls else ""))

    # 3. Target Audience & Source URL
    audience_val = key_map.get('target_audience', "")
    if isinstance(audience_val, dict):
        normalized['target_audience'] = str(audience_val.get('text', audience_val.get('description', '')))
        normalized['target_audience_source_url'] = str(audience_val.get('source_url', audience_val.get('url', processed_urls[0] if processed_urls else "")))
    else:
        normalized['target_audience'] = str(audience_val)
        normalized['target_audience_source_url'] = str(key_map.get('target_audience_source_url', processed_urls[0] if processed_urls else ""))

    # 4. Products Services
    products_raw = key_map.get('products_services', key_map.get('products', key_map.get('services', [])))
    if isinstance(products_raw, dict):
        products_raw = products_raw.get('list', products_raw.get('products', []))
    
    prod_list = []
    if isinstance(products_raw, list):
        for p in products_raw:
            if isinstance(p, dict):
                desc = str(p.get('description', '')).strip()
                src = str(p.get('source_url', processed_urls[0] if processed_urls else f"https://{domain}")).strip()
                if desc and src:
                    prod_list.append({
                        'name': str(p.get('name', '')).strip(),
                        'description': desc,
                        'source_url': src
                    })
    normalized['products_services'] = prod_list

    # 5. Contact Points
    contact_raw = key_map.get('contact_points', key_map.get('contacts', key_map.get('contact_emails', [])))
    contact_list = []
    default_src = processed_urls[0] if processed_urls else f"https://{domain}"
    if isinstance(contact_raw, dict):
        emails = contact_raw.get('emails', contact_raw.get('email_addresses', []))
        for item in emails:
            if isinstance(item, dict):
                val = str(item.get('value', item.get('email', ''))).strip()
                if val:
                    contact_list.append({
                        'type': str(item.get('type', 'Email')),
                        'value': val,
                        'source_url': str(item.get('source_url', default_src)).strip() or default_src
                    })
            elif isinstance(item, str) and item.strip():
                contact_list.append({'type': 'Email', 'value': item.strip(), 'source_url': default_src})
    elif isinstance(contact_raw, list):
        for c in contact_raw:
            if isinstance(c, dict):
                val = str(c.get('value', c.get('email', ''))).strip()
                if val:
                    contact_list.append({
                        'type': str(c.get('type', 'Email')),
                        'value': val,
                        'source_url': str(c.get('source_url', default_src)).strip() or default_src
                    })
            elif isinstance(c, str) and c.strip():
                contact_list.append({'type': 'Email', 'value': c.strip(), 'source_url': default_src})
    normalized['contact_points'] = contact_list

    # 6. Leadership
    leaders_raw = key_map.get('leadership', key_map.get('team', key_map.get('leadership_team', [])))
    if isinstance(leaders_raw, dict):
        leaders_raw = leaders_raw.get('members', leaders_raw.get('leaders', []))
        
    leader_list = []
    if isinstance(leaders_raw, list):
        for l in leaders_raw:
            if isinstance(l, dict):
                src = str(l.get('source_url', default_src)).strip() or default_src
                leader_list.append({
                    'name': str(l.get('name', '')).strip(),
                    'role': str(l.get('role', l.get('title', ''))).strip(),
                    'linkedin_url': l.get('linkedin_url', l.get('linkedin', None)),
                    'source_url': src
                })
    normalized['leadership'] = leader_list

    # 7. LLM Confidence Score & Rationale
    try:
        normalized['llm_confidence_score'] = float(key_map.get('llm_confidence_score', 0.8))
    except (ValueError, TypeError):
        normalized['llm_confidence_score'] = 0.8
    normalized['confidence_rationale'] = str(key_map.get('confidence_rationale', ''))

    return normalized


# Backward compatibility alias
normalize_llm_json = repair_llm_json



def calculate_heuristic_confidence(company_intel: Dict[str, Any]) -> float:
    """Calculates rule-based heuristic confidence score between 0.0 and 1.0 considering fill quality."""
    score = 1.0
    
    # 1. Company Overview
    overview = company_intel.get('company_overview', '')
    if not overview:
        score -= 0.2
        
    # 2. Products / Services
    products = company_intel.get('products_services', [])
    if not products:
        score -= 0.2
    else:
        valid_count = sum(
            1 for p in products 
            if isinstance(p, dict) and p.get('description') and p.get('source_url')
        )
        fill_rate = valid_count / len(products)
        score -= 0.2 * (1.0 - fill_rate)

    # 3. Leadership
    leaders = company_intel.get('leadership', [])
    if not leaders:
        score -= 0.3
    else:
        valid_count = sum(
            1 for l in leaders 
            if isinstance(l, dict) and (l.get('role') or l.get('linkedin_url')) and not str(l.get('role', '')).startswith('[Unverified]')
        )
        fill_rate = valid_count / len(leaders)
        score -= 0.3 * (1.0 - fill_rate)

    # 4. Contact Points
    contacts = company_intel.get('contact_points', [])
    if not contacts:
        score -= 0.1
    else:
        valid_count = sum(
            1 for c in contacts 
            if isinstance(c, dict) and c.get('value') and c.get('source_url')
        )
        fill_rate = valid_count / len(contacts)
        score -= 0.1 * (1.0 - fill_rate)

    return round(max(0.0, score), 2)


async def _call_groq_with_retry(client: groq.AsyncGroq, **kwargs: Any) -> Any:
    """Calls Groq API with 429 rate limit backoff retry helper."""
    max_retries = 1
    for attempt in range(max_retries + 1):
        try:
            return await client.chat.completions.create(**kwargs)
        except groq.RateLimitError as e:
            if attempt < max_retries:
                sleep_sec = 2.0
                retry_after = getattr(e, 'response', None)
                if retry_after and hasattr(retry_after, 'headers'):
                    hdr = retry_after.headers.get("Retry-After")
                    if hdr and hdr.isdigit():
                        sleep_sec = float(hdr)
                logger.warning(f"Groq API 429 Rate Limit encountered. Retrying after {sleep_sec}s (attempt {attempt + 1})...")
                await asyncio.sleep(sleep_sec)
            else:
                raise


def get_extraction_tool_schema() -> Dict[str, Any]:
    """Generates the JSON Schema parameter definition for extract_company_intelligence tool."""
    full_schema = CompanyIntelligence.model_json_schema()
    excluded = {
        "domain", "all_processed_urls", "total_tokens_used",
        "estimated_cost_usd", "heuristic_confidence_score",
        "confidence_score", "extraction_status"
    }
    props = full_schema.get("properties", {})
    filtered_props = {k: v for k, v in props.items() if k not in excluded}
    
    req = full_schema.get("required", [])
    filtered_req = [r for r in req if r not in excluded]

    tool_schema: Dict[str, Any] = {
        "type": "object",
        "properties": filtered_props,
    }
    if filtered_req:
        tool_schema["required"] = filtered_req
    if "$defs" in full_schema:
        tool_schema["$defs"] = full_schema["$defs"]
    return tool_schema


async def extract_structured_data(
    domain: str,
    collected_text: Dict[str, str],
    mailto_emails: Optional[List[str]] = None
) -> CompanyIntelligence:
    """
    Calls Groq LLM using tool calling to extract structured company intelligence.
    Enforces strict Pydantic schema validation with repair_llm_json as a safety fallback.
    """
    logger.info(f"Extracting structured data for {domain} using {LLM_MODEL}...")

    # Calculate per-page character budget based on TOTAL_CONTEXT_CHAR_BUDGET
    num_pages = max(1, len(collected_text))
    per_page_budget = max(1500, TOTAL_CONTEXT_CHAR_BUDGET // num_pages)

    content_payload = ""
    for url, text in collected_text.items():
        if text.strip():
            content_payload += f"\n--- SOURCE URL: {url} ---\n{text[:per_page_budget]}\n"

    mailto_hint = ""
    if mailto_emails:
        mailto_hint = f"\nPRE-SEEDED MAILTO EMAILS FOUND: {', '.join(mailto_emails)}. Include these verbatim in `contact_points` with type 'Email' and source_url from the domain.\n"

    system_prompt = (
        "You are a precise corporate intelligence data extractor.\n"
        "Assess data completeness honestly and self-assess `llm_confidence_score` (0.0 to 1.0) "
        "and provide a short `confidence_rationale` explaining your rating (e.g. grounded overview, leadership found, contact info available).\n"
        "Do NOT invent facts. If information is missing, leave fields empty.\n"
        "Only include a product/service entry if you can also give a real one-sentence description and the exact source URL it came from. If you can't, omit the product entirely rather than leaving fields blank.\n"
        "Only classify a person as leadership if the surrounding text explicitly identifies them as an employee, executive, or team member of the target company (e.g. their title includes the company name, or they appear on a page whose URL contains /about, /team, /company, or /leadership). Do not include people quoted as customers, partners, or in press mentions."
    )

    user_prompt = f"Extract company intelligence for {domain} from the following website text:{mailto_hint}\n{content_payload}"
    processed_urls = list(collected_text.keys())

    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY environment variable is missing.")
        fallback_data = repair_llm_json({}, domain, processed_urls)
        fallback_data['extraction_status'] = "Failed - GROQ_API_KEY environment variable missing"
        fallback_data['llm_confidence_score'] = 0.0
        fallback_data['heuristic_confidence_score'] = 0.0
        fallback_data['confidence_score'] = 0.0
        return CompanyIntelligence(**fallback_data)

    tool_schema = get_extraction_tool_schema()
    tools = [
        {
            "type": "function",
            "function": {
                "name": "extract_company_intelligence",
                "description": "Extract structured company intelligence from website content.",
                "parameters": tool_schema
            }
        }
    ]
    tool_choice = {"type": "function", "function": {"name": "extract_company_intelligence"}}

    client = groq.AsyncGroq(api_key=GROQ_API_KEY)

    try:
        response = await _call_groq_with_retry(
            client,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=LLM_MODEL,
            temperature=0.1,
            tools=tools,
            tool_choice=tool_choice
        )

        prompt_tokens = response.usage.prompt_tokens if (response.usage and hasattr(response.usage, 'prompt_tokens')) else 0
        completion_tokens = response.usage.completion_tokens if (response.usage and hasattr(response.usage, 'completion_tokens')) else 0
        total_tokens = prompt_tokens + completion_tokens
        estimated_cost = (prompt_tokens * 0.00000015) + (completion_tokens * 0.00000060)
        logger.info(f"LLM Token Usage for {domain}: {prompt_tokens} prompt + {completion_tokens} completion = {total_tokens} total tokens (~${estimated_cost:.6f} USD)")

        # Parse tool arguments
        raw_data: Dict[str, Any] = {}
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls and len(tool_calls) > 0:
            arguments_str = tool_calls[0].function.arguments
            raw_data = json.loads(arguments_str)

        raw_data['domain'] = domain
        raw_data['all_processed_urls'] = processed_urls
        raw_data['total_tokens_used'] = total_tokens
        raw_data['estimated_cost_usd'] = round(estimated_cost, 6)

        # Filter out products missing description or source_url per Bug 2
        filtered_prods = []
        for p in raw_data.get('products_services', []):
            if isinstance(p, dict):
                desc = str(p.get('description', '')).strip()
                src = str(p.get('source_url', '')).strip()
                if desc and src:
                    filtered_prods.append(p)
        raw_data['products_services'] = filtered_prods

        # Ensure leadership items have a non-empty source_url for Pydantic min_length=1 validation
        default_src = processed_urls[0] if processed_urls else f"https://{domain}"
        filtered_leaders = []
        for l in raw_data.get('leadership', []):
            if isinstance(l, dict):
                if not l.get('source_url'):
                    l['source_url'] = default_src
                filtered_leaders.append(l)
        raw_data['leadership'] = filtered_leaders

        try:
            intel = CompanyIntelligence(**raw_data)
            logger.info(f"Strict Pydantic schema validation succeeded for {domain}.")
        except Exception as val_err:
            logger.warning(f"Strict Pydantic validation failed for {domain} ({val_err}). Falling back to repair_llm_json.")
            repaired = repair_llm_json(raw_data, domain, processed_urls)
            repaired['total_tokens_used'] = total_tokens
            repaired['estimated_cost_usd'] = round(estimated_cost, 6)
            intel = CompanyIntelligence(**repaired)

        # Grounding validation check (Bug 3 & Bug 2)
        norm_processed = {u.rstrip('/') for u in processed_urls}
        
        for leader in intel.leadership:
            source_norm = leader.source_url.rstrip('/') if leader.source_url else ""
            if not source_norm or source_norm not in norm_processed:
                leader.grounded = False
                if not leader.role.startswith("[Unverified]"):
                    leader.role = f"[Unverified] {leader.role}".strip() if leader.role else "[Unverified]"

        for prod in intel.products_services:
            source_norm = prod.source_url.rstrip('/') if prod.source_url else ""
            if not source_norm or source_norm not in norm_processed:
                prod.grounded = False

        for cp in intel.contact_points:
            source_norm = cp.source_url.rstrip('/') if cp.source_url else ""
            if not source_norm or source_norm not in norm_processed:
                cp.grounded = False

        # Post-process mailto emails if missing from contact_points
        if mailto_emails:
            existing_emails = {cp.value.lower() for cp in intel.contact_points if cp.value}
            for email in mailto_emails:
                if email.lower() not in existing_emails:
                    intel.contact_points.append(
                        ContactPoint(type="Email", value=email, source_url=processed_urls[0] if processed_urls else f"https://{domain}", grounded=True)
                    )

        # Calculate heuristic confidence score and set final min score
        h_score = calculate_heuristic_confidence(intel.model_dump())
        l_score = intel.llm_confidence_score if intel.llm_confidence_score > 0 else 0.8
        
        intel.heuristic_confidence_score = h_score
        intel.llm_confidence_score = l_score
        intel.confidence_score = round(min(l_score, h_score), 2)
        
        if not intel.extraction_status or intel.extraction_status == "Success":
            missing = []
            if not intel.company_overview:
                missing.append("overview")
            if not intel.products_services:
                missing.append("products")
            if not intel.leadership:
                missing.append("leadership")
            if missing:
                intel.extraction_status = f"Success | Missing: {', '.join(missing)}"
            else:
                intel.extraction_status = "Success - Complete"

        return intel

    except Exception as e:
        logger.error(f"LLM Extraction exception for {domain}: {str(e)}")
        fallback_data = repair_llm_json({}, domain, processed_urls)
        fallback_data['extraction_status'] = f"Partial Fallback - {str(e)}"
        fallback_data['llm_confidence_score'] = 0.0
        fallback_data['heuristic_confidence_score'] = 0.0
        fallback_data['confidence_score'] = 0.0
        return CompanyIntelligence(**fallback_data)

