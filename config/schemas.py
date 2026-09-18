"""Configuration and parameter data models for the Smart Multizone Irrigation System.

Provides strictly validated Pydantic schemas for agricultural zones, crop definitions,
soil characteristics, environmental inputs, and simulation settings.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class DefuzzificationMethod(str, Enum):
    """Supported defuzzification methods for Mamdani inference."""
    CENTROID = "centroid"
    BISECTOR = "bisector"
    MOM = "mom"  # Mean of Maximum
    SOM = "som"  # Smallest of Maximum
    LOM = "lom"  # Largest of Maximum


class ControllerType(str, Enum):
    """Supported controller paradigms."""
    MAMDANI = "mamdani"
    SUGENO = "sugeno"


class CropType(str, Enum):
    """Standard crops for agricultural zones."""
    TOMATO = "Tomato"
    WHEAT = "Wheat"
    MAIZE = "Maize"
    POTATO = "Potato"
    COTTON = "Cotton"


class SoilType(str, Enum):
    """Standard soil classifications."""
    LOAM = "Loam"
    SANDY = "Sandy"
    CLAY = "Clay"
    SANDY_LOAM = "Sandy Loam"
    SILTY_CLAY = "Silty Clay"


class GrowthStage(str, Enum):
    """Phenological crop growth stages for Kc modulation."""
    INITIAL = "Initial"
    DEVELOPMENT = "Development"
    MID_SEASON = "Mid-season"
    LATE_SEASON = "Late-season"


class SimulationScenario(str, Enum):
    """Supported environmental simulation scenarios."""
    NORMAL = "Normal"
    HOT_AND_DRY = "Hot & Dry"
    RAINY = "Rainy"
    CLOUDY = "Cloudy"
    HEATWAVE = "Heatwave"
    WATER_SCARCITY = "Water Scarcity"


class CropParameters(BaseModel):
    """Agronomic parameters for crop evapotranspiration calculations."""
    name: str = Field(..., description="Crop identifier/name")
    growth_stage: GrowthStage = Field(default=GrowthStage.MID_SEASON, description="Current growth stage")
    kc: float = Field(..., gt=0.0, le=2.5, description="Crop coefficient (Kc) according to FAO-56")
    root_depth_m: float = Field(default=0.7, gt=0.0, le=3.0, description="Effective root zone depth in meters")


class SoilParameters(BaseModel):
    """Soil physical properties governing water balance and retention.

    Moisture values can be specified as percentage (0-100%) or volumetric fraction (0.0-1.0 m3/m3).
    """
    soil_type: SoilType = Field(..., description="Soil textural classification")
    field_capacity: float = Field(..., gt=0.0, le=100.0, description="Moisture content at field capacity (FC)")
    wilting_point: float = Field(..., ge=0.0, le=100.0, description="Moisture content at permanent wilting point (WP)")
    saturation: float = Field(default=85.0, gt=0.0, le=100.0, description="Saturation soil moisture capacity")
    infiltration_rate_mm_h: float = Field(default=15.0, gt=0.0, le=200.0, description="Maximum water infiltration rate (mm/h)")
    drainage_parameter: float = Field(default=0.08, ge=0.0, le=1.0, description="Drainage coefficient for moisture exceeding FC")

    @field_validator("wilting_point")
    @classmethod
    def validate_wp_lower_than_fc(cls, v: float, info) -> float:
        """Ensure wilting point is strictly less than field capacity."""
        if "field_capacity" in info.data and v >= info.data["field_capacity"]:
            raise ValueError(f"Wilting point ({v}) must be strictly less than field capacity ({info.data['field_capacity']})")
        return v


class ZoneConfig(BaseModel):
    """Specification for an individual managed agricultural zone."""
    zone_id: int = Field(..., ge=1, description="Unique zone identifier")
    name: str = Field(..., description="Descriptive zone label")
    crop: CropParameters = Field(..., description="Assigned crop agronomic parameters")
    soil: SoilParameters = Field(..., description="Assigned soil physical properties")
    area_m2: float = Field(..., gt=0.0, description="Cultivated land area in square meters")
    initial_moisture: float = Field(..., ge=0.0, le=100.0, description="Initial soil moisture content")
    target_moisture: float = Field(..., ge=0.0, le=100.0, description="Set-point target soil moisture content")
    priority: int = Field(default=1, ge=1, le=10, description="Water allocation priority weight (1=normal, 10=critical)")

    @model_validator(mode="after")
    def validate_target_between_wp_and_fc(self) -> "ZoneConfig":
        """Verify that target moisture lies between wilting point and field capacity."""
        wp = self.soil.wilting_point
        fc = self.soil.field_capacity
        if not (wp <= self.target_moisture <= fc):
            raise ValueError(
                f"Zone '{self.name}' target moisture ({self.target_moisture}) must be between "
                f"soil wilting point ({wp}) and field capacity ({fc})."
            )
        return self


class WeatherParameters(BaseModel):
    """Instantaneous environmental weather observations."""
    temperature_c: float = Field(..., ge=-20.0, le=65.0, description="Ambient air temperature in degrees Celsius")
    humidity_percent: float = Field(..., ge=0.0, le=100.0, description="Relative atmospheric humidity percentage")
    solar_radiation_wm2: float = Field(..., ge=0.0, le=1500.0, description="Global horizontal solar irradiance in W/m2")
    wind_speed_ms: float = Field(..., ge=0.0, le=50.0, description="Wind speed measured at 2m height in m/s")
    rainfall_mm: float = Field(default=0.0, ge=0.0, description="Precipitation accumulated during current step in mm")


class SimulationConfig(BaseModel):
    """Temporal configuration for simulation runs."""
    duration_hours: int = Field(default=24, ge=1, le=720, description="Total simulation duration in hours")
    timestep_minutes: int = Field(default=1, ge=1, le=60, description="Simulation discretization step size in minutes")

    @property
    def total_steps(self) -> int:
        """Calculate total discrete simulation epochs."""
        return (self.duration_hours * 60) // self.timestep_minutes


class ControllerConfig(BaseModel):
    """Fuzzy logic controller parameters."""
    type: ControllerType = Field(default=ControllerType.MAMDANI, description="Inference engine type")
    defuzzification: DefuzzificationMethod = Field(
        default=DefuzzificationMethod.CENTROID,
        description="Defuzzification method"
    )


class SystemConfig(BaseModel):
    """Master configuration encompassing simulation, controller, and zones."""
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    zones: int = Field(default=3, ge=1, description="Number of active zones")
    controller: ControllerConfig = Field(default_factory=ControllerConfig)
    zone_configs: Optional[List[ZoneConfig]] = Field(default=None, description="Detailed zone specifications")
