"""Integration tests for the navigator API — session lifecycle, hints, capacity."""

from __future__ import annotations

import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest_asyncio.fixture
async def client():
    """Async test client with mocked browser manager."""
    mock_mgr = MagicMock()
    mock_mgr.start = AsyncMock()
    mock_mgr.shutdown = AsyncMock()
    mock_mgr.active_sessions = 0

    with patch("services.browser.manager.get_browser_manager", return_value=mock_mgr), \
         patch("routers.navigator.get_browser_manager", return_value=mock_mgr):
        from config import get_settings
        get_settings.cache_clear()

        from main import app

        from routers.sessions import sessions
        from routers.navigator import active_agents
        from routers.reports import reports
        sessions.clear()
        active_agents.clear()
        reports.clear()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


async def _create_session(client: AsyncClient, url: str = "https://example.com", goal: str = "Find pricing") -> str:
    resp = await client.post("/api/sessions", json={"url": url, "goal": goal})
    assert resp.status_code == 200
    return resp.json()["id"]


# ─── Session Lifecycle ───


class TestSessionLifecycle:
    @pytest.mark.asyncio
    async def test_create_session(self, client):
        resp = await client.post(
            "/api/sessions",
            json={"url": "https://example.com", "goal": "Find pricing"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["url"] == "https://example.com"
        assert data["goal"] == "Find pricing"
        assert data["status"] == "created"

    @pytest.mark.asyncio
    async def test_create_session_with_persona(self, client):
        resp = await client.post(
            "/api/sessions",
            json={
                "url": "https://example.com",
                "goal": "Check accessibility",
                "persona": "accessibility",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["persona"] == "accessibility"

    @pytest.mark.asyncio
    async def test_create_session_missing_goal(self, client):
        resp = await client.post(
            "/api/sessions",
            json={"url": "https://example.com"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_sessions(self, client):
        await _create_session(client)
        await _create_session(client, url="https://other.com")
        resp = await client.get("/api/sessions")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @pytest.mark.asyncio
    async def test_get_session_by_id(self, client):
        sid = await _create_session(client)
        resp = await client.get(f"/api/sessions/{sid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == sid

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client):
        resp = await client.get("/api/sessions/nonexistent-id")
        assert resp.status_code == 404


# ─── Navigation API ───


class TestNavigationAPI:
    @pytest.mark.asyncio
    async def test_start_navigation_invalid_session(self, client):
        resp = await client.post("/api/navigate/nonexistent/start")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_status_invalid_session(self, client):
        resp = await client.get("/api/navigate/nonexistent/status")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_steps_invalid_session(self, client):
        resp = await client.get("/api/navigate/nonexistent/steps")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_capacity_endpoint(self, client):
        resp = await client.get("/api/navigate/capacity")
        assert resp.status_code == 200
        data = resp.json()
        assert "active" in data
        assert "max" in data
        assert "available" in data


# ─── Hint API ───


class TestHintAPI:
    @pytest.mark.asyncio
    async def test_hint_invalid_session(self, client):
        resp = await client.post(
            "/api/navigate/nonexistent/hint",
            json={"text": "Try clicking the menu"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_hint_session_not_running(self, client):
        """Hint on a session that hasn't started navigation should 404."""
        sid = await _create_session(client)
        resp = await client.post(
            f"/api/navigate/{sid}/hint",
            json={"text": "Try the menu"},
        )
        # Agent not yet started, so no active agent to receive hint
        assert resp.status_code == 404


# ─── Persona API ───


class TestPersonaAPI:
    @pytest.mark.asyncio
    async def test_list_personas(self, client):
        resp = await client.get("/api/personas")
        assert resp.status_code == 200
        personas = resp.json()
        assert isinstance(personas, list)
        assert len(personas) >= 4  # 4 built-in personas

    @pytest.mark.asyncio
    async def test_create_custom_persona(self, client):
        resp = await client.post(
            "/api/personas/custom",
            json={
                "name": "Test Persona",
                "description": "A test persona for validation",
                "behavioral_traits": ["impatient", "visual"],
                "focus_areas": ["navigation", "contrast"],
                "custom_instructions": "Focus on button visibility",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Persona"

    @pytest.mark.asyncio
    async def test_create_custom_persona_empty_name(self, client):
        resp = await client.post(
            "/api/personas/custom",
            json={
                "name": "",
                "description": "A test persona",
                "behavioral_traits": ["impatient"],
                "focus_areas": ["navigation"],
            },
        )
        assert resp.status_code == 422


# ─── Report API ───


class TestReportAPI:
    @pytest.mark.asyncio
    async def test_report_not_found(self, client):
        resp = await client.get("/api/reports/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_pdf_not_found(self, client):
        resp = await client.get("/api/reports/nonexistent/pdf")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_csv_not_found(self, client):
        resp = await client.get("/api/reports/nonexistent/csv")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_report_session_not_completed(self, client):
        sid = await _create_session(client)
        resp = await client.get(f"/api/reports/{sid}")
        assert resp.status_code == 400  # Session not completed yet
