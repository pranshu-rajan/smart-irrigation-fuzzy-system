"""
Unit and Integration Tests for Phase 6: Fuzzy Variables, Universes, and Membership Functions.

Verifies:
1. All 19 fuzzy variables exist in the registry.
2. Universes have correct physical bounds, spans, and resolutions.
3. Triangular and trapezoidal membership mathematical functions.
4. Linguistic term sets exist with correct names and ordering.
5. Membership values strictly bounded in [0.0, 1.0].
6. Complete universe coverage without gaps.
7. Adjacent membership function overlap.
8. Boundary saturation at universe extrema.
9. Normalization, denormalization, and clamping behavior.
10. Error handling for NaN, Inf, and inverted parameter inputs.
11. Vectorized NumPy evaluation matches scalar evaluation.
12. 5 FIS architectural groupings and accessors.
"""

import numpy as np
import pytest

from fuzzy_engine import (
    FUZZY_VARIABLES,
    FIS_ARCHITECTURE,
    get_fuzzy_variable,
    get_variables_by_fis,
    list_variable_names,
    triangular_mf,
    trapezoidal_mf,
    FuzzyUniverse,
    MembershipSet,
    FuzzyVariable,
    ValidationError,
    validate_fuzzy_variable,
    validate_all_variables,
)


EXPECTED_VARIABLES = [
    # Soil Stress FIS
    "rsm", "moisture_error", "soil_stress",
    # Weather Stress FIS
    "temperature", "humidity", "solar_radiation", "wind_speed", "rainfall", "weather_stress",
    # Water Demand FIS
    "etc", "crop_water_deficit", "effective_rainfall", "water_demand",
    # Main Irrigation FIS
    "irrigation_command",
    # Water Allocation FIS
    "zone_demand", "zone_stress", "available_water", "zone_priority", "zone_allocation",
]


def test_registry_contains_all_nineteen_variables():
    """Verify registry contains all 19 required variables."""
    assert len(FUZZY_VARIABLES) == 19
    for var_name in EXPECTED_VARIABLES:
        assert var_name in FUZZY_VARIABLES, f"Missing variable: {var_name}"


def test_list_variable_names():
    """Verify list_variable_names returns exact registry keys."""
    names = list_variable_names()
    assert len(names) == 19
    for expected in EXPECTED_VARIABLES:
        assert expected in names


def test_get_fuzzy_variable_success_and_failure():
    """Test lookup helper with valid and invalid names."""
    var = get_fuzzy_variable("rsm")
    assert isinstance(var, FuzzyVariable)
    assert var.name == "rsm"

    with pytest.raises(KeyError, match="not found in registry"):
        get_fuzzy_variable("non_existent_var")


def test_fis_architecture_variable_groupings():
    """Verify all 5 FIS architectures correctly map their input/output variables."""
    assert len(FIS_ARCHITECTURE) == 5

    # 1. Soil Stress FIS
    ss_vars = get_variables_by_fis("soil_stress_fis")
    assert set(ss_vars.keys()) == {"rsm", "moisture_error", "soil_stress"}

    # 2. Weather Stress FIS
    ws_vars = get_variables_by_fis("weather_stress_fis")
    assert set(ws_vars.keys()) == {
        "temperature", "humidity", "solar_radiation", "wind_speed", "rainfall", "weather_stress"
    }

    # 3. Water Demand FIS
    wd_vars = get_variables_by_fis("water_demand_fis")
    assert set(wd_vars.keys()) == {"etc", "crop_water_deficit", "effective_rainfall", "water_demand"}

    # 4. Main Irrigation FIS
    mi_vars = get_variables_by_fis("main_irrigation_fis")
    assert set(mi_vars.keys()) == {
        "soil_stress", "weather_stress", "water_demand", "moisture_error", "irrigation_command"
    }

    # 5. Water Allocation FIS
    wa_vars = get_variables_by_fis("water_allocation_fis")
    assert set(wa_vars.keys()) == {
        "zone_demand", "zone_stress", "available_water", "zone_priority", "zone_allocation"
    }

    with pytest.raises(KeyError, match="Unknown FIS architecture"):
        get_variables_by_fis("non_existent_fis")


@pytest.mark.parametrize("var_name", EXPECTED_VARIABLES)
def test_all_fuzzy_variables_pass_validation(var_name):
    """Run rigorous 11-point mathematical validation across all 19 variables."""
    var = get_fuzzy_variable(var_name)
    summary = validate_fuzzy_variable(var)
    assert summary["valid"] is True
    assert len(summary["checks_passed"]) >= 8
    assert summary["min_sum_coverage"] >= 0.3


def test_triangular_mf_math_and_bounds():
    """Verify triangular membership function mathematical precision."""
    # Peak
    assert triangular_mf(5.0, 2.0, 5.0, 8.0) == 1.0
    # Left slope mid-point
    assert pytest.approx(triangular_mf(3.5, 2.0, 5.0, 8.0)) == 0.5
    # Right slope mid-point
    assert pytest.approx(triangular_mf(6.5, 2.0, 5.0, 8.0)) == 0.5
    # Out of bounds
    assert triangular_mf(1.0, 2.0, 5.0, 8.0) == 0.0
    assert triangular_mf(9.0, 2.0, 5.0, 8.0) == 0.0

    # Vectorized evaluation
    arr_x = np.array([1.0, 3.5, 5.0, 6.5, 9.0])
    expected = np.array([0.0, 0.5, 1.0, 0.5, 0.0])
    np.testing.assert_allclose(triangular_mf(arr_x, 2.0, 5.0, 8.0), expected)


def test_trapezoidal_mf_math_and_bounds():
    """Verify trapezoidal membership function mathematical precision."""
    # Plateau (core)
    assert trapezoidal_mf(3.0, 1.0, 3.0, 6.0, 8.0) == 1.0
    assert trapezoidal_mf(4.5, 1.0, 3.0, 6.0, 8.0) == 1.0
    assert trapezoidal_mf(6.0, 1.0, 3.0, 6.0, 8.0) == 1.0
    # Left slope mid-point
    assert pytest.approx(trapezoidal_mf(2.0, 1.0, 3.0, 6.0, 8.0)) == 0.5
    # Right slope mid-point
    assert pytest.approx(trapezoidal_mf(7.0, 1.0, 3.0, 6.0, 8.0)) == 0.5
    # Out of bounds
    assert trapezoidal_mf(0.5, 1.0, 3.0, 6.0, 8.0) == 0.0
    assert trapezoidal_mf(9.0, 1.0, 3.0, 6.0, 8.0) == 0.0

    # Vectorized evaluation
    arr_x = np.array([0.5, 2.0, 4.5, 7.0, 9.0])
    expected = np.array([0.0, 0.5, 1.0, 0.5, 0.0])
    np.testing.assert_allclose(trapezoidal_mf(arr_x, 1.0, 3.0, 6.0, 8.0), expected)


def test_membership_functions_invalid_parameters():
    """Verify ValueError is raised when parameters violate monotonicity."""
    with pytest.raises(ValueError, match="a <= b <= c"):
        triangular_mf(5.0, 5.0, 4.0, 6.0)

    with pytest.raises(ValueError, match="a <= b <= c <= d"):
        trapezoidal_mf(5.0, 1.0, 5.0, 4.0, 7.0)

    with pytest.raises(ValueError, match="NaN or Inf"):
        triangular_mf(np.nan, 1.0, 2.0, 3.0)

    with pytest.raises(ValueError, match="NaN or Inf"):
        trapezoidal_mf(np.inf, 1.0, 2.0, 3.0, 4.0)


def test_fuzzy_universe_normalization_and_denormalization():
    """Verify linear mapping to [0.0, 1.0] and inverse recovery."""
    univ = FuzzyUniverse(min_val=10.0, max_val=50.0)
    assert univ.range_span == 40.0

    # Exact boundary mapping
    assert univ.normalize(10.0) == 0.0
    assert univ.normalize(50.0) == 1.0
    assert univ.normalize(30.0) == 0.5

    # Clamping behavior for out-of-range values
    assert univ.normalize(5.0) == 0.0
    assert univ.normalize(60.0) == 1.0

    # Denormalization recovery
    assert univ.denormalize(0.0) == 10.0
    assert univ.denormalize(1.0) == 50.0
    assert univ.denormalize(0.5) == 30.0

    # Vectorized normalization
    arr = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    np.testing.assert_allclose(univ.normalize(arr), [0.0, 0.25, 0.5, 0.75, 1.0])

    # Rejection of invalid inputs
    with pytest.raises(ValueError, match="NaN or Inf"):
        univ.clamp(np.nan)
    with pytest.raises(ValueError, match="NaN or Inf"):
        univ.denormalize(np.nan)


def test_rsm_membership_engineering_rules():
    """Verify Relative Soil Moisture (RSM) semantic rules and boundaries."""
    rsm = get_fuzzy_variable("rsm")
    assert rsm.universe.min_val == 0.0
    assert rsm.universe.max_val == 1.0
    assert set(rsm.set_names) == {"very_dry", "dry", "adequate", "wet", "very_wet"}

    # At wilting point (0.0): Very Dry is 1.0
    eval_0 = rsm.evaluate(0.0)
    assert eval_0["very_dry"] == 1.0
    assert eval_0["adequate"] == 0.0

    # At field capacity (1.0): Very Wet is 1.0
    eval_1 = rsm.evaluate(1.0)
    assert eval_1["very_wet"] == 1.0
    assert eval_1["very_dry"] == 0.0

    # In optimal root zone (0.55): Adequate is dominant
    eval_opt = rsm.evaluate(0.55)
    assert eval_opt["adequate"] == 1.0
    assert eval_opt["very_dry"] == 0.0
    assert eval_opt["very_wet"] == 0.0


def test_moisture_error_sign_convention():
    """
    Verify moisture tracking error sign convention:
    e = target - current.
    e > 0 => deficit (Positive / Large Positive).
    e < 0 => excess (Negative / Large Negative).
    """
    err_var = get_fuzzy_variable("moisture_error")
    assert err_var.universe.min_val == -30.0
    assert err_var.universe.max_val == 30.0

    # Positive error (deficit)
    eval_pos = err_var.evaluate(15.0)
    assert eval_pos["positive"] > 0.0 or eval_pos["large_positive"] > 0.0
    assert eval_pos["negative"] == 0.0
    assert eval_pos["large_negative"] == 0.0

    # Negative error (excess)
    eval_neg = err_var.evaluate(-15.0)
    assert eval_neg["negative"] > 0.0 or eval_neg["large_negative"] > 0.0
    assert eval_neg["positive"] == 0.0
    assert eval_neg["large_positive"] == 0.0

    # Zero error
    eval_zero = err_var.evaluate(0.0)
    assert eval_zero["zero"] == 1.0


def test_weather_variables_engineering_ranges():
    """Verify meteorological universes match verified EDA physics."""
    temp = get_fuzzy_variable("temperature")
    assert temp.universe.min_val == 10.0 and temp.universe.max_val == 50.0

    hum = get_fuzzy_variable("humidity")
    assert hum.universe.min_val == 0.0 and hum.universe.max_val == 100.0

    rad = get_fuzzy_variable("solar_radiation")
    assert rad.universe.min_val == 0.0 and rad.universe.max_val == 1200.0

    wind = get_fuzzy_variable("wind_speed")
    assert wind.universe.min_val == 0.0 and wind.universe.max_val == 15.0

    rain = get_fuzzy_variable("rainfall")
    assert rain.universe.min_val == 0.0 and rain.universe.max_val == 50.0


def test_etc_and_water_demand_engineering_bounds():
    """Verify ETc and Crop Water Deficit engineering upper bound (15.0 mm/day)."""
    etc_var = get_fuzzy_variable("etc")
    assert etc_var.universe.min_val == 0.0
    assert etc_var.universe.max_val == 15.0

    cwd_var = get_fuzzy_variable("crop_water_deficit")
    assert cwd_var.universe.min_val == 0.0
    assert cwd_var.universe.max_val == 15.0

    erain_var = get_fuzzy_variable("effective_rainfall")
    assert erain_var.universe.min_val == 0.0
    assert erain_var.universe.max_val == 50.0


def test_command_and_allocation_normalized_ranges():
    """Verify control command and allocation outputs span [0.0, 100.0]%."""
    cmd = get_fuzzy_variable("irrigation_command")
    assert cmd.universe.min_val == 0.0 and cmd.universe.max_val == 100.0
    assert set(cmd.set_names) == {"off", "low", "moderate", "high", "maximum"}

    alloc = get_fuzzy_variable("zone_allocation")
    assert alloc.universe.min_val == 0.0 and alloc.universe.max_val == 100.0
    assert set(alloc.set_names) == {"none", "low", "moderate", "high", "maximum"}


def test_vectorized_and_scalar_evaluation_consistency():
    """Ensure array inputs produce identical results to individual scalar evaluations."""
    var = get_fuzzy_variable("temperature")
    pts = np.linspace(10.0, 50.0, 9)
    vector_res = var.evaluate(pts)

    for i, pt in enumerate(pts):
        scalar_res = var.evaluate(pt)
        for term in var.set_names:
            assert pytest.approx(scalar_res[term], abs=1e-7) == vector_res[term][i]
