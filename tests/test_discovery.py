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
    links, mailtos = discover_links(base_url, html)
    
    # external.com shouldn't be there
    assert "https://external.com" not in links
    
    # prioritized links should be first
    assert links[0] in ["https://example.com/about", "https://example.com/team"]
    assert links[1] in ["https://example.com/about", "https://example.com/team"]
    
    # others should be last
    assert links[2] == "https://example.com/blog"

def test_discover_links_handles_empty():
    assert discover_links("https://example.com", "") == ([], [])
    assert discover_links("https://example.com", "<html><body>No links</body></html>") == ([], [])

def test_discover_links_netloc_and_subdomain_path():
    html = '''
    <html>
      <a href="https://example.com/sub/page">Same Domain Path</a>
      <a href="https://otherdomain.com/page">Other Domain</a>
      <a href="/relative/path">Relative Path</a>
    </html>
    '''
    links, mailtos = discover_links("https://example.com", html)
    assert "https://example.com/sub/page" in links
    assert "https://example.com/relative/path" in links
    assert "https://otherdomain.com/page" not in links

def test_discover_links_mailto_harvesting():
    html = '''
    <html>
      <a href="mailto:sales@example.com?subject=hi">Contact Sales</a>
      <a href="mailto:info@example.com">Info</a>
    </html>
    '''
def test_discover_links_negative_subdomain_and_path_filtering():
    html = '''
    <html>
      <a href="https://dashboard.example.com/login">Dashboard Login</a>
      <a href="https://example.com/signup">Signup Path</a>
      <a href="https://docs.example.com/api-reference">Docs API Reference</a>
    </html>
    '''
    links, mailtos = discover_links("https://example.com", html)
    assert "https://dashboard.example.com/login" not in links
    assert "https://example.com/signup" not in links
    assert "https://docs.example.com/api-reference" in links


