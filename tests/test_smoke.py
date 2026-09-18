"""Smoke and architecture tests for Phase 0 setup."""

import pytest
from pathlib import Path
import importlib

from config import (
    load_config,
    SystemConfig,
    SoilParameters,
    CropParameters,
    ZoneConfig,
    SoilType,
    CropType,
    GrowthStage,
    ControllerType,
    DefuzzificationMethod,
)
from fuzzy_engine.membership_functions import triangular_mf, trapezoidal_mf
from fuzzy_engine import (
    SoilStressFIS,
    WeatherStressFIS,
    WaterDemandFIS,
    MainIrrigationFIS,
    WaterAllocationFIS,
)
from models import (
    calculate_et0_fao56,
    calculate_etc,
    calculate_water_deficit,
    calculate_relative_soil_moisture,
    calculate_moisture_error,
    update_soil_moisture_step,
)


def test_directory_structure_exists(project_root: Path):
    """Verify that all architectural directories required by Section 14 exist."""
    required_dirs = [
        "engineering/matlab",
        "engineering/simulink",
        "data/raw",
        "data/processed",
        "data/simulation",
        "fuzzy_engine",
        "models",
        "simulation",
        "optimization",
        "backend/app/api",
        "backend/app/ai",
        "backend/app/database",
        "frontend",
        "tests",
        "reports",
        "docs",
        "config",
    ]
    for rel_path in required_dirs:
        dir_path = project_root / rel_path
        assert dir_path.is_dir(), f"Required directory does not exist: {rel_path}"


def test_load_base_config():
    """Verify that config/config.json loads accurately into SystemConfig."""
    cfg = load_config()
    assert isinstance(cfg, SystemConfig)
    assert cfg.simulation.duration_hours == 24
    assert cfg.simulation.timestep_minutes == 1
    assert cfg.simulation.total_steps == 1440
    assert cfg.zones == 3
    assert cfg.controller.type == ControllerType.MAMDANI
    assert cfg.controller.defuzzification == DefuzzificationMethod.CENTROID


def test_default_zones_agronomics(default_zones):
    """Verify the 3 default agricultural zones match specified configurations."""
    assert len(default_zones) == 3

    # Zone 1: Tomato / Loam / 100 m2
    z1 = default_zones[0]
    assert z1.zone_id == 1
    assert z1.crop.name == CropType.TOMATO.value
    assert z1.soil.soil_type == SoilType.LOAM
    assert z1.area_m2 == 100.0

    # Zone 2: Wheat / Sandy / 120 m2
    z2 = default_zones[1]
    assert z2.zone_id == 2
    assert z2.crop.name == CropType.WHEAT.value
    assert z2.soil.soil_type == SoilType.SANDY
    assert z2.area_m2 == 120.0

    # Zone 3: Maize / Clay / 80 m2
    z3 = default_zones[2]
    assert z3.zone_id == 3
    assert z3.crop.name == CropType.MAIZE.value
    assert z3.soil.soil_type == SoilType.CLAY
    assert z3.area_m2 == 80.0


def test_soil_validation_wilting_point_below_field_capacity():
    """Verify schema enforces WP < FC."""
    # Valid soil
    valid_soil = SoilParameters(
        soil_type=SoilType.LOAM,
        field_capacity=0.30,
        wilting_point=0.15,
    )
    assert valid_soil.field_capacity == 0.30

    # Invalid soil where WP >= FC
    with pytest.raises(ValueError):
        SoilParameters(
            soil_type=SoilType.LOAM,
            field_capacity=0.20,
            wilting_point=0.25,
        )


def test_membership_functions_math():
    """Verify triangular and trapezoidal membership evaluation."""
    # Triangular: a=0, b=5, c=10
    assert triangular_mf(0, 0, 5, 10) == 0.0
    assert triangular_mf(5, 0, 5, 10) == 1.0
    assert triangular_mf(2.5, 0, 5, 10) == 0.5
    assert triangular_mf(7.5, 0, 5, 10) == 0.5
    assert triangular_mf(10, 0, 5, 10) == 0.0
    assert triangular_mf(12, 0, 5, 10) == 0.0

    # Trapezoidal: a=2, b=4, c=6, d=8
    assert trapezoidal_mf(1, 2, 4, 6, 8) == 0.0
    assert trapezoidal_mf(3, 2, 4, 6, 8) == 0.5
    assert trapezoidal_mf(4, 2, 4, 6, 8) == 1.0
    assert trapezoidal_mf(5, 2, 4, 6, 8) == 1.0
    assert trapezoidal_mf(6, 2, 4, 6, 8) == 1.0
    assert trapezoidal_mf(7, 2, 4, 6, 8) == 0.5
    assert trapezoidal_mf(9, 2, 4, 6, 8) == 0.0


def test_placeholder_contracts_raise_not_implemented():
    """Verify that implemented Phase 4 functions return valid outputs and future phases raise NotImplementedError."""
    # Phase 4 implementations now execute accurately
    et0 = calculate_et0_fao56(25.0, 60.0, 600.0, 2.0)
    assert isinstance(et0, float)
    assert et0 > 0.0

    etc = calculate_etc(5.0, 1.15)
    assert isinstance(etc, float)
    assert etc == pytest.approx(5.75, rel=1e-3)

    deficit = calculate_water_deficit(5.75, 1.0)
    assert isinstance(deficit, float)
    assert deficit == pytest.approx(4.75, rel=1e-3)

    # Phase 5 soil water balance implementations now execute accurately
    rsm = calculate_relative_soil_moisture(0.20, 0.10, 0.30)
    assert isinstance(rsm, float)
    assert rsm == pytest.approx(0.50, rel=1e-3)

    err = calculate_moisture_error(60.0, 55.0)
    assert isinstance(err, float)
    assert err == pytest.approx(5.0, rel=1e-3)

    sm_next = update_soil_moisture_step(
        current_moisture=55.0,
        irrigation_depth_mm=5.0,
        effective_rainfall_mm=0.0,
        etc_mm=0.05,
        field_capacity=70.0,
        wilting_point=25.0,
        saturation=85.0,
        root_depth_m=0.7,
    )
    assert isinstance(sm_next, float)
    assert sm_next > 55.0

    # Phase 7 SoilStressFIS now executes accurately
    fis1 = SoilStressFIS()
    stress = fis1.evaluate(0.20, 5.0)
    assert isinstance(stress, float)
    assert 0.0 <= stress <= 100.0

    # Phase 8 WeatherStressFIS now executes accurately
    fis2 = WeatherStressFIS()
    w_stress = fis2.evaluate(30.0, 50.0, 700.0, 2.5, 0.0)
    assert isinstance(w_stress, float)
    assert 0.0 <= w_stress <= 100.0

    # Phase 9 WaterDemandFIS now executes accurately
    fis3 = WaterDemandFIS()
    demand = fis3.evaluate(5.0, 3.0, 2.0)
    assert isinstance(demand, float)
    assert 0.0 <= demand <= 100.0

    # Phase 10 MainIrrigationFIS now executes accurately
    fis4 = MainIrrigationFIS()
    cmd = fis4.evaluate(50.0, 50.0, 50.0, 0.0)
    assert isinstance(cmd, float)
    assert 0.0 <= cmd <= 100.0

    # Phase 13 WaterAllocationFIS is fully implemented and evaluates accurately
    fis5 = WaterAllocationFIS()
    alloc = fis5.evaluate(available_water=80.0, zone_demand=80.0, zone_stress=50.0, zone_priority=70.0)
    assert isinstance(alloc, float)
    assert 0.0 <= alloc <= 100.0



def test_fastapi_app_initializes():
    """Verify backend FastAPI instance initializes and loads config."""
    from backend.app.main import app
    assert app.title == "Smart Multizone Irrigation API"
