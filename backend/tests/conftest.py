from __future__ import annotations

import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Ensure backend root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest_asyncio.fixture
async def client():
    """Async test client with mocked browser manager."""
    mock_mgr = AsyncMock()
    mock_mgr.start = AsyncMock()
    mock_mgr.shutdown = AsyncMock()

    with patch("services.browser.manager.get_browser_manager", return_value=mock_mgr):
        # Clear any cached settings so tests don't need a .env file
        from config import get_settings
        get_settings.cache_clear()

        from main import app

        # Clear in-memory state between tests
        from routers.sessions import sessions
        from routers.navigator import active_agents
        from routers.reports import reports
        sessions.clear()
        active_agents.clear()
        reports.clear()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
