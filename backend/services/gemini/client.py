from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Any

from google import genai
from google.genai import types as genai_types
from pydantic import ValidationError

from config import get_settings
from schemas.navigation import (
    ActionPlan,
    BoundingBox,
    CandidateElement,
    EvaluationResult,
    NavigationStep,
    PerceptionResult,
)
from .prompts import (
    EVALUATE_PROMPT,
    PERCEIVE_AND_PLAN_PROMPT,
    RECOVERY_PROMPT,
    REPAIR_PROMPT,
    REPORT_SUMMARY_PROMPT,
    build_history_summary,
)

logger = logging.getLogger(__name__)

# JSON schemas for Gemini structured output enforcement
PERCEIVE_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "perception": {
            "type": "object",
            "properties": {
                "page_description": {"type": "string"},
                "page_purpose": {"type": "string"},
                "has_modal_or_overlay": {"type": "boolean"},
                "loading_state": {"type": "boolean"},
                "elements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "element_type": {"type": "string"},
                            "bbox": {
                                "type": "object",
                                "properties": {
                                    "x": {"type": "integer"},
                                    "y": {"type": "integer"},
                                    "width": {"type": "integer"},
                                    "height": {"type": "integer"},
                                },
                                "required": ["x", "y", "width", "height"],
                            },
                            "confidence": {"type": "number"},
                            "interactable": {"type": "boolean"},
                            "accessibility_issues": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["label", "element_type", "bbox", "confidence"],
                    },
                },
            },
            "required": ["page_description", "elements"],
        },
        "action": {
            "type": "object",
            "properties": {
                "action_type": {"type": "string"},
                "target_element": {"type": "string"},
                "coordinates": {
                    "type": "array",
                    "items": {"type": "integer"},
                },
                "input_text": {"type": "string"},
                "key": {"type": "string"},
                "seconds": {"type": "integer"},
                "reasoning": {"type": "string"},
                "confidence": {"type": "number"},
                "candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "bbox": {
                                "type": "object",
                                "properties": {
                                    "x": {"type": "integer"},
                                    "y": {"type": "integer"},
                                    "width": {"type": "integer"},
                                    "height": {"type": "integer"},
                                },
                                "required": ["x", "y", "width", "height"],
                            },
                            "confidence": {"type": "number"},
                            "is_chosen": {"type": "boolean"},
                        },
                        "required": ["label", "bbox", "confidence", "is_chosen"],
                    },
                },
            },
            "required": ["action_type", "reasoning", "confidence"],
        },
    },
    "required": ["perception", "action"],
}

EVALUATE_SCHEMA = {
    "type": "object",
    "properties": {
        "progress_made": {"type": "boolean"},
        "goal_achieved": {"type": "boolean"},
        "page_changed": {"type": "boolean"},
        "description": {"type": "string"},
        "friction_detected": {
            "type": "array",
            "items": {"type": "string"},
        },
        "friction_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "description": {"type": "string"},
                    "severity": {"type": "string"},
                },
                "required": ["category", "description", "severity"],
            },
        },
        "confidence": {"type": "number"},
    },
    "required": ["progress_made", "goal_achieved", "description", "confidence"],
}

REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "executive_summary": {"type": "string"},
        "friction_score": {"type": "number"},
        "improvement_priorities": {
            "type": "array",
            "items": {"type": "string"},
        },
        "item_suggestions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "friction_index": {"type": "integer"},
                    "suggestion": {"type": "string"},
                },
            },
        },
    },
    "required": ["executive_summary", "friction_score", "improvement_priorities"],
}


RECOVERY_ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "action_type": {"type": "string"},
        "target_element": {"type": "string"},
        "coordinates": {"type": "array", "items": {"type": "integer"}},
        "input_text": {"type": "string"},
        "key": {"type": "string"},
        "reasoning": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": ["action_type", "reasoning", "confidence"],
}


class GeminiVisionService:
    """Handles all Gemini multimodal API calls with structured output and repair retry."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.perception_model = settings.gemini_perception_model
        self.evaluation_model = settings.gemini_evaluation_model
        self.report_model = settings.gemini_report_model
        self.max_retries = settings.gemini_max_retries
        self.timeout = settings.gemini_timeout_seconds

    async def perceive_and_plan(
        self,
        screenshot_b64: str,
        goal: str,
        history: list[NavigationStep],
        persona_prompt: str = "",
        width: int = 1280,
        height: int = 720,
    ) -> tuple[PerceptionResult, ActionPlan]:
        """Combined perceive + plan in a single Gemini call."""
        history_summary = build_history_summary(history)

        prompt = PERCEIVE_AND_PLAN_PROMPT.format(
            goal=goal,
            history_count=min(len(history), 5),
            history_summary=history_summary,
            width=width,
            height=height,
            persona_prompt=persona_prompt,
        )

        image_bytes = base64.b64decode(screenshot_b64)
        image_part = genai_types.Part.from_bytes(data=image_bytes, mime_type="image/png")

        raw = await self._call_gemini(
            model=self.perception_model,
            contents=[image_part, prompt],
            schema=PERCEIVE_PLAN_SCHEMA,
            call_type="perceive_and_plan",
        )

        perception = self._parse_perception(raw)
        action = self._parse_action(raw)

        return perception, action

    async def evaluate(
        self,
        before_b64: str,
        after_b64: str,
        plan: ActionPlan,
        goal: str,
        persona_evaluation_suffix: str = "",
    ) -> EvaluationResult:
        """Evaluate progress by comparing before/after screenshots."""
        prompt = EVALUATE_PROMPT.format(
            goal=goal,
            action_type=plan.action_type,
            target_element=plan.target_element or "N/A",
            reasoning=plan.reasoning,
            persona_evaluation_suffix=persona_evaluation_suffix,
        )

        before_bytes = base64.b64decode(before_b64)
        after_bytes = base64.b64decode(after_b64)

        before_part = genai_types.Part.from_bytes(data=before_bytes, mime_type="image/png")
        after_part = genai_types.Part.from_bytes(data=after_bytes, mime_type="image/png")

        raw = await self._call_gemini(
            model=self.evaluation_model,
            contents=[
                "BEFORE screenshot:",
                before_part,
                "AFTER screenshot:",
                after_part,
                prompt,
            ],
            schema=EVALUATE_SCHEMA,
            call_type="evaluate",
        )

        # Clamp confidence fields to 0-1 range (Gemini sometimes returns 1-5 scale)
        if "confidence" in raw and isinstance(raw["confidence"], (int, float)):
            raw["confidence"] = min(max(raw["confidence"] / 5 if raw["confidence"] > 1 else raw["confidence"], 0), 1)
        for cand in raw.get("candidates", []):
            if "confidence" in cand and isinstance(cand["confidence"], (int, float)):
                cand["confidence"] = min(max(cand["confidence"] / 5 if cand["confidence"] > 1 else cand["confidence"], 0), 1)

        try:
            return EvaluationResult(**raw)
        except ValidationError as e:
            logger.warning("Evaluation parse error, using defaults: %s", e)
            return EvaluationResult(
                progress_made=raw.get("progress_made", False),
                goal_achieved=raw.get("goal_achieved", False),
                description=raw.get("description", "Failed to parse evaluation"),
                friction_detected=raw.get("friction_detected", []),
                confidence=0.3,
            )

    async def generate_report_summary(
        self,
        url: str,
        goal: str,
        persona_name: str,
        total_steps: int,
        outcome: str,
        total_time: float,
        friction_list: str,
        step_timeline: str,
    ) -> dict[str, Any]:
        """Generate friction report summary using a stronger model."""
        prompt = REPORT_SUMMARY_PROMPT.format(
            url=url,
            goal=goal,
            persona_name=persona_name or "Default",
            total_steps=total_steps,
            outcome=outcome,
            total_time=f"{total_time:.1f}",
            friction_list=friction_list,
            step_timeline=step_timeline,
        )

        return await self._call_gemini(
            model=self.report_model,
            contents=[prompt],
            schema=REPORT_SCHEMA,
            call_type="report_summary",
        )

    async def suggest_recovery(
        self,
        screenshot_b64: str,
        goal: str,
        tried_actions: list[str],
        current_url: str,
        width: int = 960,
        height: int = 540,
    ) -> ActionPlan:
        """Ask Gemini to visually analyze the page and suggest an intelligent recovery action."""
        prompt = RECOVERY_PROMPT.format(
            goal=goal,
            tried_actions="\n".join(f"- {a}" for a in tried_actions) or "None",
            current_url=current_url,
            width=width,
            height=height,
        )

        image_bytes = base64.b64decode(screenshot_b64)
        image_part = genai_types.Part.from_bytes(data=image_bytes, mime_type="image/png")

        raw = await self._call_gemini(
            model=self.perception_model,
            contents=[image_part, prompt],
            schema=RECOVERY_ACTION_SCHEMA,
            call_type="recovery",
        )

        coords = raw.get("coordinates")
        if isinstance(coords, (list, tuple)) and len(coords) == 2:
            coords = (int(coords[0]), int(coords[1]))
        else:
            coords = None

        return ActionPlan(
            action_type=raw.get("action_type", "scroll_down"),
            target_element=raw.get("target_element"),
            coordinates=coords,
            input_text=raw.get("input_text"),
            key=raw.get("key"),
            reasoning=f"[AI Recovery] {raw.get('reasoning', 'Gemini suggested action')}",
            confidence=raw.get("confidence", 0.5),
            candidates=[],
        )

    async def _call_gemini(
        self,
        model: str,
        contents: list,
        schema: dict | None,
        call_type: str,
    ) -> dict[str, Any]:
        """Call Gemini with retry, timeout, structured output schema, and repair."""
        last_error = None
        # Keep original contents for repair retries (preserves images)
        original_contents = list(contents)
        text: str | None = None

        for attempt in range(self.max_retries):
            try:
                response = await asyncio.wait_for(
                    self._generate(model, contents, schema),
                    timeout=self.timeout,
                )

                text = response.text
                if not text:
                    raise ValueError("Empty response from Gemini")

                parsed = self._extract_json(text)
                logger.info(
                    "Gemini %s call succeeded (attempt %d)", call_type, attempt + 1
                )
                return parsed

            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.warning(
                    "Gemini %s parse error (attempt %d): %s",
                    call_type, attempt + 1, e,
                )
                if attempt < self.max_retries - 1:
                    # Repair retry: append repair prompt to ORIGINAL contents (keeps images)
                    repair_prompt = REPAIR_PROMPT.format(
                        error_message=str(e),
                        previous_response=text or "N/A",
                    )
                    contents = original_contents + [repair_prompt]
                    continue

            except asyncio.TimeoutError:
                last_error = TimeoutError(f"Gemini {call_type} timed out after {self.timeout}s")
                logger.warning("Gemini %s timeout (attempt %d)", call_type, attempt + 1)

            except Exception as e:
                last_error = e
                logger.error("Gemini %s error (attempt %d): %s", call_type, attempt + 1, e)

            if attempt < self.max_retries - 1:
                import random
                wait = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff + jitter
                logger.info("Retrying %s in %.1fs (attempt %d/%d)", call_type, wait, attempt + 2, self.max_retries)
                await asyncio.sleep(wait)
                # Reset contents for non-parse retries
                contents = list(original_contents)

        raise RuntimeError(f"Gemini {call_type} failed after {self.max_retries} attempts: {last_error}")

    async def _generate(self, model: str, contents: list, schema: dict | None) -> Any:
        """Async wrapper around the synchronous Gemini SDK."""
        config = genai_types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        )
        # Attach response_schema for structured output enforcement
        if schema:
            config.response_schema = schema

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            ),
        )

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from Gemini response, handling markdown code blocks."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.strip() == "```" and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            text = "\n".join(json_lines)

        return json.loads(text)

    def _parse_perception(self, raw: dict) -> PerceptionResult:
        """Parse perception data from combined response."""
        perception_data = raw.get("perception", raw)
        try:
            return PerceptionResult(**perception_data)
        except ValidationError as e:
            logger.warning("Perception parse error: %s", e)
            return PerceptionResult(page_description="Parse error", elements=[])

    def _parse_action(self, raw: dict) -> ActionPlan:
        """Parse action plan from combined response."""
        action_data = raw.get("action", raw)

        # Convert coordinates from list/tuple to a valid (int, int) or None
        coords = action_data.get("coordinates")
        if coords is not None:
            if isinstance(coords, (list, tuple)) and len(coords) == 2:
                action_data["coordinates"] = (int(coords[0]), int(coords[1]))
            else:
                action_data["coordinates"] = None

        # Clamp confidence to 0-1 (Gemini sometimes returns 1-5 scale)
        if "confidence" in action_data and isinstance(action_data["confidence"], (int, float)):
            v = action_data["confidence"]
            action_data["confidence"] = min(max(v / 5 if v > 1 else v, 0), 1)

        # Parse candidates
        candidates_raw = action_data.get("candidates", [])
        candidates = []
        for c in candidates_raw:
            try:
                bbox = BoundingBox(**c["bbox"]) if isinstance(c.get("bbox"), dict) else c.get("bbox")
                candidates.append(CandidateElement(
                    label=c["label"],
                    bbox=bbox,
                    confidence=min(max(c.get("confidence", 0.5) / 5 if c.get("confidence", 0.5) > 1 else c.get("confidence", 0.5), 0), 1),
                    is_chosen=c.get("is_chosen", False),
                ))
            except Exception:
                continue
        action_data["candidates"] = candidates

        try:
            return ActionPlan(**action_data)
        except ValidationError as e:
            logger.warning("Action parse error: %s", e)
            return ActionPlan(
                action_type="wait",
                reasoning="Failed to parse action plan",
                confidence=0.1,
                seconds=2,
            )
