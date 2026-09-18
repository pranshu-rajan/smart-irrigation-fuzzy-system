"""AI Explanation and Agronomic Chat Router."""

from fastapi import APIRouter, Depends, HTTPException

from backend.app.schemas.allocation import AIChatRequest, AIChatResponse
from backend.app.services.ai_service import AIService
from backend.app.database.client import DatabaseRepository, get_db_repository

router = APIRouter(prefix="/ai", tags=["AI Explanation"])
ai_service = AIService()


@router.post("/chat", response_model=AIChatResponse)
def chat_with_ai(
    req: AIChatRequest,
    db: DatabaseRepository = Depends(get_db_repository),
):
    """
    Query the Agronomic AI advisor.
    Grounded via RAG with system architecture documentation and active simulation telemetry.
    Strictly advisory: cannot command actuators.
    """
    try:
        return ai_service.chat(req, db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Chat error: {str(e)}")
