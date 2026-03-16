"""Prompt templates for Gemini multimodal calls."""

PERCEIVE_AND_PLAN_PROMPT = """\
You are a web UI navigation agent. Analyze the screenshot and plan the next action.

## Your Goal
{goal}

## Navigation History (last {history_count} steps)
{history_summary}

## Instructions

**PERCEPTION**: Identify ALL interactive UI elements visible on the page. For each element provide:
- A descriptive label (e.g. "Sign In button", "Search input field")
- The element type: button, input, link, image, text, heading, navigation, modal, form, dropdown
- A bounding box as {{x, y, width, height}} in pixels (origin: top-left of the {width}x{height} screenshot)
- A confidence score (0.0 to 1.0) for bounding box accuracy
- Whether the element is interactable
- Any accessibility issues (missing labels, poor contrast, small tap target)

**PLANNING**: Based on the detected elements, choose the SINGLE next action.

Select the **top 3 candidate elements** you considered for the action, marking which one is chosen.

Action types: click, type, scroll_down, scroll_up, press_key, hover, wait, go_back, done

{persona_prompt}

## Rules
1. Choose the action most likely to advance toward the goal.
2. If the goal appears achieved, use action_type "done".
3. Click coordinates = CENTER of the chosen element's bounding box.
4. Never enter real personal data — use test data like "test@example.com".
5. If a modal/popup is blocking, dismiss it first (click X, press Escape, or click outside).
6. If confidence < 0.65, prefer scrolling to reveal more content before acting.

Return a JSON object with this exact structure:
{{
  "perception": {{
    "page_description": "string",
    "page_purpose": "string",
    "has_modal_or_overlay": boolean,
    "loading_state": boolean,
    "elements": [
      {{
        "label": "string",
        "element_type": "string",
        "bbox": {{"x": int, "y": int, "width": int, "height": int}},
        "confidence": float,
        "interactable": boolean,
        "accessibility_issues": ["string"]
      }}
    ]
  }},
  "action": {{
    "action_type": "string",
    "target_element": "string or null",
    "coordinates": [x, y] or null,
    "input_text": "string or null",
    "key": "string or null",
    "seconds": int or null,
    "reasoning": "string (1-line explanation)",
    "confidence": float,
    "candidates": [
      {{
        "label": "string",
        "bbox": {{"x": int, "y": int, "width": int, "height": int}},
        "confidence": float,
        "is_chosen": boolean
      }}
    ]
  }}
}}
"""


EVALUATE_PROMPT = """\
You are evaluating the result of a web navigation action.

## Goal
{goal}

## Action Taken
- Type: {action_type}
- Target: {target_element}
- Reasoning: {reasoning}

## Instructions
Compare the BEFORE and AFTER screenshots. Evaluate:
1. Did the page visually change? (new content, navigation, URL change)
2. Did the action make progress toward the goal?
3. Is the goal now fully achieved?
4. Were there any UX friction points? Categorize each into one of these types:
   - **navigation**: Confusing menu structure, dead-end pages, unclear wayfinding, missing breadcrumbs
   - **contrast**: Low text/background contrast, hard-to-read text, poor color choices
   - **affordance**: Unclear clickable elements, missing hover states, small tap targets, ambiguous buttons
   - **copy**: Jargon, ambiguous labels, unclear instructions, confusing error messages
   - **error**: Error states, broken functionality, failed actions, unexpected behavior
   - **performance**: Slow loading, unnecessary delays, unresponsive elements
   - **accessibility**: Missing alt text, no focus indicators, small text, keyboard traps

{persona_evaluation_suffix}

Return a JSON object:
{{
  "progress_made": boolean,
  "goal_achieved": boolean,
  "page_changed": boolean,
  "description": "string describing what happened after the action",
  "friction_detected": ["string describing each friction point"],
  "friction_items": [
    {{"category": "navigation|contrast|affordance|copy|error|performance|accessibility", "description": "specific friction point", "severity": "low|medium|high|critical"}}
  ],
  "confidence": float
}}
"""


REPAIR_PROMPT = """\
The previous response was invalid JSON or didn't match the expected schema.

Error: {error_message}

Please fix the response and return valid JSON matching the schema exactly.
Keep the same analysis, just fix the formatting.

Previous response:
{previous_response}
"""


REPORT_SUMMARY_PROMPT = """\
You are a UX analyst generating a friction report.

## Session Data
- URL: {url}
- Goal: {goal}
- Persona: {persona_name}
- Total Steps: {total_steps}
- Outcome: {outcome}
- Time: {total_time}s

## Friction Points Collected
{friction_list}

## Step Timeline
{step_timeline}

## Instructions
Generate a comprehensive UX friction analysis:

1. **Executive Summary** (2-3 sentences): Overall assessment of the user experience
2. **Friction Score** (0-100): 0 = frictionless, 100 = unusable
3. **Top 3 Improvement Priorities**: Ranked by impact
4. **Per-item suggestions**: For each friction point, a specific actionable fix

Return JSON:
{{
  "executive_summary": "string",
  "friction_score": float,
  "improvement_priorities": ["string", "string", "string"],
  "item_suggestions": [
    {{"friction_index": int, "suggestion": "string"}}
  ]
}}
"""


RECOVERY_PROMPT = """\
You are a web navigation agent that is STUCK. Analyze the current screenshot and suggest the best recovery action.

## Goal
{goal}

## What has been tried (all failed)
{tried_actions}

## Current page URL
{current_url}

## Instructions
The fixed recovery strategies (scroll, Escape, click outside, go back) have not worked.
Look at the screenshot and suggest ONE specific intelligent action to unblock navigation:
- Maybe there's a cookie banner with a specific close button
- Maybe there's a different navigation path visible
- Maybe a specific element needs to be clicked to proceed
- Maybe the goal can be reached from here via a different approach

Coordinates must be within {width}x{height} pixels.

Return JSON:
{{
  "action_type": "click|type|press_key|scroll_down|scroll_up|go_back|done",
  "target_element": "description of element to target",
  "coordinates": [x, y] or null,
  "input_text": "string or null",
  "key": "string or null",
  "reasoning": "1-line explanation of why this specific action should unblock the agent",
  "confidence": float
}}
"""


def build_history_summary(steps: list, max_steps: int = 5) -> str:
    if not steps:
        return "No previous steps."
    recent = steps[-max_steps:]
    lines = []
    for step in recent:
        lines.append(
            f"Step {step.step_number}: {step.plan.action_type} "
            f"→ {step.plan.target_element or 'N/A'} "
            f"(confidence: {step.plan.confidence:.2f}) "
            f"| Result: {'progress' if step.evaluation.progress_made else 'no change'}"
        )
    return "\n".join(lines)
