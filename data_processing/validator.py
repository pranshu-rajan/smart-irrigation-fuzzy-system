"""Data validation engine for agricultural and environmental datasets.

Performs physical bound verification, chronological consistency checks,
and pedological integrity rules without silently dropping records.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import pandas as pd
import numpy as np


@dataclass
class ValidationIssue:
    """Record of an identified data validation anomaly or rule violation."""
    severity: str  # "ERROR" or "WARNING"
    field: str
    row_index: Optional[int]
    value: Any
    message: str


@dataclass
class ValidationReport:
    """Aggregated validation findings across an entire dataset."""
    dataset_name: str
    total_records: int
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "WARNING")

    def summary(self) -> Dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "total_records": self.total_records,
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [
                {
                    "severity": i.severity,
                    "field": i.field,
                    "row": i.row_index,
                    "value": str(i.value),
                    "message": i.message,
                }
                for i in self.issues[:50]  # Cap summary output for readability
            ],
        }


class DataValidator:
    """Validates physical, agronomic, and temporal integrity of agricultural datasets."""

    @classmethod
    def validate_weather_dataset(cls, df: pd.DataFrame, name: str = "Weather Dataset") -> ValidationReport:
        """Validate meteorological observations DataFrame."""
        issues: List[ValidationIssue] = []

        # Check required columns
        req = ["timestamp", "temperature", "humidity", "solar_radiation", "wind_speed", "rainfall"]
        for col in req:
            if col not in df.columns:
                issues.append(ValidationIssue("ERROR", col, None, None, f"Missing required column '{col}'"))

        if any(i.severity == "ERROR" for i in issues):
            return ValidationReport(name, len(df), False, issues)

        # Temporal checks
        if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            try:
                parsed_ts = pd.to_datetime(df["timestamp"])
            except Exception as e:
                issues.append(ValidationIssue("ERROR", "timestamp", None, None, f"Timestamp parsing failed: {e}"))
                parsed_ts = None
        else:
            parsed_ts = df["timestamp"]

        if parsed_ts is not None:
            if not parsed_ts.is_monotonic_increasing:
                issues.append(ValidationIssue("WARNING", "timestamp", None, None, "Timestamps are not chronologically sorted."))
            dup_count = parsed_ts.duplicated().sum()
            if dup_count > 0:
                issues.append(ValidationIssue("WARNING", "timestamp", None, dup_count, f"Found {dup_count} duplicate timestamps."))

        # Value bounds checks
        checks = [
            ("temperature", -20.0, 60.0, "°C"),
            ("humidity", 0.0, 100.0, "%"),
            ("solar_radiation", 0.0, 1500.0, "W/m2"),
            ("wind_speed", 0.0, 50.0, "m/s"),
            ("rainfall", 0.0, 500.0, "mm"),
        ]

        for col, min_v, max_v, unit in checks:
            below = df[df[col] < min_v]
            for idx, val in below[col].items():
                issues.append(ValidationIssue("ERROR", col, int(idx), val, f"Value {val}{unit} below physical minimum {min_v}{unit}."))

            above = df[df[col] > max_v]
            for idx, val in above[col].items():
                issues.append(ValidationIssue("ERROR", col, int(idx), val, f"Value {val}{unit} exceeds physical maximum {max_v}{unit}."))

        is_valid = sum(1 for i in issues if i.severity == "ERROR") == 0
        return ValidationReport(name, len(df), is_valid, issues)

    @classmethod
    def validate_unified_dataset(cls, df: pd.DataFrame, name: str = "Unified Irrigation Dataset") -> ValidationReport:
        """Validate multi-zone merged dataset with soil and crop constraints."""
        issues: List[ValidationIssue] = []

        # Check required columns
        req = ["timestamp", "zone_id", "crop", "temperature", "humidity", "solar_radiation", "wind_speed", "rainfall"]
        for col in req:
            if col not in df.columns:
                issues.append(ValidationIssue("ERROR", col, None, None, f"Missing required column '{col}'"))

        if any(i.severity == "ERROR" for i in issues):
            return ValidationReport(name, len(df), False, issues)

        # Temporal checks
        if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            try:
                parsed_ts = pd.to_datetime(df["timestamp"])
            except Exception as e:
                issues.append(ValidationIssue("ERROR", "timestamp", None, None, f"Timestamp parsing failed: {e}"))
                parsed_ts = None
        else:
            parsed_ts = df["timestamp"]

        if parsed_ts is not None and "zone_id" in df.columns:
            dup_count = df.duplicated(subset=["timestamp", "zone_id"]).sum()
            if dup_count > 0:
                issues.append(ValidationIssue("WARNING", "timestamp", None, dup_count, f"Found {dup_count} duplicate timestamp+zone_id pairs."))

        # Value bounds checks
        checks = [
            ("temperature", -20.0, 60.0, "°C"),
            ("humidity", 0.0, 100.0, "%"),
            ("solar_radiation", 0.0, 1500.0, "W/m2"),
            ("wind_speed", 0.0, 50.0, "m/s"),
            ("rainfall", 0.0, 500.0, "mm"),
        ]

        for col, min_v, max_v, unit in checks:
            if col in df.columns:
                below = df[df[col] < min_v]
                for idx, val in below[col].items():
                    issues.append(ValidationIssue("ERROR", col, int(idx), val, f"Value {val}{unit} below physical minimum {min_v}{unit}."))

                above = df[df[col] > max_v]
                for idx, val in above[col].items():
                    issues.append(ValidationIssue("ERROR", col, int(idx), val, f"Value {val}{unit} exceeds physical maximum {max_v}{unit}."))

        # Multi-zone agronomic checks
        if "field_capacity" in df.columns and "wilting_point" in df.columns:
            fc_below_wp = df[df["field_capacity"] <= df["wilting_point"]]
            for idx, row in fc_below_wp.iterrows():
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "field_capacity",
                        int(idx),
                        f"FC={row['field_capacity']}, WP={row['wilting_point']}",
                        "Field Capacity must be strictly greater than Wilting Point.",
                    )
                )

        if "target_moisture" in df.columns and "field_capacity" in df.columns and "wilting_point" in df.columns:
            target_out_of_bounds = df[
                (df["target_moisture"] < df["wilting_point"]) | (df["target_moisture"] > df["field_capacity"])
            ]
            for idx, row in target_out_of_bounds.iterrows():
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "target_moisture",
                        int(idx),
                        row["target_moisture"],
                        f"Target moisture must lie between WP ({row['wilting_point']}) and FC ({row['field_capacity']}).",
                    )
                )

        if "kc" in df.columns:
            invalid_kc = df[df["kc"] <= 0.0]
            for idx, val in invalid_kc["kc"].items():
                issues.append(ValidationIssue("ERROR", "kc", int(idx), val, f"Crop coefficient Kc must be > 0 (found {val})."))

        is_valid = sum(1 for i in issues if i.severity == "ERROR") == 0
        return ValidationReport(name, len(df), is_valid, issues)

    @classmethod
    def validate_crop_database(cls, df: pd.DataFrame, name: str = "Crop Database") -> ValidationReport:
        """Validate crop agronomic parameters database."""
        issues: List[ValidationIssue] = []
        required_cols = ["crop", "growth_stage", "kc_initial", "kc_mid", "kc_end"]
        for col in required_cols:
            if col not in df.columns:
                issues.append(ValidationIssue("ERROR", col, None, None, f"Missing required column '{col}'"))

        if not any(i.severity == "ERROR" for i in issues):
            for col in ["kc_initial", "kc_mid", "kc_end"]:
                invalid_kc = df[(df[col] <= 0.0) | (df[col] > 2.5)]
                for idx, val in invalid_kc[col].items():
                    issues.append(ValidationIssue("ERROR", col, int(idx), val, f"Invalid Kc value {val} (expected 0.0 < Kc <= 2.5)"))

        is_valid = sum(1 for i in issues if i.severity == "ERROR") == 0
        return ValidationReport(name, len(df), is_valid, issues)

    @classmethod
    def validate_soil_database(cls, df: pd.DataFrame, name: str = "Soil Database") -> ValidationReport:
        """Validate soil physical parameters database."""
        issues: List[ValidationIssue] = []
        required_cols = ["soil_type", "field_capacity_pct", "wilting_point_pct", "infiltration_rate_mm_h"]
        for col in required_cols:
            if col not in df.columns:
                issues.append(ValidationIssue("ERROR", col, None, None, f"Missing required column '{col}'"))

        if not any(i.severity == "ERROR" for i in issues):
            invalid_fc_wp = df[df["field_capacity_pct"] <= df["wilting_point_pct"]]
            for idx, row in invalid_fc_wp.iterrows():
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "field_capacity_pct",
                        int(idx),
                        f"FC={row['field_capacity_pct']}, WP={row['wilting_point_pct']}",
                        "Field capacity must exceed wilting point.",
                    )
                )

        is_valid = sum(1 for i in issues if i.severity == "ERROR") == 0
        return ValidationReport(name, len(df), is_valid, issues)
