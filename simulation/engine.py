"""Multizone Agricultural and Environmental Simulation Engine.

Orchestrates the open-loop integration of:
1. Dynamic WeatherEngine (meteorological generation)
2. FAO-56 Penman-Monteith ET0 Engine
3. Multizone Crop Evapotranspiration ETc & Effective Rainfall Engine
4. Dynamic Soil Water Balance Model for Zones 1, 2, and 3
5. External/Placeholder Irrigation Interface (preparing for Phases 6-10 Fuzzy Controllers)
"""

from typing import Optional, Union, Dict, List, Any
import numpy as np
import pandas as pd

from config.schemas import SystemConfig, SimulationScenario, ZoneConfig
from config.defaults import get_default_zones
from simulation.weather import WeatherEngine
from simulation.scenarios import ScenarioManager
from models.et0 import compute_et0_timeseries
from models.etc import compute_multizone_crop_demand, CropCoefficientManager
from models.soil import SoilParameterManager
from models.water_balance import (
    SoilState,
    initialize_soil_state,
    simulate_water_balance_timeseries,
)


class SimulationEngine:
    """Orchestrates multizone environmental simulation and root-zone water dynamics."""

    def __init__(
        self,
        config: Optional[SystemConfig] = None,
        scenario: SimulationScenario = SimulationScenario.NORMAL,
        irrigation_mode: str = "none",
        fixed_irrigation_rate_mm_h: float = 0.0,
        periodic_pulse_interval_hours: float = 6.0,
        periodic_pulse_depth_mm: float = 5.0,
        custom_irrigation_arrays: Optional[Dict[int, np.ndarray]] = None,
        seed: Optional[int] = 42,
    ) -> None:
        """Initialize simulation environment.

        Args:
            config: Optional SystemConfig instance. Defaults to baseline 3-zone system.
            scenario: Environmental scenario enum (Normal, Hot & Dry, Rainy, Cloudy, Heatwave, Water Scarcity).
            irrigation_mode: 'none', 'fixed', 'periodic', or 'custom'.
            fixed_irrigation_rate_mm_h: Application rate for 'fixed' mode (mm/hour).
            periodic_pulse_interval_hours: Pulse interval for 'periodic' mode (hours).
            periodic_pulse_depth_mm: Pulse application depth for 'periodic' mode (mm).
            custom_irrigation_arrays: Optional dict mapping zone_id -> np.ndarray of irrigation depths (mm/step).
            seed: PRNG seed for reproducible stochasticity.
        """
        self.config = config if config is not None else SystemConfig()
        self.scenario = scenario
        self.irrigation_mode = irrigation_mode.lower()
        self.fixed_rate = fixed_irrigation_rate_mm_h
        self.pulse_interval = periodic_pulse_interval_hours
        self.pulse_depth = periodic_pulse_depth_mm
        self.custom_irrigation = custom_irrigation_arrays or {}
        self.seed = seed

        # Ensure zone configurations are populated
        if self.config.zone_configs is None or len(self.config.zone_configs) == 0:
            self.zones = get_default_zones()
        else:
            self.zones = self.config.zone_configs

        self.scenario_params = ScenarioManager.get_scenario_parameters(self.scenario)

    def _generate_irrigation_series(self, zone_id: int, total_steps: int, timestep_minutes: int) -> np.ndarray:
        """Generate test irrigation input array for a zone across simulation epochs."""
        if zone_id in self.custom_irrigation:
            arr = np.asarray(self.custom_irrigation[zone_id], dtype=np.float64)
            if len(arr) != total_steps:
                raise ValueError(f"Custom irrigation array length {len(arr)} does not match simulation steps {total_steps}")
            return arr

        irrigation = np.zeros(total_steps, dtype=np.float64)
        timestep_hours = timestep_minutes / 60.0

        if self.irrigation_mode == "none":
            pass
        elif self.irrigation_mode == "fixed":
            # Apply constant depth per timestep: rate [mm/h] * timestep [h]
            irrigation[:] = self.fixed_rate * timestep_hours
        elif self.irrigation_mode == "periodic":
            # Pulse applied at regular intervals over a 15-minute delivery window
            interval_steps = int((self.pulse_interval * 60) // timestep_minutes)
            pulse_window_steps = max(1, int(15 // timestep_minutes))
            step_rate = self.pulse_depth / pulse_window_steps

            for start_step in range(interval_steps, total_steps, interval_steps):
                end_step = min(total_steps, start_step + pulse_window_steps)
                irrigation[start_step:end_step] = step_rate

        # If scenario is Water Scarcity, apply physical restriction
        waf = self.scenario_params.water_availability_factor
        if waf < 1.0:
            irrigation *= waf

        return irrigation

    def run(
        self,
        duration_hours: Optional[int] = None,
        timestep_minutes: Optional[int] = None,
    ) -> pd.DataFrame:
        """Execute full multizone simulation run.

        Returns:
            pd.DataFrame: Comprehensive unified time-series dataset logging all
                         meteorology, radiation, ET, soil moisture, and hydrological fluxes.
        """
        dur_h = duration_hours if duration_hours is not None else self.config.simulation.duration_hours
        dt_min = timestep_minutes if timestep_minutes is not None else self.config.simulation.timestep_minutes
        total_steps = (dur_h * 60) // dt_min

        # 1. Weather Generation
        engine = WeatherEngine(scenario=self.scenario, seed=self.seed)
        weather_df = engine.generate_timeline(duration_hours=dur_h, timestep_minutes=dt_min)

        # 2. FAO-56 Reference Evapotranspiration
        et0_df = compute_et0_timeseries(weather_df, timestep_minutes=dt_min)

        # 3. Multizone ETc and Effective Rainfall
        zones_metadata = [
            {
                "zone_id": z.zone_id,
                "crop": z.crop.name,
                "growth_stage": z.crop.growth_stage.value,
                "kc": z.crop.kc,
            }
            for z in self.zones
        ]
        crop_demand_df = compute_multizone_crop_demand(
            et0_df=et0_df,
            zones_info=zones_metadata,
            timestep_minutes=dt_min,
        )

        # 4. Multizone Soil Water Balance Simulation
        zone_results: List[pd.DataFrame] = []
        crop_db = CropCoefficientManager.load_crop_database()

        for z in self.zones:
            z_id = z.zone_id
            z_demand = crop_demand_df[crop_demand_df["zone_id"] == z_id].reset_index(drop=True)

            # Get crop depletion fraction p from crop database
            crop_match = crop_db[crop_db["crop"].str.capitalize() == z.crop.name.capitalize()]
            p_frac = float(crop_match.iloc[0]["depletion_fraction_p"]) if not crop_match.empty else 0.50

            # Initialize zone soil state
            initial_state = initialize_soil_state(
                zone_config=z,
                depletion_fraction_p=p_frac,
                timestamp=str(weather_df["timestamp"].iloc[0]),
            )

            # Generate irrigation series for this zone
            irrig_arr = self._generate_irrigation_series(z_id, total_steps, dt_min)
            etc_arr = z_demand["etc"].to_numpy(dtype=np.float64)
            peff_arr = z_demand["effective_rainfall"].to_numpy(dtype=np.float64)
            timestamps_str = [str(ts) for ts in weather_df["timestamp"]]

            # Simulate zone water balance
            soil_df = simulate_water_balance_timeseries(
                initial_state=initial_state,
                etc_series=etc_arr,
                effective_rainfall_series=peff_arr,
                irrigation_series=irrig_arr,
                timestamps=timestamps_str,
                timestep_minutes=dt_min,
                infiltration_rate_mm_h=z.soil.infiltration_rate_mm_h,
                drainage_parameter=z.soil.drainage_parameter,
            )

            # Merge with meteorological and agronomic metadata
            soil_df["crop"] = z.crop.name
            soil_df["soil_type"] = z.soil.soil_type.value
            soil_df["rainfall"] = z_demand["rainfall"].values
            soil_df["effective_rainfall"] = z_demand["effective_rainfall"].values
            soil_df["et0"] = z_demand["et0"].values
            soil_df["etc"] = z_demand["etc"].values
            soil_df["irrigation"] = soil_df["irrigation_applied_mm"]
            soil_df["infiltration"] = soil_df["infiltration_mm"]
            soil_df["drainage"] = soil_df["drainage_mm"]
            soil_df["runoff"] = soil_df["surface_runoff_mm"]
            soil_df["soil_storage_mm"] = soil_df["storage_mm"]

            zone_results.append(soil_df)

        unified_df = pd.concat(zone_results, ignore_index=True)
        unified_df = unified_df.sort_values(by=["step", "zone_id"]).reset_index(drop=True)

        return unified_df
