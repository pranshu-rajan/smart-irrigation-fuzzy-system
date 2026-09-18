# Phase 10 Engineering Report: Main Irrigation Fuzzy Inference System (MainIrrigationFIS)

**Project**: Smart Multizone Irrigation and Water Resource Management Using Hierarchical Adaptive Fuzzy Control  
**Phase**: Phase 10 — Main Irrigation Fuzzy Inference System  
**Status**: Completed & Verified  
**Date**: September 2026  

---

## 1. Objective

The primary objective of Phase 10 is to implement and rigorously validate the **Main Irrigation Fuzzy Inference System (`MainIrrigationFIS`)**, located in `fuzzy_engine/irrigation.py` (with compatibility alias in `fuzzy_engine/main_irrigation.py`). As the core supervisory control FIS of the hierarchical architecture, `MainIrrigationFIS` continuously synthesizes:
1. **Soil Stress** ($[0.0, 100.0]\%$) from Phase 7 (`SoilStressFIS`)
2. **Weather Stress** ($[0.0, 100.0]\%$) from Phase 8 (`WeatherStressFIS`)
3. **Water Demand** ($[0.0, 100.0]\%$) from Phase 9 (`WaterDemandFIS`)
4. **Moisture Tracking Error ($e(t)$)** ($[-30.0, 30.0]\%$) from Phase 5 (`Soil Water Balance Model`)

The controller produces a normalized **Irrigation Command** ($[0.0, 100.0]\%$) that governs the supervisory watering intensity for each agricultural zone.

---

## 2. Role in Hierarchical Fuzzy Control Architecture

The Main Irrigation FIS is the tier-2 controller in the project hierarchy:

```
                    WEATHER MODEL
                         │
                         ├──────────────► WEATHER STRESS FIS (Phase 8)
                         │                         │
                         ▼                         │
                       ET0                         │
                         │                         │
                         ▼                         │
                       ETc                         │
                         │                         │
             ┌───────────┴────────────┐            │
             ▼                        ▼            │
   Effective Rainfall       Crop Water Deficit      │
             │                        │              │
             └────────────┬───────────┘              │
                          ▼                          │
                   WATER DEMAND FIS (Phase 9)       │
                          │                          │
                          └──────────┬───────────────┘
                                     ▼
                             MAIN IRRIGATION FIS (Phase 10)
                                     │
                   Soil Stress ─────┤  (from SoilStressFIS, Phase 7)
                   Weather Stress ──┤  (from WeatherStressFIS, Phase 8)
                   Water Demand ────┤  (from WaterDemandFIS, Phase 9)
                   Moisture Error ──┤  (from Dynamic Soil Water Model, Phase 5)
                                     ▼
                              IRRIGATION COMMAND
                                     │
                                     ▼
                             WATER ALLOCATION (Phase 13)
                                     │
                                     ▼
                               ZONE SYSTEM
                                     │
                                     ▼
                              SOIL-WATER MODEL
                                     │
                                     └──► FEEDBACK
```

---

## 3. Fundamental Conceptual Distinctions

To maintain absolute scientific and engineering clarity, the following distinctions are rigorously preserved:
1. **Soil Stress vs. Weather Stress vs. Water Demand**: Soil stress evaluates root-zone depletion; weather stress evaluates atmospheric evaporative tension; water demand evaluates canopy consumption after rainfall mitigation.
2. **Moisture Error**: The physical closed-loop tracking signal $e(t) = \text{SM}_{\text{target}} - \text{SM}(t)$. When $e(t) < 0$, soil moisture is above target; when $e(t) > 0$, moisture is depleted below target.
3. **Irrigation Command**: A normalized supervisory control index ($[0.0, 100.0]\%$), NOT a literal volume (liters), flow rate (L/min), or depth (mm). Actuator conversion takes place downstream.
4. **Available Water**: A supply constraint belonging exclusively to Phase 13 (Water Allocation FIS). It is NOT an input to Main Irrigation FIS.

---

## 4. Input Variables & Membership Functions

All inputs and membership functions are dynamically loaded from `config/fuzzy_config.json`:

| Variable | Universe | Linguistic Term | MF Type | Parameters |
| :--- | :--- | :--- | :--- | :--- |
| **`soil_stress`** | $[0, 100]\%$ | `low` | Trapezoidal | $[0.0, 0.0, 15.0, 35.0]$ |
| | | `moderate` | Triangular | $[25.0, 45.0, 65.0]$ |
| | | `high` | Triangular | $[55.0, 75.0, 85.0]$ |
| | | `very_high` | Trapezoidal | $[75.0, 85.0, 100.0, 100.0]$ |
| **`weather_stress`** | $[0, 100]\%$ | `low` | Trapezoidal | $[0.0, 0.0, 15.0, 35.0]$ |
| | | `moderate` | Triangular | $[25.0, 45.0, 65.0]$ |
| | | `high` | Triangular | $[55.0, 75.0, 85.0]$ |
| | | `very_high` | Trapezoidal | $[75.0, 85.0, 100.0, 100.0]$ |
| **`water_demand`** | $[0, 100]\%$ | `very_low` | Trapezoidal | $[0.0, 0.0, 10.0, 25.0]$ |
| | | `low` | Triangular | $[15.0, 30.0, 45.0]$ |
| | | `moderate` | Triangular | $[35.0, 50.0, 65.0]$ |
| | | `high` | Triangular | $[55.0, 70.0, 85.0]$ |
| | | `very_high` | Trapezoidal | $[75.0, 90.0, 100.0, 100.0]$ |
| **`moisture_error`** | $[-30, 30]\%$ | `large_negative`| Trapezoidal | $[-30.0, -30.0, -20.0, -10.0]$|
| | | `negative` | Triangular | $[-15.0, -7.5, 0.0]$ |
| | | `zero` | Triangular | $[-5.0, 0.0, 5.0]$ |
| | | `positive` | Triangular | $[0.0, 7.5, 15.0]$ |
| | | `large_positive`| Trapezoidal | $[10.0, 20.0, 30.0, 30.0]$ |

---

## 5. Output Variable

- **`irrigation_command`**: Universe $[0.0, 100.0]\%$
  - `off`: Trapezoidal $[0.0, 0.0, 5.0, 15.0]$
  - `low`: Triangular $[10.0, 25.0, 40.0]$
  - `moderate`: Triangular $[30.0, 50.0, 70.0]$
  - `high`: Triangular $[60.0, 75.0, 90.0]$
  - `maximum`: Trapezoidal $[80.0, 90.0, 100.0, 100.0]$

---

## 6. Complete 32-Rule Engineering Base

| Rule ID | Soil Stress | Weather Stress | Water Demand | Moisture Error | Consequent (Command) | Engineering Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | — | — | — | `large_negative` | `off` | Deeply oversaturated soil strictly shuts off irrigation |
| **2** | `low`, `moderate` | — | — | `negative` | `off` | Negative error with mild soil stress requires no irrigation |
| **3** | `high`, `very_high` | — | `very_low`–`moderate` | `negative` | `off` | Negative error with modest demand overrides higher stress |
| **4** | `high`, `very_high` | — | `high`, `very_high` | `negative` | `low` | Elevated stress and demand with mild negative error permits minimal pulse |
| **5** | `low` | — | `very_low` | `zero` | `off` | At target moisture with low soil stress and low demand |
| **6** | `low` | — | `low`, `moderate` | `zero` | `low` | At target with low/moderate demand maintains low replacement |
| **7** | `low` | — | `high`, `very_high` | `zero` | `moderate` | At target with high demand requires moderate replacement |
| **8** | `moderate` | — | `very_low`, `low` | `zero` | `low` | At target with moderate soil stress and low demand |
| **9** | `moderate` | — | `moderate` | `zero` | `moderate` | At target with moderate stress and moderate demand |
| **10** | `moderate` | — | `high`, `very_high` | `zero` | `high` | At target with moderate stress and high demand |
| **11** | `high` | — | `very_low`, `low` | `zero` | `moderate` | At target with high soil stress requires moderate intervention |
| **12** | `high` | — | `moderate`, `high` | `zero` | `high` | At target with high stress and high demand |
| **13** | `high` | — | `very_high` | `zero` | `maximum` | At target with high stress and very high demand |
| **14** | `very_high` | — | `very_low`, `low` | `zero` | `high` | At target with very high stress requires strong replenishment |
| **15** | `very_high` | — | `moderate`–`very_high` | `zero` | `maximum` | At target with severe stress and active demand |
| **16** | `low` | — | `very_low`, `low` | `positive` | `low` | Mild depletion with low stress requires low irrigation |
| **17** | `low` | — | `moderate` | `positive` | `moderate` | Mild depletion with moderate demand |
| **18** | `low` | — | `high`, `very_high` | `positive` | `high` | Mild depletion with high demand |
| **19** | `moderate` | — | `very_low`, `low` | `positive` | `moderate` | Positive error with moderate stress |
| **20** | `moderate` | — | `moderate` | `positive` | `moderate` | Balanced deficit with moderate demand |
| **21** | `moderate` | — | `high`, `very_high` | `positive` | `high` | Balanced deficit with high demand |
| **22** | `high` | — | `very_low`, `low` | `positive` | `high` | High soil stress with positive error |
| **23** | `high` | — | `moderate`, `high` | `positive` | `high` | High stress and positive error with active demand |
| **24** | `high` | — | `very_high` | `positive` | `maximum` | High stress and high demand with positive error |
| **25** | `very_high` | — | — | `positive` | `maximum` | Severe stress with positive error requires maximum irrigation |
| **26** | `low` | — | — | `large_positive` | `moderate` | Large deficit even if sensor stress is low |
| **27** | `moderate` | — | — | `large_positive` | `high` | Large deficit with moderate stress |
| **28** | `high`, `very_high`| — | — | `large_positive` | `maximum` | Severe depletion with high stress commands maximum irrigation |
| **29** | `moderate`–`very_high`| `very_high` | — | `positive`, `large_positive` | `maximum` | Heatwave forcing during soil deficit drives maximum irrigation |
| **30** | `high`, `very_high`| `very_high` | — | `zero` | `maximum` | Extreme climate stress with elevated root stress at target moisture |
| **31** | — | `high` | `high`, `very_high` | `positive`, `large_positive` | `high` | High atmospheric stress amplifies irrigation during moisture deficit |
| **32** | `low` | `low` | `very_low` | — | `off` | Cool calm overcast conditions with hydrated soil eliminates irrigation |

---

## 7. Inference Engine & Defuzzification

- **Mamdani Min-Max Inference**:
  $$\mu_{\text{agg}}(z) = \max_{i=1}^{32} \left[ \min(\beta_i, \mu_{C_i}(z)) \right]$$
- **Centroid Defuzzification**:
  $$z^* = \frac{\sum_{j=1}^{501} z_j \, \mu_{\text{agg}}(z_j)}{\sum_{j=1}^{501} \mu_{\text{agg}}(z_j)}$$
  Executed over a uniform 501-point grid on $[0.0, 100.0]\%$.

---

## 8. Physical Sanity & Safety Matrix (Section 11)

All 14 automated tests in `tests/test_main_irrigation.py` passed:

| Test ID | Condition | Inputs ($SS, WS, WD, e(t)$) | Result | Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Test 1** | All low stress + negative error | $10\%, 10\%, 10\%, -15\%$ | **$5.36\%$** | PASSED (Strict OFF $< 15\%$) |
| **Test 2** | Low stress + zero error + low demand | $15\%, 20\%, 25\%, 0\%$ | **$25.00\%$** | PASSED (Low replacement $10–35\%$) |
| **Test 3** | Moderate stress + mod demand + zero error | $45\%, 45\%, 45\%, 0\%$ | **$50.00\%$** | PASSED (Moderate regulation $35–65\%$) |
| **Test 4** | High stress + positive error | $75\%, 50\%, 50\%, +8\%$ | **$75.00\%$** | PASSED (High replenishment $65–85\%$) |
| **Test 5** | Extreme stress + demand + large pos error | $90\%, 80\%, 85\%, +20\%$ | **$88.46\%$** | PASSED (Maximum emergency $> 80\%$) |
| **Test 6** | High weather stress + negative error | $15\%, 85\%, 20\%, -15\%$ | **$5.36\%$** | PASSED (Safety priority $< 25\%$) |
| **Test 7** | High weather + high soil stress + pos error | $85\%, 80\%, 70\%, +10\%$ | **$88.46\%$** | PASSED (Strong response $> 75\%$) |
| **Test 8** | High demand + soil above target | $30\%, 40\%, 85\%, -15\%$ vs $+10\%$ | **$5.36\%$ vs $75.0\%$** | PASSED ($\Delta = -69.64\%$) |
| **Test 9** | Low demand + positive moisture error | $30\%, 20\%, 15\%, +15\%$ | **$71.88\%$** | PASSED (Deficit driven $> 40\%$) |
| **Test 10** | Rain-reduced demand + soil above target | $10\%, 10\%, 9.2\%, -10\%$ | **$5.36\%$** | PASSED (Low/OFF $< 15\%$) |
| **Test 11** | Boundary inputs ($0$, mid, max) | Min: $5.36\%$, Mid: $50.00\%$, Max: $91.56\%$ | PASSED | Bounded within $[0, 100]\%$ |
| **Test 12–14**| NaN, +inf, -inf inputs | Rejection with `ValueError` | PASSED | Strict safety validation |

---

## 9. Monotonicity Analysis (Section 10)

1. **Soil Stress ($\uparrow$)**: Command monotonically increases from $39.6\%$ to $91.6\%$ ($\Delta = +52.0\%$).
2. **Moisture Error ($e(t)$ from $-25\%$ to $+25\%$)**: Command rises monotonically from $5.36\%$ (OFF) to $75.0\%$ (HIGH).
3. **Water Demand ($\uparrow$)**: Command rises monotonically from $50.0\%$ to $75.0\%$.
4. **Weather Stress ($\uparrow$)**: Command remains stable and scales up to $70.9\%$ under high climatic forcing.

---

## 10. Control Surface & Visualization Analysis

All 10 control surface and contour figures were generated at 300 DPI in `reports/main_irrigation/figures/`:
1. `soil_stress_vs_moisture_error_surface.png` & `contour.png`: Demonstrates sharp transition from OFF ($<10\%$) when error is negative to HIGH ($>75\%$) when error is positive.
2. `water_demand_vs_moisture_error_surface.png` & `contour.png`: Shows that positive moisture error amplifies irrigation, while negative error suppresses irrigation even under high water demand.
3. `weather_stress_vs_moisture_error_surface.png` & `contour.png`: Confirms that high weather stress cannot force watering when soil is already wet ($e(t) < 0$).
4. `soil_stress_vs_water_demand_surface.png` & `contour.png`: Displays synergistic coupling between soil stress and canopy water demand.
5. `weather_stress_vs_soil_stress_surface.png` & `contour.png`: Shows climate modulation elevating baseline root-zone stress response.

---

## 11. Real Multizone Integration & 25,920-Record Dataset

Simulated all 6 scenarios $\times$ 3 zones $\times$ 1,440 timesteps:
- Total rows: **25,920**.
- File: `data/processed/main_irrigation.csv`.
- Full simulation runtime: **33.79 seconds**.
- Scalar evaluation speed: **0.43 ms / evaluation**.

### Zone-Wise Controller Behavior
- **Zone 1 (Tomato / Loam)**: Mean Command = **$33.18\%$** (Min: $15.37\%$, Max: $65.53\%$). Balanced moderate irrigation matching loam soil retention.
- **Zone 2 (Wheat / Sandy)**: Mean Command = **$64.46\%$** (Min: $53.91$, Max: $73.29\%$). High persistent irrigation required due to sandy soil rapid drainage.
- **Zone 3 (Maize / Clay)**: Mean Command = **$7.36\%$** (Min: $5.36\%$, Max: $12.53\%$). Low/OFF command because heavy clay holds soil moisture near target.

### Scenario-Wise Controller Behavior
- **Normal**: Mean = $35.29\%$ (balanced regulation).
- **Hot & Dry**: Mean = $38.89\%$ (elevated transpirational demand).
- **Rainy**: Mean = $27.69\%$ (natural rain infiltration suppresses command).
- **Cloudy**: Mean = $32.30\%$ (reduced solar radiation lowers demand).
- **Heatwave**: Mean = $40.11\%$ (peak climatic evaporative tension).
- **Water Scarcity**: Mean = $35.71\%$. Demand-side controller command remains identical to Normal meteorology; supply restrictions are preserved for Phase 13.

---

## 12. Limitations & Boundary Conditions

1. **Normalized Signal**: Irrigation Command is a unitless supervisory signal $[0.0, 100.0]\%$, not volumetric flow.
2. **Open-Loop Evaluation**: In Phase 10, the command does not yet close the feedback loop back into the soil model; closed-loop simulation begins in Phase 11.
3. **No Supply Filtering**: Available water constraints are excluded and deferred to Phase 13.
4. **No Optimization / ML**: Fuzzy logic operates transparently with zero reliance on neural networks, black-box heuristics, or external APIs.
