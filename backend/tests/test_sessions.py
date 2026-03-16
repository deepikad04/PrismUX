from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_create_session(client):
    response = await client.post(
        "/api/sessions",
        json={"url": "https://example.com", "goal": "Find pricing"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["url"] == "https://example.com"
    assert data["goal"] == "Find pricing"
    assert data["status"] == "created"
    assert data["total_steps"] == 0
    assert data["completed"] is False


@pytest.mark.asyncio
async def test_create_session_with_persona(client):
    response = await client.post(
        "/api/sessions",
        json={
            "url": "https://example.com",
            "goal": "Sign up",
            "persona": "impatient",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["persona"] == "impatient"


@pytest.mark.asyncio
async def test_list_sessions_empty(client):
    response = await client.get("/api/sessions")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_sessions(client):
    await client.post(
        "/api/sessions",
        json={"url": "https://a.com", "goal": "test"},
    )
    await client.post(
        "/api/sessions",
        json={"url": "https://b.com", "goal": "test2"},
    )
    response = await client.get("/api/sessions")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_session(client):
    create_res = await client.post(
        "/api/sessions",
        json={"url": "https://example.com", "goal": "Find pricing"},
    )
    session_id = create_res.json()["id"]
    response = await client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["id"] == session_id


@pytest.mark.asyncio
async def test_get_session_not_found(client):
    response = await client.get("/api/sessions/nonexistent")
    assert response.status_code == 404
