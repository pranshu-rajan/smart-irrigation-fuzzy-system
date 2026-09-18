"""Soil physical parameters, moisture normalization, and root-zone water storage.

Provides core functions for:
1. Soil parameter lookup from `data/soil_database.csv`.
2. Relative Soil Moisture (RSM) normalization:
       RSM = (SM - WP) / (FC - WP)
3. Closed-loop soil moisture tracking error:
       e(t) = SM_target - SM(t)
4. Total Available Water (TAW) and Readily Available Water (RAW) according to FAO-56 Chapter 8.
5. Bidirectional conversions between volumetric moisture fraction (m3/m3 or %) and water depth (mm).
6. Infiltration capacity and gravity drainage modeling.
"""

from pathlib import Path
from typing import Optional, Union, Dict, Any, Tuple
import numpy as np
import pandas as pd

from config.schemas import SoilType, SoilParameters


DEFAULT_SOIL_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "soil_database.csv"


class SoilParameterManager:
    """Manages USDA/FAO soil texture property lookups and parameter reconciliation."""

    _database_cache: Optional[pd.DataFrame] = None

    @classmethod
    def load_soil_database(cls, csv_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
        """Load and cache the canonical soil physical property database."""
        path = Path(csv_path) if csv_path is not None else DEFAULT_SOIL_DB_PATH
        if cls._database_cache is None or csv_path is not None:
            if not path.exists():
                raise FileNotFoundError(f"Soil database not found at {path}")
            df = pd.read_csv(path)
            cls._database_cache = df
        return cls._database_cache

    @classmethod
    def get_soil_properties(
        cls,
        soil_type: Union[str, SoilType],
        csv_path: Optional[Union[str, Path]] = None,
    ) -> Dict[str, float]:
        """Look up hydraulic parameters for a soil classification.

        Args:
            soil_type: SoilType enum or string ('Loam', 'Sandy', 'Clay', etc.).
            csv_path: Optional custom path to soil_database.csv.

        Returns:
            Dict[str, float]: Soil properties with field_capacity, wilting_point,
                             available_water, saturation, infiltration_rate_mm_h, drainage_parameter.
        """
        df = cls.load_soil_database(csv_path)
        type_str = soil_type.value if isinstance(soil_type, SoilType) else str(soil_type).strip().title()

        match = df[df["soil_type"].str.title() == type_str]
        if match.empty:
            raise ValueError(f"Soil type '{soil_type}' not found in database: {df['soil_type'].tolist()}")

        row = match.iloc[0]
        return {
            "soil_type": type_str,
            "field_capacity_pct": float(row["field_capacity_pct"]),
            "wilting_point_pct": float(row["wilting_point_pct"]),
            "available_water_pct": float(row["available_water_pct"]),
            "saturation_pct": float(row["saturation_pct"]),
            "infiltration_rate_mm_h": float(row["infiltration_rate_mm_h"]),
            "drainage_parameter": float(row["drainage_parameter"]),
        }


def calculate_relative_soil_moisture(
    soil_moisture: float,
    wilting_point: float,
    field_capacity: float,
) -> float:
    """Normalize volumetric soil moisture relative to the plant-available water range.

    RSM = (SM - WP) / (FC - WP)

    Scale-Invariant Property:
        Evaluates identically whether inputs are in volumetric fractions (m3/m3)
        or percentages (0-100%).

    Physical Boundary Enforcement:
        - RSM = 0.0: Moisture is at Permanent Wilting Point (WP).
        - RSM = 1.0: Moisture is at Field Capacity (FC).
        - Constrained to [0.0, 1.0] for physical root-zone storage representation.

    Args:
        soil_moisture: Current observed soil moisture (fraction or %).
        wilting_point: Permanent wilting point (fraction or %).
        field_capacity: Field capacity (fraction or %).

    Returns:
        float: Normalized Relative Soil Moisture (RSM) in [0.0, 1.0].
    """
    sm = float(soil_moisture)
    wp = float(wilting_point)
    fc = float(field_capacity)

    if fc <= wp:
        raise ValueError(f"Field capacity ({fc}) must be strictly greater than wilting point ({wp}).")

    rsm = (sm - wp) / (fc - wp)
    return float(np.clip(rsm, 0.0, 1.0))


# Convenient alias
calculate_rsm = calculate_relative_soil_moisture


def calculate_moisture_error(
    target_moisture: float,
    current_moisture: float,
    normalized: bool = False,
    wilting_point: Optional[float] = None,
    field_capacity: Optional[float] = None,
) -> float:
    """Calculate the closed-loop soil moisture tracking error.

    e(t) = SM_target - SM(t)

    If normalized=True:
        e_norm(t) = RSM_target - RSM(t) = (SM_target - SM(t)) / (FC - WP)

    NOTE: This is NOT the crop water deficit D_crop = max(0, ETc - Peff).
    Moisture error is a closed-loop tracking deviation in the root zone.

    Args:
        target_moisture: Set-point moisture (m3/m3 or %).
        current_moisture: Observed moisture (m3/m3 or %).
        normalized: If True, returns error normalized by plant available water range.
        wilting_point: Required if normalized=True.
        field_capacity: Required if normalized=True.

    Returns:
        float: Moisture tracking error (positive means under-irrigated/deficit).
    """
    err = float(target_moisture) - float(current_moisture)
    if not normalized:
        return err

    if wilting_point is None or field_capacity is None:
        raise ValueError("wilting_point and field_capacity are required when normalized=True.")
    aw = float(field_capacity) - float(wilting_point)
    if aw <= 0.0:
        raise ValueError(f"Field capacity ({field_capacity}) must exceed wilting point ({wilting_point}).")
    return float(err / aw)


def soil_moisture_to_storage(
    soil_moisture: float,
    root_depth_m: float,
) -> float:
    """Convert soil moisture content to equivalent root-zone water storage depth (mm).

    Storage [mm] = 1000 * theta * Zr

    Handles both percentage (e.g. 55%) and volumetric fraction (e.g. 0.55 m3/m3):
        If soil_moisture > 1.0, it is treated as a percentage (theta = soil_moisture / 100.0).

    Args:
        soil_moisture: Soil moisture as percentage (0-100%) or volumetric fraction (0.0-1.0 m3/m3).
        root_depth_m: Effective crop root-zone depth in meters (Zr).

    Returns:
        float: Equivalent water depth stored in the root zone in mm.
    """
    sm = max(0.0, float(soil_moisture))
    zr = max(0.01, float(root_depth_m))
    theta = (sm / 100.0) if sm > 1.0 else sm
    return float(1000.0 * theta * zr)


def storage_to_soil_moisture(
    storage_mm: float,
    root_depth_m: float,
    as_percent: bool = True,
) -> float:
    """Convert root-zone water storage depth (mm) back to soil moisture content.

    theta = Storage [mm] / (1000 * Zr)

    Args:
        storage_mm: Water depth in root zone in mm.
        root_depth_m: Effective root-zone depth in meters (Zr).
        as_percent: If True, returns percentage (0-100%). If False, returns fraction (0.0-1.0 m3/m3).

    Returns:
        float: Volumetric soil moisture.
    """
    s = max(0.0, float(storage_mm))
    zr = max(0.01, float(root_depth_m))
    theta = s / (1000.0 * zr)
    if as_percent:
        return float(theta * 100.0)
    return float(theta)


def calculate_taw(
    field_capacity: float,
    wilting_point: float,
    root_depth_m: float,
) -> float:
    """Calculate Total Available Water (TAW) in the root zone (FAO-56 Eq. 82).

    TAW = 1000 * (FC - WP) * Zr

    Args:
        field_capacity: Volumetric moisture at FC (fraction or %).
        wilting_point: Volumetric moisture at WP (fraction or %).
        root_depth_m: Root-zone depth in meters (Zr).

    Returns:
        float: Total available water in mm.
    """
    fc = (field_capacity / 100.0) if field_capacity > 1.0 else field_capacity
    wp = (wilting_point / 100.0) if wilting_point > 1.0 else wilting_point
    zr = max(0.01, float(root_depth_m))

    if fc <= wp:
        raise ValueError(f"Field capacity ({fc}) must exceed wilting point ({wp}).")

    return float(1000.0 * (fc - wp) * zr)


def calculate_raw(
    taw_mm: float,
    depletion_fraction_p: float = 0.50,
) -> float:
    """Calculate Readily Available Water (RAW) in the root zone (FAO-56 Eq. 83).

    RAW = p * TAW

    Where p is the crop average fraction of TAW that can be depleted from the root zone
    before moisture stress occurs (FAO-56 Table 22).

    Args:
        taw_mm: Total available water in mm.
        depletion_fraction_p: Crop depletion fraction p in (0.0, 1.0]. Default 0.50.

    Returns:
        float: Readily available water in mm.
    """
    taw = max(0.0, float(taw_mm))
    p = np.clip(float(depletion_fraction_p), 0.05, 1.0)
    return float(p * taw)


def calculate_infiltration(
    incoming_water_mm: float,
    infiltration_rate_mm_h: float,
    timestep_minutes: int = 1,
    current_moisture_pct: Optional[float] = None,
    saturation_pct: Optional[float] = None,
) -> Tuple[float, float]:
    """Partition incoming surface water (irrigation + rain) into infiltration and runoff.

    Maximum timestep infiltration capacity:
        I_max = infiltration_rate_mm_h * (timestep_minutes / 60)

    If current moisture is at or above saturation, infiltration is blocked and water runs off.

    Args:
        incoming_water_mm: Total surface water applied in current timestep (mm).
        infiltration_rate_mm_h: Maximum soil infiltration rate in mm/hour.
        timestep_minutes: Timestep duration in minutes.
        current_moisture_pct: Optional current moisture level (%).
        saturation_pct: Optional soil saturation capacity (%).

    Returns:
        Tuple[float, float]: (infiltrated_water_mm, surface_runoff_mm).
    """
    w_in = max(0.0, float(incoming_water_mm))
    if w_in < 1e-9:
        return 0.0, 0.0

    # Check saturation barrier
    if current_moisture_pct is not None and saturation_pct is not None:
        if current_moisture_pct >= saturation_pct - 1e-4:
            # Soil pore space completely filled; 100% surface runoff
            return 0.0, w_in

    timestep_hours = float(timestep_minutes) / 60.0
    i_max = max(0.0, float(infiltration_rate_mm_h) * timestep_hours)

    infiltrated = min(w_in, i_max)
    runoff = w_in - infiltrated
    return float(infiltrated), float(runoff)


def calculate_drainage(
    current_storage_mm: float,
    field_capacity_storage_mm: float,
    drainage_parameter: float = 0.08,
    saturation_storage_mm: Optional[float] = None,
) -> float:
    """Calculate gravity drainage / deep percolation below the root zone.

    Drainage occurs exclusively when moisture exceeds Field Capacity (FC):
        Excess = max(0.0, Storage - Storage_FC)
        Drainage = drainage_parameter * Excess

    If storage exceeds Saturation, the excess above saturation drains immediately.

    Args:
        current_storage_mm: Root-zone water storage after infiltration and ETc (mm).
        field_capacity_storage_mm: Water storage corresponding to Field Capacity (mm).
        drainage_parameter: Soil gravity percolation rate factor (0.0 to 1.0).
        saturation_storage_mm: Optional storage at saturation (mm).

    Returns:
        float: Drainage depth in mm.
    """
    s = max(0.0, float(current_storage_mm))
    s_fc = max(0.0, float(field_capacity_storage_mm))
    alpha_d = np.clip(float(drainage_parameter), 0.0, 1.0)

    if s <= s_fc:
        return 0.0

    excess = s - s_fc
    drainage = alpha_d * excess

    # Check if beyond saturation
    if saturation_storage_mm is not None and s > saturation_storage_mm:
        drainage = max(drainage, s - saturation_storage_mm)

    return float(min(excess, max(0.0, drainage)))
