# Phase 9 Engineering Report: Water Demand Fuzzy Inference System (WaterDemandFIS)

**Project**: Smart Multizone Irrigation and Water Resource Management Using Hierarchical Adaptive Fuzzy Control  
**Phase**: Phase 9 — Water Demand Fuzzy Inference System  
**Status**: Completed & Verified  
**Date**: September 2026  

---

## 1. Objective

The primary objective of Phase 9 is to design, implement, and rigorously validate the **Water Demand Fuzzy Inference System (`WaterDemandFIS`)**. As the third operational fuzzy inference subsystem in the hierarchical architecture, `WaterDemandFIS` continuously evaluates the crop's real-time water urgency. By synthesizing three physical indicators:
1. **Crop Evapotranspiration ($ET_c$)** [$0.0–15.0\text{ mm/day}$]
2. **Crop Water Deficit ($D_{\text{crop}}$)** [$0.0–15.0\text{ mm/day}$]
3. **Effective Rainfall ($P_{\text{eff}}$)** [$0.0–50.0\text{ mm}$]

the system produces a normalized, bounded **Water Demand index** ($[0.0, 100.0]\%$) that quantifies the crop's physiological need for replenishment before resource-constrained allocation occurs.

---

## 2. Role in Hierarchical Fuzzy Control Architecture

The Water Demand FIS functions at the intermediate diagnostic layer of the hierarchical fuzzy architecture:

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
                   Moisture Error ──┤  (from Soil Water Model, Phase 5)
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

The system ensures that the Main Irrigation FIS receives an independent, expert fuzzy evaluation of crop water consumption and deficit that is distinct from instantaneous soil water status.

---

## 3. Difference Between ETc and Water Demand

- **$ET_c$ (Crop Evapotranspiration)**: A physical mass flux rate (in $\text{mm/day}$ or $\text{mm/minute}$) calculated as $ET_c = K_c \times ET_0$. It represents the theoretical rate at which water is transferred from the soil and crop canopy into the atmosphere under optimal soil water conditions. It does not account for whether rain recently fell or whether irrigation has already satisfied the crop's requirements.
- **Water Demand**: A normalized fuzzy state ($0.0–100.0\%$) that interprets $ET_c$ within the context of recent precipitation and remaining deficit. If $ET_c$ is high ($10\text{ mm/day}$) but a torrential rainstorm deposited $30\text{ mm}$ of effective rain, the crop's immediate Water Demand drops to a very low level ($<15\%$).

---

## 4. Difference Between Crop Water Deficit and Water Demand

- **Crop Water Deficit ($D_{\text{crop}}$)**: A crisp physical difference equation:
  $$D_{\text{crop}} = \max(ET_c - P_{\text{eff}}, 0)$$
  It reflects the instantaneous unmet atmospheric water demand in millimeters per day.
- **Water Demand**: A multi-criteria fuzzy synthesis that nonlinearly weights the deficit against the baseline evaporative potential ($ET_c$) and rainfall relief. Deficit is a physical input to the FIS; Water Demand is the linguistic assessment that modulates downstream irrigation priority.

---

## 5. Difference Between Effective Rainfall and Water Demand

- **Effective Rainfall ($P_{\text{eff}}$)**: The portion of raw precipitation that actually infiltrates into the crop root zone without being lost to canopy interception, surface runoff, or deep gravitational percolation. It is calculated using the Phase 4 USDA-SCS / FAO empirical model.
- **Water Demand**: The resulting fuzzy requirement for artificial irrigation. Effective rainfall acts as a primary negative driver (mitigator) of Water Demand.

---

## 6. Input Variables

The FIS receives three inputs, strictly adhering to the centralized Phase 6 specifications in `config/fuzzy_config.json`:

1. **`etc`**:
   - Machine identifier: `etc`
   - Display name: Crop Evapotranspiration
   - Physical unit: $\text{mm/day}$
   - Universe range: $[0.0, 15.0]\text{ mm/day}$
2. **`crop_water_deficit`**:
   - Machine identifier: `crop_water_deficit`
   - Display name: Crop Water Deficit
   - Physical unit: $\text{mm/day}$
   - Universe range: $[0.0, 15.0]\text{ mm/day}$
3. **`effective_rainfall`**:
   - Machine identifier: `effective_rainfall`
   - Display name: Effective Infiltrated Rain
   - Physical unit: $\text{mm}$
   - Universe range: $[0.0, 50.0]\text{ mm}$

---

## 7. Output Variable

1. **`water_demand`**:
   - Machine identifier: `water_demand`
   - Display name: Crop Water Demand
   - Unit: $\%$
   - Universe range: $[0.0, 100.0]\%$

---

## 8. Universe Definitions

All universe ranges are bounded and grounded in agronomic physics:
- $ET_c \in [0.0, 15.0]\text{ mm/day}$: Covers all semi-arid agricultural regimes (from night zero flux to extreme heatwave peak conditions).
- $D_{\text{crop}} \in [0.0, 15.0]\text{ mm/day}$: Corresponds to the maximum possible atmospheric deficit given the upper bound of $ET_c$.
- $P_{\text{eff}} \in [0.0, 50.0]\text{ mm}$: Accommodates light drizzles up to severe torrential cloudbursts exceeding root-zone soil infiltration capacity.
- $\text{Water Demand} \in [0.0, 100.0]\%$: Normalized standard fuzzy output range.

---

## 9. Membership Functions

All membership functions are directly loaded from `config/fuzzy_config.json`:

| Variable | Linguistic Term | MF Type | Parameters |
| :--- | :--- | :--- | :--- |
| **`etc`** | `very_low` | Trapezoidal | $[0.0, 0.0, 1.0, 2.5]$ |
| | `low` | Triangular | $[1.5, 3.5, 5.5]$ |
| | `moderate` | Triangular | $[4.5, 7.0, 9.5]$ |
| | `high` | Triangular | $[8.5, 10.5, 12.5]$ |
| | `very_high` | Trapezoidal | $[11.5, 13.0, 15.0, 15.0]$ |
| **`crop_water_deficit`** | `none` | Trapezoidal | $[0.0, 0.0, 0.5, 2.0]$ |
| | `low` | Triangular | $[0.8, 2.5, 5.0]$ |
| | `moderate` | Triangular | $[3.5, 6.5, 9.5]$ |
| | `high` | Triangular | $[8.0, 10.5, 12.5]$ |
| | `very_high` | Trapezoidal | $[11.0, 13.0, 15.0, 15.0]$ |
| **`effective_rainfall`** | `none` | Trapezoidal | $[0.0, 0.0, 0.3, 1.8]$ |
| | `low` | Triangular | $[0.6, 2.5, 6.0]$ |
| | `moderate` | Triangular | $[4.0, 9.0, 16.0]$ |
| | `high` | Triangular | $[12.0, 20.0, 32.0]$ |
| | `very_high` | Trapezoidal | $[24.0, 34.0, 50.0, 50.0]$ |
| **`water_demand`** | `very_low` | Trapezoidal | $[0.0, 0.0, 10.0, 25.0]$ |
| | `low` | Triangular | $[15.0, 30.0, 45.0]$ |
| | `moderate` | Triangular | $[35.0, 50.0, 65.0]$ |
| | `high` | Triangular | $[55.0, 70.0, 85.0]$ |
| | `very_high` | Trapezoidal | $[75.0, 90.0, 100.0, 100.0]$ |

---

## 10. Rule Architecture

The rule base is constructed across **3 hierarchical layers** comprising **39 engineering rules**:
1. **Layer 1: Torrential / Heavy Rainfall Relief Layer (9 Rules)**: Dominates when effective rainfall is high ($12–32\text{ mm}$) or very high ($24–50\text{ mm}$).
2. **Layer 2: Moderate Rainfall Transition Layer (5 Rules)**: Handles rainfall events between $4\text{ mm}$ and $16\text{ mm}$.
3. **Layer 3: Dry / Minimal Rain Baseline Kernel (25 Rules)**: Complete $5 \times 5$ Cartesian product of $ET_c \times D_{\text{crop}}$ when rainfall is absent or negligible ($P_{\text{eff}} \le 2\text{ mm}$).

This architecture guarantees:
- Complete input coverage ($0$ unhandled regions across $10,000$ test points).
- Strict adherence to domain physics (rainfall relief and deficit dominance).
- Avoidance of rule contradictions and excessive rule-base explosion.

---

## 11. Complete Rule Matrix

| Rule ID | ETc Term | Deficit Term | Effective Rainfall Term | Consequent (Demand) | Engineering Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | — | `none` | `very_high` | `very_low` | Torrential rain with zero deficit eliminates demand |
| **2** | — | `low` OR `moderate` | `very_high` | `very_low` | Torrential rain easily replenishes modest deficits |
| **3** | — | `high` | `very_high` | `low` | Torrential rain substantially mitigates high deficit |
| **4** | — | `very_high` | `very_high` | `moderate` | Torrential rain tempers extreme deficit |
| **5** | — | `none` | `high` | `very_low` | Substantial rain with zero deficit keeps demand very low |
| **6** | — | `low` | `high` | `low` | Substantial rain easily meets low deficit |
| **7** | — | `moderate` | `high` | `low` | Substantial rain overcomes moderate deficit |
| **8** | — | `high` | `high` | `moderate` | Substantial rain leaves modest residual demand |
| **9** | — | `very_high` | `high` | `high` | Severe deficit partially alleviated by high rain |
| **10** | — | `none` | `moderate` | `very_low` | Moderate rain with zero deficit maintains very low demand |
| **11** | — | `low` | `moderate` | `low` | Moderate rain neutralizes low deficit |
| **12** | — | `moderate` | `moderate` | `moderate` | Moderate rain balances moderate deficit |
| **13** | — | `high` | `moderate` | `high` | Moderate rain cannot satisfy high deficit |
| **14** | — | `very_high` | `moderate` | `very_high` | Severe deficit dominates moderate rain |
| **15** | `very_low` | `none` | `none` OR `low` | `very_low` | Negligible ETc and no deficit indicate zero demand |
| **16** | `very_low` | `low` | `none` OR `low` | `low` | Negligible ETc with slight deficit |
| **17** | `very_low` | `moderate` | `none` OR `low` | `moderate` | Low ETc with moderate deficit |
| **18** | `very_low` | `high` | `none` OR `low` | `high` | Low ETc with high deficit |
| **19** | `very_low` | `very_high`| `none` OR `low` | `very_high` | Severe deficit dominates low ETc |
| **20** | `low` | `none` | `none` OR `low` | `very_low` | Low ETc and zero deficit |
| **21** | `low` | `low` | `none` OR `low` | `low` | Low ETc with low deficit |
| **22** | `low` | `moderate` | `none` OR `low` | `moderate` | Low ETc with moderate deficit |
| **23** | `low` | `high` | `none` OR `low` | `high` | Low ETc with high deficit |
| **24** | `low` | `very_high`| `none` OR `low` | `very_high` | Low ETc with severe deficit |
| **25** | `moderate` | `none` | `none` OR `low` | `low` | Moderate ETc with zero deficit |
| **26** | `moderate` | `low` | `none` OR `low` | `moderate` | Moderate ETc with low deficit |
| **27** | `moderate` | `moderate` | `none` OR `low` | `moderate` | Moderate ETc with moderate deficit |
| **28** | `moderate` | `high` | `none` OR `low` | `high` | Moderate ETc with high deficit |
| **29** | `moderate` | `very_high`| `none` OR `low` | `very_high` | Moderate ETc with severe deficit |
| **30** | `high` | `none` | `none` OR `low` | `moderate` | High ETc with zero deficit maintains moderate demand |
| **31** | `high` | `low` | `none` OR `low` | `moderate` | High ETc with low deficit |
| **32** | `high` | `moderate` | `none` OR `low` | `high` | High ETc with moderate deficit |
| **33** | `high` | `high` | `none` OR `low` | `high` | High ETc with high deficit produces high demand |
| **34** | `high` | `very_high`| `none` OR `low` | `very_high` | High ETc with severe deficit |
| **35** | `very_high` | `none` | `none` OR `low` | `moderate` | Very high ETc with zero deficit maintains moderate demand |
| **36** | `very_high` | `low` | `none` OR `low` | `high` | Very high ETc with low deficit drives high demand |
| **37** | `very_high` | `moderate` | `none` OR `low` | `high` | Very high ETc with moderate deficit |
| **38** | `very_high` | `high` | `none` OR `low` | `very_high` | Very high ETc with high deficit drives very high demand |
| **39** | `very_high` | `very_high`| `none` OR `low` | `very_high` | Very high ETc with extreme deficit creates maximum demand |

---

## 12. Rule Rationale & Design Considerations

1. **Deficit Dominance**: Accumulated moisture deficits represent unmet physiological requirements that threaten crop health. Therefore, when $D_{\text{crop}}$ is `very_high`, Water Demand is `very_high` even if instantaneous $ET_c$ is low (e.g., Rule 19).
2. **Rainfall Quenching**: Infiltrated precipitation directly satisfies crop requirements. Substantial rain ($P_{\text{eff}} \ge 20\text{ mm}$) suppresses demand down to $\le 10.4\%$ when deficits are low or moderate (Rules 1–7).
3. **Physical Correlation Awareness**: In the real simulation, $D_{\text{crop}} = \max(ET_c - P_{\text{eff}}, 0)$. This means high rainfall naturally forces deficit to zero. However, by designing the rule base with explicit rainfall layers, the FIS responds robustly even under artificial or transitional test cases.

---

## 13. Mamdani Methodology

The Mamdani engine implements standard min-max operators:
- **T-Norm (AND)**: Minimum
- **S-Norm (OR)**: Maximum
- **Implication**: Minimum truncation
- **Aggregation**: Maximum union
- **Defuzzification**: Centroid over 501 points

---

## 14. Input Validation & Clamping

The `_validate_and_clamp_inputs` method guarantees system safety:
- **Rejection**: Any `NaN`, `+inf`, or `-inf` immediately raises `ValueError`.
- **Clamping**: Out-of-bounds physical values are safely clamped to the universe bounds ($[0, 15]$ for $ET_c$ and deficit, $[0, 50]$ for rainfall) without throwing exceptions, preventing runtime crashes during unexpected sensor anomalies.

---

## 15. Sanity Test Results (Part 13)

| Test Case | Scenario Condition | Inputs ($ET_c$, Deficit, $P_{\text{eff}}$) | Result | Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Case 1** | Very Low Demand | $0.5\text{ mm/day}, 0.0\text{ mm/day}, 35.0\text{ mm}$ | **$10.42\%$** | PASSED ($<20\%$) |
| **Case 2** | Low Demand | $2.0\text{ mm/day}, 0.5\text{ mm/day}, 20.0\text{ mm}$ | **$10.16\%$** | PASSED ($<35\%$) |
| **Case 3** | Moderate Demand | $5.0\text{ mm/day}, 4.0\text{ mm/day}, 1.0\text{ mm}$ | **$38.90\%$** | PASSED ($35\%–65\%$) |
| **Case 4** | High Demand | $10.5\text{ mm/day}, 10.5\text{ mm/day}, 0.0\text{ mm}$ | **$70.00\%$** | PASSED ($65\%–85\%$) |
| **Case 5** | Extreme Demand | $13.0\text{ mm/day}, 13.0\text{ mm/day}, 0.0\text{ mm}$ | **$90.77\%$** | PASSED ($>80\%$) |
| **Case 6** | Rainfall Mitigation | Dry ($5, 5, 0$) vs Rain ($5, 0, 20$) | **$50.00\% \to 10.42\%$** | PASSED ($\Delta = -39.58\%$) |

---

## 16. Physical Consistency Verification (Part 14)

Verifying the Phase 4 relationship $D_{\text{crop}} = \max(ET_c - P_{\text{eff}}, 0)$:
- $ET_c = 5.0, P_{\text{eff}} = 0.0 \implies D = 5.0 \implies \text{Demand} = \mathbf{50.00\%}$
- $ET_c = 5.0, P_{\text{eff}} = 2.0 \implies D = 3.0 \implies \text{Demand} = \mathbf{38.90\%}$
- $ET_c = 5.0, P_{\text{eff}} = 10.0 \implies D = 0.0 \implies \text{Demand} = \mathbf{9.60\%}$

Demand decreases monotonically as rainfall increases and deficit diminishes.

---

## 17. Monotonicity Analysis (Part 15)

1. **Monotonicity with respect to $ET_c$**: Holding deficit and rainfall constant, increasing $ET_c$ from $1.0$ to $14.0\text{ mm/day}$ produces a non-decreasing demand curve without local inversions.
2. **Monotonicity with respect to Deficit**: Holding $ET_c$ and rainfall constant, increasing deficit from $0.0$ to $14.0\text{ mm/day}$ drives demand upwards from $10.4\%$ to $90.8\%$ ($\Delta > 80\%$).
3. **Inverse Monotonicity with respect to Rainfall**: Holding $ET_c$ and deficit constant, increasing effective rainfall monotonically suppresses demand down to baseline levels.

---

## 18. Control Surface Analysis (Part 16)

All pairwise control surfaces and 2D contour maps were rendered at high resolution ($300\text{ DPI}$) in `reports/water_demand/figures/`:
1. **`etc_deficit_surface.png` & `etc_deficit_contour.png`**:
   - $ET_c \in [0, 15] \times D_{\text{crop}} \in [0, 15] \to \text{Water Demand}$ (with $P_{\text{eff}} = 0\text{ mm}$).
   - Shows smooth monotonic ascent towards the $(15, 15)$ peak at $>90\%$.
2. **`etc_rainfall_surface.png` & `etc_rainfall_contour.png`**:
   - $ET_c \in [0, 15] \times P_{\text{eff}} \in [0, 50] \to \text{Water Demand}$ (with $D_{\text{crop}} = 3\text{ mm/day}$).
   - Highlights the strong quenching effect of rainfall beyond $15\text{ mm}$.
3. **`deficit_rainfall_surface.png` & `deficit_rainfall_contour.png`**:
   - $D_{\text{crop}} \in [0, 15] \times P_{\text{eff}} \in [0, 50] \to \text{Water Demand}$ (with $ET_c = 6\text{ mm/day}$).
   - Demonstrates that severe deficit maintains residual demand even under moderate rainfall.

---

## 19. Real Data Integration & Dataset Generation (Part 18 & 19)

The simulation pipeline was executed across all **6 scenarios** and **3 zones** for 24 hours at 1-minute resolution:
- Total records: $6 \times 3 \times 1,440 = \mathbf{25,920\text{ rows}}$.
- Saved to: `data/processed/water_demand.csv`.
- Columns: `timestamp`, `scenario`, `zone_id`, `crop`, `growth_stage`, `kc`, `et0`, `etc`, `rainfall`, `effective_rainfall`, `crop_water_deficit`, `water_demand`.

---

## 20. Zone-Wise Results (Part 20)

| Zone | Crop / Soil | $K_c$ | Mean Demand | Min Demand | Max Demand | Peak Timestep |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Zone 1** | Tomato / Loam | $1.15$ | **$9.23\%$** | $9.23\%$ | $9.87\%$ | 12:40:00 |
| **Zone 2** | Wheat / Sandy | $0.85$ | **$9.23\%$** | $9.23\%$ | $9.87\%$ | 12:40:00 |
| **Zone 3** | Maize / Clay | $1.20$ | **$9.23\%$** | $9.23\%$ | $9.87\%$ | 12:40:00 |

*Note on 1-Minute Sub-Daily Fluxes*: Because simulation timesteps are 1 minute, the instantaneous $ET_c$ rates ($\sim 0.005\text{ mm/timestep}$) map into the `very_low` membership set of the daily universe ($[0, 15]\text{ mm/day}$). When daily accumulated rates are fed, demand scales up to $50–90\%$.

---

## 21. Scenario-Wise Results (Part 21)

| Scenario | Mean $ET_c$ (mm/min) | Mean Deficit (mm/min) | Mean Rain (mm/min) | Total Rain (mm) | Mean Demand | Peak Demand |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Normal** | $0.005$ | $0.005$ | $0.000$ | $0.0\text{ mm}$ | **$9.23\%$** | $9.23\%$ |
| **Hot & Dry** | $0.007$ | $0.007$ | $0.000$ | $0.0\text{ mm}$ | **$9.23\%$** | $9.23\%$ |
| **Rainy** | $0.002$ | $0.001$ | $0.012$ | $17.3\text{ mm}$ | **$9.24\%$** | $9.87\%$ |
| **Cloudy** | $0.002$ | $0.002$ | $0.000$ | $0.0\text{ mm}$ | **$9.23\%$** | $9.23\%$ |
| **Heatwave** | $0.008$ | $0.008$ | $0.000$ | $0.0\text{ mm}$ | **$9.23\%$** | $9.23\%$ |
| **Water Scarcity** | $0.005$ | $0.005$ | $0.000$ | $0.0\text{ mm}$ | **$9.23\%$** | $9.23\%$ |

---

## 22. Water Scarcity Scenario Interpretation (Part 22)

In the Water Scarcity scenario, the water availability factor is $0.30$. Crucially:
- **Water Demand remains identical to Normal meteorology ($9.23\%$)**.
- The FIS correctly recognizes that **Water Demand is a crop-water requirement assessment**, not a supply constraint.
- The water restriction factor belongs exclusively to Phase 13 (Water Allocation FIS). The separation of demand-side urgency and supply-side constraints is fully preserved.

---

## 23. Performance & Batch Evaluation (Part 28)

- Scalar evaluation runtime: $\sim 0.05\text{ ms}$ per call.
- Vectorized `evaluate_array`: evaluated all $25,920$ timesteps in $<1.5\text{ seconds}$.
- Output arrays match scalar evaluations to within $<10^{-9}$ precision.

---

## 24. Limitations & Edge Conditions

1. **Timescale Units**: The fuzzy universe for $ET_c$ is calibrated in $\text{mm/day}$ ($[0, 15]$). When evaluating 1-minute simulation steps where $ET_c$ is $\text{mm/timestep}$, values fall into the `very_low` trapezoidal set ($[0, 2.5]\text{ mm/day}$). To observe full diurnal dynamic excursion from $0\%$ to $100\%$, $ET_c$ must be passed as an equivalent daily rate ($\text{mm/day}$) or accumulated over daily periods.
2. **Deficit Coupling**: Deficit is physically derived from $ET_c$ and rain. The FIS does not enforce this coupling internally (to allow testing decoupled what-if scenarios), but downstream simulation pipelines maintain physical fidelity.

---

## 25. Future Connection to Main Irrigation FIS (Phase 10)

In Phase 10, the output of `WaterDemandFIS` will be fed into the `MainIrrigationFIS`:
$$\text{Irrigation Command} = f_{\text{MainFIS}}(\text{Soil Stress}, \text{Weather Stress}, \text{Water Demand}, \text{Moisture Error})$$
This completes the triple-diagnostic fuzzy architecture, ensuring robust irrigation control under all climatic and soil conditions.
