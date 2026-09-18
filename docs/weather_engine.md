# Weather Engine Specification & User Guide

> **Core Disclaimer**: The Weather Engine generates controlled, physics-inspired simulation scenarios for control systems experimentation and is **not a numerical weather forecasting model**.

---

## 1. Overview

The `WeatherEngine` provides deterministic or stochastic time-series generation of meteorological variables required by the multizone irrigation control system. It supports discrete step sizes (default: 1 minute) across flexible simulation horizons (24 hours, 7 days, 30 days) and 6 environmental scenarios.

---

## 2. Interface Specification

### Class: `WeatherEngine`
Located in `simulation/weather.py`.

```python
from config.schemas import SimulationScenario
from simulation.weather import WeatherEngine

# Initialize engine with designated scenario and PRNG seed
engine = WeatherEngine(scenario=SimulationScenario.HOT_AND_DRY, seed=42)

# Generate 24-hour timeline at 1-minute resolution (1440 steps)
df_24h = engine.generate_timeline(
    duration_hours=24,
    timestep_minutes=1,
    start_time="2026-06-01 00:00:00",
)

# Generate 7-day timeline (10080 steps)
df_7d = engine.generate_timeline(duration_hours=168, timestep_minutes=1)

# Generate 30-day timeline (43200 steps)
df_30d = engine.generate_timeline(duration_hours=720, timestep_minutes=1)
```

### Generated Output Schema

| Column Name | Semantic Description | Physical Unit | Representation | Bounds / Constraints |
| :--- | :--- | :---: | :---: | :---: |
| `timestamp` | Simulation observation timestamp | ISO 8601 | Datetime | Monotonically increasing |
| `temperature` | Air temperature at 2m height | °C | Float (2 dec) | $[-20.0, 60.0]$ |
| `humidity` | Relative humidity at 2m height | % | Float (2 dec) | $[0.0, 100.0]$ |
| `solar_radiation` | Global downward horizontal solar irradiance | W/m² | Float (2 dec) | $\ge 0.0$ (0.0 at night) |
| `wind_speed` | Wind velocity at 2m height | m/s | Float (2 dec) | $\ge 0.2$ |
| `rainfall` | Liquid precipitation depth per timestep | mm/step | Float (3 dec) | $\ge 0.0$ |
| `scenario` | Operational scenario label | — | String | One of 6 scenarios |
| `water_availability_factor` | Reservoir budget fraction for water allocation | fraction | Float (2 dec) | $[0.1, 1.0]$ |

---

## 3. Mathematical Formulations

### 3.1 Diurnal Temperature Cycle
The ambient temperature follows an asymmetric harmonic wave:
$$T(t) = T_{\text{mean}} + \Delta T_{\text{scenario}} + \frac{T_{\text{amp}}}{2} \cdot \Psi(t_{\text{hour}}) + \Delta T_{\text{synoptic}}(d) + \epsilon_T(t)$$
- $\Psi(t_{\text{hour}})$ incorporates an asymmetric exponent accounting for rapid morning radiative warming and slower nighttime radiative cooling.
- Pre-dawn minimum occurs around $04:30$; afternoon peak occurs at $13:45$.
- Multi-day synoptic drift $\Delta T_{\text{synoptic}}(d)$ introduces realistic inter-diurnal weather front fluctuations ($\pm 1.5^\circ\text{C}$).

### 3.2 Clear-Sky Truncated Solar Arc
$$R_s(t) = \begin{cases}
R_{s,\text{peak}} \cdot \sin\left(\frac{\pi (t_{\text{hour}} - t_{\text{sr}})}{t_{\text{ss}} - t_{\text{sr}}}\right) \cdot S_{\text{multiplier}} \cdot (1 - C_{\text{cloud}}) + \epsilon_R(t), & t_{\text{sr}} \le t_{\text{hour}} \le t_{\text{ss}} \\
0.0, & \text{otherwise}
\end{cases}$$
- Sunrise $t_{\text{sr}} = 05:30$; Sunset $t_{\text{ss}} = 19:30$.
- Zero radiation strictly enforced during nighttime hours.

### 3.3 Coupled Relative Humidity
$$RH(t) = \text{clamp}\left(RH_{\text{base}} + \Delta RH_{\text{scenario}} - \beta_H \cdot (T(t) - T_{\text{mean}}) + \epsilon_{RH}(t), 0.0, 100.0\right)$$
- $\beta_H = 2.78\%/^\circ\text{C}$ models saturation vapor pressure inverse coupling.

### 3.4 Wind Velocity
$$u_2(t) = \max\left(0.2, \left(u_{2,\text{base}} + \frac{u_{2,\text{amp}}}{2} \sin\left(\frac{2\pi(t_{\text{hour}} - 8)}{24}\right) + \epsilon_u(t)\right) \cdot W_{\text{multiplier}}\right)$$

### 3.5 Event-Based Rainfall Model
Precipitation is generated as discrete episodic events:
- Initiation governed by scenario rain probability $P_{\text{rain}}$.
- Duration sampled between $t_{\text{dur,min}}$ and $t_{\text{dur,max}}$.
- Rate smoothed by a sinusoidal event envelope $I(t) = I_{\text{base}} \cdot \sin(\pi \tau) \cdot \eta(t)$ where $\tau \in [0, 1]$.
- During precipitation, humidity is elevated toward saturation ($90\text{–}98\%$) and solar radiation is strongly attenuated.

---

## 4. Scenario Definitions

1. **Normal**: Standard clear-sky diurnal cycle ($T \in [18, 34^\circ\text{C}], RH \in [40, 86\%], R_{s,\text{max}} = 933\text{ W/m}^2, u_2 \in [1.4, 3.6\text{ m/s}]$, rain $= 0.0\text{ mm}, WAF = 1.0$).
2. **Hot & Dry**: $+5.0^\circ\text{C}$ temperature shift ($T_{\text{max}} \approx 40.7^\circ\text{C}$), $-20\%$ humidity shift, $+30\%$ wind speed. High evaporative stress.
3. **Rainy**: $-4.0^\circ\text{C}$ temperature reduction, $+18\%$ humidity shift, $-65\%$ solar attenuation, multiple rainfall episodes ($~25\text{ mm}$ daily accumulation).
4. **Cloudy**: Diffuse overcast radiation (peak $<375\text{ W/m}^2$), mild diurnal amplitude, elevated humidity.
5. **Heatwave**: Severe heatwave with $+8.0^\circ\text{C}$ offset ($T_{\text{peak}} \approx 45^\circ\text{C}$), $-25\%$ humidity, acute drying power.
6. **Water Scarcity**: Baseline meteorology coupled with an explicit $30\%$ reservoir availability factor ($WAF = 0.30$), forcing water-rationing behavior in the downstream allocation controller.

---

## 5. Reproducibility & Testing

To regenerate all 6 scenario datasets and comparative plots:
```bash
python scripts/generate_weather_scenarios.py
```
To run the automated test suite:
```bash
python -m pytest tests/test_weather_engine.py -v
```
