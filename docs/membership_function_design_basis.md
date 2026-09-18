# Fuzzy Membership Function Design Basis

> **Academic Context**: B.Tech 3rd-Year Electronics & Instrumentation Engineering / Fuzzy Systems.  
> **Core Principle**: Fuzzy membership functions must NOT be arbitrary statistical quantiles. They must be strictly grounded in **Empirical Data Distributions**, **Crop Biophysics**, and **Control Engineering Principles**.  
> **Phase 2 Status**: Preliminary Design Specification (Fuzzy membership functions are **not** implemented in code during this phase).

---

## 1. Design Methodology

The hierarchical fuzzy control architecture comprises five discrete Mamdani inference systems. Each input and output variable requires:
1. **Universe of Discourse ($U$)**: The crisp numerical domain spanning all possible operational and extreme conditions.
2. **Linguistic Variable Partitioning**: Semantically meaningful fuzzy subsets (e.g., Low, Medium, High) with triangular and trapezoidal geometries.
3. **Core Operating Band & Overlap**: 25% to 50% adjacent fuzzy set overlap to ensure smooth, non-oscillatory control surface transitions and defuzzification continuity.

---

## 2. Preliminary Fuzzy Design Specifications

| Subsystem | Variable Name | Unit | Observed Range (EDA) | Recommended Engineering Universe | Future Linguistic Terms | Design Basis & Engineering Justification |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **FIS 1: Soil Stress** | `soil_moisture` (or $RSM$) | $\%$ (or ratio) | $42.0\text{–}65.0\%$ ($RSM: 0.57\text{–}0.78$) | $[0.0, 100.0\%]$ or $[0.0, 1.0]$ | Very Dry, Dry, Moderate, Wet, Very Wet | Centered around Wilting Point ($RSM=0$), Depletion Threshold ($RSM=0.5$), and Field Capacity ($RSM=1.0$). |
| | `moisture_error` ($e(t)$) | $\%$ | $+0.0\text{–}+13.0\%$ (Initial) | $[-30.0, +30.0\%]$ | Very Negative, Negative, Zero, Positive, Very Positive | $e(t) = SM_{\text{target}} - SM(t)$. Negative indicates over-saturation/hypoxia; positive indicates moisture deficit requiring irrigation. |
| | `soil_stress` | index | — | $[0.0, 1.0]$ | Very Low, Low, Moderate, High, Extreme | Dimensionless output index feeding into Main Irrigation FIS (FIS 4). High values reflect root water stress. |
| **FIS 2: Weather Stress** | `temperature` | °C | $18.0\text{–}34.2^\circ\text{C}$ | $[10.0, 50.0^\circ\text{C}]$ | Low, Moderate, High, Very High | Low ($<20^\circ\text{C}$), Moderate ($20\text{–}28^\circ\text{C}$ optimal photosynthetically), High ($28\text{–}36^\circ\text{C}$ elevated VPD), Very High ($>36^\circ\text{C}$ acute heat stress). |
| | `humidity` | % | $42.5\text{–}87.5\%$ | $[0.0, 100.0\%]$ | Very Low, Low, Moderate, High, Very High | Very Low ($<30\%$) causes stomatal closure; High ($>80\%$) suppresses evaporative transpirational pull. |
| | `solar_radiation` | $W/m^2$ | $0.0\text{–}915.2\text{ W/m}^2$ | $[0.0, 1200.0\text{ W/m}^2]$ | Very Low, Low, Moderate, High, Very High | Corresponds directly to daytime solar flux driving Penman-Monteith net radiation $R_n$. Peak noon $>800\text{ W/m}^2$. |
| | `wind_speed` | $m/s$ | $1.4\text{–}3.6\text{ m/s}$ | $[0.0, 15.0\text{ m/s}]$ | Low, Moderate, High, Very High | Low ($<2\text{ m/s}$), Moderate ($2\text{–}4\text{ m/s}$), High ($4\text{–}7\text{ m/s}$ advective boundary layer stripping), Very High ($>7\text{ m/s}$). |
| | `rainfall` | $mm$ | $0.0\text{ mm}$ (baseline day) | $[0.0, 50.0\text{ mm/step}]$ | None, Light, Moderate, Heavy | None ($0\text{ mm}$), Light ($0.1\text{–}2.0\text{ mm}$), Moderate ($2.0\text{–}10.0\text{ mm}$), Heavy ($>10.0\text{ mm}$). |
| | `weather_stress` | index | — | $[0.0, 1.0]$ | Low, Moderate, High, Extreme | Synthesized atmospheric evaporative demand driving irrigation urgency. |
| **FIS 3: Water Demand** | `etc` | $mm/\text{day}$ | *Not calculated in Phase 2* | $[0.0, 15.0\text{ mm/day}]$ | Very Low, Low, Moderate, High, Very High | *To be established after Phase 4 ET0/ETc implementation.* |
| | `water_deficit` | $\%$ or $mm$ | *Not calculated in Phase 2* | $[0.0, 40.0\%]$ | None, Low, Moderate, High, Extreme | *To be established after Phase 4 ET0/ETc implementation.* |
| | `effective_rainfall` | $mm$ | *Not calculated in Phase 2* | $[0.0, 30.0\text{ mm}]$ | None, Low, Moderate, High | *To be established after Phase 4 ET0/ETc implementation.* |
| | `water_demand` | index | — | $[0.0, 1.0]$ | None, Low, Moderate, High, Very High | Unconstrained volumetric demand score before allocation. |
| **FIS 4: Main Irrigation**| `soil_stress` | index | — | $[0.0, 1.0]$ | Very Low, Low, Moderate, High, Extreme | Transferred directly from FIS 1 output. |
| | `weather_stress` | index | — | $[0.0, 1.0]$ | Low, Moderate, High, Extreme | Transferred directly from FIS 2 output. |
| | `water_demand` | index | — | $[0.0, 1.0]$ | None, Low, Moderate, High, Very High | Transferred directly from FIS 3 output. |
| | `moisture_error` | $\%$ | $+0.0\text{–}+13.0\%$ | $[-30.0, +30.0\%]$ | Very Negative, Negative, Zero, Positive, Very Positive | Direct closed-loop error signal tracking deviation from setpoint. |
| | `irrigation_command`| index | — | $[0.0, 100.0]$ | OFF, Very Low, Low, Medium, High, Very High | Normalized control signal $[0, 100]$ translated to valve open time or flow volume. |
| **FIS 5: Allocation** | `zone_demand` | index | — | $[0.0, 100.0]$ | Very Low, Low, Moderate, High, Very High | Transferred from FIS 4 output for each zone. |
| | `zone_stress` | index | — | $[0.0, 1.0]$ | Low, Moderate, High, Extreme | Physiological urgency of the crop root system. |
| | `available_water` | $\%$ or $m^3$ | — | $[0.0, 100.0\%]$ | Critically Low, Low, Moderate, Abundant | Reservoir storage capacity status. Under drought, triggers triage. |
| | `zone_priority` | rank | $1, 2, 3$ | $[1.0, 10.0]$ | Low, Standard, High, Critical | Economic and crop value weighting (Tomato=2, Wheat=1, Maize=3). |
| | `zone_allocation` | fraction | — | $[0.0, 1.0]$ | None, Restricted, Proportional, Priority Full | Allocation fraction respecting reservoir budget $\sum V_i \le V_{\text{available}}$. |

---

## 3. Engineering Justification for Linguistic Membership Boundaries

### 3.1 Temperature Partitioning (Weather Stress FIS)
- **Low ($\le 18^\circ\text{C}$)**: Transpiration rate is minimal due to reduced vapor pressure deficit. Even with dry soil, water uptake is sluggish.
- **Moderate ($18^\circ\text{C} - 26^\circ\text{C}$)**: Optimal stomatal conductance for $C_3$ (Wheat, Tomato) and $C_4$ (Maize) crops. Evaporative demand is predictable and moderate.
- **High ($26^\circ\text{C} - 34^\circ\text{C}$)**: Transpiration escalates sharply. Crop enters defensive cooling mode.
- **Very High ($> 34^\circ\text{C}$)**: Stomatal resistance increases to prevent xylem cavitation; acute heat stress occurs. Evaporation from soil surface peaks.

### 3.2 Humidity Partitioning (Weather Stress FIS)
- **Very Low ($< 30\%$)**: Large saturation vapor pressure deficit ($e_s - e_a$). Very high atmospheric drying power.
- **Moderate ($50\% - 70\%$)**: Balanced boundary layer vapor exchange.
- **Very High ($> 85\%$)**: Vapor pressure deficit approaches zero. Evapotranspiration is severely restricted, reducing irrigation urgency.

### 3.3 Relative Soil Moisture ($RSM$) Partitioning (Soil Stress FIS)
Using $RSM = \frac{SM - WP}{FC - WP}$:
- **Very Dry ($RSM < 0.20$)**: Soil water potential drops below $-1500\text{ kPa}$. Severe plant turgor loss and permanent wilting risk. Stress is **Extreme**.
- **Dry ($0.20 \le RSM < 0.45$)**: Available water drops below Management Allowed Depletion ($MAD = p \approx 0.40 - 0.55$). Stomatal closure begins.
- **Moderate ($0.45 \le RSM < 0.80$)**: Optimal agronomic comfort zone. Soil aeration and capillary water availability are balanced.
- **Wet ($0.80 \le RSM \le 1.00$)**: Approaching field capacity. Ample water, low root stress.
- **Very Wet ($RSM > 1.00$)**: Soil moisture exceeds field capacity, entering gravitational drainage and macropore waterlogging. Poses hypoxia risk in fine-textured soils (Clay).
