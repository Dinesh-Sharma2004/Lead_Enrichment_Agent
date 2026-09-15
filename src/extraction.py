import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

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
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)
    
    return text
