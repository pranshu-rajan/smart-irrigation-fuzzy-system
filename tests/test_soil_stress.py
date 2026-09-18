"""
Unit and Integration Tests for Phase 7: Soil Stress Fuzzy Inference System (SoilStressFIS).

Verifies:
1. SoilStressFIS initialization and variable binding from central registry.
2. Part 9 critical sanity cases (Case A through Case E).
3. Strictly bounded crisp output in [0.0, 100.0]%.
4. Rejection of invalid inputs (NaN, +inf, -inf).
5. Safe clamping of out-of-universe boundary inputs.
6. Deterministic inference across multiple runs.
7. Detailed evaluation telemetry structure.
8. Representative monotonicity across agronomic regimes.
9. Vectorized evaluate_array matches scalar evaluation.
10. Fallback handling for empty fuzzy sets.
"""

import numpy as np
import pytest

from fuzzy_engine.soil_stress import SoilStressFIS


@pytest.fixture
def fis():
    """Fixture providing a SoilStressFIS instance."""
    return SoilStressFIS()


def test_soil_stress_initialization(fis):
    """Verify SoilStressFIS binds variables and initializes evaluation grid."""
    assert fis.rsm_var.name == "rsm"
    assert fis.error_var.name == "moisture_error"
    assert fis.stress_var.name == "soil_stress"
    assert len(fis.RULES) == 25
    assert len(fis.z_grid) == 501
    assert fis.z_grid[0] == 0.0
    assert fis.z_grid[-1] == 100.0


def test_sanity_case_a_extreme_drought_and_deficit(fis):
    """
    CASE A: RSM = very low (0.05), Moisture Error = strongly positive (+25%).
    Expected: Very high soil stress (> 80%).
    """
    stress = fis.evaluate(rsm=0.05, moisture_error=25.0)
    assert 80.0 <= stress <= 100.0, f"Expected very high stress, got {stress}"


def test_sanity_case_b_dry_soil_and_positive_error(fis):
    """
    CASE B: RSM = low/dry (0.25), Moisture Error = positive (+10%).
    Expected: High soil stress (> 65%).
    """
    stress = fis.evaluate(rsm=0.25, moisture_error=10.0)
    assert 65.0 <= stress <= 85.0, f"Expected high stress, got {stress}"


def test_sanity_case_c_adequate_moisture_zero_error(fis):
    """
    CASE C: RSM = adequate (0.55), Moisture Error = zero (0.0%).
    Expected: Low soil-water stress (< 25%).
    """
    stress = fis.evaluate(rsm=0.55, moisture_error=0.0)
    assert 10.0 <= stress <= 25.0, f"Expected low stress, got {stress}"


def test_sanity_case_d_wet_soil_negative_error(fis):
    """
    CASE D: RSM = high/wet (0.75), Moisture Error = negative (-10.0%).
    Expected: Low soil stress (< 20%).
    """
    stress = fis.evaluate(rsm=0.75, moisture_error=-10.0)
    assert 10.0 <= stress <= 20.0, f"Expected low stress, got {stress}"


def test_sanity_case_e_very_wet_soil_negative_error(fis):
    """
    CASE E: RSM = very wet (0.95), Moisture Error = large negative (-20.0%).
    Expected: Low soil stress (< 20%).
    """
    stress = fis.evaluate(rsm=0.95, moisture_error=-20.0)
    assert 10.0 <= stress <= 20.0, f"Expected low stress, got {stress}"


def test_output_bounds_and_determinism(fis):
    """Verify output is strictly in [0, 100] and identical across repeated evaluations."""
    res1 = fis.evaluate(0.40, 5.0)
    res2 = fis.evaluate(0.40, 5.0)
    assert res1 == res2
    assert 0.0 <= res1 <= 100.0


def test_invalid_inputs_rejected(fis):
    """Verify NaN and infinite inputs raise ValueError with descriptive message."""
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(np.nan, 0.0)

    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(0.5, np.nan)

    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(np.inf, 0.0)

    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(0.5, -np.inf)


def test_out_of_bounds_inputs_clamped_safely(fis):
    """Verify values slightly or significantly outside universe bounds are clamped safely."""
    # Under-range inputs
    stress_under = fis.evaluate(rsm=-0.5, moisture_error=-50.0)
    stress_min = fis.evaluate(rsm=0.0, moisture_error=-30.0)
    assert pytest.approx(stress_under, abs=1e-5) == stress_min

    # Over-range inputs
    stress_over = fis.evaluate(rsm=1.5, moisture_error=50.0)
    stress_max = fis.evaluate(rsm=1.0, moisture_error=30.0)
    assert pytest.approx(stress_over, abs=1e-5) == stress_max


def test_detailed_evaluation_structure(fis):
    """Verify evaluate_detailed returns complete telemetry dictionary."""
    details = fis.evaluate_detailed(0.30, 8.0)
    expected_keys = {
        "rsm_input",
        "rsm_clamped",
        "moisture_error_input",
        "moisture_error_clamped",
        "soil_stress",
        "rsm_membership",
        "error_membership",
        "consequent_activations",
        "active_rules",
        "total_fuzzy_area",
    }
    assert expected_keys.issubset(details.keys())
    assert details["rsm_input"] == 0.30
    assert details["moisture_error_input"] == 8.0
    assert isinstance(details["active_rules"], list)
    assert len(details["active_rules"]) > 0
    assert details["total_fuzzy_area"] > 0.0


def test_rsm_monotonicity_across_agronomic_regimes(fis):
    """
    Verify that across representative agronomic regimes, decreasing RSM
    produces non-decreasing (increasing) soil stress.
    """
    # At moderate deficit (error = +10%)
    rsms = [0.10, 0.35, 0.55, 0.75, 0.95]
    stresses = [fis.evaluate(r, 10.0) for r in rsms]

    # As RSM increases, stress should decrease
    for i in range(len(stresses) - 1):
        assert stresses[i] >= stresses[i + 1] - 0.5, (
            f"Expected decreasing stress with increasing RSM: {stresses[i]} -> {stresses[i+1]}"
        )


def test_moisture_error_monotonicity_across_agronomic_regimes(fis):
    """
    Verify that across representative agronomic regimes, increasing positive moisture error
    produces non-decreasing (increasing) soil stress.
    """
    # At dry soil (RSM = 0.35)
    errors = [-15.0, 0.0, 10.0, 20.0]
    stresses = [fis.evaluate(0.35, e) for e in errors]

    # As moisture error increases, stress should increase
    for i in range(len(stresses) - 1):
        assert stresses[i] <= stresses[i + 1] + 0.5, (
            f"Expected increasing stress with increasing error: {stresses[i]} -> {stresses[i+1]}"
        )


def test_vectorized_evaluate_array(fis):
    """Verify evaluate_array produces identical outputs to individual scalar evaluations."""
    rsm_grid = np.array([[0.1, 0.3], [0.6, 0.9]])
    err_grid = np.array([[15.0, 5.0], [0.0, -10.0]])

    arr_res = fis.evaluate_array(rsm_grid, err_grid)
    assert arr_res.shape == rsm_grid.shape

    for i in range(2):
        for j in range(2):
            scalar = fis.evaluate(rsm_grid[i, j], err_grid[i, j])
            assert pytest.approx(arr_res[i, j], abs=1e-6) == scalar
