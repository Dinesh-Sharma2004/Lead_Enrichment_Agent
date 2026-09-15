import pytest
from src.extraction import clean_html

def test_clean_html_removes_scripts():
    html = "<html><body><script>alert('test');</script><p>Hello World</p></body></html>"
    cleaned = clean_html(html)
    assert "alert" not in cleaned
    assert "Hello World" in cleaned

def test_clean_html_removes_nav_and_footer():
    html = '''
    <html>
      <nav>Menu Items</nav>
      <body>
        <main>Main Content</main>
      </body>
      <footer>Copyright 2024</footer>
    </html>
    '''
    cleaned = clean_html(html)
    assert "Menu Items" not in cleaned
    assert "Copyright 2024" not in cleaned
    assert "Main Content" in cleaned

def test_clean_html_empty():
    assert clean_html("") == ""
    assert clean_html(None) == ""

def test_is_blocked_page():
    from src.extraction import is_blocked_page
    assert is_blocked_page("<html><title>Access Denied</title></html>") is True
    assert is_blocked_page("<html><body>Attention Required! Cloudflare captcha</body></html>") is True
    
    long_content = "<html><body>" + ("This is a legitimate website homepage with plenty of content. " * 10) + "</body></html>"
    assert is_blocked_page(long_content) is False

def test_is_blocked_page_false_positive_prevention():
    from src.extraction import is_blocked_page
    # Script tag with cloudflare CDN + 1000+ chars of real body text must NOT be flagged as blocked
    long_body = "This is legitimate company body text describing products and leadership. " * 20
    html_normal = f'<html><head><script src="https://cdnjs.cloudflare.com/foo.js"></script></head><body>{long_body}</body></html>'
    assert is_blocked_page(html_normal) is False

    # Title is "Just a moment..." with near-empty body MUST be flagged as blocked
    html_blocked = '<html><head><title>Just a moment...</title></head><body><p>Checking your browser...</p></body></html>'
    assert is_blocked_page(html_blocked) is True

def test_clean_html_link_density_heuristic():
    # <div> full of only <a> links gets stripped
    nav_div_html = '<html><body><div><a href="/p1">Product 1</a><a href="/p2">Product 2</a><a href="/p3">Product 3</a></div></body></html>'
    cleaned_nav = clean_html(nav_div_html)
    assert "Product 1" not in cleaned_nav

    # <div> with genuine prose is preserved
    prose_div_html = '<html><body><div><p>This is a detailed description of our enterprise software platform that enables teams to automate workflows.</p><a href="/learn">Learn More</a></div></body></html>'
    cleaned_prose = clean_html(prose_div_html)
    assert "enterprise software platform" in cleaned_prose


