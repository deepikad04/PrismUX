from __future__ import annotations

import asyncio
import base64
import logging
from typing import TYPE_CHECKING

from schemas.navigation import ActionPlan, ActionResult

if TYPE_CHECKING:
    from playwright.async_api import Page

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Executes planned actions on a Playwright page."""

    async def execute(self, page: Page, plan: ActionPlan) -> ActionResult:
        try:
            action = plan.action_type

            if action == "click":
                if plan.coordinates:
                    x, y = plan.coordinates
                    await page.mouse.click(x, y)
                    await self._wait_for_stable(page)
                    # Fallback: also dispatch JS click for elements that
                    # don't respond to synthetic mouse events (cookie
                    # consent overlays, shadow DOM, etc.)
                    try:
                        await page.evaluate(
                            """([x, y]) => {
                                const el = document.elementFromPoint(x, y);
                                if (el) el.click();
                            }""",
                            [x, y],
                        )
                    except Exception:
                        pass

            elif action == "type":
                if plan.input_text:
                    await page.keyboard.type(plan.input_text, delay=50)

            elif action == "scroll_down":
                await page.mouse.wheel(0, 400)
                await asyncio.sleep(0.5)

            elif action == "scroll_up":
                await page.mouse.wheel(0, -400)
                await asyncio.sleep(0.5)

            elif action == "press_key":
                if plan.key:
                    await page.keyboard.press(plan.key)
                    await self._wait_for_stable(page)

            elif action == "hover":
                if plan.coordinates:
                    x, y = plan.coordinates
                    await page.mouse.move(x, y)
                    await asyncio.sleep(0.3)

            elif action == "wait":
                seconds = plan.seconds or 2
                await asyncio.sleep(seconds)

            elif action == "go_back":
                await page.go_back(wait_until="domcontentloaded", timeout=10_000)

            elif action == "done":
                pass

            else:
                return ActionResult(success=False, error=f"Unknown action: {action}")

            return ActionResult(success=True, url_after=page.url)

        except Exception as e:
            logger.error("Action execution failed: %s", e)
            return ActionResult(success=False, url_after=page.url, error=str(e))

    async def take_screenshot(self, page: Page) -> str:
        """Take a screenshot and return as base64 string."""
        png_bytes = await page.screenshot(type="png")
        return base64.b64encode(png_bytes).decode("utf-8")

    async def dismiss_cookie_consent(self, page: Page) -> bool:
        """Proactively find and dismiss cookie consent banners on the main page and inside iframes.

        Returns True if a consent button was clicked.
        """
        # Common button texts used by consent banners across the web
        button_texts = [
            "Accept all", "Accept All", "Accept all cookies", "Accept All Cookies",
            "Allow all", "Allow All", "Allow all cookies",
            "Accept", "I agree", "I Accept", "Agree",
            "OK", "Got it", "Got It", "Understood",
            "Godkänn alla", "Acceptera alla",  # Swedish (vasamuseet.se)
            "Tillåt alla", "Acceptera",
            "Akzeptieren", "Alle akzeptieren",  # German
            "Tout accepter", "Accepter tout",   # French
            "Aceptar todo", "Aceptar",          # Spanish
        ]

        js_dismiss = """(buttonTexts) => {
            function findAndClick(root) {
                // Search buttons, links, divs with button role, and spans inside buttons
                const candidates = root.querySelectorAll(
                    'button, a, [role="button"], input[type="button"], input[type="submit"], .consent-btn, [class*="accept"], [class*="agree"], [class*="cookie"] button, [id*="accept"], [id*="consent"] button'
                );
                for (const el of candidates) {
                    const text = (el.textContent || el.value || '').trim();
                    for (const target of buttonTexts) {
                        if (text === target || text.toLowerCase() === target.toLowerCase()) {
                            el.click();
                            return text;
                        }
                    }
                }
                // Broader: partial match on button-like elements
                for (const el of candidates) {
                    const text = (el.textContent || el.value || '').trim().toLowerCase();
                    if (text.length > 50) continue;  // Skip long text (not a button)
                    for (const target of buttonTexts) {
                        if (text.includes(target.toLowerCase())) {
                            el.click();
                            return text;
                        }
                    }
                }
                return null;
            }
            // Try main document first
            let result = findAndClick(document);
            if (result) return result;
            // Try shadow DOMs
            const allEls = document.querySelectorAll('*');
            for (const el of allEls) {
                if (el.shadowRoot) {
                    result = findAndClick(el.shadowRoot);
                    if (result) return result;
                }
            }
            return null;
        }"""

        try:
            # 1. Try the main page
            result = await page.evaluate(js_dismiss, button_texts)
            if result:
                logger.info("Cookie consent dismissed on main page: '%s'", result)
                await asyncio.sleep(1.0)
                return True

            # 2. Try all iframes (common for OneTrust, CookieBot, Didomi, etc.)
            for frame in page.frames:
                if frame == page.main_frame:
                    continue
                try:
                    result = await frame.evaluate(js_dismiss, button_texts)
                    if result:
                        logger.info("Cookie consent dismissed in iframe: '%s'", result)
                        await asyncio.sleep(1.0)
                        return True
                except Exception:
                    continue

            # 3. Playwright locator approach — click by accessible name
            for text in button_texts[:8]:  # Try top candidates
                try:
                    btn = page.get_by_role("button", name=text, exact=False)
                    if await btn.count() > 0:
                        await btn.first.click(timeout=2000)
                        logger.info("Cookie consent dismissed via locator: '%s'", text)
                        await asyncio.sleep(1.0)
                        return True
                except Exception:
                    continue

        except Exception as e:
            logger.debug("Cookie consent dismissal error: %s", e)

        return False

    async def _wait_for_stable(self, page: Page, timeout_ms: int = 3000) -> None:
        """Wait for page to stabilize after an action."""
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
        except Exception:
            pass
        await asyncio.sleep(0.5)
