from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from services.browser.manager import get_browser_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start browser on startup, close on shutdown."""
    settings = get_settings()
    browser_mgr = get_browser_manager()

    logger.info("Starting PrismUX backend...")
    await browser_mgr.start()
    logger.info("Playwright browser ready")

    yield

    logger.info("Shutting down PrismUX backend...")
    await browser_mgr.shutdown()


app = FastAPI(
    title="PrismUX",
    description="AI-powered UI Navigator with persona-based friction detection",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from routers import (
    health_router,
    navigator_router,
    personas_router,
    reports_router,
    sessions_router,
)

app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(navigator_router)
app.include_router(personas_router)
app.include_router(reports_router)


@app.get("/")
async def root():
    return {
        "service": "PrismUX",
        "description": "AI-powered UI Navigator Agent",
        "docs": "/docs",
    }
