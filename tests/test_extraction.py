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
    assert is_blocked_page("<html><body>Hi</body></html>") is True  # short text (< 200 chars)
    
    long_content = "<html><body>" + ("This is a legitimate website homepage with plenty of content. " * 10) + "</body></html>"
    assert is_blocked_page(long_content) is False

