from bs4 import BeautifulSoup

BLOCKED_MARKERS = [
    "access denied",
    "attention required",
    "cloudflare",
    "captcha",
    "verify you are human",
    "just a moment...",
    "pardon our interruption"
]

def clean_html(html: str) -> str:
    """
    Cleans raw HTML by removing scripts, styles, SVGs, and navigation boilerplate,
    and returning clean text.
    """
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted tags
    for tag in soup(["script", "style", "svg", "nav", "footer", "header", "aside", "noscript", "iframe", "meta", "link"]):
        tag.decompose()

    # Get text
    text = soup.get_text(separator="\n")

    # Clean up whitespace and empty lines
    text = "\n".join(l for l in (ln.strip() for ln in text.splitlines()) if l)
    return text

def is_blocked_page(html: str) -> bool:
    """
    Checks if an HTML string indicates a bot-blocked page or security challenge page.
    """
    if not html:
        return False

    html_lower = html.lower()
    for marker in BLOCKED_MARKERS:
        if marker in html_lower:
            return True

    text = clean_html(html)
    if len(text) < 200:
        return True

    return False
