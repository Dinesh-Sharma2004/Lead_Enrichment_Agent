import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Heuristics for important pages
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

def discover_links(base_url: str, html: str) -> list[str]:
    """
    Extracts and prioritizes internal links from the HTML content.
    Returns a sorted list of unique URLs.
    """
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    base_domain = urlparse(base_url).netloc

    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href or href.startswith(('javascript:', 'mailto:', 'tel:')):
            continue

        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)
        
        # Only keep internal links (same domain)
        if parsed_url.netloc == base_domain or parsed_url.netloc == "":
            # Normalize URL by removing fragments
            clean_url = f"{parsed_url.scheme}://{base_domain}{parsed_url.path}"
            if parsed_url.query:
                clean_url += f"?{parsed_url.query}"
            links.add(clean_url)

    # Prioritize links based on heuristics
    prioritized = []
    others = []

    for link in links:
        path = urlparse(link).path.lower()
        if any(re.search(pattern, path) for pattern in RELEVANT_PATH_PATTERNS):
            prioritized.append(link)
        else:
            others.append(link)

    # Return prioritized links first
    return sorted(prioritized) + sorted(others)
