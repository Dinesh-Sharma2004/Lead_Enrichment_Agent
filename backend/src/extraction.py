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
    Cleans raw HTML by removing scripts, styles, SVGs, navigation boilerplate,
    link-dense navigation/menu blocks, and returning clean text.
    """
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted tags
    for tag in soup(["script", "style", "svg", "nav", "footer", "header", "aside", "noscript", "iframe", "meta", "link"]):
        tag.decompose()

    # Link-density heuristic: decompose <div> and <ul> blocks where link text / total text > 0.7
    for block in list(soup.find_all(["div", "ul"])):
        if block.parent is None:
            continue
        block_text = block.get_text(strip=True)
        if not block_text:
            continue
        anchor_text = "".join(a.get_text(strip=True) for a in block.find_all("a"))
        if len(anchor_text) / len(block_text) > 0.7:
            block.decompose()

    # Get text
    text = soup.get_text(separator="\n")

    # Clean up whitespace and empty lines
    text = "\n".join(l for l in (ln.strip() for ln in text.splitlines()) if l)
    return text

def is_blocked_page(html: str) -> bool:
    """
    Checks if an HTML string indicates a bot-blocked page or security challenge page.
    Requires either a title match or (a body-text marker match and body text < 200 chars).
    """
    if not html:
        return False

    soup = BeautifulSoup(html, "html.parser")
    title_text = soup.title.string.strip().lower() if (soup.title and soup.title.string) else ""

    text = clean_html(html)
    body_head_lower = text[:500].lower()

    # 1. Check title tag match
    for marker in BLOCKED_MARKERS:
        if marker in title_text:
            return True

    # 2. Check visible body text match only if page text is short (< 200 chars)
    if len(text) < 200:
        for marker in BLOCKED_MARKERS:
            if marker in body_head_lower:
                return True

    return False

