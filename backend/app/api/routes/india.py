"""API routes for India National-Level Precision Irrigation."""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Query, HTTPException

from backend.app.schemas.india import (
    IndiaEvaluationRequest,
    IndiaEvaluationResponse,
    IndiaLocationLookupResponse,
)
from backend.app.services.india_location_service import india_location_service
from backend.app.services.india_irrigation_service import india_irrigation_service

router = APIRouter(prefix="/india", tags=["India National-Level Precision Irrigation"])


@router.get("/districts")
def list_districts() -> List[Dict[str, Any]]:
    """Return searchable index of all major Indian agricultural districts."""
    return india_location_service.list_all_districts()


@router.get("/lookup", response_model=IndiaLocationLookupResponse)
def lookup_location(
    query: Optional[str] = Query(None, description="City, district, or state name (e.g. 'Pune', 'Ludhiana')"),
    pincode: Optional[str] = Query(None, description="6-digit Indian postal code (e.g. '141004')"),
    latitude: Optional[float] = Query(None, description="Latitude (°N)"),
    longitude: Optional[float] = Query(None, description="Longitude (°E)"),
) -> IndiaLocationLookupResponse:
    """Resolve an Indian location to its ICAR agro-climatic zone, soil order, and seasonal crops."""
    return india_location_service.lookup(
        query=query,
        pincode=pincode,
        lat=latitude,
        lon=longitude,
    )


@router.post("/evaluate", response_model=IndiaEvaluationResponse)
async def evaluate_india_location(request: IndiaEvaluationRequest) -> IndiaEvaluationResponse:
    """Execute the complete end-to-end 5-stage fuzzy architecture for any Indian location."""
    try:
        return await india_irrigation_service.evaluate_location(request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating national precision irrigation for '{request.location_query}': {str(e)}"
        )
