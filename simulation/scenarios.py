"""Environmental scenario definitions and parameter configurations.

Centralizes the physical, meteorological, and resource perturbations for:
1. Normal: Baseline clear-sky diurnal profile (100% water availability).
2. Hot & Dry: Elevated thermal regime, suppressed relative humidity, higher wind.
3. Rainy: Frequent precipitation intervals, high humidity, attenuated solar radiation.
4. Cloudy: Diffuse low radiation, moderate temperatures, elevated humidity.
5. Heatwave: Extreme sustained heat (>40°C peak), desiccating vapor pressure deficit.
6. Water Scarcity: Baseline meteorology with constrained water availability (30% reservoir storage).
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from config.schemas import SimulationScenario


@dataclass
class ScenarioParameters:
    """Quantitative modifiers and event probabilities governing weather generation."""
    name: str
    scenario: SimulationScenario
    temperature_offset_c: float
    temperature_range_multiplier: float
    humidity_offset_pct: float
    solar_multiplier: float
    wind_multiplier: float
    rain_probability: float  # Probability of a rain event initiating on any given day
    rain_intensity_min_mm_min: float
    rain_intensity_max_mm_min: float
    rain_duration_min_minutes: int
    rain_duration_max_minutes: int
    water_availability_factor: float  # Fraction of standard reservoir storage (1.0 = 100%, 0.3 = 30%)
    description: str


class ScenarioManager:
    """Manages environmental scenario parameters and configurations."""

    SCENARIO_CONFIGS: Dict[SimulationScenario, ScenarioParameters] = {
        SimulationScenario.NORMAL: ScenarioParameters(
            name="Normal",
            scenario=SimulationScenario.NORMAL,
            temperature_offset_c=0.0,
            temperature_range_multiplier=1.0,
            humidity_offset_pct=0.0,
            solar_multiplier=1.0,
            wind_multiplier=1.0,
            rain_probability=0.0,  # Clear-sky baseline
            rain_intensity_min_mm_min=0.0,
            rain_intensity_max_mm_min=0.0,
            rain_duration_min_minutes=0,
            rain_duration_max_minutes=0,
            water_availability_factor=1.0,
            description="Clear-sky baseline with standard diurnal thermal and solar cycles.",
        ),
        SimulationScenario.HOT_AND_DRY: ScenarioParameters(
            name="Hot & Dry",
            scenario=SimulationScenario.HOT_AND_DRY,
            temperature_offset_c=5.0,
            temperature_range_multiplier=1.15,
            humidity_offset_pct=-20.0,
            solar_multiplier=1.05,
            wind_multiplier=1.30,
            rain_probability=0.0,
            rain_intensity_min_mm_min=0.0,
            rain_intensity_max_mm_min=0.0,
            rain_duration_min_minutes=0,
            rain_duration_max_minutes=0,
            water_availability_factor=1.0,
            description="Elevated temperature, low humidity, and high wind creating acute evaporative demand.",
        ),
        SimulationScenario.RAINY: ScenarioParameters(
            name="Rainy",
            scenario=SimulationScenario.RAINY,
            temperature_offset_c=-4.0,
            temperature_range_multiplier=0.60,
            humidity_offset_pct=18.0,
            solar_multiplier=0.35,  # Heavy cloud attenuation
            wind_multiplier=1.10,
            rain_probability=1.0,  # Guaranteed precipitation events
            rain_intensity_min_mm_min=0.05,
            rain_intensity_max_mm_min=0.45,
            rain_duration_min_minutes=45,
            rain_duration_max_minutes=150,
            water_availability_factor=1.0,
            description="Intermittent precipitation, elevated humidity, and suppressed solar irradiance.",
        ),
        SimulationScenario.CLOUDY: ScenarioParameters(
            name="Cloudy",
            scenario=SimulationScenario.CLOUDY,
            temperature_offset_c=-2.5,
            temperature_range_multiplier=0.70,
            humidity_offset_pct=10.0,
            solar_multiplier=0.40,  # Dense overcast diffuse light
            wind_multiplier=0.90,
            rain_probability=0.20,
            rain_intensity_min_mm_min=0.02,
            rain_intensity_max_mm_min=0.10,
            rain_duration_min_minutes=20,
            rain_duration_max_minutes=60,
            water_availability_factor=1.0,
            description="Persistent diffuse cloud cover with attenuated solar radiation and mild temperatures.",
        ),
        SimulationScenario.HEATWAVE: ScenarioParameters(
            name="Heatwave",
            scenario=SimulationScenario.HEATWAVE,
            temperature_offset_c=8.0,
            temperature_range_multiplier=1.25,
            humidity_offset_pct=-25.0,
            solar_multiplier=1.10,
            wind_multiplier=1.40,
            rain_probability=0.0,
            rain_intensity_min_mm_min=0.0,
            rain_intensity_max_mm_min=0.0,
            rain_duration_min_minutes=0,
            rain_duration_max_minutes=0,
            water_availability_factor=1.0,
            description="Sustained extreme thermal stress exceeding 40°C with severe atmospheric drying power.",
        ),
        SimulationScenario.WATER_SCARCITY: ScenarioParameters(
            name="Water Scarcity",
            scenario=SimulationScenario.WATER_SCARCITY,
            temperature_offset_c=1.5,
            temperature_range_multiplier=1.05,
            humidity_offset_pct=-5.0,
            solar_multiplier=1.0,
            wind_multiplier=1.05,
            rain_probability=0.0,
            rain_intensity_min_mm_min=0.0,
            rain_intensity_max_mm_min=0.0,
            rain_duration_min_minutes=0,
            rain_duration_max_minutes=0,
            water_availability_factor=0.30,  # 70% storage restriction forcing prioritization
            description="Moderate-to-warm environmental conditions coupled with acute 70% water budget restriction.",
        ),
    }

    @classmethod
    def get_scenario_parameters(cls, scenario: SimulationScenario) -> ScenarioParameters:
        """Return quantitative parameter configuration for chosen scenario.

        Args:
            scenario: Selected SimulationScenario enum.

        Returns:
            ScenarioParameters: Configuration modifiers.
        """
        if scenario not in cls.SCENARIO_CONFIGS:
            raise KeyError(f"Unsupported simulation scenario: {scenario}")
        return cls.SCENARIO_CONFIGS[scenario]

    @classmethod
    def get_scenario_bounds(cls, scenario: SimulationScenario) -> Dict[str, Any]:
        """Return descriptive summary of parameter envelopes."""
        params = cls.get_scenario_parameters(scenario)
        return {
            "name": params.name,
            "temperature_offset_c": params.temperature_offset_c,
            "humidity_offset_pct": params.humidity_offset_pct,
            "solar_multiplier": params.solar_multiplier,
            "wind_multiplier": params.wind_multiplier,
            "rain_probability": params.rain_probability,
            "water_availability_factor": params.water_availability_factor,
            "description": params.description,
        }
