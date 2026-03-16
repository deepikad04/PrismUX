"""Tests for SafetyGuard — payment, destructive, captcha, login wall detection."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schemas.navigation import ActionPlan
from services.browser.safety import SafetyGuard


def _make_plan(
    target: str = "button",
    reasoning: str = "Clicking to proceed",
) -> ActionPlan:
    return ActionPlan(
        action_type="click",
        target_element=target,
        reasoning=reasoning,
        confidence=0.9,
        candidates=[],
    )


class TestPaymentDetection:
    def setup_method(self):
        self.guard = SafetyGuard()

    def test_checkout_url(self):
        plan = _make_plan()
        stop, reason = self.guard.should_stop(plan, "https://shop.com/checkout")
        assert stop is True
        assert "payment" in reason.lower() or "checkout" in reason.lower()

    def test_payment_in_target(self):
        plan = _make_plan(target="Credit Card Payment")
        stop, _ = self.guard.should_stop(plan, "https://shop.com/cart")
        assert stop is True

    def test_billing_page(self):
        plan = _make_plan(reasoning="Entering billing info")
        stop, _ = self.guard.should_stop(plan, "https://shop.com/billing")
        assert stop is True


class TestDestructiveDetection:
    def setup_method(self):
        self.guard = SafetyGuard()

    def test_delete_account(self):
        plan = _make_plan(reasoning="Click to delete account")
        stop, reason = self.guard.should_stop(plan, "https://example.com/settings")
        assert stop is True
        assert "destructive" in reason.lower()

    def test_cancel_subscription(self):
        plan = _make_plan(target="Cancel Subscription button")
        stop, _ = self.guard.should_stop(plan, "https://example.com")
        assert stop is True

    def test_unsubscribe(self):
        plan = _make_plan(reasoning="Click unsubscribe link")
        stop, _ = self.guard.should_stop(plan, "https://example.com")
        assert stop is True


class TestCaptchaDetection:
    def setup_method(self):
        self.guard = SafetyGuard()

    def test_recaptcha_in_page(self):
        plan = _make_plan()
        stop, reason = self.guard.should_stop(
            plan, "https://example.com", page_text="Please complete the recaptcha"
        )
        assert stop is True
        assert "captcha" in reason.lower()

    def test_human_verification(self):
        plan = _make_plan()
        stop, _ = self.guard.should_stop(
            plan, "https://example.com", page_text="Verify you are human"
        )
        assert stop is True


class TestLoginWallDetection:
    def setup_method(self):
        self.guard = SafetyGuard()

    def test_sign_in_to_continue(self):
        plan = _make_plan()
        stop, reason = self.guard.should_stop(
            plan, "https://example.com", page_text="Sign in to continue"
        )
        assert stop is True
        assert "login" in reason.lower()

    def test_register_to_continue(self):
        plan = _make_plan()
        stop, _ = self.guard.should_stop(
            plan, "https://example.com", page_text="Register to continue using"
        )
        assert stop is True


class TestSafePaths:
    def setup_method(self):
        self.guard = SafetyGuard()

    def test_normal_navigation(self):
        plan = _make_plan(target="About Us", reasoning="Navigating to about page")
        stop, _ = self.guard.should_stop(plan, "https://example.com/about")
        assert stop is False

    def test_form_submission(self):
        plan = _make_plan(target="Search button", reasoning="Searching for products")
        stop, _ = self.guard.should_stop(plan, "https://example.com/search")
        assert stop is False
