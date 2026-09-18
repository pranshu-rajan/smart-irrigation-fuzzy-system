# Phase 10 Documentation: Main Irrigation Fuzzy Inference System (MainIrrigationFIS)

## 1. Overview & Architectural Role

The **Main Irrigation Fuzzy Inference System (`MainIrrigationFIS`)** is the core supervisory controller of the hierarchical adaptive fuzzy control architecture. It functions as the central synthesis node that evaluates four heterogeneous physical and diagnostic indicators:
1. **Soil Stress** ($[0.0, 100.0]\%$) — from `SoilStressFIS` (Phase 7)
2. **Weather Stress** ($[0.0, 100.0]\%$) — from `WeatherStressFIS` (Phase 8)
3. **Water Demand** ($[0.0, 100.0]\%$) — from `WaterDemandFIS` (Phase 9)
4. **Moisture Tracking Error ($e(t) = \text{SM}_{\text{target}} - \text{SM}(t)$)** ($[-30.0, 30.0]\%$) — from closed-loop root-zone soil dynamics (Phase 5)

The controller synthesizes these inputs into a single normalized **Irrigation Command** ($[0.0, 100.0]\%$).

```
+-------------------------------------------------------------------------------+
|                       MAIN IRRIGATION FIS (Phase 10)                          |
|                                                                               |
|   Soil Stress [0 - 100 %] ────────────────────────┐                           |
|   Weather Stress [0 - 100 %] ─────────────────────┼──► [ 32-Rule Mamdani FIS]─┼──► Irrigation Command
|   Water Demand [0 - 100 %] ───────────────────────┤     (5-Layer Architecture)│    [0 - 100]%
|   Moisture Error [-30 - +30 %] ───────────────────┘                           |
+-------------------------------------------------------------------------------+
```

---

## 2. Fundamental Conceptual Distinctions

To ensure control clarity and avoid conflating physical and diagnostic quantities, the system enforces the following separations:

```
+───────────────────────────────────────────────────────────────────────────────────────────────+
|                                    CONCEPTUAL DISTINCTIONS                                    |
+───────────────────────────────────────────────────────────────────────────────────────────────+
| Variable             | Domain       | Unit       | Meaning                                    |
|──────────────────────+──────────────+────────────+────────────────────────────────────────────|
| Soil Stress          | Fuzzy Index  | %          | Root-zone water deficit/wilting risk       |
| Weather Stress       | Fuzzy Index  | %          | Atmospheric climatic evaporative severity  |
| Water Demand         | Fuzzy Index  | %          | Canopy physiological replenishment urgency|
| Moisture Error       | Tracking     | % (m3/m3)  | Target soil moisture minus current moisture|
| Irrigation Command   | Control      | % (0-100)  | Normalized supervisory actuator command    |
| Available Water      | Physical     | % / Liters | Supply-side reservoir quota (Phase 13 only)|
+───────────────────────────────────────────────────────────────────────────────────────────────+
```

### 2.1 Irrigation Command is Normalized, Not Physical Volume
The Irrigation Command ($0.0–100.0\%$) is a normalized supervisory control signal. It does not directly represent liters, millimeters per hour, or valve duty cycle. Mapping from the normalized command to physical valve timing and emitter flow rates is executed by the downstream hydraulic/actuator layer.

### 2.2 Available Water is Strictly Excluded
`Available Water` represents a supply-side resource quota (e.g., reservoir reserves or water rationing factors). It belongs exclusively to the **Water Allocation FIS** (Phase 13). Main Irrigation FIS evaluates unconstrained demand-side irrigation urgency; filtering by supply constraints occurs downstream.

---

## 3. Mathematical & Fuzzy Specification

All input and output universes and membership functions are directly loaded from [`config/fuzzy_config.json`](file:///c:/Users/pranshu/Desktop/irrigation_system/config/fuzzy_config.json):

### 3.1 Input Variables
1. **`soil_stress`**: Universe $[0.0, 100.0]\%$
   - `low`: Trapezoidal $[0.0, 0.0, 15.0, 35.0]$
   - `moderate`: Triangular $[25.0, 45.0, 65.0]$
   - `high`: Triangular $[55.0, 75.0, 85.0]$
   - `very_high`: Trapezoidal $[75.0, 85.0, 100.0, 100.0]$
2. **`weather_stress`**: Universe $[0.0, 100.0]\%$
   - `low`: Trapezoidal $[0.0, 0.0, 15.0, 35.0]$
   - `moderate`: Triangular $[25.0, 45.0, 65.0]$
   - `high`: Triangular $[55.0, 75.0, 85.0]$
   - `very_high`: Trapezoidal $[75.0, 85.0, 100.0, 100.0]$
3. **`water_demand`**: Universe $[0.0, 100.0]\%$
   - `very_low`: Trapezoidal $[0.0, 0.0, 10.0, 25.0]$
   - `low`: Triangular $[15.0, 30.0, 45.0]$
   - `moderate`: Triangular $[35.0, 50.0, 65.0]$
   - `high`: Triangular $[55.0, 70.0, 85.0]$
   - `very_high`: Trapezoidal $[75.0, 90.0, 100.0, 100.0]$
4. **`moisture_error`**: Universe $[-30.0, 30.0]\%$
   - `large_negative`: Trapezoidal $[-30.0, -30.0, -20.0, -10.0]$
   - `negative`: Triangular $[-15.0, -7.5, 0.0]$
   - `zero`: Triangular $[-5.0, 0.0, 5.0]$
   - `positive`: Triangular $[0.0, 7.5, 15.0]$
   - `large_positive`: Trapezoidal $[10.0, 20.0, 30.0, 30.0]$

### 3.2 Output Variable
1. **`irrigation_command`**: Universe $[0.0, 100.0]\%$
   - `off`: Trapezoidal $[0.0, 0.0, 5.0, 15.0]$
   - `low`: Triangular $[10.0, 25.0, 40.0]$
   - `moderate`: Triangular $[30.0, 50.0, 70.0]$
   - `high`: Triangular $[60.0, 75.0, 90.0]$
   - `maximum`: Trapezoidal $[80.0, 90.0, 100.0, 100.0]$

---

## 4. Inference Engine Methodology

- **Type**: Mamdani Fuzzy Inference System
- **T-Norm (AND)**: Minimum ($\min$)
- **S-Norm (OR)**: Maximum ($\max$)
- **Implication**: Minimum truncation ($\min$)
- **Aggregation**: Maximum union ($\max$)
- **Defuzzification**: Centroid (Center of Gravity) over a 501-point uniform grid:
  $$z^* = \frac{\int_0^{100} z \, \mu_{\text{agg}}(z) \, dz}{\int_0^{100} \mu_{\text{agg}}(z) \, dz}$$

---

## 5. Hierarchical Rule Architecture (32 Rules)

Rather than an uninterpretable $4 \times 4 \times 5 \times 5 = 400$ rule Cartesian explosion, the rule base is organized into **5 transparent operational layers**:

### Layer 1: Moisture Error Safety & Oversaturation Suppression (Rules 1–4)
If current soil moisture is substantially above target ($e(t) < 0$), irrigation is strictly suppressed to `off` ($<15\%$) to prevent root hypoxia, leaching, and water waste. Only when both soil stress and water demand are extreme does the system permit a minimal maintenance pulse (`low`).

### Layer 2: Balanced / At-Target Moisture Regulation (Rules 5–15)
When soil moisture is near target ($e(t) \approx 0$), irrigation command matches active transpirational demand and emerging soil stress.

### Layer 3: Moisture Deficit Replacement Kernel (Rules 16–25)
When soil moisture is below target ($e(t) > 0$), irrigation command scales directly with soil stress severity and canopy water demand.

### Layer 4: Severe Moisture Depletion Override (Rules 26–28)
When moisture error is in `large_positive` ($e(t) \ge 10\%$), the controller issues high to maximum replenishment commands.

### Layer 5: Climatic Forcing & Environmental Modulation (Rules 29–32)
Extreme atmospheric stress (heatwaves) amplifies irrigation during soil moisture deficits, while cool calm weather eliminates unnecessary watering.

---

## 6. Python API Reference

```python
from fuzzy_engine.main_irrigation import MainIrrigationFIS

# 1. Instantiate
fis = MainIrrigationFIS(resolution=501)

# 2. Scalar Evaluation
cmd = fis.evaluate(
    soil_stress=65.0,
    weather_stress=55.0,
    water_demand=60.0,
    moisture_error=8.0
)
# Returns float in [0.0, 100.0]%

# 3. Detailed Telemetry Evaluation
telemetry = fis.evaluate_detailed(
    soil_stress=65.0,
    weather_stress=55.0,
    water_demand=60.0,
    moisture_error=8.0
)

# 4. Vectorized Batch Evaluation
cmds = fis.evaluate_array(
    soil_stress_arr,
    weather_stress_arr,
    water_demand_arr,
    moisture_error_arr
)
```
