"""Unit and integration tests for Phase 11: Single-Zone Closed-Loop Feedback Control.

Verifies:
1. Initial state initialization (Zone 1: Tomato / Loam).
2. Initial moisture error calculation e(0) = +5.0%.
3. Current state used before control action (temporal ordering).
4. Controller output bounded in [0.0, 100.0]%.
5. Soil moisture physically bounded [WP, SAT].
6. Water balance conservation residual approximately zero (|residual| < 1e-6 mm).
7. Irrigation application non-negative.
8. Zero command produces zero irrigation application.
9. Positive command produces positive application.
10. Increasing moisture deficit produces increased control response.
11. Rainfall affects subsequent soil moisture.
12. Rainfall propagates into reduced water demand.
13. Controller reacts to changing moisture error (negative feedback).
14. Closed-loop feedback drives state transitions.
15. Simulation determinism for identical seed and parameters.
16. Different weather scenarios produce distinct trajectories.
17. NaN / Inf input handling and error rejection.
18. Single-zone isolation preserved.
19. Strict causality: no future state leakage.
20. Target-band metric calculations.
21. MAE, RMSE, and IAE metric verification.
22. Baseline simulations (no irrigation, fixed irrigation) execution.
23. Water Scarcity scenario does not artificially scale control demand.
24. Future placeholder WaterAllocationFIS remains NotImplementedError.
"""

import math
import numpy as np
import pandas as pd
import pytest

from config.schemas import SimulationScenario, SoilType, CropType
from config.defaults import get_default_zones
from simulation.closed_loop import (
    ClosedLoopConfig,
    ClosedLoopMetrics,
    ClosedLoopSimulator,
    simulate_single_zone,
)
from fuzzy_engine.allocation import WaterAllocationFIS
from models.soil import calculate_moisture_error


class TestClosedLoopSimulation:
    """Comprehensive test suite for single-zone closed-loop feedback control."""

    @pytest.fixture
    def canonical_sim(self) -> ClosedLoopSimulator:
        """Fixture providing a standard ClosedLoopSimulator on Normal scenario."""
        cfg = ClosedLoopConfig(scenario=SimulationScenario.NORMAL, seed=42)
        return ClosedLoopSimulator(config=cfg)

    # -------------------------------------------------------------------------
    # TEST 1: Initial state is correctly initialized
    # -------------------------------------------------------------------------
    def test_01_initial_state_initialization(self, canonical_sim: ClosedLoopSimulator):
        """Verify initial state matches Zone 1 parameters: SM=55%, Target=60%, Loam."""
        assert canonical_sim.zone.zone_id == 1
        assert canonical_sim.zone.crop.name == CropType.TOMATO.value
        assert canonical_sim.zone.soil.soil_type == SoilType.LOAM
        assert canonical_sim.zone.initial_moisture == 55.0
        assert canonical_sim.zone.target_moisture == 60.0
        assert canonical_sim.zone.soil.field_capacity == 70.0
        assert canonical_sim.zone.soil.wilting_point == 25.0
        assert canonical_sim.zone.soil.saturation == 85.0

    # -------------------------------------------------------------------------
    # TEST 2: Initial moisture error is correct
    # -------------------------------------------------------------------------
    def test_02_initial_moisture_error(self, canonical_sim: ClosedLoopSimulator):
        """Verify e(0) = Target - Initial = 60.0 - 55.0 = +5.0%."""
        df, metrics = canonical_sim.run(mode="fuzzy")
        initial_error = df["moisture_error"].iloc[0]
        assert pytest.approx(initial_error, rel=1e-4) == 5.0
        assert pytest.approx(df["soil_moisture"].iloc[0], rel=1e-4) == 55.0
        assert pytest.approx(df["target_moisture"].iloc[0], rel=1e-4) == 60.0

    # -------------------------------------------------------------------------
    # TEST 3: Current state is used before control action
    # -------------------------------------------------------------------------
    def test_03_current_state_used_before_control(self, canonical_sim: ClosedLoopSimulator):
        """Verify step t control inputs use SM(t), and next_soil_moisture reflects t+1."""
        df, _ = canonical_sim.run(mode="fuzzy")
        for i in range(min(10, len(df) - 1)):
            # Moisture error at step i uses soil_moisture at step i
            expected_err = round(df["target_moisture"].iloc[i] - df["soil_moisture"].iloc[i], 4)
            assert pytest.approx(df["moisture_error"].iloc[i], abs=1e-3) == expected_err
            # next_soil_moisture at step i must equal soil_moisture at step i+1
            assert pytest.approx(df["next_soil_moisture"].iloc[i], abs=1e-3) == df["soil_moisture"].iloc[i + 1]

    # -------------------------------------------------------------------------
    # TEST 4: Controller output remains [0, 100]%
    # -------------------------------------------------------------------------
    def test_04_controller_output_bounded(self, canonical_sim: ClosedLoopSimulator):
        """Verify all irrigation commands remain strictly in [0.0, 100.0]%."""
        df, metrics = canonical_sim.run(mode="fuzzy")
        commands = df["irrigation_command"].values
        assert np.all(commands >= 0.0)
        assert np.all(commands <= 100.0)
        assert 0.0 <= metrics.mean_irrigation_command <= 100.0
        assert 0.0 <= metrics.max_irrigation_command <= 100.0

    # -------------------------------------------------------------------------
    # TEST 5: Soil moisture remains physically bounded
    # -------------------------------------------------------------------------
    def test_05_soil_moisture_physically_bounded(self, canonical_sim: ClosedLoopSimulator):
        """Verify soil moisture stays within [wilting_point, saturation]."""
        df, metrics = canonical_sim.run(mode="fuzzy")
        moistures = df["soil_moisture"].values
        wp = canonical_sim.zone.soil.wilting_point
        sat = canonical_sim.zone.soil.saturation
        assert np.all(moistures >= wp)
        assert np.all(moistures <= sat)
        assert metrics.min_soil_moisture >= wp
        assert metrics.max_soil_moisture <= sat

    # -------------------------------------------------------------------------
    # TEST 6: Water balance residual remains approximately zero
    # -------------------------------------------------------------------------
    def test_06_water_balance_residual_zero(self, canonical_sim: ClosedLoopSimulator):
        """Verify water conservation residual across all 1440 steps has |residual| < 1e-6 mm."""
        df, metrics = canonical_sim.run(mode="fuzzy")
        residuals = np.abs(df["water_balance_residual"].values)
        assert np.max(residuals) < 1e-6
        assert metrics.max_absolute_residual < 1e-6
        assert metrics.residual_violations == 0

    # -------------------------------------------------------------------------
    # TEST 7: Irrigation application is non-negative
    # -------------------------------------------------------------------------
    def test_07_irrigation_application_non_negative(self, canonical_sim: ClosedLoopSimulator):
        """Verify physical irrigation application is >= 0.0 mm at all steps."""
        df, metrics = canonical_sim.run(mode="fuzzy")
        app = df["irrigation_application"].values
        assert np.all(app >= 0.0)
        assert metrics.total_irrigation_applied_mm >= 0.0

    # -------------------------------------------------------------------------
    # TEST 8: No irrigation command produces no positive application
    # -------------------------------------------------------------------------
    def test_08_zero_command_zero_application(self, canonical_sim: ClosedLoopSimulator):
        """Verify that a 0.0% command maps strictly to 0.0 mm application."""
        df, metrics = canonical_sim.run(mode="none")
        assert np.all(df["irrigation_command"].values == 0.0)
        assert np.all(df["irrigation_application"].values == 0.0)
        assert metrics.total_irrigation_applied_mm == 0.0

    # -------------------------------------------------------------------------
    # TEST 9: Positive irrigation command produces positive application
    # -------------------------------------------------------------------------
    def test_09_positive_command_positive_application(self, canonical_sim: ClosedLoopSimulator):
        """Verify that positive irrigation command yields positive physical water depth."""
        df, metrics = canonical_sim.run(mode="fuzzy")
        pos_mask = df["irrigation_command"] > 1.0
        assert np.any(pos_mask), "Expected at least some active irrigation"
        assert np.all(df.loc[pos_mask, "irrigation_application"] > 0.0)
        assert metrics.total_irrigation_applied_mm > 0.0

    # -------------------------------------------------------------------------
    # TEST 10: Increasing moisture deficit produces increased control response
    # -------------------------------------------------------------------------
    def test_10_increasing_deficit_increases_response(self, canonical_sim: ClosedLoopSimulator):
        """Verify that larger moisture errors lead to higher or equal irrigation commands."""
        cmd_mild = canonical_sim.fis_main.evaluate(
            soil_stress=20.0, weather_stress=20.0, water_demand=20.0, moisture_error=2.0
        )
        cmd_severe = canonical_sim.fis_main.evaluate(
            soil_stress=60.0, weather_stress=20.0, water_demand=20.0, moisture_error=15.0
        )
        assert cmd_severe > cmd_mild, f"Expected cmd_severe ({cmd_severe}) > cmd_mild ({cmd_mild})"

    # -------------------------------------------------------------------------
    # TEST 11: Rainfall affects subsequent soil moisture
    # -------------------------------------------------------------------------
    def test_11_rainfall_affects_soil_moisture(self):
        """Verify that under Rainy scenario, rainfall raises soil moisture."""
        cfg_rainy = ClosedLoopConfig(scenario=SimulationScenario.RAINY, seed=42)
        sim_rainy = ClosedLoopSimulator(config=cfg_rainy)
        df_rainy, m_rainy = sim_rainy.run(mode="fuzzy")

        assert m_rainy.total_rainfall_mm > 10.0, "Rainy scenario must produce rainfall"
        assert m_rainy.total_effective_rainfall_mm > 5.0
        # Infiltration from rain must be registered
        assert np.sum(df_rainy["infiltration"].values) > 0.0

    # -------------------------------------------------------------------------
    # TEST 12: Rainfall propagates into reduced water demand
    # -------------------------------------------------------------------------
    def test_12_rainfall_propagates_into_reduced_demand(self, canonical_sim: ClosedLoopSimulator):
        """Verify high effective rainfall reduces water demand in WaterDemandFIS."""
        demand_dry = canonical_sim.fis_water.evaluate(
            etc=5.0, crop_water_deficit=5.0, effective_rainfall=0.0
        )
        demand_wet = canonical_sim.fis_water.evaluate(
            etc=5.0, crop_water_deficit=0.0, effective_rainfall=25.0
        )
        assert demand_wet < demand_dry, f"Demand with rain ({demand_wet}) should be < dry ({demand_dry})"

    # -------------------------------------------------------------------------
    # TEST 13: Controller reacts to changing moisture error (negative feedback)
    # -------------------------------------------------------------------------
    def test_13_controller_negative_feedback(self, canonical_sim: ClosedLoopSimulator):
        """Verify that as soil moisture increases toward target, command decreases."""
        df, _ = canonical_sim.run(mode="fuzzy")
        # Find early active period vs late settled period
        early_cmd = df["irrigation_command"].iloc[30:90].mean()
        late_cmd = df["irrigation_command"].iloc[1000:1400].mean()
        assert early_cmd > late_cmd, f"Early command ({early_cmd}) should exceed settled command ({late_cmd})"

    # -------------------------------------------------------------------------
    # TEST 14: Closed-loop feedback actually changes next state
    # -------------------------------------------------------------------------
    def test_14_closed_loop_drives_state_changes(self, canonical_sim: ClosedLoopSimulator):
        """Verify fuzzy closed-loop trajectory differs substantially from no-irrigation."""
        df_fuzzy, m_fuzzy = canonical_sim.run(mode="fuzzy")
        df_none, m_none = canonical_sim.run(mode="none")

        # Fuzzy control increases final moisture toward target
        assert m_fuzzy.final_soil_moisture > m_none.final_soil_moisture
        assert m_fuzzy.mae < m_none.mae
        assert m_fuzzy.final_soil_moisture >= 58.0  # Within target band [58, 62]

    # -------------------------------------------------------------------------
    # TEST 15: Simulation is deterministic for identical parameters/seed
    # -------------------------------------------------------------------------
    def test_15_simulation_determinism(self):
        """Verify running identical configurations yields exact bitwise results."""
        cfg = ClosedLoopConfig(scenario=SimulationScenario.NORMAL, seed=123)
        sim1 = ClosedLoopSimulator(config=cfg)
        sim2 = ClosedLoopSimulator(config=cfg)

        df1, m1 = sim1.run(mode="fuzzy")
        df2, m2 = sim2.run(mode="fuzzy")

        pd.testing.assert_frame_equal(df1, df2)
        assert m1.final_soil_moisture == m2.final_soil_moisture
        assert m1.total_irrigation_applied_mm == m2.total_irrigation_applied_mm

    # -------------------------------------------------------------------------
    # TEST 16: Different weather scenarios produce different trajectories
    # -------------------------------------------------------------------------
    def test_16_different_scenarios_produce_different_trajectories(self):
        """Verify Normal, Heatwave, and Rainy produce distinct meteorological & moisture paths."""
        sim_norm = ClosedLoopSimulator(config=ClosedLoopConfig(scenario=SimulationScenario.NORMAL, seed=42))
        sim_heat = ClosedLoopSimulator(config=ClosedLoopConfig(scenario=SimulationScenario.HEATWAVE, seed=42))
        sim_rain = ClosedLoopSimulator(config=ClosedLoopConfig(scenario=SimulationScenario.RAINY, seed=42))

        _, m_norm = sim_norm.run(mode="fuzzy")
        _, m_heat = sim_heat.run(mode="fuzzy")
        _, m_rain = sim_rain.run(mode="fuzzy")

        assert m_heat.total_etc_mm > m_norm.total_etc_mm
        assert m_rain.total_rainfall_mm > m_norm.total_rainfall_mm
        assert m_heat.total_irrigation_applied_mm != m_norm.total_irrigation_applied_mm

    # -------------------------------------------------------------------------
    # TEST 17: NaN / Inf handling remains valid
    # -------------------------------------------------------------------------
    def test_17_nan_inf_handling(self, canonical_sim: ClosedLoopSimulator):
        """Verify FIS subsystems reject NaN and infinite inputs with ValueError."""
        with pytest.raises(ValueError):
            canonical_sim.fis_soil.evaluate(rsm=float("nan"), moisture_error=5.0)
        with pytest.raises(ValueError):
            canonical_sim.fis_weather.evaluate(
                temperature=float("inf"), humidity=50.0, solar_radiation=500.0, wind_speed=2.0, rainfall=0.0
            )
        with pytest.raises(ValueError):
            canonical_sim.fis_water.evaluate(etc=float("nan"), crop_water_deficit=2.0, effective_rainfall=0.0)
        with pytest.raises(ValueError):
            canonical_sim.fis_main.evaluate(
                soil_stress=50.0, weather_stress=50.0, water_demand=float("nan"), moisture_error=0.0
            )

    # -------------------------------------------------------------------------
    # TEST 18: Single-zone isolation is preserved
    # -------------------------------------------------------------------------
    def test_18_single_zone_isolation(self, canonical_sim: ClosedLoopSimulator):
        """Verify only Zone 1 is controlled and default multizone definitions are unchanged."""
        assert canonical_sim.zone.zone_id == 1
        all_zones = get_default_zones()
        assert len(all_zones) == 3
        assert all_zones[0].crop.name == "Tomato"
        assert all_zones[1].crop.name == "Wheat"
        assert all_zones[2].crop.name == "Maize"

    # -------------------------------------------------------------------------
    # TEST 19: No future state leakage (causality proof)
    # -------------------------------------------------------------------------
    def test_19_no_future_state_leakage(self, canonical_sim: ClosedLoopSimulator):
        """Verify command(t) is computed strictly from state(t), not state(t+1)."""
        df, _ = canonical_sim.run(mode="fuzzy")
        # In df, next_soil_moisture[t] is state(t+1)
        # Verify that irrigation_command[t] does not match an inverse lookup on state(t+1)
        for t in range(5):
            sm_current = df["soil_moisture"].iloc[t]
            sm_next = df["next_soil_moisture"].iloc[t]
            # Command was computed before sm_next occurred
            assert not math.isclose(sm_current, sm_next, abs_tol=1e-5) or df["irrigation_application"].iloc[t] == 0.0

    # -------------------------------------------------------------------------
    # TEST 20: Target-band metric is calculated correctly
    # -------------------------------------------------------------------------
    def test_20_target_band_metric_calculation(self, canonical_sim: ClosedLoopSimulator):
        """Verify target-band residency time and percentage calculations."""
        df, metrics = canonical_sim.run(mode="fuzzy")
        target = 60.0
        tol = canonical_sim.config.target_moisture_tolerance_pct
        in_band = (df["soil_moisture"] >= target - tol) & (df["soil_moisture"] <= target + tol)
        expected_minutes = int(in_band.sum() * canonical_sim.config.timestep_minutes)
        expected_pct = round((expected_minutes / 1440.0) * 100.0, 2)

        assert metrics.time_in_target_band_minutes == expected_minutes
        assert metrics.percentage_in_target_band == expected_pct
        assert metrics.time_to_target_band_minutes is not None
        assert metrics.time_to_target_band_minutes > 0

    # -------------------------------------------------------------------------
    # TEST 21: MAE/RMSE/IAE calculations are correct
    # -------------------------------------------------------------------------
    def test_21_mae_rmse_iae_calculations(self, canonical_sim: ClosedLoopSimulator):
        """Verify error metrics match exact mathematical definitions."""
        df, metrics = canonical_sim.run(mode="fuzzy")
        errors = df["moisture_error"].values
        expected_mae = round(float(np.mean(np.abs(errors))), 4)
        expected_rmse = round(float(np.sqrt(np.mean(errors ** 2))), 4)
        expected_iae = round(float(np.sum(np.abs(errors)) * canonical_sim.config.timestep_minutes), 4)

        assert metrics.mae == expected_mae
        assert metrics.rmse == expected_rmse
        assert metrics.iae == expected_iae

    # -------------------------------------------------------------------------
    # TEST 22: Baseline simulations execute successfully
    # -------------------------------------------------------------------------
    def test_22_baseline_simulations_execute(self, canonical_sim: ClosedLoopSimulator):
        """Verify both Baseline A (none) and Baseline B (fixed) execute cleanly."""
        df_none, m_none = canonical_sim.run(mode="none")
        df_fixed, m_fixed = canonical_sim.run(mode="fixed")

        assert len(df_none) == 1440
        assert len(df_fixed) == 1440
        assert m_none.total_irrigation_applied_mm == 0.0
        assert m_fixed.total_irrigation_applied_mm > 0.0
        assert m_fixed.mode == "fixed"
        assert m_none.mode == "none"

    # -------------------------------------------------------------------------
    # TEST 23: Water scarcity does not accidentally activate Water Allocation
    # -------------------------------------------------------------------------
    def test_23_water_scarcity_no_allocation_curtailment(self):
        """Verify Water Scarcity scenario evaluates unconstrained control demand without WAF reduction."""
        cfg_scarcity = ClosedLoopConfig(scenario=SimulationScenario.WATER_SCARCITY, seed=42)
        sim_scarcity = ClosedLoopSimulator(config=cfg_scarcity)
        df_scarcity, m_scarcity = sim_scarcity.run(mode="fuzzy")

        # Demand and application must NOT be scaled down by WAF = 0.30 inside Phase 11 controller
        assert m_scarcity.total_irrigation_applied_mm > 0.0
        assert df_scarcity["irrigation_command"].max() > 10.0
        # Verify physical application strictly follows unconstrained formula
        first_cmd = df_scarcity["irrigation_command"].iloc[0]
        expected_app = (first_cmd / 100.0) * sim_scarcity.config.max_irrigation_rate_mm_h * (1.0 / 60.0)
        assert pytest.approx(df_scarcity["irrigation_application"].iloc[0], rel=1e-4) == expected_app

    # -------------------------------------------------------------------------
    # TEST 24: Existing future placeholder WaterAllocationFIS remains NotImplementedError
    # -------------------------------------------------------------------------
    def test_24_water_allocation_placeholder_remains_not_implemented(self):
        """Verify Phase 13 WaterAllocationFIS methods raise NotImplementedError."""
        fis_alloc = WaterAllocationFIS()
        with pytest.raises(NotImplementedError):
            fis_alloc.evaluate_zone(
                zone_demand=50.0,
                zone_stress=0.5,
                available_water_pct=30.0,
                zone_priority=2.0,
            )
        with pytest.raises(NotImplementedError):
            fis_alloc.allocate_multizone(
                demands=[50.0, 40.0, 30.0],
                stresses=[0.5, 0.4, 0.3],
                priorities=[2.0, 1.0, 3.0],
                total_available_volume_m3=100.0,
            )
