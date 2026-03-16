from __future__ import annotations

from pydantic import BaseModel, Field


class PersonaConfig(BaseModel):
    key: str
    name: str
    description: str
    prompt_suffix: str = Field(description="Appended to planning prompt to alter behavior")
    evaluation_suffix: str = Field(default="", description="Light tint for evaluation prompt")
    behavior_modifiers: dict[str, object] = Field(default_factory=dict)


class CustomPersonaCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    description: str = Field(min_length=5, max_length=200)
    behavioral_traits: list[str] = Field(
        default_factory=list,
        description="e.g. ['skips reading', 'keyboard-only', 'dislikes popups']",
        max_length=8,
    )
    focus_areas: list[str] = Field(
        default_factory=list,
        description="Friction categories to focus on: navigation, contrast, affordance, copy, error, performance, accessibility",
        max_length=7,
    )
    custom_instructions: str = Field(
        default="",
        max_length=500,
        description="Free-text prompt instructions for the persona",
    )


class ComparisonRequest(BaseModel):
    url: str
    goal: str
    personas: list[str] = Field(
        description="List of persona keys to compare",
        min_length=2,
        max_length=4,
    )


class PathStep(BaseModel):
    """Compact step summary for persona divergence visualization."""
    step: int
    action: str
    target: str | None = None
    friction: bool = False
    url: str = ""


class PersonaRunResult(BaseModel):
    persona_key: str
    persona_name: str
    total_steps: int
    retries: int = 0
    backtracks: int = 0
    time_seconds: float = 0.0
    friction_count: int = 0
    friction_by_category: dict[str, int] = Field(
        default_factory=dict,
        description="Friction count per category (navigation, contrast, etc.)",
    )
    friction_score: float = 0.0
    ux_risk_index: float = Field(default=0.0, description="0-100 headline UX risk metric")
    outcome: str = "pending"
    session_id: str = ""
    path: list[PathStep] = Field(default_factory=list, description="Step-by-step path for divergence view")
    verdict: str = Field(default="", description="One-line persona verdict summarizing experience")


class ComparisonResult(BaseModel):
    url: str
    goal: str
    results: list[PersonaRunResult] = Field(default_factory=list)
