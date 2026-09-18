"""
High-Performance Simulation Evaluator for Phase 14 PSO.

Pre-generates and caches immutable meteorological timelines and FAO-56 ET0 series
in memory to eliminate disk I/O and redundant weather generation during PSO iterations.
Precomputes weather stress and water demand arrays for maximum speed.
Evaluates candidate parameter vectors across training and validation scenarios.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

from config.schemas import SimulationScenario, ZoneConfig
from config.defaults import get_default_zones
from simulation.weather import WeatherEngine
from models.et0 import compute_et0_timeseries
from models.etc import (
    CropCoefficientManager,
    calculate_effective_rainfall,
    calculate_crop_water_deficit,
)
from models.soil import (
    calculate_relative_soil_moisture,
    calculate_moisture_error,
)
from models.water_balance import (
    SoilState,
    initialize_soil_state,
    update_water_balance,
)
from fuzzy_engine.soil_stress import SoilStressFIS
from fuzzy_engine.weather_stress import WeatherStressFIS
from fuzzy_engine.water_demand import WaterDemandFIS
from simulation.closed_loop import ClosedLoopConfig, ClosedLoopSimulator, ClosedLoopMetrics
from optimization.parameter_space import FuzzyParameterSpace
from optimization.fitness import (
    FitnessWeights,
    ScenarioFitness,
    CompositeFitnessResult,
    compute_scenario_fitness,
)

# Canonical Training and Validation Scenario Partitions
TRAINING_SCENARIOS: List[SimulationScenario] = [
    SimulationScenario.NORMAL,
    SimulationScenario.HOT_AND_DRY,
    SimulationScenario.RAINY,
    SimulationScenario.CLOUDY,
]

VALIDATION_SCENARIOS: List[SimulationScenario] = [
    SimulationScenario.HEATWAVE,
    SimulationScenario.WATER_SCARCITY,
]

ALL_SCENARIOS: List[SimulationScenario] = TRAINING_SCENARIOS + VALIDATION_SCENARIOS


class ClosedLoopEvaluator:
    """
    Caches scenario environmental data and runs fast in-memory closed-loop simulations.
    """

    def __init__(
        self,
        param_space: Optional[FuzzyParameterSpace] = None,
        weights: Optional[FitnessWeights] = None,
        seed: int = 42,
        duration_hours: int = 24,
        timestep_minutes: int = 1,
    ) -> None:
        self.param_space = param_space or FuzzyParameterSpace()
        self.weights = weights or FitnessWeights()
        self.seed = seed
        self.duration_hours = duration_hours
        self.timestep_minutes = timestep_minutes

        # Default plant: Zone 1 (Tomato / Loam)
        self.zone_config = get_default_zones()[0]

        # Fixed hierarchical upstream FIS models
        self.fis_soil = SoilStressFIS(resolution=501)
        self.fis_weather = WeatherStressFIS(resolution=501)
        self.fis_water = WaterDemandFIS(resolution=501)

        # Cache weather and ET0 timelines in memory for each scenario
        self._scenario_cache: Dict[SimulationScenario, Tuple[pd.DataFrame, pd.DataFrame]] = {}
        self._scenario_fast_data: Dict[SimulationScenario, Dict[str, Any]] = {}
        self._precompute_scenarios()

    def _precompute_scenarios(self) -> None:
        """Precompute and cache weather timelines, ET0, weather stress, and water demand arrays."""
        crop_db = CropCoefficientManager.load_crop_database()
        crop_match = crop_db[crop_db["crop"].str.capitalize() == self.zone_config.crop.name.capitalize()]
        self.p_frac = float(crop_match.iloc[0]["depletion_fraction_p"]) if not crop_match.empty else 0.50

        kc = self.zone_config.crop.kc

        for sc in ALL_SCENARIOS:
            we = WeatherEngine(scenario=sc, seed=self.seed)
            w_df = we.generate_timeline(
                duration_hours=self.duration_hours,
                timestep_minutes=self.timestep_minutes,
            )
            et0_df = compute_et0_timeseries(
                w_df,
                timestep_minutes=self.timestep_minutes,
            )
            self._scenario_cache[sc] = (w_df, et0_df)

            n = len(w_df)
            weather_stress_arr = np.zeros(n, dtype=float)
            water_demand_arr = np.zeros(n, dtype=float)
            peff_arr = np.zeros(n, dtype=float)
            etc_arr = np.zeros(n, dtype=float)
            rain_arr = w_df["rainfall"].values.astype(float)
            et0_arr = et0_df["et0"].values.astype(float)
            temp_arr = w_df["temperature"].values.astype(float)
            hum_arr = w_df["humidity"].values.astype(float)
            sol_arr = w_df["solar_radiation"].values.astype(float)
            wind_arr = w_df["wind_speed"].values.astype(float)

            for t in range(n):
                weather_stress_arr[t] = self.fis_weather.evaluate(
                    temperature=float(temp_arr[t]),
                    humidity=float(hum_arr[t]),
                    solar_radiation=float(sol_arr[t]),
                    wind_speed=float(wind_arr[t]),
                    rainfall=float(rain_arr[t]),
                )
                etc_t = kc * float(et0_arr[t])
                etc_arr[t] = etc_t
                peff_t = calculate_effective_rainfall(float(rain_arr[t]), timestep_minutes=self.timestep_minutes)
                peff_arr[t] = peff_t
                deficit_t = calculate_crop_water_deficit(etc_t, peff_t)
                water_demand_arr[t] = self.fis_water.evaluate(
                    etc=etc_t,
                    crop_water_deficit=deficit_t,
                    effective_rainfall=peff_t,
                )

            self._scenario_fast_data[sc] = {
                "n": n,
                "weather_stress": weather_stress_arr,
                "water_demand": water_demand_arr,
                "peff": peff_arr,
                "etc": etc_arr,
                "timestamps": [str(ts) for ts in w_df["timestamp"]],
            }

    def evaluate_vector(
        self,
        theta: np.ndarray,
        scenarios: Optional[List[SimulationScenario]] = None,
    ) -> CompositeFitnessResult:
        """
        Fast evaluation of a candidate parameter vector across requested scenarios.

        Args:
            theta: Physical parameter vector (18-D).
            scenarios: List of SimulationScenario to evaluate. Defaults to TRAINING_SCENARIOS.

        Returns:
            CompositeFitnessResult with mean scalar fitness and per-scenario decomposition.
        """
        eval_scenarios = scenarios or TRAINING_SCENARIOS

        # Build parameterized MainIrrigationFIS
        fis = self.param_space.build_fis(theta)

        target_sm = self.zone_config.target_moisture
        wp = self.zone_config.soil.wilting_point
        fc = self.zone_config.soil.field_capacity
        infilt_cap = self.zone_config.soil.infiltration_rate_mm_h
        drain_param = self.zone_config.soil.drainage_parameter
        area = self.zone_config.area_m2
        max_rate = 12.0  # max_irrigation_rate_mm_h default
        dt_min = self.timestep_minutes
        timestep_hours = dt_min / 60.0
        available_range = max(1.0, fc - wp)
        ref_vol = 8000.0

        scenario_results: Dict[str, ScenarioFitness] = {}
        total_j = 0.0

        for sc in eval_scenarios:
            data = self._scenario_fast_data[sc]
            n = data["n"]
            ws_arr = data["weather_stress"]
            wd_arr = data["water_demand"]
            peff_arr = data["peff"]
            etc_arr = data["etc"]
            ts_arr = data["timestamps"]

            current_state = initialize_soil_state(
                zone_config=self.zone_config,
                depletion_fraction_p=self.p_frac,
                timestamp=ts_arr[0],
            )

            moisture_errors = np.zeros(n, dtype=float)
            applied_vols_l = np.zeros(n, dtype=float)
            soil_moistures = np.zeros(n, dtype=float)
            commands = np.zeros(n, dtype=float)

            for step in range(n):
                sm_t = current_state.soil_moisture
                error_t = calculate_moisture_error(target_sm, sm_t)
                moisture_errors[step] = error_t
                soil_moistures[step] = sm_t

                rsm_t = calculate_relative_soil_moisture(sm_t, wp, fc)
                soil_stress_t = self.fis_soil.evaluate(rsm=rsm_t, moisture_error=error_t)

                cmd_t = fis.evaluate(
                    soil_stress=soil_stress_t,
                    weather_stress=ws_arr[step],
                    water_demand=wd_arr[step],
                    moisture_error=error_t,
                )
                commands[step] = cmd_t

                fractional_cmd = float(cmd_t) / 100.0
                eff_infilt = float(fractional_cmd * max_rate * timestep_hours)
                applied_vols_l[step] = eff_infilt * area

                current_state = update_water_balance(
                    current_state=current_state,
                    irrigation_mm=eff_infilt,
                    effective_rainfall_mm=peff_arr[step],
                    etc_mm=etc_arr[step],
                    timestep_minutes=dt_min,
                    infiltration_rate_mm_h=infilt_cap,
                    drainage_parameter=drain_param,
                    timestamp=ts_arr[step],
                )

            # Compute metrics
            mae = float(np.mean(np.abs(moisture_errors)))
            rmse = float(np.sqrt(np.mean(moisture_errors ** 2)))
            vol_l = float(np.sum(applied_vols_l))

            e_tracking = min(2.0, float(rmse / available_range))
            e_water = min(2.0, float(vol_l / max(1.0, ref_vol)))

            critical_threshold = target_sm - 3.0
            deficit_mask = soil_moistures < critical_threshold
            deficit_minutes = int(np.sum(deficit_mask))
            if deficit_minutes > 0:
                deficit_depths = critical_threshold - soil_moistures[deficit_mask]
                e_deficit = float(np.mean(deficit_depths) / available_range) * (deficit_minutes / n)
            else:
                e_deficit = 0.0
            e_deficit = min(2.0, e_deficit)

            cmd_diffs = np.abs(np.diff(commands))
            control_variation = float(np.mean(cmd_diffs))
            e_smoothness = min(2.0, float(control_variation / 50.0))

            j_scenario = (
                self.weights.w_tracking * e_tracking
                + self.weights.w_water * e_water
                + self.weights.w_deficit * e_deficit
                + self.weights.w_smoothness * e_smoothness
            )

            sc_fitness = ScenarioFitness(
                scenario=sc.value,
                total_fitness=float(j_scenario),
                e_tracking=e_tracking,
                e_water=e_water,
                e_deficit=e_deficit,
                e_smoothness=e_smoothness,
                mae_pct=mae,
                rmse_pct=rmse,
                water_volume_l=vol_l,
                deficit_minutes=deficit_minutes,
                control_variation=control_variation,
            )
            scenario_results[sc.value] = sc_fitness
            total_j += sc_fitness.total_fitness

        mean_j = float(total_j / len(eval_scenarios))

        return CompositeFitnessResult(
            composite_fitness=mean_j,
            scenario_fitness=scenario_results,
        )

    def evaluate_baseline(
        self,
        scenarios: Optional[List[SimulationScenario]] = None,
    ) -> CompositeFitnessResult:
        """Evaluate the unoptimized expert-designed baseline configuration."""
        return self.evaluate_vector(
            theta=self.param_space.baseline_values,
            scenarios=scenarios,
        )
