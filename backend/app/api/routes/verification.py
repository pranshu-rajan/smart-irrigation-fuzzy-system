"""Live engineering verification router.

Runs a deterministic smoke/integration verification against the actual
engineering engines used by the platform.  It is intentionally read-only
and does not require a user session so the Architecture page can expose a
transparent system-health/verification check.
"""

from time import perf_counter
from typing import Any, Dict

import numpy as np
from fastapi import APIRouter

from backend.app.services.fuzzy_service import FuzzyService
from config.schemas import SimulationScenario
from models.et0 import compute_et0_timeseries
from models.etc import calculate_etc, calculate_effective_rainfall, calculate_crop_water_deficit
from simulation.water_allocation import (
    MultizoneAllocationConfig,
    MultizoneAllocationSimulator,
)
from simulation.weather import WeatherEngine

router = APIRouter(prefix="/verification", tags=["System Verification"])


def _check(name: str, passed: bool, detail: str) -> Dict[str, Any]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "detail": detail}


@router.get("/system")
def verify_system() -> Dict[str, Any]:
    """Run deterministic component and 1-hour end-to-end control verification."""
    started = perf_counter()
    checks = []

    # 1. Fuzzy registry, variables and rule bases.
    fuzzy = FuzzyService()
    rule_counts = {k: len(v.RULES) for k, v in fuzzy.instances.items()}
    all_rules_present = len(rule_counts) == 5 and all(v > 0 for v in rule_counts.values())
    checks.append(_check("fuzzy_rule_bases", all_rules_present, f"5 Mamdani controllers; rule counts={rule_counts}"))

    # 1b. Every predefined FIS exposes at least one input/output variable definition.
    variable_counts = {}
    variables_ok = True
    for name in fuzzy.instances:
        try:
            vars_for_controller = fuzzy.get_variables_for_controller(name)
            variable_counts[name] = len(vars_for_controller)
            variables_ok = variables_ok and len(vars_for_controller) >= 2
        except Exception:
            variables_ok = False
            variable_counts[name] = 0
    checks.append(_check("fuzzy_variable_definitions", variables_ok, f"Variable definitions={variable_counts}"))

    # 2. Representative live inference for every FIS.
    samples = {
        "soil_stress": {"rsm": 0.5, "moisture_error": 5.0},
        "weather_stress": {"temperature": 30.0, "humidity": 50.0, "solar_radiation": 600.0, "wind_speed": 2.5, "rainfall": 0.0},
        "water_demand": {"etc": 5.0, "crop_water_deficit": 3.0, "effective_rainfall": 0.0},
        "main_irrigation": {"soil_stress": 40.0, "weather_stress": 45.0, "water_demand": 60.0, "moisture_error": 5.0},
        "water_allocation": {"available_water": 50.0, "zone_demand": 60.0, "zone_stress": 50.0, "zone_priority": 70.0},
    }
    outputs = {}
    inference_ok = True
    for name, inputs in samples.items():
        try:
            result = fuzzy.evaluate_controller(name, inputs)
            outputs[name] = round(float(result.crisp_output), 4)
            inference_ok = inference_ok and np.isfinite(result.crisp_output) and 0.0 <= result.crisp_output <= 100.0
        except Exception as exc:  # pragma: no cover - surfaced in response
            inference_ok = False
            outputs[name] = f"ERROR: {exc}"
    checks.append(_check("fuzzy_live_inference", inference_ok, f"Representative outputs={outputs}"))

    # 3. Weather + ET0 + ETc/deficit pipeline.
    weather = WeatherEngine(scenario=SimulationScenario.NORMAL, seed=42).generate_timeline(1, 1)
    et0 = compute_et0_timeseries(weather, timestep_minutes=1)
    etc_probe = calculate_etc(float(et0["et0"].iloc[0]), 1.15)
    peff_probe = calculate_effective_rainfall(float(weather["rainfall"].iloc[0]), timestep_minutes=1)
    deficit_probe = calculate_crop_water_deficit(etc_probe, peff_probe)
    et_ok = (len(weather) == 60 and len(et0) == 60 and np.isfinite(et0["et0"]).all()
             and (et0["et0"] >= 0).all() and np.isfinite(etc_probe) and etc_probe >= 0
             and np.isfinite(deficit_probe) and deficit_probe >= 0)
    checks.append(_check("weather_et0_etc_pipeline", bool(et_ok), f"60 weather/ET0 steps; ETc={etc_probe:.6f} mm; crop deficit={deficit_probe:.6f} mm"))

    # 4. Actual multizone end-to-end engine: environment -> ET0/ETc ->
    #    zone FIS -> allocation FIS -> hard constraints -> soil balance.
    sim = MultizoneAllocationSimulator(
        config=MultizoneAllocationConfig(
            scenario=SimulationScenario.NORMAL,
            duration_hours=1,
            timestep_minutes=1,
            seed=42,
        )
    ).run()
    telemetry = sim.telemetry_records
    n = len(telemetry)
    zones = sorted({int(r["zone_id"]) for r in telemetry})
    commands = np.asarray([float(r["irrigation_command"]) for r in telemetry])
    residuals = np.abs(np.asarray([float(r["water_balance_residual_mm"]) for r in telemetry]))
    allocated = np.asarray([float(r["water_volume_allocated_L"]) for r in telemetry])
    requested = np.asarray([float(r["water_volume_requested_L"]) for r in telemetry])

    loop_ok = (
        n == 60 * 3
        and zones == [1, 2, 3]
        and np.isfinite(commands).all()
        and (commands >= 0).all()
        and (commands <= 100).all()
        and np.isfinite(residuals).all()
        and residuals.max(initial=0.0) <= 1e-6
        and (allocated >= -1e-9).all()
        and (allocated <= requested + 1e-6).all()
    )
    checks.append(_check("closed_loop_multizone", bool(loop_ok), f"{n} telemetry rows, zones={zones}, max balance residual={float(residuals.max(initial=0.0)):.3g} mm"))

    # 5. Shared supply conservation at every timestep.
    supply_l = (sim.supply_factor_pct / 100.0) * 60.0
    per_step_alloc = {}
    for r in telemetry:
        per_step_alloc.setdefault(int(r["timestep"]), 0.0)
        per_step_alloc[int(r["timestep"])] += float(r["water_volume_allocated_L"])
    supply_ok = all(v <= supply_l + 1e-6 for v in per_step_alloc.values())
    checks.append(_check("supply_conservation", bool(supply_ok), f"max per-timestep allocation={max(per_step_alloc.values(), default=0.0):.4f} L <= supply cap={supply_l:.4f} L"))

    passed = all(c["status"] == "PASS" for c in checks)
    return {
        "status": "PASS" if passed else "FAIL",
        "verification_type": "deterministic component + 1-hour multizone integration smoke test",
        "checks": checks,
        "fuzzy_rule_counts": rule_counts,
        "fuzzy_variable_counts": variable_counts,
        "simulation": {"scenario": "Normal", "duration_hours": 1, "timestep_minutes": 1, "zones": zones, "telemetry_rows": n},
        "elapsed_seconds": round(perf_counter() - started, 3),
    }
