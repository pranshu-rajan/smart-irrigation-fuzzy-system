"""Pydantic schemas for Zone management."""

from typing import Optional
from pydantic import BaseModel, Field


class ZoneBase(BaseModel):
    zone_id: int = Field(..., ge=1, le=10, description="Agricultural Zone identifier")
    name: str = Field(..., min_length=1, max_length=100)
    crop: str = Field(..., description="Crop name (e.g., Tomato, Wheat, Maize)")
    soil: str = Field(..., description="Soil textural class (e.g., Loam, Sandy, Clay)")
    area_m2: float = Field(..., gt=0.0, le=10000.0, description="Cultivated area in m²")
    field_capacity: float = Field(..., gt=0.0, le=100.0, description="Soil Field Capacity (%)")
    wilting_point: float = Field(..., gt=0.0, le=100.0, description="Permanent Wilting Point (%)")
    saturation: float = Field(default=85.0, gt=0.0, le=100.0, description="Soil Saturation (%)")
    initial_moisture: float = Field(..., gt=0.0, le=100.0, description="Initial Soil Moisture (%)")
    target_moisture: float = Field(..., gt=0.0, le=100.0, description="Target Moisture Setpoint (%)")
    root_zone_depth: float = Field(..., gt=0.0, le=5.0, description="Effective Root Depth (m)")
    kc: float = Field(..., gt=0.0, le=2.5, description="Crop Coefficient Kc")
    priority: float = Field(..., ge=0.0, le=100.0, description="Agronomic Priority Weight [0, 100]%")


class ZoneCreateRequest(ZoneBase):
    pass


class ZoneUpdateRequest(BaseModel):
    name: Optional[str] = None
    crop: Optional[str] = None
    soil: Optional[str] = None
    area_m2: Optional[float] = None
    field_capacity: Optional[float] = None
    wilting_point: Optional[float] = None
    saturation: Optional[float] = None
    initial_moisture: Optional[float] = None
    target_moisture: Optional[float] = None
    root_zone_depth: Optional[float] = None
    kc: Optional[float] = None
    priority: Optional[float] = None


class ZoneResponse(ZoneBase):
    id: str
    user_id: str
