import asyncio
from playwright.async_api import async_playwright, Page, BrowserContext
from urllib.parse import urlparse
from .logger import get_logger

logger = get_logger(__name__)

class BrowserManager:
    def __init__(self, max_concurrent: int = 3, timeout_seconds: int = 30):
        self.max_concurrent = max_concurrent
        self.timeout = timeout_seconds * 1000
        self.playwright = None
        self.browser = None
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        logger.info("Playwright browser started.")

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Playwright browser stopped.")

    async def get_page_content(self, url: str) -> tuple[str, str]:
        """
        Navigates to the URL and returns (final_url, html_content).
        Handles redirects and basic errors.
        """
        async with self.semaphore:
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
                logger.error(f"Error navigating to {url}: {str(e)}")
                return url, ""
            finally:
                await context.close()
