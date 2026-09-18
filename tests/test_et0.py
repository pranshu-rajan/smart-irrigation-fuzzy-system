"""Unit and validation tests for FAO-56 Penman-Monteith ET0 engine.

Verifies mathematical formulas against published FAO-56 benchmark values and ensures
physical boundary adherence across atmospheric, radiation, and energy components.
"""

import pytest
import numpy as np
import pandas as pd

from models.et0 import (
    calculate_atmospheric_pressure,
    calculate_psychrometric_constant,
    calculate_saturation_vapor_pressure,
    calculate_actual_vapor_pressure,
    calculate_vpd,
    calculate_slope_vapor_pressure_curve,
    convert_wind_height,
    calculate_extraterrestrial_radiation_hourly,
    calculate_clear_sky_radiation,
    calculate_net_shortwave_radiation,
    calculate_net_longwave_radiation,
    calculate_net_radiation,
    calculate_soil_heat_flux,
    calculate_et0_fao56,
    compute_et0_timeseries,
)
from simulation.weather import WeatherEngine
from config.schemas import SimulationScenario


def test_atmospheric_pressure_sea_level_and_elevation():
    """Verify atmospheric pressure against FAO-56 Example 5 (elevation 1800m)."""
    # Sea level (z = 0 m)
    p_sea = calculate_atmospheric_pressure(0.0)
    assert p_sea == pytest.approx(101.3, abs=0.1)

    # FAO-56 Example 5 benchmark: elevation z = 1800 m -> P ≈ 81.8 kPa
    p_1800 = calculate_atmospheric_pressure(1800.0)
    assert p_1800 == pytest.approx(81.8, abs=0.2)

    # Station elevation Ahmedabad (z = 53 m)
    p_53 = calculate_atmospheric_pressure(53.0)
    assert 100.0 < p_53 < 101.3


def test_psychrometric_constant_fao56_benchmark():
    """Verify psychrometric constant gamma against FAO-56 Example 5."""
    # At sea level (101.3 kPa) -> gamma ≈ 0.0673 kPa/°C
    gamma_sea = calculate_psychrometric_constant(101.3)
    assert gamma_sea == pytest.approx(0.0673, abs=0.001)

    # FAO-56 Example 5 benchmark: P = 81.8 kPa -> gamma ≈ 0.054 kPa/°C
    gamma_1800 = calculate_psychrometric_constant(81.8)
    assert gamma_1800 == pytest.approx(0.0544, abs=0.001)


def test_saturation_vapor_pressure_fao56_values():
    """Verify saturation vapour pressure against standard thermodynamic tables."""
    # At 0°C -> es ≈ 0.6108 kPa
    es_0 = calculate_saturation_vapor_pressure(0.0)
    assert es_0 == pytest.approx(0.6108, abs=0.001)

    # At 25°C -> es ≈ 3.167 kPa (FAO-56 Annex 2 Table 2.3)
    es_25 = calculate_saturation_vapor_pressure(25.0)
    assert es_25 == pytest.approx(3.167, abs=0.01)

    # At 38°C -> es ≈ 6.63 kPa (FAO-56 Example 18)
    es_38 = calculate_saturation_vapor_pressure(38.0)
    assert es_38 == pytest.approx(6.63, abs=0.05)


def test_actual_vapor_pressure_and_vpd():
    """Verify actual vapour pressure and VPD behaviour."""
    # 25°C at 60% RH -> es ≈ 3.167, ea ≈ 1.900, VPD ≈ 1.267
    ea = calculate_actual_vapor_pressure(25.0, 60.0)
    assert ea == pytest.approx(1.900, abs=0.02)

    vpd = calculate_vpd(25.0, 60.0)
    assert vpd == pytest.approx(1.267, abs=0.02)

    # At 100% RH, VPD must be exactly 0.0
    vpd_sat = calculate_vpd(20.0, 100.0)
    assert vpd_sat == pytest.approx(0.0, abs=1e-5)

    # At 0% RH, VPD equals saturation vapour pressure
    vpd_dry = calculate_vpd(25.0, 0.0)
    assert vpd_dry == pytest.approx(calculate_saturation_vapor_pressure(25.0), abs=1e-5)


def test_slope_vapor_pressure_curve():
    """Verify slope Delta curve at benchmark temperatures."""
    # At 25°C -> Delta ≈ 0.1886 kPa/°C
    delta_25 = calculate_slope_vapor_pressure_curve(25.0)
    assert delta_25 == pytest.approx(0.1886, abs=0.002)

    # At 38°C -> Delta ≈ 0.358 kPa/°C (FAO-56 Example 18)
    delta_38 = calculate_slope_vapor_pressure_curve(38.0)
    assert delta_38 == pytest.approx(0.358, abs=0.01)

    # Slope must be strictly positive and monotonic with temperature
    assert calculate_slope_vapor_pressure_curve(10.0) < calculate_slope_vapor_pressure_curve(30.0)


def test_wind_speed_height_conversion():
    """Verify 2m wind speed passthrough and log wind profile conversion."""
    # At 2m measurement height, u2 == uz
    assert convert_wind_height(2.5, 2.0) == 2.5

    # Measured at 10m height, u2 should be less than u10 (standard ~0.75 ratio)
    u2_from_10 = convert_wind_height(4.0, 10.0)
    assert 2.8 < u2_from_10 < 3.2


def test_net_shortwave_radiation():
    """Verify net shortwave radiation with reference grass albedo (0.23)."""
    # Rns = (1 - 0.23) * Rs = 0.77 * Rs
    assert calculate_net_shortwave_radiation(10.0, 0.23) == pytest.approx(7.7, abs=1e-4)
    assert calculate_net_shortwave_radiation(0.0) == 0.0


def test_net_radiation_day_night():
    """Verify that net radiation is positive during sunlit day and negative at night."""
    # Daytime: 800 W/m2 at noon
    rn_day, rns_day, rnl_day = calculate_net_radiation(
        solar_radiation_wm2=800.0,
        temperature_c=30.0,
        humidity_percent=50.0,
        timestep_minutes=60,
        hour_of_day=12.0,
    )
    assert rns_day > rnl_day
    assert rn_day > 0.0

    # Nighttime: 0 W/m2 at midnight -> Rn < 0
    rn_night, rns_night, rnl_night = calculate_net_radiation(
        solar_radiation_wm2=0.0,
        temperature_c=18.0,
        humidity_percent=80.0,
        timestep_minutes=60,
        hour_of_day=0.0,
    )
    assert rns_night == 0.0
    assert rnl_night > 0.0
    assert rn_night < 0.0  # Net thermal radiation emission into space


def test_soil_heat_flux_formulation():
    """Verify soil heat flux density G rules according to FAO-56 Eq. 42, 45, 46."""
    # Daily aggregation G = 0
    assert calculate_soil_heat_flux(15.0, daily=True) == 0.0

    # Sub-daily daytime (Rn > 0): G = 0.10 * Rn
    assert calculate_soil_heat_flux(2.0, is_daylight=True) == pytest.approx(0.20, abs=1e-4)

    # Sub-daily nighttime (Rn < 0): G = 0.50 * Rn
    assert calculate_soil_heat_flux(-0.4, is_daylight=False) == pytest.approx(-0.20, abs=1e-4)


def test_daily_et0_fao56_magnitude():
    """Verify daily ET0 calculation under typical summer conditions."""
    # Typical warm summer day: T=28°C, RH=50%, daily mean Solar=250 W/m2 (21.6 MJ/m2/day), Wind=2.5 m/s
    et0_daily = calculate_et0_fao56(
        temperature_c=28.0,
        humidity_percent=50.0,
        solar_radiation_wm2=250.0,
        wind_speed_ms=2.5,
        timestep_minutes=1440,
    )
    assert isinstance(et0_daily, float)
    # Standard agricultural ET0 falls within 4 to 9 mm/day
    assert 4.0 <= et0_daily <= 9.0


def test_nighttime_zero_solar_et0_safety():
    """Verify numerical safety and non-negativity at night (zero solar radiation)."""
    et0_night = calculate_et0_fao56(
        temperature_c=18.0,
        humidity_percent=85.0,
        solar_radiation_wm2=0.0,
        wind_speed_ms=1.5,
        timestep_minutes=1,
        hour_of_day=2.0,
        as_step_depth=True,
    )
    assert isinstance(et0_night, float)
    assert et0_night >= 0.0
    assert not np.isnan(et0_night)


def test_compute_et0_timeseries_structure_and_bounds():
    """Verify timeseries generation over full 24-hour weather dataframe."""
    engine = WeatherEngine(scenario=SimulationScenario.NORMAL, seed=42)
    weather_df = engine.generate_timeline(duration_hours=24, timestep_minutes=1)

    et0_df = compute_et0_timeseries(weather_df, timestep_minutes=1)

    # Verify column presence
    expected_cols = [
        "timestamp", "temperature", "humidity", "solar_radiation", "wind_speed", "rainfall",
        "atmospheric_pressure", "saturation_vapor_pressure", "actual_vapor_pressure", "vpd",
        "delta", "gamma", "net_shortwave_radiation", "net_longwave_radiation", "net_radiation",
        "soil_heat_flux", "et0", "et0_rate_mm_day"
    ]
    for col in expected_cols:
        assert col in et0_df.columns, f"Missing required column: {col}"

    # Verify no NaNs or Infs
    assert not et0_df.isna().any().any(), "NaN values detected in et0_df"
    assert not np.isinf(et0_df["et0"]).any(), "Infinite values detected in et0"

    # Verify ET0 non-negativity
    assert (et0_df["et0"] >= 0.0).all()
    assert (et0_df["vpd"] >= 0.0).all()

    # Verify daily accumulated ET0 is within realistic physiological envelope (3 to 8 mm/day)
    total_daily_et0 = et0_df["et0"].sum()
    assert 3.0 <= total_daily_et0 <= 8.0, f"Total daily ET0 {total_daily_et0} mm outside expected range"
