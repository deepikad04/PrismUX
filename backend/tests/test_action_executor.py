"""Tests for ActionExecutor — browser action execution and cookie consent."""

from __future__ import annotations

import asyncio
import base64
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schemas.navigation import ActionPlan, ActionResult
from services.browser.actions import ActionExecutor


@pytest.fixture
def executor():
    return ActionExecutor()


@pytest.fixture
def mock_page():
    """Create a mock Playwright page with all needed methods."""
    page = AsyncMock()
    page.url = "https://example.com"
    page.mouse = AsyncMock()
    page.keyboard = AsyncMock()
    page.evaluate = AsyncMock(return_value=None)
    page.wait_for_load_state = AsyncMock()
    page.go_back = AsyncMock()
    page.screenshot = AsyncMock(return_value=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    page.main_frame = MagicMock()
    page.frames = [page.main_frame]
    page.get_by_role = MagicMock()
    return page


# ─── Action Execution Tests ───


@pytest.mark.asyncio
async def test_click_with_coordinates(executor, mock_page):
    plan = ActionPlan(
        action_type="click",
        coordinates=(100, 200),
        reasoning="Click the signup button",
        confidence=0.9,
    )
    result = await executor.execute(mock_page, plan)
    assert result.success is True
    mock_page.mouse.click.assert_called_once_with(100, 200)


@pytest.mark.asyncio
async def test_click_without_coordinates(executor, mock_page):
    """Click action with no coordinates should still succeed (no-op click)."""
    plan = ActionPlan(
        action_type="click",
        reasoning="Click something",
        confidence=0.8,
    )
    result = await executor.execute(mock_page, plan)
    assert result.success is True
    mock_page.mouse.click.assert_not_called()


@pytest.mark.asyncio
async def test_type_action(executor, mock_page):
    plan = ActionPlan(
        action_type="type",
        input_text="hello@example.com",
        reasoning="Type email",
        confidence=0.95,
    )
    result = await executor.execute(mock_page, plan)
    assert result.success is True
    mock_page.keyboard.type.assert_called_once_with("hello@example.com", delay=50)


@pytest.mark.asyncio
async def test_type_without_text(executor, mock_page):
    plan = ActionPlan(
        action_type="type",
        reasoning="Type nothing",
        confidence=0.5,
    )
    result = await executor.execute(mock_page, plan)
    assert result.success is True
    mock_page.keyboard.type.assert_not_called()


@pytest.mark.asyncio
async def test_scroll_down(executor, mock_page):
    plan = ActionPlan(
        action_type="scroll_down",
        reasoning="Scroll to see more",
        confidence=0.8,
    )
    result = await executor.execute(mock_page, plan)
    assert result.success is True
    mock_page.mouse.wheel.assert_called_once_with(0, 400)


@pytest.mark.asyncio
async def test_scroll_up(executor, mock_page):
    plan = ActionPlan(
        action_type="scroll_up",
        reasoning="Scroll back up",
        confidence=0.7,
    )
    result = await executor.execute(mock_page, plan)
    assert result.success is True
    mock_page.mouse.wheel.assert_called_once_with(0, -400)


@pytest.mark.asyncio
async def test_press_key(executor, mock_page):
    plan = ActionPlan(
        action_type="press_key",
        key="Escape",
        reasoning="Dismiss modal",
        confidence=0.9,
    )
    result = await executor.execute(mock_page, plan)
    assert result.success is True
    mock_page.keyboard.press.assert_called_once_with("Escape")


@pytest.mark.asyncio
async def test_press_key_without_key(executor, mock_page):
    plan = ActionPlan(
        action_type="press_key",
        reasoning="Press key without specifying which",
        confidence=0.5,
    )
    result = await executor.execute(mock_page, plan)
    assert result.success is True
    mock_page.keyboard.press.assert_not_called()


@pytest.mark.asyncio
async def test_hover(executor, mock_page):
    plan = ActionPlan(
        action_type="hover",
        coordinates=(300, 400),
        reasoning="Hover over menu",
        confidence=0.85,
    )
    result = await executor.execute(mock_page, plan)
    assert result.success is True
    mock_page.mouse.move.assert_called_once_with(300, 400)


@pytest.mark.asyncio
async def test_wait_action(executor, mock_page):
    plan = ActionPlan(
        action_type="wait",
        seconds=1,
        reasoning="Wait for page load",
        confidence=0.7,
    )
    result = await executor.execute(mock_page, plan)
    assert result.success is True


@pytest.mark.asyncio
async def test_go_back(executor, mock_page):
    plan = ActionPlan(
        action_type="go_back",
        reasoning="Return to previous page",
        confidence=0.8,
    )
    result = await executor.execute(mock_page, plan)
    assert result.success is True
    mock_page.go_back.assert_called_once()


@pytest.mark.asyncio
async def test_done_action(executor, mock_page):
    plan = ActionPlan(
        action_type="done",
        reasoning="Goal achieved",
        confidence=1.0,
    )
    result = await executor.execute(mock_page, plan)
    assert result.success is True


@pytest.mark.asyncio
async def test_action_failure_returns_error(executor, mock_page):
    mock_page.mouse.click.side_effect = Exception("Element detached")
    plan = ActionPlan(
        action_type="click",
        coordinates=(50, 50),
        reasoning="Click button",
        confidence=0.9,
    )
    result = await executor.execute(mock_page, plan)
    assert result.success is False
    assert "Element detached" in result.error


@pytest.mark.asyncio
async def test_action_result_includes_url(executor, mock_page):
    mock_page.url = "https://example.com/new-page"
    plan = ActionPlan(
        action_type="scroll_down",
        reasoning="Scroll",
        confidence=0.8,
    )
    result = await executor.execute(mock_page, plan)
    assert result.url_after == "https://example.com/new-page"


# ─── Screenshot Tests ───


@pytest.mark.asyncio
async def test_take_screenshot(executor, mock_page):
    result = await executor.take_screenshot(mock_page)
    assert isinstance(result, str)
    # Verify it's valid base64
    decoded = base64.b64decode(result)
    assert decoded.startswith(b"\x89PNG")


# ─── Cookie Consent Dismissal Tests ───


@pytest.mark.asyncio
async def test_cookie_consent_main_page_found(executor, mock_page):
    """Cookie consent found on main page via JS evaluation."""
    mock_page.evaluate = AsyncMock(return_value="Accept All")
    result = await executor.dismiss_cookie_consent(mock_page)
    assert result is True


@pytest.mark.asyncio
async def test_cookie_consent_not_found(executor, mock_page):
    """No cookie consent banner on the page."""
    mock_page.evaluate = AsyncMock(return_value=None)
    # Make get_by_role return a mock with count() = 0
    mock_btn = AsyncMock()
    mock_btn.count = AsyncMock(return_value=0)
    mock_page.get_by_role = MagicMock(return_value=mock_btn)
    result = await executor.dismiss_cookie_consent(mock_page)
    assert result is False


@pytest.mark.asyncio
async def test_cookie_consent_found_in_iframe(executor, mock_page):
    """Cookie consent found inside an iframe."""
    mock_page.evaluate = AsyncMock(return_value=None)
    mock_iframe = AsyncMock()
    mock_iframe.evaluate = AsyncMock(return_value="I agree")
    mock_page.frames = [mock_page.main_frame, mock_iframe]
    # Make get_by_role return a mock with count() = 0
    mock_btn = AsyncMock()
    mock_btn.count = AsyncMock(return_value=0)
    mock_page.get_by_role = MagicMock(return_value=mock_btn)
    result = await executor.dismiss_cookie_consent(mock_page)
    assert result is True


@pytest.mark.asyncio
async def test_cookie_consent_via_playwright_locator(executor, mock_page):
    """Cookie consent found via Playwright get_by_role fallback."""
    mock_page.evaluate = AsyncMock(return_value=None)
    mock_btn = AsyncMock()
    mock_btn.count = AsyncMock(return_value=1)
    mock_btn.first = AsyncMock()
    mock_btn.first.click = AsyncMock()
    mock_page.get_by_role = MagicMock(return_value=mock_btn)
    result = await executor.dismiss_cookie_consent(mock_page)
    assert result is True


@pytest.mark.asyncio
async def test_cookie_consent_handles_errors_gracefully(executor, mock_page):
    """Errors during cookie dismissal don't crash the agent."""
    mock_page.evaluate = AsyncMock(side_effect=Exception("Page crashed"))
    result = await executor.dismiss_cookie_consent(mock_page)
    assert result is False
