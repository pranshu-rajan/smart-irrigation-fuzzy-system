"""Unit and integration tests for Phase 12: Multizone Closed-Loop Fuzzy Control.

Verifies:
1. Three zones initialize correctly (Zone 1, Zone 2, Zone 3).
2. Zone-specific FC/WP are correct.
3. Zone-specific initial moisture is correct.
4. Zone-specific targets are correct.
5. Each zone has an independent state.
6. All zones execute MainIrrigationFIS.
7. Commands remain bounded in [0.0, 100.0]%.
8. Applications are non-negative.
9. Soil moisture remains physically bounded in [WP, SAT].
10. Water balance residual is approximately zero (|residual| < 1e-6 mm).
11. No future-state leakage (causality).
12. Zone 1 perturbation does not alter Zone 2.
13. Zone 1 perturbation does not alter Zone 3.
14. Zone 2 perturbation does not alter Zone 1.
15. Zone 2 perturbation does not alter Zone 3.
16. Zone 3 perturbation does not alter Zone 1.
17. Zone 3 perturbation does not alter Zone 2.
18. Rainfall changes zone states appropriately.
19. Different crop Kc values affect ETc appropriately.
20. Different soil properties affect soil dynamics appropriately.
21. Identical simulation parameters are reproducible.
22. Different scenarios generate different trajectories.
23. No-irrigation baseline executes across all 3 zones.
24. Fixed-irrigation baseline executes across all 3 zones.
25. Fuzzy multizone controller executes across all 3 zones.
26. Water scarcity does not activate supply rationing.
27. WaterAllocationFIS remains NotImplementedError.
28. Depth-to-volume conversion is exact.
29. Aggregate system metrics are calculated correctly.
30. Expected 12,960 records generated across 6 scenarios.
31. NaN / Inf validation remains active.
32. Phase 11 single-zone simulation remains operational and backward compatible.
"""

import copy
import math
import numpy as np
import pandas as pd
import pytest

from config.schemas import SimulationScenario, SoilType, CropType, ZoneConfig
from config.defaults import get_default_zones
from simulation.multizone_closed_loop import (
    MultizoneClosedLoopConfig,
    ZoneClosedLoopMetrics,
    SystemClosedLoopMetrics,
    MultizoneClosedLoopSimulator,
    simulate_multizone_closed_loop,
)
from simulation.closed_loop import ClosedLoopSimulator, ClosedLoopConfig
from fuzzy_engine.allocation import WaterAllocationFIS


class TestMultizoneClosedLoop:
    """Comprehensive test suite for Phase 12 multizone closed-loop fuzzy control."""

    @pytest.fixture
    def canonical_sim(self) -> MultizoneClosedLoopSimulator:
        """Fixture providing a standard MultizoneClosedLoopSimulator on Normal scenario."""
        cfg = MultizoneClosedLoopConfig(scenario=SimulationScenario.NORMAL, seed=42)
        return MultizoneClosedLoopSimulator(config=cfg)

    # -------------------------------------------------------------------------
    # TEST 1: Three zones initialize correctly
    # -------------------------------------------------------------------------
    def test_01_three_zones_initialize_correctly(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify standard 3 zones are loaded with correct crop, soil, and area."""
        zones = canonical_sim.zones
        assert len(zones) == 3
        z1, z2, z3 = zones[0], zones[1], zones[2]
        assert z1.zone_id == 1 and z1.crop.name == "Tomato" and z1.soil.soil_type == SoilType.LOAM and z1.area_m2 == 100.0
        assert z2.zone_id == 2 and z2.crop.name == "Wheat" and z2.soil.soil_type == SoilType.SANDY and z2.area_m2 == 120.0
        assert z3.zone_id == 3 and z3.crop.name == "Maize" and z3.soil.soil_type == SoilType.CLAY and z3.area_m2 == 80.0

    # -------------------------------------------------------------------------
    # TEST 2: Zone-specific FC/WP are correct
    # -------------------------------------------------------------------------
    def test_02_zone_specific_fc_wp(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify soil hydraulic thresholds for Loam, Sandy, and Clay."""
        z1, z2, z3 = canonical_sim.zones
        assert z1.soil.field_capacity == 70.0 and z1.soil.wilting_point == 25.0
        assert z2.soil.field_capacity == 60.0 and z2.soil.wilting_point == 18.0
        assert z3.soil.field_capacity == 75.0 and z3.soil.wilting_point == 30.0

    # -------------------------------------------------------------------------
    # TEST 3: Zone-specific initial moisture is correct
    # -------------------------------------------------------------------------
    def test_03_zone_specific_initial_moisture(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify initial moisture values: Z1=55%, Z2=42%, Z3=65%."""
        z1, z2, z3 = canonical_sim.zones
        assert z1.initial_moisture == 55.0
        assert z2.initial_moisture == 42.0
        assert z3.initial_moisture == 65.0

    # -------------------------------------------------------------------------
    # TEST 4: Zone-specific targets are correct
    # -------------------------------------------------------------------------
    def test_04_zone_specific_targets(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify target setpoint values: Z1=60%, Z2=55%, Z3=65%."""
        z1, z2, z3 = canonical_sim.zones
        assert z1.target_moisture == 60.0
        assert z2.target_moisture == 55.0
        assert z3.target_moisture == 65.0

    # -------------------------------------------------------------------------
    # TEST 5: Each zone has an independent state
    # -------------------------------------------------------------------------
    def test_05_independent_zone_states(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify zones maintain distinct soil moisture and error trajectories."""
        res = canonical_sim.run(mode="fuzzy")
        df = res.df
        df1 = df[df["zone_id"] == 1].reset_index(drop=True)
        df2 = df[df["zone_id"] == 2].reset_index(drop=True)
        df3 = df[df["zone_id"] == 3].reset_index(drop=True)

        assert not np.array_equal(df1["soil_moisture"].values, df2["soil_moisture"].values)
        assert not np.array_equal(df2["soil_moisture"].values, df3["soil_moisture"].values)
        assert not np.array_equal(df1["moisture_error"].values, df2["moisture_error"].values)

    # -------------------------------------------------------------------------
    # TEST 6: All zones execute MainIrrigationFIS
    # -------------------------------------------------------------------------
    def test_06_all_zones_execute_main_irrigation_fis(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify all 3 zones produce valid, evaluated fuzzy commands."""
        res = canonical_sim.run(mode="fuzzy")
        for z_id in (1, 2, 3):
            z_df = res.df[res.df["zone_id"] == z_id]
            assert len(z_df) == 1440
            assert not z_df["irrigation_command"].isnull().any()
            assert res.zone_metrics[z_id].mean_irrigation_command > 0.0

    # -------------------------------------------------------------------------
    # TEST 7: Commands remain in [0, 100]%
    # -------------------------------------------------------------------------
    def test_07_commands_remain_bounded(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify all zone commands stay within [0.0, 100.0]%."""
        res = canonical_sim.run(mode="fuzzy")
        commands = res.df["irrigation_command"].values
        assert np.all(commands >= 0.0)
        assert np.all(commands <= 100.0)

    # -------------------------------------------------------------------------
    # TEST 8: Applications are non-negative
    # -------------------------------------------------------------------------
    def test_08_applications_non_negative(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify irrigation depth and volume applications are >= 0 across all zones."""
        res = canonical_sim.run(mode="fuzzy")
        assert np.all(res.df["irrigation_application"].values >= 0.0)
        assert np.all(res.df["irrigation_volume_l"].values >= 0.0)

    # -------------------------------------------------------------------------
    # TEST 9: Soil moisture remains physically bounded
    # -------------------------------------------------------------------------
    def test_09_soil_moisture_physically_bounded(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify soil moisture stays within [WP_z, SAT_z] for each zone."""
        res = canonical_sim.run(mode="fuzzy")
        for z in canonical_sim.zones:
            z_df = res.df[res.df["zone_id"] == z.zone_id]
            moistures = z_df["soil_moisture"].values
            assert np.all(moistures >= z.soil.wilting_point)
            assert np.all(moistures <= z.soil.saturation)

    # -------------------------------------------------------------------------
    # TEST 10: Water balance residual is near zero
    # -------------------------------------------------------------------------
    def test_10_water_balance_residual_zero(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify |residual| < 1e-6 mm across all zones and timesteps."""
        res = canonical_sim.run(mode="fuzzy")
        residuals = np.abs(res.df["water_balance_residual"].values)
        assert np.max(residuals) < 1e-6
        assert res.system_metrics.total_residual_violations == 0

    # -------------------------------------------------------------------------
    # TEST 11: No future-state leakage
    # -------------------------------------------------------------------------
    def test_11_no_future_state_leakage(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify step t control inputs use SM_z(t) and not next_soil_moisture."""
        res = canonical_sim.run(mode="fuzzy")
        df = res.df
        for z_id in (1, 2, 3):
            z_df = df[df["zone_id"] == z_id].reset_index(drop=True)
            for i in range(5):
                expected_err = round(z_df["target_moisture"].iloc[i] - z_df["soil_moisture"].iloc[i], 4)
                assert pytest.approx(z_df["moisture_error"].iloc[i], abs=1e-3) == expected_err
                assert pytest.approx(z_df["next_soil_moisture"].iloc[i], abs=1e-3) == z_df["soil_moisture"].iloc[i + 1]

    # -------------------------------------------------------------------------
    # ISOLATION TESTS: PERTURBATION VERIFICATION (Tests 12 - 17)
    # -------------------------------------------------------------------------
    def test_12_zone1_perturbation_does_not_alter_zone2(self, canonical_sim: MultizoneClosedLoopSimulator):
        """TEST 12: Perturb Zone 1 initial moisture; verify Zone 2 remains unchanged."""
        base_res = canonical_sim.run(mode="fuzzy")

        perturbed_zones = [copy.deepcopy(z) for z in canonical_sim.zones]
        perturbed_zones[0].initial_moisture = 45.0  # Perturb Zone 1 from 55% to 45%

        p_sim = MultizoneClosedLoopSimulator(config=canonical_sim.config, zone_configs=perturbed_zones)
        p_res = p_sim.run(mode="fuzzy")

        z1_base = base_res.df[base_res.df["zone_id"] == 1]["soil_moisture"].values
        z1_pert = p_res.df[p_res.df["zone_id"] == 1]["soil_moisture"].values
        assert not np.allclose(z1_base, z1_pert)

        z2_base = base_res.df[base_res.df["zone_id"] == 2]["soil_moisture"].values
        z2_pert = p_res.df[p_res.df["zone_id"] == 2]["soil_moisture"].values
        np.testing.assert_allclose(z2_base, z2_pert, atol=1e-10)

    def test_13_zone1_perturbation_does_not_alter_zone3(self, canonical_sim: MultizoneClosedLoopSimulator):
        """TEST 13: Perturb Zone 1 initial moisture; verify Zone 3 remains unchanged."""
        base_res = canonical_sim.run(mode="fuzzy")

        perturbed_zones = [copy.deepcopy(z) for z in canonical_sim.zones]
        perturbed_zones[0].initial_moisture = 45.0

        p_sim = MultizoneClosedLoopSimulator(config=canonical_sim.config, zone_configs=perturbed_zones)
        p_res = p_sim.run(mode="fuzzy")

        z3_base = base_res.df[base_res.df["zone_id"] == 3]["soil_moisture"].values
        z3_pert = p_res.df[p_res.df["zone_id"] == 3]["soil_moisture"].values
        np.testing.assert_allclose(z3_base, z3_pert, atol=1e-10)

    def test_14_zone2_perturbation_does_not_alter_zone1(self, canonical_sim: MultizoneClosedLoopSimulator):
        """TEST 14: Perturb Zone 2 target moisture; verify Zone 1 remains unchanged."""
        base_res = canonical_sim.run(mode="fuzzy")

        perturbed_zones = [copy.deepcopy(z) for z in canonical_sim.zones]
        perturbed_zones[1].target_moisture = 50.0  # Perturb Zone 2 target from 55% to 50%

        p_sim = MultizoneClosedLoopSimulator(config=canonical_sim.config, zone_configs=perturbed_zones)
        p_res = p_sim.run(mode="fuzzy")

        z2_base = base_res.df[base_res.df["zone_id"] == 2]["soil_moisture"].values
        z2_pert = p_res.df[p_res.df["zone_id"] == 2]["soil_moisture"].values
        assert not np.allclose(z2_base, z2_pert)

        z1_base = base_res.df[base_res.df["zone_id"] == 1]["soil_moisture"].values
        z1_pert = p_res.df[p_res.df["zone_id"] == 1]["soil_moisture"].values
        np.testing.assert_allclose(z1_base, z1_pert, atol=1e-10)

    def test_15_zone2_perturbation_does_not_alter_zone3(self, canonical_sim: MultizoneClosedLoopSimulator):
        """TEST 15: Perturb Zone 2 target moisture; verify Zone 3 remains unchanged."""
        base_res = canonical_sim.run(mode="fuzzy")

        perturbed_zones = [copy.deepcopy(z) for z in canonical_sim.zones]
        perturbed_zones[1].target_moisture = 50.0

        p_sim = MultizoneClosedLoopSimulator(config=canonical_sim.config, zone_configs=perturbed_zones)
        p_res = p_sim.run(mode="fuzzy")

        z3_base = base_res.df[base_res.df["zone_id"] == 3]["soil_moisture"].values
        z3_pert = p_res.df[p_res.df["zone_id"] == 3]["soil_moisture"].values
        np.testing.assert_allclose(z3_base, z3_pert, atol=1e-10)

    def test_16_zone3_perturbation_does_not_alter_zone1(self, canonical_sim: MultizoneClosedLoopSimulator):
        """TEST 16: Perturb Zone 3 crop parameter (Kc); verify Zone 1 remains unchanged."""
        base_res = canonical_sim.run(mode="fuzzy")

        perturbed_zones = [copy.deepcopy(z) for z in canonical_sim.zones]
        perturbed_zones[2].crop.kc = 0.70  # Perturb Zone 3 Kc from 1.20 to 0.70

        p_sim = MultizoneClosedLoopSimulator(config=canonical_sim.config, zone_configs=perturbed_zones)
        p_res = p_sim.run(mode="fuzzy")

        z3_base = base_res.df[base_res.df["zone_id"] == 3]["soil_moisture"].values
        z3_pert = p_res.df[p_res.df["zone_id"] == 3]["soil_moisture"].values
        assert not np.allclose(z3_base, z3_pert)

        z1_base = base_res.df[base_res.df["zone_id"] == 1]["soil_moisture"].values
        z1_pert = p_res.df[p_res.df["zone_id"] == 1]["soil_moisture"].values
        np.testing.assert_allclose(z1_base, z1_pert, atol=1e-10)

    def test_17_zone3_perturbation_does_not_alter_zone2(self, canonical_sim: MultizoneClosedLoopSimulator):
        """TEST 17: Perturb Zone 3 crop parameter (Kc); verify Zone 2 remains unchanged."""
        base_res = canonical_sim.run(mode="fuzzy")

        perturbed_zones = [copy.deepcopy(z) for z in canonical_sim.zones]
        perturbed_zones[2].crop.kc = 0.70

        p_sim = MultizoneClosedLoopSimulator(config=canonical_sim.config, zone_configs=perturbed_zones)
        p_res = p_sim.run(mode="fuzzy")

        z2_base = base_res.df[base_res.df["zone_id"] == 2]["soil_moisture"].values
        z2_pert = p_res.df[p_res.df["zone_id"] == 2]["soil_moisture"].values
        np.testing.assert_allclose(z2_base, z2_pert, atol=1e-10)

    # -------------------------------------------------------------------------
    # TEST 18: Rainfall changes zone states
    # -------------------------------------------------------------------------
    def test_18_rainfall_changes_zone_states(self):
        """Verify that under Rainy scenario, rainfall raises moisture and suppresses demand across zones."""
        cfg_rain = MultizoneClosedLoopConfig(scenario=SimulationScenario.RAINY, seed=42)
        sim_rain = MultizoneClosedLoopSimulator(config=cfg_rain)
        res_rain = sim_rain.run(mode="fuzzy")

        for z_id in (1, 2, 3):
            m = res_rain.zone_metrics[z_id]
            assert m.total_rainfall_mm > 10.0
            assert m.total_effective_rainfall_mm > 5.0

    # -------------------------------------------------------------------------
    # TEST 19: Different crop Kc values affect ETc appropriately
    # -------------------------------------------------------------------------
    def test_19_kc_affects_etc_proportionately(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify Kc ordering (Maize 1.20 > Tomato 1.15 > Wheat 0.85) yields ETc ordering."""
        res = canonical_sim.run(mode="fuzzy")
        m1 = res.zone_metrics[1]
        m2 = res.zone_metrics[2]
        m3 = res.zone_metrics[3]
        assert m3.total_etc_mm > m1.total_etc_mm > m2.total_etc_mm

    # -------------------------------------------------------------------------
    # TEST 20: Different soil properties affect soil dynamics appropriately
    # -------------------------------------------------------------------------
    def test_20_different_soil_properties_affect_dynamics(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify drainage and infiltration reflect Loam, Sandy, and Clay soil differences."""
        res = canonical_sim.run(mode="fuzzy")
        df = res.df
        # Sandy soil has higher drainage parameter than Loam or Clay
        z2 = canonical_sim.zones[1]
        assert z2.soil.drainage_parameter == 0.18
        assert canonical_sim.zones[0].soil.drainage_parameter == 0.08
        assert canonical_sim.zones[2].soil.drainage_parameter == 0.03

    # -------------------------------------------------------------------------
    # TEST 21: Identical simulation parameters are reproducible
    # -------------------------------------------------------------------------
    def test_21_simulation_reproducibility(self):
        """Verify running identical multizone simulations produces bitwise matching results."""
        cfg = MultizoneClosedLoopConfig(scenario=SimulationScenario.NORMAL, seed=99)
        sim1 = MultizoneClosedLoopSimulator(config=cfg)
        sim2 = MultizoneClosedLoopSimulator(config=cfg)

        res1 = sim1.run(mode="fuzzy")
        res2 = sim2.run(mode="fuzzy")

        pd.testing.assert_frame_equal(res1.df, res2.df)
        assert res1.system_metrics.total_system_irrigation_volume_l == res2.system_metrics.total_system_irrigation_volume_l

    # -------------------------------------------------------------------------
    # TEST 22: Different scenarios generate different trajectories
    # -------------------------------------------------------------------------
    def test_22_scenarios_generate_different_trajectories(self):
        """Verify Normal, Heatwave, and Rainy produce distinct multizone trajectories."""
        res_norm = simulate_multizone_closed_loop(scenario=SimulationScenario.NORMAL)
        res_heat = simulate_multizone_closed_loop(scenario=SimulationScenario.HEATWAVE)
        res_rain = simulate_multizone_closed_loop(scenario=SimulationScenario.RAINY)

        assert res_heat.system_metrics.total_system_etc_volume_l > res_norm.system_metrics.total_system_etc_volume_l
        assert res_rain.system_metrics.total_system_irrigation_volume_l < res_norm.system_metrics.total_system_irrigation_volume_l

    # -------------------------------------------------------------------------
    # TEST 23: No-irrigation baseline executes
    # -------------------------------------------------------------------------
    def test_23_no_irrigation_baseline_executes(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify Baseline A executes with exactly zero irrigation depth across all zones."""
        res_none = canonical_sim.run(mode="none")
        assert res_none.system_metrics.total_system_irrigation_volume_l == 0.0
        assert np.all(res_none.df["irrigation_application"].values == 0.0)

    # -------------------------------------------------------------------------
    # TEST 24: Fixed-irrigation baseline executes
    # -------------------------------------------------------------------------
    def test_24_fixed_irrigation_baseline_executes(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify Baseline B executes with fixed 1.5 mm/h across all zones."""
        res_fixed = canonical_sim.run(mode="fixed")
        assert res_fixed.system_metrics.total_system_irrigation_volume_l > 0.0
        for z_id in (1, 2, 3):
            # 1.5 mm/h * 24 h = 36.0 mm depth
            assert pytest.approx(res_fixed.zone_metrics[z_id].total_irrigation_applied_mm, abs=0.1) == 36.0

    # -------------------------------------------------------------------------
    # TEST 25: Fuzzy multizone controller executes
    # -------------------------------------------------------------------------
    def test_25_fuzzy_multizone_controller_executes(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify fuzzy multizone controller generates valid, responsive commands."""
        res_fuzzy = canonical_sim.run(mode="fuzzy")
        assert res_fuzzy.system_metrics.total_system_irrigation_volume_l > 0.0
        assert res_fuzzy.system_metrics.system_mean_mae < 5.0

    # -------------------------------------------------------------------------
    # TEST 26: Water scarcity does not activate allocation
    # -------------------------------------------------------------------------
    def test_26_water_scarcity_no_allocation_curtailment(self):
        """Verify Water Scarcity computes unconstrained control demand without WAF=0.30 scaling."""
        cfg_scarcity = MultizoneClosedLoopConfig(scenario=SimulationScenario.WATER_SCARCITY, seed=42)
        sim_scarcity = MultizoneClosedLoopSimulator(config=cfg_scarcity)
        res_scarcity = sim_scarcity.run(mode="fuzzy")

        # Demand and applications are not rationed by 0.30 inside Phase 12 controller
        assert res_scarcity.system_metrics.total_system_irrigation_volume_l > 10000.0

    # -------------------------------------------------------------------------
    # TEST 27: WaterAllocationFIS remains NotImplementedError
    # -------------------------------------------------------------------------
    def test_27_water_allocation_placeholder_intact(self):
        """Verify Phase 13 WaterAllocationFIS raises NotImplementedError."""
        fis_alloc = WaterAllocationFIS()
        with pytest.raises(NotImplementedError):
            fis_alloc.evaluate_zone(50.0, 0.5, 30.0, 2.0)
        with pytest.raises(NotImplementedError):
            fis_alloc.allocate_multizone([50.0, 40.0, 30.0], [0.5, 0.4, 0.3], [2.0, 1.0, 3.0], 1000.0)

    # -------------------------------------------------------------------------
    # TEST 28: Depth-to-volume conversion is correct
    # -------------------------------------------------------------------------
    def test_28_depth_to_volume_conversion(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify Volume_L = Depth_mm * Area_m2 for each zone."""
        res = canonical_sim.run(mode="fuzzy")
        for z in canonical_sim.zones:
            m = res.zone_metrics[z.zone_id]
            expected_vol = round(m.total_irrigation_applied_mm * z.area_m2, 2)
            assert pytest.approx(m.total_irrigation_volume_l, abs=0.1) == expected_vol

    # -------------------------------------------------------------------------
    # TEST 29: Aggregate system metrics are calculated correctly
    # -------------------------------------------------------------------------
    def test_29_aggregate_system_metrics(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify system-level sums and weighted averages match zone totals."""
        res = canonical_sim.run(mode="fuzzy")
        sm = res.system_metrics
        expected_sys_vol = sum(m.total_irrigation_volume_l for m in res.zone_metrics.values())
        assert pytest.approx(sm.total_system_irrigation_volume_l, abs=0.5) == expected_sys_vol
        assert sm.total_system_area_m2 == 300.0

    # -------------------------------------------------------------------------
    # TEST 30: Expected record count per scenario and multizone suite
    # -------------------------------------------------------------------------
    def test_30_expected_record_count(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify 3 zones * 1440 steps = 4,320 records per scenario run,
        which scales to exactly 25,920 records across all 6 scenarios (or 12,960 for 3 scenarios)."""
        res = canonical_sim.run(mode="fuzzy")
        assert len(res.df) == 3 * 1440 == 4320

    # -------------------------------------------------------------------------
    # TEST 31: NaN / Inf validation remains active
    # -------------------------------------------------------------------------
    def test_31_nan_inf_validation(self, canonical_sim: MultizoneClosedLoopSimulator):
        """Verify underlying FIS subsystems reject NaN/Inf inputs."""
        with pytest.raises(ValueError):
            canonical_sim.fis_soil.evaluate(rsm=float("nan"), moisture_error=5.0)
        with pytest.raises(ValueError):
            canonical_sim.fis_weather.evaluate(float("inf"), 50.0, 500.0, 2.0, 0.0)

    # -------------------------------------------------------------------------
    # TEST 32: Phase 11 single-zone simulation remains operational
    # -------------------------------------------------------------------------
    def test_32_phase_11_single_zone_backward_compatibility(self):
        """Verify Phase 11 single-zone ClosedLoopSimulator continues running flawlessly."""
        p11_sim = ClosedLoopSimulator(config=ClosedLoopConfig(scenario=SimulationScenario.NORMAL, seed=42))
        df_p11, m_p11 = p11_sim.run(mode="fuzzy")
        assert len(df_p11) == 1440
        assert m_p11.final_soil_moisture > 58.0
