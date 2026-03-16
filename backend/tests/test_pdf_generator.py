"""Tests for PDF report generation."""

from __future__ import annotations

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schemas.report import (
    ErrorClassification,
    FrictionItem,
    FrictionReport,
    StepSummary,
)
from services.reporting.pdf_generator import generate_pdf


def _make_report(**kwargs) -> FrictionReport:
    """Build a FrictionReport with sensible defaults, overridable via kwargs."""
    defaults = dict(
        session_id="test-session-123",
        url="https://example.com",
        goal="Find the pricing page",
        persona="Impatient User",
        status="completed",
        total_steps=5,
        total_time_seconds=42.3,
        friction_score=55.0,
        ux_risk_index=62.0,
        executive_summary="The website has moderate friction. Navigation is confusing and key CTAs are hard to find.",
        improvement_priorities=[
            "Improve main navigation labels",
            "Increase CTA button contrast",
            "Add breadcrumbs for orientation",
        ],
        friction_items=[
            FrictionItem(
                category="navigation",
                description="Main menu labels are ambiguous",
                severity="high",
                evidence_step=2,
                improvement_suggestion="Use clearer, action-oriented labels",
            ),
            FrictionItem(
                category="contrast",
                description="CTA button has low contrast ratio (2.1:1)",
                severity="critical",
                evidence_step=3,
                improvement_suggestion="Increase contrast to at least 4.5:1",
            ),
            FrictionItem(
                category="affordance",
                description="Clickable card doesn't look interactive",
                severity="medium",
                evidence_step=4,
                improvement_suggestion="Add hover effect and cursor pointer",
            ),
        ],
        step_timeline=[
            StepSummary(
                step_number=1,
                action_type="click",
                target="Navigation menu",
                reasoning="Open the main navigation",
                confidence=0.9,
            ),
            StepSummary(
                step_number=2,
                action_type="click",
                target="Pricing link",
                reasoning="Navigate to pricing page",
                friction_detected=["ambiguous label"],
                confidence=0.7,
            ),
        ],
        error_classification=ErrorClassification(error_type="none"),
    )
    defaults.update(kwargs)
    return FrictionReport(**defaults)


class TestPDFGeneration:
    def test_generates_valid_pdf_bytes(self):
        report = _make_report()
        pdf_bytes = generate_pdf(report)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000  # Non-trivial PDF
        assert pdf_bytes[:5] == b"%PDF-"  # Valid PDF header

    def test_empty_friction_items(self):
        """PDF should still generate when there are no friction items."""
        report = _make_report(friction_items=[], friction_score=0.0, ux_risk_index=0.0)
        pdf_bytes = generate_pdf(report)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_critical_severity_report(self):
        """PDF with all critical items should generate."""
        items = [
            FrictionItem(
                category="accessibility",
                description=f"Issue {i}",
                severity="critical",
                evidence_step=i,
            )
            for i in range(1, 6)
        ]
        report = _make_report(friction_items=items, friction_score=95.0, ux_risk_index=92.0)
        pdf_bytes = generate_pdf(report)
        assert pdf_bytes[:5] == b"%PDF-"
        assert len(pdf_bytes) > 2000

    def test_with_error_classification(self):
        """PDF should include error classification section."""
        report = _make_report(
            error_classification=ErrorClassification(
                error_type="login_wall",
                details="Login required to proceed past this page",
                recoverable=False,
            )
        )
        pdf_bytes = generate_pdf(report)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_no_executive_summary(self):
        """PDF should generate even without executive summary."""
        report = _make_report(executive_summary="", improvement_priorities=[])
        pdf_bytes = generate_pdf(report)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_long_descriptions(self):
        """PDF handles long text without breaking layout."""
        long_text = "This is a very long description. " * 20
        items = [
            FrictionItem(
                category="copy",
                description=long_text,
                severity="medium",
                evidence_step=1,
                improvement_suggestion=long_text,
            )
        ]
        report = _make_report(friction_items=items, executive_summary=long_text)
        pdf_bytes = generate_pdf(report)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_all_severity_levels(self):
        """PDF should handle all four severity levels."""
        items = [
            FrictionItem(category="navigation", description=f"{sev} issue", severity=sev, evidence_step=i + 1)
            for i, sev in enumerate(["critical", "high", "medium", "low"])
        ]
        report = _make_report(friction_items=items)
        pdf_bytes = generate_pdf(report)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_empty_step_timeline(self):
        """PDF should generate with no step timeline."""
        report = _make_report(step_timeline=[])
        pdf_bytes = generate_pdf(report)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_many_friction_items(self):
        """PDF should handle a large number of friction items (multi-page)."""
        items = [
            FrictionItem(
                category="navigation",
                description=f"Friction item number {i}",
                severity=["low", "medium", "high", "critical"][i % 4],
                evidence_step=i + 1,
                improvement_suggestion=f"Fix issue number {i}",
            )
            for i in range(20)
        ]
        report = _make_report(friction_items=items)
        pdf_bytes = generate_pdf(report)
        assert pdf_bytes[:5] == b"%PDF-"
        # Should be larger since it has many items
        assert len(pdf_bytes) > 5000
