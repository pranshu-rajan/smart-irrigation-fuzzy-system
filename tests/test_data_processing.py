"""Comprehensive unit tests for Phase 1 data processing and validation pipelines."""

import pytest
from pathlib import Path
import pandas as pd
import numpy as np

from data_processing.weather_preprocessor import WeatherPreprocessor
from data_processing.dataset_builder import DatasetBuilder
from data_processing.validator import DataValidator, ValidationReport, ValidationIssue
from config import load_config, get_default_zones, CropType, SoilType


@pytest.fixture
def sample_raw_weather_path(tmp_path: Path) -> Path:
    """Create a temporary raw weather CSV file with non-standard column names and an anomaly."""
    csv_content = (
        "RECORD_TIME,TEMP_2M_C,REL_HUM_PCT,SOLAR_RAD_WM2,WIND_SPEED_2M_MS,PRECIP_MM\n"
        "2026-06-01 02:00:00,18.5,85.0,0.0,1.5,0.0\n"
        "2026-06-01 01:00:00,19.0,84.0,0.0,1.6,0.0\n"  # Unsorted timestamp
        "2026-06-01 03:00:00,18.0,86.0,0.0,1.4,0.0\n"
        "2026-06-01 04:00:00,17.5,88.0,0.0,1.3,0.0\n"
        "2026-06-01 05:00:00,22.0,75.0,150.0,2.0,0.0\n"
    )
    file_path = tmp_path / "test_weather_raw.csv"
    file_path.write_text(csv_content, encoding="utf-8")
    return file_path


def test_crop_database_integrity():
    """Verify crop database exists, loads, and contains required crops with FAO-56 parameters."""
    crop_path = Path("data/crop_database.csv")
    assert crop_path.is_file(), "data/crop_database.csv does not exist"

    df = pd.read_csv(crop_path)
    report = DataValidator.validate_crop_database(df)
    assert report.is_valid, f"Crop database validation failed: {[i.message for i in report.issues]}"

    crops = set(df["crop"].unique())
    assert "Tomato" in crops
    assert "Wheat" in crops
    assert "Maize" in crops

    for _, row in df.iterrows():
        assert 0.1 <= row["kc_initial"] <= 1.5
        assert 0.5 <= row["kc_mid"] <= 2.0
        assert 0.1 <= row["kc_end"] <= 1.5
        assert row["root_depth_min_m"] <= row["root_depth_max_m"]


def test_soil_database_integrity():
    """Verify soil database exists, loads, and contains Loam, Sandy, and Clay with FC > WP."""
    soil_path = Path("data/soil_database.csv")
    assert soil_path.is_file(), "data/soil_database.csv does not exist"

    df = pd.read_csv(soil_path)
    report = DataValidator.validate_soil_database(df)
    assert report.is_valid, f"Soil database validation failed: {[i.message for i in report.issues]}"

    soils = set(df["soil_type"].unique())
    assert "Loam" in soils
    assert "Sandy" in soils
    assert "Clay" in soils

    for _, row in df.iterrows():
        assert row["field_capacity_pct"] > row["wilting_point_pct"]
        assert row["available_water_pct"] == pytest.approx(
            row["field_capacity_pct"] - row["wilting_point_pct"], abs=0.1
        )
        assert row["infiltration_rate_mm_h"] > 0.0


def test_zone_configuration_parameters():
    """Verify Section 6 model assumptions for the 3 agricultural zones."""
    zones = get_default_zones()
    assert len(zones) == 3

    # Zone 1
    z1 = zones[0]
    assert z1.crop.name == "Tomato"
    assert z1.soil.soil_type == SoilType.LOAM
    assert z1.soil.field_capacity == 70.0
    assert z1.soil.wilting_point == 25.0
    assert z1.initial_moisture == 55.0
    assert z1.target_moisture == 60.0

    # Zone 2
    z2 = zones[1]
    assert z2.crop.name == "Wheat"
    assert z2.soil.soil_type == SoilType.SANDY
    assert z2.soil.field_capacity == 60.0
    assert z2.soil.wilting_point == 18.0
    assert z2.initial_moisture == 42.0
    assert z2.target_moisture == 55.0

    # Zone 3
    z3 = zones[2]
    assert z3.crop.name == "Maize"
    assert z3.soil.soil_type == SoilType.CLAY
    assert z3.soil.field_capacity == 75.0
    assert z3.soil.wilting_point == 30.0
    assert z3.initial_moisture == 65.0
    assert z3.target_moisture == 65.0


def test_weather_preprocessor_workflow(sample_raw_weather_path: Path):
    """Verify loading, column renaming, sorting, and resampling in weather preprocessor."""
    preprocessor = WeatherPreprocessor(raw_path=sample_raw_weather_path)
    clean_df = preprocessor.process(interpolate_resolution=None)

    # Check standardized column names
    expected_cols = ["timestamp", "temperature", "humidity", "solar_radiation", "wind_speed", "rainfall"]
    for col in expected_cols:
        assert col in clean_df.columns

    # Check chronological sorting
    assert clean_df["timestamp"].is_monotonic_increasing

    # Check non-empty
    assert len(clean_df) == 5


def test_dataset_builder_multizone_structure():
    """Verify that dataset builder creates canonical columns and leaves downstream fields as NaN."""
    # Create simple 2-step weather dataframe
    weather_df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-06-01 00:00:00", "2026-06-01 01:00:00"]),
        "temperature": [20.0, 21.0],
        "humidity": [80.0, 75.0],
        "solar_radiation": [0.0, 50.0],
        "wind_speed": [1.5, 2.0],
        "rainfall": [0.0, 0.0],
    })

    builder = DatasetBuilder()
    unified = builder.build(weather_df)

    # 2 timestamps * 3 zones = 6 rows
    assert len(unified) == 6

    # Verify canonical schema columns
    for col in DatasetBuilder.CANONICAL_COLUMNS:
        assert col in unified.columns

    # Verify downstream uncalculated fields are strictly NaN
    for col in ["et0", "etc", "effective_rainfall", "moisture_error", "water_deficit", "available_water"]:
        assert unified[col].isna().all(), f"Field '{col}' should be NaN in Phase 1."


def test_data_validator_identifies_anomalies():
    """Verify that DataValidator catches invalid temperatures and impossible soil moisture."""
    invalid_weather = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-06-01 00:00:00"]),
        "temperature": [95.0],  # Out of physical bounds
        "humidity": [120.0],    # Impossible humidity > 100%
        "solar_radiation": [-5.0], # Impossible negative radiation
        "wind_speed": [2.0],
        "rainfall": [0.0],
    })

    report = DataValidator.validate_weather_dataset(invalid_weather)
    assert not report.is_valid
    assert report.error_count >= 3
