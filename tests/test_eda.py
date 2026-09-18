"""Unit tests for Phase 2 Exploratory Data Analysis (EDA) module."""

import pytest
from pathlib import Path
import pandas as pd
import numpy as np

from analysis.eda_weather import WeatherEDA
from analysis.eda_agriculture import AgricultureEDA
from analysis.eda_multizone import MultizoneEDA
from analysis.generate_eda_report import generate_all_eda


def test_weather_eda_summary_statistics():
    """Verify statistical summary metrics calculated on cleaned weather dataset."""
    eda = WeatherEDA()
    stats = eda.compute_summary_statistics()

    assert isinstance(stats, pd.DataFrame)
    assert len(stats) == 5  # temp, hum, solar, wind, rain

    for _, row in stats.iterrows():
        assert row["count"] == 1441
        assert row["min"] <= row["median"] <= row["max"]
        assert row["p05"] <= row["p25"] <= row["p75"] <= row["p95"]
        assert row["missing"] == 0


def test_weather_eda_correlations():
    """Verify pairwise correlation properties."""
    eda = WeatherEDA()
    corr = eda.compute_correlations(drop_constant=True)

    assert isinstance(corr, pd.DataFrame)
    assert len(corr.columns) >= 4  # temp, hum, solar, wind
    # Check diagonal is 1.0
    for col in corr.columns:
        assert corr.loc[col, col] == pytest.approx(1.0, abs=1e-5)

    # Temperature and humidity must be strongly inversely correlated
    assert corr.loc["temperature", "humidity"] < -0.80

    # Temperature and solar radiation must be positively correlated
    assert corr.loc["temperature", "solar_radiation"] > 0.50


def test_agriculture_eda_summaries():
    """Verify agronomic and pedological metrics."""
    eda = AgricultureEDA()
    crops = eda.summarize_crops()
    soils = eda.summarize_soils()

    assert len(crops) >= 12
    assert len(soils) >= 3

    # Soil AWC check
    for _, row in soils.iterrows():
        assert row["field_capacity_pct"] > row["wilting_point_pct"]
        assert row["calculated_awc_pct"] == pytest.approx(
            row["field_capacity_pct"] - row["wilting_point_pct"], abs=1e-3
        )


def test_multizone_eda_rsm_and_error():
    """Verify Relative Soil Moisture and tracking error calculations."""
    eda = MultizoneEDA()
    zone_table = eda.generate_zone_comparison_table()

    assert len(zone_table) == 3

    # Zone 1: Tomato / Loam: FC=70, WP=25, SM0=55, Target=60
    # RSM = (55 - 25) / (70 - 25) = 30 / 45 = 0.6667
    # Error = 60 - 55 = +5.0
    z1 = zone_table[zone_table["zone_id"] == 1].iloc[0]
    assert z1["initial_rsm"] == pytest.approx(0.6667, abs=1e-3)
    assert z1["initial_moisture_error"] == pytest.approx(5.0, abs=1e-3)

    # Zone 2: Wheat / Sandy: FC=60, WP=18, SM0=42, Target=55
    # RSM = (42 - 18) / (60 - 18) = 24 / 42 = 0.5714
    # Error = 55 - 42 = +13.0
    z2 = zone_table[zone_table["zone_id"] == 2].iloc[0]
    assert z2["initial_rsm"] == pytest.approx(0.5714, abs=1e-3)
    assert z2["initial_moisture_error"] == pytest.approx(13.0, abs=1e-3)

    # Zone 3: Maize / Clay: FC=75, WP=30, SM0=65, Target=65
    # RSM = (65 - 30) / (75 - 30) = 35 / 45 = 0.7778
    # Error = 65 - 65 = 0.0
    z3 = zone_table[zone_table["zone_id"] == 3].iloc[0]
    assert z3["initial_rsm"] == pytest.approx(0.7778, abs=1e-3)
    assert z3["initial_moisture_error"] == pytest.approx(0.0, abs=1e-3)


def test_generate_all_eda_pipeline(tmp_path: Path):
    """Verify end-to-end report and plot generation into temporary test directory."""
    fig_dir = tmp_path / "figures"
    report_file = tmp_path / "TEST_EDA_REPORT.md"

    generate_all_eda(figures_dir=fig_dir, report_path=report_file)

    assert report_file.is_file()
    content = report_file.read_text(encoding="utf-8")
    assert "# Exploratory Data Analysis (EDA) Report" in content
    assert "Relative Soil Moisture" in content

    # Check generated figures
    assert (fig_dir / "weather" / "temperature_distribution.png").is_file()
    assert (fig_dir / "weather" / "weather_timeline_24h.png").is_file()
    assert (fig_dir / "weather" / "correlation_heatmap.png").is_file()
    assert (fig_dir / "agriculture" / "crop_kc_comparison.png").is_file()
    assert (fig_dir / "agriculture" / "soil_water_retention_awc.png").is_file()
    assert (fig_dir / "agriculture" / "zone_moisture_targets.png").is_file()
