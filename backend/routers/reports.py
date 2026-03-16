from __future__ import annotations

import asyncio
import csv
import io
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from routers.navigator import active_agents
from routers.sessions import sessions
from schemas.report import FrictionReport
from services.reporting.friction_analyzer import FrictionAnalyzer
from services.reporting.pdf_generator import generate_pdf
from services.storage.firestore import get_firestore_client

router = APIRouter(prefix="/api/reports", tags=["reports"])
logger = logging.getLogger(__name__)

# In-memory report cache
reports: dict[str, FrictionReport] = {}


@router.get("/{session_id}", response_model=FrictionReport)
async def get_report(session_id: str):
    """Generate or retrieve friction report for a completed session."""
    # Check cache
    if session_id in reports:
        return reports[session_id]

    # Check if agent exists with step data
    agent = active_agents.get(session_id)
    if agent and agent.status in ("completed", "abandoned", "blocked", "error"):
        analyzer = FrictionAnalyzer()
        report = await analyzer.analyze(
            session_id=session_id,
            url=agent.url,
            goal=agent.goal,
            persona=agent.persona.key if agent.persona else None,
            status=agent.status,
            steps=agent.steps,
            elapsed_seconds=agent.elapsed_seconds,
        )
        reports[session_id] = report

        # Persist to Firestore in background
        async def _persist():
            try:
                fs = get_firestore_client()
                await fs.save_report(session_id, report.model_dump(mode="json"))
                logger.info("Report %s persisted to Firestore", session_id)
            except Exception as exc:
                logger.warning("Firestore report persist failed for %s: %s", session_id, exc)

        asyncio.create_task(_persist())

        return report

    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    raise HTTPException(
        status_code=400,
        detail=f"Session status is '{session.status}'. Report available after navigation completes.",
    )


@router.get("/{session_id}/pdf")
async def export_pdf(session_id: str):
    """Generate and download a PDF friction report."""
    # Reuse existing report generation logic
    report = await get_report(session_id)

    pdf_bytes = generate_pdf(report)

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="prismux-report-{session_id}.pdf"',
        },
    )


@router.get("/{session_id}/csv")
async def export_csv(session_id: str):
    """Download friction items as CSV."""
    report = await get_report(session_id)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Category", "Severity", "Description", "Step",
        "Suggestion", "Persona",
    ])
    for item in report.friction_items:
        writer.writerow([
            item.category,
            item.severity,
            item.description,
            item.evidence_step,
            item.improvement_suggestion,
            item.persona_impacted or "",
        ])

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="prismux-friction-{session_id}.csv"',
        },
    )
