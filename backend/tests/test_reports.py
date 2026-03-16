from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_get_report_not_found(client):
    response = await client.get("/api/reports/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_report_session_not_completed(client):
    """Report should return 400 if session exists but hasn't completed."""
    create_res = await client.post(
        "/api/sessions",
        json={"url": "https://example.com", "goal": "test"},
    )
    session_id = create_res.json()["id"]
    response = await client.get(f"/api/reports/{session_id}")
    assert response.status_code == 400
    assert "created" in response.json()["detail"]
