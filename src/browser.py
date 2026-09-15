import asyncio
from dataclasses import dataclass
from typing import Optional
from playwright.async_api import async_playwright, Page, BrowserContext, Error as PlaywrightError
from .logger import get_logger
from .extraction import is_blocked_page
from .config import NETWORK_IDLE_TIMEOUT_MS, PAGE_HYDRATION_TIMEOUT_MS, MAX_RETRIES

logger = get_logger(__name__)

@dataclass
class PageResult:
    final_url: str
    html: str
    blocked: bool = False
    status: int = 200

class BrowserManager:
    def __init__(self, max_concurrent: int = 3, timeout_seconds: int = 30):
        self.max_concurrent = max_concurrent
        self.timeout = timeout_seconds * 1000
        self.playwright = None
        self.browser = None
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def start(self) -> None:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        logger.info("Playwright browser started.")

    async def stop(self) -> None:
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Playwright browser stopped.")

    async def get_page_content(self, url: str) -> PageResult:
        """
        Navigates to the URL with layered waiting, retry with exponential backoff for transient failures,
        and bot-block detection.
        Returns a PageResult object.
        """
        async with self.semaphore:
            attempts = MAX_RETRIES + 1

            for attempt in range(attempts):
                context: Optional[BrowserContext] = None
                try:
                    context = await self.browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        viewport={'width': 1920, 'height': 1080}
                    )
                    page = await context.new_page()
                    page.set_default_timeout(self.timeout)

                    logger.info(f"Navigating to {url} (Attempt {attempt + 1}/{attempts})")
                    response = await page.goto(url, wait_until="domcontentloaded")

                    status_code = response.status if response else 200

                    # 4xx client errors should not be retried
                    if 400 <= status_code < 500:
                        logger.warning(f"Failed to load {url} - Client Error Status: {status_code}")
                        return PageResult(final_url=url, html="", blocked=False, status=status_code)

                    # 5xx server errors trigger retry
                    if status_code >= 500:
                        raise PlaywrightError(f"Server error HTTP {status_code}")

                    # Layered wait: networkidle (optional/best-effort)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT_MS)
                    except Exception:
                        pass

                    # Scroll step to trigger lazy load
                    try:
                        await page.evaluate("window.scrollBy(0, 500)")
                    except Exception:
                        pass

                    # Bounded hydration wait
                    await page.wait_for_timeout(PAGE_HYDRATION_TIMEOUT_MS)

                    html = await page.content()
                    final_url = page.url
                    blocked = is_blocked_page(html)

                    if blocked:
                        logger.warning(f"Bot block / interstitial detected on {url}")

                    return PageResult(final_url=final_url, html=html, blocked=blocked, status=status_code)

                except Exception as e:
                    if attempt < MAX_RETRIES:
                        backoff = 1.0 * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1}/{attempts} failed for {url}: {str(e)}. Retrying in {backoff}s...")
                        await asyncio.sleep(backoff)
                    else:
                        logger.error(f"All retries exhausted for {url}: {str(e)}")
                finally:
                    if context:
                        await context.close()

            return PageResult(final_url=url, html="", blocked=False, status=500)
