"""Unified multizone dataset builder.

Synthesizes meteorological time-series records with multi-zone agronomic and pedological
parameters into a unified tabular structure ready for downstream simulation and modeling.
"""

from pathlib import Path
from typing import Union, List, Optional
import pandas as pd
import numpy as np

from config import load_config, SystemConfig, ZoneConfig


class DatasetBuilder:
    """Builds the canonical multizone irrigation dataset."""

    CANONICAL_COLUMNS: List[str] = [
        "timestamp",
        "zone_id",
        "crop",
        "growth_stage",
        "soil_type",
        "temperature",
        "humidity",
        "solar_radiation",
        "wind_speed",
        "rainfall",
        "soil_moisture",
        "field_capacity",
        "wilting_point",
        "target_moisture",
        "kc",
        "et0",
        "etc",
        "effective_rainfall",
        "moisture_error",
        "water_deficit",
        "available_water",
    ]

    def __init__(self, config: Optional[SystemConfig] = None) -> None:
        """Initialize builder with system configuration."""
        self.config = config or load_config()

    def build(
        self,
        weather_df: pd.DataFrame,
        zones: Optional[List[ZoneConfig]] = None,
    ) -> pd.DataFrame:
        """Combine weather observations across each active zone into the unified schema.

        Args:
            weather_df: Cleaned meteorological DataFrame (must contain timestamp, temperature,
                        humidity, solar_radiation, wind_speed, rainfall).
            zones: Optional list of ZoneConfig objects (defaults to system config zones).

        Returns:
            pd.DataFrame: Unified multi-zone dataset.
        """
        active_zones = zones or self.config.zone_configs or []
        if not active_zones:
            raise ValueError("No active zones found in configuration.")

        zone_dfs = []
        for zone in active_zones:
            df_zone = weather_df.copy()
            df_zone["zone_id"] = zone.zone_id
            df_zone["crop"] = zone.crop.name
            df_zone["growth_stage"] = zone.crop.growth_stage.value
            df_zone["soil_type"] = zone.soil.soil_type.value

            # Physical parameters
            df_zone["soil_moisture"] = zone.initial_moisture
            df_zone["field_capacity"] = zone.soil.field_capacity
            df_zone["wilting_point"] = zone.soil.wilting_point
            df_zone["target_moisture"] = zone.target_moisture
            df_zone["kc"] = zone.crop.kc

            # Uncalculated Phase 0/1 fields remain NaN/empty for subsequent phases
            df_zone["et0"] = np.nan
            df_zone["etc"] = np.nan
            df_zone["effective_rainfall"] = np.nan
            df_zone["moisture_error"] = np.nan
            df_zone["water_deficit"] = np.nan
            df_zone["available_water"] = np.nan

            zone_dfs.append(df_zone)

        combined_df = pd.concat(zone_dfs, ignore_index=True)

        # Sort chronologically by timestamp and then by zone_id
        combined_df = combined_df.sort_values(by=["timestamp", "zone_id"]).reset_index(drop=True)

        # Reorder to canonical schema order
        canonical_present = [c for c in self.CANONICAL_COLUMNS if c in combined_df.columns]
        return combined_df[canonical_present]

    def build_and_save(
        self,
        weather_path: Union[str, Path] = "data/processed/weather_clean.csv",
        output_path: Union[str, Path] = "data/processed/irrigation_dataset.csv",
    ) -> Path:
        """Load cleaned weather data, build multi-zone unified dataset, and save to CSV."""
        weather_p = Path(weather_path)
        if not weather_p.is_file():
            raise FileNotFoundError(f"Cleaned weather file not found at: {weather_p.resolve()}")

        weather_df = pd.read_csv(weather_p)
        weather_df["timestamp"] = pd.to_datetime(weather_df["timestamp"])

        unified_df = self.build(weather_df)

        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        unified_df.to_csv(out_p, index=False)
        return out_p
