"""Pydantic data models for application persistence (Supabase & local store)."""

from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from pydantic import BaseModel, Field


class ProfileRecord(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ZoneRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    zone_id: int
    name: str
    crop: str
    soil: str
    area_m2: float
    field_capacity: float
    wilting_point: float
    saturation: float = 85.0
    initial_moisture: float
    target_moisture: float
    root_zone_depth: float
    kc: float
    priority: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SimulationRunRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    scenario: str
    duration_hours: int = 24
    timestep_minutes: int = 1
    status: str = "completed"  # queued, running, completed, failed
    controller_type: str = "fuzzy"  # fuzzy, baseline_none, baseline_fixed, pso_tuned
    supply_scenario: str = "Normal Supply"
    config_snapshot: Dict[str, Any] = Field(default_factory=dict)
    summary_metrics: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OptimizationRunRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    status: str = "completed"  # queued, running, completed, failed
    seed: int = 42
    swarm_size: int = 20
    max_iterations: int = 30
    objective_weights: Dict[str, float] = Field(default_factory=dict)
    baseline_fitness: float = 0.0
    optimized_fitness: float = 0.0
    convergence_history: List[Dict[str, Any]] = Field(default_factory=list)
    optimized_parameters: Dict[str, float] = Field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ReportRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    simulation_id: Optional[str] = None
    optimization_id: Optional[str] = None
    report_type: str = "simulation_pdf"
    title: str
    filename: str
    file_path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AIConversationRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AIMessageRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    role: str  # user, assistant, system
    content: str
    grounded_context: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
