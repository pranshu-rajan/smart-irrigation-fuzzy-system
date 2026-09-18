# Data Dictionary — Smart Multizone Irrigation System

> **Classification Taxonomy**:
> - **MEASURED / OBSERVED**: Physical telemetry captured by real/reference weather stations and environmental sensors.
> - **DERIVED**: Analytically computed from physical equations (e.g., FAO-56 Penman-Monteith, Relative Soil Moisture).
> - **MODEL ASSUMPTION**: Baseline agronomic/pedological parameters configured by user or reference standard.
> - **SIMULATION-GENERATED**: State variables produced iteratively by closed-loop numerical simulation.

---

## 1. Crop Agronomic Database (`data/crop_database.csv`)

| Column Name | Semantic Meaning | Unit | Data Type | Valid Range | Taxonomy Classification | Source / Reference |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `crop` | Cultivated crop common name | — | String | Valid plant taxon | MODEL ASSUMPTION | FAO-56 Table 12 |
| `growth_stage` | Phenological stage of crop development | — | String | Initial, Development, Mid-season, Late-season | MODEL ASSUMPTION | FAO-56 Irrigation and Drainage Paper 56 |
| `kc_initial` | Crop coefficient during initial growth stage | dimensionless | Float | $0.1 \le K_c \le 1.5$ | MODEL ASSUMPTION | FAO-56 Table 12 |
| `kc_mid` | Crop coefficient during peak mid-season stage | dimensionless | Float | $0.5 \le K_c \le 2.0$ | MODEL ASSUMPTION | FAO-56 Table 12 |
| `kc_end` | Crop coefficient during late harvest stage | dimensionless | Float | $0.1 \le K_c \le 1.5$ | MODEL ASSUMPTION | FAO-56 Table 12 |
| `root_depth_min_m` | Minimum effective root depth at emergence | meters ($m$) | Float | $0.1 \le z_r \le 1.5$ | MODEL ASSUMPTION | FAO-56 Table 22 |
| `root_depth_max_m` | Maximum effective root depth at full maturity | meters ($m$) | Float | $0.3 \le z_r \le 3.0$ | MODEL ASSUMPTION | FAO-56 Table 22 |
| `depletion_fraction_p` | Soil water depletion fraction for no stress | dimensionless | Float | $0.1 \le p \le 0.8$ | MODEL ASSUMPTION | FAO-56 Table 22 |
| `source` | Agronomic literature or database citation | — | String | Text | METADATA | FAO Guidelines |
| `notes` | Crop-specific sensitivity and ecological notes | — | String | Text | METADATA | Agronomic observations |

---

## 2. Soil Hydraulic Database (`data/soil_database.csv`)

| Column Name | Semantic Meaning | Unit | Data Type | Valid Range | Taxonomy Classification | Source / Reference |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `soil_type` | USDA soil textural class name | — | String | Loam, Sandy, Clay, etc. | MODEL ASSUMPTION | USDA-NRCS Soil Classification |
| `field_capacity_pct` | Soil water content retained after free gravity drainage | percent (%) | Float | $10\% \le FC \le 80\%$ | MODEL ASSUMPTION | FAO Soils Bulletin / USDA |
| `wilting_point_pct` | Soil water content where vegetation permanently wilts | percent (%) | Float | $5\% \le WP < FC$ | MODEL ASSUMPTION | FAO Soils Bulletin / USDA |
| `available_water_pct` | Total plant-available water ($AWC = FC - WP$) | percent (%) | Float | $5\% \le AWC \le 40\%$ | DERIVED | $FC - WP$ |
| `saturation_pct` | Total pore volume filled with water | percent (%) | Float | $FC < \text{Sat} \le 100\%$ | MODEL ASSUMPTION | Soil Porosity tables |
| `infiltration_rate_mm_h`| Maximum intake velocity of water through soil surface | $mm/h$ | Float | $1.0 \le f \le 100.0$ | MODEL ASSUMPTION | Horton/USDA Infiltration curves |
| `drainage_parameter` | Fractional drainage rate of moisture exceeding FC | $1/\text{day}$ | Float | $0.01 \le k_d \le 0.5$ | MODEL ASSUMPTION | Darcy-Buckingham unsaturated flow |
| `source` | Pedological authority citation | — | String | Text | METADATA | USDA-NRCS / FAO |
| `notes` | Soil physical behavior and hydraulic notes | — | String | Text | METADATA | Soil physics reference |

---

## 3. Clean Weather Dataset (`data/processed/weather_clean.csv`)

| Column Name | Semantic Meaning | Unit | Data Type | Valid Range | Taxonomy Classification | Source / Reference |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `timestamp` | UTC or local observation timestamp | ISO 8601 | Datetime | Chronologically ordered | MEASURED / OBSERVED | Weather station telemetry |
| `temperature` | Dry-bulb ambient air temperature at 2m height | degrees Celsius (°C) | Float | $-20.0 \le T \le 60.0$ | MEASURED / OBSERVED | NASA POWER / NOAA ISD |
| `humidity` | Relative humidity of air at 2m height | percent (%) | Float | $0.0 \le RH \le 100.0$ | MEASURED / OBSERVED | NASA POWER / NOAA ISD |
| `solar_radiation` | Global horizontal downward shortwave solar irradiance | Watts per sq meter ($W/m^2$) | Float | $0.0 \le R_s \le 1500.0$ | MEASURED / OBSERVED | Pyranometer / Satellite |
| `wind_speed` | Mean horizontal wind speed measured at 2m height | meters per second ($m/s$) | Float | $0.0 \le u_2 \le 50.0$ | MEASURED / OBSERVED | Anemometer |
| `rainfall` | Liquid precipitation depth during timestep | millimeters ($mm$) | Float | $0.0 \le P \le 300.0$ | MEASURED / OBSERVED | Tipping bucket rain gauge |

---

## 4. Unified Multizone Dataset (`data/processed/irrigation_dataset.csv`)

| Column Name | Semantic Meaning | Unit | Data Type | Valid Range | Taxonomy Classification | Downstream Implementation |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `timestamp` | Time of observation/step | ISO 8601 | Datetime | 24-hr sequence | MEASURED / OBSERVED | Synchronizer |
| `zone_id` | Identifier of agricultural management zone | integer | Integer | $1, 2, 3, \dots$ | MODEL ASSUMPTION | Zone controller routing |
| `crop` | Assigned crop species in zone | — | String | Tomato, Wheat, Maize | MODEL ASSUMPTION | Config |
| `growth_stage` | Crop phenological phase | — | String | Initial, Mid, Late | MODEL ASSUMPTION | Kc selection |
| `soil_type` | Soil textural category in zone | — | String | Loam, Sandy, Clay | MODEL ASSUMPTION | Soil model |
| `temperature` | Ambient temperature | °C | Float | $-20 \le T \le 60$ | MEASURED / OBSERVED | Weather Stress FIS & ET0 |
| `humidity` | Atmospheric relative humidity | % | Float | $0 \le RH \le 100$ | MEASURED / OBSERVED | Weather Stress FIS & ET0 |
| `solar_radiation` | Solar irradiance | $W/m^2$ | Float | $0 \le R_s \le 1500$ | MEASURED / OBSERVED | Weather Stress FIS & ET0 |
| `wind_speed` | Wind speed at 2m | $m/s$ | Float | $0 \le u_2 \le 50$ | MEASURED / OBSERVED | Weather Stress FIS & ET0 |
| `rainfall` | Precipitation accumulation | $mm$ | Float | $P \ge 0$ | MEASURED / OBSERVED | Water Balance & Demand FIS |
| `soil_moisture` | Volumetric soil moisture content | % (or $m^3/m^3$) | Float | $WP \le SM \le \text{Sat}$ | SIMULATION-GENERATED | Soil Stress FIS & Error |
| `field_capacity` | Upper retention limit before drainage | % | Float | $WP < FC \le 100$ | MODEL ASSUMPTION | RSM normalization |
| `wilting_point` | Permanent wilting threshold | % | Float | $0 \le WP < FC$ | MODEL ASSUMPTION | RSM normalization |
| `target_moisture` | Optimal agronomic moisture setpoint | % | Float | $WP \le SM_{\text{target}} \le FC$ | MODEL ASSUMPTION | Error calculation |
| `kc` | Instantaneous crop coefficient | dimensionless | Float | $0.1 \le K_c \le 2.0$ | MODEL ASSUMPTION | Crop ETc |
| `et0` | Reference crop evapotranspiration | $mm/\text{day}$ | Float | $\ge 0.0$ | DERIVED | **Phase 4 (FAO-56 PM)** |
| `etc` | Crop evapotranspiration ($K_c \times ET_0$) | $mm/\text{day}$ | Float | $\ge 0.0$ | DERIVED | **Phase 4** |
| `effective_rainfall` | Precipitation infiltrating root zone | $mm$ | Float | $0 \le P_{\text{eff}} \le P$ | DERIVED | **Phase 4 / 5** |
| `moisture_error` | Tracking error $SM_{\text{target}} - SM(t)$ | % | Float | Unbounded | DERIVED | **Phase 5** |
| `water_deficit` | Moisture depletion below target | % | Float | $\ge 0.0$ | DERIVED | **Phase 4 / 5** |
| `available_water` | Remaining reservoir water storage | $m^3$ or % | Float | $\ge 0.0$ | SIMULATION-GENERATED | **Phase 13 (Allocation FIS)** |

---

## 5. Distinction: Data vs. Fuzzy Sets

The system maintains a rigorous separation between crisp data variables and fuzzy linguistic evaluation:

```
+-------------------------------------------------------------------------------+
| CRISP NUMERICAL DATASET (Phase 1)                                             |
|   Temperature       = 34.2 °C                                                 |
|   Humidity          = 42.5 %                                                  |
|   Solar Radiation   = 880.6 W/m²                                              |
|   Soil Moisture     = 55.0 %                                                  |
+-------------------------------------------------------------------------------+
                                      |
                                      v (Fuzzification in Phase 6-10)
+-------------------------------------------------------------------------------+
| FUZZY LINGUISTIC MEMBERSHIP EVALUATION (Future Phases)                         |
|   Temperature is HIGH        [degree = 0.85]                                  |
|   Humidity is LOW            [degree = 0.60]                                  |
|   Solar Radiation is HIGH    [degree = 0.90]                                  |
|   Soil Moisture is MODERATE  [degree = 0.75]                                  |
+-------------------------------------------------------------------------------+
```
