"""Google ADK (Agent Development Kit) integration for PrismUX navigator.

Wraps Playwright browser actions as ADK FunctionTools, then composes them
into a LoopAgent → LlmAgent hierarchy that Gemini drives autonomously.
"""

from __future__ import annotations

import base64
import contextvars
import logging
from typing import TYPE_CHECKING

from google.adk.agents import LlmAgent, LoopAgent
from google.adk.tools import FunctionTool

if TYPE_CHECKING:
    from playwright.async_api import Page

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Playwright action functions exposed as ADK FunctionTools
# ---------------------------------------------------------------------------

# Use contextvars for task-local page reference (safe for concurrent sessions)
_page_var: contextvars.ContextVar[Page | None] = contextvars.ContextVar(
    "_page_var", default=None
)


def _get_page() -> Page | None:
    """Get the current page from the task-local context variable."""
    return _page_var.get()


async def click_element(x: int, y: int) -> str:
    """Click the element at pixel coordinates (x, y) on the current page."""
    page = _get_page()
    if not page:
        return "error: no page"
    await page.mouse.click(x, y)
    await page.wait_for_load_state("domcontentloaded", timeout=3000)
    return f"clicked ({x}, {y}) — now on {page.url}"


async def type_text(text: str) -> str:
    """Type text into the currently focused input field."""
    page = _get_page()
    if not page:
        return "error: no page"
    await page.keyboard.type(text, delay=50)
    return f"typed '{text}'"


async def scroll_down() -> str:
    """Scroll the page down to reveal more content."""
    page = _get_page()
    if not page:
        return "error: no page"
    await page.mouse.wheel(0, 400)
    return "scrolled down 400px"


async def scroll_up() -> str:
    """Scroll the page up."""
    page = _get_page()
    if not page:
        return "error: no page"
    await page.mouse.wheel(0, -400)
    return "scrolled up 400px"


async def press_key(key: str) -> str:
    """Press a keyboard key (e.g. 'Enter', 'Tab', 'Escape')."""
    page = _get_page()
    if not page:
        return "error: no page"
    await page.keyboard.press(key)
    return f"pressed {key}"


async def go_back() -> str:
    """Navigate the browser back to the previous page."""
    page = _get_page()
    if not page:
        return "error: no page"
    await page.go_back(wait_until="domcontentloaded", timeout=10_000)
    return f"went back — now on {page.url}"


async def take_screenshot() -> dict:
    """Take a screenshot of the current page and return it as base64."""
    page = _get_page()
    if not page:
        return {"error": "no page"}
    png = await page.screenshot(type="png")
    b64 = base64.b64encode(png).decode()
    return {"screenshot_b64": b64, "url": page.url}


async def finish_navigation(reason: str) -> str:
    """Call this when the navigation goal has been achieved or cannot be achieved."""
    return f"DONE: {reason}"


# ---------------------------------------------------------------------------
# Build ADK agent graph
# ---------------------------------------------------------------------------

TOOLS = [
    FunctionTool(click_element),
    FunctionTool(type_text),
    FunctionTool(scroll_down),
    FunctionTool(scroll_up),
    FunctionTool(press_key),
    FunctionTool(go_back),
    FunctionTool(take_screenshot),
    FunctionTool(finish_navigation),
]


def build_adk_agent(goal: str, persona_prompt: str = "") -> LoopAgent:
    """Create a LoopAgent wrapping an LlmAgent configured for UI navigation."""

    instruction = f"""You are PrismUX, an AI UI Navigator agent.

GOAL: {goal}

{persona_prompt}

You can see the page via take_screenshot() and interact using click_element, type_text, scroll_down, scroll_up, press_key, go_back.

STRATEGY:
1. Start by calling take_screenshot() to see the current page.
2. Analyze the screenshot to understand the page layout and find relevant UI elements.
3. Take actions toward the goal. After each action, take a screenshot to verify the result.
4. If you detect UX friction (confusing labels, low contrast, small targets, unclear navigation), note it in your reasoning.
5. When the goal is achieved or you determine it cannot be achieved, call finish_navigation(reason).

IMPORTANT:
- Always use pixel coordinates from the screenshot (viewport is 1280x720).
- Take a screenshot after every action to verify results.
- Be methodical and explain your reasoning.
"""

    navigator = LlmAgent(
        name="prismux_navigator",
        model="gemini-2.0-flash",
        instruction=instruction,
        tools=TOOLS,
    )

    loop = LoopAgent(
        name="navigation_loop",
        sub_agents=[navigator],
        max_iterations=30,
    )

    return loop


def set_page_ref(page: Page) -> None:
    """Set the task-local page reference for ADK tools to use."""
    _page_var.set(page)


def clear_page_ref() -> None:
    """Clear the task-local page reference."""
    _page_var.set(None)
