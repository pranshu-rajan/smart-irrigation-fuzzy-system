"""Persistent active PSO calibration for the production fuzzy controller.

The active parameter file is deliberately separate from the rule base.  PSO remains
an offline optimizer, while the selected calibration becomes the parameterization
used by the online closed-loop simulator after it has been validated and activated.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from optimization.parameter_space import FuzzyParameterSpace

DEFAULT_PATH = Path("config/active_fuzzy_parameters.json")


def load_active_parameters(path: Path | str = DEFAULT_PATH) -> Optional[Dict[str, float]]:
    p = Path(path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        params = data.get("parameters") if isinstance(data, dict) else None
        if not isinstance(params, dict) or not params:
            return None
        return {str(k): float(v) for k, v in params.items()}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def save_active_parameters(
    parameters: Dict[str, float],
    *,
    path: Path | str = DEFAULT_PATH,
    source: str = "PSO",
    run_id: Optional[str] = None,
) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload: Dict[str, Any] = {
        "schema_version": 1,
        "status": "active",
        "source": source,
        "run_id": run_id,
        "parameters": {k: float(v) for k, v in parameters.items()},
    }
    p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def build_active_main_irrigation_fis(path: Path | str = DEFAULT_PATH):
    """Return a PSO-calibrated MainIrrigationFIS when an active calibration exists."""
    params = load_active_parameters(path)
    if not params:
        return None
    space = FuzzyParameterSpace()
    theta = space.dict_to_vector(params)
    return space.build_fis(theta)
