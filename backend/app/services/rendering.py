"""
Rendering Service
Uses Playwright to render SPA (Single Page Applications) and fetch full DOM.
Uses Synchronous Playwright in a thread to avoid asyncio loop conflicts on Windows.
"""
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Playwright, Page, Error as PlaywrightError
import logging
import asyncio

logger = logging.getLogger(__name__)

class RenderingService:
    """
    Service to handle Headless Browser rendering using Playwright.
    Uses sync_playwright wrapped in asyncio.to_thread for robust compatibility.
    """
    
    @classmethod
    async def start(cls):
        """No-op for sync scheduler - browser is launched per request or managed internally"""
        # We can implement a persistent sync browser later if performance is an issue,
        # but for now, launching per request or letting the sync context handle it is safer against loop errors.
        logger.info("🚀 RenderingService: Ready (Sync Mode)")

    @classmethod
    async def stop(cls):
        """No-op for sync scheduler"""
        pass

    @classmethod
    def _fetch_sync(cls, url: str, timeout: int) -> str:
        """Sync implementation of fetching"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-accelerated-2d-canvas",
                        "--no-first-run",
                        "--no-zygote",
                        "--single-process",
                        "--disable-gpu"
                    ]
                )
                
                context = browser.new_context(
                    user_agent="SiteAuditorBot/1.0 (Deep Scan Mode; +https://example.com/bot)"
                )
                
                try:
                    page = context.new_page()
                    # logger is not thread-safe safe? usually yes, but let's be careful
                    # print(f"🕸️ Deep Scan (Sync): Navigating to {url}...")
                    
                    page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
                    
                    try:
                        page.wait_for_load_state("networkidle", timeout=timeout * 1000)
                    except Exception:
                        pass # Warning: networkidle timeout
                    
                    content = page.content()
                    return content
                finally:
                    context.close()
                    browser.close()
        except Exception as e:
            raise e

    @classmethod
    async def fetch_rendered_html(cls, url: str, timeout: int = 30) -> str:
        """
        Navigate to URL, wait for network idle, and return full HTML.
        Runs sync playwright in a separate thread.
        """
        try:
            logger.info(f"🕸️ Deep Scan: Navigating to {url}...")
            content = await asyncio.to_thread(cls._fetch_sync, url, timeout)
            logger.info(f"✅ Deep Scan: Retrieved {len(content)} bytes of HTML.")
            return content
        except Exception as e:
            logger.error(f"❌ Deep Scan Error on {url}: {e}")
            raise e
