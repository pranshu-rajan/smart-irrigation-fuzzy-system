"""Preprocessing pipeline for agricultural weather datasets.

Standardizes, cleans, validates, and aligns raw environmental time-series data
into the project's canonical meteorological schema.
"""

from pathlib import Path
from typing import Optional, Dict, Any, Union, List, Tuple
import pandas as pd
import numpy as np


class WeatherPreprocessor:
    """Loads, cleans, and standardizes meteorological time-series records."""

    COLUMN_MAPPINGS: Dict[str, str] = {
        # Timestamps
        "record_time": "timestamp",
        "date_time": "timestamp",
        "datetime": "timestamp",
        "time": "timestamp",
        "date": "timestamp",
        # Temperature
        "temp_2m_c": "temperature",
        "temperature_c": "temperature",
        "air_temp_c": "temperature",
        "t2m": "temperature",
        "temp": "temperature",
        # Humidity
        "rel_hum_pct": "humidity",
        "humidity_percent": "humidity",
        "relative_humidity": "humidity",
        "rh2m": "humidity",
        "rh": "humidity",
        # Solar Radiation
        "solar_rad_wm2": "solar_radiation",
        "solar_radiation_wm2": "solar_radiation",
        "allsky_sfc_sw_dwn": "solar_radiation",
        "srad": "solar_radiation",
        "radiation": "solar_radiation",
        # Wind Speed
        "wind_speed_2m_ms": "wind_speed",
        "wind_speed_ms": "wind_speed",
        "ws2m": "wind_speed",
        "wind": "wind_speed",
        # Precipitation
        "precip_mm": "rainfall",
        "rainfall_mm": "rainfall",
        "prectotcorr": "rainfall",
        "precipitation": "rainfall",
        "rain": "rainfall",
    }

    PHYSICAL_BOUNDS: Dict[str, Tuple[float, float]] = {
        "temperature": (-20.0, 60.0),    # Celsius
        "humidity": (0.0, 100.0),        # Percentage
        "solar_radiation": (0.0, 1500.0),# W/m2
        "wind_speed": (0.0, 50.0),       # m/s
        "rainfall": (0.0, 300.0),        # mm/step
    }

    def __init__(self, raw_path: Union[str, Path] = "data/raw/weather_raw.csv") -> None:
        """Initialize preprocessor with path to raw weather data file.

        Args:
            raw_path: Path to the raw weather CSV.
        """
        self.raw_path = Path(raw_path)
        self.raw_df: Optional[pd.DataFrame] = None
        self.cleaned_df: Optional[pd.DataFrame] = None
        self.processing_log: List[str] = []

    def load_data(self) -> pd.DataFrame:
        """Load raw CSV file and store in instance memory."""
        if not self.raw_path.is_file():
            raise FileNotFoundError(f"Raw weather file not found at: {self.raw_path.resolve()}")

        df = pd.read_csv(self.raw_path)
        self.raw_df = df
        self.processing_log.append(f"Loaded raw dataset with {len(df)} rows and {len(df.columns)} columns.")
        return df

    def standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to lower-case standard project naming."""
        rename_dict = {}
        for col in df.columns:
            normalized = str(col).strip().lower()
            if normalized in self.COLUMN_MAPPINGS:
                rename_dict[col] = self.COLUMN_MAPPINGS[normalized]
            else:
                rename_dict[col] = normalized

        renamed_df = df.rename(columns=rename_dict)
        self.processing_log.append(f"Standardized columns: {list(renamed_df.columns)}")
        return renamed_df

    def process(
        self,
        interpolate_resolution: Optional[str] = "1min",
        fill_missing: bool = True,
    ) -> pd.DataFrame:
        """Execute end-to-end cleaning and preprocessing pipeline.

        Args:
            interpolate_resolution: Target resampling frequency (e.g. '1min' for 1440 steps,
                                   or None to preserve native raw timestamps).
            fill_missing: Whether to interpolate missing interior values.

        Returns:
            pd.DataFrame: Standardized, validated, clean weather DataFrame.
        """
        df = self.load_data() if self.raw_df is None else self.raw_df.copy()
        df = self.standardize_columns(df)

        # Ensure required canonical columns are present
        required_cols = ["timestamp", "temperature", "humidity", "solar_radiation", "wind_speed", "rainfall"]
        missing_canonical = [col for col in required_cols if col not in df.columns]
        if missing_canonical:
            raise ValueError(f"Raw weather dataset missing mandatory columns: {missing_canonical}")

        # Filter down to required canonical columns
        df = df[required_cols].copy()

        # Parse timestamps
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.dropna(subset=["timestamp"])

        # Check and handle duplicate timestamps
        num_duplicates = df.duplicated(subset=["timestamp"]).sum()
        if num_duplicates > 0:
            self.processing_log.append(f"Found {num_duplicates} duplicate timestamps. Averaging duplicates.")
            df = df.groupby("timestamp").mean().reset_index()

        # Chronological sorting
        df = df.sort_values(by="timestamp").reset_index(drop=True)

        # Detect and log out-of-bounds physical anomalies
        for col, (lower, upper) in self.PHYSICAL_BOUNDS.items():
            if col in df.columns:
                anomalies = df[(df[col] < lower) | (df[col] > upper)]
                if len(anomalies) > 0:
                    self.processing_log.append(
                        f"Detected {len(anomalies)} physically implausible values in '{col}' "
                        f"outside [{lower}, {upper}]. Clamping to physical range."
                    )
                    df[col] = df[col].clip(lower=lower, upper=upper)

        # Handle missing values
        null_counts = df.isnull().sum().to_dict()
        self.processing_log.append(f"Missing value counts before imputation: {null_counts}")
        if fill_missing:
            # Linear interpolation for continuous weather variables, 0 for rainfall
            numeric_cols = ["temperature", "humidity", "solar_radiation", "wind_speed"]
            df[numeric_cols] = df[numeric_cols].interpolate(method="linear").bfill().ffill()
            df["rainfall"] = df["rainfall"].fillna(0.0)

        # High-resolution interpolation (e.g. hourly raw -> 1-minute steps for simulation)
        if interpolate_resolution:
            df = df.set_index("timestamp")
            resampled = df.resample(interpolate_resolution).interpolate(method="time")
            # Rainfall during interpolation should be partitioned or conserved
            resampled["rainfall"] = resampled["rainfall"].fillna(0.0)
            df = resampled.reset_index()
            self.processing_log.append(
                f"Resampled weather timeline to '{interpolate_resolution}' with {len(df)} total steps."
            )

        self.cleaned_df = df
        return df

    def save_clean(self, output_path: Union[str, Path] = "data/processed/weather_clean.csv") -> Path:
        """Save cleaned weather dataframe to destination CSV."""
        if self.cleaned_df is None:
            self.process()

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self.cleaned_df.to_csv(out_path, index=False)
        self.processing_log.append(f"Saved cleaned weather data to {out_path.resolve()}")
        return out_path
