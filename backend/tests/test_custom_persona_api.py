"""Tests for custom persona API endpoint and CSV export."""

from __future__ import annotations

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.agent.persona_engine import PERSONAS


class TestCustomPersonaEndpoint:
    @pytest.mark.asyncio
    async def test_create_custom_persona(self, client):
        resp = await client.post(
            "/api/personas/custom",
            json={
                "name": "Elderly User",
                "description": "Senior citizen with low vision needs",
                "behavioral_traits": ["Needs large text", "Slow reader"],
                "focus_areas": ["contrast", "affordance"],
                "custom_instructions": "Focus on readability",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["key"].startswith("custom_")
        assert data["name"] == "Elderly User"

        # Clean up
        PERSONAS.pop(data["key"], None)

    @pytest.mark.asyncio
    async def test_create_persona_missing_name(self, client):
        resp = await client.post(
            "/api/personas/custom",
            json={
                "name": "",
                "description": "Test",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_persona_missing_description(self, client):
        resp = await client.post(
            "/api/personas/custom",
            json={
                "name": "Test",
                "description": "",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_custom_persona_appears_in_list(self, client):
        await client.post(
            "/api/personas/custom",
            json={
                "name": "API Test Persona",
                "description": "Created via API test",
                "behavioral_traits": [],
                "focus_areas": [],
            },
        )
        resp = await client.get("/api/personas")
        assert resp.status_code == 200
        keys = [p["key"] for p in resp.json()]
        assert "custom_api_test_persona" in keys

        # Clean up
        PERSONAS.pop("custom_api_test_persona", None)


class TestCSVExport:
    @pytest.mark.asyncio
    async def test_csv_export_not_found(self, client):
        resp = await client.get("/api/reports/nonexistent/csv")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_csv_export_not_completed(self, client):
        # Create a session
        resp = await client.post(
            "/api/sessions",
            json={"url": "https://example.com", "goal": "Test goal"},
        )
        session_id = resp.json()["id"]

        resp = await client.get(f"/api/reports/{session_id}/csv")
        # Should fail because session not completed (no report)
        assert resp.status_code in (400, 404)
