"""Controller Benchmark Simulation Engine: Fuzzy vs PID vs On-Off.

Direct parity with MATLAB simulation.run_benchmark_comparison:
Compares:
1. Hierarchical Mamdani Fuzzy Controller (5 FIS stages + bounded arbitrator)
2. On-Off (Bang-Bang Hysteresis) Controller (turns ON below Target-2%, OFF at Target)
3. Classical PID Controller (Discrete error tracking with Anti-Windup Clamping)
"""

from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from config.schemas import SimulationScenario, ZoneConfig
from config.defaults import get_default_zones
from simulation.weather import WeatherEngine
from models.et0 import compute_et0_timeseries
from models.etc import calculate_effective_rainfall
from models.soil import calculate_relative_soil_moisture, calculate_moisture_error
from models.water_balance import update_soil_moisture_step
from simulation.water_allocation import bounded_priority_weighted_allocation
from fuzzy_engine.soil_stress import SoilStressFIS
from fuzzy_engine.weather_stress import WeatherStressFIS
from fuzzy_engine.water_demand import WaterDemandFIS
from fuzzy_engine.irrigation import MainIrrigationFIS
from fuzzy_engine.water_allocation import WaterAllocationFIS


class ControllerMetrics(BaseModel):
    name: str
    total_water_l: float
    rmse_pct: float
    mae_pct: float
    valve_switches: int
    mean_command_pct: float
    savings_vs_onoff_pct: float = 0.0
    savings_vs_pid_pct: float = 0.0


class BenchmarkComparisonResult(BaseModel):
    scenario: str
    duration_hours: int
    timestep_minutes: int
    timesteps: int
    time_hours: List[float]
    controllers: Dict[str, ControllerMetrics]
    savings_vs_onoff_pct: float
    savings_vs_pid_pct: float
    zone_targets: Dict[int, float]
    # Timeseries for visualization (Zone 1 Tomato as reference)
    timeseries: Dict[str, List[float]]


def run_benchmark_comparison(
    scenario_name: str = "Normal",
    duration_hours: int = 24,
    dt_minutes: int = 60,
    seed: int = 42,
) -> BenchmarkComparisonResult:
    """Execute complete 24-hour benchmark comparison across Fuzzy, PID, and On-Off."""
    try:
        sc_enum = SimulationScenario(scenario_name.lower().replace(" ", "_").replace("&", "and"))
    except Exception:
        sc_enum = SimulationScenario.NORMAL

    # 1. Weather timeline
    w_engine = WeatherEngine(scenario=sc_enum, seed=seed)
    weather_df = w_engine.generate_timeline(duration_hours=duration_hours, timestep_minutes=dt_minutes)
    et0_df = compute_et0_timeseries(weather_df, timestep_minutes=dt_minutes)
    total_steps = len(weather_df)
    time_hours = [round(i * (dt_minutes / 60.0), 2) for i in range(total_steps)]
    dt_hr = dt_minutes / 60.0

    # 2. Zones & Setup
    zones = get_default_zones()
    zone_ids = [z.zone_id for z in zones]
    areas = {z.zone_id: z.area_m2 for z in zones}
    priorities = {1: 70.0, 2: 40.0, 3: 85.0}
    targets = {z.zone_id: z.target_moisture for z in zones}
    fcs = {z.zone_id: z.soil.field_capacity for z in zones}
    wps = {z.zone_id: z.soil.wilting_point for z in zones}
    sats = {z.zone_id: z.soil.saturation for z in zones}
    zrs = {z.zone_id: z.crop.root_depth_m for z in zones}
    kcs = {z.zone_id: z.crop.kc for z in zones}

    # Available supply (60 L/min nominal capacity)
    avail_supply_l = 60.0 * dt_minutes

    # =========================================================================
    # 1. HIERARCHICAL FUZZY CONTROLLER
    # =========================================================================
    fis_soil = SoilStressFIS()
    fis_weather = WeatherStressFIS()
    fis_demand = WaterDemandFIS()
    fis_main = MainIrrigationFIS()
    fis_alloc = WaterAllocationFIS()

    fuzzy_sm = {z_id: np.zeros(total_steps) for z_id in zone_ids}
    fuzzy_cmd = {z_id: np.zeros(total_steps) for z_id in zone_ids}
    fuzzy_alloc = {z_id: np.zeros(total_steps) for z_id in zone_ids}
    for z in zones:
        fuzzy_sm[z.zone_id][0] = z.initial_moisture

    # Maximum delivery rate for hourly control steps (4.0 mm/h)
    nominal_delivery_rate_mm_h = 4.0
    cutoff_threshold = 18.0  # Corresponds to linguistic term 'Off'

    for t in range(total_steps):
        row_w = weather_df.iloc[t]
        row_et = et0_df.iloc[t]
        t_c = float(row_w["temperature"])
        rh = float(row_w["humidity"])
        rs = float(row_w["solar_radiation"])
        u2 = float(row_w["wind_speed"])
        p_mm = float(row_w["rainfall"])
        et0_val = float(row_et["et0_rate_mm_day"])

        ws_val = float(fis_weather.evaluate(
            temperature=t_c, humidity=rh, solar_radiation=rs, wind_speed=u2, rainfall=p_mm
        ))
        peff_step = calculate_effective_rainfall(p_mm, timestep_minutes=dt_minutes)

        raw_reqs: Dict[int, float] = {}
        fuzzy_reqs: Dict[int, float] = {}
        for z_id in zone_ids:
            curr_sm = fuzzy_sm[z_id][t]
            rsm = calculate_relative_soil_moisture(curr_sm, wps[z_id], fcs[z_id])
            err = calculate_moisture_error(targets[z_id], curr_sm)

            ss = float(fis_soil.evaluate(rsm=rsm, moisture_error=err))
            etc = kcs[z_id] * et0_val
            c_def = max(0.0, etc - (peff_step * (1440.0 / dt_minutes)))
            wd = float(fis_demand.evaluate(etc=etc, crop_water_deficit=c_def, effective_rainfall=peff_step))

            cmd = float(fis_main.evaluate(
                soil_stress=ss, weather_stress=ws_val, water_demand=wd, moisture_error=err
            ))
            # Deadband cutoff: below 18% is Off
            effective_cmd = max(0.0, (cmd - cutoff_threshold) / (100.0 - cutoff_threshold) * 100.0) if cmd > cutoff_threshold else 0.0
            fuzzy_cmd[z_id][t] = effective_cmd

            req_l = (effective_cmd / 100.0) * (nominal_delivery_rate_mm_h * areas[z_id] * dt_hr)
            raw_reqs[z_id] = req_l

            af = float(fis_alloc.evaluate(
                available_water=100.0, zone_demand=wd, zone_stress=ss, zone_priority=priorities[z_id]
            ))
            fuzzy_reqs[z_id] = req_l * (af / 100.0)

        granted_l = bounded_priority_weighted_allocation(
            raw_requests_l=fuzzy_reqs, priorities_pct=priorities, available_supply_l=avail_supply_l
        )

        for z_id in zone_ids:
            fuzzy_alloc[z_id][t] = granted_l[z_id]
            app_mm = granted_l[z_id] / areas[z_id]
            step_etc = (kcs[z_id] * et0_val / 24.0) * dt_hr

            next_sm = update_soil_moisture_step(
                current_moisture=fuzzy_sm[z_id][t],
                irrigation_depth_mm=app_mm,
                effective_rainfall_mm=peff_step,
                etc_mm=step_etc,
                field_capacity=fcs[z_id],
                wilting_point=wps[z_id],
                saturation=sats[z_id],
                root_depth_m=zrs[z_id],
                drainage_coefficient=0.08,
                infiltration_rate_mm_h=20.0,
                timestep_minutes=dt_minutes,
            )
            if t + 1 < total_steps:
                fuzzy_sm[z_id][t + 1] = next_sm

    # =========================================================================
    # 2. ON-OFF (BANG-BANG HYSTERESIS) CONTROLLER
    # =========================================================================
    onoff_sm = {z_id: np.zeros(total_steps) for z_id in zone_ids}
    onoff_cmd = {z_id: np.zeros(total_steps) for z_id in zone_ids}
    onoff_alloc = {z_id: np.zeros(total_steps) for z_id in zone_ids}
    for z in zones:
        onoff_sm[z.zone_id][0] = z.initial_moisture

    for t in range(total_steps):
        row_w = weather_df.iloc[t]
        row_et = et0_df.iloc[t]
        p_mm = float(row_w["rainfall"])
        et0_val = float(row_et["et0_rate_mm_day"])
        peff_step = calculate_effective_rainfall(p_mm, timestep_minutes=dt_minutes)

        raw_reqs = {}
        for z_id in zone_ids:
            curr_sm = onoff_sm[z_id][t]
            target = targets[z_id]
            # Hysteresis Bang-Bang
            if curr_sm < target - 2.0:
                cmd = 100.0
            elif curr_sm >= target:
                cmd = 0.0
            else:
                cmd = onoff_cmd[z_id][t - 1] if t > 0 else 0.0

            onoff_cmd[z_id][t] = cmd
            req_l = (cmd / 100.0) * (nominal_delivery_rate_mm_h * areas[z_id] * dt_hr)
            raw_reqs[z_id] = req_l

        granted_l = bounded_priority_weighted_allocation(
            raw_requests_l=raw_reqs, priorities_pct=priorities, available_supply_l=avail_supply_l
        )

        for z_id in zone_ids:
            onoff_alloc[z_id][t] = granted_l[z_id]
            app_mm = granted_l[z_id] / areas[z_id]
            step_etc = (kcs[z_id] * et0_val / 24.0) * dt_hr

            next_sm = update_soil_moisture_step(
                current_moisture=onoff_sm[z_id][t],
                irrigation_depth_mm=app_mm,
                effective_rainfall_mm=peff_step,
                etc_mm=step_etc,
                field_capacity=fcs[z_id],
                wilting_point=wps[z_id],
                saturation=sats[z_id],
                root_depth_m=zrs[z_id],
                drainage_coefficient=0.08,
                infiltration_rate_mm_h=20.0,
                timestep_minutes=dt_minutes,
            )
            if t + 1 < total_steps:
                onoff_sm[z_id][t + 1] = next_sm

    # =========================================================================
    # 3. CLASSICAL PID CONTROLLER (WITH ANTI-WINDUP)
    # =========================================================================
    pid_sm = {z_id: np.zeros(total_steps) for z_id in zone_ids}
    pid_cmd = {z_id: np.zeros(total_steps) for z_id in zone_ids}
    pid_alloc = {z_id: np.zeros(total_steps) for z_id in zone_ids}
    for z in zones:
        pid_sm[z.zone_id][0] = z.initial_moisture

    kp, ki, kd = 4.5, 0.6, 1.2
    integral_err = {z_id: 0.0 for z_id in zone_ids}
    prev_err = {z_id: 0.0 for z_id in zone_ids}

    for t in range(total_steps):
        row_w = weather_df.iloc[t]
        row_et = et0_df.iloc[t]
        p_mm = float(row_w["rainfall"])
        et0_val = float(row_et["et0_rate_mm_day"])
        peff_step = calculate_effective_rainfall(p_mm, timestep_minutes=dt_minutes)

        raw_reqs = {}
        for z_id in zone_ids:
            curr_sm = pid_sm[z_id][t]
            err = targets[z_id] - curr_sm
            integral_err[z_id] = max(-12.0, min(12.0, integral_err[z_id] + err * dt_hr))
            deriv = (err - prev_err[z_id]) / dt_hr
            prev_err[z_id] = err

            u = kp * err + ki * integral_err[z_id] + kd * deriv
            cmd = max(0.0, min(100.0, u))
            pid_cmd[z_id][t] = cmd
            req_l = (cmd / 100.0) * (nominal_delivery_rate_mm_h * areas[z_id] * dt_hr)
            raw_reqs[z_id] = req_l

        granted_l = bounded_priority_weighted_allocation(
            raw_requests_l=raw_reqs, priorities_pct=priorities, available_supply_l=avail_supply_l
        )

        for z_id in zone_ids:
            pid_alloc[z_id][t] = granted_l[z_id]
            app_mm = granted_l[z_id] / areas[z_id]
            step_etc = (kcs[z_id] * et0_val / 24.0) * dt_hr

            next_sm = update_soil_moisture_step(
                current_moisture=pid_sm[z_id][t],
                irrigation_depth_mm=app_mm,
                effective_rainfall_mm=peff_step,
                etc_mm=step_etc,
                field_capacity=fcs[z_id],
                wilting_point=wps[z_id],
                saturation=sats[z_id],
                root_depth_m=zrs[z_id],
                drainage_coefficient=0.08,
                infiltration_rate_mm_h=20.0,
                timestep_minutes=dt_minutes,
            )
            if t + 1 < total_steps:
                pid_sm[z_id][t + 1] = next_sm

    # =========================================================================
    # 4. METRIC COMPUTATION
    # =========================================================================
    def calc_metrics(name: str, sm_dict: Dict[int, np.ndarray], cmd_dict: Dict[int, np.ndarray], alloc_dict: Dict[int, np.ndarray]) -> ControllerMetrics:
        all_errs = []
        tot_water = sum(float(np.sum(alloc_dict[zid])) for zid in zone_ids)
        switches = sum(int(np.sum(np.abs(np.diff((cmd_dict[zid] > 5.0).astype(int))))) for zid in zone_ids)
        mean_cmd = float(np.mean([np.mean(cmd_dict[zid]) for zid in zone_ids]))

        for zid in zone_ids:
            err = targets[zid] - sm_dict[zid]
            all_errs.extend(err)

        err_arr = np.array(all_errs)
        rmse = float(np.sqrt(np.mean(err_arr ** 2)))
        mae = float(np.mean(np.abs(err_arr)))

        return ControllerMetrics(
            name=name,
            total_water_l=round(tot_water, 1),
            rmse_pct=round(rmse, 2),
            mae_pct=round(mae, 2),
            valve_switches=switches,
            mean_command_pct=round(mean_cmd, 1),
        )

    m_fuzzy = calc_metrics("Fuzzy Logic Control", fuzzy_sm, fuzzy_cmd, fuzzy_alloc)
    m_onoff = calc_metrics("On-Off (Bang-Bang)", onoff_sm, onoff_cmd, onoff_alloc)
    m_pid = calc_metrics("Classical PID", pid_sm, pid_cmd, pid_alloc)

    sav_onoff = max(0.0, (m_onoff.total_water_l - m_fuzzy.total_water_l) / m_onoff.total_water_l * 100.0) if m_onoff.total_water_l > 0 else 0.0
    sav_pid = max(0.0, (m_pid.total_water_l - m_fuzzy.total_water_l) / m_pid.total_water_l * 100.0) if m_pid.total_water_l > 0 else 0.0

    m_fuzzy.savings_vs_onoff_pct = round(sav_onoff, 1)
    m_fuzzy.savings_vs_pid_pct = round(sav_pid, 1)
    m_onoff.savings_vs_onoff_pct = 0.0
    m_pid.savings_vs_onoff_pct = round((m_onoff.total_water_l - m_pid.total_water_l) / m_onoff.total_water_l * 100.0, 1) if m_onoff.total_water_l > 0 else 0.0

    controllers_dict = {
        "fuzzy": m_fuzzy,
        "pid": m_pid,
        "onoff": m_onoff,
    }

    # Reference timeseries for Zone 1 (Tomato)
    ts_dict = {
        "fuzzy_sm_zone1": [round(float(v), 2) for v in fuzzy_sm[1]],
        "pid_sm_zone1": [round(float(v), 2) for v in pid_sm[1]],
        "onoff_sm_zone1": [round(float(v), 2) for v in onoff_sm[1]],
        "fuzzy_cmd_zone1": [round(float(v), 1) for v in fuzzy_cmd[1]],
        "pid_cmd_zone1": [round(float(v), 1) for v in pid_cmd[1]],
        "onoff_cmd_zone1": [round(float(v), 1) for v in onoff_cmd[1]],
    }

    return BenchmarkComparisonResult(
        scenario=scenario_name,
        duration_hours=duration_hours,
        timestep_minutes=dt_minutes,
        timesteps=total_steps,
        time_hours=time_hours,
        controllers=controllers_dict,
        savings_vs_onoff_pct=round(sav_onoff, 1),
        savings_vs_pid_pct=round(sav_pid, 1),
        zone_targets=targets,
        timeseries=ts_dict,
    )
