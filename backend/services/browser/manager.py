from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from playwright.async_api import async_playwright

from config import get_settings

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)

_browser_manager: BrowserManager | None = None

# Maximum concurrent browser contexts (navigation sessions)
MAX_CONCURRENT_SESSIONS = 3


class BrowserManager:
    """Singleton managing Playwright browser lifecycle with bounded concurrency."""

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_SESSIONS)
        self._active_count = 0

    @property
    def active_sessions(self) -> int:
        return self._active_count

    async def start(self) -> None:
        settings = get_settings()
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.browser_headless,
        )
        logger.info("Playwright browser launched (headless=%s)", settings.browser_headless)

    async def new_session(self, url: str) -> tuple[BrowserContext, Page]:
        if self._browser is None:
            raise RuntimeError("BrowserManager not started. Call start() first.")

        await self._semaphore.acquire()
        self._active_count += 1
        logger.info(
            "Browser session acquired (%d/%d active)",
            self._active_count, MAX_CONCURRENT_SESSIONS,
        )

        try:
            settings = get_settings()
            context = await self._browser.new_context(
                viewport={
                    "width": settings.screenshot_width,
                    "height": settings.screenshot_height,
                },
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            # Release semaphore when context closes
            original_close = context.close

            async def _tracked_close() -> None:
                await original_close()
                self._active_count -= 1
                self._semaphore.release()
                logger.info(
                    "Browser session released (%d/%d active)",
                    self._active_count, MAX_CONCURRENT_SESSIONS,
                )

            context.close = _tracked_close  # type: ignore[assignment]

            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            logger.info("Browser session opened: %s", url)
            return context, page

        except Exception:
            self._active_count -= 1
            self._semaphore.release()
            raise

    async def shutdown(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Playwright browser shut down")


def get_browser_manager() -> BrowserManager:
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager()
    return _browser_manager
