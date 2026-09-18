"""
Membership Function Factory and Configuration Loader.

Provides factory functions for creating membership sets and complete fuzzy variables
from declarative JSON configurations or Python dictionaries.
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Union

import numpy as np

from fuzzy_engine.membership import triangular_mf, trapezoidal_mf
from fuzzy_engine.variables import FuzzyUniverse, MembershipSet, FuzzyVariable


def create_triangular_mf(a: float, b: float, c: float) -> Callable[[Union[float, np.ndarray]], Union[float, np.ndarray]]:
    """Factory creating a reusable triangular membership function callable."""
    return lambda x: triangular_mf(x, a, b, c)


def create_trapezoidal_mf(a: float, b: float, c: float, d: float) -> Callable[[Union[float, np.ndarray]], Union[float, np.ndarray]]:
    """Factory creating a reusable trapezoidal membership function callable."""
    return lambda x: trapezoidal_mf(x, a, b, c, d)


def create_membership_set(
    name: str,
    display_name: str,
    mf_type: str,
    params: List[float],
) -> MembershipSet:
    """Factory creating a validated MembershipSet instance."""
    # Map common aliases to canonical types
    type_map = {
        "trimf": "triangular",
        "triangular": "triangular",
        "trapmf": "trapezoidal",
        "trapezoidal": "trapezoidal",
    }
    canon_type = type_map.get(mf_type.lower().strip(), mf_type.lower().strip())
    return MembershipSet(name=name, display_name=display_name, mf_type=canon_type, params=params)


def create_fuzzy_variable_from_dict(var_dict: Dict[str, Any]) -> FuzzyVariable:
    """
    Construct a FuzzyVariable instance from a declarative dictionary definition.

    Handles both direct key structures (min, max, resolution) and nested
    'universe' sub-dictionaries, as well as set mappings with 'trimf'/'trapmf'.
    """
    name = var_dict["name"]
    display_name = var_dict.get("display_name", name.replace("_", " ").title())
    unit = var_dict.get("unit", "")
    role = var_dict.get("fis_role", var_dict.get("role", "input"))
    fis_groups = var_dict.get("associated_fis", var_dict.get("fis_groups", []))
    if isinstance(fis_groups, str):
        fis_groups = [f.strip() for f in fis_groups.split("/")]
    description = var_dict.get("description", "")

    # Universe extraction
    if "universe" in var_dict:
        univ_dict = var_dict["universe"]
        min_val = univ_dict["min"]
        max_val = univ_dict["max"]
        resolution = univ_dict.get("resolution", 0.1)
        num_points = univ_dict.get("num_points", 501)
    else:
        min_val = var_dict["min"]
        max_val = var_dict["max"]
        res_raw = var_dict.get("resolution", 200)
        # If resolution is an integer >= 10, treat as num_points
        if isinstance(res_raw, int) and res_raw >= 10:
            num_points = res_raw
            resolution = (max_val - min_val) / res_raw
        else:
            resolution = float(res_raw)
            num_points = int(np.round((max_val - min_val) / resolution)) + 1

    universe = FuzzyUniverse(
        min_val=min_val,
        max_val=max_val,
        resolution=resolution,
        num_points=num_points,
    )

    # Sets extraction
    sets: Dict[str, MembershipSet] = {}
    sets_data = var_dict.get("sets", var_dict.get("membership_sets", {}))

    if isinstance(sets_data, list):
        for set_dict in sets_data:
            m_set = create_membership_set(
                name=set_dict["name"],
                display_name=set_dict.get("display_name", set_dict["name"]),
                mf_type=set_dict["type"],
                params=set_dict["parameters"],
            )
            sets[m_set.name] = m_set
    elif isinstance(sets_data, dict):
        for raw_name, set_info in sets_data.items():
            # Machine identifier: e.g. "Very Dry" -> "very_dry"
            m_name = raw_name.lower().replace(" ", "_")
            d_name = raw_name
            m_set = create_membership_set(
                name=m_name,
                display_name=d_name,
                mf_type=set_info["type"],
                params=set_info["parameters"],
            )
            sets[m_name] = m_set

    return FuzzyVariable(
        name=name,
        display_name=display_name,
        unit=unit,
        universe=universe,
        sets=sets,
        role=role,
        fis_groups=fis_groups,
        description=description,
    )


def load_fuzzy_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """Load raw JSON fuzzy configuration from disk."""
    p = Path(config_path)
    if not p.exists():
        raise FileNotFoundError(f"Fuzzy configuration file not found at: {config_path}")

    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def build_all_fuzzy_variables(config_path: Union[str, Path]) -> Dict[str, FuzzyVariable]:
    """
    Load configuration and build all FuzzyVariable instances.

    Parameters
    ----------
    config_path : str or Path
        Path to config/fuzzy_config.json.

    Returns
    -------
    dict of {str: FuzzyVariable}
        Dictionary mapping variable names to their FuzzyVariable instances.
    """
    cfg = load_fuzzy_config(config_path)
    variables = {}
    raw_vars = cfg.get("variables", {})

    if isinstance(raw_vars, dict):
        for var_name, var_def in raw_vars.items():
            # Ensure name is present in var_def
            if "name" not in var_def:
                var_def["name"] = var_name
            fv = create_fuzzy_variable_from_dict(var_def)
            variables[fv.name] = fv
    elif isinstance(raw_vars, list):
        for var_def in raw_vars:
            fv = create_fuzzy_variable_from_dict(var_def)
            variables[fv.name] = fv

    return variables
