"""Comprehensive unit test suite for Phase 3 Dynamic Weather Engine.

Tests:
1. Correct number of records (1440 for 24h at 1-min)
2. Correct timestep intervals (1 minute)
3. Monotonic chronological ordering
4. Complete non-null data integrity
5. Relative humidity within [0, 100]%
6. Solar radiation non-negative (>= 0 W/m2)
7. Wind speed non-negative (>= 0 m/s)
8. Rainfall non-negative (>= 0 mm)
9. Seed deterministic reproducibility
10. Stochastic variation across different seeds
11. Normal scenario characteristics
12. Hot & Dry scenario thermal elevation and drying
13. Rainy scenario precipitation generation and solar attenuation
14. Cloudy scenario diffuse radiation suppression
15. Heatwave scenario extreme temperatures (>40°C peak)
16. Water Scarcity scenario metadata restriction (WAF = 0.30)
17. 7-day simulation horizon scaling (10,080 steps)
18. 30-day simulation horizon scaling (43,200 steps)
19. Strict nighttime solar zeroing
20. No impossible boundary violations
"""

import pytest
import pandas as pd
import numpy as np

from config.schemas import SimulationScenario
from simulation.weather import WeatherEngine
from simulation.scenarios import ScenarioManager


@pytest.fixture
def default_engine() -> WeatherEngine:
    """Fixture providing baseline normal weather engine."""
    return WeatherEngine(scenario=SimulationScenario.NORMAL, seed=42)


# 1. Correct number of records
def test_weather_engine_step_count(default_engine: WeatherEngine):
    df = default_engine.generate_timeline(duration_hours=24, timestep_minutes=1)
    assert len(df) == 1440


# 2. Correct timestep resolution
def test_weather_engine_timestep_delta(default_engine: WeatherEngine):
    df = default_engine.generate_timeline(duration_hours=24, timestep_minutes=1)
    diffs = df["timestamp"].diff().dropna()
    assert (diffs == pd.Timedelta(minutes=1)).all()


# 3. Monotonic chronological ordering
def test_weather_engine_chronological_order(default_engine: WeatherEngine):
    df = default_engine.generate_timeline(duration_hours=24, timestep_minutes=1)
    assert df["timestamp"].is_monotonic_increasing


# 4. No missing values
def test_weather_engine_no_nulls(default_engine: WeatherEngine):
    df = default_engine.generate_timeline(duration_hours=24, timestep_minutes=1)
    assert df.isnull().sum().sum() == 0


# 5. Humidity within physical bounds [0, 100]%
def test_humidity_bounds(default_engine: WeatherEngine):
    df = default_engine.generate_timeline(duration_hours=24, timestep_minutes=1)
    assert df["humidity"].min() >= 0.0
    assert df["humidity"].max() <= 100.0


# 6. Solar radiation non-negative
def test_solar_radiation_non_negative(default_engine: WeatherEngine):
    df = default_engine.generate_timeline(duration_hours=24, timestep_minutes=1)
    assert (df["solar_radiation"] >= 0.0).all()


# 7. Wind speed non-negative
def test_wind_speed_non_negative(default_engine: WeatherEngine):
    df = default_engine.generate_timeline(duration_hours=24, timestep_minutes=1)
    assert (df["wind_speed"] >= 0.0).all()


# 8. Rainfall non-negative
def test_rainfall_non_negative():
    engine = WeatherEngine(scenario=SimulationScenario.RAINY, seed=42)
    df = engine.generate_timeline(duration_hours=24, timestep_minutes=1)
    assert (df["rainfall"] >= 0.0).all()


# 9. Seed reproducibility
def test_seed_reproducibility():
    e1 = WeatherEngine(scenario=SimulationScenario.NORMAL, seed=123)
    df1 = e1.generate_timeline(duration_hours=24, timestep_minutes=1)

    e2 = WeatherEngine(scenario=SimulationScenario.NORMAL, seed=123)
    df2 = e2.generate_timeline(duration_hours=24, timestep_minutes=1)

    pd.testing.assert_frame_equal(df1, df2)


# 10. Different seeds produce valid variation
def test_different_seeds_produce_variation():
    e1 = WeatherEngine(scenario=SimulationScenario.NORMAL, seed=10)
    df1 = e1.generate_timeline(duration_hours=24, timestep_minutes=1)

    e2 = WeatherEngine(scenario=SimulationScenario.NORMAL, seed=99)
    df2 = e2.generate_timeline(duration_hours=24, timestep_minutes=1)

    assert not df1["temperature"].equals(df2["temperature"])


# 11. Normal scenario generation
def test_normal_scenario_characteristics():
    engine = WeatherEngine(scenario=SimulationScenario.NORMAL, seed=42)
    df = engine.generate_timeline(duration_hours=24, timestep_minutes=1)
    assert df["scenario"].iloc[0] == "Normal"
    assert df["water_availability_factor"].iloc[0] == 1.0
    assert 17.0 <= df["temperature"].min() <= 20.0
    assert 32.0 <= df["temperature"].max() <= 36.0


# 12. Hot & Dry scenario
def test_hot_and_dry_scenario():
    normal_eng = WeatherEngine(scenario=SimulationScenario.NORMAL, seed=42)
    df_normal = normal_eng.generate_timeline(duration_hours=24, timestep_minutes=1)

    hot_eng = WeatherEngine(scenario=SimulationScenario.HOT_AND_DRY, seed=42)
    df_hot = hot_eng.generate_timeline(duration_hours=24, timestep_minutes=1)

    # Hot & Dry should have higher mean temp and lower mean humidity than Normal
    assert df_hot["temperature"].mean() > df_normal["temperature"].mean() + 4.0
    assert df_hot["humidity"].mean() < df_normal["humidity"].mean() - 15.0


# 13. Rainy scenario
def test_rainy_scenario():
    rain_eng = WeatherEngine(scenario=SimulationScenario.RAINY, seed=42)
    df_rain = rain_eng.generate_timeline(duration_hours=24, timestep_minutes=1)

    assert df_rain["rainfall"].sum() > 5.0  # Must have rain accumulation
    assert df_rain["humidity"].mean() > 80.0  # High relative humidity


# 14. Cloudy scenario
def test_cloudy_scenario():
    normal_eng = WeatherEngine(scenario=SimulationScenario.NORMAL, seed=42)
    df_normal = normal_eng.generate_timeline(duration_hours=24, timestep_minutes=1)

    cloudy_eng = WeatherEngine(scenario=SimulationScenario.CLOUDY, seed=42)
    df_cloudy = cloudy_eng.generate_timeline(duration_hours=24, timestep_minutes=1)

    # Solar peak must be attenuated compared to Normal
    assert df_cloudy["solar_radiation"].max() < df_normal["solar_radiation"].max() * 0.55


# 15. Heatwave scenario
def test_heatwave_scenario():
    hw_eng = WeatherEngine(scenario=SimulationScenario.HEATWAVE, seed=42)
    df_hw = hw_eng.generate_timeline(duration_hours=24, timestep_minutes=1)

    assert df_hw["temperature"].max() >= 40.0  # Extreme peak heat
    assert df_hw["humidity"].min() < 20.0     # Desiccating air


# 16. Water Scarcity scenario metadata
def test_water_scarcity_scenario():
    ws_eng = WeatherEngine(scenario=SimulationScenario.WATER_SCARCITY, seed=42)
    df_ws = ws_eng.generate_timeline(duration_hours=24, timestep_minutes=1)

    assert df_ws["scenario"].iloc[0] == "Water Scarcity"
    assert df_ws["water_availability_factor"].iloc[0] == 0.30  # Restricted budget


# 17. 7-day generation (10,080 steps)
def test_seven_day_generation():
    engine = WeatherEngine(scenario=SimulationScenario.NORMAL, seed=42)
    df_7d = engine.generate_timeline(duration_hours=168, timestep_minutes=1)
    assert len(df_7d) == 10080
    assert df_7d.isnull().sum().sum() == 0


# 18. 30-day generation (43,200 steps)
def test_thirty_day_generation():
    engine = WeatherEngine(scenario=SimulationScenario.NORMAL, seed=42)
    df_30d = engine.generate_timeline(duration_hours=720, timestep_minutes=1)
    assert len(df_30d) == 43200
    assert df_30d.isnull().sum().sum() == 0


# 19. Nighttime solar zeroing
def test_nighttime_solar_zeroing(default_engine: WeatherEngine):
    df = default_engine.generate_timeline(duration_hours=24, timestep_minutes=1)
    # Filter between 21:00 and 04:00
    night_mask = (df["timestamp"].dt.hour >= 21) | (df["timestamp"].dt.hour <= 4)
    assert (df.loc[night_mask, "solar_radiation"] == 0.0).all()


# 20. No impossible boundary violations
def test_no_boundary_violations():
    for sc in SimulationScenario:
        engine = WeatherEngine(scenario=sc, seed=42)
        df = engine.generate_timeline(duration_hours=24, timestep_minutes=1)
        assert -20.0 <= df["temperature"].min() and df["temperature"].max() <= 60.0
        assert 0.0 <= df["humidity"].min() and df["humidity"].max() <= 100.0
        assert df["solar_radiation"].min() >= 0.0
        assert df["wind_speed"].min() >= 0.0
        assert df["rainfall"].min() >= 0.0
