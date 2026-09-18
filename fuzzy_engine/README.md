# Fuzzy Engine Package (`fuzzy_engine/`)

This package forms the hierarchical fuzzy control foundation for the **Smart Multizone Irrigation and Water Resource Management** project.

## Architecture Overview

The system employs a hierarchical Mamdani fuzzy architecture consisting of 5 specialized Fuzzy Inference Systems (FIS) using 19 standard fuzzy variables:

1. **Soil Stress FIS**: Assesses root-zone agricultural moisture stress.
   - *Inputs*: Relative Soil Moisture (`rsm`), Moisture Error (`moisture_error`)
   - *Output*: Soil Stress (`soil_stress`)
2. **Weather Stress FIS**: Computes atmospheric evaporative demand stress.
   - *Inputs*: Temperature (`temperature`), Relative Humidity (`humidity`), Solar Radiation (`solar_radiation`), Wind Speed (`wind_speed`), Rainfall (`rainfall`)
   - *Output*: Weather Stress (`weather_stress`)
3. **Water Demand FIS**: Determines agronomic water requirement.
   - *Inputs*: Crop Evapotranspiration (`etc`), Crop Water Deficit (`crop_water_deficit`), Effective Rainfall (`effective_rainfall`)
   - *Output*: Water Demand (`water_demand`)
4. **Main Irrigation FIS**: Synthesizes stresses and demand into an irrigation command.
   - *Inputs*: Soil Stress (`soil_stress`), Weather Stress (`weather_stress`), Water Demand (`water_demand`), Moisture Error (`moisture_error`)
   - *Output*: Irrigation Command (`irrigation_command`)
5. **Water Allocation FIS**: Prioritizes and distributes constrained water volume across zones.
   - *Inputs*: Zone Demand (`zone_demand`), Zone Stress (`zone_stress`), Available Water (`available_water`), Zone Priority (`zone_priority`)
   - *Output*: Zone Allocation (`zone_allocation`)

## Package Modules

| Module | Description |
| :--- | :--- |
| `membership.py` | Vectorized pure NumPy and scalar evaluation of triangular ($\mu(x; a, b, c)$) and trapezoidal ($\mu(x; a, b, c, d)$) membership functions. |
| `variables.py` | Object-oriented classes: `FuzzyUniverse`, `MembershipSet`, and `FuzzyVariable`. Supports membership evaluation, physical clamping, normalization, and denormalization. |
| `mf_factory.py` | Declarative loaders and factory functions converting configuration schemas into validated fuzzy variables. |
| `universes.py` | Centralized repository `FUZZY_VARIABLES` containing all 19 pre-instantiated, validated fuzzy variables. |
| `validation.py` | Automated validation engine verifying universe limits, parameter non-decreasing order, grid resolution, partition of unity coverage, and boundary saturation. |
| `config/fuzzy_config.json` | Declarative single source of truth defining universes, linguistic terms, and MF parameters. |

## Quick Usage Example

```python
from fuzzy_engine import get_fuzzy_variable, FUZZY_VARIABLES

# Retrieve a fuzzy variable
rsm_var = get_fuzzy_variable("rsm")

# Evaluate membership degrees for an observed value (e.g. 42% available moisture)
degrees = rsm_var.evaluate(0.42)
# Output: {'very_dry': 0.0, 'dry': 0.4, 'adequate': 0.6, 'wet': 0.0, 'very_wet': 0.0}

# Normalize a physical reading
norm = rsm_var.normalize(0.42)  # 0.42
```
