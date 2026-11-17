import re
from urllib.parse import urljoin, urlparse
from typing import List, Tuple
from bs4 import BeautifulSoup

RELEVANT_PATH_PATTERNS = [
    r'/about',
    r'/company',
    r'/team',
    r'/leadership',
    r'/contact',
    r'/pricing',
    r'/product',
    r'/solution',
    r'/feature',
    r'/career'
]

NEGATIVE_PATH_PATTERNS = [
    r'/login',
    r'/signin',
    r'/signup',
    r'/register',
    r'/logout'
]

NEGATIVE_SUBDOMAIN_PREFIXES = [
    'dashboard.',
    'app.',
    'portal.',
    'my.'
]

def discover_links(base_url: str, html: str) -> Tuple[List[str], List[str]]:
    """
    Extracts internal page links and mailto email addresses from HTML content.
    Excludes negative path patterns and auth/dashboard subdomains.
    Returns a tuple of (prioritized_page_links, mailto_emails).
    """
    if not html:
        return [], []

    soup = BeautifulSoup(html, "html.parser")

    base_parsed = urlparse(base_url)
    base_domain = base_parsed.netloc

    links = set()
    mailto_emails = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href:
            continue

        if href.lower().startswith('mailto:'):
            email = href[7:].split('?')[0].strip()
            if '@' in email and '.' in email.split('@')[-1]:
                mailto_emails.add(email)
            continue

        if href.startswith(('javascript:', 'tel:')):
            continue

        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)
        
        target_netloc = parsed_url.netloc if parsed_url.netloc else base_domain

        # Negative subdomain check
        if any(target_netloc.startswith(prefix) for prefix in NEGATIVE_SUBDOMAIN_PREFIXES):
            continue

        # Negative path check
        path_lower = parsed_url.path.lower()
        if any(re.search(pattern, path_lower) for pattern in NEGATIVE_PATH_PATTERNS):
            continue

        # Check if internal domain or subdomain
        is_internal = False
        if target_netloc == base_domain:
            is_internal = True
        elif target_netloc.endswith('.' + base_domain) or base_domain.endswith('.' + target_netloc):
            is_internal = True
        elif target_netloc == "":
            is_internal = True

        if is_internal and parsed_url.scheme in ('http', 'https'):
            clean_url = f"{parsed_url.scheme}://{target_netloc}{parsed_url.path}"
            if parsed_url.query:
                clean_url += f"?{parsed_url.query}"
            links.add(clean_url)

    prioritized = []
    others = []

    for link in links:
        path = urlparse(link).path.lower()
        if any(re.search(pattern, path) for pattern in RELEVANT_PATH_PATTERNS):
            prioritized.append(link)
        else:
            others.append(link)

    page_links = sorted(prioritized) + sorted(others)
    return page_links, sorted(list(mailto_emails))

