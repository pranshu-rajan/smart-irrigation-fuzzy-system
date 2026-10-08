"""Pydantic schemas for Fuzzy Inference Systems inspection and evaluation."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class LinguisticSetSchema(BaseModel):
    name: str
    type: str  # trimf, trapmf
    parameters: List[float]


class FuzzyVariableSchema(BaseModel):
    name: str
    display_name: str
    unit: str
    min: float
    max: float
    resolution: int
    fis_role: str  # input, output
    associated_fis: str
    sets: Dict[str, LinguisticSetSchema]
    curve_points: Optional[Dict[str, List[List[float]]]] = None  # [x, y] coordinates for plotting


class ControllerOverview(BaseModel):
    id: Optional[str] = None
    name: str
    title: str
    description: str
    inputs: List[str]
    output: str
    rule_count: int
    inference_type: str = "Mamdani"
    and_operator: str = "Minimum"
    or_operator: str = "Maximum"
    implication: str = "Minimum"
    aggregation: str = "Maximum"
    defuzzification: str = "Centroid (501 points)"


class FuzzyRuleSchema(BaseModel):
    id: int
    conditions_text: str
    antecedents: Dict[str, Any]
    consequent: str
    description: Optional[str] = None


class FuzzyEvaluateRequest(BaseModel):
    controller_name: Optional[str] = None
    controller: Optional[str] = None
    target_controller: Optional[str] = None
    inputs: Dict[str, float]

    @property
    def resolved_controller(self) -> str:
        return self.target_controller or self.controller_name or self.controller or "main_irrigation"


class RuleActivationDetail(BaseModel):
    rule_id: int
    conditions: str
    consequent: str
    weight: float
    is_active: bool


class FuzzyEvaluateResponse(BaseModel):
    controller_name: str
    inputs: Dict[str, float]
    fuzzified_inputs: Dict[str, Dict[str, float]]  # variable -> set -> membership
    active_rules: List[RuleActivationDetail]
    aggregated_output_name: str
    crisp_output: float
    outputs: Optional[Dict[str, float]] = None
    firing_weights: Optional[List[float]] = None
    unit: str


class EndToEndArchitectureRequest(BaseModel):
    """Input payload to evaluate all 5 stages of the fuzzy system in unified cascade."""
    soil_moisture: float = Field(default=45.0, ge=0.0, le=100.0, description="Current soil moisture (%)")
    target_moisture: float = Field(default=60.0, ge=0.0, le=100.0, description="Target soil moisture (%)")
    temperature: float = Field(default=32.0, ge=-20.0, le=60.0, description="Air temperature (°C)")
    humidity: float = Field(default=38.0, ge=0.0, le=100.0, description="Relative humidity (%)")
    solar_radiation: float = Field(default=820.0, ge=0.0, le=1500.0, description="Solar radiation (W/m²)")
    wind_speed: float = Field(default=3.2, ge=0.0, le=50.0, description="Wind speed (m/s)")
    rainfall: float = Field(default=0.0, ge=0.0, le=100.0, description="Rainfall depth (mm)")
    reservoir_storage_pct: float = Field(default=50.0, ge=0.0, le=100.0, description="Shared reservoir water storage (%)")


class ZoneAllocationOutput(BaseModel):
    zone_id: int
    name: str
    crop: str
    priority_pct: float
    fis_alloc_factor: float
    requested_l: float
    allocated_l: float
    fulfillment_ratio: float
    status: str


class EndToEndArchitectureResponse(BaseModel):
    """Complete diagnostic cascade across all 5 FIS stages, exactly matching MATLAB evaluate_fuzzy_architecture."""
    inputs: Dict[str, float]
    soil_stress: float
    soil_stress_level: str
    weather_stress: float
    weather_stress_level: str
    water_demand: float
    water_demand_level: str
    etc_mm_day: float
    main_command: float
    main_command_level: str
    zone_allocations: List[ZoneAllocationOutput]
    total_requested_l: float
    total_allocated_l: float
    available_supply_l: float
    is_constrained: bool
    decision_summary: str

