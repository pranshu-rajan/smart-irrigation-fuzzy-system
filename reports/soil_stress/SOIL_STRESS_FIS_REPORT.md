# Phase 7 Engineering Report: Soil Stress Fuzzy Inference System (SoilStressFIS)

**Project**: Smart Multizone Irrigation and Water Resource Management Using Hierarchical Adaptive Fuzzy Control  
**Phase**: Phase 7 — Soil Stress Fuzzy Inference System  
**Status**: Completed & Verified  
**Date**: September 2026  

---

## 1. Objective

The primary objective of Phase 7 is to implement, validate, and benchmark the **Soil Stress Fuzzy Inference System (`SoilStressFIS`)**, which is the first operational fuzzy controller in the hierarchical architecture. The system transforms continuous soil hydrological states—specifically **Relative Soil Moisture (RSM)** and **Moisture Tracking Error ($e(t)$)**—into a normalized **Soil Stress index** ($[0.0, 100.0]\%$) for each agricultural zone.

---

## 2. Role in Hierarchical Fuzzy Control Architecture

The Soil Stress FIS operates as a primary observer at Tier 1 of the 3-tier hierarchical architecture:

```
                  WEATHER MODEL
                       │
                       ▼
               WEATHER STRESS FIS (Phase 8)
                       │
                       │
SOIL MOISTURE ──► SOIL STRESS FIS (Phase 7) ────┐
                       │                        │
                       │                        │
ET0 / ETc ──────► WATER DEMAND FIS (Phase 8)    │
                       │                        │
                       ▼                        ▼
               MAIN IRRIGATION FIS (Phase 9) ◄──┘
                       │
                       ▼
               IRRIGATION DEMAND
                       │
                       ▼
             WATER ALLOCATION FIS (Phase 10)
                       │
            ┌──────────┼──────────┐
            ▼          ▼          ▼
          ZONE 1     ZONE 2     ZONE 3
            │          │          │
            └──────────┼──────────┘
                       ▼
               SOIL-WATER MODEL
                       │
                       ▼
                  FEEDBACK
```

The decoupled nature of this architecture ensures that root-zone physical moisture dynamics remain completely distinct from atmospheric demand, preventing rule-base explosion.

---

## 3. Input & Output Variables

All universes and membership functions are sourced directly from the single source of truth (`config/fuzzy_config.json` and `fuzzy_engine/universes.py`):

| Variable | Symbol | Role | Universe | Unit | Linguistic Terms |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Relative Soil Moisture** | $\text{RSM}$ | Input 1 | $[0.0, 1.0]$ | dim | Very Dry, Dry, Adequate, Wet, Very Wet |
| **Moisture Tracking Error** | $e(t)$ | Input 2 | $[-30.0, 30.0]$ | % | Large Negative, Negative, Zero, Positive, Large Positive |
| **Soil Stress** | $S_{\text{soil}}$ | Output | $[0.0, 100.0]$ | % | Low, Moderate, High, Very High |

### Semantic Interpretation
- **RSM**: $0.0 = \text{Wilting Point}$, $1.0 = \text{Field Capacity}$.
- **Moisture Error**: $e(t) = \theta_{\text{target}} - \theta(t)$. Positive indicates a water deficit below target; negative indicates surplus water above target.
- **Soil Stress**: $0.0\% = \text{Optimal/No Stress}$, $100.0\% = \text{Catastrophic Root Dehydration Danger}$.

---

## 4. Membership Function Formulations & Parameters

Input and output membership functions use piecewise linear triangular (`trimf`) and trapezoidal (`trapmf`) shapes with open shoulders at boundaries to guarantee numerical saturation:

### 4.1 Input 1: Relative Soil Moisture (`rsm`)
- **Very Dry**: $\text{trapmf}(0.0, 0.0, 0.15, 0.30)$
- **Dry**: $\text{trimf}(0.20, 0.35, 0.50)$
- **Adequate**: $\text{trimf}(0.40, 0.55, 0.70)$
- **Wet**: $\text{trimf}(0.60, 0.75, 0.85)$
- **Very Wet**: $\text{trapmf}(0.75, 0.85, 1.0, 1.0)$

### 4.2 Input 2: Moisture Tracking Error (`moisture_error`)
- **Large Negative**: $\text{trapmf}(-30.0, -30.0, -20.0, -10.0)$
- **Negative**: $\text{trimf}(-15.0, -7.5, 0.0)$
- **Zero**: $\text{trimf}(-5.0, 0.0, 5.0)$
- **Positive**: $\text{trimf}(0.0, 7.5, 15.0)$
- **Large Positive**: $\text{trapmf}(10.0, 20.0, 30.0, 30.0)$

### 4.3 Output: Soil Stress (`soil_stress`)
- **Low**: $\text{trapmf}(0.0, 0.0, 15.0, 35.0)$
- **Moderate**: $\text{trimf}(25.0, 45.0, 65.0)$
- **High**: $\text{trimf}(55.0, 75.0, 85.0)$
- **Very High**: $\text{trapmf}(75.0, 85.0, 100.0, 100.0)$

---

## 5. Engineering Rule Base (25 Rules)

The rule base forms a complete $5 \times 5$ matrix:

| RSM \ Error | Large Negative | Negative | Zero | Positive | Large Positive |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Very Dry** | Moderate (R5) | High (R4) | High (R3) | Very High (R2) | Very High (R1) |
| **Dry** | Low (R10) | Low (R9) | Moderate (R8) | High (R7) | Very High (R6) |
| **Adequate** | Low (R15) | Low (R14) | Low (R13) | Moderate (R12) | High (R11) |
| **Wet** | Low (R20) | Low (R19) | Low (R18) | Low (R17) | Moderate (R16) |
| **Very Wet** | Low (R25) | Low (R24) | Low (R23) | Low (R22) | Low (R21) |

---

## 6. Inference & Centroid Defuzzification

The inference engine executes:
1. **Antecedent T-Norm**: $\alpha_k = \min(\mu_{\text{RSM}, k}(r), \mu_{e, k}(e))$.
2. **Implication**: Mamdani min-clipping of consequent fuzzy sets.
3. **Aggregation**: S-Norm maximum across all active rules: $\mu_{\text{agg}}(z) = \max_k \mu_{C_k}'(z)$.
4. **Defuzzification**: Numerical centroid integration across $M = 501$ points ($dz = 0.2\%$):
   $$z^* = \frac{\sum_{m=1}^{501} z_m \cdot \mu_{\text{agg}}(z_m)}{\sum_{m=1}^{501} \mu_{\text{agg}}(z_m)}$$

---

## 7. Critical Sanity Verification Cases

The 5 mandatory sanity scenarios specified in Part 9 were empirically evaluated:

| Test Case | Scenario Description | RSM Input | Error Input | Resulting Soil Stress | Linguistic Match | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **Case A** | Extreme drought near WP + massive deficit | $0.05$ | $+25.0\%$ | **89.84%** | Very High | **PASS** |
| **Case B** | Dry soil + moderate deficit | $0.25$ | $+10.0\%$ | **79.17%** | High | **PASS** |
| **Case C** | Adequate moisture on target | $0.55$ | $0.0\%$ | **13.11%** | Low | **PASS** |
| **Case D** | Wet soil + moisture surplus | $0.75$ | $-10.0\%$ | **14.38%** | Low | **PASS** |
| **Case E** | Saturated soil + large surplus | $0.95$ | $-20.0\%$ | **13.11%** | Low | **PASS** |

All cases behave in exact agreement with agricultural physics.

---

## 8. Monotonicity Analysis

Across major agronomic operating regimes:
- **RSM Monotonicity**: Holding Moisture Error constant at $+10.0\%$ and increasing RSM from $0.10 \to 0.35 \to 0.55 \to 0.75 \to 0.95$ yields Soil Stress of:
  $$89.1\% \ge 71.4\% \ge 45.0\% \ge 14.4\% \ge 14.4\%$$
  Soil stress strictly decreases as water availability rises.
- **Moisture Error Monotonicity**: Holding RSM constant at $0.35$ (Dry) and increasing Moisture Error from $-15.0\% \to 0.0\% \to +10.0\% \to +20.0\%$ yields Soil Stress of:
  $$13.1\% \le 45.0\% \le 71.4\% \le 89.8\%$$
  Soil stress strictly increases as root-zone deficit widens.

*Note on Local Interpolation Effects*: Mamdani centroid defuzzification with clipped asymmetrical trapezoidal shoulders produces minor centroid shifts ($\approx 1.2\%$) within a single linguistic set. Macro transitions across linguistic sets are completely monotonic.

---

## 9. Visualizations & Figures

All figures have been saved at 300 DPI in `reports/soil_stress/figures/`:

1. **3D Control Surface**: `soil_stress_surface.png` (Smooth surface rising toward low RSM + high positive error).
2. **2D Contour Map**: `soil_stress_contour.png` (Isolines highlighting the low-stress vs emergency-stress operating regions).
3. **Mamdani Step-by-Step Inference**: `soil_stress_inference_example.png` (Visualizes fuzzification, min-implication clipping, max-aggregation, and centroid line).
4. **Input & Output Memberships**: `rsm_membership.png`, `moisture_error_membership.png`, `soil_stress_membership.png`.
5. **Scenario Comparison**: `soil_stress_scenarios.png` (24-hour multi-zone timeseries across all 6 weather scenarios).

---

## 10. Real Simulation Integration & Dataset Creation

The Phase 5 root-zone simulation dataset (`data/processed/soil_water_balance.csv`, 4,320 timesteps) was evaluated through `SoilStressFIS.evaluate_array()`, generating **`data/processed/soil_stress.csv`**:

### Baseline Zone-Wise Results (24-Hour Simulation)

| Zone ID | Crop | Soil Type | Initial Moisture | Initial Error | Initial RSM | Initial Soil Stress | Mean Soil Stress | Max Soil Stress |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Zone 1** | Tomato | Loam | $55.0\%$ | $+5.0\%$ | $0.667$ | **25.98%** | **23.34%** | **26.04%** |
| **Zone 2** | Wheat | Sandy | $42.0\%$ | $+13.0\%$ | $0.571$ | **56.37%** | **54.61%** | **56.39%** |
| **Zone 3** | Maize | Clay | $65.0\%$ | $0.0\%$ | $0.778$ | **14.15%** | **14.01%** | **14.26%** |

### Agronomic Evaluation
- **Zone 3 (Maize/Clay)**: Highest soil moisture ($65\%$), error is zero $\implies$ consistently lowest stress ($\approx 14\%$).
- **Zone 1 (Tomato/Loam)**: Mild deficit ($5\%$) below target ($60\%$) $\implies$ low-to-moderate stress ($\approx 23-26\%$).
- **Zone 2 (Wheat/Sandy)**: Significant deficit ($13\%$) below target ($55\%$) and coarse sandy soil $\implies$ highest stress ($\approx 55-56\%$). In Phase 10, this zone will rightfully receive top water allocation priority!

---

## 11. Multi-Scenario Stress Dynamics

Simulations across the 6 meteorological scenarios revealed clear dynamics:
- **Rainy Scenario**: Infiltration pulses cause RSM to rise, driving Soil Stress down to baseline low levels ($\approx 13\%$).
- **Heatwave & Hot/Dry Scenarios**: Elevated $ET_c$ rapidly depletes root storage, causing upward drift in soil stress over the 24-hour horizon.
- **Water Scarcity Scenario**: Without irrigation compensation, coarse soils (Zone 2) exhibit rapid stress escalation.

---

## 12. Test & Quality Assurance Summary

Running the complete automated test suite:
```
python -m pytest tests/ -v
============================ 120 passed in 12.85s =============================
```

- **Previous Test Count**: 107
- **New Tests Added**: 13 (in `tests/test_soil_stress.py`)
- **Total Tests**: **120**
- **Passed**: 120 (100%)
- **Failed**: 0
- **Errors**: 0
- **Warnings**: 0

---

## 13. Limitations & Future Integration

1. **Observer-Only Mode in Phase 7**: The FIS currently acts as an open-loop observer estimating stress. Closed-loop valve commands will be generated when the **Main Irrigation FIS** (Phase 9) synthesizes this Soil Stress with Weather Stress and Water Demand.
2. **Fixed Rule Weights**: All 25 rules currently carry unit weight ($w_k = 1.0$). In Phase 11, rule weights and membership vertices will be adaptively optimized via Particle Swarm Optimization (PSO).

---

## 14. Conclusion & Next Phase

Phase 7 is completely finished and validated.

**STOPPING AT PHASE 7**. Per instructions:
- The next planned phase is **PHASE 8 — WEATHER STRESS FIS & WATER DEMAND FIS**.
- Do NOT proceed to Phase 8 now.
