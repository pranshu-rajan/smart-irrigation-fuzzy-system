"""
Comprehensive Test Suite for Phase 13: Water Allocation Fuzzy Inference System.

Validates:
1. Mamdani fuzzy inference engine correctness and mathematical fidelity.
2. Input validation and NaN/inf rejection.
3. Boundary clamping and domain guarantees [0.0, 100.0]%.
4. Engineering rules and sensitivity monotonicity (Supply, Demand, Stress, Priority).
5. Hard physical supply conservation enforcement (Allocated <= Available, Allocated <= Requested).
6. Zero-demand and zero-supply safety invariants.
7. Telemetry diagnostics and vectorized batch evaluation.
8. Controlled supply-sweep and priority sensitivity experiments.
9. Full multizone 24-hour closed-loop integration under supply constraints.
"""

import math
import pytest
import numpy as np

from fuzzy_engine.water_allocation import WaterAllocationFIS
from simulation.water_allocation import (
    allocate_water,
    bounded_priority_weighted_allocation,
    AllocationResult,
    MultizoneAllocationConfig,
    MultizoneAllocationSimulator,
    simulate_multizone_allocation,
)
from config.allocation_defaults import SupplyScenario, DEFAULT_ZONE_PRIORITIES_PCT
from config.schemas import SimulationScenario


@pytest.fixture(scope="module")
def fis() -> WaterAllocationFIS:
    """Instantiate a shared WaterAllocationFIS engine."""
    return WaterAllocationFIS()


class TestWaterAllocationFISCore:
    """Unit tests for WaterAllocationFIS inference and mathematical properties."""

    # TEST 1: Zero available water -> allocation is strictly 0.0%
    def test_01_zero_available_water_safety(self, fis: WaterAllocationFIS):
        """Verify allocation factor is strictly 0.0 when available water is 0.0%."""
        val = fis.evaluate(
            available_water=0.0,
            zone_demand=80.0,
            zone_stress=75.0,
            zone_priority=85.0,
        )
        assert val == 0.0

    # TEST 2: Very low available water + high demand -> strongly restricted allocation
    def test_02_very_low_available_water_high_demand(self, fis: WaterAllocationFIS):
        """Verify allocation is severely restricted when available supply is very low."""
        val_low_water = fis.evaluate(
            available_water=5.0,
            zone_demand=90.0,
            zone_stress=20.0,
            zone_priority=40.0,
        )
        val_abundant = fis.evaluate(
            available_water=90.0,
            zone_demand=90.0,
            zone_stress=20.0,
            zone_priority=40.0,
        )
        assert val_low_water < 25.0
        assert val_abundant > val_low_water

    # TEST 3: High available water + low demand -> low allocation (no unjustified maximum)
    def test_03_high_available_water_low_demand(self, fis: WaterAllocationFIS):
        """Verify low demand yields low allocation even if water is abundant."""
        val = fis.evaluate(
            available_water=95.0,
            zone_demand=15.0,
            zone_stress=10.0,
            zone_priority=50.0,
        )
        assert val < 45.0

    # TEST 4: High available water + high demand -> high allocation
    def test_04_high_available_water_high_demand(self, fis: WaterAllocationFIS):
        """Verify high demand yields high allocation when water is abundant."""
        val = fis.evaluate(
            available_water=90.0,
            zone_demand=85.0,
            zone_stress=50.0,
            zone_priority=70.0,
        )
        assert val >= 70.0

    # TEST 5: High stress increases allocation tendency
    def test_05_stress_sensitivity(self, fis: WaterAllocationFIS):
        """Verify increasing crop stress increases allocation tendency."""
        low_stress = fis.evaluate(
            available_water=60.0,
            zone_demand=65.0,
            zone_stress=10.0,
            zone_priority=60.0,
        )
        high_stress = fis.evaluate(
            available_water=60.0,
            zone_demand=65.0,
            zone_stress=90.0,
            zone_priority=60.0,
        )
        assert high_stress >= low_stress

    # TEST 6: High priority increases allocation tendency under scarcity
    def test_06_priority_sensitivity_under_scarcity(self, fis: WaterAllocationFIS):
        """Verify high priority zones receive stronger allocation under water scarcity."""
        low_prio = fis.evaluate(
            available_water=25.0,
            zone_demand=70.0,
            zone_stress=40.0,
            zone_priority=20.0,
        )
        high_prio = fis.evaluate(
            available_water=25.0,
            zone_demand=70.0,
            zone_stress=40.0,
            zone_priority=85.0,
        )
        assert high_prio > low_prio

    # TEST 7: Low priority does not receive more allocation than higher priority
    def test_07_priority_ordering(self, fis: WaterAllocationFIS):
        """Verify priority monotonicity: low priority <= medium <= high <= critical."""
        allocs = [
            fis.evaluate(available_water=50.0, zone_demand=60.0, zone_stress=50.0, zone_priority=p)
            for p in [10.0, 45.0, 75.0, 95.0]
        ]
        for i in range(len(allocs) - 1):
            assert allocs[i] <= allocs[i + 1] + 1e-4

    # TEST 8: High demand + high stress + high priority -> strong allocation
    def test_08_critical_urgent_demand(self, fis: WaterAllocationFIS):
        """Verify high demand, severe stress, and high priority command near-maximum allocation."""
        val = fis.evaluate(
            available_water=80.0,
            zone_demand=90.0,
            zone_stress=90.0,
            zone_priority=90.0,
        )
        assert val >= 80.0

    # TEST 9: NaN rejection
    def test_09_nan_rejection(self, fis: WaterAllocationFIS):
        """Verify all inputs reject NaN with ValueError."""
        with pytest.raises(ValueError):
            fis.evaluate(float("nan"), 50.0, 50.0, 50.0)
        with pytest.raises(ValueError):
            fis.evaluate(50.0, float("nan"), 50.0, 50.0)
        with pytest.raises(ValueError):
            fis.evaluate(50.0, 50.0, float("nan"), 50.0)
        with pytest.raises(ValueError):
            fis.evaluate(50.0, 50.0, 50.0, float("nan"))

    # TEST 10: Inf rejection
    def test_10_inf_rejection(self, fis: WaterAllocationFIS):
        """Verify all inputs reject infinite values with ValueError."""
        with pytest.raises(ValueError):
            fis.evaluate(float("inf"), 50.0, 50.0, 50.0)
        with pytest.raises(ValueError):
            fis.evaluate(50.0, float("-inf"), 50.0, 50.0)

    # TEST 11: Boundary clamping
    def test_11_boundary_clamping(self, fis: WaterAllocationFIS):
        """Verify finite values outside [0, 100]% are clamped without raising errors."""
        val_neg = fis.evaluate(-20.0, 50.0, 50.0, 50.0)
        val_high = fis.evaluate(150.0, 50.0, 50.0, 50.0)
        assert val_neg == 0.0  # Clamped to 0% available water
        assert 0.0 <= val_high <= 100.0

    # TEST 12: Output strictly in [0.0, 100.0]%
    def test_12_output_bounds(self, fis: WaterAllocationFIS):
        """Verify allocation output is strictly bounded within [0, 100]%."""
        grid = [0.0, 20.0, 50.0, 80.0, 100.0]
        for aw in grid:
            for zd in grid:
                for zs in grid:
                    for zp in grid:
                        out = fis.evaluate(aw, zd, zs, zp)
                        assert 0.0 <= out <= 100.0

    # TEST 13: Monotonicity with available water
    def test_13_monotonicity_available_water(self, fis: WaterAllocationFIS):
        """Verify allocation factor increases or remains steady as available water increases."""
        supplies = [10.0, 30.0, 50.0, 75.0, 100.0]
        results = [
            fis.evaluate(available_water=aw, zone_demand=70.0, zone_stress=60.0, zone_priority=70.0)
            for aw in supplies
        ]
        for i in range(len(results) - 1):
            assert results[i] <= results[i + 1] + 1e-4

    # TEST 14: Zero demand safety
    def test_14_zero_demand_safety(self, fis: WaterAllocationFIS):
        """Verify allocation is 0.0 when zone demand is 0.0, regardless of supply and priority."""
        for aw in [0.0, 50.0, 100.0]:
            for zp in [20.0, 50.0, 90.0]:
                out = fis.evaluate(available_water=aw, zone_demand=0.0, zone_stress=80.0, zone_priority=zp)
                assert out == 0.0

    # TEST 15: Detailed evaluation telemetry
    def test_15_detailed_evaluation(self, fis: WaterAllocationFIS):
        """Verify evaluate_detailed returns full telemetry structure."""
        res = fis.evaluate_detailed(
            available_water=75.0,
            zone_demand=60.0,
            zone_stress=50.0,
            zone_priority=70.0,
        )
        assert "inputs" in res
        assert "clamped_inputs" in res
        assert "memberships" in res
        assert "active_rules" in res
        assert "consequent_activations" in res
        assert "defuzzified_output" in res
        assert len(res["active_rules"]) > 0

    # TEST 16: Batch array evaluation
    def test_16_array_evaluation(self, fis: WaterAllocationFIS):
        """Verify vectorized evaluate_array matches point-by-point scalar evaluation."""
        n = 10
        np.random.seed(42)
        aw = np.random.uniform(0.0, 100.0, n)
        zd = np.random.uniform(0.0, 100.0, n)
        zs = np.random.uniform(0.0, 100.0, n)
        zp = np.random.uniform(0.0, 100.0, n)

        arr_out = fis.evaluate_array(aw, zd, zs, zp)
        assert arr_out.shape == (n,)
        for i in range(n):
            scalar_out = fis.evaluate(aw[i], zd[i], zs[i], zp[i])
            assert pytest.approx(arr_out[i], abs=1e-5) == scalar_out


class TestDeterministicConstraintEnforcement:
    """Tests for physical shared-water supply constraint enforcement."""

    # TEST 17: Request exceeds supply -> Hard constraint caps allocation at available supply
    def test_17_request_exceeds_supply(self, fis: WaterAllocationFIS):
        """Verify Allocated_total <= Available_Supply when requests exceed supply."""
        requests_mm = {1: 0.20, 2: 0.20, 3: 0.20}  # 0.2 mm in 1 min
        areas = {1: 100.0, 2: 120.0, 3: 80.0}       # Total volume req = 20 + 24 + 16 = 60 L
        stresses = {1: 50.0, 2: 40.0, 3: 60.0}
        priorities = {1: 70.0, 2: 40.0, 3: 85.0}

        # Available supply is only 18.0 Liters (30% capacity)
        available_supply_l = 18.0
        available_water_pct = 30.0

        res = allocate_water(
            requests_mm=requests_mm,
            areas_m2=areas,
            stresses_pct=stresses,
            priorities_pct=priorities,
            available_water_pct=available_water_pct,
            available_supply_l=available_supply_l,
            fis=fis,
        )

        assert res.is_supply_constrained is True
        assert res.total_requested_l == pytest.approx(60.0, abs=1e-4)
        assert res.total_allocated_l <= available_supply_l + 1e-9
        assert res.total_unmet_l == pytest.approx(res.total_requested_l - res.total_allocated_l, abs=1e-4)

    # TEST 18: Request below supply -> No artificial extra allocation occurs
    def test_18_request_below_supply(self, fis: WaterAllocationFIS):
        """Verify Allocated_total <= Requested_total when supply is abundant."""
        requests_mm = {1: 0.05, 2: 0.02, 3: 0.03}  # Total req volume = 5 + 2.4 + 2.4 = 9.8 L
        areas = {1: 100.0, 2: 120.0, 3: 80.0}
        stresses = {1: 30.0, 2: 20.0, 3: 30.0}
        priorities = {1: 70.0, 2: 40.0, 3: 85.0}

        # Abundant supply = 60.0 Liters (100%)
        res = allocate_water(
            requests_mm=requests_mm,
            areas_m2=areas,
            stresses_pct=stresses,
            priorities_pct=priorities,
            available_water_pct=100.0,
            available_supply_l=60.0,
            fis=fis,
        )

        assert res.total_allocated_l <= res.total_requested_l + 1e-9
        for z_id in [1, 2, 3]:
            assert res.allocated_volumes_l[z_id] <= res.requested_volumes_l[z_id] + 1e-9
            assert res.allocated_depths_mm[z_id] <= requests_mm[z_id] + 1e-9

    # TEST 19: All zone requests are zero -> Total allocation is zero
    def test_19_zero_requests_all_zones(self, fis: WaterAllocationFIS):
        """Verify allocation is zero for all zones when requests are zero."""
        requests_mm = {1: 0.0, 2: 0.0, 3: 0.0}
        areas = {1: 100.0, 2: 120.0, 3: 80.0}
        stresses = {1: 80.0, 2: 80.0, 3: 80.0}
        priorities = {1: 90.0, 2: 90.0, 3: 90.0}

        res = allocate_water(
            requests_mm=requests_mm,
            areas_m2=areas,
            stresses_pct=stresses,
            priorities_pct=priorities,
            available_water_pct=100.0,
            available_supply_l=60.0,
            fis=fis,
        )

        assert res.total_allocated_l == 0.0
        assert res.total_unmet_l == 0.0
        assert all(v == 0.0 for v in res.allocated_volumes_l.values())

    # TEST 20: Zero available supply -> Total allocation is zero
    def test_20_zero_available_supply(self, fis: WaterAllocationFIS):
        """Verify allocation is zero when available shared water is zero."""
        requests_mm = {1: 0.20, 2: 0.20, 3: 0.20}
        areas = {1: 100.0, 2: 120.0, 3: 80.0}
        stresses = {1: 90.0, 2: 90.0, 3: 90.0}
        priorities = {1: 90.0, 2: 90.0, 3: 90.0}

        res = allocate_water(
            requests_mm=requests_mm,
            areas_m2=areas,
            stresses_pct=stresses,
            priorities_pct=priorities,
            available_water_pct=0.0,
            available_supply_l=0.0,
            fis=fis,
        )

        assert res.total_allocated_l == 0.0
        assert res.total_unmet_l == res.total_requested_l
        assert all(v == 0.0 for v in res.allocated_volumes_l.values())

    # TEST 21: Depth to volume and volume to depth conversions
    def test_21_depth_volume_consistency(self, fis: WaterAllocationFIS):
        """Verify Depth_mm * Area_m2 == Volume_L and Volume_L / Area_m2 == Depth_mm."""
        requests_mm = {1: 0.15, 2: 0.10, 3: 0.12}
        areas = {1: 100.0, 2: 120.0, 3: 80.0}
        stresses = {1: 40.0, 2: 30.0, 3: 50.0}
        priorities = {1: 70.0, 2: 40.0, 3: 85.0}

        res = allocate_water(
            requests_mm=requests_mm,
            areas_m2=areas,
            stresses_pct=stresses,
            priorities_pct=priorities,
            available_water_pct=70.0,
            available_supply_l=42.0,
            fis=fis,
        )

        for z_id in [1, 2, 3]:
            # Requested
            assert pytest.approx(res.requested_volumes_l[z_id], abs=1e-5) == requests_mm[z_id] * areas[z_id]
            # Allocated
            assert pytest.approx(res.allocated_volumes_l[z_id], abs=1e-5) == res.allocated_depths_mm[z_id] * areas[z_id]
            # Unmet
            assert pytest.approx(res.unmet_volumes_l[z_id], abs=1e-5) == res.unmet_depths_mm[z_id] * areas[z_id]


class TestMultizoneAllocationIntegration:
    """Integration tests for 24-hour multizone simulation under shared supply constraints."""

    # TEST 22: Controlled supply-sweep experiment
    def test_22_supply_sweep_experiment(self):
        """Verify increasing available water increases or maintains allocated volume."""
        supplies = [0.0, 15.0, 30.0, 50.0, 75.0, 100.0]
        results = []
        for s in supplies:
            res = simulate_multizone_allocation(
                scenario=SimulationScenario.NORMAL,
                supply_factor_override=s,
                duration_hours=2,
                seed=42,
            )
            results.append(res.total_allocated_volume_l)

        # 0% supply gives 0.0 Liters allocated
        assert results[0] == 0.0
        # Monotonicity with available water
        for i in range(len(results) - 1):
            assert results[i] <= results[i + 1] + 1e-4

    # TEST 23: Controlled priority experiment
    def test_23_priority_experiment(self):
        """Verify increasing Zone 1 priority increases its allocated share under scarcity."""
        # Low Zone 1 priority
        prio_low = {1: 20.0, 2: 60.0, 3: 80.0}
        res_low = simulate_multizone_allocation(
            scenario=SimulationScenario.NORMAL,
            supply_factor_override=30.0,
            duration_hours=2,
            zone_priorities_pct=prio_low,
            seed=42,
        )

        # High Zone 1 priority
        prio_high = {1: 90.0, 2: 60.0, 3: 80.0}
        res_high = simulate_multizone_allocation(
            scenario=SimulationScenario.NORMAL,
            supply_factor_override=30.0,
            duration_hours=2,
            zone_priorities_pct=prio_high,
            seed=42,
        )

        z1_alloc_low = res_low.zone_metrics[1]["total_allocated_l"]
        z1_alloc_high = res_high.zone_metrics[1]["total_allocated_l"]
        assert z1_alloc_high > z1_alloc_low

    # TEST 24: Deterministic reproducibility
    def test_24_deterministic_reproducibility(self):
        """Verify identical configurations and seeds produce identical allocation results."""
        res1 = simulate_multizone_allocation(
            scenario=SimulationScenario.NORMAL,
            supply_factor_override=50.0,
            duration_hours=2,
            seed=123,
        )
        res2 = simulate_multizone_allocation(
            scenario=SimulationScenario.NORMAL,
            supply_factor_override=50.0,
            duration_hours=2,
            seed=123,
        )

        assert res1.total_requested_volume_l == res2.total_requested_volume_l
        assert res1.total_allocated_volume_l == res2.total_allocated_volume_l
        assert res1.total_unmet_volume_l == res2.total_unmet_volume_l
        for z_id in [1, 2, 3]:
            assert res1.zone_metrics[z_id]["total_allocated_l"] == res2.zone_metrics[z_id]["total_allocated_l"]

    # TEST 25: Full 24-hour simulation under Normal scenario
    def test_25_normal_scenario_execution(self):
        """Verify full 24-hour Normal scenario allocation simulation executes cleanly."""
        res = simulate_multizone_allocation(
            scenario=SimulationScenario.NORMAL,
            supply_scenario=SupplyScenario.NORMAL,
            seed=42,
        )
        assert len(res.telemetry_records) == 1440 * 3  # 4,320 zone-timestep records
        assert res.total_requested_volume_l > 0.0
        assert res.total_allocated_volume_l > 0.0
        assert res.total_allocated_volume_l <= res.total_requested_volume_l
        assert res.system_allocation_ratio > 0.50

    # TEST 26: Water Scarcity scenario constraint activation
    def test_26_water_scarcity_constraint_activation(self):
        """Verify Water Scarcity scenario triggers active supply constraints and unmet demand."""
        res = simulate_multizone_allocation(
            scenario=SimulationScenario.WATER_SCARCITY,
            seed=42,
        )
        assert res.constrained_timesteps_count > 0
        assert res.total_unmet_volume_l > 0.0
        assert res.total_allocated_volume_l < res.total_requested_volume_l

    # TEST 27: Soil-water conservation residual verification across all timesteps
    def test_27_water_balance_conservation_residual(self):
        """Verify water balance residual is bounded by 1e-5 mm for all records."""
        res = simulate_multizone_allocation(
            scenario=SimulationScenario.NORMAL,
            seed=42,
        )
        for rec in res.telemetry_records:
            assert abs(rec["water_balance_residual_mm"]) < 1e-5


class TestBoundedPriorityAllocationAdversarial:
    """
    Dedicated adversarial test suite specifically designed to expose mathematical failures:
    - Verifies bounded priority-weighted allocation algorithm.
    - Tests demand ceilings (A_final,z <= A_raw,z).
    - Tests hard supply ceilings (sum(A_final,z) <= W_available).
    - Tests priority-driven distribution without artificial water creation.
    - Executes 1,000 randomized property tests.
    """

    # TEST 28: One high-priority zone (Test 1)
    def test_28_adversarial_one_high_priority_zone(self):
        """
        Verify: Zone 1 (request=small, priority=very high) and Zone 2 (request=large, priority=low)
        under scarce supply respects both individual ceilings: A1 <= R1 and A2 <= R2.
        """
        requests = {1: 1.0, 2: 20.0}
        priorities = {1: 99.0, 2: 10.0}
        supply = 8.0  # Scarce: total req = 21.0 > 8.0

        alloc = bounded_priority_weighted_allocation(requests, priorities, supply)

        assert alloc[1] <= requests[1] + 1e-9
        assert alloc[2] <= requests[2] + 1e-9
        assert sum(alloc.values()) <= supply + 1e-9
        # Zone 1 requested 1.0 L, so it must receive exactly 1.0 L (capped at ceiling), NOT 8.0 * (99/109) = 7.26 L!
        assert alloc[1] == pytest.approx(1.0, abs=1e-5)
        # Zone 2 receives remaining 7.0 L
        assert alloc[2] == pytest.approx(7.0, abs=1e-5)

    # TEST 29: Extreme priority imbalance (Test 2)
    def test_29_adversarial_extreme_priority_imbalance(self):
        """Verify extreme priority values never cause any zone to exceed its own request."""
        requests = {1: 2.0, 2: 15.0}
        priorities = {1: 1000.0, 2: 0.001}
        supply = 10.0

        alloc = bounded_priority_weighted_allocation(requests, priorities, supply)

        assert alloc[1] <= requests[1] + 1e-9
        assert alloc[2] <= requests[2] + 1e-9
        assert sum(alloc.values()) <= supply + 1e-9
        assert alloc[1] == pytest.approx(2.0, abs=1e-5)
        assert alloc[2] == pytest.approx(8.0, abs=1e-5)

    # TEST 30: Tiny request with huge priority (Test 3)
    def test_30_adversarial_tiny_request_huge_priority(self):
        """Verify a zone with tiny request and huge priority is capped at its tiny request."""
        requests = {1: 0.001, 2: 50.0}
        priorities = {1: 100.0, 2: 1.0}
        supply = 30.0

        alloc = bounded_priority_weighted_allocation(requests, priorities, supply)

        assert alloc[1] <= requests[1] + 1e-9
        assert alloc[1] == pytest.approx(0.001, abs=1e-6)
        assert alloc[2] == pytest.approx(29.999, abs=1e-4)
        assert sum(alloc.values()) <= supply + 1e-9

    # TEST 31: Supply greater than total request (Test 4)
    def test_31_adversarial_supply_greater_than_request(self):
        """Verify allocation = request and not available supply when supply is abundant."""
        requests = {1: 5.0, 2: 8.0, 3: 4.0}  # Total = 17.0 L
        priorities = {1: 70.0, 2: 40.0, 3: 85.0}
        supply = 60.0  # Abundant

        alloc = bounded_priority_weighted_allocation(requests, priorities, supply)

        for z in [1, 2, 3]:
            assert alloc[z] == pytest.approx(requests[z], abs=1e-6)
        assert sum(alloc.values()) == pytest.approx(17.0, abs=1e-6)
        assert sum(alloc.values()) < supply

    # TEST 32: Zero supply (Test 5)
    def test_32_adversarial_zero_supply(self):
        """Verify all final allocations are exactly zero when available supply is zero."""
        requests = {1: 10.0, 2: 20.0, 3: 15.0}
        priorities = {1: 90.0, 2: 80.0, 3: 95.0}
        supply = 0.0

        alloc = bounded_priority_weighted_allocation(requests, priorities, supply)

        for z in [1, 2, 3]:
            assert alloc[z] == 0.0
        assert sum(alloc.values()) == 0.0

    # TEST 33: Zero demand (Test 6)
    def test_33_adversarial_zero_demand(self):
        """Verify a zone with zero demand receives exactly zero regardless of priority."""
        requests = {1: 0.0, 2: 15.0, 3: 10.0}
        priorities = {1: 100.0, 2: 40.0, 3: 50.0}  # Zone 1 has highest priority!
        supply = 20.0

        alloc = bounded_priority_weighted_allocation(requests, priorities, supply)

        assert alloc[1] == 0.0
        assert alloc[2] > 0.0
        assert alloc[3] > 0.0
        assert sum(alloc.values()) <= supply + 1e-9

    # TEST 34: One zone only (Test 7)
    def test_34_adversarial_single_zone(self):
        """Verify single zone allocation is strictly min(request, available_supply)."""
        # Scarce
        alloc_scarce = bounded_priority_weighted_allocation({1: 12.0}, {1: 70.0}, 8.0)
        assert alloc_scarce[1] == pytest.approx(8.0, abs=1e-6)

        # Abundant
        alloc_abundant = bounded_priority_weighted_allocation({1: 5.0}, {1: 70.0}, 8.0)
        assert alloc_abundant[1] == pytest.approx(5.0, abs=1e-6)

        # Exact match
        alloc_exact = bounded_priority_weighted_allocation({1: 8.0}, {1: 70.0}, 8.0)
        assert alloc_exact[1] == pytest.approx(8.0, abs=1e-6)

    # TEST 35: Equal priorities (Test 8)
    def test_35_adversarial_equal_priorities(self):
        """Verify equal priorities produce deterministic, symmetric, and reproducible shares."""
        requests = {1: 10.0, 2: 10.0, 3: 10.0}
        priorities = {1: 50.0, 2: 50.0, 3: 50.0}
        supply = 15.0

        alloc = bounded_priority_weighted_allocation(requests, priorities, supply)

        assert alloc[1] == pytest.approx(5.0, abs=1e-6)
        assert alloc[2] == pytest.approx(5.0, abs=1e-6)
        assert alloc[3] == pytest.approx(5.0, abs=1e-6)
        assert sum(alloc.values()) == pytest.approx(15.0, abs=1e-6)

        # 100 repeated executions yield bit-exact results
        for _ in range(100):
            alloc_rep = bounded_priority_weighted_allocation(requests, priorities, supply)
            assert alloc_rep == alloc

    # TEST 36: Priority perturbation (Test 9)
    def test_36_adversarial_priority_perturbation(self):
        """Verify changing priority under genuine scarcity redistributes water while respecting ceilings."""
        requests = {1: 10.0, 2: 10.0}
        supply = 12.0

        # Case A: Zone 1 has higher priority
        alloc_a = bounded_priority_weighted_allocation(requests, {1: 80.0, 2: 20.0}, supply)
        assert alloc_a[1] > alloc_a[2]
        assert alloc_a[1] <= requests[1]
        assert alloc_a[2] <= requests[2]
        assert sum(alloc_a.values()) == pytest.approx(supply, abs=1e-6)

        # Case B: Zone 2 has higher priority
        alloc_b = bounded_priority_weighted_allocation(requests, {1: 20.0, 2: 80.0}, supply)
        assert alloc_b[2] > alloc_b[1]
        assert alloc_b[1] <= requests[1]
        assert alloc_b[2] <= requests[2]
        assert sum(alloc_b.values()) == pytest.approx(supply, abs=1e-6)

    # TEST 37: System conservation in allocate_water (Test 10)
    def test_37_adversarial_system_conservation(self, fis: WaterAllocationFIS):
        """Verify system conservation across diverse multi-variable steps in allocate_water."""
        np.random.seed(123)
        areas = {1: 100.0, 2: 120.0, 3: 80.0}
        priorities = {1: 70.0, 2: 40.0, 3: 85.0}

        for _ in range(50):
            reqs_mm = {
                1: float(np.random.uniform(0.0, 0.20)),
                2: float(np.random.uniform(0.0, 0.20)),
                3: float(np.random.uniform(0.0, 0.20)),
            }
            stresses = {
                1: float(np.random.uniform(0.0, 100.0)),
                2: float(np.random.uniform(0.0, 100.0)),
                3: float(np.random.uniform(0.0, 100.0)),
            }
            avail_pct = float(np.random.uniform(0.0, 100.0))
            supply_l = (avail_pct / 100.0) * 60.0

            res = allocate_water(
                requests_mm=reqs_mm,
                areas_m2=areas,
                stresses_pct=stresses,
                priorities_pct=priorities,
                available_water_pct=avail_pct,
                available_supply_l=supply_l,
                fis=fis,
            )

            # Invariant checks
            assert res.total_allocated_l <= supply_l + 1e-9
            assert res.total_allocated_l <= res.total_requested_l + 1e-9
            for z in [1, 2, 3]:
                assert res.allocated_volumes_l[z] <= res.requested_volumes_l[z] + 1e-9
                assert res.allocated_depths_mm[z] <= reqs_mm[z] + 1e-9

    # TEST 38: Randomized property testing (1,000 cases)
    def test_38_randomized_property_testing_1000_cases(self):
        """
        Verify all mathematical invariants across 1,000 randomized allocation cases:
        - 0 <= allocation_z <= raw_request_z
        - sum(allocation_z) <= available_supply
        - zero request -> zero allocation
        - zero supply -> zero allocation
        - if total request <= supply: allocation_z == request_z
        """
        np.random.seed(42)

        for case in range(1000):
            n_zones = int(np.random.randint(1, 6))
            zones = list(range(1, n_zones + 1))
            requests = {
                z: float(np.random.exponential(10.0)) if np.random.rand() > 0.25 else 0.0
                for z in zones
            }
            priorities = {z: float(np.random.uniform(0.0, 100.0)) for z in zones}
            supply = float(np.random.uniform(0.0, sum(requests.values()) * 1.5))
            if np.random.rand() < 0.10:
                supply = 0.0

            alloc = bounded_priority_weighted_allocation(requests, priorities, supply)

            tot_req = sum(requests.values())
            tot_alloc = sum(alloc.values())

            # Invariant A: Zero supply -> Zero allocation
            if supply == 0.0:
                assert tot_alloc == 0.0

            # Invariant B: Zero request -> Zero allocation
            for z in zones:
                if requests[z] == 0.0:
                    assert alloc[z] == 0.0

            # Invariant C: Demand ceiling (0 <= alloc <= request)
            for z in zones:
                assert alloc[z] >= -1e-12
                assert alloc[z] <= requests[z] + 1e-9

            # Invariant D: Supply ceiling (sum alloc <= supply)
            assert tot_alloc <= supply + 1e-9

            # Invariant E: Full satisfaction if supply >= total request
            if tot_req <= supply:
                assert abs(tot_alloc - tot_req) < 1e-6
                for z in zones:
                    assert abs(alloc[z] - requests[z]) < 1e-6

