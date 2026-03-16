from __future__ import annotations

import logging

from schemas.navigation import NavigationStep
from schemas.report import ErrorClassification, FrictionItem, FrictionReport, StepSummary
from services.gemini.client import GeminiVisionService

logger = logging.getLogger(__name__)

FRICTION_CATEGORIES = {
    "loading": "performance",
    "slow": "performance",
    "delay": "performance",
    "confus": "navigation",
    "unclear": "navigation",
    "where": "navigation",
    "breadcrumb": "navigation",
    "contrast": "contrast",
    "color": "contrast",
    "readable": "contrast",
    "small": "affordance",
    "tap target": "affordance",
    "click": "affordance",
    "hover": "affordance",
    "button": "affordance",
    "label": "copy",
    "jargon": "copy",
    "complex": "copy",
    "idiom": "copy",
    "ambiguous": "copy",
    "aria": "accessibility",
    "alt text": "accessibility",
    "focus": "accessibility",
    "keyboard": "accessibility",
    "screen reader": "accessibility",
    "error": "error",
    "broken": "error",
    "failed": "error",
    "trust": "navigation",
    "security": "navigation",
    "privacy": "navigation",
}


class FrictionAnalyzer:
    """Aggregates step-level friction into a ranked report."""

    async def analyze(
        self,
        session_id: str,
        url: str,
        goal: str,
        persona: str | None,
        status: str,
        steps: list[NavigationStep],
        elapsed_seconds: float,
    ) -> FrictionReport:
        # Collect all friction points
        friction_items: list[FrictionItem] = []
        step_timeline: list[StepSummary] = []

        for step in steps:
            step_timeline.append(StepSummary(
                step_number=step.step_number,
                action_type=step.plan.action_type,
                target=step.plan.target_element,
                reasoning=step.plan.reasoning,
                friction_detected=step.evaluation.friction_detected,
                confidence=step.plan.confidence,
            ))

            # Prefer structured friction_items from Gemini/persona checks
            if step.evaluation.friction_items:
                for fi in step.evaluation.friction_items:
                    friction_items.append(FrictionItem(
                        category=fi.category,
                        description=fi.description,
                        severity=fi.severity,
                        evidence_step=step.step_number,
                        persona_impacted=persona,
                    ))
            else:
                # Fallback: categorize from plain text friction_detected
                for friction_text in step.evaluation.friction_detected:
                    category = self._categorize(friction_text)
                    severity = self._score_severity(friction_text, step.step_number, len(steps))
                    friction_items.append(FrictionItem(
                        category=category,
                        description=friction_text,
                        severity=severity,
                        evidence_step=step.step_number,
                        persona_impacted=persona,
                    ))

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        friction_items.sort(key=lambda f: severity_order.get(f.severity, 4))

        # Compute friction score
        score = self._compute_friction_score(friction_items, len(steps), status)

        # Generate report summary via Gemini
        executive_summary = ""
        improvement_priorities: list[str] = []

        try:
            gemini = GeminiVisionService()
            friction_text = "\n".join(
                f"[{f.severity}] {f.category}: {f.description}" for f in friction_items
            )
            timeline_text = "\n".join(
                f"Step {s.step_number}: {s.action_type} → {s.target or 'N/A'} ({s.reasoning})"
                for s in step_timeline
            )
            summary_data = await gemini.generate_report_summary(
                url=url,
                goal=goal,
                persona_name=persona or "Default",
                total_steps=len(steps),
                outcome=status,
                total_time=elapsed_seconds,
                friction_list=friction_text or "No friction detected.",
                step_timeline=timeline_text,
            )

            executive_summary = summary_data.get("executive_summary", "")
            improvement_priorities = summary_data.get("improvement_priorities", [])

            # Apply item suggestions
            for suggestion in summary_data.get("item_suggestions", []):
                idx = suggestion.get("friction_index", -1)
                if 0 <= idx < len(friction_items):
                    friction_items[idx].improvement_suggestion = suggestion.get("suggestion", "")

        except Exception as e:
            logger.error("Report summary generation failed: %s", e)
            executive_summary = f"Navigation {'completed' if status == 'completed' else 'did not complete'} in {len(steps)} steps with {len(friction_items)} friction points."

        error_class = self._classify_error(status, steps)

        risk_index = self._compute_ux_risk_index(friction_items, len(steps), status, elapsed_seconds, score)

        return FrictionReport(
            session_id=session_id,
            url=url,
            goal=goal,
            persona=persona,
            status=status,
            total_steps=len(steps),
            total_time_seconds=elapsed_seconds,
            friction_items=friction_items,
            friction_score=score,
            ux_risk_index=risk_index,
            metrics={
                "avg_confidence": sum(s.plan.confidence for s in steps) / max(len(steps), 1),
                "recovery_steps": sum(1 for s in steps if s.is_recovery),
                "backtracks": sum(1 for s in steps if s.is_recovery and "back" in (s.recovery_reason or "")),
            },
            error_classification=error_class,
            executive_summary=executive_summary,
            improvement_priorities=improvement_priorities,
            step_timeline=step_timeline,
        )

    def _categorize(self, text: str) -> str:
        text_lower = text.lower()
        for keyword, category in FRICTION_CATEGORIES.items():
            if keyword in text_lower:
                return category
        return "navigation"

    def _score_severity(self, text: str, step_num: int, total_steps: int) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["block", "cannot", "impossible", "broken"]):
            return "critical"
        if any(w in text_lower for w in ["confus", "unclear", "missing", "error"]):
            return "high"
        if step_num <= 2:
            return "high"  # Early friction is more severe
        if any(w in text_lower for w in ["slow", "delay", "minor"]):
            return "low"
        return "medium"

    def _classify_error(
        self, status: str, steps: list[NavigationStep],
    ) -> ErrorClassification:
        """Classify the failure mode when navigation doesn't complete."""
        if status == "completed":
            return ErrorClassification(error_type="none")

        # Gather all step descriptions and reasons for analysis
        all_text = " ".join(
            (s.evaluation.description or "") + " " + (s.recovery_reason or "")
            for s in steps
        ).lower()

        # Network errors
        if any(kw in all_text for kw in ["net::err", "dns", "connection refused", "network", "fetch failed"]):
            return ErrorClassification(
                error_type="network",
                details="Network connectivity or DNS resolution failure",
                recoverable=True,
            )

        # Timeout
        if any(kw in all_text for kw in ["timeout", "timed out", "too long", "deadline"]):
            return ErrorClassification(
                error_type="timeout",
                details="Page or action took too long to respond",
                recoverable=True,
            )

        # Login wall / auth required
        if any(kw in all_text for kw in ["login", "sign in", "log in", "auth", "login_wall", "credentials"]):
            return ErrorClassification(
                error_type="login_wall",
                details="Authentication required to proceed",
                recoverable=False,
            )

        # Safety-blocked (captcha, payment, destructive)
        if status == "blocked" or any(kw in all_text for kw in [
            "safety", "captcha", "payment", "destructive", "blocked",
        ]):
            return ErrorClassification(
                error_type="safety",
                details="Safety guard prevented further navigation",
                recoverable=False,
            )

        # Abandoned — agent got stuck
        if status == "abandoned":
            return ErrorClassification(
                error_type="blocked",
                details="Agent exhausted recovery attempts without reaching goal",
                recoverable=True,
            )

        # Error status with no specific pattern
        if status == "error":
            return ErrorClassification(
                error_type="unknown",
                details="An unexpected error occurred during navigation",
                recoverable=True,
            )

        return ErrorClassification(error_type="none")

    def _compute_friction_score(
        self, items: list[FrictionItem], total_steps: int, status: str
    ) -> float:
        if total_steps == 0:
            return 0.0

        severity_weights = {"critical": 25, "high": 15, "medium": 8, "low": 3}
        raw_score = sum(severity_weights.get(f.severity, 5) for f in items)

        # Normalize: more steps with more friction = higher score
        density = raw_score / max(total_steps, 1)
        score = min(density * 10, 100)

        # Boost score if task wasn't completed
        if status in ("abandoned", "blocked", "error"):
            score = min(score + 20, 100)

        return round(score, 1)

    @staticmethod
    def _compute_ux_risk_index(
        items: list[FrictionItem],
        total_steps: int,
        status: str,
        elapsed_seconds: float,
        friction_score: float,
    ) -> float:
        """Compute a 0-100 UX Risk Index headline metric.

        Factors:
        1. Friction score (40%) — severity-weighted density
        2. Task completion (30%) — did the user reach their goal?
        3. Efficiency (15%) — steps & time relative to ideal
        4. Category breadth (15%) — friction across many categories is worse
        """
        # 1. Friction component (already 0-100)
        friction_component = friction_score * 0.40

        # 2. Task completion component
        completion_map = {"completed": 0, "abandoned": 70, "blocked": 85, "error": 90}
        completion_component = completion_map.get(status, 50) * 0.30

        # 3. Efficiency: penalize sessions that take too many steps or too long
        #    Ideal: ≤5 steps, ≤30 seconds
        step_penalty = min((max(total_steps - 5, 0) / 25) * 100, 100)
        time_penalty = min((max(elapsed_seconds - 30, 0) / 120) * 100, 100) if elapsed_seconds > 0 else 0
        efficiency_component = ((step_penalty + time_penalty) / 2) * 0.15

        # 4. Category breadth: friction in many categories signals systemic issues
        unique_cats = len({f.category for f in items})
        breadth_component = min((unique_cats / 7) * 100, 100) * 0.15

        risk = friction_component + completion_component + efficiency_component + breadth_component
        return round(min(risk, 100), 1)
