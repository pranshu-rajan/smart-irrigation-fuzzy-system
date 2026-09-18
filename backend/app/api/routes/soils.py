"""Soils Reference Router."""

from typing import List, Dict, Any
from pathlib import Path
import pandas as pd
from fastapi import APIRouter

router = APIRouter(prefix="/soils", tags=["Soils"])

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
SOIL_DB_PATH = ROOT_DIR / "data" / "soil_database.csv"


@router.get("", response_model=List[Dict[str, Any]])
def get_soils():
    """Retrieve soil hydraulic properties database records."""
    if SOIL_DB_PATH.exists():
        df = pd.read_csv(SOIL_DB_PATH)
        return df.to_dict(orient="records")
    return [
        {"soil_type": "Loam", "field_capacity_pct": 28.0, "wilting_point_pct": 14.0, "available_water_pct": 14.0, "saturation_pct": 46.0},
        {"soil_type": "Sandy", "field_capacity_pct": 18.0, "wilting_point_pct": 8.0, "available_water_pct": 10.0, "saturation_pct": 38.0},
        {"soil_type": "Clay", "field_capacity_pct": 36.0, "wilting_point_pct": 20.0, "available_water_pct": 16.0, "saturation_pct": 52.0},
        {"soil_type": "Sandy Loam", "field_capacity_pct": 22.0, "wilting_point_pct": 10.0, "available_water_pct": 12.0, "saturation_pct": 42.0},
        {"soil_type": "Silty Clay", "field_capacity_pct": 34.0, "wilting_point_pct": 19.0, "available_water_pct": 15.0, "saturation_pct": 50.0},
    ]
