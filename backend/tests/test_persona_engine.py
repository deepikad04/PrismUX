"""Tests for PersonaEngine — persona CRUD, constraint checks, and language analysis."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schemas.navigation import BoundingBox, CategorizedFriction, DetectedElement
from schemas.persona import PersonaConfig
from services.agent.persona_engine import PERSONAS, PersonaEngine


class TestGetPersona:
    def test_returns_none_for_none(self):
        assert PersonaEngine.get_persona(None) is None

    def test_returns_known_persona(self):
        persona = PersonaEngine.get_persona("impatient")
        assert persona is not None
        assert persona.name == "Impatient User"

    def test_returns_none_for_unknown(self):
        assert PersonaEngine.get_persona("nonexistent_persona") is None


class TestGetAllPersonas:
    def test_returns_built_in_personas(self):
        all_p = PersonaEngine.get_all_personas()
        keys = {p.key for p in all_p}
        assert "impatient" in keys
        assert "cautious" in keys
        assert "accessibility" in keys
        assert "non_native_english" in keys


class TestRegisterCustom:
    def teardown_method(self):
        # Clean up any custom personas
        keys_to_remove = [k for k in PERSONAS if k.startswith("custom_")]
        for k in keys_to_remove:
            del PERSONAS[k]

    def test_creates_custom_persona(self):
        persona = PersonaEngine.register_custom(
            name="Elderly User",
            description="Senior citizen with low vision",
            behavioral_traits=["Needs large text", "Slow reader"],
            focus_areas=["contrast", "affordance"],
            custom_instructions="Focus on readability",
        )
        assert persona.key == "custom_elderly_user"
        assert "Elderly User" in persona.name
        assert "large text" in persona.prompt_suffix.lower() or "Needs large text" in persona.prompt_suffix
        assert "contrast" in persona.evaluation_suffix.lower()

    def test_custom_persona_accessible_via_get(self):
        PersonaEngine.register_custom(
            name="Test User",
            description="Just a test",
            behavioral_traits=[],
            focus_areas=[],
        )
        assert PersonaEngine.get_persona("custom_test_user") is not None

    def test_custom_persona_key_truncated(self):
        persona = PersonaEngine.register_custom(
            name="Very Long Persona Name That Exceeds Limit",
            description="Test",
            behavioral_traits=[],
            focus_areas=[],
        )
        assert len(persona.key) <= len("custom_") + 20


class TestPlanningAndEvaluationPrompts:
    def test_planning_prompt_none_persona(self):
        assert PersonaEngine.get_planning_prompt(None) == ""

    def test_planning_prompt_returns_suffix(self):
        persona = PersonaEngine.get_persona("impatient")
        prompt = PersonaEngine.get_planning_prompt(persona)
        assert "IMPATIENT" in prompt
        assert len(prompt) > 10

    def test_evaluation_suffix_none_persona(self):
        assert PersonaEngine.get_evaluation_suffix(None) == ""

    def test_evaluation_suffix_returns_suffix(self):
        persona = PersonaEngine.get_persona("cautious")
        suffix = PersonaEngine.get_evaluation_suffix(persona)
        assert "CAUTIOUS" in suffix


def _make_element(
    label: str = "Button",
    element_type: str = "button",
    width: int = 60,
    height: int = 40,
    interactable: bool = True,
    accessibility_issues: list[str] | None = None,
) -> DetectedElement:
    return DetectedElement(
        label=label,
        element_type=element_type,
        bbox=BoundingBox(x=100, y=100, width=width, height=height),
        confidence=0.9,
        interactable=interactable,
        accessibility_issues=accessibility_issues or [],
    )


class TestCheckConstraints:
    def test_none_persona_returns_empty(self):
        assert PersonaEngine.check_constraints(None, []) == []

    def test_small_tap_target_medium(self):
        """Tap target <44px but >=24px → medium severity."""
        persona = PersonaEngine.get_persona("impatient")
        el = _make_element(width=30, height=30)
        frictions = PersonaEngine.check_constraints(persona, [el])
        tap_frictions = [f for f in frictions if "tap target" in f.description.lower()]
        assert len(tap_frictions) >= 1
        assert tap_frictions[0].severity == "medium"

    def test_tiny_tap_target_high(self):
        """Tap target <24px → high severity."""
        persona = PersonaEngine.get_persona("impatient")
        el = _make_element(width=20, height=20)
        frictions = PersonaEngine.check_constraints(persona, [el])
        tap_frictions = [f for f in frictions if "tap target" in f.description.lower()]
        assert len(tap_frictions) >= 1
        assert tap_frictions[0].severity == "high"

    def test_adequate_tap_target_no_friction(self):
        """Tap target >=44px → no friction."""
        persona = PersonaEngine.get_persona("impatient")
        el = _make_element(width=50, height=50)
        frictions = PersonaEngine.check_constraints(persona, [el])
        tap_frictions = [f for f in frictions if "tap target" in f.description.lower()]
        assert len(tap_frictions) == 0


class TestAccessibilityChecks:
    def test_flags_accessibility_issues(self):
        persona = PersonaEngine.get_persona("accessibility")
        el = _make_element(
            label="Submit",
            accessibility_issues=["Missing alt text"],
            width=50,
            height=50,
        )
        frictions = PersonaEngine.check_constraints(persona, [el])
        a11y_frictions = [f for f in frictions if f.category == "accessibility"]
        assert len(a11y_frictions) >= 1
        assert "alt text" in a11y_frictions[0].description.lower()

    def test_flags_icon_only_buttons(self):
        persona = PersonaEngine.get_persona("accessibility")
        el = _make_element(label="X", element_type="button", width=50, height=50)
        frictions = PersonaEngine.check_constraints(persona, [el])
        icon_frictions = [f for f in frictions if "icon-only" in f.description.lower()]
        assert len(icon_frictions) >= 1


class TestLanguageChecks:
    def test_detects_jargon_in_page_text(self):
        persona = PersonaEngine.get_persona("non_native_english")
        el = _make_element(width=50, height=50)
        frictions = PersonaEngine.check_constraints(
            persona, [el], page_text="Level up your skills today!"
        )
        jargon_frictions = [f for f in frictions if "jargon" in f.description.lower()]
        assert len(jargon_frictions) >= 1
        assert jargon_frictions[0].category == "copy"

    def test_detects_jargon_in_element_labels(self):
        persona = PersonaEngine.get_persona("non_native_english")
        el = _make_element(label="Snag this deal", width=50, height=50)
        frictions = PersonaEngine.check_constraints(persona, [el])
        jargon_frictions = [f for f in frictions if "snag" in f.description.lower()]
        assert len(jargon_frictions) >= 1
        assert jargon_frictions[0].severity == "high"

    def test_no_jargon_clean_text(self):
        persona = PersonaEngine.get_persona("non_native_english")
        el = _make_element(label="Buy now", width=50, height=50)
        frictions = PersonaEngine.check_constraints(
            persona, [el], page_text="Welcome to our store."
        )
        jargon_frictions = [f for f in frictions if "jargon" in f.description.lower()]
        assert len(jargon_frictions) == 0
