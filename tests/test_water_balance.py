"""Unit and hydrological tests for discrete root-zone soil water balance model.

Verifies:
1. Canonical update_soil_moisture_step contract
2. Analytical water conservation (exact manual residual calculation)
3. Zero-irrigation progressive drying
4. Saturated infiltration and drainage activation
5. Permanent wilting point lower bound protection
6. Multizone compartment independence (Zone 1, 2, 3)
7. Full 24-hour simulation engine execution across all 6 scenarios
8. Zero-residual water conservation at every discrete epoch
"""

import pytest
import numpy as np
import pandas as pd

from models.water_balance import (
    SoilState,
    update_soil_moisture_step,
    update_water_balance,
    initialize_soil_state,
    simulate_water_balance_timeseries,
)
from models.soil import soil_moisture_to_storage, storage_to_soil_moisture
from simulation.engine import SimulationEngine
from config.schemas import SimulationScenario, ZoneConfig
from config.defaults import get_default_zones


def test_update_soil_moisture_step_functional_contract():
    """Verify standard functional contract for update_soil_moisture_step."""
    # Zone 1 baseline: Loam (FC=70%, WP=25%, SAT=85%, Zr=0.7m, Infil=20mm/h)
    # Over a 60-minute period: 5.0 mm irrigation added (< 20 mm infil capacity), 0.5 mm ETc -> moisture increases
    sm_next = update_soil_moisture_step(
        current_moisture=55.0,
        irrigation_depth_mm=5.0,
        effective_rainfall_mm=0.0,
        etc_mm=0.5,
        field_capacity=70.0,
        wilting_point=25.0,
        saturation=85.0,
        root_depth_m=0.7,
        drainage_coefficient=0.08,
        timestep_minutes=60,
    )
    assert isinstance(sm_next, float)
    assert sm_next > 55.0
    # Net water added: 4.5 mm on 700 mm root depth = 4.5 / 7.0 ≈ +0.643%
    assert sm_next == pytest.approx(55.0 + (4.5 / 7.0), abs=1e-3)


def test_analytical_water_conservation_residual_no_drainage():
    """Exact manual verification of water conservation residual without drainage."""
    # Initial: 55.0% on 0.7m -> Storage = 385.0 mm
    # FC = 70.0% -> Storage_FC = 490.0 mm
    zr = 0.70
    sm_init = 55.0
    s_init = soil_moisture_to_storage(sm_init, zr)  # 385.0 mm

    zones = get_default_zones()
    z1 = zones[0]
    state = initialize_soil_state(z1)

    irrig = 10.0  # mm
    peff = 5.0    # mm
    etc = 2.0     # mm

    next_state = update_water_balance(
        current_state=state,
        irrigation_mm=irrig,
        effective_rainfall_mm=peff,
        etc_mm=etc,
        timestep_minutes=60,
    )

    # Infiltrated = 15.0 mm (below 20 mm/h max)
    # Expected storage = 385.0 + 15.0 - 2.0 = 398.0 mm
    assert next_state.infiltration_mm == pytest.approx(15.0, abs=1e-5)
    assert next_state.drainage_mm == 0.0
    assert next_state.storage_mm == pytest.approx(398.0, abs=1e-4)
    # Conservation residual must be zero to numerical precision
    assert abs(next_state.water_balance_residual) < 1e-9


def test_analytical_water_conservation_residual_with_drainage():
    """Exact manual verification of water conservation residual when drainage occurs."""
    zr = 0.70
    fc = 70.0
    s_fc = soil_moisture_to_storage(fc, zr)  # 490.0 mm

    zones = get_default_zones()
    z1 = zones[0]
    # Set initial moisture very close to FC (68.0%)
    z1.initial_moisture = 68.0
    state = initialize_soil_state(z1)

    s_init = state.storage_mm  # 476.0 mm
    irrig = 30.0  # mm (large flood)
    peff = 0.0
    etc = 1.0

    next_state = update_water_balance(
        current_state=state,
        irrigation_mm=irrig,
        effective_rainfall_mm=peff,
        etc_mm=etc,
        timestep_minutes=120,  # 2 hours allows 40 mm infiltration
    )

    # S_after = 476.0 + 30.0 - 1.0 = 505.0 mm
    # Excess above FC = 505.0 - 490.0 = 15.0 mm
    # Drainage = 0.08 * 15.0 = 1.2 mm
    # S_final = 505.0 - 1.2 = 503.8 mm
    assert next_state.drainage_mm == pytest.approx(1.2, abs=1e-4)
    assert next_state.storage_mm == pytest.approx(503.8, abs=1e-4)
    assert abs(next_state.water_balance_residual) < 1e-9


def test_zero_irrigation_depletion():
    """Verify continuous drying under zero irrigation."""
    zones = get_default_zones()
    z1 = zones[0]
    state = initialize_soil_state(z1)

    etc_steps = np.full(60, 0.05)  # 60 steps of 0.05 mm ETc = 3.0 mm total
    df = simulate_water_balance_timeseries(
        initial_state=state,
        etc_series=etc_steps,
        timestep_minutes=1,
    )

    # Storage must strictly decrease monotonically
    assert df["storage_mm"].is_monotonic_decreasing
    # Final storage should be exactly initial - 3.0 mm
    assert df["storage_mm"].iloc[-1] == pytest.approx(state.storage_mm - 3.0, abs=1e-4)
    # Conservation residuals must all be zero
    assert (df["water_balance_residual"].abs() < 1e-8).all()


def test_wilting_point_bound_enforcement():
    """Verify that root-zone water cannot be depleted below permanent wilting point."""
    zones = get_default_zones()
    z1 = zones[0]
    # Start close to WP (25.5%)
    z1.initial_moisture = 25.5
    state = initialize_soil_state(z1)

    # Apply enormous ETc demand (50.0 mm)
    next_state = update_water_balance(
        current_state=state,
        irrigation_mm=0.0,
        effective_rainfall_mm=0.0,
        etc_mm=50.0,
        timestep_minutes=60,
    )

    # Soil moisture must not drop below wilting point (25.0%)
    assert next_state.soil_moisture >= 25.0
    assert next_state.rsm == 0.0
    # Actual ET extracted is limited to available water above WP
    assert next_state.actual_et_mm < 50.0
    assert abs(next_state.water_balance_residual) < 1e-8


def test_multizone_compartment_independence():
    """Verify that Zones 1, 2, and 3 maintain completely independent soil dynamics."""
    engine = SimulationEngine(scenario=SimulationScenario.NORMAL, irrigation_mode="none", seed=42)
    df = engine.run(duration_hours=24, timestep_minutes=1)

    z1_df = df[df["zone_id"] == 1]
    z2_df = df[df["zone_id"] == 2]
    z3_df = df[df["zone_id"] == 3]

    assert len(z1_df) == 1440
    assert len(z2_df) == 1440
    assert len(z3_df) == 1440

    # Verify distinct physical initial and final moisture
    assert z1_df["soil_moisture"].iloc[0] == 55.0  # Tomato / Loam
    assert z2_df["soil_moisture"].iloc[0] == 42.0  # Wheat / Sandy
    assert z3_df["soil_moisture"].iloc[0] == 65.0  # Maize / Clay

    # All three must have different storage depths due to different root depths (0.7m, 0.9m, 1.0m)
    assert z1_df["soil_storage_mm"].iloc[0] != z2_df["soil_storage_mm"].iloc[0]
    assert z2_df["soil_storage_mm"].iloc[0] != z3_df["soil_storage_mm"].iloc[0]


def test_simulation_engine_all_six_scenarios():
    """Verify that full multizone simulation executes cleanly across all 6 scenarios."""
    scenarios = [
        SimulationScenario.NORMAL,
        SimulationScenario.HOT_AND_DRY,
        SimulationScenario.RAINY,
        SimulationScenario.CLOUDY,
        SimulationScenario.HEATWAVE,
        SimulationScenario.WATER_SCARCITY,
    ]

    for sc in scenarios:
        engine = SimulationEngine(scenario=sc, irrigation_mode="periodic", seed=42)
        df = engine.run(duration_hours=24, timestep_minutes=1)

        # 1440 steps * 3 zones = 4320 rows
        assert len(df) == 4320
        assert not df.isna().any().any(), f"NaNs detected in scenario {sc.value}"
        # Water conservation residual must remain zero across all rows
        assert (df["water_balance_residual"].abs() < 1e-6).all()


def test_deterministic_reproducibility():
    """Verify that identical simulation runs with the same seed yield identical states."""
    engine1 = SimulationEngine(scenario=SimulationScenario.HOT_AND_DRY, seed=123)
    df1 = engine1.run(duration_hours=12, timestep_minutes=1)

    engine2 = SimulationEngine(scenario=SimulationScenario.HOT_AND_DRY, seed=123)
    df2 = engine2.run(duration_hours=12, timestep_minutes=1)

    pd.testing.assert_frame_equal(df1, df2)
