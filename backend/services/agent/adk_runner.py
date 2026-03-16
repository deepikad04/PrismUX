"""ADK-based navigator runner that bridges ADK events to PrismUX SSE format.

Produces the same NavigationStep-like dicts so the frontend works unchanged.
"""

from __future__ import annotations

import base64
import logging
import time
from collections.abc import AsyncGenerator
from datetime import datetime

from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

from config import get_settings
from schemas.navigation import (
    ActionPlan,
    ActionResult,
    EvaluationResult,
    NavigationStep,
    PerceptionResult,
)
from schemas.persona import PersonaConfig
from services.browser.manager import get_browser_manager

from .adk_agent import build_adk_agent, clear_page_ref, set_page_ref
from .persona_engine import PersonaEngine

logger = logging.getLogger(__name__)


class ADKNavigatorRunner:
    """Runs the ADK LoopAgent and yields NavigationStep objects for SSE."""

    def __init__(
        self,
        session_id: str,
        url: str,
        goal: str,
        persona: PersonaConfig | None = None,
    ) -> None:
        self.session_id = session_id
        self.url = url
        self.goal = goal
        self.persona = persona
        self.steps: list[NavigationStep] = []
        self.status = "created"
        self.start_time: float = 0.0
        self.elapsed_seconds: float = 0.0

    async def run(self) -> AsyncGenerator[NavigationStep | dict, None]:
        """Run ADK agent, converting events to NavigationSteps."""
        settings = get_settings()
        browser_mgr = get_browser_manager()
        persona_prompt = PersonaEngine.get_planning_prompt(self.persona)

        self.status = "running"
        self.start_time = time.time()

        context = None
        step_num = 0

        try:
            context, page = await browser_mgr.new_session(self.url)
            set_page_ref(page)

            # Build ADK agent
            loop_agent = build_adk_agent(self.goal, persona_prompt)

            # Create runner
            runner = InMemoryRunner(
                agent=loop_agent,
                app_name="prismux",
            )

            # Create a session for the runner
            user_id = f"prismux_{self.session_id}"
            runner_session = await runner.session_service.create_session(
                app_name="prismux",
                user_id=user_id,
            )

            # Send initial message to start the agent
            user_msg = genai_types.Content(
                parts=[genai_types.Part.from_text(
                    f"Navigate to the page at {self.url} and accomplish this goal: {self.goal}"
                )],
                role="user",
            )

            # Yield a thought event to show ADK is running
            yield {
                "type": "thought",
                "phase": "plan",
                "message": f"ADK agent started — navigating to {self.url}",
            }

            # Process events from the runner
            last_screenshot = ""
            async for event in runner.run_async(
                user_id=user_id,
                session_id=runner_session.id,
                new_message=user_msg,
            ):
                # Extract useful information from ADK events
                if not event or not event.content or not event.content.parts:
                    continue

                for part in event.content.parts:
                    # Check for function calls (actions being taken)
                    if part.function_call:
                        fn_name = part.function_call.name
                        fn_args = dict(part.function_call.args) if part.function_call.args else {}

                        # Yield thought event for each action
                        yield {
                            "type": "thought",
                            "phase": "act",
                            "message": f"Calling {fn_name}({fn_args})",
                        }

                    # Check for function responses (results of actions)
                    if part.function_response:
                        fn_name = part.function_response.name
                        result = part.function_response.response

                        # If screenshot was taken, create a navigation step
                        if fn_name == "take_screenshot" and isinstance(result, dict):
                            screenshot_b64 = result.get("screenshot_b64", "")
                            if screenshot_b64:
                                last_screenshot = screenshot_b64

                        # If finish_navigation was called, we're done
                        if fn_name == "finish_navigation":
                            self.status = "completed"
                            yield {
                                "type": "thought",
                                "phase": "evaluate",
                                "message": f"Navigation complete: {result}",
                            }

                    # Check for text content (reasoning)
                    if part.text:
                        text = part.text.strip()
                        if text and len(text) > 10:
                            yield {
                                "type": "thought",
                                "phase": "perceive",
                                "message": text[:200],
                            }

                            # Create a navigation step for substantial text responses
                            if last_screenshot and ("click" in text.lower() or "scroll" in text.lower() or "type" in text.lower()):
                                step = self._make_step(
                                    step_num=step_num,
                                    description=text[:200],
                                    screenshot=last_screenshot,
                                    action_type="click",
                                    url=page.url,
                                )
                                self.steps.append(step)
                                step_num += 1
                                yield step

            if self.status != "completed":
                self.status = "completed"

        except Exception as e:
            logger.error("ADK navigator error: %s", e, exc_info=True)
            self.status = "error"
            yield {
                "type": "thought",
                "phase": "evaluate",
                "message": f"Error: {e}",
            }
        finally:
            self.elapsed_seconds = time.time() - self.start_time
            clear_page_ref()
            if context:
                await context.close()

    def _make_step(
        self,
        step_num: int,
        description: str,
        screenshot: str,
        action_type: str = "click",
        url: str = "",
    ) -> NavigationStep:
        return NavigationStep(
            step_number=step_num,
            perception=PerceptionResult(
                page_description=description,
                page_purpose="ADK-driven navigation",
                elements=[],
            ),
            plan=ActionPlan(
                action_type=action_type,
                reasoning=description,
                confidence=0.8,
            ),
            action_result=ActionResult(success=True, url_after=url),
            evaluation=EvaluationResult(
                progress_made=True,
                goal_achieved=False,
                description=description,
                confidence=0.8,
            ),
            screenshot_before_b64=screenshot,
            screenshot_after_b64=screenshot,
            timestamp=datetime.utcnow(),
        )

    def get_metrics(self) -> dict:
        return {
            "total_steps": len(self.steps),
            "retries": 0,
            "backtracks": 0,
            "time_seconds": self.elapsed_seconds,
            "friction_count": 0,
            "outcome": self.status,
            "recovery_steps": 0,
            "engine": "adk",
        }
