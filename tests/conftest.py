"""Global pytest fixtures for test suite."""

import pytest
from pathlib import Path
from config import (
    load_config,
    SystemConfig,
    DEFAULT_SOILS,
    DEFAULT_CROPS,
    get_default_zones,
    CropType,
    SoilType,
)


@pytest.fixture
def project_root() -> Path:
    """Return the absolute path to the project root directory."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def base_config() -> SystemConfig:
    """Return a validated base SystemConfig instance."""
    return load_config()


@pytest.fixture
def default_zones():
    """Return the standard 3-zone configuration list."""
    return get_default_zones()


@pytest.fixture
def soil_library():
    """Return standard soil parameters dictionary."""
    return DEFAULT_SOILS


@pytest.fixture
def crop_library():
    """Return standard crop parameters dictionary."""
    return DEFAULT_CROPS
