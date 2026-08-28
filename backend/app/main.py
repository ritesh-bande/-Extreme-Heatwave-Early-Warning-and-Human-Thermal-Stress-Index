"""
Heatwave Early Warning System — FastAPI Backend

A Heat Stress & Mortality Risk Early Warning System that provides
ward-level risk assessment, weather forecasting, and automated alerts
for multiple stakeholder audiences.
"""

import asyncio
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.wards import router as wards_router
from app.api.alerts import router as alerts_router
from app.api.ev_safety import router as ev_safety_router
from app.tasks.scheduler import run_ingestion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run ingestion on startup, then periodically."""
    logger.info("🌡️ Heatwave EWS starting up — running initial ingestion...")
    try:
        await run_ingestion()
        logger.info("✅ Initial ingestion complete.")
    except Exception as e:
        logger.error(f"⚠️ Initial ingestion failed: {e}")

    yield  # App runs here

    logger.info("Heatwave EWS shutting down.")


app = FastAPI(
    title="Heatwave EWS API",
    description=(
        "Heat Stress & Mortality Risk Early Warning System. "
        "Provides ward-level thermal risk indices, vulnerability scoring, "
        "weather forecast ingestion, and role-specific alerts."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the Vite dev server and any local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://frontend:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.feedback import router as feedback_router
from app.api.citizens import router as citizens_router
from app.api.cooling import router as cooling_router

# ── Register API routers ──
app.include_router(wards_router)
app.include_router(alerts_router)
app.include_router(ev_safety_router)
app.include_router(feedback_router)
app.include_router(citizens_router)
app.include_router(cooling_router)


@app.get("/health", tags=["system"])
async def health_check():
    """Liveness / readiness probe."""
    return {"status": "ok"}


@app.post("/api/ingest", tags=["system"])
async def trigger_ingestion():
    """Manually trigger a weather ingestion cycle (for testing)."""
    await run_ingestion()
    return {"status": "ingestion_complete"}
