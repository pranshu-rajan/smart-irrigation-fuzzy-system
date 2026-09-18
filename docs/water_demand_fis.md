# Phase 9 Documentation: Water Demand Fuzzy Inference System (WaterDemandFIS)

## 1. Overview & Architectural Role

The **Water Demand Fuzzy Inference System (`WaterDemandFIS`)** is the third diagnostic fuzzy inference subsystem in the hierarchical smart irrigation architecture. Its objective is to evaluate the real-time crop water urgency by synthesizing three physical indicators:
1. **Crop Evapotranspiration ($ET_c$)** [$0.0–15.0\text{ mm/day}$]
2. **Crop Water Deficit ($D_{\text{crop}}$)** [$0.0–15.0\text{ mm/day}$]
3. **Effective Rainfall ($P_{\text{eff}}$)** [$0.0–50.0\text{ mm}$]

The resulting **Water Demand index** $[0.0, 100.0]\%$ quantifies the normalized physiological urgency of the crop for water replenishment. In the overall control hierarchy, this output feeds directly into the **Main Irrigation FIS** (Phase 10) alongside root-zone Soil Stress (Phase 7), atmospheric Weather Stress (Phase 8), and Soil Moisture Tracking Error.

```
+-------------------------------------------------------------------------------+
|                        WATER DEMAND FIS (Phase 9)                             |
|                                                                               |
|   Crop Evapotranspiration ETc [0 - 15 mm/day] ────┐                           |
|   Crop Water Deficit [0 - 15 mm/day] ─────────────┼──► [ 39-Rule Mamdani FIS]──► Water Demand
|   Effective Rainfall [0 - 50 mm] ─────────────────┘     (3-Layer Architecture)  [0 - 100]%
|                                                                               |
+-------------------------------------------------------------------------------+
```

---

## 2. Fundamental Conceptual Distinctions

To ensure theoretical integrity and prevent conceptual confusion across agronomic and control engineering domains, the architecture strictly distinguishes seven key quantities:

```
+───────────────────────────────────────────────────────────────────────────────────────────────+
|                                    CONCEPTUAL DISTINCTIONS                                    |
+───────────────────────────────────────────────────────────────────────────────────────────────+
| Variable             | Domain       | Unit       | Physical / Functional Meaning             |
|──────────────────────+──────────────+────────────+───────────────────────────────────────────|
| ETc                  | Physical     | mm/day     | Crop evapotranspiration rate: Kc * ET0    |
| Crop Water Deficit   | Physical     | mm/day     | Atmospheric demand remaining: max(ETc-Peff,0)|
| Effective Rainfall   | Physical     | mm         | Infiltrated rainfall available to rootzone|
| Soil Moisture Error  | Tracking     | % (m3/m3)  | Target moisture minus current moisture    |
| Soil Stress          | Fuzzy Index  | %          | Root-zone water scarcity from RSM & error |
| Weather Stress       | Fuzzy Index  | %          | Atmospheric climatic evaporative severity |
| Water Demand         | Fuzzy Index  | %          | Normalized crop-water urgency assessment  |
| Available Water      | Physical     | % / Liters | Reservoir / supply resource constraint    |
| Irrigation Command   | Control      | % (0-100)  | Final actuator pulse or valve command     |
+───────────────────────────────────────────────────────────────────────────────────────────────+
```

### 2.1 Water Demand $\neq$ ETc
- **$ET_c$** is the physical consumptive water rate of the crop under standard non-stress conditions ($ET_c = K_c \times ET_0$), expressed in millimeters per day.
- **Water Demand** is a normalized fuzzy interpretation ($0–100\%$) that combines $ET_c$ with immediate natural replenishment ($P_{\text{eff}}$) and the remaining atmospheric deficit. Even with elevated $ET_c$, substantial rainfall reduces Water Demand.

### 2.2 Water Demand $\neq$ Crop Water Deficit
- **Crop Water Deficit** ($D_{\text{crop}} = \max(ET_c - P_{\text{eff}}, 0)$) is an unbuffered physical flux deficit in millimeters per day.
- **Water Demand** provides a fuzzy nonlinear mapping that accounts for the relative magnitude of $ET_c$ and rainfall relief, providing smooth control surfaces without hard step discontinuities.

### 2.3 Water Demand $\neq$ Soil Stress
- **Soil Stress** evaluates the underground root-zone state (Relative Soil Moisture and tracking error relative to field capacity and wilting point).
- **Water Demand** evaluates the aboveground consumptive requirement and atmospheric replenishment. A crop may experience high Water Demand (due to hot sunny weather) while Soil Stress is still low (because soil moisture is currently near field capacity).

### 2.4 Water Demand $\neq$ Available Water
- **Available Water** is a supply-side resource constraint reflecting reservoir storage or delivery quota (used in Phase 13: Water Allocation FIS).
- **Water Demand** is entirely demand-side: how much water the crop physiologically requires regardless of supply limitations.

### 2.5 Water Demand $\neq$ Irrigation Command
- **Irrigation Command** ($0–100\%$) is the final supervisory control decision generated by the Main Irrigation FIS (Phase 10), which synthesizes Soil Stress, Weather Stress, Water Demand, and Moisture Error. Water Demand is an input to this synthesis, not the final decision.

---

## 3. Mathematical & Fuzzy Specification

### 3.1 Input Universes & Membership Sets (from `config/fuzzy_config.json`)

#### 1. Crop Evapotranspiration ($ET_c$)
- **Universe**: $[0.0, 15.0]\text{ mm/day}$
- **Linguistic Terms**:
  - `very_low`: Trapezoidal $[0.0, 0.0, 1.0, 2.5]$
  - `low`: Triangular $[1.5, 3.5, 5.5]$
  - `moderate`: Triangular $[4.5, 7.0, 9.5]$
  - `high`: Triangular $[8.5, 10.5, 12.5]$
  - `very_high`: Trapezoidal $[11.5, 13.0, 15.0, 15.0]$

#### 2. Crop Water Deficit ($D_{\text{crop}}$)
- **Universe**: $[0.0, 15.0]\text{ mm/day}$
- **Linguistic Terms**:
  - `none`: Trapezoidal $[0.0, 0.0, 0.5, 2.0]$
  - `low`: Triangular $[0.8, 2.5, 5.0]$
  - `moderate`: Triangular $[3.5, 6.5, 9.5]$
  - `high`: Triangular $[8.0, 10.5, 12.5]$
  - `very_high`: Trapezoidal $[11.0, 13.0, 15.0, 15.0]$

#### 3. Effective Rainfall ($P_{\text{eff}}$)
- **Universe**: $[0.0, 50.0]\text{ mm}$
- **Linguistic Terms**:
  - `none`: Trapezoidal $[0.0, 0.0, 0.3, 1.8]$
  - `low`: Triangular $[0.6, 2.5, 6.0]$
  - `moderate`: Triangular $[4.0, 9.0, 16.0]$
  - `high`: Triangular $[12.0, 20.0, 32.0]$
  - `very_high`: Trapezoidal $[24.0, 34.0, 50.0, 50.0]$

### 3.2 Output Universe & Membership Sets

#### Water Demand
- **Universe**: $[0.0, 100.0]\%$
- **Linguistic Terms**:
  - `very_low`: Trapezoidal $[0.0, 0.0, 10.0, 25.0]$
  - `low`: Triangular $[15.0, 30.0, 45.0]$
  - `moderate`: Triangular $[35.0, 50.0, 65.0]$
  - `high`: Triangular $[55.0, 70.0, 85.0]$
  - `very_high`: Trapezoidal $[75.0, 90.0, 100.0, 100.0]$

---

## 4. Inference Engine Methodology

The inference engine strictly adheres to the project-wide standard:
- **Inference Type**: Mamdani Fuzzy Inference System
- **T-Norm (AND)**: Minimum ($\min$)
- **S-Norm (OR)**: Maximum ($\max$)
- **Implication**: Minimum truncation ($\min$)
- **Aggregation**: Maximum union ($\max$)
- **Defuzzification**: Centroid (Center of Gravity) over a 501-point uniform grid

$$\mu_{\text{agg}}(z) = \max_{i=1}^M \left[ \min(\beta_i, \mu_{C_i}(z)) \right]$$

$$z^* = \frac{\int_{0}^{100} z \, \mu_{\text{agg}}(z) \, dz}{\int_{0}^{100} \mu_{\text{agg}}(z) \, dz}$$

---

## 5. Hierarchical Rule Architecture (39 Rules)

To avoid an uninterpretable $5 \times 5 \times 5 = 125$ Cartesian explosion while guaranteeing 100% input space coverage, the rule base is organized into 3 operational layers:

### Layer 1: Heavy / Torrential Rainfall Mitigation (9 Rules)
- Active when $P_{\text{eff}} \in \{\text{high}, \text{very\_high}\}$.
- Significant rainfall quenches immediate water demand regardless of instantaneous $ET_c$.
- Deficit dominance is preserved: if legacy deficit is extreme (`very_high`), demand is tempered to `moderate` rather than completely eliminated.

### Layer 2: Moderate Rainfall Regime (5 Rules)
- Active when $P_{\text{eff}} \in \{\text{moderate}\}$.
- Moderate rainfall satisfies low deficits, balances moderate deficits, but leaves elevated residual demand when deficits are high or severe.

### Layer 3: Dry / Minimal Rain Baseline Kernel (25 Rules)
- Active when $P_{\text{eff}} \in \{\text{none}, \text{low}\}$.
- Complete $5 \times 5$ matrix of $ET_c \times \text{Deficit}$ covering all transpirational and deficit combinations under parched or dry conditions.

---

## 6. Python API Reference

```python
from fuzzy_engine.water_demand import WaterDemandFIS

# 1. Instantiate
fis = WaterDemandFIS(resolution=501)

# 2. Scalar Evaluation
demand = fis.evaluate(etc=6.5, crop_water_deficit=4.0, effective_rainfall=1.0)
# Returns float in [0.0, 100.0]%

# 3. Detailed Telemetry Evaluation
telemetry = fis.evaluate_detailed(etc=6.5, crop_water_deficit=4.0, effective_rainfall=1.0)
# Returns dict with memberships, active rules, weights, total fuzzy area, and crisp output

# 4. Vectorized Batch Evaluation (High Performance)
import numpy as np
etc_arr = np.array([1.0, 5.0, 10.0])
def_arr = np.array([0.0, 3.0, 8.0])
rain_arr = np.array([15.0, 2.0, 0.0])
demands = fis.evaluate_array(etc_arr, def_arr, rain_arr)
```
