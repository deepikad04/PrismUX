from __future__ import annotations

import asyncio
import json
import logging
from collections import OrderedDict

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from config import get_settings
from routers.sessions import sessions
from schemas.navigation import NavigationStep
from services.agent.navigator import NavigatorAgent
from services.agent.persona_engine import PersonaEngine
from services.browser.manager import MAX_CONCURRENT_SESSIONS, get_browser_manager
from services.storage.cloud_storage import get_gcs_client
from services.storage.firestore import get_firestore_client

router = APIRouter(prefix="/api/navigate", tags=["navigator"])
logger = logging.getLogger(__name__)

# Active + completed agent sessions (kept for report generation)
active_agents: dict[str, NavigatorAgent] = {}

# Queue for sessions waiting for a browser slot
_queue: OrderedDict[str, asyncio.Event] = OrderedDict()
_QUEUE_TIMEOUT = 120  # seconds to wait in queue before giving up


def _notify_next_in_queue() -> None:
    """Wake the next queued session when a slot opens."""
    for sid, event in _queue.items():
        if not event.is_set():
            event.set()
            logger.info("Queue: woke session %s", sid)
            break


@router.get("/capacity")
async def get_capacity():
    """Return current session capacity info."""
    mgr = get_browser_manager()
    return {
        "active": mgr.active_sessions,
        "max": MAX_CONCURRENT_SESSIONS,
        "available": MAX_CONCURRENT_SESSIONS - mgr.active_sessions,
        "queued": len(_queue),
    }


@router.post("/{session_id}/start")
async def start_navigation(
    session_id: str,
    engine: str = Query(default="default", description="Navigation engine: 'default' or 'adk'"),
):
    """Start navigation and return SSE stream. Queues if all slots are busy."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session_id in active_agents:
        raise HTTPException(status_code=409, detail="Navigation already running")

    # Queue if at capacity
    mgr = get_browser_manager()
    if mgr.active_sessions >= MAX_CONCURRENT_SESSIONS:
        slot_event = asyncio.Event()
        _queue[session_id] = slot_event
        session.status = "queued"
        position = len(_queue)
        logger.info("Session %s queued at position %d", session_id, position)

        try:
            await asyncio.wait_for(slot_event.wait(), timeout=_QUEUE_TIMEOUT)
        except asyncio.TimeoutError:
            _queue.pop(session_id, None)
            session.status = "error"
            raise HTTPException(
                status_code=429,
                detail=f"Queue timeout after {_QUEUE_TIMEOUT}s — all browser slots remained busy.",
            )
        finally:
            _queue.pop(session_id, None)

    persona = PersonaEngine.get_persona(session.persona)

    # Choose engine
    settings = get_settings()
    use_adk = engine == "adk" and settings.adk_enabled

    if use_adk:
        from services.agent.adk_runner import ADKNavigatorRunner
        agent = ADKNavigatorRunner(
            session_id=session_id,
            url=session.url,
            goal=session.goal,
            persona=persona,
        )
    else:
        agent = NavigatorAgent(
            session_id=session_id,
            url=session.url,
            goal=session.goal,
            persona=persona,
        )
    active_agents[session_id] = agent

    async def event_generator():
        try:
            async for event in agent.run():
                if isinstance(event, NavigationStep):
                    step_data = event.model_dump(mode="json")
                    yield f"data: {json.dumps(step_data)}\n\n"
                elif isinstance(event, dict):
                    yield f"data: {json.dumps(event)}\n\n"

            # Send completion event
            metrics = agent.get_metrics()
            yield f"data: {json.dumps({'type': 'complete', 'status': agent.status, 'metrics': metrics})}\n\n"

            # Update in-memory session
            session.status = agent.status
            session.total_steps = len(agent.steps)
            session.completed = agent.status == "completed"

            # Persist session + steps to Firestore in background
            async def _persist():
                try:
                    fs = get_firestore_client()
                    await fs.save_session(session_id, session.model_dump(mode="json"))
                    step_dicts = [s.model_dump(mode="json") for s in agent.steps]
                    await fs.save_steps(session_id, step_dicts)
                    logger.info("Session %s + %d steps persisted to Firestore", session_id, len(step_dicts))
                except Exception as exc:
                    logger.warning("Firestore persist failed for %s: %s", session_id, exc)

            asyncio.create_task(_persist())

        except Exception as e:
            logger.error("SSE stream error: %s", e, exc_info=True)
            agent.status = "error"
            session.status = "error"
            session.total_steps = len(agent.steps)
            session.completed = False
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            # Notify next queued session that a slot may be available
            _notify_next_in_queue()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/hint")
async def send_hint(session_id: str, body: dict):
    """Send a user hint to the running agent for the next planning step."""
    agent = active_agents.get(session_id)
    if not agent:
        raise HTTPException(status_code=404, detail="No active agent for this session")
    if agent.status not in ("running", "created"):
        raise HTTPException(status_code=400, detail="Agent is not running")
    hint = (body.get("hint") or "").strip()
    if not hint:
        raise HTTPException(status_code=422, detail="Hint text is required")
    agent.add_hint(hint)
    return {"ok": True, "hint": hint}


@router.get("/{session_id}/steps")
async def get_session_steps(session_id: str):
    """Return all navigation steps for a completed session (used by replay)."""
    agent = active_agents.get(session_id)
    if agent:
        if agent.status not in ("completed", "abandoned", "blocked", "error"):
            raise HTTPException(status_code=400, detail="Session still in progress")
        return [step.model_dump(mode="json") for step in agent.steps]

    # Fall back to Firestore for persisted steps
    fs = get_firestore_client()
    persisted_steps = await fs.get_steps(session_id)
    if persisted_steps:
        # Re-hydrate screenshot URLs from GCS so replay can display images
        gcs = get_gcs_client()
        if gcs.bucket:
            for step in persisted_steps:
                sn = step.get("step_number", 0)
                step["screenshot_before_b64"] = ""
                step["screenshot_after_b64"] = ""
                step["screenshot_before_url"] = gcs.get_screenshot_url(session_id, sn)
                step["screenshot_after_url"] = gcs.get_screenshot_url(session_id, sn * 10 + 1)
        return persisted_steps

    raise HTTPException(status_code=404, detail="Session not found or expired")


@router.get("/{session_id}/status")
async def get_navigation_status(session_id: str):
    agent = active_agents.get(session_id)
    if agent:
        return {
            "session_id": session_id,
            "status": agent.status,
            "steps": len(agent.steps),
            "elapsed_seconds": agent.elapsed_seconds,
        }
    # Check queue
    if session_id in _queue:
        position = list(_queue.keys()).index(session_id) + 1
        return {
            "session_id": session_id,
            "status": "queued",
            "queue_position": position,
        }
    session = sessions.get(session_id)
    if session:
        return {
            "session_id": session_id,
            "status": session.status,
            "steps": session.total_steps,
        }
    raise HTTPException(status_code=404, detail="Session not found")
