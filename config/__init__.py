"""Configuration package for the Smart Multizone Irrigation System."""

import json
from pathlib import Path
from typing import Union
from .schemas import (
    SystemConfig,
    SimulationConfig,
    ControllerConfig,
    ZoneConfig,
    CropParameters,
    SoilParameters,
    WeatherParameters,
    CropType,
    SoilType,
    GrowthStage,
    SimulationScenario,
    DefuzzificationMethod,
    ControllerType,
)
from .defaults import (
    DEFAULT_SOILS,
    DEFAULT_CROPS,
    get_default_zones,
)


def load_config(config_path: Union[str, Path] = "config/config.json") -> SystemConfig:
    """Load and parse the JSON configuration file into a validated SystemConfig object.

    Args:
        config_path: Relative or absolute path to the configuration JSON file.

    Returns:
        SystemConfig: Pydantic validated configuration object.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValidationError: If JSON structure does not conform to SystemConfig schema.
    """
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found at: {path.resolve()}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cfg = SystemConfig(**data)
    if cfg.zone_configs is None:
        cfg.zone_configs = get_default_zones()
    return cfg


__all__ = [
    "SystemConfig",
    "SimulationConfig",
    "ControllerConfig",
    "ZoneConfig",
    "CropParameters",
    "SoilParameters",
    "WeatherParameters",
    "CropType",
    "SoilType",
    "GrowthStage",
    "SimulationScenario",
    "DefuzzificationMethod",
    "ControllerType",
    "DEFAULT_SOILS",
    "DEFAULT_CROPS",
    "get_default_zones",
    "load_config",
]
