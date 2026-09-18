# Phase 11 Engineering Report: Single-Zone Closed-Loop Feedback Control

============================================================
PHASE: 11 — Single-Zone Closed-Loop Feedback Control
STATUS: Completed & Verified
REGRESSION BASELINE: 205 passed, 0 failed, 0 errors, 0 warnings
============================================================

## 1. Executive Summary

Phase 11 implements and verifies the first **true closed-loop feedback control simulation** of the Smart Multizone Irrigation System. In this phase, the four hierarchical Fuzzy Inference Systems—`SoilStressFIS` (Phase 7), `WeatherStressFIS` (Phase 8), `WaterDemandFIS` (Phase 9), and `MainIrrigationFIS` (Phase 10)—are coupled with the discrete dynamic soil-water balance model from Phase 5 into an autonomous feedback loop.

The simulation executes sequentially at a **1-minute temporal resolution over a 24-hour horizon (1,440 timesteps)** for **Zone 1 (Tomato, Loam soil, 100 m²)** across all six established environmental scenarios, compiling an 8,640-record dataset in `data/processed/closed_loop_single_zone.csv`.

Key engineering achievements include:
1. **Strict Temporal Causality**: Controller command $u(t)$ depends exclusively on past and current state variables ($SM(t), e(t), RSM(t)$), strictly forbidding future-state leakage ($SM(t+1)$).
2. **Transparent Actuator Mapping**: A deterministic linear mapping converts normalized supervisory commands $[0, 100]\%$ into physical application depth ($I_{\max} = 12.0\text{ mm/h}$), safely below loam infiltration capacity ($20.0\text{ mm/h}$).
3. **Rigorous Conservation Accounting**: The root-zone water balance residual remains mathematically zero ($|\text{residual}| = 0.00\text{ mm}$, 0 violations across all 8,640 timesteps).
4. **Objective Baseline Superiority**: Compared to open-loop baselines (No Irrigation and Fixed Irrigation at 1.5 mm/h), the fuzzy closed-loop controller achieves the lowest Mean Absolute Error ($\text{MAE} = 2.26\%$), lowest Root Mean Square Error ($\text{RMSE} = 2.61\%$), and lowest Integral Absolute Error ($\text{IAE} = 3254.67\%\cdot\text{min}$), settling precisely inside the target tolerance band ($59.72\%$ vs $60.00\%$ target).
5. **Architectural Separation**: The single-zone controller computes unconstrained agronomic demand. Supply-side water allocation and rationing under scarcity are reserved for Phase 13.

---

## 2. Zone 1 Agronomic Configuration

Phase 11 is strictly scoped to Zone 1, preserving all established database and operational parameters:

| Parameter | Configuration Value | Physical Meaning / Agronomic Source |
| :--- | :--- | :--- |
| **Zone ID** | `1` | Canonical mid-season testbed zone |
| **Crop** | `Tomato` (*Solanum lycopersicum*) | High-value vegetable crop |
| **Growth Stage** | `Mid-season` | Peak vegetative and reproductive stage |
| **Crop Coefficient ($K_c$)** | `1.15` | FAO-56 Chapter 6 standard |
| **Root Depth ($Z_r$)** | `0.70 m` | Effective active root extraction depth |
| **Soil Textural Class** | `Loam` | Standard balanced agricultural soil |
| **Field Capacity ($FC$)** | `70.0%` vol | Upper retention threshold against gravity |
| **Permanent Wilting Point ($WP$)**| `25.0%` vol | Lower extraction limit for plant roots |
| **Saturation Capacity ($SAT$)** | `85.0%` vol | Total pore space capacity |
| **Infiltration Capacity** | `20.0 mm/h` | Maximum water absorption rate |
| **Drainage Parameter** | `0.08` | Gravity deep percolation coefficient |
| **Initial Soil Moisture ($SM_0$)** | `55.0%` vol | Starting condition (depleted below target) |
| **Target Setpoint ($SM_{\text{target}}$)**| `60.0%` vol | Optimal moisture setpoint for tomato |
| **Initial Moisture Error ($e(0)$)**| `+5.0%` vol | Initial deficit ($60.0 - 55.0 = +5.0\%$) |
| **Target Band** | `[58.0%, 62.0%]` | Target $\pm 2.0\%$ operational tolerance band |
| **Cultivated Area** | `100.0 m²` | Surface boundary |

---

## 3. Mathematical Formulation and Governing Equations

The closed-loop dynamics are governed by standard agronomic and hydrological relationships:

### 3.1 Moisture Tracking Error:
$$e(t) = SM_{\text{target}} - SM(t)$$
Where $e(t) > 0$ represents moisture depletion below setpoint, and $e(t) < 0$ represents surplus moisture.

### 3.2 Relative Soil Moisture (RSM):
$$RSM(t) = \frac{SM(t) - WP}{FC - WP} = \frac{SM(t) - 25.0}{70.0 - 25.0}$$
At initial step: $RSM(0) = \frac{55.0 - 25.0}{45.0} = 0.6667$ (adequate moisture regime).

### 3.3 Crop Evapotranspiration:
$$ET_c(t) = K_c(t) \cdot ET_0(t) = 1.15 \cdot ET_0(t)$$
Where $ET_0(t)$ is computed via the FAO-56 Penman-Monteith sub-daily formulation.

### 3.4 Crop Water Deficit:
$$D_{\text{crop}}(t) = \max(ET_c(t) - P_{\text{eff}}(t), 0.0)$$
Where $P_{\text{eff}}(t)$ is calculated via the USDA-SCS sub-daily precipitation adaptation.

### 3.5 Hierarchical Fuzzy Inference Systems:
1. **Soil Stress FIS**:
   $$SS(t) = \text{SoilStressFIS}(RSM(t), e(t)) \in [0.0, 100.0]\%$$
2. **Weather Stress FIS**:
   $$WS(t) = \text{WeatherStressFIS}(T(t), RH(t), R_s(t), u_2(t), P(t)) \in [0.0, 100.0]\%$$
3. **Water Demand FIS**:
   $$WD(t) = \text{WaterDemandFIS}(ET_c(t), D_{\text{crop}}(t), P_{\text{eff}}(t)) \in [0.0, 100.0]\%$$
4. **Main Irrigation FIS**:
   $$u(t) = \text{MainIrrigationFIS}(SS(t), WS(t), WD(t), e(t)) \in [0.0, 100.0]\%$$

### 3.6 Actuator Delivery Mapping:
$$I_{\text{app}}(t) = \left(\frac{u(t)}{100.0}\right) \times I_{\max} \times \left(\frac{\Delta t}{60}\right)\text{ mm}$$
With $I_{\max} = 12.0\text{ mm/h}$ and $\Delta t = 1\text{ min}$, $I_{\text{app}}(t) \in [0.0, 0.20]\text{ mm/min}$.

### 3.7 Dynamic Root-Zone Soil-Water Balance:
$$S(t+1) = S(t) + W_{\text{inf}}(t) - ET_{\text{act}}(t) - D(t)$$
Where:
- $S(t) = 1000 \cdot \frac{SM(t)}{100} \cdot Z_r = 7.0 \cdot SM(t)\text{ mm}$.
- $W_{\text{inf}}(t) = \min(I_{\text{app}}(t) + P_{\text{eff}}(t), K_{\text{inf}} \cdot \frac{\Delta t}{60})$.
- $ET_{\text{act}}(t) = \min(ET_c(t), \max(0, S_{\text{after\_inflow}} - S_{WP}))$.
- $D(t) = \text{calculate\_drainage}(S_{\text{after\_et}}, S_{FC})$.
- $SM(t+1) = \frac{S(t+1)}{1000 \cdot Z_r} \times 100\%$.

---

## 4. Causality and Temporal Ordering Proof

Strict causality is enforced by construction and verified by automated unit tests (`test_03_current_state_used_before_control` and `test_19_no_future_state_leakage`):

1. At time step $t$, the controller reads $SM(t)$.
2. The error $e(t) = 60.0 - SM(t)$ and relative moisture $RSM(t)$ are evaluated.
3. Subsystem FISs compute stress and demand from state $t$.
4. The supervisory command $u(t)$ and actuator delivery $I_{\text{app}}(t)$ are determined.
5. Infiltration, ET extraction, and drainage compute $S(t+1)$ and $SM(t+1)$.
6. The updated state $SM(t+1)$ is stored in `next_soil_moisture` and becomes the input for step $t+1$.

At no point does the computation of $u(t)$ access $SM(t+1)$.

---

## 5. Performance Metrics and Baseline Comparison

Under the canonical **Normal** environmental scenario (24 hours, 1,440 timesteps, initial moisture = $55.0\%$, target = $60.0\%$), three regimes were evaluated:

| Performance Metric | Baseline A: No Irrigation | Baseline B: Fixed (1.5 mm/h) | Control: Fuzzy Closed-Loop | Physical Advantage of Closed-Loop |
| :--- | :---: | :---: | :---: | :--- |
| **Initial Soil Moisture** | $55.00\%$ | $55.00\%$ | $55.00\%$ | Identical initial conditions |
| **Final Soil Moisture** | $53.93\%$ | $59.07\%$ | **$59.72\%$** | **Closest to setpoint ($60.00\%$)** |
| **Final Tracking Error $e(T)$** | $+6.07\%$ | $+0.93\%$ | **$+0.28\%$** | **Near-zero steady-state residual** |
| **Minimum Soil Moisture** | $53.93\%$ | $55.00\%$ | $55.00\%$ | Prevents crop root depletion |
| **Maximum Soil Moisture** | $55.00\%$ | $59.07\%$ | $59.72\%$ | Stays within target tolerance band |
| **Mean Soil Moisture** | $54.53\%$ | $57.09\%$ | $57.74\%$ | Rapid rise to optimal range |
| **Mean Absolute Error (MAE)** | $5.4742\%$ | $2.9046\%$ | **$2.2602\%$** | **22.2% lower MAE than Fixed** |
| **Root Mean Square Error (RMSE)**| $5.4915\%$ | $3.0960\%$ | **$2.6066\%$** | **15.8% lower RMSE than Fixed** |
| **Integral Absolute Error (IAE)**| $7882.87\%\cdot\text{min}$| $4182.58\%\cdot\text{min}$| **$3254.67\%\cdot\text{min}$**| **22.2% reduction in error integral** |
| **Total Irrigation Applied** | $0.00\text{ mm}$ | $36.00\text{ mm}$ | $40.53\text{ mm}$ | Matches deficit ($35\text{ mm}$) + $ET_c$ ($7.5\text{ mm}$) |
| **Total Cumulative $ET_c$** | $7.51\text{ mm}$ | $7.51\text{ mm}$ | $7.51\text{ mm}$ | Driven by FAO-56 atmospheric demand |
| **Actual $ET$ Consumed** | $7.51\text{ mm}$ | $7.51\text{ mm}$ | $7.51\text{ mm}$ | Unstressed transpiration maintained |
| **Total Deep Drainage** | $0.00\text{ mm}$ | $0.00\text{ mm}$ | $0.00\text{ mm}$ | Zero deep percolation losses |
| **Time to Enter Target Band** | Never | $760\text{ min}$ | **$738\text{ min}$** | **Enters target band 22 min faster** |
| **Time in Target Band** | $0\text{ min}$ ($0.0\%$) | $680\text{ min}$ ($47.2\%$) | **$702\text{ min}$ ($48.8\%$)**| **Longest residence in optimal band** |
| **Max Conservation Residual** | $0.00\text{ mm}$ | $0.00\text{ mm}$ | $0.00\text{ mm}$ | Exact conservation across all models |

### Key Control Observations:
1. **Negative Feedback Damping**: In the early hours (Steps 0–300), the controller commands $21.66\%$ ($0.0433\text{ mm/min}$), delivering consistent replenishment. As soil moisture crosses $58.0\%$ and approaches $60.0\%$, the moisture tracking error drops to zero, reducing the command from $21.66\%$ down to $7.54\%$, preventing overshoot.
2. **Open-Loop Deficiencies**: Baseline A suffers continuous depletion due to uncompensated $ET_c$, ending at $53.93\%$. Baseline B delivers water at a rigid unmodulated rate ($1.5\text{ mm/h}$), ending at $59.07\%$ but lacking any capability to compensate for midday evaporative spikes or rainfall events.

---

## 6. Multi-Scenario Closed-Loop Evaluation

All six environmental scenarios were simulated under closed-loop control. The response demonstrates robust, physically consistent adaptation:

| Scenario | Total Rain (mm) | Eff Rain (mm) | Total $ET_c$ (mm) | Total Irrig (mm) | Final SM (%) | Final Error (%) | MAE (%) | In-Band Time (%) | Max Command (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Normal** | $0.00$ | $0.00$ | $7.51$ | $40.53$ | $59.72\%$ | $+0.28\%$ | $2.26\%$ | $48.8\%$ | $21.66\%$ |
| **Hot & Dry** | $0.00$ | $0.00$ | $10.44$ | $42.93$ | $59.64\%$ | $+0.36\%$ | $2.16\%$ | $54.9\%$ | $28.46\%$ |
| **Rainy** | $21.99$ | $17.19$ | $2.35$ | **$31.03$** | $60.88\%$ | $-0.88\%$ | **$1.90\%$** | $52.4\%$ | $21.66\%$ |
| **Cloudy** | $0.00$ | $0.00$ | $3.17$ | $37.79$ | $59.95\%$ | $+0.05\%$ | $2.10\%$ | $51.8\%$ | $21.66\%$ |
| **Heatwave** | $0.00$ | $0.00$ | $12.04$ | **$44.04$** | $59.57\%$ | $+0.43\%$ | $2.15\%$ | **$56.7\%$** | **$28.67\%$** |
| **Water Scarcity**| $0.00$ | $0.00$ | $8.11$ | $40.94$ | $59.69\%$ | $+0.31\%$ | $2.27\%$ | $49.0\%$ | $21.66\%$ |

### Agronomic Analysis of Scenarios:
1. **Rainy Scenario Response**: Under $21.99\text{ mm}$ of rainfall ($17.19\text{ mm}$ effective), natural precipitation infiltrates into the root zone. This decreases moisture tracking error and suppresses `WaterDemandFIS` output. Consequently, irrigation automatically throttles down to $31.03\text{ mm}$ ($9.5\text{ mm}$ or $23.4\%$ water savings compared to Normal), with final moisture settling smoothly at $60.88\%$.
2. **Hot & Dry / Heatwave Adaptation**: High midday temperatures and severe vapor pressure deficits elevate $ET_c$ to $10.44\text{ mm}$ and $12.04\text{ mm}$. The controller responds by increasing peak irrigation commands to $28.46\%$ and $28.67\%$, delivering $42.93\text{ mm}$ and $44.04\text{ mm}$ to prevent drought stress.
3. **Water Scarcity Boundary Verification**: In the Water Scarcity scenario ($WAF = 0.30$), the controller computes the true unconstrained agronomic demand ($40.94\text{ mm}$ applied, final $SM = 59.69\%$). The single-zone controller does not artificially scale down command outputs; supply-constrained rationing belongs strictly to Phase 13.

---

## 7. Water Balance Conservation Verification

Across all six scenarios ($6 \times 1440 = 8,640$ discrete timesteps), the conservation equation:
$$\text{Residual}(t) = S(t) + W_{\text{inf}}(t) - ET_{\text{act}}(t) - D(t) - S(t+1)$$
was calculated at every step:
- **Maximum Absolute Residual across all 8,640 timesteps**: $0.00\text{ mm}$ ($< 10^{-12}\text{ mm}$).
- **Mean Absolute Residual**: $0.00\text{ mm}$.
- **Conservation Violations ($> 10^{-6}\text{ mm}$)**: **0**.

No numerical water creation or disappearance occurred.

---

## 8. Analytical Figures

All figures have been rendered at 300 DPI and are located in `reports/closed_loop/figures/`:

1. **Master Closed-Loop Feedback Timeline (Soil Moisture vs Target vs Command)**:
   `reports/closed_loop/figures/closed_loop_response_master.png`
2. **Controller vs Baselines (No Irrigation vs Fixed Irrigation)**:
   `reports/closed_loop/figures/closed_loop_baseline_comparison.png`
3. **Multi-Scenario Soil Moisture Trajectories**:
   `reports/closed_loop/figures/closed_loop_scenarios_comparison.png`
4. **Multi-Scenario Irrigation Commands**:
   `reports/closed_loop/figures/closed_loop_scenarios_commands.png`
5. **Cumulative Hydrological Fluxes (Irrigation, ETc, Actual ET, Drainage)**:
   `reports/closed_loop/figures/closed_loop_cumulative_fluxes.png`
6. **Hierarchical Fuzzy Subsystem Indices (Soil Stress, Weather Stress, Water Demand)**:
   `reports/closed_loop/figures/closed_loop_fuzzy_subsystems.png`
7. **Diurnal ETc vs Rainfall**:
   `reports/closed_loop/figures/closed_loop_etc_vs_rainfall.png`
8. **Tracking Error Over Time**:
   `reports/closed_loop/figures/closed_loop_moisture_error.png`
9. **Physical Actuator Water Delivery**:
   `reports/closed_loop/figures/closed_loop_irrigation_application.png`
10. **Controller vs No-Irrigation Baseline**:
    `reports/closed_loop/figures/closed_loop_vs_no_irrigation.png`
11. **Controller vs Fixed-Irrigation Baseline**:
    `reports/closed_loop/figures/closed_loop_vs_fixed_irrigation.png`
12. **Soil Moisture vs Target Band**:
    `reports/closed_loop/figures/closed_loop_soil_moisture_vs_target.png`
13. **Irrigation Command vs Time**:
    `reports/closed_loop/figures/closed_loop_irrigation_command.png`
14. **Soil Stress FIS Output**:
    `reports/closed_loop/figures/closed_loop_soil_stress.png`
15. **Weather Stress FIS Output**:
    `reports/closed_loop/figures/closed_loop_weather_stress.png`
16. **Water Demand FIS Output**:
    `reports/closed_loop/figures/closed_loop_water_demand.png`

---

## 9. Computational Performance

- **Single-Zone 1440-step simulation runtime**: ~2.66 seconds.
- **Six-scenario suite execution (8,640 timesteps total)**: 15.94 seconds.
- **Average timestep evaluation time**: ~1.85 ms (including 4 Mamdani centroid defuzzifications and water balance update).

---

## 10. Test Suite and Regression Audit

The automated test suite `tests/test_closed_loop.py` covers all 24 required specifications:
- `test_01_initial_state_initialization`: PASSED
- `test_02_initial_moisture_error`: PASSED
- `test_03_current_state_used_before_control`: PASSED
- `test_04_controller_output_bounded`: PASSED
- `test_05_soil_moisture_physically_bounded`: PASSED
- `test_06_water_balance_residual_zero`: PASSED
- `test_07_irrigation_application_non_negative`: PASSED
- `test_08_zero_command_zero_application`: PASSED
- `test_09_positive_command_positive_application`: PASSED
- `test_10_increasing_deficit_increases_response`: PASSED
- `test_11_rainfall_affects_soil_moisture`: PASSED
- `test_12_rainfall_propagates_into_reduced_demand`: PASSED
- `test_13_controller_negative_feedback`: PASSED
- `test_14_closed_loop_drives_state_changes`: PASSED
- `test_15_simulation_determinism`: PASSED
- `test_16_different_scenarios_produce_different_trajectories`: PASSED
- `test_17_nan_inf_handling`: PASSED
- `test_18_single_zone_isolation`: PASSED
- `test_19_no_future_state_leakage`: PASSED
- `test_20_target_band_metric_calculation`: PASSED
- `test_21_mae_rmse_iae_calculations`: PASSED
- `test_22_baseline_simulations_execute`: PASSED
- `test_23_water_scarcity_no_allocation_curtailment`: PASSED
- `test_24_water_allocation_placeholder_remains_not_implemented`: PASSED

### Full Test Suite Status:
- **Previous baseline (Phases 0–10)**: 181 passed
- **New Phase 11 tests**: 24 passed
- **Final total**: **205 passed, 0 failed, 0 errors, 0 warnings** (Runtime: 72.53s)

---

## 11. Files Created and Modified

### Files Created:
1. `simulation/closed_loop.py`: Dedicated single-zone closed-loop simulation orchestrator, data models (`ClosedLoopConfig`, `ClosedLoopMetrics`), and `simulate_single_zone()` API.
2. `tests/test_closed_loop.py`: Comprehensive 24-test verification suite.
3. `scripts/generate_closed_loop_analysis.py`: Scenario generator, dataset compiler, baseline runner, and plotting script.
4. `docs/single_zone_closed_loop.md`: Engineering architecture and formulation documentation.
5. `reports/closed_loop/SINGLE_ZONE_CLOSED_LOOP_REPORT.md`: This comprehensive engineering report.
6. `data/processed/closed_loop_single_zone.csv`: Consolidated 8,640-row dataset across all 6 scenarios.
7. `reports/closed_loop/figures/*.png`: 16 high-resolution figures at 300 DPI.

### Files Modified:
- None. All Phase 0–10 code remains strictly intact and unmodified.

---

## 12. Future Placeholders Verification

The following boundaries are explicitly confirmed:
- **Phase 12 (Multizone Closed-Loop Control)**: NOT implemented.
- **Phase 13 (Water Allocation FIS)**: NOT implemented (`WaterAllocationFIS` raises `NotImplementedError`).
- **PSO / Adaptive Controller**: NOT implemented.
- **Backend (FastAPI)**: NOT implemented.
- **Database (Supabase)**: NOT implemented.
- **Frontend (Next.js / Dashboard)**: NOT implemented.
- **LLM / Groq / RAG**: NOT implemented.
- **Deployment**: NOT implemented.

============================================================
PHASE 11 COMPLETE — STOPPED BEFORE PHASE 12.
============================================================
