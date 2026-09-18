"""Discrete-time dynamic root-zone soil water balance model.

Governing Water Conservation Equation:
    S(t+1) = S(t) + I_inf(t) + Peff_inf(t) - ETc_actual(t) - Drainage(t)

Where:
    S(t): Root-zone water storage at time t [mm] = 1000 * theta(t) * Zr
    I_inf(t): Infiltrated irrigation depth [mm]
    Peff_inf(t): Infiltrated effective rainfall depth [mm]
    ETc_actual(t): Actual crop evapotranspiration water loss [mm]
    Drainage(t): Deep percolation below root zone [mm]
    S(t+1): Updated root-zone water storage [mm]

Physical Constraints:
    - Moisture cannot fall below Permanent Wilting Point (WP) through evapotranspiration alone.
    - Moisture cannot exceed Saturation (SAT); excess incoming water becomes surface runoff.
    - Gravity drainage occurs when moisture exceeds Field Capacity (FC).
    - Water balance residual |S_init + Inflow - Outflow - S_final| ~ 0.0 is strictly tracked.
"""

from typing import Optional, Union, Dict, Any, Tuple, List
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from config.schemas import SoilParameters, CropParameters, ZoneConfig
from models.soil import (
    calculate_relative_soil_moisture,
    calculate_moisture_error,
    calculate_taw,
    calculate_raw,
    soil_moisture_to_storage,
    storage_to_soil_moisture,
    calculate_infiltration,
    calculate_drainage,
)


class SoilState(BaseModel):
    """Structured agronomic and hydrological state of a single root-zone compartment."""

    zone_id: int = Field(default=1, description="Agricultural zone identifier")
    step: int = Field(default=0, description="Simulation timestep index")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp of observation")

    # Moisture states (working scale % and volumetric fraction m3/m3)
    soil_moisture: float = Field(..., description="Soil moisture content in working percentage (%)")
    soil_moisture_fraction: float = Field(..., description="Volumetric water content theta (m3/m3)")
    storage_mm: float = Field(..., description="Equivalent water depth stored in root zone (mm)")
    rsm: float = Field(..., ge=0.0, le=1.0, description="Relative Soil Moisture in [0.0, 1.0]")
    moisture_error: float = Field(..., description="Closed loop error e(t) = target - current (%)")

    # Agronomic thresholds
    target_moisture: float = Field(..., description="Target soil moisture set-point (%)")
    field_capacity: float = Field(..., description="Field capacity (%)")
    wilting_point: float = Field(..., description="Permanent wilting point (%)")
    saturation: float = Field(..., description="Saturation moisture content (%)")
    root_depth_m: float = Field(..., gt=0.0, description="Root-zone depth Zr (m)")
    taw_mm: float = Field(..., description="Total Available Water (mm)")
    raw_mm: float = Field(..., description="Readily Available Water (mm)")

    # Fluxes across timestep (mm)
    irrigation_applied_mm: float = Field(default=0.0, description="Applied irrigation (mm)")
    effective_rainfall_applied_mm: float = Field(default=0.0, description="Applied effective rain (mm)")
    infiltration_mm: float = Field(default=0.0, description="Actual infiltrated water into root zone (mm)")
    surface_runoff_mm: float = Field(default=0.0, description="Excess surface water rejected by soil (mm)")
    etc_mm: float = Field(default=0.0, description="Crop evapotranspiration demand (mm)")
    actual_et_mm: float = Field(default=0.0, description="Actual evapotranspiration extracted (mm)")
    drainage_mm: float = Field(default=0.0, description="Deep percolation below root zone (mm)")

    # Diagnostic indicators
    water_stress_indicator: float = Field(default=0.0, ge=0.0, le=1.0, description="Plant water stress indicator [0=none, 1=severe]")
    water_balance_residual: float = Field(default=0.0, description="Conservation residual error (mm)")


def update_soil_moisture_step(
    current_moisture: float,
    irrigation_depth_mm: float,
    effective_rainfall_mm: float,
    etc_mm: float,
    field_capacity: float,
    wilting_point: float,
    saturation: float,
    root_depth_m: float,
    drainage_coefficient: float = 0.08,
    infiltration_rate_mm_h: float = 20.0,
    timestep_minutes: int = 1,
) -> float:
    """Compute updated volumetric soil moisture SM(t+1) for the next simulation timestep.

    Canonical Section 6 functional contract for Phase 5.

    Args:
        current_moisture: Soil moisture at step t (% or fraction).
        irrigation_depth_mm: Applied irrigation depth (mm).
        effective_rainfall_mm: Effective precipitation depth (mm).
        etc_mm: Potential crop evapotranspiration loss (mm).
        field_capacity: Field capacity (% or fraction).
        wilting_point: Permanent wilting point (% or fraction).
        saturation: Soil saturation capacity (% or fraction).
        root_depth_m: Root-zone depth in meters.
        drainage_coefficient: Soil gravity drainage rate parameter.
        infiltration_rate_mm_h: Maximum infiltration capacity in mm/h.
        timestep_minutes: Discretization step in minutes.

    Returns:
        float: Updated soil moisture SM(t+1) in the same units as current_moisture.
    """
    is_percent = current_moisture > 1.0 or field_capacity > 1.0

    # Ensure consistent percentage representation internally
    sm_pct = current_moisture if is_percent else current_moisture * 100.0
    fc_pct = field_capacity if is_percent else field_capacity * 100.0
    wp_pct = wilting_point if is_percent else wilting_point * 100.0
    sat_pct = saturation if is_percent else saturation * 100.0

    # 1. Current storage
    s_init = soil_moisture_to_storage(sm_pct, root_depth_m)
    s_wp = soil_moisture_to_storage(wp_pct, root_depth_m)
    s_fc = soil_moisture_to_storage(fc_pct, root_depth_m)
    s_sat = soil_moisture_to_storage(sat_pct, root_depth_m)

    # 2. Infiltration & Runoff
    total_incoming = max(0.0, float(irrigation_depth_mm)) + max(0.0, float(effective_rainfall_mm))
    infiltrated, _ = calculate_infiltration(
        incoming_water_mm=total_incoming,
        infiltration_rate_mm_h=infiltration_rate_mm_h,
        timestep_minutes=timestep_minutes,
        current_moisture_pct=sm_pct,
        saturation_pct=sat_pct,
    )

    # 3. Add infiltration
    s_after_inflow = s_init + infiltrated

    # 4. Actual ET extraction: cannot pull storage below WP
    available_to_et = max(0.0, s_after_inflow - s_wp)
    actual_et = min(max(0.0, float(etc_mm)), available_to_et)
    s_after_et = s_after_inflow - actual_et

    # 5. Gravity Drainage (occurs when storage exceeds FC)
    drainage = calculate_drainage(
        current_storage_mm=s_after_et,
        field_capacity_storage_mm=s_fc,
        drainage_parameter=drainage_coefficient,
        saturation_storage_mm=s_sat,
    )
    s_final = max(s_wp, s_after_et - drainage)

    # 6. Convert to moisture
    sm_final_pct = storage_to_soil_moisture(s_final, root_depth_m, as_percent=True)
    sm_final_pct = np.clip(sm_final_pct, wp_pct, sat_pct)

    if is_percent:
        return float(sm_final_pct)
    return float(sm_final_pct / 100.0)


def update_water_balance(
    current_state: SoilState,
    irrigation_mm: float = 0.0,
    effective_rainfall_mm: float = 0.0,
    etc_mm: float = 0.0,
    timestep_minutes: int = 1,
    infiltration_rate_mm_h: float = 20.0,
    drainage_parameter: float = 0.08,
    timestamp: Optional[str] = None,
) -> SoilState:
    """Execute complete state transition update for one discrete simulation epoch.

    Maintains rigorous water conservation accounting and produces complete diagnostic telemetry.

    Args:
        current_state: SoilState at start of timestep t.
        irrigation_mm: Applied irrigation depth in mm.
        effective_rainfall_mm: Effective precipitation in mm.
        etc_mm: Potential crop evapotranspiration in mm.
        timestep_minutes: Step size in minutes.
        infiltration_rate_mm_h: Maximum infiltration rate (mm/h).
        drainage_parameter: Soil gravity drainage parameter.
        timestamp: Optional current timestamp string.

    Returns:
        SoilState: Complete updated state at t+1.
    """
    s_init = current_state.storage_mm
    zr = current_state.root_depth_m
    wp_pct = current_state.wilting_point
    fc_pct = current_state.field_capacity
    sat_pct = current_state.saturation
    target_pct = current_state.target_moisture
    taw = current_state.taw_mm
    raw = current_state.raw_mm

    s_wp = soil_moisture_to_storage(wp_pct, zr)
    s_fc = soil_moisture_to_storage(fc_pct, zr)
    s_sat = soil_moisture_to_storage(sat_pct, zr)

    # 1. Surface Inflow, Infiltration & Runoff
    w_irr = max(0.0, float(irrigation_mm))
    w_rain = max(0.0, float(effective_rainfall_mm))
    w_incoming = w_irr + w_rain

    infiltrated, runoff = calculate_infiltration(
        incoming_water_mm=w_incoming,
        infiltration_rate_mm_h=infiltration_rate_mm_h,
        timestep_minutes=timestep_minutes,
        current_moisture_pct=current_state.soil_moisture,
        saturation_pct=sat_pct,
    )

    # 2. Add infiltrated water to root-zone storage
    s_after_inflow = s_init + infiltrated

    # 3. Actual ET extraction (cannot deplete below Wilting Point)
    etc_val = max(0.0, float(etc_mm))
    available_to_et = max(0.0, s_after_inflow - s_wp)
    actual_et = min(etc_val, available_to_et)
    s_after_et = s_after_inflow - actual_et

    # 4. Drainage / Deep Percolation
    drainage = calculate_drainage(
        current_storage_mm=s_after_et,
        field_capacity_storage_mm=s_fc,
        drainage_parameter=drainage_parameter,
        saturation_storage_mm=s_sat,
    )
    s_final = max(s_wp, s_after_et - drainage)

    # 5. Conservation Residual: S_init + Infiltrated - Actual_ET - Drainage - S_final
    residual = s_init + infiltrated - actual_et - drainage - s_final

    # 6. Updated soil moisture values
    sm_final_pct = storage_to_soil_moisture(s_final, zr, as_percent=True)
    sm_final_pct = float(np.clip(sm_final_pct, wp_pct, sat_pct))
    sm_final_frac = sm_final_pct / 100.0

    # 7. Normalized indicators
    rsm_final = calculate_relative_soil_moisture(sm_final_pct, wp_pct, fc_pct)
    err_final = calculate_moisture_error(target_pct, sm_final_pct)

    # 8. Water stress indicator: activates when storage drops below FC - RAW
    stress_threshold = s_fc - raw
    if s_final < stress_threshold:
        stress = (stress_threshold - s_final) / max(1e-4, stress_threshold - s_wp)
        stress_indicator = float(np.clip(stress, 0.0, 1.0))
    else:
        stress_indicator = 0.0

    return SoilState(
        zone_id=current_state.zone_id,
        step=current_state.step + 1,
        timestamp=timestamp,
        soil_moisture=round(sm_final_pct, 4),
        soil_moisture_fraction=round(sm_final_frac, 6),
        storage_mm=round(s_final, 4),
        rsm=round(rsm_final, 4),
        moisture_error=round(err_final, 4),
        target_moisture=target_pct,
        field_capacity=fc_pct,
        wilting_point=wp_pct,
        saturation=sat_pct,
        root_depth_m=zr,
        taw_mm=round(taw, 4),
        raw_mm=round(raw, 4),
        irrigation_applied_mm=round(w_irr, 4),
        effective_rainfall_applied_mm=round(w_rain, 4),
        infiltration_mm=round(infiltrated, 4),
        surface_runoff_mm=round(runoff, 4),
        etc_mm=round(etc_val, 4),
        actual_et_mm=round(actual_et, 4),
        drainage_mm=round(drainage, 4),
        water_stress_indicator=round(stress_indicator, 4),
        water_balance_residual=round(residual, 10),
    )


def initialize_soil_state(
    zone_config: ZoneConfig,
    depletion_fraction_p: float = 0.50,
    timestamp: Optional[str] = None,
) -> SoilState:
    """Initialize a SoilState instance from a ZoneConfig object."""
    z_id = zone_config.zone_id
    sm_init = zone_config.initial_moisture
    fc = zone_config.soil.field_capacity
    wp = zone_config.soil.wilting_point
    sat = zone_config.soil.saturation
    target = zone_config.target_moisture
    zr = zone_config.crop.root_depth_m

    taw = calculate_taw(fc, wp, zr)
    raw = calculate_raw(taw, depletion_fraction_p)
    s_init = soil_moisture_to_storage(sm_init, zr)
    rsm = calculate_relative_soil_moisture(sm_init, wp, fc)
    err = calculate_moisture_error(target, sm_init)

    stress_thresh = soil_moisture_to_storage(fc, zr) - raw
    stress = max(0.0, (stress_thresh - s_init) / max(1e-4, stress_thresh - soil_moisture_to_storage(wp, zr))) if s_init < stress_thresh else 0.0

    return SoilState(
        zone_id=z_id,
        step=0,
        timestamp=timestamp,
        soil_moisture=round(sm_init, 4),
        soil_moisture_fraction=round(sm_init / 100.0, 6),
        storage_mm=round(s_init, 4),
        rsm=round(rsm, 4),
        moisture_error=round(err, 4),
        target_moisture=target,
        field_capacity=fc,
        wilting_point=wp,
        saturation=sat,
        root_depth_m=zr,
        taw_mm=round(taw, 4),
        raw_mm=round(raw, 4),
        irrigation_applied_mm=0.0,
        effective_rainfall_applied_mm=0.0,
        infiltration_mm=0.0,
        surface_runoff_mm=0.0,
        etc_mm=0.0,
        actual_et_mm=0.0,
        drainage_mm=0.0,
        water_stress_indicator=round(min(1.0, stress), 4),
        water_balance_residual=0.0,
    )


def simulate_water_balance_timeseries(
    initial_state: SoilState,
    etc_series: Union[List[float], np.ndarray],
    effective_rainfall_series: Optional[Union[List[float], np.ndarray]] = None,
    irrigation_series: Optional[Union[List[float], np.ndarray]] = None,
    timestamps: Optional[List[str]] = None,
    timestep_minutes: int = 1,
    infiltration_rate_mm_h: float = 20.0,
    drainage_parameter: float = 0.08,
) -> pd.DataFrame:
    """Run sequential discrete root-zone water balance simulation over an input timeline.

    Args:
        initial_state: SoilState at step 0.
        etc_series: Array of ETc values (mm per step).
        effective_rainfall_series: Optional array of effective rainfall values (mm per step).
        irrigation_series: Optional array of irrigation commands (mm per step).
        timestamps: Optional list of timestamp strings.
        timestep_minutes: Discretization step in minutes.
        infiltration_rate_mm_h: Soil maximum infiltration rate (mm/h).
        drainage_parameter: Soil gravity drainage parameter.

    Returns:
        pd.DataFrame: Complete time-series logging all moisture states, fluxes, and conservation residuals.
    """
    n_steps = len(etc_series)
    peff_arr = np.zeros(n_steps) if effective_rainfall_series is None else np.asarray(effective_rainfall_series)
    irrig_arr = np.zeros(n_steps) if irrigation_series is None else np.asarray(irrigation_series)

    states: List[SoilState] = [initial_state]
    current = initial_state

    for i in range(n_steps):
        ts = timestamps[i] if (timestamps is not None and i < len(timestamps)) else None
        next_state = update_water_balance(
            current_state=current,
            irrigation_mm=float(irrig_arr[i]),
            effective_rainfall_mm=float(peff_arr[i]),
            etc_mm=float(etc_series[i]),
            timestep_minutes=timestep_minutes,
            infiltration_rate_mm_h=infiltration_rate_mm_h,
            drainage_parameter=drainage_parameter,
            timestamp=ts,
        )
        states.append(next_state)
        current = next_state

    # Convert list of SoilState instances to DataFrame (excluding step 0 or indexing appropriately)
    records = [s.model_dump() for s in states[1:]]  # Steps 1 to N
    return pd.DataFrame(records)
