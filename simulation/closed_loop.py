"""Single-Zone Closed-Loop Feedback Control Simulation Engine.

Implements the first true dynamic closed-loop feedback control simulation of the
hierarchical smart irrigation architecture for Zone 1 (Tomato, Loam soil, 100 m²).

At each discrete simulation timestep t (1-minute resolution over 24 hours):
1. Read current soil moisture: SM(t)
2. Moisture tracking error: e(t) = SM_target - SM(t)
3. Relative soil moisture: RSM(t) = [SM(t) - WP] / [FC - WP]
4. Soil Stress FIS: soil_stress(t) = SoilStressFIS(RSM(t), e(t))
5. Weather Stress FIS: weather_stress(t) = WeatherStressFIS(T(t), RH(t), Rs(t), u2(t), P(t))
6. Reference Evapotranspiration: ET0(t) from FAO-56 Penman-Monteith
7. Crop Evapotranspiration: ETc(t) = Kc(t) * ET0(t)
8. Effective Rainfall: Peff(t) from USDA-SCS sub-daily formulation
9. Crop Water Deficit: D_crop(t) = max(ETc(t) - Peff(t), 0.0)
10. Water Demand FIS: water_demand(t) = WaterDemandFIS(ETc(t), D_crop(t), Peff(t))
11. Main Irrigation FIS: irrigation_command(t) = MainIrrigationFIS(soil_stress, weather_stress, water_demand, e(t))
12. Actuator Mapping:
        I_app(t) = (irrigation_command(t) / 100.0) * I_max * (dt / 60) [mm]
13. Soil-Water Balance:
        S(t+1) = S(t) + W_inf(t) - ET_actual(t) - Drainage(t)
14. State Transition:
        SM(t+1) and RSM(t+1) feed strictly into timestep t+1 (no future state leakage).
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


class ClosedLoopConfig(BaseModel):
    """Configuration parameters for single-zone closed-loop feedback simulation."""

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
    zone_id: int = Field(
        default=1,
        ge=1,
        le=3,
        description="Target agricultural zone ID (Zone 1: Tomato / Loam)"
    )
    max_irrigation_rate_mm_h: float = Field(
        default=12.0,
        gt=0.0,
        le=50.0,
        description="Maximum actuator irrigation delivery rate in mm/hour at 100% command"
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


class ClosedLoopMetrics(BaseModel):
    """Agronomic, control, and conservation performance metrics for closed-loop simulation."""

    scenario: str = Field(..., description="Scenario name")
    zone_id: int = Field(..., description="Zone identifier")
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

    # Cumulative water fluxes (mm)
    total_irrigation_applied_mm: float = Field(..., description="Cumulative irrigation applied (mm)")
    total_rainfall_mm: float = Field(..., description="Cumulative rainfall observed (mm)")
    total_effective_rainfall_mm: float = Field(..., description="Cumulative effective rainfall infiltrated (mm)")
    total_etc_mm: float = Field(..., description="Cumulative crop evapotranspiration demand (mm)")
    total_actual_et_mm: float = Field(..., description="Cumulative actual evapotranspiration consumed (mm)")
    total_drainage_mm: float = Field(..., description="Cumulative deep percolation / drainage (mm)")

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


class ClosedLoopSimulator:
    """Dedicated single-zone closed-loop feedback controller and simulation orchestrator."""

    def __init__(
        self,
        config: Optional[ClosedLoopConfig] = None,
        zone_config: Optional[ZoneConfig] = None,
        fis_main: Optional[MainIrrigationFIS] = None,
    ) -> None:
        """Initialize ClosedLoopSimulator for single-zone evaluation.

        Args:
            config: ClosedLoopConfig instance. Defaults to Normal scenario on Zone 1.
            zone_config: Optional ZoneConfig override. Defaults to Zone 1 (Tomato / Loam).
            fis_main: Optional custom MainIrrigationFIS instance for parameter optimization.
        """
        self.config = config if config is not None else ClosedLoopConfig()

        # Select Zone 1 by default or matching zone_id
        if zone_config is not None:
            self.zone = zone_config
        else:
            default_zones = get_default_zones()
            matching = [z for z in default_zones if z.zone_id == self.config.zone_id]
            if not matching:
                raise ValueError(f"Zone ID {self.config.zone_id} not found in default zones.")
            self.zone = matching[0]

        # Initialize the 4 hierarchical Fuzzy Inference Systems
        self.fis_soil = SoilStressFIS(resolution=501)
        self.fis_weather = WeatherStressFIS(resolution=501)
        self.fis_water = WaterDemandFIS(resolution=501)
        self.fis_main = fis_main if fis_main is not None else MainIrrigationFIS(resolution=501)

    def run(
        self,
        mode: str = "fuzzy",
        weather_df: Optional[pd.DataFrame] = None,
        et0_df: Optional[pd.DataFrame] = None,
    ) -> Tuple[pd.DataFrame, ClosedLoopMetrics]:
        """Execute full closed-loop feedback simulation for the configured zone.

        Args:
            mode: Simulation control mode ('fuzzy', 'none', or 'fixed').
            weather_df: Optional pre-generated weather timeline DataFrame for fast evaluation.
            et0_df: Optional pre-generated ET0 time-series DataFrame.

        Returns:
            Tuple[pd.DataFrame, ClosedLoopMetrics]: Complete simulation dataset and metrics.
        """
        mode_clean = mode.strip().lower()
        if mode_clean not in ("fuzzy", "none", "fixed"):
            raise ValueError(f"Unknown control mode '{mode}'. Choose 'fuzzy', 'none', or 'fixed'.")

        dur_h = self.config.duration_hours
        dt_min = self.config.timestep_minutes
        total_steps = (dur_h * 60) // dt_min
        timestep_hours = dt_min / 60.0

        # Step 1: Generate Environmental Timeline if not provided
        if weather_df is None:
            weather_engine = WeatherEngine(
                scenario=self.config.scenario,
                seed=self.config.seed
            )
            weather_df = weather_engine.generate_timeline(
                duration_hours=dur_h,
                timestep_minutes=dt_min
            )

        # Step 2: Compute FAO-56 Reference Evapotranspiration ET0 if not provided
        if et0_df is None:
            et0_df = compute_et0_timeseries(
                weather_df,
                timestep_minutes=dt_min
            )

        # Crop parameters
        kc = self.zone.crop.kc
        zr = self.zone.crop.root_depth_m
        fc = self.zone.soil.field_capacity
        wp = self.zone.soil.wilting_point
        sat = self.zone.soil.saturation
        target_sm = self.zone.target_moisture
        infilt_cap = self.zone.soil.infiltration_rate_mm_h
        drain_param = self.zone.soil.drainage_parameter

        # Load depletion fraction p from crop database
        crop_db = CropCoefficientManager.load_crop_database()
        crop_match = crop_db[crop_db["crop"].str.capitalize() == self.zone.crop.name.capitalize()]
        p_frac = float(crop_match.iloc[0]["depletion_fraction_p"]) if not crop_match.empty else 0.50

        # Initialize root-zone soil state at step 0
        current_state = initialize_soil_state(
            zone_config=self.zone,
            depletion_fraction_p=p_frac,
            timestamp=str(weather_df["timestamp"].iloc[0]),
        )

        records: List[Dict[str, Any]] = []

        # Target band definition: target ± tolerance
        target_tol = self.config.target_moisture_tolerance_pct
        band_low = target_sm - target_tol
        band_high = target_sm + target_tol

        # Sequential Discrete Closed-Loop Feedback Loop
        for step in range(total_steps):
            row_w = weather_df.iloc[step]
            row_et = et0_df.iloc[step]
            ts = str(row_w["timestamp"])

            # -------------------------------------------------------------
            # STEP 1: Current Soil State (strictly causal: state at t)
            # -------------------------------------------------------------
            sm_t = current_state.soil_moisture
            storage_t = current_state.storage_mm

            # -------------------------------------------------------------
            # STEP 2: Moisture Tracking Error
            # -------------------------------------------------------------
            error_t = calculate_moisture_error(target_sm, sm_t)

            # -------------------------------------------------------------
            # STEP 3: Relative Soil Moisture
            # -------------------------------------------------------------
            rsm_t = calculate_relative_soil_moisture(sm_t, wp, fc)

            # -------------------------------------------------------------
            # STEP 4: Soil Stress FIS
            # -------------------------------------------------------------
            soil_stress_t = self.fis_soil.evaluate(rsm=rsm_t, moisture_error=error_t)

            # -------------------------------------------------------------
            # STEP 5: Weather Stress FIS
            # -------------------------------------------------------------
            temp_c = float(row_w["temperature"])
            hum_pct = float(row_w["humidity"])
            solar_wm2 = float(row_w["solar_radiation"])
            wind_ms = float(row_w["wind_speed"])
            rain_step_mm = float(row_w["rainfall"])

            weather_stress_t = self.fis_weather.evaluate(
                temperature=temp_c,
                humidity=hum_pct,
                solar_radiation=solar_wm2,
                wind_speed=wind_ms,
                rainfall=rain_step_mm,
            )

            # -------------------------------------------------------------
            # STEP 6: Reference Evapotranspiration ET0
            # -------------------------------------------------------------
            et0_step_mm = float(row_et["et0"])

            # -------------------------------------------------------------
            # STEP 7: Crop Evapotranspiration ETc
            # -------------------------------------------------------------
            etc_step_mm = float(kc * et0_step_mm)

            # -------------------------------------------------------------
            # STEP 8: Effective Rainfall Peff
            # -------------------------------------------------------------
            peff_step_mm = calculate_effective_rainfall(
                rainfall_mm=rain_step_mm,
                method=self.config.effective_rainfall_method,
                timestep_minutes=dt_min,
            )

            # -------------------------------------------------------------
            # STEP 9: Crop Water Deficit D_crop
            # -------------------------------------------------------------
            crop_deficit_step_mm = calculate_crop_water_deficit(
                etc_mm=etc_step_mm,
                effective_rainfall_mm=peff_step_mm,
            )

            # -------------------------------------------------------------
            # STEP 10: Water Demand FIS
            # -------------------------------------------------------------
            water_demand_t = self.fis_water.evaluate(
                etc=etc_step_mm,
                crop_water_deficit=crop_deficit_step_mm,
                effective_rainfall=peff_step_mm,
            )

            # -------------------------------------------------------------
            # STEP 11: Main Irrigation FIS (or Baseline mode override)
            # -------------------------------------------------------------
            if mode_clean == "fuzzy":
                cmd_t = self.fis_main.evaluate(
                    soil_stress=soil_stress_t,
                    weather_stress=weather_stress_t,
                    water_demand=water_demand_t,
                    moisture_error=error_t,
                )
            elif mode_clean == "none":
                cmd_t = 0.0
            elif mode_clean == "fixed":
                # Equivalent normalized command representing fixed application rate
                cmd_t = float(np.clip(
                    (self.config.fixed_rate_mm_h / self.config.max_irrigation_rate_mm_h) * 100.0,
                    0.0,
                    100.0
                ))

            # -------------------------------------------------------------
            # STEP 12: Actuator Mapping (Command [%] -> Application Depth [mm])
            # -------------------------------------------------------------
            if mode_clean == "fixed":
                irrig_app_step_mm = float(self.config.fixed_rate_mm_h * timestep_hours)
            else:
                fractional_cmd = float(cmd_t) / 100.0
                irrig_app_step_mm = float(
                    fractional_cmd * self.config.max_irrigation_rate_mm_h * timestep_hours
                )

            # -------------------------------------------------------------
            # STEP 13: Dynamic Root-Zone Soil Water Balance (Phase 5 engine)
            # -------------------------------------------------------------
            next_state = update_water_balance(
                current_state=current_state,
                irrigation_mm=irrig_app_step_mm,
                effective_rainfall_mm=peff_step_mm,
                etc_mm=etc_step_mm,
                timestep_minutes=dt_min,
                infiltration_rate_mm_h=infilt_cap,
                drainage_parameter=drain_param,
                timestamp=ts,
            )

            # -------------------------------------------------------------
            # STEP 14: Log State and Diagnostic Fluxes
            # -------------------------------------------------------------
            next_sm = next_state.soil_moisture
            infilt_mm = next_state.infiltration_mm
            actual_et_mm = next_state.actual_et_mm
            drainage_mm = next_state.drainage_mm
            residual = next_state.water_balance_residual

            rec = {
                "step": step,
                "timestamp": ts,
                "scenario": self.config.scenario.value,
                "zone_id": self.zone.zone_id,
                "crop": self.zone.crop.name,
                "soil_moisture": round(sm_t, 4),
                "target_moisture": round(target_sm, 4),
                "moisture_error": round(error_t, 4),
                "rsm": round(rsm_t, 4),
                "soil_stress": round(soil_stress_t, 2),
                "weather_stress": round(weather_stress_t, 2),
                "et0": round(et0_step_mm, 6),
                "etc": round(etc_step_mm, 6),
                "rainfall": round(rain_step_mm, 4),
                "effective_rainfall": round(peff_step_mm, 4),
                "crop_water_deficit": round(crop_deficit_step_mm, 6),
                "water_demand": round(water_demand_t, 2),
                "irrigation_command": round(cmd_t, 2),
                "irrigation_application": round(irrig_app_step_mm, 6),
                "infiltration": round(infilt_mm, 6),
                "actual_et": round(actual_et_mm, 6),
                "drainage": round(drainage_mm, 6),
                "next_soil_moisture": round(next_sm, 4),
                "water_balance_residual": round(residual, 10),
                "storage_mm": round(storage_t, 4),
            }
            records.append(rec)

            # Advance current state to next state (feedback closure)
            current_state = next_state

        df = pd.DataFrame(records)

        # Calculate Closed-Loop Performance Metrics
        errors = df["moisture_error"].values
        abs_errors = np.abs(errors)
        mae = float(np.mean(abs_errors))
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        iae = float(np.sum(abs_errors) * dt_min)

        moistures = df["soil_moisture"].values
        commands = df["irrigation_command"].values

        # Target band entry and residency
        in_band = (moistures >= band_low) & (moistures <= band_high)
        in_band_indices = np.where(in_band)[0]
        time_to_target_minutes: Optional[int] = (
            int(in_band_indices[0] * dt_min) if len(in_band_indices) > 0 else None
        )
        time_in_target_minutes = int(np.sum(in_band) * dt_min)
        pct_in_target = float((time_in_target_minutes / (total_steps * dt_min)) * 100.0)

        # Operational counts
        active_steps = int(np.sum(commands > 0.5))
        off_steps = int(np.sum(commands <= 0.5))

        # Conservation residuals
        residuals = np.abs(df["water_balance_residual"].values)
        max_res = float(np.max(residuals))
        mean_res = float(np.mean(residuals))
        res_violations = int(np.sum(residuals > 1e-6))

        metrics = ClosedLoopMetrics(
            scenario=self.config.scenario.value,
            zone_id=self.zone.zone_id,
            mode=mode_clean,
            initial_soil_moisture=float(df["soil_moisture"].iloc[0]),
            final_soil_moisture=float(df["next_soil_moisture"].iloc[-1]),
            target_soil_moisture=target_sm,
            final_moisture_error=round(target_sm - float(df["next_soil_moisture"].iloc[-1]), 4),
            min_soil_moisture=float(np.min(moistures)),
            max_soil_moisture=float(np.max(moistures)),
            mean_soil_moisture=float(np.mean(moistures)),
            mean_irrigation_command=float(np.mean(commands)),
            max_irrigation_command=float(np.max(commands)),
            total_irrigation_applied_mm=float(np.sum(df["irrigation_application"].values)),
            total_rainfall_mm=float(np.sum(df["rainfall"].values)),
            total_effective_rainfall_mm=float(np.sum(df["effective_rainfall"].values)),
            total_etc_mm=float(np.sum(df["etc"].values)),
            total_actual_et_mm=float(np.sum(df["actual_et"].values)),
            total_drainage_mm=float(np.sum(df["drainage"].values)),
            active_irrigation_timesteps=active_steps,
            off_irrigation_timesteps=off_steps,
            time_to_target_band_minutes=time_to_target_minutes,
            time_in_target_band_minutes=time_in_target_minutes,
            percentage_in_target_band=round(pct_in_target, 2),
            mae=round(mae, 4),
            rmse=round(rmse, 4),
            iae=round(iae, 4),
            max_absolute_residual=max_res,
            mean_absolute_residual=mean_res,
            residual_violations=res_violations,
        )

        return df, metrics


def simulate_single_zone(
    scenario: SimulationScenario = SimulationScenario.NORMAL,
    zone_id: int = 1,
    parameters: Optional[ClosedLoopConfig] = None,
    mode: str = "fuzzy",
    fis_main: Optional[MainIrrigationFIS] = None,
) -> Tuple[pd.DataFrame, ClosedLoopMetrics]:
    """Convenience API to run a single-zone simulation.

    Args:
        scenario: Environmental weather scenario enum.
        zone_id: Agricultural zone ID (default 1).
        parameters: Optional ClosedLoopConfig instance.
        mode: Control mode ('fuzzy', 'none', 'fixed').
        fis_main: Optional custom MainIrrigationFIS instance.

    Returns:
        Tuple[pd.DataFrame, ClosedLoopMetrics]: Complete simulation dataset and metrics.
    """
    cfg = parameters if parameters is not None else ClosedLoopConfig(scenario=scenario, zone_id=zone_id)
    cfg.scenario = scenario
    cfg.zone_id = zone_id
    simulator = ClosedLoopSimulator(config=cfg, fis_main=fis_main)
    return simulator.run(mode=mode)
