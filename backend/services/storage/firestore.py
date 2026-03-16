from __future__ import annotations

import logging

from config import get_settings

logger = logging.getLogger(__name__)

_firestore_client: FirestoreClient | None = None


class FirestoreClient:
    """Firestore client for session and report persistence."""

    def __init__(self) -> None:
        self.db = None
        settings = get_settings()
        if settings.firestore_project:
            try:
                from google.cloud import firestore
                self.db = firestore.AsyncClient(project=settings.firestore_project)
                logger.info("Firestore connected to project: %s", settings.firestore_project)
            except Exception as e:
                logger.warning("Firestore not available: %s", e)

    async def save_session(self, session_id: str, data: dict) -> None:
        if self.db is None:
            return
        await self.db.collection("sessions").document(session_id).set(data)

    async def get_session(self, session_id: str) -> dict | None:
        if self.db is None:
            return None
        doc = await self.db.collection("sessions").document(session_id).get()
        return doc.to_dict() if doc.exists else None

    async def save_report(self, session_id: str, data: dict) -> None:
        if self.db is None:
            return
        await self.db.collection("reports").document(session_id).set(data)

    async def get_report(self, session_id: str) -> dict | None:
        if self.db is None:
            return None
        doc = await self.db.collection("reports").document(session_id).get()
        return doc.to_dict() if doc.exists else None

    async def save_steps(self, session_id: str, steps: list[dict]) -> None:
        """Persist navigation steps (without large base64 screenshots)."""
        if self.db is None:
            return
        # Strip base64 screenshots to keep Firestore docs under 1MB
        stripped = []
        for s in steps:
            copy = {k: v for k, v in s.items() if k not in ("screenshot_before_b64", "screenshot_after_b64")}
            copy["screenshot_before_b64"] = ""
            copy["screenshot_after_b64"] = ""
            stripped.append(copy)
        await self.db.collection("steps").document(session_id).set({"steps": stripped})

    async def get_steps(self, session_id: str) -> list[dict] | None:
        if self.db is None:
            return None
        doc = await self.db.collection("steps").document(session_id).get()
        if doc.exists:
            data = doc.to_dict()
            return data.get("steps")
        return None

    async def list_sessions(self, limit: int = 20) -> list[dict]:
        if self.db is None:
            return []
        docs = self.db.collection("sessions").order_by(
            "created_at", direction="DESCENDING"
        ).limit(limit).stream()
        results = []
        async for doc in docs:
            results.append(doc.to_dict())
        return results


def get_firestore_client() -> FirestoreClient:
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = FirestoreClient()
    return _firestore_client
