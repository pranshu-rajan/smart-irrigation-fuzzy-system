"""Physical, environmental, and soil dynamics models for multizone irrigation.

Submodules:
- et0: Reference crop evapotranspiration based on the FAO-56 Penman-Monteith methodology.
- etc: Crop-specific evapotranspiration, effective rainfall, and water deficit models.
- soil: Soil moisture normalization (RSM), tracking error, TAW, RAW, conversions, and drainage models.
- water_balance: Dynamic discrete-time root-zone soil water balance engine.
"""

from .et0 import (
    calculate_et0_fao56,
    calculate_atmospheric_pressure,
    calculate_psychrometric_constant,
    calculate_saturation_vapor_pressure,
    calculate_actual_vapor_pressure,
    calculate_vpd,
    calculate_slope_vapor_pressure_curve,
    calculate_net_radiation,
    calculate_soil_heat_flux,
    compute_et0_timeseries,
)
from .etc import (
    calculate_etc,
    calculate_effective_rainfall,
    calculate_crop_water_deficit,
    calculate_water_deficit,
    CropCoefficientManager,
    compute_multizone_crop_demand,
)
from .soil import (
    calculate_relative_soil_moisture,
    calculate_rsm,
    calculate_moisture_error,
    calculate_taw,
    calculate_raw,
    soil_moisture_to_storage,
    storage_to_soil_moisture,
    calculate_infiltration,
    calculate_drainage,
    SoilParameterManager,
)
from .water_balance import (
    update_soil_moisture_step,
    update_water_balance,
    initialize_soil_state,
    simulate_water_balance_timeseries,
    SoilState,
)

__all__ = [
    # ET0
    "calculate_et0_fao56",
    "calculate_atmospheric_pressure",
    "calculate_psychrometric_constant",
    "calculate_saturation_vapor_pressure",
    "calculate_actual_vapor_pressure",
    "calculate_vpd",
    "calculate_slope_vapor_pressure_curve",
    "calculate_net_radiation",
    "calculate_soil_heat_flux",
    "compute_et0_timeseries",
    # ETc
    "calculate_etc",
    "calculate_effective_rainfall",
    "calculate_crop_water_deficit",
    "calculate_water_deficit",
    "CropCoefficientManager",
    "compute_multizone_crop_demand",
    # Soil
    "calculate_relative_soil_moisture",
    "calculate_rsm",
    "calculate_moisture_error",
    "calculate_taw",
    "calculate_raw",
    "soil_moisture_to_storage",
    "storage_to_soil_moisture",
    "calculate_infiltration",
    "calculate_drainage",
    "SoilParameterManager",
    # Water Balance
    "update_soil_moisture_step",
    "update_water_balance",
    "initialize_soil_state",
    "simulate_water_balance_timeseries",
    "SoilState",
]
