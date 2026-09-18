"""Multizone Closed-Loop Feedback Control Simulation Engine.

Extends the single-zone closed-loop feedback controller to 3 independent agricultural zones:
- Zone 1: Tomato / Loam (100 m², FC=70%, WP=25%, Initial SM=55%, Target SM=60%, Priority=2, Kc=1.15)
- Zone 2: Wheat / Sandy (120 m², FC=60%, WP=18%, Initial SM=42%, Target SM=55%, Priority=1, Kc=0.85)
- Zone 3: Maize / Clay (80 m², FC=75%, WP=30%, Initial SM=65%, Target SM=65%, Priority=3, Kc=1.20)

Parallel, independent control execution:
- Common meteorological forcing (T, RH, Rs, u2, P) and FAO-56 ET0.
- Independent per-zone root-zone states, tracking errors, and Relative Soil Moisture.
- Independent subsystem FIS evaluations (SoilStressFIS, WaterDemandFIS, MainIrrigationFIS).
- Independent physical actuator application with depth (mm) and volume (L) accounting.
- Independent Phase 5 soil-water balance state transitions with strict conservation accounting.
- Strictly no cross-zone state coupling or future-state leakage.
"""

from typing import Optional, Dict, Any, Tuple, List, Union
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from config.schemas import SimulationScenario, ZoneConfig, CropType, SoilType
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
from fuzzy_engine.main_irrigation import MainIrrigationFIS


class MultizoneClosedLoopConfig(BaseModel):
    """Configuration parameters for multizone closed-loop feedback simulation."""

    scenario: SimulationScenario = Field(
        default=SimulationScenario.NORMAL,
        description="Environmental weather scenario"
    )
    duration_hours: int = Field(
        default=24,
        ge=1,
        le=720,
        description="Simulation duration in hours"
    )
    timestep_minutes: int = Field(
        default=1,
        ge=1,
        le=60,
        description="Discretization time step in minutes"
    )
    max_irrigation_rate_mm_h: float = Field(
        default=12.0,
        gt=0.0,
        le=50.0,
        description="Default maximum actuator irrigation delivery rate in mm/hour at 100% command"
    )
    zone_max_irrigation_rates: Optional[Dict[int, float]] = Field(
        default=None,
        description="Optional per-zone maximum irrigation delivery rate overrides (mm/hour)"
    )
    target_moisture_tolerance_pct: float = Field(
        default=2.0,
        gt=0.0,
        le=10.0,
        description="Tolerance half-width around target moisture defining the target band (%)"
    )
    fixed_rate_mm_h: float = Field(
        default=1.5,
        ge=0.0,
        description="Fixed application rate for Baseline B comparison (mm/hour)"
    )
    effective_rainfall_method: str = Field(
        default="usda_scs",
        description="Effective precipitation methodology ('usda_scs', 'fao_empirical')"
    )
    seed: Optional[int] = Field(
        default=42,
        description="PRNG seed for reproducible weather generation"
    )


class ZoneClosedLoopMetrics(BaseModel):
    """Agronomic, control, and conservation performance metrics for an individual zone."""

    zone_id: int = Field(..., description="Zone identifier (1, 2, or 3)")
    crop: str = Field(..., description="Assigned crop type")
    soil: str = Field(..., description="Assigned soil textural class")
    area_m2: float = Field(..., description="Cultivated land area in square meters")
    scenario: str = Field(..., description="Scenario name")
    mode: str = Field(..., description="Control mode ('fuzzy', 'none', 'fixed')")

    # Moisture states (%)
    initial_soil_moisture: float = Field(..., description="Initial soil moisture (%)")
    final_soil_moisture: float = Field(..., description="Final soil moisture at end of run (%)")
    target_soil_moisture: float = Field(..., description="Target soil moisture setpoint (%)")
    final_moisture_error: float = Field(..., description="Final tracking error e(T) = Target - Final (%)")
    min_soil_moisture: float = Field(..., description="Minimum soil moisture observed (%)")
    max_soil_moisture: float = Field(..., description="Maximum soil moisture observed (%)")
    mean_soil_moisture: float = Field(..., description="Time-averaged soil moisture (%)")

    # Controller command states (%)
    mean_irrigation_command: float = Field(..., description="Time-averaged normalized irrigation command (%)")
    max_irrigation_command: float = Field(..., description="Peak normalized irrigation command (%)")

    # Cumulative water fluxes: Depth (mm) and Volume (Liters)
    total_irrigation_applied_mm: float = Field(..., description="Cumulative irrigation depth applied (mm)")
    total_irrigation_volume_l: float = Field(..., description="Cumulative irrigation volume applied (Liters = mm * m²)")
    total_rainfall_mm: float = Field(..., description="Cumulative rainfall observed (mm)")
    total_effective_rainfall_mm: float = Field(..., description="Cumulative effective rainfall infiltrated (mm)")
    total_etc_mm: float = Field(..., description="Cumulative crop evapotranspiration demand (mm)")
    total_etc_volume_l: float = Field(..., description="Cumulative crop evapotranspiration volume (Liters)")
    total_actual_et_mm: float = Field(..., description="Cumulative actual evapotranspiration consumed (mm)")
    total_drainage_mm: float = Field(..., description="Cumulative deep percolation / drainage (mm)")
    total_drainage_volume_l: float = Field(..., description="Cumulative deep percolation volume (Liters)")

    # Temporal operational counts
    active_irrigation_timesteps: int = Field(..., description="Count of timesteps with irrigation_command > 0.5%")
    off_irrigation_timesteps: int = Field(..., description="Count of timesteps with irrigation_command <= 0.5%")
    time_to_target_band_minutes: Optional[int] = Field(
        default=None,
        description="Time to first enter target band [Target - tol, Target + tol] in minutes; None if never reached"
    )
    time_in_target_band_minutes: int = Field(..., description="Total time spent within target band (minutes)")
    percentage_in_target_band: float = Field(..., description="Percentage of total simulation time inside target band (%)")

    # Tracking error metrics
    mae: float = Field(..., description="Mean Absolute Error (MAE) in %")
    rmse: float = Field(..., description="Root Mean Square Error (RMSE) in %")
    iae: float = Field(..., description="Integral Absolute Error (IAE) in % * minutes")

    # Water balance conservation verification
    max_absolute_residual: float = Field(..., description="Maximum absolute water balance residual |residual| (mm)")
    mean_absolute_residual: float = Field(..., description="Mean absolute water balance residual (mm)")
    residual_violations: int = Field(..., description="Count of residual conservation violations (> 1e-6 mm)")


class SystemClosedLoopMetrics(BaseModel):
    """Aggregate system-level hydrological and control performance metrics across all zones."""

    scenario: str = Field(..., description="Scenario name")
    mode: str = Field(..., description="Control mode ('fuzzy', 'none', 'fixed')")
    zone_count: int = Field(default=3, description="Number of active zones")
    total_system_area_m2: float = Field(..., description="Total cultivated area across all zones (m²)")

    # Aggregate volumes (Liters)
    total_system_irrigation_volume_l: float = Field(..., description="Total irrigation volume delivered across all zones (L)")
    total_system_etc_volume_l: float = Field(..., description="Total ETc volume across all zones (L)")
    total_system_actual_et_volume_l: float = Field(..., description="Total actual ET volume consumed across all zones (L)")
    total_system_drainage_volume_l: float = Field(..., description="Total deep drainage volume across all zones (L)")

    # Equivalent area-weighted depths (mm)
    weighted_irrigation_depth_mm: float = Field(..., description="Area-weighted average irrigation depth across zones (mm)")
    weighted_etc_depth_mm: float = Field(..., description="Area-weighted average ETc depth across zones (mm)")

    # System-wide tracking error metrics
    system_mean_mae: float = Field(..., description="Average MAE across all active zones (%)")
    system_mean_rmse: float = Field(..., description="Average RMSE across all active zones (%)")
    system_total_iae: float = Field(..., description="Sum of IAE across all active zones (% * min)")

    # System-wide target band residency
    total_zone_timesteps_in_band: int = Field(..., description="Total zone-timesteps spent inside respective target bands")
    overall_target_band_occupancy_pct: float = Field(..., description="Overall target band occupancy percentage (%)")

    # Water balance integrity across all zones
    max_conservation_residual: float = Field(..., description="Maximum absolute residual across all zones (mm)")
    total_residual_violations: int = Field(..., description="Total conservation violations across all zones")


class MultizoneSimulationResult(BaseModel):
    """Unified container for multizone simulation dataset and metrics."""

    df: Any = Field(..., description="Simulation pandas DataFrame (1440 * n_zones rows)")
    zone_metrics: Dict[int, ZoneClosedLoopMetrics] = Field(..., description="Per-zone metrics mapping")
    system_metrics: SystemClosedLoopMetrics = Field(..., description="System aggregate metrics")

    class Config:
        arbitrary_types_allowed = True


class MultizoneClosedLoopSimulator:
    """Dedicated multizone parallel closed-loop feedback controller and simulation orchestrator."""

    def __init__(
        self,
        config: Optional[MultizoneClosedLoopConfig] = None,
        zone_configs: Optional[List[ZoneConfig]] = None,
        fis_main: Optional[MainIrrigationFIS] = None,
    ) -> None:
        """Initialize multizone simulator with configuration, zone parameters, and fuzzy engines.

        Args:
            config: MultizoneClosedLoopConfig instance. Defaults to Normal scenario on 3 zones.
            zone_configs: Optional list of ZoneConfig overrides. Defaults to standard 3 zones.
            fis_main: Optional custom MainIrrigationFIS instance for parameter optimization.
        """
        self.config = config if config is not None else MultizoneClosedLoopConfig()
        self.zones = zone_configs if zone_configs is not None else get_default_zones()

        # Initialize the 4 hierarchical Fuzzy Inference Systems (reused across zones)
        self.fis_soil = SoilStressFIS(resolution=501)
        self.fis_weather = WeatherStressFIS(resolution=501)
        self.fis_water = WaterDemandFIS(resolution=501)
        self.fis_main = fis_main if fis_main is not None else MainIrrigationFIS(resolution=501)

    def _get_max_irrigation_rate(self, zone_id: int) -> float:
        """Retrieve maximum actuator delivery rate for a specific zone."""
        if self.config.zone_max_irrigation_rates and zone_id in self.config.zone_max_irrigation_rates:
            return float(self.config.zone_max_irrigation_rates[zone_id])
        return float(self.config.max_irrigation_rate_mm_h)

    def run(self, mode: str = "fuzzy") -> MultizoneSimulationResult:
        """Execute full parallel closed-loop feedback simulation across all configured zones.

        Args:
            mode: Simulation control mode:
                  - 'fuzzy': Dynamic hierarchical fuzzy feedback controller per zone.
                  - 'none': Baseline A with zero irrigation across all zones.
                  - 'fixed': Baseline B with open-loop constant application rate.

        Returns:
            MultizoneSimulationResult containing:
                - Consolidated DataFrame (1440 * num_zones records).
                - Dict mapping zone_id -> ZoneClosedLoopMetrics.
                - SystemClosedLoopMetrics object.
        """
        mode_clean = mode.strip().lower()
        if mode_clean not in ("fuzzy", "none", "fixed"):
            raise ValueError(f"Unknown control mode '{mode}'. Choose 'fuzzy', 'none', or 'fixed'.")

        dur_h = self.config.duration_hours
        dt_min = self.config.timestep_minutes
        total_steps = (dur_h * 60) // dt_min
        timestep_hours = dt_min / 60.0

        # Step 1: Generate Environmental Timeline (Shared across zones)
        weather_engine = WeatherEngine(
            scenario=self.config.scenario,
            seed=self.config.seed
        )
        weather_df = weather_engine.generate_timeline(
            duration_hours=dur_h,
            timestep_minutes=dt_min
        )

        # Step 2: Compute Reference Evapotranspiration ET0 (FAO-56 Penman-Monteith)
        et0_df = compute_et0_timeseries(
            weather_df,
            timestep_minutes=dt_min
        )

        # Step 3: Initialize Independent Root-Zone Soil States for each Zone
        crop_db = CropCoefficientManager.load_crop_database()
        current_states: Dict[int, SoilState] = {}
        zone_params: Dict[int, Dict[str, Any]] = {}

        for z in self.zones:
            z_id = z.zone_id
            crop_match = crop_db[crop_db["crop"].str.capitalize() == z.crop.name.capitalize()]
            p_frac = float(crop_match.iloc[0]["depletion_fraction_p"]) if not crop_match.empty else 0.50

            initial_state = initialize_soil_state(
                zone_config=z,
                depletion_fraction_p=p_frac,
                timestamp=str(weather_df["timestamp"].iloc[0]),
            )
            current_states[z_id] = initial_state
            zone_params[z_id] = {
                "config": z,
                "kc": z.crop.kc,
                "zr": z.crop.root_depth_m,
                "fc": z.soil.field_capacity,
                "wp": z.soil.wilting_point,
                "sat": z.soil.saturation,
                "target_sm": z.target_moisture,
                "infilt_cap": z.soil.infiltration_rate_mm_h,
                "drain_param": z.soil.drainage_parameter,
                "area_m2": z.area_m2,
                "max_rate": self._get_max_irrigation_rate(z_id),
            }

        records: List[Dict[str, Any]] = []
        target_tol = self.config.target_moisture_tolerance_pct

        # Sequential Discrete Multizone Closed-Loop Simulation
        for step in range(total_steps):
            row_w = weather_df.iloc[step]
            row_et = et0_df.iloc[step]
            ts = str(row_w["timestamp"])

            # Common meteorological variables for step t
            temp_c = float(row_w["temperature"])
            hum_pct = float(row_w["humidity"])
            solar_wm2 = float(row_w["solar_radiation"])
            wind_ms = float(row_w["wind_speed"])
            rain_step_mm = float(row_w["rainfall"])
            et0_step_mm = float(row_et["et0"])

            # Common Weather Stress evaluated once per step
            weather_stress_t = self.fis_weather.evaluate(
                temperature=temp_c,
                humidity=hum_pct,
                solar_radiation=solar_wm2,
                wind_speed=wind_ms,
                rainfall=rain_step_mm,
            )

            # Common Effective Rainfall calculated for the step
            peff_step_mm = calculate_effective_rainfall(
                rainfall_mm=rain_step_mm,
                method=self.config.effective_rainfall_method,
                timestep_minutes=dt_min,
            )

            # Parallel Per-Zone Independent Evaluation
            for z in self.zones:
                z_id = z.zone_id
                state_z = current_states[z_id]
                zp = zone_params[z_id]

                # 1. Current Soil State (strictly causal: state at t)
                sm_z = state_z.soil_moisture
                storage_z = state_z.storage_mm

                # 2. Moisture Tracking Error
                error_z = calculate_moisture_error(zp["target_sm"], sm_z)

                # 3. Relative Soil Moisture
                rsm_z = calculate_relative_soil_moisture(sm_z, zp["wp"], zp["fc"])

                # 4. Soil Stress FIS
                soil_stress_z = self.fis_soil.evaluate(rsm=rsm_z, moisture_error=error_z)

                # 5. Crop Evapotranspiration ETc = Kc * ET0
                etc_z_mm = float(zp["kc"] * et0_step_mm)

                # 6. Crop Water Deficit
                crop_deficit_z_mm = calculate_crop_water_deficit(
                    etc_mm=etc_z_mm,
                    effective_rainfall_mm=peff_step_mm,
                )

                # 7. Water Demand FIS
                water_demand_z = self.fis_water.evaluate(
                    etc=etc_z_mm,
                    crop_water_deficit=crop_deficit_z_mm,
                    effective_rainfall=peff_step_mm,
                )

                # 8. Main Irrigation FIS (or Baseline mode override)
                if mode_clean == "fuzzy":
                    cmd_z = self.fis_main.evaluate(
                        soil_stress=soil_stress_z,
                        weather_stress=weather_stress_t,
                        water_demand=water_demand_z,
                        moisture_error=error_z,
                    )
                elif mode_clean == "none":
                    cmd_z = 0.0
                elif mode_clean == "fixed":
                    cmd_z = float(np.clip(
                        (self.config.fixed_rate_mm_h / zp["max_rate"]) * 100.0,
                        0.0,
                        100.0
                    ))

                # 9. Actuator Mapping: Command [%] -> Physical Application Depth [mm] & Volume [L]
                if mode_clean == "fixed":
                    irrig_app_z_mm = float(self.config.fixed_rate_mm_h * timestep_hours)
                else:
                    fractional_cmd = float(cmd_z) / 100.0
                    irrig_app_z_mm = float(fractional_cmd * zp["max_rate"] * timestep_hours)

                irrig_vol_z_l = float(irrig_app_z_mm * zp["area_m2"])

                # 10. Dynamic Root-Zone Soil Water Balance (Phase 5 engine)
                next_state_z = update_water_balance(
                    current_state=state_z,
                    irrigation_mm=irrig_app_z_mm,
                    effective_rainfall_mm=peff_step_mm,
                    etc_mm=etc_z_mm,
                    timestep_minutes=dt_min,
                    infiltration_rate_mm_h=zp["infilt_cap"],
                    drainage_parameter=zp["drain_param"],
                    timestamp=ts,
                )

                # 11. State Advance & Conservation Extraction
                next_sm_z = next_state_z.soil_moisture
                infilt_z_mm = next_state_z.infiltration_mm
                actual_et_z_mm = next_state_z.actual_et_mm
                drainage_z_mm = next_state_z.drainage_mm
                residual_z = next_state_z.water_balance_residual

                rec = {
                    "step": step,
                    "timestamp": ts,
                    "scenario": self.config.scenario.value,
                    "zone_id": z_id,
                    "crop": z.crop.name,
                    "soil_type": z.soil.soil_type.value,
                    "area_m2": zp["area_m2"],
                    "soil_moisture": round(sm_z, 4),
                    "target_moisture": round(zp["target_sm"], 4),
                    "moisture_error": round(error_z, 4),
                    "rsm": round(rsm_z, 4),
                    "soil_stress": round(soil_stress_z, 2),
                    "weather_stress": round(weather_stress_t, 2),
                    "water_demand": round(water_demand_z, 2),
                    "et0": round(et0_step_mm, 6),
                    "kc": round(zp["kc"], 3),
                    "etc": round(etc_z_mm, 6),
                    "rainfall": round(rain_step_mm, 4),
                    "effective_rainfall": round(peff_step_mm, 4),
                    "crop_water_deficit": round(crop_deficit_z_mm, 6),
                    "irrigation_command": round(cmd_z, 2),
                    "irrigation_application": round(irrig_app_z_mm, 6),
                    "irrigation_volume_l": round(irrig_vol_z_l, 4),
                    "infiltration": round(infilt_z_mm, 6),
                    "actual_et": round(actual_et_z_mm, 6),
                    "drainage": round(drainage_z_mm, 6),
                    "next_soil_moisture": round(next_sm_z, 4),
                    "water_balance_residual": round(residual_z, 10),
                    "storage_mm": round(storage_z, 4),
                }
                records.append(rec)

                # Advance this zone's state independently
                current_states[z_id] = next_state_z

        df = pd.DataFrame(records)
        # Sort sequentially by step and zone_id
        df = df.sort_values(by=["step", "zone_id"]).reset_index(drop=True)

        # Compute Per-Zone Metrics
        zone_metrics: Dict[int, ZoneClosedLoopMetrics] = {}
        total_zone_timesteps_in_band = 0

        for z in self.zones:
            z_id = z.zone_id
            z_df = df[df["zone_id"] == z_id].reset_index(drop=True)
            zp = zone_params[z_id]

            errors = z_df["moisture_error"].values
            abs_errors = np.abs(errors)
            mae = float(np.mean(abs_errors))
            rmse = float(np.sqrt(np.mean(errors ** 2)))
            iae = float(np.sum(abs_errors) * dt_min)

            moistures = z_df["soil_moisture"].values
            commands = z_df["irrigation_command"].values
            target_sm = zp["target_sm"]
            band_low = target_sm - target_tol
            band_high = target_sm + target_tol

            in_band = (moistures >= band_low) & (moistures <= band_high)
            in_band_indices = np.where(in_band)[0]
            time_to_target: Optional[int] = (
                int(in_band_indices[0] * dt_min) if len(in_band_indices) > 0 else None
            )
            time_in_target = int(np.sum(in_band) * dt_min)
            pct_in_target = float((time_in_target / (total_steps * dt_min)) * 100.0)
            total_zone_timesteps_in_band += int(np.sum(in_band))

            active_steps = int(np.sum(commands > 0.5))
            off_steps = int(np.sum(commands <= 0.5))

            residuals = np.abs(z_df["water_balance_residual"].values)
            max_res = float(np.max(residuals))
            mean_res = float(np.mean(residuals))
            res_violations = int(np.sum(residuals > 1e-6))

            tot_irrig_mm = float(np.sum(z_df["irrigation_application"].values))
            tot_irrig_l = float(tot_irrig_mm * zp["area_m2"])
            tot_etc_mm = float(np.sum(z_df["etc"].values))
            tot_etc_l = float(tot_etc_mm * zp["area_m2"])
            tot_drain_mm = float(np.sum(z_df["drainage"].values))
            tot_drain_l = float(tot_drain_mm * zp["area_m2"])

            z_metric = ZoneClosedLoopMetrics(
                zone_id=z_id,
                crop=z.crop.name,
                soil=z.soil.soil_type.value,
                area_m2=zp["area_m2"],
                scenario=self.config.scenario.value,
                mode=mode_clean,
                initial_soil_moisture=float(z_df["soil_moisture"].iloc[0]),
                final_soil_moisture=float(z_df["next_soil_moisture"].iloc[-1]),
                target_soil_moisture=target_sm,
                final_moisture_error=round(target_sm - float(z_df["next_soil_moisture"].iloc[-1]), 4),
                min_soil_moisture=float(np.min(moistures)),
                max_soil_moisture=float(np.max(moistures)),
                mean_soil_moisture=float(np.mean(moistures)),
                mean_irrigation_command=float(np.mean(commands)),
                max_irrigation_command=float(np.max(commands)),
                total_irrigation_applied_mm=round(tot_irrig_mm, 4),
                total_irrigation_volume_l=round(tot_irrig_l, 2),
                total_rainfall_mm=round(float(np.sum(z_df["rainfall"].values)), 4),
                total_effective_rainfall_mm=round(float(np.sum(z_df["effective_rainfall"].values)), 4),
                total_etc_mm=round(tot_etc_mm, 4),
                total_etc_volume_l=round(tot_etc_l, 2),
                total_actual_et_mm=round(float(np.sum(z_df["actual_et"].values)), 4),
                total_drainage_mm=round(tot_drain_mm, 4),
                total_drainage_volume_l=round(tot_drain_l, 2),
                active_irrigation_timesteps=active_steps,
                off_irrigation_timesteps=off_steps,
                time_to_target_band_minutes=time_to_target,
                time_in_target_band_minutes=time_in_target,
                percentage_in_target_band=round(pct_in_target, 2),
                mae=round(mae, 4),
                rmse=round(rmse, 4),
                iae=round(iae, 4),
                max_absolute_residual=max_res,
                mean_absolute_residual=mean_res,
                residual_violations=res_violations,
            )
            zone_metrics[z_id] = z_metric

        # Compute System-Level Aggregate Metrics
        total_area = sum(z.area_m2 for z in self.zones)
        total_sys_vol_l = sum(m.total_irrigation_volume_l for m in zone_metrics.values())
        total_sys_etc_vol_l = sum(m.total_etc_volume_l for m in zone_metrics.values())
        total_sys_drain_vol_l = sum(m.total_drainage_volume_l for m in zone_metrics.values())
        total_sys_aet_vol_l = sum(
            float(np.sum(df[df["zone_id"] == z_id]["actual_et"]) * zone_params[z_id]["area_m2"])
            for z_id in zone_metrics
        )

        weighted_irrig_mm = total_sys_vol_l / total_area
        weighted_etc_mm = total_sys_etc_vol_l / total_area

        mean_mae = float(np.mean([m.mae for m in zone_metrics.values()]))
        mean_rmse = float(np.mean([m.rmse for m in zone_metrics.values()]))
        total_iae = float(np.sum([m.iae for m in zone_metrics.values()]))

        total_possible_zone_steps = total_steps * len(self.zones)
        overall_occupancy_pct = (total_zone_timesteps_in_band / total_possible_zone_steps) * 100.0

        max_sys_res = max(m.max_absolute_residual for m in zone_metrics.values())
        total_sys_res_viol = sum(m.residual_violations for m in zone_metrics.values())

        system_metrics = SystemClosedLoopMetrics(
            scenario=self.config.scenario.value,
            mode=mode_clean,
            zone_count=len(self.zones),
            total_system_area_m2=total_area,
            total_system_irrigation_volume_l=round(total_sys_vol_l, 2),
            total_system_etc_volume_l=round(total_sys_etc_vol_l, 2),
            total_system_actual_et_volume_l=round(total_sys_aet_vol_l, 2),
            total_system_drainage_volume_l=round(total_sys_drain_vol_l, 2),
            weighted_irrigation_depth_mm=round(weighted_irrig_mm, 4),
            weighted_etc_depth_mm=round(weighted_etc_mm, 4),
            system_mean_mae=round(mean_mae, 4),
            system_mean_rmse=round(mean_rmse, 4),
            system_total_iae=round(total_iae, 4),
            total_zone_timesteps_in_band=total_zone_timesteps_in_band,
            overall_target_band_occupancy_pct=round(overall_occupancy_pct, 2),
            max_conservation_residual=max_sys_res,
            total_residual_violations=total_sys_res_viol,
        )

        return MultizoneSimulationResult(
            df=df,
            zone_metrics=zone_metrics,
            system_metrics=system_metrics,
        )


def simulate_multizone_closed_loop(
    scenario: SimulationScenario = SimulationScenario.NORMAL,
    parameters: Optional[MultizoneClosedLoopConfig] = None,
    mode: str = "fuzzy",
    fis_main: Optional[MainIrrigationFIS] = None,
) -> MultizoneSimulationResult:
    """Convenience API to run a complete multizone closed-loop simulation.

    Args:
        scenario: Environmental weather scenario enum.
        parameters: Optional MultizoneClosedLoopConfig instance.
        mode: Control mode ('fuzzy', 'none', 'fixed').
        fis_main: Optional custom MainIrrigationFIS instance.

    Returns:
        MultizoneSimulationResult: Consolidated DataFrame, per-zone metrics, and system metrics.
    """
    cfg = parameters if parameters is not None else MultizoneClosedLoopConfig(scenario=scenario)
    cfg.scenario = scenario
    simulator = MultizoneClosedLoopSimulator(config=cfg, fis_main=fis_main)
    return simulator.run(mode=mode)
