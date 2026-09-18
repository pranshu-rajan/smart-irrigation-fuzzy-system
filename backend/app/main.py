"""FastAPI application entry point for the Smart Multizone Irrigation Platform.

Provides RESTful endpoints for:
- System status and health checks
- Agricultural zone CRUD
- Crop and soil reference databases
- Environmental simulation execution and timeseries
- Fuzzy inference subsystem inspection and live evaluation
- Bounded multi-zone water allocation
- Offline Particle Swarm Optimization (PSO) tuning
- Groq AI explanation & RAG assistance
- ReportLab PDF engineering reports & telemetry export
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.zones import router as zones_router
from backend.app.api.routes.crops import router as crops_router
from backend.app.api.routes.soils import router as soils_router
from backend.app.api.routes.scenarios import router as scenarios_router
from backend.app.api.routes.simulations import router as simulations_router
from backend.app.api.routes.fuzzy import router as fuzzy_router
from backend.app.api.routes.allocation import router as allocation_router
from backend.app.api.routes.optimization import router as optimization_router
from backend.app.api.routes.ai import router as ai_router
from backend.app.api.routes.reports import router as reports_router

logger = get_logger("main")
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Hierarchical Adaptive Fuzzy Control Platform for Smart Multizone Irrigation",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api
app.include_router(health_router, prefix="/api")
app.include_router(zones_router, prefix="/api")
app.include_router(crops_router, prefix="/api")
app.include_router(soils_router, prefix="/api")
app.include_router(scenarios_router, prefix="/api")
app.include_router(simulations_router, prefix="/api")
app.include_router(fuzzy_router, prefix="/api")
app.include_router(allocation_router, prefix="/api")
app.include_router(optimization_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(reports_router, prefix="/api")


# Backward compatibility root health check
@app.get("/health", tags=["System"])
def root_health_check():
    """Root health and readiness check."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "supabase" if settings.has_supabase else "local_sqlite",
        "groq_enabled": bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your-groq-api-key-here"),
    }


@app.get("/", tags=["System"])
def root():
    """Root API welcome."""
    return {
        "message": "Smart Multizone Fuzzy Irrigation Platform API is running.",
        "docs": "/docs",
        "version": settings.APP_VERSION,
    }


@app.get("/api", tags=["System"])
def api_root():
    """API base route returning endpoint index."""
    return {
        "status": "healthy",
        "message": "Smart Multizone Fuzzy Irrigation Platform API is running.",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/health",
            "zones": "/api/zones",
            "simulations": "/api/simulations/run",
            "fuzzy": "/api/fuzzy/overview",
            "allocation": "/api/allocation/config",
            "optimization": "/api/optimization/summary",
            "scenarios": "/api/scenarios",
            "reports": "/api/reports/generate"
        },
        "version": settings.APP_VERSION,
    }
