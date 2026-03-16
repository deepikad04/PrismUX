from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    url: str = Field(description="Target URL to navigate")
    goal: str = Field(description="User goal e.g. 'Find the pricing page'")
    persona: str | None = Field(default=None, description="Persona key: impatient, cautious, accessibility, non_native_english")


class SessionResponse(BaseModel):
    id: str
    url: str
    goal: str
    persona: str | None = None
    status: str = "created"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_steps: int = 0
    completed: bool = False


class SessionStatus(BaseModel):
    id: str
    status: Literal["created", "queued", "running", "completed", "abandoned", "blocked", "error"]
    total_steps: int = 0
    current_url: str = ""
    elapsed_seconds: float = 0.0
