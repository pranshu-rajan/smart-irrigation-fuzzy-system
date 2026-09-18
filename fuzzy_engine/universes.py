"""
Central Fuzzy Universes and Global Variable Registry.

Pre-instantiates all 19 fuzzy variables across the 5 FIS architectures
from config/fuzzy_config.json into a centralized, immutable registry.
"""

from pathlib import Path
from typing import Dict, List, Optional

from fuzzy_engine.mf_factory import build_all_fuzzy_variables
from fuzzy_engine.variables import FuzzyVariable


# Determine path to config/fuzzy_config.json relative to repository root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "config" / "fuzzy_config.json"

# Centralized global registry of all 19 fuzzy variables
FUZZY_VARIABLES: Dict[str, FuzzyVariable] = build_all_fuzzy_variables(_CONFIG_PATH)

# Architectural FIS specification mapping system name to inputs and output
FIS_ARCHITECTURE = {
    "soil_stress_fis": {
        "name": "Soil Stress FIS",
        "inputs": ["rsm", "moisture_error"],
        "output": "soil_stress",
    },
    "weather_stress_fis": {
        "name": "Weather Stress FIS",
        "inputs": ["temperature", "humidity", "solar_radiation", "wind_speed", "rainfall"],
        "output": "weather_stress",
    },
    "water_demand_fis": {
        "name": "Water Demand FIS",
        "inputs": ["etc", "crop_water_deficit", "effective_rainfall"],
        "output": "water_demand",
    },
    "main_irrigation_fis": {
        "name": "Main Irrigation FIS",
        "inputs": ["soil_stress", "weather_stress", "water_demand", "moisture_error"],
        "output": "irrigation_command",
    },
    "water_allocation_fis": {
        "name": "Water Allocation FIS",
        "inputs": ["zone_demand", "zone_stress", "available_water", "zone_priority"],
        "output": "zone_allocation",
    },
}


def get_fuzzy_variable(name: str) -> FuzzyVariable:
    """
    Retrieve a FuzzyVariable by machine identifier.

    Parameters
    ----------
    name : str
        Machine identifier (e.g. 'rsm', 'soil_stress').

    Returns
    -------
    FuzzyVariable
        The requested fuzzy variable instance.
    """
    if name not in FUZZY_VARIABLES:
        available = list(FUZZY_VARIABLES.keys())
        raise KeyError(f"Fuzzy variable '{name}' not found in registry. Available variables: {available}")
    return FUZZY_VARIABLES[name]


def get_variables_by_fis(fis_name: str) -> Dict[str, FuzzyVariable]:
    """
    Retrieve all input and output fuzzy variables associated with a specific FIS.

    Parameters
    ----------
    fis_name : str
        One of 'soil_stress_fis', 'weather_stress_fis', 'water_demand_fis',
        'main_irrigation_fis', 'water_allocation_fis'.

    Returns
    -------
    dict of {str: FuzzyVariable}
        Dictionary containing all relevant variable instances.
    """
    if fis_name not in FIS_ARCHITECTURE:
        raise KeyError(f"Unknown FIS architecture '{fis_name}'. Available: {list(FIS_ARCHITECTURE.keys())}")

    arch = FIS_ARCHITECTURE[fis_name]
    var_names = arch["inputs"] + [arch["output"]]
    return {name: get_fuzzy_variable(name) for name in var_names}


def list_variable_names() -> List[str]:
    """Return a list of all 19 registered fuzzy variable identifiers."""
    return list(FUZZY_VARIABLES.keys())
