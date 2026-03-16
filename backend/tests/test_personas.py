from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_list_personas(client):
    response = await client.get("/api/personas")
    assert response.status_code == 200
    personas = response.json()
    assert isinstance(personas, list)
    assert len(personas) >= 4

    keys = {p["key"] for p in personas}
    assert "impatient" in keys
    assert "cautious" in keys
    assert "accessibility" in keys
    assert "non_native_english" in keys

    # Verify schema
    for p in personas:
        assert "key" in p
        assert "name" in p
        assert "description" in p
