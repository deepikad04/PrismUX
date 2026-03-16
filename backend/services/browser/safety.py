from __future__ import annotations

import logging
import re

from schemas.navigation import ActionPlan

logger = logging.getLogger(__name__)

PAYMENT_PATTERNS = [
    r"checkout", r"payment", r"credit.?card", r"billing",
    r"pay\b", r"purchase", r"order.?confirm",
]

DESTRUCTIVE_PATTERNS = [
    r"delete.*account", r"remove.*data", r"unsubscribe",
    r"cancel.*subscription", r"close.*account",
]

CAPTCHA_INDICATORS = [
    "captcha", "recaptcha", "hcaptcha", "i'm not a robot",
    "verify you are human", "security check",
]

LOGIN_WALL_INDICATORS = [
    "sign in to continue", "log in to continue",
    "create an account", "register to continue",
]


class SafetyGuard:
    """Detects payment pages, destructive actions, CAPTCHAs, and login walls."""

    def should_stop(
        self,
        plan: ActionPlan,
        current_url: str,
        page_text: str = "",
    ) -> tuple[bool, str]:
        combined = f"{current_url} {plan.target_element or ''} {plan.reasoning} {page_text}".lower()

        for pattern in PAYMENT_PATTERNS:
            if re.search(pattern, combined):
                reason = f"Payment/checkout detected: matched '{pattern}'"
                logger.warning(reason)
                return True, reason

        for pattern in DESTRUCTIVE_PATTERNS:
            if re.search(pattern, combined):
                reason = f"Destructive action detected: matched '{pattern}'"
                logger.warning(reason)
                return True, reason

        for indicator in CAPTCHA_INDICATORS:
            if indicator in combined:
                reason = f"CAPTCHA detected: '{indicator}'"
                logger.warning(reason)
                return True, reason

        for indicator in LOGIN_WALL_INDICATORS:
            if indicator in combined:
                reason = f"Login wall detected: '{indicator}'"
                logger.warning(reason)
                return True, reason

        return False, ""
