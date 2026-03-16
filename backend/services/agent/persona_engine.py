from __future__ import annotations

import logging

from schemas.navigation import CategorizedFriction, DetectedElement
from schemas.persona import PersonaConfig

logger = logging.getLogger(__name__)


PERSONAS: dict[str, PersonaConfig] = {
    "impatient": PersonaConfig(
        key="impatient",
        name="Impatient User",
        description="Skips reading, clicks fast, abandons after delays",
        behavior_modifiers={
            "max_wait_seconds": 2,
            "skip_reading": True,
            "abandon_threshold": 3,
            "scroll_patience": "low",
        },
        prompt_suffix=(
            "## PERSONA: IMPATIENT USER\n"
            "You are simulating an IMPATIENT user. Apply these behavioral rules:\n"
            "- Skip reading body text; only scan headings, buttons, and navigation\n"
            "- Always prefer the FIRST and MOST PROMINENT visible action button (hero CTA)\n"
            "- Do NOT scroll to find alternatives — pick what's immediately visible\n"
            "- If a page takes more than 2 seconds or shows a multi-step form, flag it as friction\n"
            "- Abandon the task after encountering 3+ friction points\n"
            "- Express frustration in your reasoning when encountering delays or complex flows\n"
            "- Prefer shortcut paths over thorough exploration"
        ),
        evaluation_suffix=(
            "Evaluate friction from the perspective of an IMPATIENT user. "
            "Any loading delay, multi-step process, popup, or unclear next step is HIGH friction."
        ),
    ),
    "cautious": PersonaConfig(
        key="cautious",
        name="Cautious User",
        description="Reads everything, prefers nav menus, security-conscious",
        behavior_modifiers={
            "max_wait_seconds": 15,
            "read_all_text": True,
            "hover_before_click": True,
            "security_conscious": True,
        },
        prompt_suffix=(
            "## PERSONA: CAUTIOUS USER\n"
            "You are simulating a CAUTIOUS user. Apply these behavioral rules:\n"
            "- Read all visible text before taking action\n"
            "- PREFER navigation menus over hero CTAs — look for nav bar, hamburger menu, footer links\n"
            "- Look for security indicators (HTTPS, padlock, privacy policy links)\n"
            "- Hesitate before providing personal information\n"
            "- Hover over elements to check tooltips before clicking\n"
            "- Prefer well-labeled, official-looking UI elements over flashy buttons\n"
            "- Flag any trust or security concerns as friction"
        ),
        evaluation_suffix=(
            "Evaluate friction from the perspective of a CAUTIOUS user. "
            "Missing privacy info, unclear data handling, aggressive CTAs, and auto-opt-ins are HIGH friction."
        ),
    ),
    "accessibility": PersonaConfig(
        key="accessibility",
        name="Accessibility-First User",
        description="Relies on screen readers, keyboard nav, high contrast",
        behavior_modifiers={
            "keyboard_only": True,
            "check_aria_labels": True,
            "check_color_contrast": True,
            "check_focus_indicators": True,
        },
        prompt_suffix=(
            "## PERSONA: ACCESSIBILITY-FIRST USER\n"
            "You are simulating a user who RELIES ON ACCESSIBILITY features. Apply these rules:\n"
            "- Check if elements have proper ARIA labels and alt text\n"
            "- Note missing alt text on images\n"
            "- Flag poor color contrast between text and background\n"
            "- Flag tap targets smaller than 44x44 pixels\n"
            "- Prefer elements with clear, descriptive labels over icon-only buttons\n"
            "- Choose elements that have proper ARIA labels over unlabeled alternatives\n"
            "- Report elements that lack visible focus indicators\n"
            "- Flag any violation of WCAG 2.1 AA guidelines you can identify visually"
        ),
        evaluation_suffix=(
            "Evaluate friction from an ACCESSIBILITY perspective. "
            "Small tap targets, missing labels, poor contrast, icon-only buttons, "
            "and elements without focus indicators are all HIGH friction."
        ),
    ),
    "non_native_english": PersonaConfig(
        key="non_native_english",
        name="Non-Native English Speaker",
        description="Struggles with jargon, idioms, ambiguous labels",
        behavior_modifiers={
            "simple_language_preferred": True,
            "confused_by_idioms": True,
            "needs_clear_labels": True,
        },
        prompt_suffix=(
            "## PERSONA: NON-NATIVE ENGLISH SPEAKER\n"
            "You are simulating a NON-NATIVE ENGLISH speaker. Apply these rules:\n"
            "- Get confused by jargon, idioms, or culturally specific references\n"
            "- Prefer buttons/links with simple, clear labels (e.g. 'Buy' over 'Snag this deal')\n"
            "- Prefer icon-driven UI elements where meaning is visually clear\n"
            "- May misunderstand ambiguous instructions or clever wordplay\n"
            "- Flag unclear, overly complex, or jargon-heavy language as friction\n"
            "- Note where translations or simpler alternatives would help\n"
            "- Prefer familiar UI patterns (standard nav, clear forms) over creative layouts"
        ),
        evaluation_suffix=(
            "Evaluate friction from the perspective of a NON-NATIVE ENGLISH speaker. "
            "Jargon, idioms, clever wordplay, ambiguous labels, and complex sentence structures are HIGH friction."
        ),
    ),
}


class PersonaEngine:
    """Manages persona configs and generates persona-specific prompts."""

    @staticmethod
    def get_persona(key: str | None) -> PersonaConfig | None:
        if key is None:
            return None
        return PERSONAS.get(key)

    @staticmethod
    def get_all_personas() -> list[PersonaConfig]:
        return list(PERSONAS.values())

    @staticmethod
    def register_custom(
        name: str,
        description: str,
        behavioral_traits: list[str],
        focus_areas: list[str],
        custom_instructions: str = "",
    ) -> PersonaConfig:
        """Build and register a custom persona from user-provided traits."""
        key = "custom_" + name.lower().replace(" ", "_")[:20]

        # Build prompt suffix from traits
        trait_rules = "\n".join(f"- {t}" for t in behavioral_traits) if behavioral_traits else "- Follow your best judgment"
        focus_text = ", ".join(focus_areas) if focus_areas else "all categories"

        prompt_suffix = (
            f"## PERSONA: {name.upper()}\n"
            f"You are simulating a custom user persona: {description}\n"
            f"Apply these behavioral rules:\n{trait_rules}\n"
        )
        if custom_instructions:
            prompt_suffix += f"\nAdditional instructions: {custom_instructions}\n"
        prompt_suffix += f"\nFocus on detecting friction in these categories: {focus_text}"

        eval_suffix = (
            f"Evaluate friction from the perspective of: {description}. "
            f"Pay special attention to: {focus_text}."
        )

        persona = PersonaConfig(
            key=key,
            name=name,
            description=description,
            prompt_suffix=prompt_suffix,
            evaluation_suffix=eval_suffix,
            behavior_modifiers={
                "custom": True,
                "focus_areas": focus_areas,
                "traits": behavioral_traits,
            },
        )
        PERSONAS[key] = persona
        logger.info("Registered custom persona: %s (%s)", name, key)
        return persona

    @staticmethod
    def get_planning_prompt(persona: PersonaConfig | None) -> str:
        if persona is None:
            return ""
        return persona.prompt_suffix

    @staticmethod
    def get_evaluation_suffix(persona: PersonaConfig | None) -> str:
        if persona is None:
            return ""
        return persona.evaluation_suffix

    @staticmethod
    def check_constraints(
        persona: PersonaConfig | None,
        elements: list[DetectedElement],
        page_text: str = "",
    ) -> list[CategorizedFriction]:
        """Run persona-specific constraint checks on detected elements."""
        if persona is None:
            return []

        frictions: list[CategorizedFriction] = []
        key = persona.key

        if key == "accessibility":
            frictions.extend(PersonaEngine._check_accessibility(elements))
        elif key == "non_native_english":
            frictions.extend(PersonaEngine._check_language(elements, page_text))

        # Universal: small tap targets (< 44x44 WCAG recommendation)
        min_size = persona.behavior_modifiers.get("min_target_size", 44)
        for el in elements:
            if el.interactable and (el.bbox.width < min_size or el.bbox.height < min_size):
                frictions.append(CategorizedFriction(
                    category="affordance",
                    description=f"Small tap target: '{el.label}' is {el.bbox.width}x{el.bbox.height}px (min {min_size}px)",
                    severity="high" if el.bbox.width < 24 or el.bbox.height < 24 else "medium",
                    evidence=f"{el.bbox.width}x{el.bbox.height}px < {min_size}px WCAG minimum",
                ))

        return frictions

    @staticmethod
    def _check_accessibility(elements: list[DetectedElement]) -> list[CategorizedFriction]:
        """Check accessibility-specific constraints."""
        frictions: list[CategorizedFriction] = []

        for el in elements:
            # Flag elements with accessibility issues reported by Gemini
            for issue in el.accessibility_issues:
                frictions.append(CategorizedFriction(
                    category="accessibility",
                    description=f"'{el.label}': {issue}",
                    severity="high",
                    evidence=f"element: {el.element_type} '{el.label}' at ({el.bbox.x},{el.bbox.y})",
                ))

            # Icon-only buttons (very short labels with no descriptive text)
            if el.element_type == "button" and len(el.label.strip()) <= 2:
                frictions.append(CategorizedFriction(
                    category="accessibility",
                    description=f"Icon-only button without descriptive label: '{el.label}'",
                    severity="medium",
                    evidence=f"label length: {len(el.label.strip())} chars — needs descriptive text or aria-label",
                ))

        return frictions

    # Common jargon/idiom patterns that confuse non-native speakers
    _JARGON_TERMS = [
        "snag", "grab", "nab", "score", "land", "nail", "crush it",
        "level up", "game-changer", "deep dive", "circle back",
        "low-hanging fruit", "move the needle", "boil the ocean",
        "at the end of the day", "no brainer", "touch base",
        "out of the box", "bleeding edge", "best-in-class",
    ]

    @staticmethod
    def _check_language(elements: list[DetectedElement], page_text: str) -> list[CategorizedFriction]:
        """Check for jargon and complex language that non-native speakers struggle with."""
        frictions: list[CategorizedFriction] = []
        text_lower = page_text.lower()

        for term in PersonaEngine._JARGON_TERMS:
            if term in text_lower:
                frictions.append(CategorizedFriction(
                    category="copy",
                    description=f"Jargon detected: '{term}' — may confuse non-native speakers",
                    severity="medium",
                    evidence=f"term: '{term}' found in page text",
                ))

        # Check element labels for jargon
        for el in elements:
            label_lower = el.label.lower()
            for term in PersonaEngine._JARGON_TERMS:
                if term in label_lower:
                    frictions.append(CategorizedFriction(
                        category="copy",
                        description=f"Jargon in '{el.element_type}' label: '{el.label}' contains '{term}'",
                        severity="high",
                        evidence=f"term: '{term}' in {el.element_type} label '{el.label}'",
                    ))

        return frictions
