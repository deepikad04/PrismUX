from __future__ import annotations

from pydantic import BaseModel, Field


class StepSummary(BaseModel):
    step_number: int
    action_type: str
    target: str | None = None
    reasoning: str = ""
    friction_detected: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    screenshot_url: str = ""


class FrictionItem(BaseModel):
    category: str = Field(description="navigation, contrast, affordance, copy, error, performance, accessibility")
    description: str
    severity: str = Field(description="low, medium, high, critical")
    evidence_step: int
    evidence_screenshot_url: str = ""
    improvement_suggestion: str = ""
    persona_impacted: str | None = None


class ErrorClassification(BaseModel):
    error_type: str = Field(
        default="none",
        description="none, network, timeout, blocked, login_wall, safety, unknown",
    )
    details: str = ""
    recoverable: bool = True


class FrictionReport(BaseModel):
    session_id: str
    url: str
    goal: str
    persona: str | None = None
    status: str
    total_steps: int
    total_time_seconds: float = 0.0
    friction_items: list[FrictionItem] = Field(default_factory=list)
    friction_score: float = Field(default=0.0, description="0-100, lower is better")
    ux_risk_index: float = Field(
        default=0.0,
        description="0-100 headline metric: 0 = no risk, 100 = critical. Combines friction density, severity, task completion, and time efficiency.",
    )
    metrics: dict = Field(default_factory=dict)
    error_classification: ErrorClassification = Field(default_factory=ErrorClassification)
    executive_summary: str = ""
    improvement_priorities: list[str] = Field(default_factory=list)
    step_timeline: list[StepSummary] = Field(default_factory=list)
