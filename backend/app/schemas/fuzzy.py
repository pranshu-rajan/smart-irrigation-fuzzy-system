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
