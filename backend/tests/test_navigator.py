from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_start_navigation_not_found(client):
    response = await client.post("/api/navigate/nonexistent/start")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_navigation_status_not_found(client):
    response = await client.get("/api/navigate/nonexistent/status")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_navigation_status_created_session(client):
    """A created session without active navigation returns session status."""
    create_res = await client.post(
        "/api/sessions",
        json={"url": "https://example.com", "goal": "test"},
    )
    session_id = create_res.json()["id"]
    response = await client.get(f"/api/navigate/{session_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["status"] == "created"
