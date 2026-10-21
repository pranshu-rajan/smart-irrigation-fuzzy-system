"""Pydantic schemas for India National-Level Precision Irrigation."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class IndiaDistrictInfo(BaseModel):
    """District profile with geographic and agro-climatic metadata."""
    district: str
    state: str
    latitude: float
    longitude: float
    elevation_m: float
    agro_climatic_zone: str
    zone_number: int
    dominant_soil: str
    field_capacity_pct: float
    wilting_point_pct: float
    saturation_pct: float
    primary_kharif_crop: str
    primary_rabi_crop: str
    primary_zaid_crop: str


class IndiaLocationLookupResponse(BaseModel):
    """Response returned when looking up an Indian location."""
    query: str
    matched_district: str
    state: str
    latitude: float
    longitude: float
    elevation_m: float
    agro_climatic_zone: str
    zone_number: int
    dominant_soil: str
    soil_properties: Dict[str, float]
    recommended_crops: Dict[str, str]
    all_districts_count: int


class IndiaLiveWeather(BaseModel):
    """Real-time meteorological readings for an Indian site."""
    temperature_c: float
    humidity_percent: float
    solar_radiation_w_m2: float
    wind_speed_m_s: float
    rainfall_mm: float
    atmospheric_pressure_kpa: float
    source: str
    timestamp: str
    is_live: bool


class IndiaZoneAllocation(BaseModel):
    """Zone-specific allocation result under local Indian crop conditions."""
    zone_id: int
    name: str
    crop: str
    season: str
    kc: float
    soil_type: str
    area_m2: float
    target_moisture_pct: float
    current_moisture_pct: float
    soil_stress_pct: float
    water_demand_pct: float
    main_command_pct: float
    requested_liters: float
    allocated_liters: float
    fulfillment_ratio_pct: float
    status: str


class IndiaSimulationTimestep(BaseModel):
    """Hourly simulation point for 24-hour predictive trajectory."""
    hour: int
    time_label: str
    temperature_c: float
    solar_radiation_w_m2: float
    rainfall_mm: float
    et0_mm: float
    zone1_moisture: float
    zone2_moisture: float
    zone3_moisture: float
    irrigation_liters: float


class IndiaEvaluationRequest(BaseModel):
    """Request payload to evaluate end-to-end fuzzy architecture for an Indian location."""
    location_query: Optional[str] = Field(None, description="City, district, or state name (e.g., 'Ludhiana', 'Pune', 'Varanasi')")
    pincode: Optional[str] = Field(None, description="6-digit Indian postal code (e.g., '141004', '411001')")
    latitude: Optional[float] = Field(None, description="Latitude (°N)")
    longitude: Optional[float] = Field(None, description="Longitude (°E)")
    elevation_m: Optional[float] = Field(None, description="Optional elevation in meters")
    soil_moisture_override: Optional[float] = Field(None, description="Override initial soil moisture (%)")
    target_moisture_override: Optional[float] = Field(None, description="Override target setpoint (%)")
    reservoir_storage_pct: Optional[float] = Field(65.0, description="Available farm pond / reservoir capacity (%)")
    temperature_override: Optional[float] = Field(None, description="Override atmospheric temperature (°C)")
    humidity_override: Optional[float] = Field(None, description="Override relative humidity (%)")
    solar_radiation_override: Optional[float] = Field(None, description="Override solar irradiance (W/m²)")
    rainfall_override: Optional[float] = Field(None, description="Override rainfall (mm)")
    zone1_crop_override: Optional[str] = Field(None, description="Override primary Zone 1 crop")
    zone2_crop_override: Optional[str] = Field(None, description="Override Zone 2 crop")
    zone3_crop_override: Optional[str] = Field(None, description="Override Zone 3 crop")


class IndiaEvaluationResponse(BaseModel):
    """Comprehensive response containing live weather, agronomics, and 5-stage FIS decisions."""
    location: IndiaDistrictInfo
    weather: IndiaLiveWeather
    physics_agronomy: Dict[str, Any]
    fuzzy_stages: Dict[str, Any]
    zone_allocations: List[IndiaZoneAllocation]
    total_requested_liters: float
    total_allocated_liters: float
    available_supply_liters: float
    is_supply_constrained: bool = Field(..., alias="is_supply_constrained")
    hourly_telemetry: List[IndiaSimulationTimestep]
    decision_summary: str
    water_savings_vs_onoff_pct: float
    water_savings_vs_pid_pct: float

    class Config:
        populate_by_name = True


class IndiaAgrometAdvisoryRequest(BaseModel):
    """Request for live ICAR/IMD Agromet Advisory synthesized by GPT-OSS-120B with Tavily."""
    district: str
    state: str
    crop: Optional[str] = "Wheat"
    soil_type: Optional[str] = "Alluvial Loam"
    irrigation_depth_mm: Optional[float] = 0.0
    et0_mm_day: Optional[float] = 4.5
    current_temp_c: Optional[float] = 28.0
    current_humidity_pct: Optional[float] = 50.0


class IndiaAgrometAdvisoryResponse(BaseModel):
    """Response containing live ICAR advisory, GPT-OSS-120B analysis, reasoning, and citations."""
    district: str
    state: str
    crop: str
    advisory_summary: str
    critical_farming_tips: List[str]
    model_name: str = "openai/gpt-oss-120b"
    reasoning: Optional[str] = None
    web_sources: List[Dict[str, str]] = []

