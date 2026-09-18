"""
Hierarchical Adaptive Mamdani Fuzzy Inference Engine.

Subsystems:
1. SoilStressFIS: Evaluates crop root-zone stress based on soil moisture and tracking error.
2. WeatherStressFIS: Assesses atmospheric stress induced by temperature, humidity, radiation, wind, and rain.
3. WaterDemandFIS: Derives crop water requirement from ETc, water deficit, and effective rainfall.
4. MainIrrigationFIS: Synthesizes soil stress, weather stress, water demand, and error into an irrigation command (0-100).
5. WaterAllocationFIS: Allocates constrained water resources across competing agricultural zones.
"""

from fuzzy_engine.soil_stress import SoilStressFIS
from fuzzy_engine.weather_stress import WeatherStressFIS
from fuzzy_engine.water_demand import WaterDemandFIS
from fuzzy_engine.irrigation import MainIrrigationFIS
from fuzzy_engine.water_allocation import WaterAllocationFIS

from fuzzy_engine.membership import triangular_mf, trapezoidal_mf
from fuzzy_engine.variables import FuzzyUniverse, MembershipSet, FuzzyVariable
from fuzzy_engine.mf_factory import (
    create_triangular_mf,
    create_trapezoidal_mf,
    create_membership_set,
    create_fuzzy_variable_from_dict,
    build_all_fuzzy_variables,
)
from fuzzy_engine.universes import (
    FUZZY_VARIABLES,
    FIS_ARCHITECTURE,
    get_fuzzy_variable,
    get_variables_by_fis,
    list_variable_names,
)
from fuzzy_engine.validation import (
    ValidationError,
    validate_fuzzy_variable,
    validate_all_variables,
)

__all__ = [
    # FIS Subsystems (Phase 7-10)
    "SoilStressFIS",
    "WeatherStressFIS",
    "WaterDemandFIS",
    "MainIrrigationFIS",
    "WaterAllocationFIS",
    # Mathematical MFs
    "triangular_mf",
    "trapezoidal_mf",
    # Core Classes
    "FuzzyUniverse",
    "MembershipSet",
    "FuzzyVariable",
    # Factories
    "create_triangular_mf",
    "create_trapezoidal_mf",
    "create_membership_set",
    "create_fuzzy_variable_from_dict",
    "build_all_fuzzy_variables",
    # Registry & Architecture
    "FUZZY_VARIABLES",
    "FIS_ARCHITECTURE",
    "get_fuzzy_variable",
    "get_variables_by_fis",
    "list_variable_names",
    # Validation
    "ValidationError",
    "validate_fuzzy_variable",
    "validate_all_variables",
]
