# Phase 11 Documentation: Single-Zone Closed-Loop Feedback Control

## 1. Objective and Overview

The primary objective of **Phase 11** is to establish the first true **dynamic closed-loop feedback control simulation** within the Smart Multizone Irrigation System. In previous phases (Phases 0–5), the environmental engine and soil-water dynamics operated in an open-loop regime. In Phases 6–10, the four hierarchical fuzzy inference subsystems were implemented and evaluated sequentially. Phase 11 couples these components into an operational closed-loop feedback system where actuator commands alter root-zone water storage, and the updated moisture state feeds dynamically into subsequent control epochs.

This phase is strictly scoped to **Zone 1 (Tomato, Loam soil, 100 m²)**, executing at 1-minute discrete intervals across 24 hours (1,440 timesteps).

---

## 2. Closed-Loop Architecture

The single-zone closed-loop architecture follows a rigorous negative feedback topology:

```
                  ┌─────────────────────────────────────────────────────────┐
                  │               Environmental Meteorology                 │
                  │        (Temperature, Humidity, Solar, Wind, Rain)       │
                  └──────────────┬───────────────────────────┬──────────────┘
                                 │                           │
                                 ▼                           ▼
                        ┌──────────────────┐       ┌──────────────────┐
                        │   WeatherStress  │       │  FAO-56 ET0/ETc  │
                        │       FIS        │       │  & Peff Engine   │
                        └────────┬─────────┘       └─────────┬────────┘
                                 │                           │
                                 │                           ▼
                                 │                 ┌──────────────────┐
                                 │                 │   WaterDemand    │
                                 │                 │       FIS        │
                                 │                 └─────────┬────────┘
                                 │                           │
      ┌────────────────┐         │                           │
      │  Target SM     │         │                           │
      │   (60.0%)      │         │                           │
      └───┬────────────┘         │                           │
          │                      │                           │
          ▼                      │                           │
      ( + )                      │                           │
        │                        │                           │
        ├──> e(t) ───────────────┼───────────────────────────┤
        │                        │                           │
      ( - )                      │                           │
        ▲                        ▼                           ▼
        │              ┌───────────────────────────────────────────────┐
        │              │             Main Irrigation FIS               │
        │              │  Inputs: SoilStress, WeatherStress, Demand, e │
        │              └───────────────────────┬───────────────────────┘
        │                                      │
        │                                      ▼
        │                           Irrigation Command [%]
        │                                      │
        │                                      ▼
        │                          ┌───────────────────────┐
        │                          │   Actuator Mapping    │
        │                          │   (Linear Rate Model) │
        │                          └───────────┬───────────┘
        │                                      │
        │                                      ▼
        │                          Irrigation Application [mm]
        │                                      │
        │                                      ▼
        │                          ┌───────────────────────┐
        │                          │   Soil Water Balance  │
        │                          │  S(t+1) = S(t)+I-ET-D │
        │                          └───────────┬───────────┘
        │                                      │
        │                                      ▼
        │                             Updated Soil State
        │                            SM(t+1), RSM(t+1)
        │                                      │
        └──────────────────────────────────────┘
                  Dynamic State Feedback (↺)
```

---

## 3. State Variables and Schema

At each discrete simulation step $t \in [0, 1439]$, the simulation state vector maintains:

| Variable | Symbol | Unit | Physical Description |
| :--- | :--- | :--- | :--- |
| `timestamp` | $t$ | ISO string | Chronological timestamp of the observation |
| `soil_moisture` | $SM(t)$ | % vol | Working root-zone moisture percentage |
| `storage_mm` | $S(t)$ | mm | Equivalent water depth in root zone ($1000 \cdot \theta \cdot Z_r$) |
| `target_moisture` | $SM_{\text{target}}$ | % vol | Agronomic setpoint ($60.0\%$) |
| `moisture_error` | $e(t)$ | % vol | Tracking error: $SM_{\text{target}} - SM(t)$ |
| `rsm` | $RSM(t)$ | $[0, 1]$ | Normalized relative moisture: $\frac{SM(t) - WP}{FC - WP}$ |
| `soil_stress` | $SS(t)$ | % | Output from `SoilStressFIS` |
| `weather_stress` | $WS(t)$ | % | Output from `WeatherStressFIS` |
| `et0` | $ET_0(t)$ | mm/step | FAO-56 Penman-Monteith reference evapotranspiration |
| `etc` | $ET_c(t)$ | mm/step | Crop evapotranspiration: $K_c \cdot ET_0(t)$ |
| `rainfall` | $P(t)$ | mm/step | Atmospheric precipitation |
| `effective_rainfall`| $P_{\text{eff}}(t)$| mm/step | Infiltrated rainfall available to roots |
| `crop_water_deficit`| $D_{\text{crop}}(t)$| mm/step | Atmospheric deficit: $\max(ET_c - P_{\text{eff}}, 0)$ |
| `water_demand` | $WD(t)$ | % | Output from `WaterDemandFIS` |
| `irrigation_command`| $u(t)$ | % | Supervisory normalized control command ($[0, 100]\%$) |
| `irrigation_application`| $I_{\text{app}}(t)$| mm/step | Physical actuator water depth |
| `infiltration` | $W_{\text{inf}}(t)$ | mm/step | Infiltrated water volume reaching root zone |
| `actual_et` | $ET_{\text{act}}(t)$| mm/step | Actual evapotranspiration extracted |
| `drainage` | $D(t)$ | mm/step | Gravitational deep percolation below root zone |
| `next_soil_moisture`| $SM(t+1)$ | % vol | State update feeding timestep $t+1$ |
| `water_balance_residual`| $R(t)$ | mm/step | Conservation residual: $S(t) + W_{\text{inf}} - ET_{\text{act}} - D - S(t+1)$ |

---

## 4. Control Loop Execution Order

At timestep $t$, execution proceeds in strict sequence:
1. **Current Soil State**: Read $SM(t)$ from current `SoilState`.
2. **Moisture Tracking Error**:
   $$e(t) = SM_{\text{target}} - SM(t)$$
3. **Relative Soil Moisture**:
   $$RSM(t) = \frac{SM(t) - WP}{FC - WP}$$
4. **Soil Stress FIS**:
   $$\text{soil\_stress}(t) = \text{SoilStressFIS}(RSM(t), e(t))$$
5. **Weather Stress FIS**:
   $$\text{weather\_stress}(t) = \text{WeatherStressFIS}(T(t), RH(t), R_s(t), u_2(t), P(t))$$
6. **FAO-56 Evapotranspiration**:
   $$ET_0(t) = \text{FAO56}(T, RH, R_s, u_2)$$
   $$ET_c(t) = K_c \cdot ET_0(t)$$
7. **Effective Rainfall & Crop Water Deficit**:
   $$P_{\text{eff}}(t) = \text{USDA\_SCS}(P(t), \Delta t)$$
   $$D_{\text{crop}}(t) = \max(ET_c(t) - P_{\text{eff}}(t), 0.0)$$
8. **Water Demand FIS**:
   $$\text{water\_demand}(t) = \text{WaterDemandFIS}(ET_c(t), D_{\text{crop}}(t), P_{\text{eff}}(t))$$
9. **Main Irrigation FIS**:
   $$\text{irrigation\_command}(t) = \text{MainIrrigationFIS}(\text{soil\_stress}(t), \text{weather\_stress}(t), \text{water\_demand}(t), e(t))$$
10. **Actuator Mapping**:
    $$I_{\text{app}}(t) = \left(\frac{\text{irrigation\_command}(t)}{100.0}\right) \times I_{\max} \times \left(\frac{\Delta t}{60}\right)\text{ mm}$$
11. **Soil-Water Balance**:
    $$S(t+1) = S(t) + W_{\text{inf}}(t) - ET_{\text{actual}}(t) - D(t)$$
12. **State Advance**: $SM(t+1) = \frac{S(t+1)}{1000 \cdot Z_r} \times 100\%$, feeding timestep $t+1$.

---

## 5. Actuator Mapping: Command to Physical Application

The `MainIrrigationFIS` outputs a normalized dimensionless control command $u(t) \in [0.0, 100.0]\%$. To convert this command into a physical irrigation application depth $I_{\text{app}}(t)$ (mm), a linear actuator delivery model is employed:

$$I_{\text{app}}(t) = \left(\frac{u(t)}{100.0}\right) \times I_{\max} \times \left(\frac{\Delta t}{60}\right)$$

Where:
- $u(t)$: Normalized irrigation command ($[0, 100]\%$).
- $I_{\max}$: Maximum rated actuator delivery capacity ($12.0\text{ mm/hour}$).
- $\Delta t$: Simulation time step ($1\text{ minute}$).
- $12.0 / 60 = 0.20\text{ mm/minute}$ at maximum $100\%$ valve opening.

### Physical Grounding and Soil Compatibility:
- Loam soil maximum infiltration capacity is $K_{\text{inf}} = 20.0\text{ mm/hour}$.
- Setting $I_{\max} = 12.0\text{ mm/hour}$ ensures that $I_{\max} < K_{\text{inf}}$, strictly preventing actuator-induced surface runoff and soil erosion under normal operating conditions.
- For Zone 1 ($Z_r = 0.7\text{ m}$), an error of $+5.0\%$ represents $35.0\text{ mm}$ of depleted storage ($1000 \times 0.05 \times 0.7$). At $12.0\text{ mm/hour}$, this deficit can be fully replenished in ~3.5 hours of equivalent full-capacity pumping.

---

## 6. Target Band and Error Metrics

The setpoint target moisture is $SM_{\text{target}} = 60.0\%$.
A symmetric tolerance band of $\pm 2.0\%$ defines the acceptable operational regime:
$$\text{Target Band} = [58.0\%, 62.0\%]$$

### Control Performance Metrics:
1. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{N} \sum_{t=1}^N |SM_{\text{target}} - SM(t)|$$
2. **Root Mean Square Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{t=1}^N (SM_{\text{target}} - SM(t))^2}$$
3. **Integral Absolute Error (IAE)**:
   $$\text{IAE} = \sum_{t=1}^N |SM_{\text{target}} - SM(t)| \cdot \Delta t \quad [\% \cdot \text{minutes}]$$
4. **Time to Target Band ($T_{\text{target}}$)**: Timestep index (in minutes) at which soil moisture first enters $[58.0\%, 62.0\%]$.
5. **Time in Target Band ($T_{\text{in\_band}}$)**: Cumulative minutes where $SM(t) \in [58.0\%, 62.0\%]$.

---

## 7. Baseline Comparisons

To objectively demonstrate control effectiveness, two benchmark baselines are simulated under identical weather and initial conditions:

1. **Baseline A: No Irrigation ($I = 0.0\text{ mm}$)**
   Simulates natural unassisted crop depletion under ambient atmospheric demand.
2. **Baseline B: Fixed Irrigation ($I = 1.5\text{ mm/hour}$ constant)**
   Simulates conventional open-loop scheduled timer irrigation ($36.0\text{ mm/day}$ total), representing average daily deficit replacement without feedback sensing.
3. **Control: Fuzzy Closed-Loop**
   Dynamic adaptive demand modulation with negative feedback damping.

---

## 8. Architectural Boundaries and Limitations

1. **Single-Zone Isolation**: Phase 11 controls Zone 1 only. Zone 2 (Wheat / Sandy) and Zone 3 (Maize / Clay) remain uncoupled. Multizone coordination belongs to Phase 12.
2. **Separation of Control Demand vs Supply Allocation**:
   In the Water Scarcity scenario ($WAF = 0.30$), Phase 11 computes the **unconstrained agronomic control demand**. Supply-constrained reservoir rationing belongs strictly to **Phase 13 (Water Allocation FIS)**.
3. **No Optimization / Adaptation**: The fuzzy membership functions and rule base remain fixed (Mamdani centroid); no PSO or online parameter tuning is implemented.
