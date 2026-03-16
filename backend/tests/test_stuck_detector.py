"""Tests for StuckDetector — loop detection, recovery escalation, and reset."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schemas.navigation import (
    ActionPlan,
    ActionResult,
    EvaluationResult,
    NavigationStep,
    PerceptionResult,
)
from services.agent.stuck_detector import StuckDetector


def _make_step(
    action_type: str = "click",
    target: str = "button",
    url_after: str = "https://example.com",
    progress_made: bool = False,
    page_changed: bool = True,
) -> NavigationStep:
    return NavigationStep(
        step_number=1,
        perception=PerceptionResult(page_description="A page"),
        plan=ActionPlan(
            action_type=action_type,
            target_element=target,
            reasoning="Test action",
            confidence=0.8,
            candidates=[],
        ),
        action_result=ActionResult(success=True, url_after=url_after),
        evaluation=EvaluationResult(
            progress_made=progress_made,
            goal_achieved=False,
            page_changed=page_changed,
            description="Test",
            confidence=0.8,
        ),
    )


class TestIsStuck:
    def test_not_stuck_with_progress(self):
        detector = StuckDetector(max_identical_steps=3)
        step = _make_step(progress_made=True)
        for _ in range(5):
            assert detector.is_stuck(step) is False

    def test_stuck_same_url(self):
        detector = StuckDetector(max_identical_steps=3)
        step = _make_step(url_after="https://example.com/stuck")
        # First 2 calls: not stuck yet
        assert detector.is_stuck(step) is False
        assert detector.is_stuck(step) is False
        # Third call: stuck
        assert detector.is_stuck(step) is True

    def test_stuck_same_action(self):
        detector = StuckDetector(max_identical_steps=3)
        step = _make_step(action_type="click", target="submit")
        # Vary URLs so URL check doesn't trigger
        step2 = _make_step(action_type="click", target="submit", url_after="https://a.com")
        step3 = _make_step(action_type="click", target="submit", url_after="https://b.com")
        detector.is_stuck(step)
        detector.is_stuck(step2)
        assert detector.is_stuck(step3) is True

    def test_stuck_identical_screenshots(self):
        detector = StuckDetector(max_identical_steps=3)
        step = _make_step(url_after="https://a.com")
        step2 = _make_step(url_after="https://b.com", action_type="scroll_down", target="page")
        step3 = _make_step(url_after="https://c.com", action_type="scroll_up", target="page")
        same_screenshot = "identical_base64_content"
        detector.is_stuck(step, same_screenshot)
        detector.is_stuck(step2, same_screenshot)
        assert detector.is_stuck(step3, same_screenshot) is True

    def test_stuck_no_progress_streak(self):
        detector = StuckDetector(max_identical_steps=5)  # high threshold to avoid URL/action triggers
        step1 = _make_step(url_after="https://a.com", action_type="click", target="a", page_changed=False)
        step2 = _make_step(url_after="https://b.com", action_type="click", target="b", page_changed=False)
        detector.is_stuck(step1)
        assert detector.is_stuck(step2) is True

    def test_progress_resets_detector(self):
        detector = StuckDetector(max_identical_steps=3)
        step_stuck = _make_step()
        detector.is_stuck(step_stuck)
        detector.is_stuck(step_stuck)
        # Progress resets everything
        step_progress = _make_step(progress_made=True)
        assert detector.is_stuck(step_progress) is False
        assert detector.recovery_level == 0


class TestRecoveryEscalation:
    def test_escalating_recovery(self):
        detector = StuckDetector()
        actions = []
        for _ in range(6):
            action = detector.get_recovery_action()
            actions.append(action.action_type)

        assert actions[0] == "scroll_down"
        assert actions[1] == "press_key"
        assert actions[2] == "click"
        assert actions[3] == "go_back"
        assert actions[4] == "done"
        assert actions[5] == "done"  # stays at done


class TestReset:
    def test_reset_clears_state(self):
        detector = StuckDetector()
        step = _make_step()
        detector.is_stuck(step)
        detector.is_stuck(step)
        detector.get_recovery_action()

        detector.reset()
        assert detector.recent_urls == []
        assert detector.recent_actions == []
        assert detector.recovery_level == 0
        assert detector._no_progress_count == 0
