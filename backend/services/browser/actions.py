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

    async def _wait_for_stable(self, page: Page, timeout_ms: int = 3000) -> None:
        """Wait for page to stabilize after an action."""
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
        except Exception:
            pass
        await asyncio.sleep(0.5)
