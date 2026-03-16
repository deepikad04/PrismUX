from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from datetime import datetime

from config import get_settings
from schemas.navigation import ActionPlan, ActionResult, CategorizedFriction, EvaluationResult, NavigationStep, PerceptionResult
from schemas.persona import PersonaConfig
from services.browser.actions import ActionExecutor
from services.browser.manager import get_browser_manager
from services.browser.safety import SafetyGuard
from services.gemini.client import GeminiVisionService
from services.storage.cloud_storage import get_gcs_client

from .persona_engine import PersonaEngine
from .stuck_detector import StuckDetector

logger = logging.getLogger(__name__)


class NavigatorAgent:
    """Core Perceive-Plan-Act-Evaluate loop with confidence gating and recovery."""

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
        # User hints queue — populated via REST endpoint, consumed during PPAE
        self._hint_queue: asyncio.Queue[str] = asyncio.Queue()
        # Cross-page memory: persists across navigation steps
        self.memory: dict = {
            "visited_urls": [],
            "successful_elements": [],  # elements that led to progress
            "avoid_elements": [],       # elements that led to no change
            "goal_progress": [],        # milestones achieved
        }

    def add_hint(self, hint: str) -> None:
        """Add a user hint to be consumed on the next planning step."""
        self._hint_queue.put_nowait(hint)

    async def run(self) -> AsyncGenerator[NavigationStep | dict, None]:
        """Run the full agent loop, yielding steps and thought events for SSE."""
        settings = get_settings()
        browser_mgr = get_browser_manager()
        gemini = GeminiVisionService()
        executor = ActionExecutor()
        safety = SafetyGuard()
        stuck = StuckDetector()
        gcs = get_gcs_client()

        persona_prompt = PersonaEngine.get_planning_prompt(self.persona)
        eval_suffix = PersonaEngine.get_evaluation_suffix(self.persona)

        self.status = "running"
        self.start_time = time.time()

        context = None
        try:
            context, page = await browser_mgr.new_session(self.url)

            # Proactively dismiss cookie consent banners before navigation starts
            try:
                dismissed = await executor.dismiss_cookie_consent(page)
                if dismissed:
                    yield {"type": "thought", "phase": "perceive", "message": "Dismissed cookie consent banner"}
            except Exception as e:
                logger.debug("Cookie consent pre-check failed: %s", e)

            for step_num in range(settings.max_steps):
                # 1. PERCEIVE + PLAN
                yield {"type": "thought", "phase": "perceive", "message": f"Step {step_num}: Capturing screenshot and analyzing page..."}

                # Track visited URLs
                current_url = page.url
                if current_url not in self.memory["visited_urls"]:
                    self.memory["visited_urls"].append(current_url)

                screenshot_before = await executor.take_screenshot(page)

                # Build memory context for planning
                memory_prompt = self._build_memory_prompt()

                # Run DOM extraction in parallel with Gemini vision call
                dom_task = asyncio.create_task(self._extract_dom_elements(page))

                try:
                    perception, plan = await gemini.perceive_and_plan(
                        screenshot_b64=screenshot_before,
                        goal=self.goal,
                        history=self.steps[-5:],  # Only pass last 5 to limit memory
                        persona_prompt=persona_prompt + memory_prompt,
                        width=settings.screenshot_width,
                        height=settings.screenshot_height,
                    )
                except Exception as e:
                    logger.error("Perceive+Plan failed: %s", e)
                    dom_task.cancel()
                    self.status = "error"
                    break

                # Fuse DOM results with vision results for better targeting
                try:
                    dom_elements = await dom_task
                    if dom_elements and plan.action_type == "click" and plan.coordinates:
                        fused_coords = self._fuse_vision_dom(
                            plan, dom_elements,
                            settings.screenshot_width, settings.screenshot_height,
                        )
                        if fused_coords and fused_coords != plan.coordinates:
                            yield {
                                "type": "thought",
                                "phase": "plan",
                                "message": f"DOM fusion: adjusted target from {plan.coordinates} to {fused_coords}",
                                "data": {"dom_fusion": True},
                            }
                            plan = ActionPlan(
                                action_type=plan.action_type,
                                target_element=plan.target_element,
                                coordinates=fused_coords,
                                input_text=plan.input_text,
                                key=plan.key,
                                seconds=plan.seconds,
                                reasoning=f"[DOM-fused] {plan.reasoning}",
                                confidence=min(plan.confidence + 0.1, 1.0),
                                candidates=plan.candidates,
                            )
                except Exception as e:
                    logger.debug("DOM fusion skipped: %s", e)

                # Emit thought events for perception and plan
                elem_count = len(perception.elements)
                yield {
                    "type": "thought",
                    "phase": "perceive",
                    "message": f"I see {elem_count} elements — {perception.page_description[:120]}",
                    "data": {"element_count": elem_count, "page_purpose": perception.page_purpose},
                }
                yield {
                    "type": "thought",
                    "phase": "plan",
                    "message": f"Planning to {plan.action_type}: {plan.reasoning[:120]}",
                    "data": {"confidence": plan.confidence, "action_type": plan.action_type},
                }

                # 2. CONFIDENCE GATE
                if plan.confidence < settings.confidence_threshold and plan.action_type != "done":
                    logger.info(
                        "Low confidence (%.2f < %.2f), attempting fallback",
                        plan.confidence, settings.confidence_threshold,
                    )
                    fallback_plan = ActionPlan(
                        action_type="scroll_down",
                        reasoning=f"Low confidence ({plan.confidence:.2f}), scrolling to reveal more content",
                        confidence=0.5,
                        candidates=plan.candidates,
                    )
                    await executor.execute(page, fallback_plan)
                    screenshot_after_scroll = await executor.take_screenshot(page)

                    # Re-perceive after scroll
                    try:
                        perception, plan = await gemini.perceive_and_plan(
                            screenshot_b64=screenshot_after_scroll,
                            goal=self.goal,
                            history=self.steps[-5:],
                            persona_prompt=persona_prompt,
                            width=settings.screenshot_width,
                            height=settings.screenshot_height,
                        )
                        screenshot_before = screenshot_after_scroll
                    except Exception as e:
                        logger.warning("Re-perceive after scroll failed: %s", e)
                        # Use original plan

                # 3. SAFETY CHECK — extract page text for better detection
                page_text = ""
                try:
                    page_text = await page.inner_text("body", timeout=2000)
                    page_text = page_text[:500]  # Limit to first 500 chars
                except Exception:
                    pass

                should_stop, stop_reason = safety.should_stop(plan, page.url, page_text)
                if should_stop:
                    logger.warning("Safety guard triggered: %s", stop_reason)
                    step = self._make_step(
                        step_num=step_num,
                        perception=perception,
                        plan=ActionPlan(
                            action_type="done",
                            reasoning=f"Blocked: {stop_reason}",
                            confidence=1.0,
                        ),
                        action_result=ActionResult(success=False, url_after=page.url),
                        evaluation=EvaluationResult(
                            progress_made=False,
                            goal_achieved=False,
                            description=f"Safety stop: {stop_reason}",
                            confidence=1.0,
                        ),
                        screenshot_before=screenshot_before,
                        screenshot_after=screenshot_before,
                    )
                    self.steps.append(step)
                    yield step
                    self.status = "blocked"
                    break

                # 4. CHECK GOAL ACHIEVED
                if plan.action_type == "done":
                    step = self._make_step(
                        step_num=step_num,
                        perception=perception,
                        plan=plan,
                        action_result=ActionResult(success=True, url_after=page.url),
                        evaluation=EvaluationResult(
                            progress_made=True,
                            goal_achieved=True,
                            description=plan.reasoning,
                            confidence=plan.confidence,
                        ),
                        screenshot_before=screenshot_before,
                        screenshot_after=screenshot_before,
                    )
                    self.steps.append(step)
                    self._upload_screenshots(gcs, step)
                    yield step
                    self.status = "completed"
                    break

                # 5. GROUNDING CHECK — cross-validate Gemini target with DOM
                if plan.action_type == "click" and plan.coordinates and plan.target_element:
                    grounding_ok, grounding_msg = await self._grounding_check(
                        page, plan.coordinates, plan.target_element,
                    )
                    if not grounding_ok:
                        yield {
                            "type": "thought",
                            "phase": "plan",
                            "message": f"[!] Grounding mismatch: {grounding_msg}",
                            "data": {"grounding_warning": True},
                        }
                        # GROUNDING FALLBACK — try DOM text search for the target
                        fallback_coords = await self._grounding_fallback(
                            page, plan.target_element,
                        )
                        if fallback_coords:
                            yield {
                                "type": "thought",
                                "phase": "plan",
                                "message": f"Fallback: found '{plan.target_element}' via DOM at ({fallback_coords[0]}, {fallback_coords[1]})",
                            }
                            plan = ActionPlan(
                                action_type=plan.action_type,
                                target_element=plan.target_element,
                                coordinates=fallback_coords,
                                input_text=plan.input_text,
                                key=plan.key,
                                seconds=plan.seconds,
                                reasoning=f"[DOM fallback] {plan.reasoning}",
                                confidence=min(plan.confidence + 0.1, 1.0),
                                candidates=plan.candidates,
                            )

                # 6. ACT — capture pre-click state for verification
                pre_click_state = None
                if plan.action_type == "click" and plan.coordinates:
                    pre_click_state = await self._capture_element_state(page, plan.coordinates)

                yield {"type": "thought", "phase": "act", "message": f"Executing {plan.action_type}..."}
                action_result = await executor.execute(page, plan)

                # 6b. COOKIE CONSENT — re-check after navigation to a new page
                if action_result.success and page.url != current_url:
                    try:
                        await executor.dismiss_cookie_consent(page)
                    except Exception:
                        pass

                # 7. ACTION VERIFICATION — compare pre/post click state
                screenshot_after = await executor.take_screenshot(page)
                if pre_click_state is not None and plan.coordinates:
                    verified, verify_msg = await self._verify_action(
                        page, plan.coordinates, pre_click_state,
                    )
                    if not verified:
                        yield {
                            "type": "thought",
                            "phase": "evaluate",
                            "message": f"[!] Action verification: {verify_msg}",
                            "data": {"action_verification_failed": True},
                        }

                # 8. EVALUATE — skip API call for trivial actions
                _trivial = {"scroll_down", "scroll_up", "wait"}
                if plan.action_type in _trivial:
                    evaluation = EvaluationResult(
                        progress_made=False,
                        goal_achieved=False,
                        page_changed=plan.action_type != "wait",
                        description=f"{plan.action_type} executed — skipped full evaluation",
                        confidence=0.5,
                    )
                else:
                    try:
                        evaluation = await gemini.evaluate(
                            before_b64=screenshot_before,
                            after_b64=screenshot_after,
                            plan=plan,
                            goal=self.goal,
                            persona_evaluation_suffix=eval_suffix,
                        )
                    except Exception as e:
                        logger.error("Evaluation failed: %s", e)
                        evaluation = EvaluationResult(
                            progress_made=False,
                            goal_achieved=False,
                            description=f"Evaluation error: {e}",
                            confidence=0.1,
                        )

                # Persona constraint checks — merge into evaluation
                persona_frictions = PersonaEngine.check_constraints(
                    self.persona, perception.elements, page_text,
                )
                if persona_frictions:
                    evaluation.friction_items.extend(persona_frictions)
                    # Also add to friction_detected for backward compat
                    for pf in persona_frictions:
                        evaluation.friction_detected.append(f"[{pf.category}] {pf.description}")

                # Emit evaluation thought
                friction_list = evaluation.friction_detected
                eval_msg = evaluation.description[:120]
                if friction_list:
                    eval_msg += f" | Friction: {', '.join(friction_list[:3])}"
                yield {
                    "type": "thought",
                    "phase": "evaluate",
                    "message": eval_msg,
                    "data": {
                        "progress_made": evaluation.progress_made,
                        "goal_achieved": evaluation.goal_achieved,
                        "friction_count": len(friction_list),
                    },
                }

                # UPDATE CROSS-PAGE MEMORY
                self._update_memory(plan, evaluation, page.url)

                # Build step
                step = self._make_step(
                    step_num=step_num,
                    perception=perception,
                    plan=plan,
                    action_result=action_result,
                    evaluation=evaluation,
                    screenshot_before=screenshot_before,
                    screenshot_after=screenshot_after,
                )
                self.steps.append(step)
                self._upload_screenshots(gcs, step)
                yield step

                # 7. CHECK GOAL COMPLETION
                if evaluation.goal_achieved:
                    self.status = "completed"
                    break

                # 8. STUCK DETECTION + RECOVERY
                if stuck.is_stuck(step, screenshot_after_b64=screenshot_after):
                    recovery_plan = stuck.get_recovery_action()
                    logger.info("Recovery action: %s", recovery_plan.reasoning)

                    # Before abandoning, try Gemini-powered intelligent recovery
                    if recovery_plan.action_type == "done":
                        yield {"type": "thought", "phase": "plan", "message": "Fixed recovery exhausted — asking Gemini for intelligent recovery..."}
                        try:
                            tried = [s.plan.reasoning for s in self.steps[-6:] if s.is_recovery]
                            ai_plan = await gemini.suggest_recovery(
                                screenshot_b64=screenshot_after,
                                goal=self.goal,
                                tried_actions=tried,
                                current_url=page.url,
                                width=settings.screenshot_width,
                                height=settings.screenshot_height,
                            )
                            if ai_plan.action_type != "done":
                                yield {"type": "thought", "phase": "plan", "message": f"AI Recovery: {ai_plan.reasoning}"}
                                recovery_plan = ai_plan
                                # Give one more chance — don't abandon yet
                                stuck.recovery_level = 5  # So next stuck triggers real abandon
                            else:
                                logger.info("Gemini also recommends abandoning")
                        except Exception as e:
                            logger.warning("Gemini recovery suggestion failed: %s", e)

                    if recovery_plan.action_type == "done":
                        self.status = "abandoned"
                        recovery_step = self._make_step(
                            step_num=step_num + 1,
                            perception=perception,
                            plan=recovery_plan,
                            action_result=ActionResult(success=False, url_after=page.url),
                            evaluation=EvaluationResult(
                                progress_made=False,
                                goal_achieved=False,
                                description="Agent abandoned after recovery attempts exhausted",
                                confidence=0.2,
                            ),
                            screenshot_before=screenshot_after,
                            screenshot_after=screenshot_after,
                            is_recovery=True,
                            recovery_reason=recovery_plan.reasoning,
                        )
                        self.steps.append(recovery_step)
                        yield recovery_step
                        break

                    # Execute recovery action
                    recovery_result = await executor.execute(page, recovery_plan)
                    recovery_screenshot = await executor.take_screenshot(page)
                    recovery_step = self._make_step(
                        step_num=step_num + 1,
                        perception=perception,
                        plan=recovery_plan,
                        action_result=recovery_result,
                        evaluation=EvaluationResult(
                            progress_made=False,
                            goal_achieved=False,
                            description=f"Recovery: {recovery_plan.reasoning}",
                            confidence=0.5,
                        ),
                        screenshot_before=screenshot_after,
                        screenshot_after=recovery_screenshot,
                        is_recovery=True,
                        recovery_reason=recovery_plan.reasoning,
                    )
                    self.steps.append(recovery_step)
                    self._upload_screenshots(gcs, recovery_step)
                    yield recovery_step

            else:
                # Max steps reached
                self.status = "abandoned"

        except Exception as e:
            logger.error("Navigator agent error: %s", e, exc_info=True)
            self.status = "error"

        finally:
            self.elapsed_seconds = time.time() - self.start_time
            if context:
                await context.close()
            logger.info(
                "Session %s finished: status=%s, steps=%d, time=%.1fs",
                self.session_id, self.status, len(self.steps), self.elapsed_seconds,
            )

    @staticmethod
    async def _capture_element_state(page, coordinates: tuple[int, int]) -> dict:
        """Capture DOM state at click coordinates before the action."""
        x, y = coordinates
        try:
            return await page.evaluate(
                """([x, y]) => {
                    const el = document.elementFromPoint(x, y);
                    if (!el) return { exists: false, url: location.href };
                    const rect = el.getBoundingClientRect();
                    return {
                        exists: true,
                        url: location.href,
                        tagName: el.tagName,
                        text: (el.textContent || '').trim().substring(0, 100),
                        className: el.className || '',
                        boundingTop: Math.round(rect.top),
                        boundingLeft: Math.round(rect.left),
                        boundingWidth: Math.round(rect.width),
                        boundingHeight: Math.round(rect.height),
                    };
                }""",
                [x, y],
            )
        except Exception:
            return {"exists": False, "url": ""}

    @staticmethod
    async def _verify_action(
        page, coordinates: tuple[int, int], pre_state: dict,
    ) -> tuple[bool, str]:
        """Compare pre/post click state to verify the action had an effect."""
        x, y = coordinates
        try:
            post_state = await page.evaluate(
                """([x, y]) => {
                    const el = document.elementFromPoint(x, y);
                    if (!el) return { exists: false, url: location.href };
                    const rect = el.getBoundingClientRect();
                    return {
                        exists: true,
                        url: location.href,
                        tagName: el.tagName,
                        text: (el.textContent || '').trim().substring(0, 100),
                        className: el.className || '',
                        boundingTop: Math.round(rect.top),
                        boundingLeft: Math.round(rect.left),
                        boundingWidth: Math.round(rect.width),
                        boundingHeight: Math.round(rect.height),
                    };
                }""",
                [x, y],
            )

            # URL changed — navigation happened, click worked
            if post_state.get("url") != pre_state.get("url"):
                return True, ""

            # Element disappeared — likely modal closed or navigation
            if not post_state.get("exists"):
                return True, ""

            # Element changed (different tag, text, class, or position)
            if pre_state.get("exists"):
                changes = []
                if post_state.get("tagName") != pre_state.get("tagName"):
                    changes.append("element replaced")
                if post_state.get("text") != pre_state.get("text"):
                    changes.append("text changed")
                if post_state.get("className") != pre_state.get("className"):
                    changes.append("class changed")
                if (abs(post_state.get("boundingTop", 0) - pre_state.get("boundingTop", 0)) > 5 or
                    abs(post_state.get("boundingLeft", 0) - pre_state.get("boundingLeft", 0)) > 5):
                    changes.append("position shifted")

                if changes:
                    return True, ""

                # Nothing changed at all — click may not have had an effect
                return False, f"No visible change detected after click at ({x}, {y})"

            return True, ""

        except Exception as e:
            logger.debug("Action verification error: %s", e)
            return True, ""

    @staticmethod
    async def _grounding_check(
        page, coordinates: tuple[int, int], target_label: str,
    ) -> tuple[bool, str]:
        """Cross-validate Gemini's chosen click target with Playwright DOM text."""
        x, y = coordinates
        try:
            # Use Playwright's elementFromPoint to get the actual DOM element
            el_text = await page.evaluate(
                """([x, y]) => {
                    const el = document.elementFromPoint(x, y);
                    if (!el) return '';
                    return (el.textContent || el.getAttribute('aria-label') || el.getAttribute('alt') || '').trim().substring(0, 200);
                }""",
                [x, y],
            )
            if not el_text:
                return True, ""  # No text found — can't validate, skip

            # Fuzzy match: check if any significant word from target appears in DOM text
            target_words = {w.lower() for w in target_label.split() if len(w) > 2}
            dom_words = {w.lower() for w in el_text.split() if len(w) > 2}

            if not target_words:
                return True, ""

            overlap = target_words & dom_words
            if overlap:
                return True, ""
            else:
                return False, f"Expected '{target_label}' but DOM shows '{el_text[:80]}'"

        except Exception as e:
            logger.debug("Grounding check failed: %s", e)
            return True, ""  # On error, don't block the action

    def _drain_hints(self) -> list[str]:
        """Drain all pending user hints from the queue."""
        hints: list[str] = []
        while not self._hint_queue.empty():
            try:
                hints.append(self._hint_queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return hints

    def _build_memory_prompt(self) -> str:
        """Build a memory context string to inject into the planning prompt."""
        parts = []

        # Drain user hints — highest priority context
        hints = self._drain_hints()
        if hints:
            parts.append(f"\n## USER GUIDANCE (follow this)\n" + "\n".join(f"- {h}" for h in hints))

        if self.memory["visited_urls"]:
            parts.append(f"\nPages visited: {', '.join(self.memory['visited_urls'][-5:])}")
        if self.memory["successful_elements"]:
            recent = self.memory["successful_elements"][-5:]
            parts.append(f"Successful interactions: {', '.join(recent)}")
        if self.memory["avoid_elements"]:
            recent = self.memory["avoid_elements"][-5:]
            parts.append(f"AVOID (led to no progress): {', '.join(recent)}")
        if self.memory["goal_progress"]:
            parts.append(f"Progress so far: {', '.join(self.memory['goal_progress'][-3:])}")
        if not parts:
            return ""
        return "\n\n## Agent Memory\n" + "\n".join(parts)

    def _update_memory(
        self, plan: ActionPlan, evaluation: EvaluationResult, current_url: str,
    ) -> None:
        """Update cross-page memory based on action outcome."""
        target = plan.target_element or plan.action_type
        if evaluation.progress_made:
            if target not in self.memory["successful_elements"]:
                self.memory["successful_elements"].append(target)
            if evaluation.description and len(evaluation.description) > 10:
                summary = evaluation.description[:80]
                if summary not in self.memory["goal_progress"]:
                    self.memory["goal_progress"].append(summary)
        elif plan.action_type == "click" and not evaluation.progress_made:
            if target not in self.memory["avoid_elements"]:
                self.memory["avoid_elements"].append(target)
        # Track URL
        if current_url not in self.memory["visited_urls"]:
            self.memory["visited_urls"].append(current_url)

    @staticmethod
    async def _grounding_fallback(
        page, target_label: str,
    ) -> tuple[int, int] | None:
        """DOM text search fallback when vision coordinates miss the target."""
        try:
            # Search for clickable elements matching the target label
            result = await page.evaluate(
                """(label) => {
                    const lower = label.toLowerCase();
                    const selectors = ['a', 'button', '[role="button"]', '[role="link"]', 'input[type="submit"]'];
                    for (const sel of selectors) {
                        for (const el of document.querySelectorAll(sel)) {
                            const text = (el.textContent || el.getAttribute('aria-label') || '').trim().toLowerCase();
                            if (text.includes(lower) || lower.includes(text)) {
                                const rect = el.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0) {
                                    return [
                                        Math.round(rect.x + rect.width / 2),
                                        Math.round(rect.y + rect.height / 2),
                                    ];
                                }
                            }
                        }
                    }
                    return null;
                }""",
                target_label,
            )
            return tuple(result) if result else None
        except Exception as e:
            logger.debug("Grounding fallback failed: %s", e)
            return None

    @staticmethod
    async def _extract_dom_elements(page) -> list[dict]:
        """Extract interactive DOM elements with bounding boxes for vision fusion."""
        try:
            return await page.evaluate("""() => {
                const selectors = 'a, button, [role="button"], [role="link"], input, select, textarea, [tabindex], [onclick]';
                const results = [];
                for (const el of document.querySelectorAll(selectors)) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width < 5 || rect.height < 5) continue;
                    if (rect.bottom < 0 || rect.top > window.innerHeight) continue;
                    const text = (el.textContent || el.getAttribute('aria-label') || el.getAttribute('alt') || el.getAttribute('placeholder') || '').trim().substring(0, 100);
                    if (!text && el.tagName !== 'INPUT') continue;
                    results.push({
                        tag: el.tagName.toLowerCase(),
                        text: text,
                        x: Math.round(rect.x + rect.width / 2),
                        y: Math.round(rect.y + rect.height / 2),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                    });
                }
                return results.slice(0, 50);  // Limit to top 50 elements
            }""")
        except Exception as e:
            logger.debug("DOM extraction failed: %s", e)
            return []

    @staticmethod
    def _fuse_vision_dom(
        plan: ActionPlan,
        dom_elements: list[dict],
        viewport_width: int,
        viewport_height: int,
    ) -> tuple[int, int] | None:
        """Cross-reference Gemini's target with DOM elements.

        If Gemini picked coordinates that don't match any DOM element but the
        target label matches a DOM element, use the DOM element's coordinates.
        """
        if not plan.target_element or not plan.coordinates:
            return None

        vx, vy = plan.coordinates
        target_lower = plan.target_element.lower()
        target_words = {w for w in target_lower.split() if len(w) > 2}

        # Check if Gemini's coords already land on a matching DOM element
        for el in dom_elements:
            dx = abs(el["x"] - vx)
            dy = abs(el["y"] - vy)
            if dx < el["width"] // 2 + 10 and dy < el["height"] // 2 + 10:
                # Vision coords land on a DOM element — already good
                el_words = {w for w in el["text"].lower().split() if len(w) > 2}
                if target_words & el_words:
                    return None  # No adjustment needed

        # Vision coords don't land on a matching element — search for text match in DOM
        best_match = None
        best_score = 0
        for el in dom_elements:
            el_text = el["text"].lower()
            el_words = {w for w in el_text.split() if len(w) > 2}

            # Score: word overlap + partial string match
            overlap = len(target_words & el_words)
            contains = 1 if (target_lower in el_text or el_text in target_lower) else 0
            score = overlap + contains * 2

            if score > best_score:
                best_score = score
                best_match = el

        if best_match and best_score >= 2:
            new_x = min(best_match["x"], viewport_width - 1)
            new_y = min(best_match["y"], viewport_height - 1)
            return (new_x, new_y)

        return None

    def _make_step(
        self,
        step_num: int,
        perception: PerceptionResult,
        plan: ActionPlan,
        action_result: ActionResult,
        evaluation: EvaluationResult,
        screenshot_before: str,
        screenshot_after: str,
        is_recovery: bool = False,
        recovery_reason: str | None = None,
    ) -> NavigationStep:
        return NavigationStep(
            step_number=step_num,
            perception=perception,
            plan=plan,
            action_result=action_result,
            evaluation=evaluation,
            screenshot_before_b64=screenshot_before,
            screenshot_after_b64=screenshot_after,
            timestamp=datetime.utcnow(),
            is_recovery=is_recovery,
            recovery_reason=recovery_reason,
        )

    def _upload_screenshots(self, gcs, step: NavigationStep) -> None:
        """Upload screenshots to GCS in a background thread (non-blocking)."""
        import asyncio

        async def _upload():
            try:
                loop = asyncio.get_event_loop()
                if step.screenshot_before_b64:
                    await loop.run_in_executor(
                        None, gcs.upload_screenshot,
                        self.session_id, step.step_number, step.screenshot_before_b64,
                    )
                if step.screenshot_after_b64:
                    await loop.run_in_executor(
                        None, gcs.upload_screenshot,
                        self.session_id, step.step_number * 10 + 1, step.screenshot_after_b64,
                    )
                logger.debug("GCS upload completed for step %d", step.step_number)
            except Exception as e:
                logger.warning("GCS upload failed for step %d: %s", step.step_number, e)

        asyncio.create_task(_upload())

    def get_metrics(self) -> dict:
        """Compute run metrics for reporting."""
        retries = sum(1 for s in self.steps if s.is_recovery and "scroll" in (s.recovery_reason or ""))
        backtracks = sum(1 for s in self.steps if s.is_recovery and "back" in (s.recovery_reason or ""))
        friction_count = sum(len(s.evaluation.friction_detected) for s in self.steps)

        return {
            "total_steps": len(self.steps),
            "retries": retries,
            "backtracks": backtracks,
            "time_seconds": self.elapsed_seconds,
            "friction_count": friction_count,
            "outcome": self.status,
            "recovery_steps": sum(1 for s in self.steps if s.is_recovery),
        }
