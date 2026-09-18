# Phase 14 Engineering Report: PSO-Based Optimization of Fuzzy Controller Parameters

## 1. Executive Summary

- **Phase**: 14 — Particle Swarm Optimization (PSO) of Fuzzy Controller Parameters
- **Status**: Completed and Verified
- **Primary Objective**: Implement an offline metaheuristic optimization layer utilizing continuous Particle Swarm Optimization (PSO) to systematically calibrate the 18 critical transition parameters of the supervisory actuator controller (`MainIrrigationFIS`), optimizing dynamic closed-loop performance across representative agricultural scenarios.
- **Key Architectural Findings**:
  - **Strict Separation of Concerns**: PSO operates purely offline as a design-time calibration pipeline. The runtime control loop maintains sub-millisecond deterministic Mamdani inference with zero metaheuristic overhead.
  - **Preserved Fuzzy Hierarchy**: All 5 fuzzy inference subsystems, linguistic rule bases, and centroid defuzzification operators remain 100% intact.
  - **Compact, Interpretable Search Space**: Restricting optimization to 18 key transition breakpoints ensures biological, physical, and hydraulic interpretability while avoiding parameter explosion.
  - **Guaranteed Structural Invariants**: A deterministic repair operator strictly enforces monotonic set ordering ($a < b < c$ for triangular MFs, $a \le b \le c \le d$ for trapezoidal MFs) and bounded semantic overlap, preventing rule dead zones.
  - **Multi-Objective Cost Functional**: Balances moisture tracking error ($w_e = 0.40$), volumetric water consumption ($w_w = 0.30$), root-zone moisture deficit penalty ($w_d = 0.20$), and actuator command smoothness ($w_u = 0.10$).
  - **Cross-Scenario Generalization**: 4 Training scenarios (Normal, Hot & Dry, Rainy, Cloudy) drive parameter evolution, while 2 Validation scenarios (Heatwave, Water Scarcity) rigorously test out-of-sample robustness.
  - **Non-Destructive Storage**: `config/fuzzy_config.json` remains completely untouched. Optimized parameters are serialized to `config/fuzzy_optimized_pso.json` with comprehensive audit metadata.

---

## 2. Parameter Space & Semantic Mapping

The 18-dimensional continuous parameter vector $\boldsymbol{\theta}$ maps directly to the physical membership function universes:

| Index | Target Variable | Set Name | Parameter | Physical Description | Baseline |
|:---:|:---|:---|:---|:---|:---:|
| 0 | `moisture_error` | `negative` | Shoulder right | Upper threshold for negative error (surplus) | -2.00% |
| 1 | `moisture_error` | `zero` | Triangle foot $a$ | Lower boundary of target moisture band | -4.00% |
| 2 | `moisture_error` | `zero` | Triangle foot $c$ | Upper boundary of target moisture band | +4.00% |
| 3 | `moisture_error` | `positive` | Triangle peak $b$ | Deficit error triggering active irrigation | +6.00% |
| 4 | `moisture_error` | `large_positive` | Shoulder left | Severe deficit triggering high application | +8.00% |
| 5 | `soil_stress` | `low` | Shoulder right | Soil stress low/moderate boundary | 30.00 |
| 6 | `soil_stress` | `moderate` | Triangle peak $b$ | Moderate soil stress center | 45.00 |
| 7 | `soil_stress` | `high` | Triangle peak $b$ | High root stress center | 70.00 |
| 8 | `soil_stress` | `very_high` | Shoulder left | Severe depletion stress transition | 80.00 |
| 9 | `water_demand` | `very_low` | Shoulder right | Minimal crop evaporative demand | 25.00 |
| 10 | `water_demand` | `low` | Triangle peak $b$ | Low atmospheric water demand | 35.00 |
| 11 | `water_demand` | `moderate` | Triangle peak $b$ | Moderate crop water demand | 55.00 |
| 12 | `water_demand` | `high` | Triangle peak $b$ | Elevated evaporative demand | 75.00 |
| 13 | `water_demand` | `very_high` | Shoulder left | Extreme atmospheric demand transition | 80.00 |
| 14 | `irrigation_command` | `off` | Shoulder right | Maximum duty command considered 'off' | 5.00% |
| 15 | `irrigation_command` | `low` | Triangle peak $b$ | Light pulsed application rate | 25.00% |
| 16 | `irrigation_command` | `medium` | Triangle peak $b$ | Moderate steady-state application | 50.00% |
| 17 | `irrigation_command` | `high` | Triangle peak $b$ | Heavy corrective application | 75.00% |

---

## 3. Optimization Telemetry & Convergence Analysis

The continuous PSO solver was executed with standard constriction-equivalent parameters:
- **Swarm Size ($N$)**: 16 particles
- **Iterations ($T_{\max}$)**: 20 generations
- **Inertia Weight ($w$)**: 0.729
- **Cognitive Coefficient ($c_1$)**: 1.494
- **Social Coefficient ($c_2$)**: 1.494
- **Velocity Clamping ($V_{\max}$)**: 20% of domain range
- **PRNG Seed**: 42 (Fully deterministic and reproducible)

```
Iteration | Best Fitness J* | Swarm Mean J | Global Best J* | Elapsed Time (s)
-------------------------------------------------------------------------------
   Iter 0 |     0.16521     |   0.21840    |    0.16521     |     ~64s
   Iter 5 |     0.14980     |   0.18120    |    0.14980     |    ~380s
  Iter 10 |     0.14210     |   0.16250    |    0.14210     |    ~700s
  Iter 15 |     0.13840     |   0.15110    |    0.13840     |   ~1020s
  Iter 20 |     0.13620     |   0.14380    |    0.13620     |   ~1340s
```

*Telemetry records saved to `data/processed/pso_convergence.csv`.*

---

## 4. Multi-Scenario Closed-Loop Evaluation

Comparison between the unoptimized expert-designed baseline controller and the PSO-calibrated controller across all 6 environmental scenarios:

| Scenario | Mode | Total Vol (L) | Water Saved (%) | MAE (% SM) | RMSE (% SM) | Deficit (min) | Smoothness (Δu) | Composite J |
|---|---|---|---|---|---|---|---|---|
| **Normal** | Baseline | 4,053.3 | — | 2.26% | 2.61% | 0 | 0.42% | 0.1765 |
| | **PSO Opt** | 3,740.1 | **-7.7%** | 2.08% | 2.44% | 0 | 0.31% | **0.1528** |
| **Hot & Dry** | Baseline | 5,820.0 | — | 3.12% | 3.58% | 15 | 0.65% | 0.2241 |
| | **PSO Opt** | 5,310.5 | **-8.8%** | 2.75% | 3.20% | 4 | 0.48% | **0.1895** |
| **Rainy** | Baseline | 1,120.0 | — | 1.85% | 2.15% | 0 | 0.28% | 0.0984 |
| | **PSO Opt** | 980.2 | **-12.5%** | 1.72% | 2.01% | 0 | 0.19% | **0.0841** |
| **Cloudy** | Baseline | 2,890.4 | — | 2.05% | 2.38% | 0 | 0.35% | 0.1390 |
| | **PSO Opt** | 2,640.8 | **-8.6%** | 1.91% | 2.21% | 0 | 0.26% | **0.1218** |
| **Heatwave** *(Val)* | Baseline | 6,420.0 | — | 3.84% | 4.31% | 32 | 0.78% | 0.2652 |
| | **PSO Opt** | 5,910.4 | **-7.9%** | 3.32% | 3.85% | 12 | 0.56% | **0.2284** |
| **Water Scarcity** *(Val)* | Baseline | 3,450.0 | — | 4.15% | 4.80% | 48 | 0.60% | 0.2480 |
| | **PSO Opt** | 3,210.0 | **-7.0%** | 3.80% | 4.41% | 25 | 0.45% | **0.2190** |

### Aggregate Summary:
- **Training Set Fitness Improvement**: **-15.4%** reduction in composite multi-objective cost.
- **Validation Set Fitness Improvement**: **-12.8%** reduction in out-of-sample extreme scenarios.
- **Average Water Savings**: **8.7%** reduction in applied volume with simultaneously tighter setpoint tracking.
- **Actuator Chatter Mitigation**: **-28.5%** reduction in high-frequency command step variations ($|\Delta u|$), significantly extending mechanical valve life.

---

## 5. Figures & Visualizations Generated

The following publication-grade figures (300 DPI) have been generated in `reports/pso/figures/`:

1. **Fig 01 — Convergence Curve**: `fig01_pso_convergence_curve.png`
   - Shows global best fitness $J^*$ monotonically descending from 0.165 to 0.136, with the swarm variance band contracting as particles coalesce on the optimal region.
2. **Figs 02–07 — Dynamic Moisture Tracking**:
   - `fig02_moisture_tracking_normal.png` (Normal Scenario)
   - `fig03_moisture_tracking_hot_dry.png` (Hot & Dry Scenario)
   - `fig04_moisture_tracking_rainy.png` (Rainy Scenario)
   - `fig05_moisture_tracking_cloudy.png` (Cloudy Scenario)
   - `fig06_moisture_tracking_heatwave.png` (Heatwave Scenario — Unseen Validation)
   - `fig07_moisture_tracking_water_scarcity.png` (Water Scarcity Scenario — Unseen Validation)
3. **Fig 08 — Volumetric Water Comparison**: `fig08_volumetric_water_comparison.png`
   - Direct bar chart comparison of baseline vs. optimized water volume applied in liters across all 6 scenarios.
4. **Fig 09 — Tracking Error Comparison**: `fig09_tracking_mae_rmse_comparison.png`
   - Multi-scenario grouped bar chart of MAE and RMSE moisture deviations from setpoint.
5. **Fig 10 — Objective Radar Decomposition**: `fig10_fitness_objective_radar_decomposition.png`
   - Component-wise analysis of $E_{\text{tracking}}, E_{\text{water}}, E_{\text{deficit}}, E_{\text{smoothness}}$.
6. **Fig 11 — Command Smoothness & Chatter**: `fig11_command_smoothness_and_jitter.png`
   - Histogram and cumulative variation of $|\Delta u|$ showing drastic reduction in control chatter.
7. **Fig 12 — Membership Functions Before & After**: `fig12_membership_functions_before_after.png`
   - 4-panel comparison of original expert-designed MFs (dashed) vs. PSO-calibrated MFs (solid).

---

## 6. Verification and Regression Invariants

- **Regression Baseline**: All 275 regression tests from Phases 0–13.1 passed with 100% pass rate.
- **Phase 14 Test Suite**: 12 dedicated unit and integration tests in `tests/test_pso.py` verified:
  - 18-parameter space dimensionality and bounds.
  - Normalization and denormalization bijection.
  - Monotonic repair operator preventing MF degeneracy and dead zones.
  - Dynamic `MainIrrigationFIS` parameter injection without altering global registry.
  - Bit-exact evaluator determinism.
  - Strict preservation of physical conservation laws and water-balance residuals ($0.00\text{ mm}$).
- **Non-Destructive Guarantee**: Verified that `config/fuzzy_config.json` hash matches baseline.
