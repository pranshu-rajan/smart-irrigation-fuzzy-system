"""
Unit and Integration Tests for Phase 8: Weather Stress Fuzzy Inference System (WeatherStressFIS).

Verifies:
1. WeatherStressFIS initialization and variable binding from central registry.
2. Part 15 critical sanity cases (Case 1 through Case 6).
3. Part 17 multi-variable interaction tests.
4. Part 16 5-dimensional monotonicity checks.
5. Strictly bounded crisp output in [0.0, 100.0]%.
6. Rejection of invalid inputs (NaN, +inf, -inf).
7. Safe clamping of out-of-universe boundary inputs.
8. Deterministic inference across multiple evaluations.
9. Detailed evaluation telemetry structure.
10. Vectorized evaluate_array matches scalar evaluation.
"""

import numpy as np
import pytest

from fuzzy_engine.weather_stress import WeatherStressFIS


@pytest.fixture
def fis():
    """Fixture providing a WeatherStressFIS instance."""
    return WeatherStressFIS()


def test_weather_stress_initialization(fis):
    """Verify WeatherStressFIS binds variables and initializes evaluation grid."""
    assert fis.temp_var.name == "temperature"
    assert fis.hum_var.name == "humidity"
    assert fis.solar_var.name == "solar_radiation"
    assert fis.wind_var.name == "wind_speed"
    assert fis.rain_var.name == "rainfall"
    assert fis.stress_var.name == "weather_stress"
    assert len(fis.RULES) == 34
    assert len(fis.z_grid) == 501
    assert fis.z_grid[0] == 0.0
    assert fis.z_grid[-1] == 100.0


def test_sanity_case_1_cool_humid(fis):
    """
    CASE 1: Cool & Humid (T=15°C, H=80%, S=100 W/m², W=2 m/s, R=0 mm).
    Expected: Low weather stress (< 25%).
    """
    stress = fis.evaluate(15.0, 80.0, 100.0, 2.0, 0.0)
    assert 0.0 <= stress <= 25.0, f"Expected low stress, got {stress}"


def test_sanity_case_2_normal_conditions(fis):
    """
    CASE 2: Normal Conditions (T=28°C, H=55%, S=500 W/m², W=3 m/s, R=0 mm).
    Expected: Low-to-moderate weather stress (30% - 60%).
    """
    stress = fis.evaluate(28.0, 55.0, 500.0, 3.0, 0.0)
    assert 30.0 <= stress <= 60.0, f"Expected moderate stress, got {stress}"


def test_sanity_case_3_hot_dry(fis):
    """
    CASE 3: Hot & Dry (T=38°C, H=25%, S=850 W/m², W=7 m/s, R=0 mm).
    Expected: High weather stress (> 65%).
    """
    stress = fis.evaluate(38.0, 25.0, 850.0, 7.0, 0.0)
    assert 65.0 <= stress <= 90.0, f"Expected high stress, got {stress}"


def test_sanity_case_4_extreme_hot_dry(fis):
    """
    CASE 4: Extreme Hot/Dry (T=45°C, H=12%, S=1050 W/m², W=12 m/s, R=0 mm).
    Expected: Very high weather stress (> 80%).
    """
    stress = fis.evaluate(45.0, 12.0, 1050.0, 12.0, 0.0)
    assert 80.0 <= stress <= 100.0, f"Expected very high stress, got {stress}"


def test_sanity_case_5_heavy_rain(fis):
    """
    CASE 5: Heavy Rain (T=30°C, H=85%, S=150 W/m², W=2 m/s, R=25 mm).
    Expected: Low weather stress (< 25%).
    """
    stress = fis.evaluate(30.0, 85.0, 150.0, 2.0, 25.0)
    assert 0.0 <= stress <= 25.0, f"Expected low stress with rain, got {stress}"


def test_sanity_case_6_rain_mitigation(fis):
    """
    CASE 6: Rain Mitigation.
    Evaluate same atmospheric condition twice: No Rain vs Heavy Rain.
    Expected: Stress(Rain) < Stress(No Rain).
    """
    stress_norain = fis.evaluate(38.0, 25.0, 850.0, 7.0, 0.0)
    stress_rain = fis.evaluate(38.0, 25.0, 850.0, 7.0, 25.0)
    assert stress_rain < stress_norain - 30.0, (
        f"Expected substantial rain relief: {stress_norain} -> {stress_rain}"
    )


def test_interaction_temp_with_humidity(fis):
    """Test interaction: high temperature with high humidity vs low humidity."""
    s_humid = fis.evaluate(38.0, 80.0, 500.0, 3.0, 0.0)
    s_dry = fis.evaluate(38.0, 20.0, 500.0, 3.0, 0.0)
    assert s_dry > s_humid + 30.0, "Dry air must produce significantly higher stress"


def test_interaction_solar_with_humidity(fis):
    """Test interaction: high solar with high humidity vs low humidity."""
    sol_humid = fis.evaluate(28.0, 80.0, 950.0, 3.0, 0.0)
    sol_dry = fis.evaluate(28.0, 20.0, 950.0, 3.0, 0.0)
    assert sol_dry > sol_humid + 30.0, "High solar with dry air must produce higher stress"


def test_interaction_wind_with_humidity(fis):
    """Test interaction: high wind in humid vs dry conditions."""
    w_humid = fis.evaluate(32.0, 80.0, 500.0, 10.0, 0.0)
    w_dry = fis.evaluate(32.0, 20.0, 500.0, 10.0, 0.0)
    assert w_dry > w_humid + 30.0, "High wind with dry air must accelerate stress"


def test_interaction_extreme_conditions_with_rain(fis):
    """Test interaction: extreme heatwave without rain vs with rain."""
    ext_norain = fis.evaluate(45.0, 15.0, 1050.0, 12.0, 0.0)
    ext_rain = fis.evaluate(45.0, 15.0, 1050.0, 12.0, 25.0)
    assert ext_norain > 80.0
    assert ext_rain < 30.0


def test_monotonicity_temperature(fis):
    """Holding other variables constant, increasing temperature must not decrease stress."""
    t_vals = [15.0, 25.0, 35.0, 45.0]
    stresses = [fis.evaluate(t, 40.0, 500.0, 3.0, 0.0) for t in t_vals]
    for i in range(len(stresses) - 1):
        assert stresses[i] <= stresses[i + 1] + 1e-4


def test_monotonicity_solar_radiation(fis):
    """Holding other variables constant, increasing solar radiation must not decrease stress."""
    s_vals = [100.0, 400.0, 800.0, 1100.0]
    stresses = [fis.evaluate(35.0, 35.0, s, 3.0, 0.0) for s in s_vals]
    for i in range(len(stresses) - 1):
        assert stresses[i] <= stresses[i + 1] + 1e-4


def test_monotonicity_wind_speed(fis):
    """Holding other variables constant, increasing wind speed must not decrease stress."""
    w_vals = [1.0, 4.0, 8.0, 13.0]
    stresses = [fis.evaluate(38.0, 25.0, 600.0, w, 0.0) for w in w_vals]
    for i in range(len(stresses) - 1):
        assert stresses[i] <= stresses[i + 1] + 1e-4


def test_monotonicity_humidity_inverse(fis):
    """Holding other variables constant, increasing humidity must not increase stress."""
    h_vals = [15.0, 35.0, 55.0, 75.0, 90.0]
    stresses = [fis.evaluate(35.0, h, 600.0, 4.0, 0.0) for h in h_vals]
    for i in range(len(stresses) - 1):
        assert stresses[i] >= stresses[i + 1] - 1e-4


def test_monotonicity_rainfall_inverse(fis):
    """Holding other variables constant, increasing rainfall must not increase stress."""
    r_vals = [0.0, 2.0, 8.0, 20.0, 40.0]
    stresses = [fis.evaluate(35.0, 35.0, 600.0, 4.0, r) for r in r_vals]
    for i in range(len(stresses) - 1):
        assert stresses[i] >= stresses[i + 1] - 1e-4


def test_output_bounds_and_determinism(fis):
    """Verify output is strictly in [0, 100] and identical across repeated calls."""
    res1 = fis.evaluate(30.0, 50.0, 600.0, 3.0, 0.0)
    res2 = fis.evaluate(30.0, 50.0, 600.0, 3.0, 0.0)
    assert res1 == res2
    assert 0.0 <= res1 <= 100.0


def test_invalid_inputs_rejected(fis):
    """Verify NaN and infinite inputs for any variable raise ValueError."""
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(np.nan, 50.0, 500.0, 3.0, 0.0)
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(30.0, np.nan, 500.0, 3.0, 0.0)
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(30.0, 50.0, np.nan, 3.0, 0.0)
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(30.0, 50.0, 500.0, np.nan, 0.0)
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(30.0, 50.0, 500.0, 3.0, np.nan)
    with pytest.raises(ValueError, match="cannot be NaN or infinite"):
        fis.evaluate(np.inf, 50.0, 500.0, 3.0, 0.0)


def test_out_of_bounds_inputs_clamped_safely(fis):
    """Verify out-of-universe inputs are safely clamped without throwing exceptions."""
    stress_under = fis.evaluate(5.0, -20.0, -100.0, -5.0, -10.0)
    stress_min = fis.evaluate(10.0, 0.0, 0.0, 0.0, 0.0)
    assert pytest.approx(stress_under, abs=1e-5) == stress_min

    stress_over = fis.evaluate(60.0, 120.0, 1500.0, 25.0, 80.0)
    stress_max = fis.evaluate(50.0, 100.0, 1200.0, 15.0, 50.0)
    assert pytest.approx(stress_over, abs=1e-5) == stress_max


def test_detailed_evaluation_structure(fis):
    """Verify evaluate_detailed returns complete telemetry dictionary."""
    details = fis.evaluate_detailed(32.0, 45.0, 700.0, 4.0, 0.0)
    expected_keys = {
        "temperature",
        "temperature_clamped",
        "humidity",
        "humidity_clamped",
        "solar_radiation",
        "solar_radiation_clamped",
        "wind_speed",
        "wind_speed_clamped",
        "rainfall",
        "rainfall_clamped",
        "weather_stress",
        "temperature_membership",
        "humidity_membership",
        "solar_radiation_membership",
        "wind_speed_membership",
        "rainfall_membership",
        "consequent_activations",
        "active_rules",
        "total_fuzzy_area",
    }
    assert expected_keys.issubset(details.keys())
    assert isinstance(details["active_rules"], list)
    assert len(details["active_rules"]) > 0
    assert details["total_fuzzy_area"] > 0.0


def test_vectorized_evaluate_array(fis):
    """Verify evaluate_array produces identical outputs to individual scalar evaluations."""
    t_arr = np.array([20.0, 35.0])
    h_arr = np.array([60.0, 30.0])
    s_arr = np.array([300.0, 800.0])
    w_arr = np.array([2.0, 6.0])
    r_arr = np.array([0.0, 0.0])

    arr_res = fis.evaluate_array(t_arr, h_arr, s_arr, w_arr, r_arr)
    assert arr_res.shape == t_arr.shape

    for i in range(len(t_arr)):
        scalar = fis.evaluate(t_arr[i], h_arr[i], s_arr[i], w_arr[i], r_arr[i])
        assert pytest.approx(arr_res[i], abs=1e-6) == scalar
