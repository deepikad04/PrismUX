from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from schemas.session import SessionCreate, SessionResponse
from services.storage.firestore import get_firestore_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# In-memory session store (also persisted to Firestore when available)
sessions: dict[str, SessionResponse] = {}


@router.post("", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    session_id = str(uuid.uuid4())[:8]
    session = SessionResponse(
        id=session_id,
        url=request.url,
        goal=request.goal,
        persona=request.persona,
        status="created",
        created_at=datetime.utcnow(),
    )
    sessions[session_id] = session

    # Persist to Firestore in background
    async def _persist():
        try:
            fs = get_firestore_client()
            await fs.save_session(session_id, session.model_dump(mode="json"))
            logger.info("Session %s persisted to Firestore", session_id)
        except Exception as exc:
            logger.warning("Firestore persist failed for %s: %s", session_id, exc)

    asyncio.create_task(_persist())

    return session


@router.get("", response_model=list[SessionResponse])
async def list_sessions():
    return list(sessions.values())


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
