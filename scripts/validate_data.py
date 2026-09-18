#!/usr/bin/env python3
"""Data validation CLI script.

Executes physical, agronomic, and temporal verification across:
1. data/crop_database.csv
2. data/soil_database.csv
3. data/processed/weather_clean.csv
4. data/processed/irrigation_dataset.csv
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_processing.validator import DataValidator


def main() -> int:
    print("=" * 70)
    print(" Smart Multizone Irrigation System - Data Integrity Validator")
    print("=" * 70)

    all_passed = True

    # 1. Validate Crop Database
    crop_path = Path("data/crop_database.csv")
    print(f"\n[1/4] Validating Crop Database ({crop_path})...")
    if crop_path.is_file():
        crop_df = pd.read_csv(crop_path)
        crop_report = DataValidator.validate_crop_database(crop_df)
        print(f"      Status: {'PASSED' if crop_report.is_valid else 'FAILED'}")
        print(f"      Records: {crop_report.total_records}, Errors: {crop_report.error_count}, Warnings: {crop_report.warning_count}")
        if not crop_report.is_valid:
            all_passed = False
            for err in crop_report.issues:
                print(f"      -> {err.severity}: {err.message}")
    else:
        print(f"      ERROR: File not found: {crop_path}")
        all_passed = False

    # 2. Validate Soil Database
    soil_path = Path("data/soil_database.csv")
    print(f"\n[2/4] Validating Soil Database ({soil_path})...")
    if soil_path.is_file():
        soil_df = pd.read_csv(soil_path)
        soil_report = DataValidator.validate_soil_database(soil_df)
        print(f"      Status: {'PASSED' if soil_report.is_valid else 'FAILED'}")
        print(f"      Records: {soil_report.total_records}, Errors: {soil_report.error_count}, Warnings: {soil_report.warning_count}")
        if not soil_report.is_valid:
            all_passed = False
            for err in soil_report.issues:
                print(f"      -> {err.severity}: {err.message}")
    else:
        print(f"      ERROR: File not found: {soil_path}")
        all_passed = False

    # 3. Validate Clean Weather Dataset
    weather_path = Path("data/processed/weather_clean.csv")
    print(f"\n[3/4] Validating Clean Weather Dataset ({weather_path})...")
    if weather_path.is_file():
        weather_df = pd.read_csv(weather_path)
        weather_df["timestamp"] = pd.to_datetime(weather_df["timestamp"])
        weather_report = DataValidator.validate_weather_dataset(weather_df)
        print(f"      Status: {'PASSED' if weather_report.is_valid else 'FAILED'}")
        print(f"      Records: {weather_report.total_records}, Errors: {weather_report.error_count}, Warnings: {weather_report.warning_count}")
        if not weather_report.is_valid:
            all_passed = False
            for err in weather_report.issues:
                print(f"      -> {err.severity}: {err.message}")
    else:
        print(f"      NOTE: Clean weather file does not exist yet. Run prepare_data.py first.")

    # 4. Validate Unified Irrigation Dataset
    dataset_path = Path("data/processed/irrigation_dataset.csv")
    print(f"\n[4/4] Validating Unified Irrigation Dataset ({dataset_path})...")
    if dataset_path.is_file():
        dataset_df = pd.read_csv(dataset_path)
        dataset_df["timestamp"] = pd.to_datetime(dataset_df["timestamp"])
        unified_report = DataValidator.validate_unified_dataset(dataset_df)
        print(f"      Status: {'PASSED' if unified_report.is_valid else 'FAILED'}")
        print(f"      Records: {unified_report.total_records}, Errors: {unified_report.error_count}, Warnings: {unified_report.warning_count}")
        if not unified_report.is_valid:
            all_passed = False
            for err in unified_report.issues:
                print(f"      -> {err.severity}: {err.message}")
    else:
        print(f"      NOTE: Unified dataset does not exist yet. Run prepare_data.py first.")

    print("\n" + "=" * 70)
    if all_passed:
        print(" ALL DATASETS ARE STRICTLY COMPLIANT")
        print("=" * 70)
        return 0
    else:
        print(" VALIDATION DETECTED ANOMALIES")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
