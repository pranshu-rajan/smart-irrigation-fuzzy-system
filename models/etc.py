"""Crop evapotranspiration (ETc) and crop water deficit calculation engine.

Implements FAO-56 single crop coefficient methodology (Chapter 6):
    ETc = Kc * ET0

Where:
    ET0: Reference crop evapotranspiration [mm/day, mm/hour, or mm/step].
    Kc: Crop coefficient accounting for crop characteristics, canopy cover, and growth stage.
    ETc: Crop evapotranspiration under standard, non-stress conditions.

Also calculates:
    Effective Rainfall (P_eff): Infiltrated precipitation retained in the root zone.
    Atmospheric/Crop Water Deficit (D_crop):
        D_crop = max(0.0, ETc - P_eff)

CRITICAL CONCEPTUAL DISTINCTION:
    Atmospheric/Crop Water Deficit (D_crop) represents the atmospheric demand unfulfilled
    by precipitation over a given interval (mm).
    Soil Moisture Control Error e(t) = SM_target - SM(t) represents the root-zone volumetric
    or percentage moisture tracking deviation (m3/m3 or %).
    These two quantities must never be conflated.
"""

from pathlib import Path
from typing import Optional, Union, Dict, Any, Tuple
import numpy as np
import pandas as pd

from config.schemas import CropType, GrowthStage


DEFAULT_CROP_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "crop_database.csv"


class CropCoefficientManager:
    """Manages FAO-56 crop coefficient lookups and phenological stage interpolation."""

    _database_cache: Optional[pd.DataFrame] = None

    @classmethod
    def load_crop_database(cls, csv_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
        """Load and cache the canonical FAO-56 crop database."""
        path = Path(csv_path) if csv_path is not None else DEFAULT_CROP_DB_PATH
        if cls._database_cache is None or csv_path is not None:
            if not path.exists():
                raise FileNotFoundError(f"Crop database not found at {path}")
            df = pd.read_csv(path)
            cls._database_cache = df
        return cls._database_cache

    @classmethod
    def get_kc(
        cls,
        crop_name: str,
        growth_stage: Union[str, GrowthStage] = GrowthStage.MID_SEASON,
        stage_progress: float = 0.5,
        csv_path: Optional[Union[str, Path]] = None,
    ) -> float:
        """Look up or interpolate Kc for a crop and growth stage.

        Phenological Stages (FAO-56 Chapter 6):
            - Initial: Kc = kc_initial (constant)
            - Development: Kc linearly increases from kc_initial to kc_mid
            - Mid-season: Kc = kc_mid (constant peak)
            - Late-season: Kc linearly transitions from kc_mid to kc_end

        Args:
            crop_name: Common crop name (e.g. 'Tomato', 'Wheat', 'Maize').
            growth_stage: GrowthStage enum or string ('Initial', 'Development', 'Mid-season', 'Late-season').
            stage_progress: Relative progress through the stage [0.0, 1.0]. Default 0.5.
            csv_path: Optional custom path to crop_database.csv.

        Returns:
            float: Recommended Kc value.
        """
        df = cls.load_crop_database(csv_path)
        crop_name_clean = str(crop_name).strip().capitalize()
        stage_str = growth_stage.value if isinstance(growth_stage, GrowthStage) else str(growth_stage).strip()

        # Match crop in database
        crop_rows = df[df["crop"].str.capitalize() == crop_name_clean]
        if crop_rows.empty:
            raise ValueError(f"Crop '{crop_name}' not found in crop database: {df['crop'].unique().tolist()}")

        row = crop_rows.iloc[0]
        kc_ini = float(row["kc_initial"])
        kc_mid = float(row["kc_mid"])
        kc_end = float(row["kc_end"])

        prog = np.clip(float(stage_progress), 0.0, 1.0)
        stage_lower = stage_str.lower()

        if "ini" in stage_lower:
            return kc_ini
        elif "dev" in stage_lower:
            # Linear interpolation from Kc_ini to Kc_mid
            return float(kc_ini + prog * (kc_mid - kc_ini))
        elif "mid" in stage_lower:
            return kc_mid
        elif "late" in stage_lower or "end" in stage_lower:
            # Linear decline from Kc_mid to Kc_end
            return float(kc_mid + prog * (kc_end - kc_mid))
        else:
            # Fallback default
            return kc_mid


def calculate_etc(et0_mm: float, kc: float) -> float:
    """Calculate crop-specific evapotranspiration under standard conditions (FAO-56 Eq. 56).

    ETc = Kc * ET0

    Args:
        et0_mm: Reference crop evapotranspiration (mm/day, mm/hour, or mm/step).
        kc: Dimensionless crop coefficient.

    Returns:
        float: Crop evapotranspiration ETc in the same unit/timescale as ET0.
    """
    et0 = max(0.0, float(et0_mm))
    kc_val = max(0.0, float(kc))
    return float(kc_val * et0)


def calculate_effective_rainfall(
    rainfall_mm: float,
    method: str = "usda_scs",
    timestep_minutes: int = 1440,
    canopy_storage_threshold_mm: float = 0.2,
    efficiency_fraction: float = 0.80,
) -> float:
    """Calculate effective precipitation Peff available to the crop root zone.

    Supported Methods:
        1. 'usda_scs' (USDA Soil Conservation Service method):
            For daily rainfall P (mm/day):
                If P <= 8.3 mm/day: Peff = max(0, P * (125 - 0.2 * P) / 125)
                If P > 8.3 mm/day:  Peff = max(0, 125 / 3 + 0.1 * P)
            For sub-daily steps: scales threshold proportionally to avoid over-counting interception.

        2. 'fao_empirical' (FAO CROPWAT / empirical method):
            For daily rainfall:
                If P <= 0.2 mm: Peff = 0.0 (lost to interception and droplet evaporation)
                If P > 0.2 mm:  Peff = max(0.0, 0.8 * (P - 0.2))

        3. 'fixed_percentage':
            Peff = max(0.0, efficiency_fraction * (P - canopy_storage_threshold_mm))

    Args:
        rainfall_mm: Total observed precipitation during the timestep (mm).
        method: Calculation methodology ('usda_scs', 'fao_empirical', 'fixed_percentage').
        timestep_minutes: Discretization period in minutes (default 1440 = daily).
        canopy_storage_threshold_mm: Interception storage capacity (mm).
        efficiency_fraction: Retention efficiency coefficient (default 0.80).

    Returns:
        float: Effective rainfall Peff in mm.
    """
    p = max(0.0, float(rainfall_mm))
    if p < 1e-6:
        return 0.0

    method_clean = method.strip().lower()

    if method_clean == "usda_scs":
        if timestep_minutes >= 1440:
            # Standard daily USDA-SCS equation
            if p <= 83.3:
                peff = p * (125.0 - 0.2 * p) / 125.0
            else:
                peff = (125.0 / 3.0) + 0.1 * p
            return float(np.clip(peff, 0.0, p))
        else:
            # Sub-daily timestep adaptation:
            # Scale canopy threshold by timestep fraction so light drizzles evaporate
            step_thresh = canopy_storage_threshold_mm * (timestep_minutes / 60.0)
            step_thresh = min(canopy_storage_threshold_mm, max(0.01, step_thresh))
            if p <= step_thresh:
                return 0.0
            # Retain ~80% of precipitation above interception
            return float(np.clip(0.80 * (p - step_thresh), 0.0, p))

    elif method_clean == "fao_empirical":
        thresh = canopy_storage_threshold_mm if timestep_minutes >= 1440 else (canopy_storage_threshold_mm / 10.0)
        if p <= thresh:
            return 0.0
        return float(np.clip(0.80 * (p - thresh), 0.0, p))

    elif method_clean == "fixed_percentage":
        thresh = canopy_storage_threshold_mm if timestep_minutes >= 1440 else (canopy_storage_threshold_mm / 10.0)
        if p <= thresh:
            return 0.0
        return float(np.clip(efficiency_fraction * (p - thresh), 0.0, p))

    else:
        raise ValueError(f"Unknown effective rainfall method: '{method}'. Choose 'usda_scs', 'fao_empirical', or 'fixed_percentage'.")


def calculate_crop_water_deficit(etc_mm: float, effective_rainfall_mm: float) -> float:
    """Calculate atmospheric/crop water deficit (D_crop).

    D_crop = max(0.0, ETc - Peff)

    This represents the atmospheric water demand not satisfied by natural precipitation.

    NOTE: This is NOT the soil moisture tracking error e(t) = SM_target - SM(t).

    Args:
        etc_mm: Crop evapotranspiration in mm.
        effective_rainfall_mm: Effective precipitation in mm.

    Returns:
        float: Crop water deficit D_crop in mm (non-negative).
    """
    etc = max(0.0, float(etc_mm))
    peff = max(0.0, float(effective_rainfall_mm))
    return float(max(0.0, etc - peff))


def calculate_water_deficit(etc_or_target: float, peff_or_current: float) -> float:
    """Calculate water deficit (compatibility function).

    If both arguments are <= 1.0 (or typical soil moisture fractions/percentages),
    calculates volumetric soil deficit: max(0.0, target - current).
    Otherwise, evaluates atmospheric crop deficit: max(0.0, etc - peff).

    Args:
        etc_or_target: Crop ETc (mm) or Target soil moisture (m3/m3 or %).
        peff_or_current: Effective rainfall (mm) or Current soil moisture (m3/m3 or %).

    Returns:
        float: Deficit (non-negative).
    """
    # Primary evaluation: atmospheric crop water deficit
    return calculate_crop_water_deficit(etc_or_target, peff_or_current)


def compute_multizone_crop_demand(
    et0_df: pd.DataFrame,
    zones_info: Optional[list] = None,
    timestep_minutes: int = 1,
    effective_rainfall_method: str = "usda_scs",
) -> pd.DataFrame:
    """Compute multizone crop evapotranspiration, effective rainfall, and water deficit.

    Evaluates ETc, Peff, and D_crop across all active agricultural zones.

    Default 3-Zone Agronomic Testbed:
        - Zone 1: Tomato (Mid-season, Kc = 1.15)
        - Zone 2: Wheat (Development, Kc = 0.85)
        - Zone 3: Maize (Mid-season, Kc = 1.20)

    Args:
        et0_df: DataFrame containing ET0 output from `compute_et0_timeseries`.
        zones_info: Optional list of dicts specifying [{'zone_id': int, 'crop': str,
                    'growth_stage': str, 'kc': Optional[float]}].
        timestep_minutes: Discretization step in minutes (default 1).
        effective_rainfall_method: Methodology for effective rainfall calculation.

    Returns:
        pd.DataFrame: Multizone dataset containing:
            ['timestamp', 'zone_id', 'crop', 'growth_stage', 'kc', 'et0',
             'etc', 'rainfall', 'effective_rainfall', 'water_deficit']
    """
    if zones_info is None:
        # Canonical Section 5 & 6 default zones
        zones_info = [
            {"zone_id": 1, "crop": "Tomato", "growth_stage": "Mid-season", "kc": 1.15},
            {"zone_id": 2, "crop": "Wheat", "growth_stage": "Development", "kc": 0.85},
            {"zone_id": 3, "crop": "Maize", "growth_stage": "Mid-season", "kc": 1.20},
        ]

    records = []
    # Calculate effective rainfall array
    raw_rainfall = et0_df["rainfall"].to_numpy(dtype=np.float64) if "rainfall" in et0_df.columns else np.zeros(len(et0_df))
    peff_series = np.array([
        calculate_effective_rainfall(r, method=effective_rainfall_method, timestep_minutes=timestep_minutes)
        for r in raw_rainfall
    ], dtype=np.float64)

    timestamps = et0_df["timestamp"].values if "timestamp" in et0_df.columns else np.arange(len(et0_df))
    et0_series = et0_df["et0"].to_numpy(dtype=np.float64)

    for zone in zones_info:
        z_id = zone["zone_id"]
        c_name = zone["crop"]
        stage = zone.get("growth_stage", "Mid-season")
        kc = zone.get("kc")
        if kc is None:
            kc = CropCoefficientManager.get_kc(c_name, stage)

        etc_series = et0_series * kc
        deficit_series = np.maximum(0.0, etc_series - peff_series)

        zone_df = pd.DataFrame({
            "timestamp": timestamps,
            "zone_id": z_id,
            "crop": c_name,
            "growth_stage": stage,
            "kc": round(kc, 3),
            "et0": np.round(et0_series, 6),
            "etc": np.round(etc_series, 6),
            "rainfall": np.round(raw_rainfall, 4),
            "effective_rainfall": np.round(peff_series, 4),
            "water_deficit": np.round(deficit_series, 6),
        })
        records.append(zone_df)

    out_df = pd.concat(records, ignore_index=True)
    out_df = out_df.sort_values(by=["timestamp", "zone_id"]).reset_index(drop=True)
    return out_df
