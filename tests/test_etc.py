"""Unit and agronomic tests for crop evapotranspiration (ETc) and crop water deficit engine.

Verifies:
- FAO-56 single crop coefficient lookup and phenological stage interpolation.
- Linearity of ETc = Kc * ET0.
- Effective rainfall hydrological retention (USDA-SCS and FAO empirical).
- Atmospheric crop water deficit D_crop = max(0, ETc - Peff).
- Multizone agronomic differentiation across Tomato, Wheat, and Maize.
"""

import pytest
import numpy as np
import pandas as pd

from models.etc import (
    CropCoefficientManager,
    calculate_etc,
    calculate_effective_rainfall,
    calculate_crop_water_deficit,
    calculate_water_deficit,
    compute_multizone_crop_demand,
)
from models.et0 import compute_et0_timeseries
from simulation.weather import WeatherEngine
from config.schemas import SimulationScenario, GrowthStage


def test_etc_scaling_with_kc():
    """Verify standard ETc = Kc * ET0 calculation."""
    et0 = 5.0
    kc = 1.15
    assert calculate_etc(et0, kc) == pytest.approx(5.75, abs=1e-4)

    # Zero ET0 yields zero ETc
    assert calculate_etc(0.0, 1.20) == 0.0

    # Non-negative enforcement
    assert calculate_etc(-2.0, 1.0) == 0.0


def test_crop_coefficient_manager_database_lookup():
    """Verify Kc lookups for standard crops from crop_database.csv."""
    # Tomato: ini=0.60, mid=1.15, end=0.80
    assert CropCoefficientManager.get_kc("Tomato", GrowthStage.INITIAL) == pytest.approx(0.60, abs=1e-3)
    assert CropCoefficientManager.get_kc("Tomato", GrowthStage.MID_SEASON) == pytest.approx(1.15, abs=1e-3)

    # Wheat: ini=0.30, mid=1.15, end=0.25
    assert CropCoefficientManager.get_kc("Wheat", GrowthStage.INITIAL) == pytest.approx(0.30, abs=1e-3)
    assert CropCoefficientManager.get_kc("Wheat", GrowthStage.MID_SEASON) == pytest.approx(1.15, abs=1e-3)

    # Maize: ini=0.30, mid=1.20, end=0.35
    assert CropCoefficientManager.get_kc("Maize", GrowthStage.INITIAL) == pytest.approx(0.30, abs=1e-3)
    assert CropCoefficientManager.get_kc("Maize", GrowthStage.MID_SEASON) == pytest.approx(1.20, abs=1e-3)


def test_crop_growth_stage_interpolation():
    """Verify linear interpolation during development and late-season stages."""
    # Wheat: ini=0.30, mid=1.15
    # At 50% development progress -> 0.30 + 0.5 * (1.15 - 0.30) = 0.725
    kc_dev_50 = CropCoefficientManager.get_kc("Wheat", GrowthStage.DEVELOPMENT, stage_progress=0.5)
    assert kc_dev_50 == pytest.approx(0.725, abs=1e-3)

    # At 0% development progress -> equals initial (0.30)
    kc_dev_0 = CropCoefficientManager.get_kc("Wheat", GrowthStage.DEVELOPMENT, stage_progress=0.0)
    assert kc_dev_0 == pytest.approx(0.30, abs=1e-3)

    # At 100% development progress -> equals mid-season (1.15)
    kc_dev_100 = CropCoefficientManager.get_kc("Wheat", GrowthStage.DEVELOPMENT, stage_progress=1.0)
    assert kc_dev_100 == pytest.approx(1.15, abs=1e-3)


def test_effective_rainfall_zero_and_light_precipitation():
    """Verify that zero rainfall and sub-threshold drizzles yield zero effective rainfall."""
    assert calculate_effective_rainfall(0.0) == 0.0

    # Sub-daily drizzle below threshold evaporates before entering root zone
    peff_drizzle = calculate_effective_rainfall(0.001, timestep_minutes=1)
    assert peff_drizzle == 0.0


def test_effective_rainfall_never_exceeds_raw_rainfall():
    """Verify physical law that Peff <= P across various intensities and methods."""
    for p in [0.5, 2.0, 10.0, 25.0, 60.0, 120.0]:
        peff_usda = calculate_effective_rainfall(p, method="usda_scs", timestep_minutes=1440)
        assert 0.0 <= peff_usda <= p

        peff_fao = calculate_effective_rainfall(p, method="fao_empirical", timestep_minutes=1440)
        assert 0.0 <= peff_fao <= p

        peff_pct = calculate_effective_rainfall(p, method="fixed_percentage", timestep_minutes=1440)
        assert 0.0 <= peff_pct <= p


def test_crop_water_deficit_calculation():
    """Verify crop water deficit D_crop = max(0, ETc - Peff)."""
    # High demand, low rain: ETc = 4.5 mm, Peff = 1.0 mm -> Deficit = 3.5 mm
    assert calculate_crop_water_deficit(4.5, 1.0) == pytest.approx(3.5, abs=1e-4)

    # Heavy rain exceeding demand: ETc = 3.0 mm, Peff = 15.0 mm -> Deficit = 0.0 mm
    assert calculate_crop_water_deficit(3.0, 15.0) == 0.0

    # Compatibility function returns identical deficit
    assert calculate_water_deficit(4.5, 1.0) == pytest.approx(3.5, abs=1e-4)


def test_multizone_crop_demand_pipeline():
    """Verify complete multizone crop demand evaluation across Zones 1, 2, and 3."""
    engine = WeatherEngine(scenario=SimulationScenario.NORMAL, seed=42)
    weather_df = engine.generate_timeline(duration_hours=24, timestep_minutes=1)
    et0_df = compute_et0_timeseries(weather_df, timestep_minutes=1)

    demand_df = compute_multizone_crop_demand(et0_df, timestep_minutes=1)

    # Check structure
    expected_cols = [
        "timestamp", "zone_id", "crop", "growth_stage", "kc", "et0",
        "etc", "rainfall", "effective_rainfall", "water_deficit"
    ]
    for col in expected_cols:
        assert col in demand_df.columns

    # 3 zones over 1440 steps = 4320 rows
    assert len(demand_df) == 1440 * 3
    assert set(demand_df["zone_id"].unique()) == {1, 2, 3}

    # Verify no missing data
    assert not demand_df.isna().any().any()

    # Zone-specific checks: Zone 3 (Maize, Kc=1.20) > Zone 1 (Tomato, Kc=1.15) > Zone 2 (Wheat, Kc=0.85)
    z1_etc = demand_df[demand_df["zone_id"] == 1]["etc"].sum()
    z2_etc = demand_df[demand_df["zone_id"] == 2]["etc"].sum()
    z3_etc = demand_df[demand_df["zone_id"] == 3]["etc"].sum()

    assert z3_etc > z1_etc > z2_etc, f"Zone ETc hierarchy violated: Z3={z3_etc}, Z1={z1_etc}, Z2={z2_etc}"
