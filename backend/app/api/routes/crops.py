"""Crops Reference Router."""

from typing import List, Dict, Any
from pathlib import Path
import pandas as pd
from fastapi import APIRouter

router = APIRouter(prefix="/crops", tags=["Crops"])

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
CROP_DB_PATH = ROOT_DIR / "data" / "crop_database.csv"


@router.get("", response_model=List[Dict[str, Any]])
def get_crops():
    """Retrieve agronomic crop database records including Kc and root parameters."""
    if CROP_DB_PATH.exists():
        df = pd.read_csv(CROP_DB_PATH)
        return df.to_dict(orient="records")
    return [
        {"crop": "Tomato", "kc_initial": 0.60, "kc_mid": 1.15, "kc_end": 0.80, "depletion_fraction_p": 0.40},
        {"crop": "Wheat", "kc_initial": 0.30, "kc_mid": 1.15, "kc_end": 0.25, "depletion_fraction_p": 0.55},
        {"crop": "Maize", "kc_initial": 0.30, "kc_mid": 1.20, "kc_end": 0.35, "depletion_fraction_p": 0.55},
        {"crop": "Potato", "kc_initial": 0.50, "kc_mid": 1.15, "kc_end": 0.75, "depletion_fraction_p": 0.35},
        {"crop": "Cotton", "kc_initial": 0.35, "kc_mid": 1.20, "kc_end": 0.60, "depletion_fraction_p": 0.65},
    ]
