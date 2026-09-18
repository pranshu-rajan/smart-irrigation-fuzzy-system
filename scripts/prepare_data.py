#!/usr/bin/env python3
"""Data preparation CLI script.

Executes:
1. Preprocessing of raw meteorological records -> data/processed/weather_clean.csv
2. Building unified multizone dataset -> data/processed/irrigation_dataset.csv
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_processing.weather_preprocessor import WeatherPreprocessor
from data_processing.dataset_builder import DatasetBuilder


def main() -> int:
    print("=" * 70)
    print(" Smart Multizone Irrigation System - Data Preparation Pipeline")
    print("=" * 70)

    raw_weather = Path("data/raw/weather_raw.csv")
    clean_weather = Path("data/processed/weather_clean.csv")
    unified_dataset = Path("data/processed/irrigation_dataset.csv")

    # Step 1: Preprocess Weather
    print(f"\n[1/2] Preprocessing raw weather data from '{raw_weather}'...")
    preprocessor = WeatherPreprocessor(raw_path=raw_weather)
    preprocessor.process(interpolate_resolution="1min")
    preprocessor.save_clean(output_path=clean_weather)
    print(f"      -> Cleaned weather dataset saved to: {clean_weather}")
    print(f"      -> Total observation steps: {len(preprocessor.cleaned_df)}")

    # Step 2: Build Unified Multi-Zone Dataset
    print(f"\n[2/2] Synthesizing multizone dataset to '{unified_dataset}'...")
    builder = DatasetBuilder()
    builder.build_and_save(weather_path=clean_weather, output_path=unified_dataset)
    print(f"      -> Unified dataset successfully created at: {unified_dataset}")

    print("\n" + "=" * 70)
    print(" DATA PREPARATION COMPLETE")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
