"""Default agronomic and physical constants for the Smart Multizone Irrigation System.

Provides standard definitions for:
- Crops: Tomato, Wheat, Maize, Potato, Cotton (FAO-56 derived)
- Soils: Loam, Sandy, Clay (USDA/FAO baseline properties)
- Initial 3-Zone Configuration specified in project requirements (Section 5 & 6)
"""

from typing import Dict, List
from .schemas import (
    CropParameters,
    SoilParameters,
    ZoneConfig,
    CropType,
    SoilType,
    GrowthStage,
)

# Standard Soil Textural Library (Section 6 Model Assumptions)
DEFAULT_SOILS: Dict[SoilType, SoilParameters] = {
    SoilType.LOAM: SoilParameters(
        soil_type=SoilType.LOAM,
        field_capacity=70.0,
        wilting_point=25.0,
        saturation=85.0,
        infiltration_rate_mm_h=20.0,
        drainage_parameter=0.08,
    ),
    SoilType.SANDY: SoilParameters(
        soil_type=SoilType.SANDY,
        field_capacity=60.0,
        wilting_point=18.0,
        saturation=78.0,
        infiltration_rate_mm_h=45.0,
        drainage_parameter=0.18,
    ),
    SoilType.CLAY: SoilParameters(
        soil_type=SoilType.CLAY,
        field_capacity=75.0,
        wilting_point=30.0,
        saturation=90.0,
        infiltration_rate_mm_h=5.0,
        drainage_parameter=0.03,
    ),
    SoilType.SANDY_LOAM: SoilParameters(
        soil_type=SoilType.SANDY_LOAM,
        field_capacity=65.0,
        wilting_point=20.0,
        saturation=80.0,
        infiltration_rate_mm_h=30.0,
        drainage_parameter=0.12,
    ),
    SoilType.SILTY_CLAY: SoilParameters(
        soil_type=SoilType.SILTY_CLAY,
        field_capacity=72.0,
        wilting_point=28.0,
        saturation=88.0,
        infiltration_rate_mm_h=6.0,
        drainage_parameter=0.04,
    ),
}

# Standard Crop Agronomic Library (FAO-56 derived)
DEFAULT_CROPS: Dict[CropType, CropParameters] = {
    CropType.TOMATO: CropParameters(
        name=CropType.TOMATO.value,
        growth_stage=GrowthStage.MID_SEASON,
        kc=1.15,
        root_depth_m=0.7,
    ),
    CropType.WHEAT: CropParameters(
        name=CropType.WHEAT.value,
        growth_stage=GrowthStage.DEVELOPMENT,
        kc=0.85,
        root_depth_m=0.9,
    ),
    CropType.MAIZE: CropParameters(
        name=CropType.MAIZE.value,
        growth_stage=GrowthStage.MID_SEASON,
        kc=1.20,
        root_depth_m=1.0,
    ),
    CropType.POTATO: CropParameters(
        name=CropType.POTATO.value,
        growth_stage=GrowthStage.INITIAL,
        kc=0.50,
        root_depth_m=0.5,
    ),
    CropType.COTTON: CropParameters(
        name=CropType.COTTON.value,
        growth_stage=GrowthStage.INITIAL,
        kc=0.35,
        root_depth_m=1.2,
    ),
}


def get_default_zones() -> List[ZoneConfig]:
    """Instantiate the standard 3-zone agricultural testbed configuration.

    Zone 1:
        Crop = Tomato, Soil = Loam, Area = 100 m2
        FC = 70%, WP = 25%, Initial SM = 55%, Target SM = 60%, Priority = 2
    Zone 2:
        Crop = Wheat, Soil = Sandy, Area = 120 m2
        FC = 60%, WP = 18%, Initial SM = 42%, Target SM = 55%, Priority = 1
    Zone 3:
        Crop = Maize, Soil = Clay, Area = 80 m2
        FC = 75%, WP = 30%, Initial SM = 65%, Target SM = 65%, Priority = 3

    Returns:
        List[ZoneConfig]: List of 3 validated ZoneConfig instances.
    """
    return [
        ZoneConfig(
            zone_id=1,
            name="Zone 1 - Tomato / Loam",
            crop=DEFAULT_CROPS[CropType.TOMATO],
            soil=DEFAULT_SOILS[SoilType.LOAM],
            area_m2=100.0,
            initial_moisture=55.0,
            target_moisture=60.0,
            priority=2,
        ),
        ZoneConfig(
            zone_id=2,
            name="Zone 2 - Wheat / Sandy",
            crop=DEFAULT_CROPS[CropType.WHEAT],
            soil=DEFAULT_SOILS[SoilType.SANDY],
            area_m2=120.0,
            initial_moisture=42.0,
            target_moisture=55.0,
            priority=1,
        ),
        ZoneConfig(
            zone_id=3,
            name="Zone 3 - Maize / Clay",
            crop=DEFAULT_CROPS[CropType.MAIZE],
            soil=DEFAULT_SOILS[SoilType.CLAY],
            area_m2=80.0,
            initial_moisture=65.0,
            target_moisture=65.0,
            priority=3,
        ),
    ]
