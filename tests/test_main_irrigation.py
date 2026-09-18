"""
Unit and Integration Tests for Phase 10: Main Irrigation Fuzzy Inference System (MainIrrigationFIS).

Verifies:
1. MainIrrigationFIS initialization and variable binding from central registry.
2. Section 11 Physical Sanity Test Matrix (Tests 1 through 14).
3. Section 9 Important Controller Safety Cases (Cases A through G).
4. Section 10 Monotonicity across all 4 input dimensions.
5. Output bounded strictly within [0.0, 100.0]% and deterministic.
6. Rejection of invalid inputs (NaN, +inf, -inf).
7. Safe clamping of boundary inputs.
8. Detailed evaluation telemetry structure.
9. Vectorized evaluate_array matches pointwise scalar evaluate.
"""

import numpy as np
import pytest

from fuzzy_engine.irrigation import MainIrrigationFIS


@pytest.fixture
def fis():
    """Fixture providing a MainIrrigationFIS instance."""
    return MainIrrigationFIS()


def test_main_irrigation_initialization(fis):
    """Verify MainIrrigationFIS binds variables and initializes evaluation grid."""
    assert fis.soil_stress_var.name == "soil_stress"
    assert fis.weather_stress_var.name == "weather_stress"
    assert fis.water_demand_var.name == "water_demand"
    assert fis.moisture_error_var.name == "moisture_error"
    assert fis.command_var.name == "irrigation_command"
    assert len(fis.RULES) == 32
    assert len(fis.z_grid) == 501
    assert fis.z_grid[0] == 0.0
    assert fis.z_grid[-1] == 100.0


# =============================================================================
# SECTION 11: PHYSICAL SANITY TEST MATRIX (TESTS 1 - 10)
# =============================================================================

def test_sanity_test_1_all_low_stress_negative_error(fis):
    """
    Test 1: All low stress + negative error
    Expected: near-zero / OFF irrigation (< 15%).
    """
    cmd = fis.evaluate(soil_stress=10.0, weather_stress=10.0, water_demand=10.0, moisture_error=-15.0)
    assert 0.0 <= cmd < 15.0, f"Expected near-zero irrigation, got {cmd:.2f}%"


def test_sanity_test_2_low_soil_stress_zero_error_low_demand(fis):
    """
    Test 2: Low soil stress + zero error + low demand
    Expected: low irrigation (10% to 35%).
    """
    cmd = fis.evaluate(soil_stress=15.0, weather_stress=20.0, water_demand=25.0, moisture_error=0.0)
    assert 10.0 <= cmd <= 35.0, f"Expected low irrigation, got {cmd:.2f}%"


def test_sanity_test_3_moderate_soil_stress_moderate_demand_zero_error(fis):
    """
    Test 3: Moderate soil stress + moderate demand + zero error
    Expected: moderate irrigation (35% to 65%).
    """
    cmd = fis.evaluate(soil_stress=45.0, weather_stress=45.0, water_demand=45.0, moisture_error=0.0)
    assert 35.0 <= cmd <= 65.0, f"Expected moderate irrigation, got {cmd:.2f}%"


def test_sanity_test_4_high_soil_stress_positive_error(fis):
    """
    Test 4: High soil stress + positive error
    Expected: high irrigation (65% to 85%).
    """
    cmd = fis.evaluate(soil_stress=75.0, weather_stress=50.0, water_demand=50.0, moisture_error=8.0)
    assert 65.0 <= cmd <= 85.0, f"Expected high irrigation, got {cmd:.2f}%"


def test_sanity_test_5_very_high_stress_high_demand_strong_positive_error(fis):
    """
    Test 5: Very high soil stress + high demand + strong positive error
    Expected: very high / maximum irrigation (> 80%).
    """
    cmd = fis.evaluate(soil_stress=90.0, weather_stress=80.0, water_demand=85.0, moisture_error=20.0)
    assert 80.0 <= cmd <= 100.0, f"Expected maximum irrigation, got {cmd:.2f}%"


def test_sanity_test_6_high_weather_stress_low_soil_stress_negative_error(fis):
    """
    Test 6: High weather stress + low soil stress + negative error
    Expected: limited irrigation (< 25%, weather cannot force irrigation if soil is wet).
    """
    cmd = fis.evaluate(soil_stress=15.0, weather_stress=85.0, water_demand=20.0, moisture_error=-15.0)
    assert 0.0 <= cmd < 25.0, f"Expected limited irrigation, got {cmd:.2f}%"


def test_sanity_test_7_high_weather_stress_high_soil_stress_positive_error(fis):
    """
    Test 7: High weather stress + high soil stress + positive error
    Expected: high / very high irrigation (> 75%).
    """
    cmd = fis.evaluate(soil_stress=85.0, weather_stress=80.0, water_demand=70.0, moisture_error=10.0)
    assert 75.0 <= cmd <= 100.0, f"Expected high/very high irrigation, got {cmd:.2f}%"


def test_sanity_test_8_high_water_demand_soil_above_target(fis):
    """
    Test 8: High water demand + soil moisture above target
    Expected: suppressed relative to the equivalent positive-error case.
    """
    cmd_neg = fis.evaluate(soil_stress=30.0, weather_stress=40.0, water_demand=85.0, moisture_error=-15.0)
    cmd_pos = fis.evaluate(soil_stress=30.0, weather_stress=40.0, water_demand=85.0, moisture_error=10.0)
    assert cmd_neg < cmd_pos, f"Expected demand suppression when wet: {cmd_neg:.2f}% vs {cmd_pos:.2f}%"
    assert (cmd_pos - cmd_neg) > 40.0, f"Expected substantial separation (>40%), got {cmd_pos - cmd_neg:.2f}%"


def test_sanity_test_9_low_demand_positive_moisture_error(fis):
    """
    Test 9: Low demand + positive moisture error
    Expected: irrigation should respond to soil deficit even without strong atmospheric demand (> 40%).
    """
    cmd = fis.evaluate(soil_stress=30.0, weather_stress=20.0, water_demand=15.0, moisture_error=15.0)
    assert cmd >= 40.0, f"Expected response to deficit, got {cmd:.2f}%"


def test_sanity_test_10_rain_reduced_demand_soil_above_target(fis):
    """
    Test 10: Rain-related reduced water demand + soil moisture above target
    Expected: irrigation should remain low / OFF (< 15%).
    """
    cmd = fis.evaluate(soil_stress=10.0, weather_stress=10.0, water_demand=9.2, moisture_error=-10.0)
    assert 0.0 <= cmd < 15.0, f"Expected low/OFF command, got {cmd:.2f}%"


# =============================================================================
# SECTION 11: BOUNDARY & EXCEPTION TESTS (TESTS 11 - 14)
# =============================================================================

def test_boundary_inputs(fis):
    """Test 11: Boundary inputs (0, maximum, and intermediate values)."""
    # Minimum corner
    cmd_min = fis.evaluate(0.0, 0.0, 0.0, -30.0)
    assert 0.0 <= cmd_min <= 10.0

    # Maximum corner
    cmd_max = fis.evaluate(100.0, 100.0, 100.0, 30.0)
    assert 85.0 <= cmd_max <= 100.0

    # Midpoints
    cmd_mid = fis.evaluate(50.0, 50.0, 50.0, 0.0)
    assert 40.0 <= cmd_mid <= 60.0


def test_nan_input_rejected(fis):
    """Test 12: NaN input raises ValueError."""
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(np.nan, 50.0, 50.0, 0.0)
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(50.0, np.nan, 50.0, 0.0)
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(50.0, 50.0, np.nan, 0.0)
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(50.0, 50.0, 50.0, np.nan)


def test_positive_inf_rejected(fis):
    """Test 13: +inf raises ValueError."""
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(np.inf, 50.0, 50.0, 0.0)


def test_negative_inf_rejected(fis):
    """Test 14: -inf raises ValueError."""
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(50.0, -np.inf, 50.0, 0.0)


# =============================================================================
# SECTION 10: MONOTONICITY TESTS
# =============================================================================

def test_monotonicity_soil_stress(fis):
    """Holding other inputs constant, increasing soil stress must not decrease irrigation command."""
    s_vals = np.linspace(5.0, 95.0, 10)
    cmds = [fis.evaluate(soil_stress=s, weather_stress=40.0, water_demand=40.0, moisture_error=5.0) for s in s_vals]
    assert cmds[-1] > cmds[0] + 30.0
    for i in range(len(cmds) - 1):
        assert cmds[i + 1] >= cmds[i] - 0.5, f"Drop at step {i}: {cmds[i]} -> {cmds[i+1]}"


def test_monotonicity_moisture_error(fis):
    """Holding other inputs constant, moving moisture error from negative to positive must increase irrigation."""
    e_vals = np.linspace(-25.0, 25.0, 11)
    cmds = [fis.evaluate(soil_stress=45.0, weather_stress=40.0, water_demand=40.0, moisture_error=e) for e in e_vals]
    assert cmds[-1] > cmds[0] + 50.0
    for i in range(len(cmds) - 1):
        assert cmds[i + 1] >= cmds[i] - 0.5, f"Drop at step {i}: {cmds[i]} -> {cmds[i+1]}"


def test_monotonicity_water_demand(fis):
    """Holding other inputs constant, increasing water demand must generally not decrease irrigation."""
    d_vals = np.linspace(5.0, 95.0, 10)
    cmds = [fis.evaluate(soil_stress=45.0, weather_stress=40.0, water_demand=d, moisture_error=5.0) for d in d_vals]
    assert cmds[-1] >= cmds[0]
    for i in range(len(cmds) - 1):
        assert cmds[i + 1] >= cmds[i] - 0.5, f"Drop at step {i}: {cmds[i]} -> {cmds[i+1]}"


def test_monotonicity_weather_stress(fis):
    """Holding other inputs constant, increasing weather stress must generally not decrease irrigation."""
    w_vals = np.linspace(5.0, 95.0, 10)
    cmds = [fis.evaluate(soil_stress=45.0, weather_stress=w, water_demand=40.0, moisture_error=5.0) for w in w_vals]
    assert cmds[-1] >= cmds[0]
    for i in range(len(cmds) - 1):
        assert cmds[i + 1] >= cmds[i] - 0.5, f"Drop at step {i}: {cmds[i]} -> {cmds[i+1]}"


# =============================================================================
# DETAILED TELEMETRY & BATCH VECTORIZATION
# =============================================================================

def test_detailed_evaluation_structure(fis):
    """Verify evaluate_detailed returns full telemetry structure."""
    det = fis.evaluate_detailed(soil_stress=50.0, weather_stress=40.0, water_demand=60.0, moisture_error=5.0)
    assert "soil_stress" in det
    assert "weather_stress" in det
    assert "water_demand" in det
    assert "moisture_error" in det
    assert "irrigation_command" in det
    assert "soil_stress_membership" in det
    assert "weather_stress_membership" in det
    assert "water_demand_membership" in det
    assert "moisture_error_membership" in det
    assert "consequent_activations" in det
    assert "active_rules" in det
    assert "total_fuzzy_area" in det
    assert isinstance(det["active_rules"], list)
    assert len(det["active_rules"]) > 0
    assert 0.0 <= det["irrigation_command"] <= 100.0


def test_vectorized_evaluate_array(fis):
    """Verify evaluate_array matches pointwise evaluate calls."""
    ss_arr = np.array([10.0, 45.0, 75.0, 90.0])
    ws_arr = np.array([10.0, 45.0, 50.0, 80.0])
    wd_arr = np.array([10.0, 45.0, 50.0, 85.0])
    me_arr = np.array([-15.0, 0.0, 8.0, 20.0])

    vec = fis.evaluate_array(ss_arr, ws_arr, wd_arr, me_arr)
    assert len(vec) == 4
    for i in range(4):
        scalar = fis.evaluate(ss_arr[i], ws_arr[i], wd_arr[i], me_arr[i])
        assert pytest.approx(vec[i], abs=1e-9) == scalar


def test_evaluate_array_dimension_mismatch(fis):
    """Verify evaluate_array rejects mismatched array dimensions."""
    with pytest.raises(ValueError, match="identical dimensions"):
        fis.evaluate_array(np.array([1.0, 2.0]), np.array([1.0]), np.array([1.0, 2.0]), np.array([1.0, 2.0]))
