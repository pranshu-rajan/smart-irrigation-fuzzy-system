"""Unit tests for soil physical parameters, conversions, TAW, RAW, RSM, and hydraulic limits.

Tests:
1. Soil parameter lookup from soil_database.csv
2. Relative Soil Moisture (RSM) normalization and boundary clamping
3. Scale-invariance of RSM (fractions vs. percentages)
4. Soil moisture tracking error calculation
5. Bidirectional conversion between volumetric moisture and root-zone water storage (mm)
6. Total Available Water (TAW) and Readily Available Water (RAW) according to FAO-56
7. Infiltration capacity constraints and runoff partitioning
8. Infiltration blocking at saturation
9. Gravity drainage activation strictly above field capacity
"""

import pytest
import numpy as np

from models.soil import (
    SoilParameterManager,
    calculate_relative_soil_moisture,
    calculate_rsm,
    calculate_moisture_error,
    soil_moisture_to_storage,
    storage_to_soil_moisture,
    calculate_taw,
    calculate_raw,
    calculate_infiltration,
    calculate_drainage,
)
from config.schemas import SoilType


def test_soil_parameter_manager_lookup():
    """Verify soil parameter lookups from canonical soil_database.csv."""
    loam = SoilParameterManager.get_soil_properties(SoilType.LOAM)
    assert loam["field_capacity_pct"] == pytest.approx(28.0, abs=0.1)
    assert loam["wilting_point_pct"] == pytest.approx(14.0, abs=0.1)
    assert loam["infiltration_rate_mm_h"] == pytest.approx(20.0, abs=0.1)

    sandy = SoilParameterManager.get_soil_properties("Sandy")
    assert sandy["field_capacity_pct"] == pytest.approx(18.0, abs=0.1)
    assert sandy["wilting_point_pct"] == pytest.approx(8.0, abs=0.1)
    assert sandy["infiltration_rate_mm_h"] == pytest.approx(45.0, abs=0.1)

    clay = SoilParameterManager.get_soil_properties(SoilType.CLAY)
    assert clay["field_capacity_pct"] == pytest.approx(36.0, abs=0.1)
    assert clay["wilting_point_pct"] == pytest.approx(20.0, abs=0.1)
    assert clay["drainage_parameter"] == pytest.approx(0.03, abs=0.01)


def test_calculate_relative_soil_moisture_bounds():
    """Verify RSM normalization, wilting point (0.0), field capacity (1.0), and bounds."""
    # Exactly at WP -> RSM = 0.0
    assert calculate_relative_soil_moisture(25.0, 25.0, 70.0) == pytest.approx(0.0, abs=1e-5)

    # Exactly at FC -> RSM = 1.0
    assert calculate_relative_soil_moisture(70.0, 25.0, 70.0) == pytest.approx(1.0, abs=1e-5)

    # Midpoint -> RSM = 0.50
    mid = 25.0 + 0.5 * (70.0 - 25.0)  # 47.5
    assert calculate_relative_soil_moisture(mid, 25.0, 70.0) == pytest.approx(0.50, abs=1e-5)

    # Below WP -> clamped to 0.0
    assert calculate_relative_soil_moisture(20.0, 25.0, 70.0) == 0.0

    # Above FC -> clamped to 1.0
    assert calculate_relative_soil_moisture(80.0, 25.0, 70.0) == 1.0

    # Alias check
    assert calculate_rsm(mid, 25.0, 70.0) == pytest.approx(0.50, abs=1e-5)


def test_rsm_scale_invariance():
    """Verify that RSM yields identical values whether using working percent or volumetric fraction."""
    # Working percentage scale (e.g. Zone 1: SM=55%, WP=25%, FC=70%)
    rsm_pct = calculate_relative_soil_moisture(55.0, 25.0, 70.0)

    # Volumetric fraction scale (SM=0.55, WP=0.25, FC=0.70)
    rsm_frac = calculate_relative_soil_moisture(0.55, 0.25, 0.70)

    assert rsm_pct == pytest.approx(rsm_frac, abs=1e-6)
    assert rsm_pct == pytest.approx(30.0 / 45.0, abs=1e-5)


def test_moisture_error_tracking():
    """Verify moisture tracking error e(t) = target - current."""
    # Under-irrigated (deficit): target 60%, current 55% -> error = +5.0%
    err_dry = calculate_moisture_error(60.0, 55.0)
    assert err_dry == pytest.approx(5.0, abs=1e-5)

    # Over-irrigated: target 60%, current 65% -> error = -5.0%
    err_wet = calculate_moisture_error(60.0, 65.0)
    assert err_wet == pytest.approx(-5.0, abs=1e-5)

    # Normalized error by available water range (45%) -> 5.0 / 45.0 = 0.1111
    err_norm = calculate_moisture_error(60.0, 55.0, normalized=True, wilting_point=25.0, field_capacity=70.0)
    assert err_norm == pytest.approx(5.0 / 45.0, abs=1e-5)


def test_storage_conversion_bidirectional():
    """Verify bidirectional conversion between moisture and water depth (Storage = 1000 * theta * Zr)."""
    zr = 0.70  # meters
    sm_pct = 55.0  # %

    # Storage = 1000 * 0.55 * 0.70 = 385.0 mm
    s_mm = soil_moisture_to_storage(sm_pct, zr)
    assert s_mm == pytest.approx(385.0, abs=1e-4)

    # Invert back to percentage
    sm_back = storage_to_soil_moisture(s_mm, zr, as_percent=True)
    assert sm_back == pytest.approx(55.0, abs=1e-4)

    # Invert back to fraction
    sm_frac = storage_to_soil_moisture(s_mm, zr, as_percent=False)
    assert sm_frac == pytest.approx(0.55, abs=1e-5)


def test_taw_and_raw_calculation():
    """Verify TAW = 1000*(FC-WP)*Zr and RAW = p*TAW according to FAO-56."""
    zr = 0.70
    fc = 70.0
    wp = 25.0
    p = 0.40  # Tomato depletion fraction

    # TAW = 1000 * (0.70 - 0.25) * 0.70 = 315.0 mm
    taw = calculate_taw(fc, wp, zr)
    assert taw == pytest.approx(315.0, abs=1e-4)

    # RAW = 0.40 * 315.0 = 126.0 mm
    raw = calculate_raw(taw, p)
    assert raw == pytest.approx(126.0, abs=1e-4)


def test_infiltration_capacity_limiting():
    """Verify infiltration rate partitioning between infiltrated depth and surface runoff."""
    infil_rate = 20.0  # mm/hour
    timestep = 15      # minutes -> max capacity = 20 * (15/60) = 5.0 mm

    # Water below capacity: 3.0 mm applied -> 3.0 mm infiltrated, 0.0 mm runoff
    inf1, ro1 = calculate_infiltration(3.0, infil_rate, timestep)
    assert inf1 == pytest.approx(3.0, abs=1e-5)
    assert ro1 == pytest.approx(0.0, abs=1e-5)

    # Water exceeding capacity: 8.0 mm applied -> 5.0 mm infiltrated, 3.0 mm runoff
    inf2, ro2 = calculate_infiltration(8.0, infil_rate, timestep)
    assert inf2 == pytest.approx(5.0, abs=1e-5)
    assert ro2 == pytest.approx(3.0, abs=1e-5)
    assert (inf2 + ro2) == pytest.approx(8.0, abs=1e-5)


def test_infiltration_blocked_at_saturation():
    """Verify that when soil is at or above saturation, incoming water is rejected as runoff."""
    infiltrated, runoff = calculate_infiltration(
        incoming_water_mm=10.0,
        infiltration_rate_mm_h=30.0,
        timestep_minutes=1,
        current_moisture_pct=85.0,
        saturation_pct=85.0,
    )
    assert infiltrated == 0.0
    assert runoff == pytest.approx(10.0, abs=1e-5)


def test_drainage_occurs_only_above_fc():
    """Verify deep percolation occurs strictly when storage exceeds Field Capacity."""
    zr = 0.70
    fc = 70.0
    s_fc = soil_moisture_to_storage(fc, zr)  # 490.0 mm
    drain_param = 0.08

    # Below FC (Storage = 400 mm) -> Drainage = 0.0 mm
    d_sub = calculate_drainage(400.0, s_fc, drain_param)
    assert d_sub == 0.0

    # Above FC (Storage = 510 mm) -> Excess = 20 mm -> Drainage = 0.08 * 20 = 1.6 mm
    d_sup = calculate_drainage(510.0, s_fc, drain_param)
    assert d_sup == pytest.approx(1.6, abs=1e-4)
