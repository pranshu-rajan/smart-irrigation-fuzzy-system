"""Pydantic schemas for Simulation execution and telemetry."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SimulationRunRequest(BaseModel):
    scenario: str = Field(default="Normal", description="Environmental scenario name (Normal, Hot & Dry, Rainy, Cloudy, Heatwave, Water Scarcity)")
    duration_hours: int = Field(default=24, ge=1, le=720, description="Duration in hours (default 24)")
    timestep_minutes: int = Field(default=1, ge=1, le=60, description="Timestep in minutes (default 1)")
    controller_type: str = Field(default="fuzzy", description="Controller type ('fuzzy', 'fixed', 'none', 'pso_tuned')")
    supply_scenario: str = Field(default="Normal Supply", description="Shared supply scenario ('Abundant', 'Normal Supply', 'Moderate Scarcity', 'Severe Scarcity', 'Extreme Scarcity', 'Zero Supply')")
    supply_factor_override: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Optional override for available water percentage")
    seed: Optional[int] = Field(default=42, description="Random seed for deterministic weather generation")
    zone_ids: Optional[List[int]] = Field(default=None, description="Optional subset of zone IDs to simulate (default all configured)")


class SimulationSummaryResponse(BaseModel):
    id: str
    user_id: str
    scenario: str
    duration_hours: int
    timestep_minutes: int
    status: str
    controller_type: str
    supply_scenario: str
    summary_metrics: Dict[str, Any]
    started_at: str
    completed_at: Optional[str] = None
    created_at: str


class TimeseriesRecord(BaseModel):
    step: int
    timestamp: str
    zone_id: int
    soil_moisture: float
    target_moisture: float
    moisture_error: float
    rsm: float
    soil_stress: float
    weather_stress: float
    water_demand: float
    irrigation_command: float
    raw_request_mm: float
    allocated_irrigation_mm: float
    unmet_demand_mm: float
    water_volume_requested_l: float
    water_volume_allocated_l: float
    water_volume_unmet_l: float
    et0_mm: float
    etc_mm: float
    rainfall_mm: float
    effective_rainfall_mm: float
    water_balance_residual: float


class TimeseriesResponse(BaseModel):
    simulation_id: str
    total_records: int
    zone_count: int
    timesteps: int
    records: List[Dict[str, Any]]
