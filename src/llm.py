import json
from typing import Dict, Any, List
import groq
from .schemas import CompanyIntelligence, ProductOrService, ContactPoint, Leader
from .logger import get_logger
from .config import GROQ_API_KEY, LLM_MODEL

logger = get_logger(__name__)


def normalize_llm_json(raw_data: Dict[str, Any], domain: str, processed_urls: List[str]) -> Dict[str, Any]:
    """
    Normalizes inconsistent LLM output structures into the canonical Pydantic dict format.
    Handles nested objects, title-case keys, array wrappers, and missing fields.
    """
    normalized = {}
    
    # Lowercase / snake_case map for keys
    key_map = {}
    for k, v in raw_data.items():
        clean_k = k.lower().replace(" ", "_").replace("-", "_")
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
                prod_list.append({
                    'name': str(p.get('name', '')),
                    'description': str(p.get('description', '')),
                    'source_url': str(p.get('source_url', processed_urls[0] if processed_urls else ""))
                })
            elif isinstance(p, str):
                prod_list.append({
                    'name': p,
                    'description': p,
                    'source_url': processed_urls[0] if processed_urls else ""
                })
    normalized['products_services'] = prod_list

    # 5. Contact Points
    contact_raw = key_map.get('contact_points', key_map.get('contacts', key_map.get('contact_emails', [])))
    contact_list = []
    if isinstance(contact_raw, dict):
        emails = contact_raw.get('emails', contact_raw.get('email_addresses', []))
        for item in emails:
            if isinstance(item, dict):
                contact_list.append({
                    'type': str(item.get('type', 'Email')),
                    'value': str(item.get('value', item.get('email', ''))),
                    'source_url': str(item.get('source_url', processed_urls[0] if processed_urls else ""))
                })
            elif isinstance(item, str):
                contact_list.append({'type': 'Email', 'value': item, 'source_url': processed_urls[0] if processed_urls else ""})
    elif isinstance(contact_raw, list):
        for c in contact_raw:
            if isinstance(c, dict):
                contact_list.append({
                    'type': str(c.get('type', 'Email')),
                    'value': str(c.get('value', c.get('email', ''))),
                    'source_url': str(c.get('source_url', processed_urls[0] if processed_urls else ""))
                })
            elif isinstance(c, str):
                contact_list.append({'type': 'Email', 'value': c, 'source_url': processed_urls[0] if processed_urls else ""})
    normalized['contact_points'] = contact_list

    # 6. Leadership
    leaders_raw = key_map.get('leadership', key_map.get('team', key_map.get('leadership_team', [])))
    if isinstance(leaders_raw, dict):
        leaders_raw = leaders_raw.get('members', leaders_raw.get('leaders', []))
        
    leader_list = []
    if isinstance(leaders_raw, list):
        for l in leaders_raw:
            if isinstance(l, dict):
                leader_list.append({
                    'name': str(l.get('name', '')),
                    'role': str(l.get('role', l.get('title', ''))),
                    'linkedin_url': l.get('linkedin_url', l.get('linkedin', None)),
                    'source_url': str(l.get('source_url', processed_urls[0] if processed_urls else ""))
                })
    normalized['leadership'] = leader_list

    # 7. Confidence Score & Extraction Status
    confidence = 1.0
    missing_fields = []
    if not normalized['company_overview']:
        confidence -= 0.2
        missing_fields.append('overview')
    if not normalized['products_services']:
        confidence -= 0.2
        missing_fields.append('products')
    if not normalized['leadership']:
        confidence -= 0.3
        missing_fields.append('leadership')
        
    normalized['confidence_score'] = round(max(0.1, confidence), 2)
    if missing_fields:
        normalized['extraction_status'] = f"Success | Missing: {', '.join(missing_fields)}"
    else:
        normalized['extraction_status'] = "Success - Complete"

    return normalized


async def extract_structured_data(domain: str, collected_text: Dict[str, str]) -> CompanyIntelligence:
    """
    Calls Groq LLM to extract structured data based on the canonical Pydantic schema.
    """
    logger.info(f"Extracting structured data for {domain} using {LLM_MODEL}...")

    content_payload = ""
    for url, text in collected_text.items():
        if text.strip():
            content_payload += f"\n--- SOURCE URL: {url} ---\n{text[:4000]}\n"

    system_prompt = """You are a precise corporate intelligence data extractor. You output ONLY valid JSON matching this exact flat schema:

{
  "company_name": "Official Name",
  "company_overview": "Exactly two concise sentences describing the company.",
  "overview_source_url": "URL where overview was found",
  "target_audience": "Ideal customer profile or target market.",
  "target_audience_source_url": "URL where target audience was found",
  "products_services": [
    {"name": "Product Name", "description": "Short description", "source_url": "URL"}
  ],
  "contact_points": [
    {"type": "Email", "value": "contact@company.com", "source_url": "URL"}
  ],
  "leadership": [
    {"name": "Full Name", "role": "Title", "linkedin_url": "https://linkedin.com/in/...", "source_url": "URL"}
  ]
}

CRITICAL RULES:
- `company_overview` MUST be a single string (NOT a nested object).
- `target_audience` MUST be a single string (NOT a nested object).
- `contact_points` MUST be a list of objects with type, value, and source_url.
- `source_url` values MUST be chosen from the provided SOURCE URL section headers.
- Do NOT invent information. If unknown, use empty strings or empty lists.
"""

    user_prompt = f"Extract company intelligence for {domain} from the following website text:\n{content_payload}"

    processed_urls = list(collected_text.keys())

    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY environment variable is missing.")
        fallback_data = normalize_llm_json({}, domain, processed_urls)
        fallback_data['extraction_status'] = "Failed - GROQ_API_KEY environment variable missing"
        fallback_data['confidence_score'] = 0.0
        return CompanyIntelligence(**fallback_data)

    client = groq.AsyncGroq(api_key=GROQ_API_KEY)

    try:
        response = await client.chat.completions.create(

            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=LLM_MODEL,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        
        raw_json = response.choices[0].message.content
        data = json.loads(raw_json)
        
        normalized_data = normalize_llm_json(data, domain, processed_urls)
        return CompanyIntelligence(**normalized_data)

    except Exception as e:
        logger.error(f"LLM Extraction exception for {domain}: {str(e)}")
        fallback_data = normalize_llm_json({}, domain, processed_urls)
        fallback_data['extraction_status'] = f"Partial Fallback - {str(e)}"
        fallback_data['confidence_score'] = 0.0
        return CompanyIntelligence(**fallback_data)
