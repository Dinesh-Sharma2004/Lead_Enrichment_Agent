import pytest
from src.discovery import discover_links

def test_discover_links_prioritization():
    html = '''
    <html>
      <a href="/about">About</a>
      <a href="/blog">Blog</a>
      <a href="/team">Team</a>
      <a href="https://external.com">External</a>
    </html>
    '''
    base_url = "https://example.com"
    links = discover_links(base_url, html)
    
    # external.com shouldn't be there
    assert "https://external.com" not in links
    
    # prioritized links should be first
    assert links[0] in ["https://example.com/about", "https://example.com/team"]
    assert links[1] in ["https://example.com/about", "https://example.com/team"]
    
    # others should be last
    assert links[2] == "https://example.com/blog"

def test_discover_links_handles_empty():
    assert discover_links("https://example.com", "") == []
    assert discover_links("https://example.com", "<html><body>No links</body></html>") == []
