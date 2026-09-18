# Phase 6 Technical Documentation: Fuzzy Variables, Universes, and Membership Functions

## 1. Purpose

This document provides the mathematical, engineering, and architectural specification of all 19 fuzzy variables, universes of discourse, and linguistic membership functions established in Phase 6 for the **Smart Multizone Irrigation and Water Resource Management Using Hierarchical Adaptive Fuzzy Control** system.

This module acts as the foundational fuzzy-variable layer for the five planned Mamdani Fuzzy Inference Systems (FIS). It guarantees consistent semantic interpretation, strict mathematical validity, partition of unity coverage, and physical unit integrity without yet implementing fuzzy rules or defuzzification (which are reserved for Phases 7–10).

---

## 2. Hierarchical Fuzzy-Control Architecture

The irrigation control architecture coordinates 5 specialized FIS modules organized hierarchically across three operational tiers:

```
[ Tier 1: Domain-Specific Stress & Demand Analysis ]
┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐
│   Soil Stress FIS      │  │   Weather Stress FIS   │  │    Water Demand FIS    │
│ Inputs: RSM, Error     │  │ Inputs: T, RH, Rs, u, P│  │ Inputs: ETc, CWD, Peff │
│ Output: Soil Stress    │  │ Output: Weather Stress │  │ Output: Water Demand   │
└───────────┬────────────┘  └───────────┬────────────┘  └───────────┬────────────┘
            │                           │                           │
            └───────────────────┐       │       ┌───────────────────┘
                                ▼       ▼       ▼
                    ┌────────────────────────────────────────┐
                    │       Main Irrigation Controller       │
                    │ Inputs: Soil Stress, Weather Stress,   │ [ Tier 2: Supervisory ]
                    │         Water Demand, Moisture Error   │
                    │ Output: Irrigation Command [0 - 100]%  │
                    └───────────────────┬────────────────────┘
                                        │
                                        ▼
                    ┌────────────────────────────────────────┐
                    │      Water Allocation Controller       │
                    │ Inputs: Zone Demand, Zone Stress,      │ [ Tier 3: Multizone ]
                    │         Available Water, Zone Priority │
                    │ Output: Zone Allocation [0 - 100]%     │
                    └────────────────────────────────────────┘
```

This decoupled hierarchical structure prevents rule-base explosion. A single monolithic controller with 14 inputs would require $5^{14} \approx 6.1 \times 10^9$ rules. By partitioning the system into 5 coordinated FIS units, the maximum rule base per subsystem is limited to $3^2$ to $5^4$, keeping the system interpretable, computationally lightweight, and suitable for embedded or edge deployment.

---

## 3. Mamdani Fuzzy Logic Methodology

The system adopts the classical **Mamdani fuzzy inference methodology**:
1. **Fuzzification**: Numerical crisp sensor inputs are evaluated against membership functions $\mu_A(x) \in [0.0, 1.0]$.
2. **Conjunction (T-Norm)**: Minimum operator $\min(\mu_A(x), \mu_B(y))$.
3. **Disjunction (S-Norm)**: Maximum operator $\max(\mu_A(x), \mu_B(y))$.
4. **Implication**: Mamdani min-implication truncating output membership functions.
5. **Aggregation**: Max-aggregation across all active rules.
6. **Defuzzification (Phases 7–10)**: Centroid (Center of Gravity / Area) defuzzification.

In Phase 6, the emphasis is placed on ensuring that the universes and membership functions are properly shaped and saturated so that downstream fuzzification never yields indeterminate states or division-by-zero errors.

---

## 4. Input and Output Variables Specification

The 19 fuzzy variables are grouped by subsystem:

| FIS Subsystem | Role | Variable Name | Display Name | Physical Range | Unit | Linguistic Sets |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Soil Stress FIS** | Input | `rsm` | Relative Soil Moisture | $[0.0, 1.0]$ | dimensionless | Very Dry, Dry, Adequate, Wet, Very Wet |
| | Input | `moisture_error` | Moisture Tracking Error | $[-30.0, 30.0]$ | % | Large Negative, Negative, Zero, Positive, Large Positive |
| | Output | `soil_stress` | Soil Moisture Stress | $[0.0, 100.0]$ | % | Low, Moderate, High, Very High |
| **Weather Stress FIS** | Input | `temperature` | Ambient Temperature | $[10.0, 50.0]$ | °C | Low, Moderate, High, Very High |
| | Input | `humidity` | Relative Humidity | $[0.0, 100.0]$ | % | Very Low, Low, Moderate, High, Very High |
| | Input | `solar_radiation` | Solar Radiation | $[0.0, 1200.0]$ | $\text{W/m}^2$ | Low, Moderate, High, Very High |
| | Input | `wind_speed` | Wind Speed | $[0.0, 15.0]$ | m/s | Calm, Low, Moderate, High, Very High |
| | Input | `rainfall` | Precipitation | $[0.0, 50.0]$ | mm | None, Light, Moderate, Heavy, Very Heavy |
| | Output | `weather_stress` | Weather Stress | $[0.0, 100.0]$ | % | Low, Moderate, High, Very High |
| **Water Demand FIS** | Input | `etc` | Crop Evapotranspiration | $[0.0, 15.0]$ | mm/day | Very Low, Low, Moderate, High, Very High |
| | Input | `crop_water_deficit` | Crop Water Deficit | $[0.0, 15.0]$ | mm/day | None, Low, Moderate, High, Very High |
| | Input | `effective_rainfall` | Effective Infiltrated Rain | $[0.0, 50.0]$ | mm | None, Low, Moderate, High, Very High |
| | Output | `water_demand` | Crop Water Demand | $[0.0, 100.0]$ | % | Very Low, Low, Moderate, High, Very High |
| **Main Irrigation FIS** | Input | `soil_stress` | Soil Moisture Stress | $[0.0, 100.0]$ | % | Low, Moderate, High, Very High |
| | Input | `weather_stress` | Weather Stress | $[0.0, 100.0]$ | % | Low, Moderate, High, Very High |
| | Input | `water_demand` | Crop Water Demand | $[0.0, 100.0]$ | % | Very Low, Low, Moderate, High, Very High |
| | Input | `moisture_error` | Moisture Tracking Error | $[-30.0, 30.0]$ | % | Large Negative, Negative, Zero, Positive, Large Positive |
| | Output | `irrigation_command` | Irrigation Command | $[0.0, 100.0]$ | % | Off, Low, Moderate, High, Maximum |
| **Water Allocation FIS** | Input | `zone_demand` | Zone Water Demand | $[0.0, 100.0]$ | % | Very Low, Low, Moderate, High, Very High |
| | Input | `zone_stress` | Zone Crop Stress | $[0.0, 100.0]$ | % | Low, Moderate, High, Very High |
| | Input | `available_water` | Available Source Supply | $[0.0, 100.0]$ | % | Very Low, Low, Moderate, High, Very High |
| | Input | `zone_priority` | Zone Priority Level | $[0.0, 100.0]$ | % | Low, Medium, High, Critical |
| | Output | `zone_allocation` | Allocated Water Ratio | $[0.0, 100.0]$ | % | None, Low, Moderate, High, Maximum |

---

## 5. Mathematical Membership Function Equations

### 5.1 Triangular Membership Function (`trimf`)

A triangular membership function is parameterized by three ordered real numbers $a \le b \le c$:

$$\mu(x; a, b, c) = \begin{cases}
0, & x \le a \\
\frac{x - a}{b - a}, & a < x < b \\
1, & x = b \\
\frac{c - x}{c - b}, & b < x < c \\
0, & x \ge c
\end{cases}$$

### 5.2 Trapezoidal Membership Function (`trapmf`)

A trapezoidal membership function is parameterized by four ordered real numbers $a \le b \le c \le d$:

$$\mu(x; a, b, c, d) = \begin{cases}
0, & x \le a \\
\frac{x - a}{b - a}, & a < x < b \\
1, & b \le x \le c \\
\frac{d - x}{d - c}, & c < x < d \\
0, & x \ge d
\end{cases}$$

### 5.3 Boundary Saturation (Open Shoulders)

To ensure that sensor readings slightly outside the expected physical universe or resting precisely on the boundary do not produce a zero-membership dropout:
- **Left-edge sets** use trapezoidal functions with $a = b = x_{\min}$, maintaining $\mu(x) = 1.0$ for all $x \le b$.
- **Right-edge sets** use trapezoidal functions with $c = d = x_{\max}$, maintaining $\mu(x) = 1.0$ for all $x \ge c$.

---

## 6. Detailed Membership Function Parameter Tables

### 6.1 Soil-Related Variables

#### Relative Soil Moisture (`rsm`) — $[0.0, 1.0]$
- Wilting Point corresponds to $\text{RSM} = 0.0$; Field Capacity corresponds to $\text{RSM} = 1.0$.
- `very_dry`: `trapmf([0.0, 0.0, 0.15, 0.30])`
- `dry`: `trimf([0.20, 0.35, 0.50])`
- `adequate`: `trimf([0.40, 0.55, 0.70])`
- `wet`: `trimf([0.60, 0.75, 0.85])`
- `very_wet`: `trapmf([0.75, 0.85, 1.0, 1.0])`

#### Moisture Tracking Error (`moisture_error`) — $[-30.0, 30.0]\%$
- Definition: $e(t) = \theta_{\text{target}} - \theta_{\text{current}}$. Positive error indicates moisture deficit; negative error indicates excess moisture.
- `large_negative`: `trapmf([-30.0, -30.0, -20.0, -10.0])`
- `negative`: `trimf([-15.0, -7.5, 0.0])`
- `zero`: `trimf([-5.0, 0.0, 5.0])`
- `positive`: `trimf([0.0, 7.5, 15.0])`
- `large_positive`: `trapmf([10.0, 20.0, 30.0, 30.0])`

#### Soil Moisture Stress (`soil_stress`) — $[0.0, 100.0]\%$
- `low`: `trapmf([0.0, 0.0, 15.0, 35.0])`
- `moderate`: `trimf([25.0, 45.0, 65.0])`
- `high`: `trimf([55.0, 75.0, 85.0])`
- `very_high`: `trapmf([75.0, 85.0, 100.0, 100.0])`

---

### 6.2 Meteorological Variables

#### Ambient Temperature (`temperature`) — $[10.0, 50.0]^\circ\text{C}$
- `low`: `trapmf([10.0, 10.0, 18.0, 24.0])`
- `moderate`: `trimf([20.0, 28.0, 34.0])`
- `high`: `trimf([30.0, 38.0, 44.0])`
- `very_high`: `trapmf([40.0, 45.0, 50.0, 50.0])`

#### Relative Humidity (`humidity`) — $[0.0, 100.0]\%$
- `very_low`: `trapmf([0.0, 0.0, 15.0, 30.0])`
- `low`: `trimf([20.0, 35.0, 50.0])`
- `moderate`: `trimf([40.0, 55.0, 70.0])`
- `high`: `trimf([60.0, 75.0, 85.0])`
- `very_high`: `trapmf([75.0, 90.0, 100.0, 100.0])`

#### Solar Radiation (`solar_radiation`) — $[0.0, 1200.0]\text{ W/m}^2$
- `low`: `trapmf([0.0, 0.0, 150.0, 350.0])`
- `moderate`: `trimf([250.0, 500.0, 750.0])`
- `high`: `trimf([650.0, 850.0, 1000.0])`
- `very_high`: `trapmf([900.0, 1050.0, 1200.0, 1200.0])`

#### Wind Speed (`wind_speed`) — $[0.0, 15.0]\text{ m/s}$
- `calm`: `trapmf([0.0, 0.0, 1.0, 2.5])`
- `low`: `trimf([1.5, 3.5, 5.5])`
- `moderate`: `trimf([4.5, 7.0, 9.5])`
- `high`: `trimf([8.5, 10.5, 12.5])`
- `very_high`: `trapmf([11.5, 13.0, 15.0, 15.0])`

#### Precipitation (`rainfall`) — $[0.0, 50.0]\text{ mm}$
- `none`: `trapmf([0.0, 0.0, 0.2, 1.5])`
- `light`: `trimf([0.4, 2.0, 4.5])`
- `moderate`: `trimf([3.0, 7.0, 14.0])`
- `heavy`: `trimf([10.0, 18.0, 28.0])`
- `very_heavy`: `trapmf([22.0, 32.0, 50.0, 50.0])`

#### Weather Stress (`weather_stress`) — $[0.0, 100.0]\%$
- `low`: `trapmf([0.0, 0.0, 15.0, 35.0])`
- `moderate`: `trimf([25.0, 45.0, 65.0])`
- `high`: `trimf([55.0, 75.0, 85.0])`
- `very_high`: `trapmf([75.0, 85.0, 100.0, 100.0])`

---

### 6.3 Agronomic Demand Variables

#### Crop Evapotranspiration (`etc`) — $[0.0, 15.0]\text{ mm/day}$
- Derived from Phase 4 Penman-Monteith simulations where peak $ET_c$ was observed at $12.56\text{ mm/day}$ under Heatwave scenario. The upper bound of $15.0\text{ mm/day}$ provides a 20% engineering safety margin.
- `very_low`: `trapmf([0.0, 0.0, 1.0, 2.5])`
- `low`: `trimf([1.5, 3.5, 5.5])`
- `moderate`: `trimf([4.5, 7.0, 9.5])`
- `high`: `trimf([8.5, 10.5, 12.5])`
- `very_high`: `trapmf([11.5, 13.0, 15.0, 15.0])`

#### Crop Water Deficit (`crop_water_deficit`) — $[0.0, 15.0]\text{ mm/day}$
- Derived from $CWD = \max(0, ET_c - P_{\text{eff}})$. In dry periods, $P_{\text{eff}} = 0$, so $CWD$ tracks $ET_c$ directly up to $15.0\text{ mm/day}$.
- `none`: `trapmf([0.0, 0.0, 0.5, 2.0])`
- `low`: `trimf([0.8, 2.5, 5.0])`
- `moderate`: `trimf([3.5, 6.5, 9.5])`
- `high`: `trimf([8.0, 10.5, 12.5])`
- `very_high`: `trapmf([11.0, 13.0, 15.0, 15.0])`

#### Effective Infiltrated Rain (`effective_rainfall`) — $[0.0, 50.0]\text{ mm}$
- `none`: `trapmf([0.0, 0.0, 0.3, 1.8])`
- `low`: `trimf([0.6, 2.5, 6.0])`
- `moderate`: `trimf([4.0, 9.0, 16.0])`
- `high`: `trimf([12.0, 20.0, 32.0])`
- `very_high`: `trapmf([24.0, 34.0, 50.0, 50.0])`

#### Crop Water Demand (`water_demand`) — $[0.0, 100.0]\%$
- `very_low`: `trapmf([0.0, 0.0, 10.0, 25.0])`
- `low`: `trimf([15.0, 30.0, 45.0])`
- `moderate`: `trimf([35.0, 50.0, 65.0])`
- `high`: `trimf([55.0, 70.0, 85.0])`
- `very_high`: `trapmf([75.0, 90.0, 100.0, 100.0])`

---

### 6.4 Controller Command & Multizone Allocation Variables

#### Irrigation Command Output (`irrigation_command`) — $[0.0, 100.0]\%$
- `off`: `trapmf([0.0, 0.0, 5.0, 15.0])`
- `low`: `trimf([10.0, 25.0, 40.0])`
- `moderate`: `trimf([30.0, 50.0, 70.0])`
- `high`: `trimf([60.0, 75.0, 90.0])`
- `maximum`: `trapmf([80.0, 90.0, 100.0, 100.0])`

#### Zone Water Demand (`zone_demand`) — $[0.0, 100.0]\%$
- `very_low`: `trapmf([0.0, 0.0, 10.0, 25.0])`
- `low`: `trimf([15.0, 30.0, 45.0])`
- `moderate`: `trimf([35.0, 50.0, 65.0])`
- `high`: `trimf([55.0, 70.0, 85.0])`
- `very_high`: `trapmf([75.0, 90.0, 100.0, 100.0])`

#### Zone Crop Stress (`zone_stress`) — $[0.0, 100.0]\%$
- `low`: `trapmf([0.0, 0.0, 15.0, 35.0])`
- `moderate`: `trimf([25.0, 45.0, 65.0])`
- `high`: `trimf([55.0, 75.0, 85.0])`
- `very_high`: `trapmf([75.0, 85.0, 100.0, 100.0])`

#### Available Source Supply (`available_water`) — $[0.0, 100.0]\%$
- `very_low`: `trapmf([0.0, 0.0, 10.0, 25.0])`
- `low`: `trimf([15.0, 30.0, 45.0])`
- `moderate`: `trimf([35.0, 50.0, 65.0])`
- `high`: `trimf([55.0, 70.0, 85.0])`
- `very_high`: `trapmf([75.0, 90.0, 100.0, 100.0])`

#### Zone Priority (`zone_priority`) — $[0.0, 100.0]\%$
- `low`: `trapmf([0.0, 0.0, 15.0, 35.0])`
- `medium`: `trimf([25.0, 45.0, 65.0])`
- `high`: `trimf([55.0, 75.0, 85.0])`
- `critical`: `trapmf([75.0, 85.0, 100.0, 100.0])`

#### Allocated Water Ratio (`zone_allocation`) — $[0.0, 100.0]\%$
- `none`: `trapmf([0.0, 0.0, 5.0, 15.0])`
- `low`: `trimf([10.0, 25.0, 40.0])`
- `moderate`: `trimf([30.0, 50.0, 70.0])`
- `high`: `trimf([60.0, 75.0, 90.0])`
- `maximum`: `trapmf([80.0, 90.0, 100.0, 100.0])`

---

## 7. Engineering Rationale and Justifications

### 7.1 Why Triangular and Trapezoidal Membership Functions Were Selected
1. **Explainability for Viva Defense**: Piecewise linear functions have distinct corner vertices ($a, b, c, d$) that correspond directly to physical thresholds (e.g. permanent wilting point, RAW threshold, field capacity). Gaussian curves lack finite support, giving non-zero membership to physically impossible states.
2. **Computational Determinism**: Linear interpolation requires only 4 arithmetic operations per point, enabling real-time execution on microcontrollers (ESP32 / STM32) without exponential floating-point latency.
3. **Partition of Unity Overlap**: Designing linear slopes that intersect at $\mu \approx 0.5$ guarantees that the sum of memberships satisfies $\sum_i \mu_i(x) \approx 1.0$, preventing control deadbands.

### 7.2 Justification of ETc and Deficit Upper Bounds (15.0 mm/day)
During Phase 4 stress-scenario testing, Zone 3 (Tomato under Heatwave conditions) produced an hourly ETc peaking at $0.98\text{ mm/hr}$, which extrapolates to $12.56\text{ mm/day}$. Setting the upper bound of the universe at $15.0\text{ mm/day}$ provides a 20% engineering safety margin while preventing excessive compression of the low-to-moderate demand range.

---

## 8. Normalization and Safeguards

While the fuzzy inference layer normalizes universes linearly to $[0.0, 1.0]$ internally when required by optimization algorithms (such as PSO in Phase 11), **the physical models and interface boundaries strictly preserve physical units**:
- Clamping is automatically performed by `FuzzyUniverse.clamp(x)` to guarantee that numerical anomalies or sensor noise do not produce out-of-range indexing.
- `NaN` and `Inf` inputs are explicitly trapped and rejected with clear `ValueError` exceptions.

---

## 9. Validation Methodology

Every registered variable must pass the automated 11-point validation suite implemented in `fuzzy_engine.validation`:
1. Universe bounds: $x_{\min} < x_{\max}$.
2. Resolution: Grid points $\ge 100$.
3. Parameter monotonicity: $a \le b \le c$ or $a \le b \le c \le d$.
4. Finite parameters: No `NaN` or `Inf`.
5. Bounded range: $\mu(x) \in [0.0, 1.0]$ everywhere.
6. Non-zero support and core apex reaches 1.0.
7. Universe coverage: $\sum_i \mu_i(x) \ge 0.3$ across all grid points.
8. Adjacent set overlap: Non-empty intersection.
9. No dead zones: $\max_i \mu_i(x) > 0$.
10. Boundary saturation: $\mu_{\text{first}}(x_{\min}) = 1.0$, $\mu_{\text{last}}(x_{\max}) = 1.0$.
11. Numerical reproducibility: Identical results across repeated invocations.

---

## 10. How Phase 7 Will Use These Variables

In **Phase 7 (Soil Stress FIS)**:
1. `fuzzy_engine.universes.get_variables_by_fis("soil_stress_fis")` will supply `rsm`, `moisture_error`, and `soil_stress`.
2. A 25-rule Mamdani rule base ($5 \times 5$ grid) will be constructed mapping combinations of `rsm` and `moisture_error` to `soil_stress`.
3. The inference engine will compute min-implication and centroid defuzzification to yield an agricultural soil stress percentage.
