import asyncio
import aiohttp
from urllib.parse import urlparse
from .logger import get_logger

logger = get_logger(__name__)

try:
    from playwright.async_api import async_playwright, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

class BrowserManager:
    def __init__(self, max_concurrent: int = 3, timeout_seconds: int = 30):
        self.max_concurrent = max_concurrent
        self.timeout = timeout_seconds * 1000
        self.timeout_sec = timeout_seconds
        self.playwright = None
        self.browser = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.use_fallback = not PLAYWRIGHT_AVAILABLE

    async def start(self):
        if not PLAYWRIGHT_AVAILABLE:
            logger.info("Playwright not installed in environment. Using HTTP scraper fallback.")
            self.use_fallback = True
            return

        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            logger.info("Playwright browser started.")
        except Exception as e:
            logger.warning(f"Playwright failed to launch ({str(e)}). Switching to HTTP fallback scraper.")
            self.use_fallback = True


    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser manager stopped.")

    async def get_page_content(self, url: str) -> tuple[str, str]:
        """
        Navigates to the URL and returns (final_url, html_content).
        Handles redirects and basic errors.
        """
        async with self.semaphore:
            if self.use_fallback or not self.browser:
                return await self._http_fallback_get(url)

            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            page.set_default_timeout(self.timeout)

            try:
                logger.info(f"Navigating to {url}")
                response = await page.goto(url, wait_until="domcontentloaded")
                if response and response.status >= 400:
                    logger.warning(f"Failed to load {url} - Status: {response.status}")
                    return url, ""
                
                # Scroll a bit to trigger lazy loading
                await page.evaluate("window.scrollBy(0, 500)")
                await asyncio.sleep(0.5)

                html = await page.content()
                final_url = page.url
                return final_url, html
            except Exception as e:
                logger.error(f"Error navigating to {url}: {str(e)}. Attempting HTTP fallback.")
                return await self._http_fallback_get(url)
            finally:
                await context.close()

    async def _http_fallback_get(self, url: str) -> tuple[str, str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=self.timeout_sec, allow_redirects=True) as resp:
                    if resp.status < 400:
                        html = await resp.text()
                        return str(resp.url), html
                    else:
                        logger.warning(f"HTTP fallback load {url} - Status: {resp.status}")
                        return url, ""
        except Exception as e:
            logger.error(f"HTTP fallback error for {url}: {str(e)}")
            return url, ""

