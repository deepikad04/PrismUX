from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x: int = Field(description="Top-left x coordinate in pixels")
    y: int = Field(description="Top-left y coordinate in pixels")
    width: int = Field(description="Width in pixels")
    height: int = Field(description="Height in pixels")

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)


class CandidateElement(BaseModel):
    label: str = Field(description="Descriptive label e.g. 'Sign In button'")
    bbox: BoundingBox
    confidence: float = Field(ge=0, le=1)
    is_chosen: bool = Field(description="True if this is the selected action target")


class DetectedElement(BaseModel):
    label: str
    element_type: str = Field(description="button, input, link, image, text, heading, navigation, modal, form, dropdown")
    bbox: BoundingBox
    confidence: float = Field(ge=0, le=1)
    interactable: bool = True
    accessibility_issues: list[str] = Field(default_factory=list)


class PerceptionResult(BaseModel):
    page_description: str
    page_purpose: str = ""
    has_modal_or_overlay: bool = False
    loading_state: bool = False
    elements: list[DetectedElement] = Field(default_factory=list)


class ActionPlan(BaseModel):
    action_type: Literal[
        "click", "type", "scroll_down", "scroll_up",
        "press_key", "hover", "wait", "go_back", "done"
    ]
    target_element: str | None = None
    coordinates: tuple[int, int] | None = None
    input_text: str | None = None
    key: str | None = None
    seconds: int | None = None
    reasoning: str = Field(description="1-line explanation shown in UI")
    confidence: float = Field(ge=0, le=1)
    candidates: list[CandidateElement] = Field(
        default_factory=list,
        description="Top-3 candidate elements considered"
    )


FRICTION_CATEGORIES = ("navigation", "contrast", "affordance", "copy", "error", "performance", "accessibility")


class CategorizedFriction(BaseModel):
    category: str = Field(description="One of: navigation, contrast, affordance, copy, error, performance, accessibility")
    description: str = Field(description="Specific friction point description")
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    evidence: str = Field(default="", description="Measured data backing this friction point, e.g. '24x18px (min 44px)' or 'term: circle back'")


class EvaluationResult(BaseModel):
    progress_made: bool
    goal_achieved: bool
    page_changed: bool = True
    description: str
    friction_detected: list[str] = Field(default_factory=list)
    friction_items: list[CategorizedFriction] = Field(
        default_factory=list,
        description="Categorized friction points with severity"
    )
    confidence: float = Field(ge=0, le=1)


class ActionResult(BaseModel):
    success: bool
    url_after: str = ""
    error: str | None = None


class NavigationStep(BaseModel):
    step_number: int
    perception: PerceptionResult
    plan: ActionPlan
    action_result: ActionResult
    evaluation: EvaluationResult
    screenshot_before_b64: str = ""
    screenshot_after_b64: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_recovery: bool = False
    recovery_reason: str | None = None
