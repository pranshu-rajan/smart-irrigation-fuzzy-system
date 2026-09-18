"""Health and System Status Router."""

from fastapi import APIRouter
from backend.app.core.config import get_settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check():
    """System health and readiness check."""
    settings = get_settings()
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "supabase" if settings.has_supabase else "local_sqlite",
        "groq_enabled": bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your-groq-api-key-here"),
    }
