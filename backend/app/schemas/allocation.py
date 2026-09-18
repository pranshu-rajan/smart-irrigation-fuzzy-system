"""Pydantic schemas for Water Allocation, Optimization, AI, and Reports."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# --- Allocation Schemas ---
class AllocationEvaluateRequest(BaseModel):
    available_water_pct: float = Field(..., ge=0.0, le=100.0, description="Available shared supply (%)")
    available_supply_l: Optional[float] = Field(default=None, ge=0.0, description="Optional available supply in Liters")
    requests_mm: Dict[int, float] = Field(..., description="Requested depth per zone in mm")
    stresses_pct: Optional[Dict[int, float]] = Field(default=None, description="Optional stress per zone (%)")
    priorities_pct: Optional[Dict[int, float]] = Field(default=None, description="Optional priority per zone (%)")


class AllocationSweepRequest(BaseModel):
    requests_mm: Dict[int, float] = Field(..., description="Requested depth per zone in mm")
    priorities_pct: Optional[Dict[int, float]] = Field(default=None, description="Optional priority per zone (%)")


class ZoneAllocationDetail(BaseModel):
    zone_id: int
    area_m2: float
    requested_depth_mm: float
    requested_volume_l: float
    raw_allocation_factor_pct: float
    allocated_depth_mm: float
    allocated_volume_l: float
    unmet_depth_mm: float
    unmet_volume_l: float
    fulfillment_ratio: float


class AllocationEvaluateResponse(BaseModel):
    available_water_pct: float
    available_supply_l: float
    total_requested_l: float
    total_allocated_l: float
    total_unmet_l: float
    system_fulfillment_ratio: float
    is_supply_constrained: bool
    zones: List[ZoneAllocationDetail]


# --- Optimization Schemas ---
class OptimizationRunRequest(BaseModel):
    swarm_size: int = Field(default=15, ge=3, le=50, description="Particle swarm size")
    max_iterations: int = Field(default=20, ge=1, le=100, description="Maximum iterations")
    seed: int = Field(default=42, description="Random seed")
    weights: Optional[Dict[str, float]] = Field(default=None, description="Fitness weights: tracking, water, deficit, smoothness")


class ConvergencePoint(BaseModel):
    iteration: int
    best_fitness: float
    mean_fitness: float
    global_best_fitness: float
    elapsed_seconds: float


class ParameterComparisonItem(BaseModel):
    name: str
    target_var: str
    linguistic_set: str
    point_index: int
    min_bound: float
    max_bound: float
    baseline_value: float
    optimized_value: float
    delta: float


class OptimizationSummaryResponse(BaseModel):
    id: str
    user_id: str
    status: str
    seed: int
    swarm_size: int
    max_iterations: int
    baseline_fitness: float
    optimized_fitness: float
    fitness_improvement_pct: float
    convergence: List[ConvergencePoint]
    parameters: List[ParameterComparisonItem]
    created_at: str
    completed_at: Optional[str] = None


# --- AI Schemas ---
class AIChatRequest(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=1000)
    simulation_id: Optional[str] = Field(default=None, description="Optional simulation ID for grounded telemetry")
    zone_id: Optional[int] = Field(default=None, description="Optional zone ID")
    conversation_id: Optional[str] = Field(default=None)


class AIChatResponse(BaseModel):
    response: str
    conversation_id: str
    grounded_context_summary: Optional[Dict[str, Any]] = None
    source: str = "groq"  # groq or rule_based_fallback


# --- Report Schemas ---
class ReportGenerateRequest(BaseModel):
    simulation_id: str
    include_ai_summary: bool = True
    optimization_id: Optional[str] = None


class ReportResponse(BaseModel):
    id: str
    simulation_id: Optional[str]
    title: str
    filename: str
    download_url: str
    metadata: Dict[str, Any]
    created_at: str
