from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter

from routers.navigator import active_agents
from schemas.persona import ComparisonRequest, ComparisonResult, CustomPersonaCreate, PathStep, PersonaConfig, PersonaRunResult
from services.agent.navigator import NavigatorAgent
from services.agent.persona_engine import PersonaEngine
from services.reporting.friction_analyzer import FrictionAnalyzer

router = APIRouter(prefix="/api/personas", tags=["personas"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[PersonaConfig])
async def list_personas():
    return PersonaEngine.get_all_personas()


@router.post("/custom", response_model=PersonaConfig)
async def create_custom_persona(request: CustomPersonaCreate):
    """Create a custom persona with user-defined behavioral traits."""
    persona = PersonaEngine.register_custom(
        name=request.name,
        description=request.description,
        behavioral_traits=request.behavioral_traits,
        focus_areas=request.focus_areas,
        custom_instructions=request.custom_instructions,
    )
    return persona


@router.post("/compare", response_model=ComparisonResult)
async def compare_personas(request: ComparisonRequest):
    """Run the same goal with multiple personas sequentially and compare results."""
    results: list[PersonaRunResult] = []

    for persona_key in request.personas:
        persona = PersonaEngine.get_persona(persona_key)
        if not persona:
            logger.warning("Unknown persona: %s, skipping", persona_key)
            continue

        session_id = str(uuid.uuid4())[:8]
        agent = NavigatorAgent(
            session_id=session_id,
            url=request.url,
            goal=request.goal,
            persona=persona,
        )

        # Register agent so reports/replay endpoints can find it
        active_agents[session_id] = agent

        # Run the agent to completion
        async for _ in agent.run():
            pass

        metrics = agent.get_metrics()

        # Collect friction by category from step evaluations
        friction_by_cat: dict[str, int] = {}
        for step in agent.steps:
            if step.evaluation.friction_items:
                for fi in step.evaluation.friction_items:
                    friction_by_cat[fi.category] = friction_by_cat.get(fi.category, 0) + 1
            elif step.evaluation.friction_detected:
                friction_by_cat["other"] = friction_by_cat.get("other", 0) + len(step.evaluation.friction_detected)

        # Compute quick friction score
        severity_w = {"critical": 25, "high": 15, "medium": 8, "low": 3}
        raw = sum(
            severity_w.get(fi.severity, 5)
            for step in agent.steps
            for fi in step.evaluation.friction_items
        )
        density = raw / max(len(agent.steps), 1)
        fscore = min(density * 10, 100)
        if metrics["outcome"] in ("abandoned", "blocked", "error"):
            fscore = min(fscore + 20, 100)

        # Build friction items list for risk index calculation
        all_friction = [
            fi for step in agent.steps for fi in step.evaluation.friction_items
        ]
        risk_index = FrictionAnalyzer._compute_ux_risk_index(
            all_friction, metrics["total_steps"], metrics["outcome"],
            metrics["time_seconds"], round(fscore, 1),
        )

        # Build compact path for divergence view
        path = [
            PathStep(
                step=s.step_number,
                action=s.plan.action_type,
                target=s.plan.target_element,
                friction=bool(s.evaluation.friction_detected or s.evaluation.friction_items),
                url=s.action_result.url_after,
            )
            for s in agent.steps
            if not s.is_recovery
        ]

        # Generate one-line verdict
        if metrics["outcome"] == "completed":
            verdict = f"Reached goal in {metrics['total_steps']} steps with {metrics['friction_count']} friction points."
        elif metrics["outcome"] == "abandoned":
            last_reason = agent.steps[-1].recovery_reason if agent.steps else "unknown"
            verdict = f"Abandoned after {metrics['total_steps']} steps — {last_reason or 'stuck in loop'}."
        elif metrics["outcome"] == "blocked":
            verdict = f"Blocked after {metrics['total_steps']} steps — safety guard triggered."
        else:
            verdict = f"Failed after {metrics['total_steps']} steps."

        results.append(PersonaRunResult(
            persona_key=persona.key,
            persona_name=persona.name,
            total_steps=metrics["total_steps"],
            retries=metrics["retries"],
            backtracks=metrics["backtracks"],
            time_seconds=metrics["time_seconds"],
            friction_count=metrics["friction_count"],
            friction_by_category=friction_by_cat,
            friction_score=round(fscore, 1),
            ux_risk_index=risk_index,
            outcome=metrics["outcome"],
            session_id=session_id,
            path=path,
            verdict=verdict,
        ))
        logger.info(
            "Comparison run for %s: %s in %d steps",
            persona.name, metrics["outcome"], metrics["total_steps"],
        )

    return ComparisonResult(
        url=request.url,
        goal=request.goal,
        results=results,
    )
