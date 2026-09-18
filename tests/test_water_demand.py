"""
Unit and Integration Tests for Phase 9: Water Demand Fuzzy Inference System (WaterDemandFIS).

Verifies:
1. WaterDemandFIS initialization and variable binding from central registry.
2. Part 13 critical sanity cases (Case 1 through Case 6).
3. Part 14 physical consistency tests (ETc, Deficit, Effective Rainfall relationship).
4. Part 15 monotonicity checks (ETc, Deficit, Effective Rainfall).
5. Strictly bounded crisp output in [0.0, 100.0]%.
6. Rejection of invalid inputs (NaN, +inf, -inf).
7. Safe clamping of out-of-universe boundary inputs.
8. Deterministic inference across multiple evaluations.
9. Detailed evaluation telemetry structure.
10. Vectorized evaluate_array matches scalar evaluation.
"""

import numpy as np
import pytest

from fuzzy_engine.water_demand import WaterDemandFIS
from models.etc import calculate_crop_water_deficit


@pytest.fixture
def fis():
    """Fixture providing a WaterDemandFIS instance."""
    return WaterDemandFIS()


def test_water_demand_initialization(fis):
    """Verify WaterDemandFIS binds variables and initializes evaluation grid."""
    assert fis.etc_var.name == "etc"
    assert fis.deficit_var.name == "crop_water_deficit"
    assert fis.rainfall_var.name == "effective_rainfall"
    assert fis.demand_var.name == "water_demand"
    assert len(fis.RULES) == 39
    assert len(fis.z_grid) == 501
    assert fis.z_grid[0] == 0.0
    assert fis.z_grid[-1] == 100.0


# =============================================================================
# PART 13: SANITY CASES
# =============================================================================

def test_sanity_case_1_very_low_demand(fis):
    """
    CASE 1: Very Low Demand
    ETc: very low (0.5 mm/day)
    Deficit: none (0.0 mm/day)
    Effective rainfall: high / very high (35.0 mm)
    Expected: very low water demand (< 20%).
    """
    demand = fis.evaluate(etc=0.5, crop_water_deficit=0.0, effective_rainfall=35.0)
    assert 0.0 <= demand <= 20.0, f"Expected very low demand, got {demand:.2f}%"


def test_sanity_case_2_low_demand(fis):
    """
    CASE 2: Low Demand
    ETc: low (2.0 mm/day)
    Deficit: low / none (0.5 mm/day)
    Effective rainfall: moderate / high (20.0 mm)
    Expected: low water demand (< 35%).
    """
    demand = fis.evaluate(etc=2.0, crop_water_deficit=0.5, effective_rainfall=20.0)
    assert 0.0 <= demand <= 35.0, f"Expected low demand, got {demand:.2f}%"


def test_sanity_case_3_moderate_demand(fis):
    """
    CASE 3: Moderate Demand
    ETc: moderate (5.0 mm/day)
    Deficit: moderate (4.0 mm/day)
    Effective rainfall: low / moderate (1.0 mm)
    Expected: moderate demand (35% to 65%).
    """
    demand = fis.evaluate(etc=5.0, crop_water_deficit=4.0, effective_rainfall=1.0)
    assert 35.0 <= demand <= 65.0, f"Expected moderate demand, got {demand:.2f}%"


def test_sanity_case_4_high_demand(fis):
    """
    CASE 4: High Demand
    ETc: high (10.5 mm/day, core of High MF [8.5, 10.5, 12.5])
    Deficit: high (10.5 mm/day, core of High MF [8.0, 10.5, 12.5])
    Effective rainfall: low / none (0.0 mm)
    Expected: high demand (65% to 85%).
    """
    demand = fis.evaluate(etc=10.5, crop_water_deficit=10.5, effective_rainfall=0.0)
    assert 65.0 <= demand <= 85.0, f"Expected high demand, got {demand:.2f}%"


def test_sanity_case_5_extreme_demand(fis):
    """
    CASE 5: Extreme Demand
    ETc: very high (13.0 mm/day)
    Deficit: very high (13.0 mm/day)
    Effective rainfall: none (0.0 mm)
    Expected: very high demand (> 80%).
    """
    demand = fis.evaluate(etc=13.0, crop_water_deficit=13.0, effective_rainfall=0.0)
    assert 80.0 <= demand <= 100.0, f"Expected very high demand, got {demand:.2f}%"


def test_sanity_case_6_rainfall_mitigation(fis):
    """
    CASE 6: Rainfall Mitigation
    Keep ETc fixed at 5.0 mm/day.
    Condition A: Dry spell (Effective Rainfall = 0 mm, Deficit = 5.0 mm/day)
    Condition B: Rain event (Effective Rainfall = 20 mm, Deficit = 0.0 mm/day)
    Expected: WaterDemand(B) significantly < WaterDemand(A).
    """
    demand_a = fis.evaluate(etc=5.0, crop_water_deficit=5.0, effective_rainfall=0.0)
    demand_b = fis.evaluate(etc=5.0, crop_water_deficit=0.0, effective_rainfall=20.0)
    assert demand_b < demand_a, f"Expected rainfall to reduce demand: A={demand_a}, B={demand_b}"
    assert (demand_a - demand_b) > 20.0, f"Expected substantial mitigation (>20%), got {demand_a - demand_b:.2f}%"


# =============================================================================
# PART 14: PHYSICAL CONSISTENCY TESTS
# =============================================================================

def test_physical_consistency_deficit_definition():
    """
    Test Phase 4 physical definition:
    Crop Water Deficit = max(ETc - Effective Rainfall, 0)
    """
    # ETc = 5, P_eff = 0 -> Deficit = 5
    def_1 = calculate_crop_water_deficit(etc_mm=5.0, effective_rainfall_mm=0.0)
    assert pytest.approx(def_1, rel=1e-3) == 5.0

    # ETc = 5, P_eff = 2 -> Deficit = 3
    def_2 = calculate_crop_water_deficit(etc_mm=5.0, effective_rainfall_mm=2.0)
    assert pytest.approx(def_2, rel=1e-3) == 3.0

    # ETc = 5, P_eff = 8 -> Deficit = 0
    def_3 = calculate_crop_water_deficit(etc_mm=5.0, effective_rainfall_mm=8.0)
    assert pytest.approx(def_3, rel=1e-3) == 0.0


def test_fis_response_to_physically_consistent_inputs(fis):
    """
    Verify that when inputs follow the physical relationship:
    Deficit = max(ETc - P_eff, 0), Water Demand responds consistently.
    """
    etc = 5.0

    # Step 1: Zero rain -> Deficit = 5.0
    rain_1 = 0.0
    def_1 = calculate_crop_water_deficit(etc, rain_1)
    demand_1 = fis.evaluate(etc=etc, crop_water_deficit=def_1, effective_rainfall=rain_1)

    # Step 2: Partial rain = 2.0 -> Deficit = 3.0
    rain_2 = 2.0
    def_2 = calculate_crop_water_deficit(etc, rain_2)
    demand_2 = fis.evaluate(etc=etc, crop_water_deficit=def_2, effective_rainfall=rain_2)

    # Step 3: Heavy rain = 10.0 -> Deficit = 0.0
    rain_3 = 10.0
    def_3 = calculate_crop_water_deficit(etc, rain_3)
    demand_3 = fis.evaluate(etc=etc, crop_water_deficit=def_3, effective_rainfall=rain_3)

    assert demand_1 > demand_2 > demand_3, (
        f"Demand should strictly decrease as rain increases and deficit drops: "
        f"{demand_1:.2f} > {demand_2:.2f} > {demand_3:.2f}"
    )


# =============================================================================
# PART 15: MONOTONICITY TESTS
# =============================================================================

def test_monotonicity_etc(fis):
    """
    Monotonicity with respect to ETc:
    Holding Deficit=3.0 mm/day and P_eff=0.0 mm constant,
    increasing ETc from 1.0 to 14.0 mm/day should generally not decrease Water Demand.
    """
    etc_values = np.linspace(1.0, 14.0, 14)
    demands = [fis.evaluate(etc=e, crop_water_deficit=3.0, effective_rainfall=0.0) for e in etc_values]

    # Check non-decreasing trend across significant steps
    assert demands[-1] >= demands[0], f"Expected overall ETc increase, got {demands[0]} -> {demands[-1]}"
    for i in range(len(demands) - 1):
        # Allow small tolerance for centroid discretization (0.5%)
        assert demands[i + 1] >= demands[i] - 0.5, (
            f"ETc monotonicity drop at {etc_values[i]} -> {etc_values[i+1]}: {demands[i]} -> {demands[i+1]}"
        )


def test_monotonicity_deficit(fis):
    """
    Monotonicity with respect to Crop Water Deficit:
    Holding ETc=5.0 mm/day and P_eff=0.0 mm constant,
    increasing Deficit from 0.0 to 14.0 mm/day should not decrease Water Demand.
    """
    def_values = np.linspace(0.0, 14.0, 15)
    demands = [fis.evaluate(etc=5.0, crop_water_deficit=d, effective_rainfall=0.0) for d in def_values]

    assert demands[-1] >= demands[0] + 40.0, f"Expected strong deficit increase: {demands[0]} -> {demands[-1]}"
    for i in range(len(demands) - 1):
        assert demands[i + 1] >= demands[i] - 0.5, (
            f"Deficit monotonicity drop at {def_values[i]} -> {def_values[i+1]}: {demands[i]} -> {demands[i+1]}"
        )


def test_monotonicity_effective_rainfall_inverse(fis):
    """
    Inverse monotonicity with respect to Effective Rainfall:
    Holding ETc=5.0 mm/day and Deficit=3.0 mm/day constant,
    increasing Effective Rainfall from 0.0 to 45.0 mm should not increase Water Demand.
    """
    rain_values = [0.0, 2.0, 5.0, 8.0, 12.0, 16.0, 20.0, 25.0, 30.0, 40.0]
    demands = [fis.evaluate(etc=5.0, crop_water_deficit=3.0, effective_rainfall=r) for r in rain_values]

    assert demands[-1] <= demands[0], f"Expected demand to drop with rain: {demands[0]} -> {demands[-1]}"
    for i in range(len(demands) - 1):
        assert demands[i + 1] <= demands[i] + 0.5, (
            f"Rain monotonicity violation at {rain_values[i]} -> {rain_values[i+1]}: {demands[i]} -> {demands[i+1]}"
        )


# =============================================================================
# VALIDATION AND ROBUSTNESS TESTS
# =============================================================================

def test_output_bounds_and_determinism(fis):
    """Verify output is strictly bounded within [0.0, 100.0]% and deterministic."""
    for _ in range(5):
        val = fis.evaluate(6.2, 4.1, 1.5)
        assert 0.0 <= val <= 100.0
        assert val == pytest.approx(fis.evaluate(6.2, 4.1, 1.5), abs=1e-9)


def test_invalid_inputs_rejected(fis):
    """Verify NaN and +/- inf inputs raise ValueError."""
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(np.nan, 2.0, 0.0)
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(5.0, np.inf, 0.0)
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(5.0, 2.0, -np.inf)


def test_out_of_bounds_inputs_clamped_safely(fis):
    """Verify inputs beyond universe bounds are safely clamped without throwing exceptions."""
    demand_high = fis.evaluate(999.0, 999.0, 999.0)
    assert 0.0 <= demand_high <= 100.0

    demand_low = fis.evaluate(-50.0, -50.0, -50.0)
    assert 0.0 <= demand_low <= 100.0


def test_detailed_evaluation_structure(fis):
    """Verify evaluate_detailed returns complete telemetry schema."""
    telemetry = fis.evaluate_detailed(etc=6.0, crop_water_deficit=4.5, effective_rainfall=0.5)

    assert "etc" in telemetry
    assert "crop_water_deficit" in telemetry
    assert "effective_rainfall" in telemetry
    assert "water_demand" in telemetry
    assert "etc_membership" in telemetry
    assert "deficit_membership" in telemetry
    assert "effective_rainfall_membership" in telemetry
    assert "consequent_activations" in telemetry
    assert "active_rules" in telemetry
    assert "total_fuzzy_area" in telemetry

    assert isinstance(telemetry["active_rules"], list)
    assert len(telemetry["active_rules"]) > 0
    assert telemetry["total_fuzzy_area"] > 0.0
    assert 0.0 <= telemetry["water_demand"] <= 100.0


def test_vectorized_evaluate_array(fis):
    """Verify evaluate_array matches pointwise evaluate calls exactly."""
    etc_arr = np.array([0.5, 3.0, 6.0, 9.0, 14.0])
    def_arr = np.array([0.0, 1.5, 5.0, 8.0, 14.0])
    rain_arr = np.array([25.0, 10.0, 1.0, 0.0, 0.0])

    vectorized_results = fis.evaluate_array(etc_arr, def_arr, rain_arr)
    assert len(vectorized_results) == 5

    for i in range(5):
        scalar = fis.evaluate(etc_arr[i], def_arr[i], rain_arr[i])
        assert pytest.approx(vectorized_results[i], abs=1e-9) == scalar


def test_evaluate_array_dimension_mismatch(fis):
    """Verify evaluate_array raises ValueError on mismatched input lengths."""
    with pytest.raises(ValueError, match="identical dimensions"):
        fis.evaluate_array(np.array([1.0, 2.0]), np.array([1.0]), np.array([1.0, 2.0]))
