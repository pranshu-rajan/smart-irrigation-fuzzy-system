"""Zones Management Router."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.schemas.zones import ZoneCreateRequest, ZoneUpdateRequest, ZoneResponse
from backend.app.core.security import get_current_user, User
from backend.app.database.client import DatabaseRepository, get_db_repository
from backend.app.database.models import ZoneRecord

router = APIRouter(prefix="/zones", tags=["Zones"])


@router.get("", response_model=List[ZoneResponse])
def list_zones(
    user: User = Depends(get_current_user),
    db: DatabaseRepository = Depends(get_db_repository),
):
    """List all agricultural zones."""
    records = db.get_all_zones()
    return [ZoneResponse(**r.dict()) for r in records]


@router.get("/{zone_id}", response_model=ZoneResponse)
def get_zone(
    zone_id: int,
    user: User = Depends(get_current_user),
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Get an agricultural zone by ID."""
    rec = db.get_zone(zone_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")
    return ZoneResponse(**rec.dict())


@router.post("", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(
    req: ZoneCreateRequest,
    user: User = Depends(get_current_user),
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Create a new agricultural zone."""
    existing = db.get_zone(req.zone_id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Zone {req.zone_id} already exists")

    rec = ZoneRecord(
        zone_id=req.zone_id,
        name=req.name,
        crop=req.crop,
        soil=req.soil,
        area_m2=req.area_m2,
        field_capacity=req.field_capacity,
        wilting_point=req.wilting_point,
        saturation=req.saturation,
        initial_moisture=req.initial_moisture,
        target_moisture=req.target_moisture,
        root_zone_depth=req.root_zone_depth,
        kc=req.kc,
        priority=req.priority,
        user_id=user.id,
    )
    saved = db.save_zone(rec)
    return ZoneResponse(**saved.dict())


@router.put("/{zone_id}", response_model=ZoneResponse)
def update_zone(
    zone_id: int,
    req: ZoneUpdateRequest,
    user: User = Depends(get_current_user),
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Update agricultural zone parameters."""
    rec = db.get_zone(zone_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")

    data = req.dict(exclude_unset=True)
    for k, v in data.items():
        if hasattr(rec, k):
            setattr(rec, k, v)

    saved = db.save_zone(rec)
    return ZoneResponse(**saved.dict())


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(
    zone_id: int,
    user: User = Depends(get_current_user),
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Delete an agricultural zone."""
    success = db.delete_zone(zone_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")
    return None
