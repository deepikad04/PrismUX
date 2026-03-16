"""Tests for FrictionAnalyzer — categorization, severity, scoring, and error classification."""

from __future__ import annotations

import sys
import os
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schemas.navigation import (
    ActionPlan,
    ActionResult,
    CategorizedFriction,
    EvaluationResult,
    NavigationStep,
    PerceptionResult,
)
from schemas.report import ErrorClassification
from services.reporting.friction_analyzer import FrictionAnalyzer


def _make_step(
    step_number: int = 1,
    friction_detected: list[str] | None = None,
    friction_items: list[CategorizedFriction] | None = None,
    progress_made: bool = True,
    description: str = "Clicked button",
    is_recovery: bool = False,
    recovery_reason: str | None = None,
    confidence: float = 0.8,
    action_type: str = "click",
    url_after: str = "https://example.com",
) -> NavigationStep:
    return NavigationStep(
        step_number=step_number,
        perception=PerceptionResult(page_description="A web page"),
        plan=ActionPlan(
            action_type=action_type,
            target_element="button",
            reasoning="Clicking to proceed",
            confidence=confidence,
            candidates=[],
        ),
        action_result=ActionResult(success=True, url_after=url_after),
        evaluation=EvaluationResult(
            progress_made=progress_made,
            goal_achieved=False,
            description=description,
            friction_detected=friction_detected or [],
            friction_items=friction_items or [],
            confidence=0.9,
        ),
        is_recovery=is_recovery,
        recovery_reason=recovery_reason,
    )


class TestCategorize:
    """Test keyword-based friction categorization."""

    def setup_method(self):
        self.analyzer = FrictionAnalyzer()

    def test_performance_keywords(self):
        assert self.analyzer._categorize("Page loading is slow") == "performance"
        assert self.analyzer._categorize("Long delay before response") == "performance"

    def test_navigation_keywords(self):
        assert self.analyzer._categorize("Confusing navigation menu") == "navigation"
        assert self.analyzer._categorize("Unclear where to go next") == "navigation"

    def test_contrast_keywords(self):
        assert self.analyzer._categorize("Low contrast text") == "contrast"
        assert self.analyzer._categorize("Hard to read color") == "contrast"

    def test_affordance_keywords(self):
        assert self.analyzer._categorize("Small tap target") == "affordance"
        assert self.analyzer._categorize("Hard to click button") == "affordance"

    def test_copy_keywords(self):
        assert self.analyzer._categorize("Ambiguous label text") == "copy"
        assert self.analyzer._categorize("Jargon-heavy language") == "copy"

    def test_accessibility_keywords(self):
        assert self.analyzer._categorize("No aria support on page") == "accessibility"
        assert self.analyzer._categorize("No keyboard focus") == "accessibility"

    def test_error_keywords(self):
        assert self.analyzer._categorize("Broken link on page") == "error"
        assert self.analyzer._categorize("Form submission failed") == "error"

    def test_default_category(self):
        assert self.analyzer._categorize("Something weird happened") == "navigation"


class TestScoreSeverity:
    """Test severity scoring logic."""

    def setup_method(self):
        self.analyzer = FrictionAnalyzer()

    def test_critical_keywords(self):
        assert self.analyzer._score_severity("Cannot proceed, blocked", 5, 10) == "critical"
        assert self.analyzer._score_severity("Impossible to find", 5, 10) == "critical"

    def test_high_keywords(self):
        assert self.analyzer._score_severity("Confusing layout", 5, 10) == "high"
        assert self.analyzer._score_severity("Missing label", 5, 10) == "high"

    def test_early_step_high(self):
        assert self.analyzer._score_severity("Some issue", 1, 10) == "high"
        assert self.analyzer._score_severity("Some issue", 2, 10) == "high"

    def test_low_keywords(self):
        assert self.analyzer._score_severity("Minor slow loading", 5, 10) == "low"

    def test_default_medium(self):
        assert self.analyzer._score_severity("Generic friction point", 5, 10) == "medium"


class TestComputeFrictionScore:
    """Test friction score computation."""

    def setup_method(self):
        self.analyzer = FrictionAnalyzer()

    def test_zero_steps(self):
        assert self.analyzer._compute_friction_score([], 0, "completed") == 0.0

    def test_no_friction(self):
        assert self.analyzer._compute_friction_score([], 5, "completed") == 0.0

    def test_severity_weighting(self):
        from schemas.report import FrictionItem

        items = [
            FrictionItem(category="nav", description="test", severity="critical", evidence_step=1),
            FrictionItem(category="nav", description="test", severity="low", evidence_step=2),
        ]
        score = self.analyzer._compute_friction_score(items, 5, "completed")
        assert score > 0

    def test_abandoned_boost(self):
        from schemas.report import FrictionItem

        items = [FrictionItem(category="nav", description="test", severity="medium", evidence_step=1)]
        score_completed = self.analyzer._compute_friction_score(items, 5, "completed")
        score_abandoned = self.analyzer._compute_friction_score(items, 5, "abandoned")
        assert score_abandoned > score_completed

    def test_score_capped_at_100(self):
        from schemas.report import FrictionItem

        items = [
            FrictionItem(category="nav", description="test", severity="critical", evidence_step=i)
            for i in range(50)
        ]
        score = self.analyzer._compute_friction_score(items, 1, "error")
        assert score <= 100


class TestClassifyError:
    """Test error classification logic."""

    def setup_method(self):
        self.analyzer = FrictionAnalyzer()

    def test_completed_no_error(self):
        result = self.analyzer._classify_error("completed", [])
        assert result.error_type == "none"

    def test_network_error(self):
        step = _make_step(description="net::err_connection_refused")
        result = self.analyzer._classify_error("error", [step])
        assert result.error_type == "network"
        assert result.recoverable is True

    def test_timeout_error(self):
        step = _make_step(description="Page timed out loading")
        result = self.analyzer._classify_error("error", [step])
        assert result.error_type == "timeout"

    def test_login_wall(self):
        step = _make_step(description="Please login to continue")
        result = self.analyzer._classify_error("error", [step])
        assert result.error_type == "login_wall"
        assert result.recoverable is False

    def test_safety_blocked(self):
        result = self.analyzer._classify_error("blocked", [])
        assert result.error_type == "safety"
        assert result.recoverable is False

    def test_abandoned(self):
        step = _make_step(description="Could not proceed")
        result = self.analyzer._classify_error("abandoned", [step])
        assert result.error_type == "blocked"

    def test_unknown_error(self):
        step = _make_step(description="Something happened")
        result = self.analyzer._classify_error("error", [step])
        assert result.error_type == "unknown"


class TestAnalyze:
    """Test the full analyze pipeline."""

    def setup_method(self):
        self.analyzer = FrictionAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_with_structured_friction(self):
        """Test analyze uses structured friction_items when available."""
        friction = CategorizedFriction(
            category="affordance",
            description="Tiny button",
            severity="high",
        )
        steps = [_make_step(friction_items=[friction])]

        with patch("services.reporting.friction_analyzer.GeminiVisionService") as mock_cls:
            mock_gemini = AsyncMock()
            mock_gemini.generate_report_summary = AsyncMock(return_value={
                "executive_summary": "Test summary",
                "improvement_priorities": ["Fix buttons"],
                "item_suggestions": [],
            })
            mock_cls.return_value = mock_gemini

            report = await self.analyzer.analyze(
                session_id="test-123",
                url="https://example.com",
                goal="Find info",
                persona=None,
                status="completed",
                steps=steps,
                elapsed_seconds=10.0,
            )

        assert report.session_id == "test-123"
        assert len(report.friction_items) == 1
        assert report.friction_items[0].category == "affordance"
        assert report.total_steps == 1

    @pytest.mark.asyncio
    async def test_analyze_fallback_text_friction(self):
        """Test analyze falls back to text categorization without structured items."""
        steps = [_make_step(friction_detected=["Slow loading page"])]

        with patch("services.reporting.friction_analyzer.GeminiVisionService") as mock_cls:
            mock_gemini = AsyncMock()
            mock_gemini.generate_report_summary = AsyncMock(return_value={
                "executive_summary": "Summary",
                "improvement_priorities": [],
                "item_suggestions": [],
            })
            mock_cls.return_value = mock_gemini

            report = await self.analyzer.analyze(
                session_id="test-456",
                url="https://example.com",
                goal="Buy item",
                persona="impatient",
                status="completed",
                steps=steps,
                elapsed_seconds=5.0,
            )

        assert len(report.friction_items) == 1
        assert report.friction_items[0].category == "performance"
        assert report.friction_items[0].persona_impacted == "impatient"

    @pytest.mark.asyncio
    async def test_analyze_gemini_failure_fallback(self):
        """Test analyze handles Gemini failure gracefully."""
        steps = [_make_step()]

        with patch("services.reporting.friction_analyzer.GeminiVisionService") as mock_cls:
            mock_cls.return_value.generate_report_summary = AsyncMock(
                side_effect=Exception("API error")
            )

            report = await self.analyzer.analyze(
                session_id="test-789",
                url="https://example.com",
                goal="Navigate",
                persona=None,
                status="completed",
                steps=steps,
                elapsed_seconds=3.0,
            )

        assert "completed" in report.executive_summary.lower()
        assert report.total_steps == 1
