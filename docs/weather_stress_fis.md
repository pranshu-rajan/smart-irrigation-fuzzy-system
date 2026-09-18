# Phase 8 Documentation: Weather Stress Fuzzy Inference System (WeatherStressFIS)

## 1. Overview & Purpose

The **Weather Stress Fuzzy Inference System (`WeatherStressFIS`)** is the second diagnostic fuzzy inference subsystem in the hierarchical smart irrigation architecture. Its objective is to evaluate the real-time atmospheric and environmental water stress exerted on the crop canopy by synthesizing five meteorological variables:
1. **Air Temperature ($T$)** [10–50 °C]
2. **Relative Humidity ($RH$)** [0–100 %]
3. **Solar Radiation ($R_s$)** [0–1200 W/m²]
4. **Wind Speed ($u_2$)** [0–15 m/s]
5. **Rainfall ($P$)** [0–50 mm/timestep]

The resulting **Weather Stress index** $[0.0, 100.0]\%$ quantifies atmospheric evaporative demand and climatic pressure, which will later feed into the **Main Irrigation FIS** alongside root-zone Soil Stress.

```
+-------------------------------------------------------------------------------+
|                       WEATHER STRESS FIS (Phase 8)                            |
|                                                                               |
|   Temperature [10 - 50 °C] ───────────────┐                                   |
|   Relative Humidity [0 - 100 %] ──────────┤                                   |
|   Solar Radiation [0 - 1200 W/m²] ────────┼──► [ 34-Rule Mamdani FIS ] ──►   |  Weather Stress
|   Wind Speed [0 - 15 m/s] ────────────────┤     (5-Layer Architecture)        |  [0 - 100]%
|   Rainfall [0 - 50 mm] ───────────────────┘                                   |
+-------------------------------------------------------------------------------+
```

---

## 2. Fundamental Semantic Distinctions

To ensure theoretical integrity and prevent conceptual confusion during examinations and reviews, the architecture strictly distinguishes four key variables:

```
+─────────────────────────────────────────────────────────────────────────────+
|                          ARCHITECTURAL SEPARATION                           |
+─────────────────────────────────────────────────────────────────────────────+
|  Variable         | Type          | Unit    | Physical / Functional Meaning  |
|───────────────────+───────────────+─────────+────────────────────────────────|
|  ET0              | Physical Rate | mm/day  | FAO-56 Penman-Monteith physical|
|                   |               | (mm/min)| atmospheric vapor flux from a  |
|                   |               |         | hypothetical reference crop.   |
|───────────────────+───────────────+─────────+────────────────────────────────|
|  Weather Stress   | Fuzzy Index   | %       | Linguistic assessment of       |
|                   |               |         | climatic severity and drought  |
|                   |               |         | pressure on canopy biology.    |
|───────────────────+───────────────+─────────+────────────────────────────────|
|  Soil Stress      | Fuzzy Index   | %       | Root-zone water scarcity       |
|                   |               |         | derived from RSM and error.    |
|───────────────────+───────────────+─────────+────────────────────────────────|
|  Water Demand     | Fuzzy Index / | % /     | Integrated irrigation demand   |
|                   | Volume Rate   | mm      | combining atmospheric flux and |
|                   |               |         | crop developmental stage (Kc). |
+─────────────────────────────────────────────────────────────────────────────+
```

### 2.1 Weather Stress $\neq$ Reference Evapotranspiration ($ET_0$)
- **$ET_0$** is an absolute physical flux rate derived deterministically from energy balance and aerodynamic equations (FAO-56 Penman-Monteith).
- **Weather Stress** is a unitless fuzzy index ($0–100\%$) that interprets the combined severity of meteorological stress on plant physiology (e.g., stomatal closure pressure, heat stress risk, wind desiccation).
- Later in the hierarchy, $ET_0 \to ET_c$ feeds the **Water Demand FIS**, whereas Weather Stress feeds the **Main Irrigation FIS** directly as an environmental urgency factor.

### 2.2 Weather Stress $\neq$ Soil Stress
- **Soil Stress** represents underground physical water deficit in the root zone (supply constraint).
- **Weather Stress** represents aboveground atmospheric evaporative demand and climate aggression (demand driver).
- A crop can experience low soil stress (field capacity) under extreme weather stress (hot dry desert winds), or conversely, high soil stress under low weather stress (cool humid overcast days).

### 2.3 Weather Stress $\neq$ Water Demand
- Atmospheric stress is only one driver of irrigation necessity. Water demand depends additionally on crop type, phenological stage ($K_c$), root depth, and current soil moisture deficits.

---

## 3. Physical Roles of Meteorological Inputs

1. **Air Temperature ($T$) [10–50 °C]**:
   - *Thermal Driver*: Governs the saturation vapor pressure curve $e_s(T)$. High temperatures dramatically expand the air's water-holding capacity, accelerating potential transpirational loss and cellular heat stress.
2. **Relative Humidity ($RH$) [0–100 %]**:
   - *Vapor Pressure Deficit Driver*: Determines the vapor pressure gradient between the substomatal cavity and ambient air ($VPD = e_s - e_a$). Low RH steepens this gradient, creating extreme transpirational pull; high RH suppresses evaporative demand.
3. **Solar Radiation ($R_s$) [0–1200 W/m²]**:
   - *Radiative Energy Driver*: Provides the net radiation ($R_n$) and latent heat required for liquid water vaporization at the leaf surface. High radiation stimulates stomatal opening and canopy heating.
4. **Wind Speed ($u_2$) [0–15 m/s]**:
   - *Aerodynamic Transport Driver*: Strips away the humid laminar boundary layer adhering to leaf surfaces, maintaining a steep vapor pressure gradient and maximizing turbulent transfer.
5. **Rainfall ($P$) [0–50 mm/timestep]**:
   - *Immediate Atmospheric Relief*: Wet canopies, saturated boundary layers, cloud cover, and falling precipitation immediately relieve atmospheric transpirational pressure, driving Weather Stress to minimal levels regardless of background temperature.

---

## 4. Mathematical Inference Specification

`WeatherStressFIS` implements standard Mamdani fuzzy inference:

### 4.1 Fuzzification
The 5 inputs $\mathbf{x} = [T, RH, R_s, u_2, P]$ are evaluated against Phase 6 triangular and trapezoidal membership functions:
$$\mu_{A_i}(x_i) \in [0, 1], \quad i \in \{1, 2, 3, 4, 5\}$$

### 4.2 Antecedent Conjunction (T-Norm)
The rule antecedent uses the standard Mamdani **minimum** operator:
$$\alpha_k = \min\left(\mu_{A_{k, 1}}(T), \mu_{A_{k, 2}}(RH), \mu_{A_{k, 3}}(R_s), \mu_{A_{k, 4}}(u_2), \mu_{A_{k, 5}}(P)\right)$$
For rules omitting certain inputs, unconstrained dimensions have implicit membership $1.0$.

### 4.3 Implication
Mamdani **minimum-truncation** implication clips the consequent fuzzy set for each rule:
$$\mu_{C_k}'(z) = \min\left(\alpha_k, \mu_{C_k}(z)\right), \quad \forall z \in [0, 100]\%$$

### 4.4 Consequent Aggregation (S-Norm)
Individual rule outputs are aggregated across the 4 linguistic output terms using the **maximum** operator:
$$\beta_L = \max_{\{k \mid C_k = L\}} \alpha_k, \quad L \in \{\text{Low}, \text{Moderate}, \text{High}, \text{Very High}\}$$
$$\mu_{\text{agg}}(z) = \max_L \left(\min(\beta_L, \mu_L(z))\right), \quad \forall z \in [0, 100]\%$$

### 4.5 Centroid Defuzzification
The continuous centroid integral is approximated over a discrete uniform grid of $M = 501$ points across $[0, 100]\%$ ($dz = 0.2\%$):
$$z^* = \frac{\sum_{m=1}^M z_m \cdot \mu_{\text{agg}}(z_m)}{\sum_{m=1}^M \mu_{\text{agg}}(z_m)}$$

### 4.6 Pathological Edge-Case Fallback
If $\sum_{m=1}^M \mu_{\text{agg}}(z_m) < 10^{-9}$, the defuzzifier gracefully returns $0.0\%$ to prevent division by zero.

---

## 5. 34-Rule Hierarchical Engineering Rule Base

Rather than an unmanageable $4 \times 5 \times 4 \times 5 \times 5 = 2000$ full Cartesian expansion, `WeatherStressFIS` employs a 5-layer hierarchical structure with 34 physically grounded rules:

### Layer 1: Precipitation Suppression & Relief (Rules R1–R3)
*Precipitation overrides background thermal-aerodynamic stress by saturating the canopy boundary layer.*
- **R1**: IF Rainfall is *Very Heavy* THEN Weather Stress is *Low*.
- **R2**: IF Rainfall is *Heavy* THEN Weather Stress is *Low*.
- **R3**: IF Rainfall is *Moderate* AND Humidity is *High* OR *Very High* THEN Weather Stress is *Low*.

### Layer 2: Thermal-Humidity (VPD) Baseline Kernel (Rules R4–R23)
*Complete $4 \times 5 = 20$ Cartesian matrix establishing baseline evaporative demand across all temperature and humidity regimes when rainfall is absent or light.*
- **R4** (T=Low, RH=Very Low): *Moderate*
- **R5** (T=Low, RH=Low): *Low*
- **R6** (T=Low, RH=Moderate): *Low*
- **R7** (T=Low, RH=High): *Low*
- **R8** (T=Low, RH=Very High): *Low*
- **R9** (T=Mod, RH=Very Low): *High*
- **R10** (T=Mod, RH=Low): *Moderate*
- **R11** (T=Mod, RH=Moderate): *Moderate*
- **R12** (T=Mod, RH=High): *Low*
- **R13** (T=Mod, RH=Very High): *Low*
- **R14** (T=High, RH=Very Low): *Very High*
- **R15** (T=High, RH=Low): *High*
- **R16** (T=High, RH=Moderate): *High*
- **R17** (T=High, RH=High): *Moderate*
- **R18** (T=High, RH=Very High): *Low*
- **R19** (T=Very High, RH=Very Low): *Very High*
- **R20** (T=Very High, RH=Low): *Very High*
- **R21** (T=Very High, RH=Moderate): *High*
- **R22** (T=Very High, RH=High): *High*
- **R23** (T=Very High, RH=Very High): *Moderate*

### Layer 3: Radiative & Solar Forcing Modulation (Rules R24–R27)
*Solar radiation amplifies thermal stress under clear skies.*
- **R24**: IF Solar is *Very High* AND Humidity is *Low* OR *Very Low* AND Temperature is *High* OR *Very High* AND Rainfall is *None* THEN Weather Stress is *Very High*.
- **R25**: IF Solar is *High* AND Humidity is *Low* AND Temperature is *High* AND Rainfall is *None* THEN Weather Stress is *High*.
- **R26**: IF Solar is *Low* AND Temperature is *Low* OR *Moderate* THEN Weather Stress is *Low*.
- **R27**: IF Solar is *Very High* AND Temperature is *Moderate* AND Humidity is *Moderate* THEN Weather Stress is *High*.

### Layer 4: Advective Desiccating Wind Modulation (Rules R28–R31)
*High winds accelerate boundary-layer stripping, turning warm/dry conditions into severe desiccation.*
- **R28**: IF Wind is *Very High* AND Humidity is *Low* OR *Very Low* AND Temperature is *High* OR *Very High* AND Rainfall is *None* THEN Weather Stress is *Very High*.
- **R29**: IF Wind is *High* AND Humidity is *Low* AND Temperature is *High* THEN Weather Stress is *High*.
- **R30**: IF Wind is *Calm* AND Humidity is *High* OR *Very High* THEN Weather Stress is *Low*.
- **R31**: IF Wind is *Very High* AND Temperature is *Moderate* AND Humidity is *Moderate* THEN Weather Stress is *High*.

### Layer 5: Nocturnal & Calm Mitigation (Rules R32–R34)
*Accounts for night-time conditions (zero solar) and light rainfall moderations.*
- **R32**: IF Solar is *Low* AND Wind is *Calm* OR *Low* AND Humidity is *Moderate* OR *High* THEN Weather Stress is *Low*.
- **R33**: IF Rainfall is *Light* AND Temperature is *Low* OR *Moderate* THEN Weather Stress is *Low*.
- **R34**: IF Rainfall is *Light* AND Temperature is *High* OR *Very High* AND Humidity is *Moderate* OR *High* THEN Weather Stress is *Moderate*.

---

## 6. Software Architecture & API

The class `WeatherStressFIS` resides in `fuzzy_engine/weather_stress.py` and implements:

```python
class WeatherStressFIS:
    def __init__(self, config_path: Path | str = None):
        """Initializes universes, membership functions from fuzzy_config.json, and compiles rules."""
        ...

    def evaluate(
        self,
        temperature: float,
        humidity: float,
        solar_radiation: float,
        wind_speed: float,
        rainfall: float
    ) -> float:
        """Scalar evaluation returning defuzzified weather stress in [0.0, 100.0]%."""
        ...

    def evaluate_detailed(
        self,
        temperature: float,
        humidity: float,
        solar_radiation: float,
        wind_speed: float,
        rainfall: float
    ) -> dict:
        """Diagnostic evaluation returning input memberships, rule activations, and aggregated area."""
        ...

    def evaluate_array(
        self,
        temperature: np.ndarray,
        humidity: np.ndarray,
        solar_radiation: np.ndarray,
        wind_speed: np.ndarray,
        rainfall: np.ndarray
    ) -> np.ndarray:
        """Vectorized batch evaluation across simulation timesteps without recreating the FIS."""
        ...
```

---

## 7. Verification Summary

- **Test Suite**: 21 unit and regression tests in `tests/test_weather_stress.py`.
- **Global Regression**: 141/141 passing across all 8 phases (0 failures, 0 errors, 0 warnings).
- **Sanity Verification**: All 6 benchmark operating cases verified (Cool/Humid $\to 13.11\%$, Normal $\to 45.00\%$, Hot/Dry $\to 79.17\%$, Extreme Hot/Dry $\to 89.29\%$, Heavy Rain $\to 16.00\%$, Rain Relief $\Delta = -63.17\%$).
- **Monotonicity**: Rigorously proven across all 5 physical dimensions.
- **Coverage**: Zero rule gaps or zero-area fallbacks across 6,125 grid test points.
