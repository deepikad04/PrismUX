"""Tests for GeminiVisionService — JSON parsing, retry logic, error handling."""

from __future__ import annotations

import json
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── JSON Extraction Tests ───


class TestExtractJson:
    """Test _extract_json method — handles raw JSON and markdown code blocks."""

    @pytest.fixture
    def service(self):
        with patch("services.gemini.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                gemini_api_key="test-key",
                gemini_perception_model="gemini-2.0-flash",
                gemini_evaluation_model="gemini-2.0-flash",
                gemini_report_model="gemini-2.5-pro",
                gemini_max_retries=3,
                gemini_timeout_seconds=30,
            )
            with patch("services.gemini.client.genai"):
                from services.gemini.client import GeminiVisionService
                return GeminiVisionService()

    def test_plain_json(self, service):
        result = service._extract_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_with_whitespace(self, service):
        result = service._extract_json('  \n {"key": "value"} \n  ')
        assert result == {"key": "value"}

    def test_json_in_code_block(self, service):
        text = '```json\n{"key": "value"}\n```'
        result = service._extract_json(text)
        assert result == {"key": "value"}

    def test_json_in_plain_code_block(self, service):
        text = '```\n{"key": "value"}\n```'
        result = service._extract_json(text)
        assert result == {"key": "value"}

    def test_nested_json(self, service):
        data = {"perception": {"page_description": "A login page"}, "action": {"action_type": "click"}}
        result = service._extract_json(json.dumps(data))
        assert result["perception"]["page_description"] == "A login page"

    def test_invalid_json_raises(self, service):
        with pytest.raises(json.JSONDecodeError):
            service._extract_json("not json at all")

    def test_empty_string_raises(self, service):
        with pytest.raises(json.JSONDecodeError):
            service._extract_json("")


# ─── Perception Parsing Tests ───


class TestParsePerception:
    @pytest.fixture
    def service(self):
        with patch("services.gemini.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                gemini_api_key="test-key",
                gemini_perception_model="gemini-2.0-flash",
                gemini_evaluation_model="gemini-2.0-flash",
                gemini_report_model="gemini-2.5-pro",
                gemini_max_retries=3,
                gemini_timeout_seconds=30,
            )
            with patch("services.gemini.client.genai"):
                from services.gemini.client import GeminiVisionService
                return GeminiVisionService()

    def test_parse_valid_perception(self, service):
        raw = {
            "perception": {
                "page_description": "A product listing page",
                "page_purpose": "E-commerce",
                "has_modal_or_overlay": False,
                "loading_state": False,
                "elements": [
                    {
                        "label": "Add to Cart",
                        "element_type": "button",
                        "bbox": {"x": 100, "y": 200, "width": 80, "height": 30},
                        "confidence": 0.95,
                        "interactable": True,
                    }
                ],
            }
        }
        result = service._parse_perception(raw)
        assert result.page_description == "A product listing page"
        assert len(result.elements) == 1
        assert result.elements[0].label == "Add to Cart"

    def test_parse_perception_missing_data(self, service):
        """Should return fallback PerceptionResult on invalid data."""
        raw = {"perception": {"invalid_field": True}}
        result = service._parse_perception(raw)
        assert result.page_description == "Parse error"

    def test_parse_perception_no_key(self, service):
        """If 'perception' key missing, try parsing raw dict directly."""
        raw = {"page_description": "Direct parse", "elements": []}
        result = service._parse_perception(raw)
        assert result.page_description == "Direct parse"


# ─── Action Parsing Tests ───


class TestParseAction:
    @pytest.fixture
    def service(self):
        with patch("services.gemini.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                gemini_api_key="test-key",
                gemini_perception_model="gemini-2.0-flash",
                gemini_evaluation_model="gemini-2.0-flash",
                gemini_report_model="gemini-2.5-pro",
                gemini_max_retries=3,
                gemini_timeout_seconds=30,
            )
            with patch("services.gemini.client.genai"):
                from services.gemini.client import GeminiVisionService
                return GeminiVisionService()

    def test_parse_click_action(self, service):
        raw = {
            "action": {
                "action_type": "click",
                "target_element": "Sign In button",
                "coordinates": [480, 320],
                "reasoning": "Click the sign in button to proceed",
                "confidence": 0.92,
                "candidates": [
                    {
                        "label": "Sign In",
                        "bbox": {"x": 440, "y": 300, "width": 80, "height": 40},
                        "confidence": 0.92,
                        "is_chosen": True,
                    },
                    {
                        "label": "Register",
                        "bbox": {"x": 540, "y": 300, "width": 80, "height": 40},
                        "confidence": 0.6,
                        "is_chosen": False,
                    },
                ],
            }
        }
        result = service._parse_action(raw)
        assert result.action_type == "click"
        assert result.coordinates == (480, 320)
        assert len(result.candidates) == 2
        assert result.candidates[0].is_chosen is True

    def test_parse_action_invalid_coordinates(self, service):
        """Invalid coordinates should be set to None."""
        raw = {
            "action": {
                "action_type": "click",
                "coordinates": [100],  # Too few values
                "reasoning": "Click something",
                "confidence": 0.8,
            }
        }
        result = service._parse_action(raw)
        assert result.coordinates is None

    def test_parse_action_fallback_on_error(self, service):
        """Should return safe fallback on parse error."""
        raw = {"action": {"bad_field": True}}
        result = service._parse_action(raw)
        assert result.action_type == "wait"
        assert result.confidence == 0.1

    def test_parse_scroll_action(self, service):
        raw = {
            "action": {
                "action_type": "scroll_down",
                "reasoning": "Need to see more content",
                "confidence": 0.75,
            }
        }
        result = service._parse_action(raw)
        assert result.action_type == "scroll_down"
        assert result.coordinates is None

    def test_parse_type_action(self, service):
        raw = {
            "action": {
                "action_type": "type",
                "input_text": "test@example.com",
                "reasoning": "Enter email address",
                "confidence": 0.88,
            }
        }
        result = service._parse_action(raw)
        assert result.action_type == "type"
        assert result.input_text == "test@example.com"


# ─── Retry / Error Handling Tests ───


class TestCallGemini:
    @pytest.fixture
    def service(self):
        with patch("services.gemini.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                gemini_api_key="test-key",
                gemini_perception_model="gemini-2.0-flash",
                gemini_evaluation_model="gemini-2.0-flash",
                gemini_report_model="gemini-2.5-pro",
                gemini_max_retries=2,
                gemini_timeout_seconds=5,
            )
            with patch("services.gemini.client.genai"):
                from services.gemini.client import GeminiVisionService
                svc = GeminiVisionService()
                return svc

    @pytest.mark.asyncio
    async def test_successful_call(self, service):
        mock_response = MagicMock()
        mock_response.text = '{"result": "ok"}'
        service._generate = AsyncMock(return_value=mock_response)

        result = await service._call_gemini("model", ["test"], None, "test")
        assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_retry_on_json_error_then_succeed(self, service):
        """First call returns bad JSON, repair retry succeeds."""
        bad_response = MagicMock()
        bad_response.text = "not json"
        good_response = MagicMock()
        good_response.text = '{"result": "fixed"}'
        service._generate = AsyncMock(side_effect=[bad_response, good_response])

        result = await service._call_gemini("model", ["test"], None, "test")
        assert result == {"result": "fixed"}
        assert service._generate.call_count == 2

    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self, service):
        """All retries fail — raises RuntimeError."""
        bad_response = MagicMock()
        bad_response.text = "not json"
        service._generate = AsyncMock(return_value=bad_response)

        with pytest.raises(RuntimeError, match="failed after 2 attempts"):
            await service._call_gemini("model", ["test"], None, "test")

    @pytest.mark.asyncio
    async def test_empty_response_retries(self, service):
        """Empty response triggers retry."""
        empty_response = MagicMock()
        empty_response.text = ""
        good_response = MagicMock()
        good_response.text = '{"ok": true}'
        service._generate = AsyncMock(side_effect=[empty_response, good_response])

        result = await service._call_gemini("model", ["test"], None, "test")
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_timeout_retries(self, service):
        """Timeout triggers retry with backoff."""
        import asyncio

        good_response = MagicMock()
        good_response.text = '{"ok": true}'
        service._generate = AsyncMock(
            side_effect=[asyncio.TimeoutError(), good_response]
        )

        # Patch sleep to speed up test
        with patch("services.gemini.client.asyncio.sleep", new_callable=AsyncMock):
            result = await service._call_gemini("model", ["test"], None, "test")
            assert result == {"ok": True}
