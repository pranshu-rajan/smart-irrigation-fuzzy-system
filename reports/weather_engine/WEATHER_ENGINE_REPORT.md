# Dynamic Weather Engine & Scenario Evaluation Report — Phase 3

> **Project**: Smart Multizone Irrigation and Water Resource Management Using Hierarchical Adaptive Fuzzy Control  
> **Phase**: Phase 3 Dynamic Weather Engine  
> **Status**: Verified, Fully Operational, Physics-Grounded, and Deterministically Reproducible

---

## 1. Objective

The primary objective of Phase 3 is to construct a **configurable, physics-consistent meteorological scenario generator** that supplies synthetic, high-resolution environmental time-series ($T, RH, R_s, u_2, P$) to the closed-loop irrigation system. The engine supports 6 operational scenarios:
1. **Normal**: Baseline clear-sky diurnal profile (reference controller benchmark).
2. **Hot & Dry**: Elevated thermal regime, suppressed relative humidity, elevated wind speed.
3. **Rainy**: Intermittent precipitation events, elevated humidity, attenuated solar radiation.
4. **Cloudy**: Diffuse low radiation, mild temperatures, suppressed evaporative demand.
5. **Heatwave**: Sustained extreme heat ($>40^\circ\text{C}$ peak) with acute vapor pressure deficit.
6. **Water Scarcity**: Realistic meteorological conditions coupled with a restricted 30% reservoir storage factor ($WAF = 0.30$).

---

## 2. Architecture & Subsystem Interfaces

The Weather Engine acts as the top-level environmental excitation module in the system hierarchy:

```
                               +-------------------------------------+
                               |         SCENARIO MANAGER            |
                               |  Offsets, Multipliers, Rain Params, |
                               |      Water Availability Factor      |
                               +-------------------------------------+
                                                  |
                                                  v
                               +-------------------------------------+
                               |         WEATHER ENGINE              |
                               |  Harmonic Diurnal Solar & Temp,     |
                               |   Psychrometric RH, Wind & Rain     |
                               +-------------------------------------+
                                                  |
                                                  | Continuous Time-Series
                                                  | (T, RH, Rs, u2, P, WAF)
                        +-------------------------+-------------------------+
                        |                                                   |
                        v                                                   v
        +-------------------------------+                   +-------------------------------+
        |      WEATHER STRESS FIS       |                   |        ET0 / ETc MODEL        |
        |           (Phase 8)           |                   |           (Phase 4)           |
        | Atmospheric evaporative pull  |                   | FAO-56 Penman-Monteith crop   |
        | and plant climatic stress     |                   | water consumption             |
        +-------------------------------+                   +-------------------------------+
```

---

## 3. Mathematical Generation Approach

The engine implements continuous parametric formulations calibrated against the empirical observations identified during Phase 2 EDA:

### 3.1 Asymmetric Diurnal Temperature
$$T(t) = T_{\text{mean}} + \Delta T_{\text{scenario}} + \frac{T_{\text{amp}}}{2} \cdot \Psi(t_{\text{hour}}) + \Delta T_{\text{synoptic}}(d) + \epsilon_T(t)$$
Where:
- Pre-dawn minimum occurs at $04:30$; afternoon maximum occurs at $13:45$.
- $\Psi(t_{\text{hour}})$ is an asymmetric harmonic function accounting for faster daytime heating vs. slower radiative nighttime cooling.
- Baseline: $T_{\text{min}} = 18.00^\circ\text{C}, T_{\text{max}} = 34.20^\circ\text{C}, T_{\text{mean}} = 25.75^\circ\text{C}$.

### 3.2 Clear-Sky Truncated Solar Arc
$$R_s(t) = \begin{cases}
R_{s,\text{peak}} \cdot \sin\left(\frac{\pi (t_{\text{hour}} - 5.5)}{14.0}\right) \cdot S_{\text{multiplier}} \cdot \epsilon_s(t), & 5.5 \le t_{\text{hour}} \le 19.5 \\
0.0, & \text{otherwise}
\end{cases}$$
With strict non-negativity enforced: $R_s(t) \ge 0.0\text{ W/m}^2$.

### 3.3 Coupled Relative Humidity
$$RH(t) = \text{clamp}\left(RH_{\text{base}} + \Delta RH_{\text{scenario}} - \beta_H \cdot (T(t) - T_{\text{mean}}) + \epsilon_{RH}(t), 0.0, 100.0\right)$$
Where $\beta_H = 2.78\%/^\circ\text{C}$ models inverse psychrometric saturation pressure dynamics.

### 3.4 Wind Speed
$$u_2(t) = \max\left(0.2, \left(u_{2,\text{base}} + \frac{u_{2,\text{amp}}}{2}\sin\left(\frac{2\pi (t_{\text{hour}} - 8)}{24}\right) + \epsilon_u(t)\right) \cdot W_{\text{multiplier}}\right)$$

### 3.5 Event-Based Precipitation Model
Precipitation is modeled as discrete rainfall events rather than continuous white noise. When an event is triggered by the scenario probability, intensity follows a smoothed envelope with configurable duration ($15\text{–}150\text{ min}$) and peak rate ($mm/\text{min}$). During rain events, humidity is elevated to saturation ($90\text{–}97\%$) and solar radiation is attenuated.

---

## 4. Scenario Parameter Matrix

| Parameter / Modifier | Normal | Hot & Dry | Rainy | Cloudy | Heatwave | Water Scarcity |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Temperature Offset ($\Delta T$)** | $+0.0^\circ\text{C}$ | $+5.0^\circ\text{C}$ | $-4.0^\circ\text{C}$ | $-2.5^\circ\text{C}$ | $+8.0^\circ\text{C}$ | $+1.5^\circ\text{C}$ |
| **Diurnal Range Multiplier** | $1.00$ | $1.15$ | $0.60$ | $0.70$ | $1.25$ | $1.05$ |
| **Relative Humidity Offset ($\Delta RH$)** | $+0.0\%$ | $-20.0\%$ | $+18.0\%$ | $+10.0\%$ | $-25.0\%$ | $-5.0\%$ |
| **Solar Irradiance Multiplier** | $1.00$ | $1.05$ | $0.35$ | $0.40$ | $1.10$ | $1.00$ |
| **Wind Speed Multiplier** | $1.00$ | $1.30$ | $1.10$ | $0.90$ | $1.40$ | $1.05$ |
| **Rain Event Probability / Day** | $0.00$ | $0.00$ | $1.00$ | $0.20$ | $0.00$ | $0.00$ |
| **Rain Duration Range (min)** | $0$ | $0$ | $45\text{–}150$ | $20\text{–}60$ | $0$ | $0$ |
| **Water Availability Factor ($WAF$)**| **$1.00$** | **$1.00$** | **$1.00$** | **$1.00$** | **$1.00$** | **$0.30$** |

---

## 5. 24-Hour Simulation Results (1,440 Steps per Scenario)

| Scenario | Temp Range (°C) | Temp Mean (°C) | RH Range (%) | RH Mean (%) | Solar Peak (W/m²) | Cumulative Rain (mm) | $WAF$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Normal** | $18.17\text{–}34.42$ | $25.75$ | $40.56\text{–}85.80$ | $64.53$ | $933.24$ | $0.00$ | $1.00$ |
| **Hot & Dry** | $22.02\text{–}40.67$ | $30.74$ | $16.74\text{–}68.75$ | $44.53$ | $985.34$ | $0.00$ | $1.00$ |
| **Rainy** | $16.89\text{–}26.65$ | $21.75$ | $68.61\text{–}96.96$ | $88.58$ | $328.77$ | $25.29$ | $1.00$ |
| **Cloudy** | $17.58\text{–}28.91$ | $23.25$ | $55.56\text{–}90.04$ | $74.52$ | $374.88$ | $0.00$ | $1.00$ |
| **Heatwave** | $24.72\text{–}44.97$ | $33.74$ | $9.32\text{–}63.74$ | $39.54$ | $1032.17$ | $0.00$ | $1.00$ |
| **Water Scarcity** | $19.09\text{–}36.00$ | $27.25$ | $36.03\text{–}82.20$ | $59.54$ | $933.24$ | $0.00$ | **$0.30$** |

---

## 6. Multi-Day Scalability & Synoptic Weather Drift

The engine scales dynamically beyond 24 hours:
- **7-Day Simulation**: 10,080 discrete 1-minute steps.
- **30-Day Simulation**: 43,200 discrete 1-minute steps.
- **Inter-Diurnal Variation**: Synoptic drift ensures day-to-day temperature means vary realistically by $\pm 1.5^\circ\text{C}$ across multiple days without naive array repetition, providing rigorous test conditions for closed-loop controllers.

---

## 7. Deterministic Reproducibility

- The PRNG is governed by `numpy.random.default_rng(seed)`.
- When identical seeds (e.g. `seed=42`) are provided, the generated time-series is **bit-for-bit identical across runs**.
- Different seeds generate distinct, valid meteorological realizations.

---

## 8. Visualizations Generated

All figures are compiled in [`reports/weather_engine/figures/`](figures/):
1. `temperature_comparison.png`: Diurnal temperature profiles across all 6 scenarios.
2. `humidity_comparison.png`: Diurnal relative humidity comparison.
3. `solar_radiation_comparison.png`: Solar radiation comparison highlighting clear-sky vs. cloud-attenuated profiles.
4. `wind_speed_comparison.png`: Convective wind profiles.
5. `rainfall_comparison.png`: Instantaneous rate ($mm/\text{min}$) and cumulative depth ($mm$).
6. Individual 24h profiles:
   - `profile_normal.png`
   - `profile_hot_dry.png`
   - `profile_rainy.png`
   - `profile_cloudy.png`
   - `profile_heatwave.png`
   - `profile_water_scarcity.png`

---

## 9. Downstream Hand-off

1. **Phase 4: FAO-56 Penman-Monteith $ET_0$ / $ET_c$**: Will ingest $T(t), RH(t), R_s(t), u_2(t)$ directly to calculate reference evapotranspiration.
2. **Phase 8: Weather Stress FIS**: Will evaluate climatic harshness index from temperature, humidity, solar radiation, and wind speed.
3. **Phase 13: Water Allocation FIS**: Will ingest `water_availability_factor` to trigger triage and priority-based allocation when storage drops below threshold.

---

## 10. Confirmation & Next Step

- **CONFIRMED**: No ET0/ETc equations, crop water demand, or closed-loop soil-water balances were implemented.
- **CONFIRMED**: No fuzzy logic, membership functions, or rules were created.
- **NEXT STEP**: **PHASE 4 — FAO-56 PENMAN-MONTEITH ET0 / ETc MODELS**.
