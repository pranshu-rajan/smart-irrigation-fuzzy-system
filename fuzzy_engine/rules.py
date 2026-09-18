"""Fuzzy rule base structures and engineering justifications.

Every rule in the system is required to have an explicit engineering / control-theoretic
justification to ensure interpretability and rigor during academic review.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class FuzzyRule(BaseModel):
    """Encapsulation of a single Mamdani rule with engineering justification."""
    rule_id: int = Field(..., description="Unique rule identifier")
    antecedents: Dict[str, str] = Field(..., description="Mapping of input variable name to linguistic label")
    consequent: Dict[str, str] = Field(..., description="Mapping of output variable name to linguistic label")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Rule confidence weight")
    justification: str = Field(..., description="Physical or control-theoretic rationale")
