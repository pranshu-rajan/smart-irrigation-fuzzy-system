"""Scenarios Reference Router."""

from typing import List, Dict, Any
from fastapi import APIRouter

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

SCENARIOS_DATA = [
    {
        "id": "Normal",
        "name": "Normal Scenario",
        "category": "Training",
        "temp_range_c": [18.0, 28.0],
        "rh_range_pct": [40.0, 70.0],
        "solar_peak_w_m2": 800.0,
        "rainfall_mm": 0.0,
        "description": "Diurnal cycle with moderate solar irradiance and typical evaporative demand.",
    },
    {
        "id": "Hot & Dry",
        "name": "Hot & Dry Scenario",
        "category": "Training",
        "temp_range_c": [25.0, 38.0],
        "rh_range_pct": [15.0, 35.0],
        "solar_peak_w_m2": 950.0,
        "rainfall_mm": 0.0,
        "description": "High temperature and elevated vapor pressure deficit driving severe crop evapotranspiration.",
    },
    {
        "id": "Rainy",
        "name": "Rainy Scenario",
        "category": "Training",
        "temp_range_c": [15.0, 22.0],
        "rh_range_pct": [75.0, 95.0],
        "solar_peak_w_m2": 350.0,
        "rainfall_mm": 18.5,
        "description": "Overcast conditions with intermittent precipitation pulses and suppressed evaporative loss.",
    },
    {
        "id": "Cloudy",
        "name": "Cloudy Scenario",
        "category": "Training",
        "temp_range_c": [16.0, 24.0],
        "rh_range_pct": [60.0, 80.0],
        "solar_peak_w_m2": 450.0,
        "rainfall_mm": 0.0,
        "description": "Diffused irradiance and low atmospheric demand requiring reduced irrigation application.",
    },
    {
        "id": "Heatwave",
        "name": "Heatwave Scenario (Validation)",
        "category": "Validation",
        "temp_range_c": [28.0, 42.0],
        "rh_range_pct": [10.0, 25.0],
        "solar_peak_w_m2": 1050.0,
        "rainfall_mm": 0.0,
        "description": "Extreme climatic stress test to validate controller out-of-sample resilience.",
    },
    {
        "id": "Water Scarcity",
        "name": "Water Scarcity Scenario (Validation)",
        "category": "Validation",
        "temp_range_c": [24.0, 35.0],
        "rh_range_pct": [20.0, 45.0],
        "solar_peak_w_m2": 900.0,
        "rainfall_mm": 0.0,
        "description": "Severe shared supply throttling testing Layer C bounded water-filling and priority fairness.",
    },
]


@router.get("", response_model=List[Dict[str, Any]])
def get_scenarios():
    """List all 6 standard environmental simulation scenarios."""
    return SCENARIOS_DATA
