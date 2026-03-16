from __future__ import annotations

import hashlib
import logging

from schemas.navigation import ActionPlan, NavigationStep

logger = logging.getLogger(__name__)

MAX_HISTORY = 20


class StuckDetector:
    """Detects when the agent is stuck and provides escalating recovery strategies."""

    def __init__(self, max_identical_steps: int = 3) -> None:
        self.max_identical_steps = max_identical_steps
        self.recent_urls: list[str] = []
        self.recent_actions: list[str] = []
        self.recent_screenshot_hashes: list[str] = []
        self.recovery_level = 0
        self._no_progress_count = 0

    @staticmethod
    def _hash_screenshot(screenshot_b64: str) -> str:
        """Compute a fast hash of a screenshot for visual loop detection."""
        return hashlib.md5(screenshot_b64.encode("utf-8")).hexdigest()

    def is_stuck(self, step: NavigationStep, screenshot_after_b64: str = "") -> bool:
        url = step.action_result.url_after
        action_key = f"{step.plan.action_type}:{step.plan.target_element}"

        self.recent_urls.append(url)
        self.recent_actions.append(action_key)

        # Track screenshot hashes for visual loop detection
        if screenshot_after_b64:
            sh = self._hash_screenshot(screenshot_after_b64)
            self.recent_screenshot_hashes.append(sh)
            if len(self.recent_screenshot_hashes) > MAX_HISTORY:
                self.recent_screenshot_hashes = self.recent_screenshot_hashes[-MAX_HISTORY:]

        # Cap list growth
        if len(self.recent_urls) > MAX_HISTORY:
            self.recent_urls = self.recent_urls[-MAX_HISTORY:]
        if len(self.recent_actions) > MAX_HISTORY:
            self.recent_actions = self.recent_actions[-MAX_HISTORY:]

        # Reset on progress
        if step.evaluation.progress_made:
            self.recovery_level = 0
            self._no_progress_count = 0
            return False

        # Check if URL hasn't changed for N steps
        if len(self.recent_urls) >= self.max_identical_steps:
            last_n = self.recent_urls[-self.max_identical_steps:]
            if len(set(last_n)) == 1:
                logger.info("Stuck: URL unchanged for %d steps", self.max_identical_steps)
                return True

        # Check if same action repeated
        if len(self.recent_actions) >= self.max_identical_steps:
            last_n = self.recent_actions[-self.max_identical_steps:]
            if len(set(last_n)) == 1:
                logger.info("Stuck: same action repeated %d times", self.max_identical_steps)
                return True

        # Visual loop detection: identical screenshots for N steps
        if len(self.recent_screenshot_hashes) >= self.max_identical_steps:
            last_n = self.recent_screenshot_hashes[-self.max_identical_steps:]
            if len(set(last_n)) == 1:
                logger.info("Stuck: identical screenshots for %d steps (visual loop)", self.max_identical_steps)
                return True

        # Track no-progress streaks
        if not step.evaluation.progress_made and not step.evaluation.page_changed:
            self._no_progress_count += 1
            if self._no_progress_count >= 3:
                logger.info("Stuck: no progress for %d evaluations", self._no_progress_count)
                return True

        return False

    def get_recovery_action(self) -> ActionPlan:
        """Return escalating recovery actions. Increments level each call."""
        self.recovery_level += 1
        # Reset no-progress count so stuck detection doesn't immediately re-trigger
        self._no_progress_count = 0
        level = self.recovery_level

        if level <= 1:
            return ActionPlan(
                action_type="scroll_down",
                reasoning="Recovery: scrolling down to reveal hidden content",
                confidence=0.5,
                candidates=[],
            )
        elif level == 2:
            return ActionPlan(
                action_type="scroll_up",
                reasoning="Recovery: scrolling up — target may be above the fold",
                confidence=0.5,
                candidates=[],
            )
        elif level == 3:
            return ActionPlan(
                action_type="press_key",
                key="Escape",
                reasoning="Recovery: pressing Escape to dismiss modal or popup",
                confidence=0.5,
                candidates=[],
            )
        elif level == 4:
            return ActionPlan(
                action_type="click",
                coordinates=(50, 50),
                reasoning="Recovery: clicking outside modal overlay area",
                confidence=0.4,
                candidates=[],
            )
        elif level == 5:
            return ActionPlan(
                action_type="go_back",
                reasoning="Recovery: navigating back to try alternative path",
                confidence=0.4,
                candidates=[],
            )
        elif level == 6:
            return ActionPlan(
                action_type="press_key",
                key="Tab",
                reasoning="Recovery: pressing Tab to focus next interactive element",
                confidence=0.4,
                candidates=[],
            )
        else:
            return ActionPlan(
                action_type="done",
                reasoning="Recovery exhausted: abandoning task after multiple failed attempts",
                confidence=0.2,
                candidates=[],
            )

    def reset(self) -> None:
        self.recent_urls.clear()
        self.recent_actions.clear()
        self.recovery_level = 0
        self._no_progress_count = 0
