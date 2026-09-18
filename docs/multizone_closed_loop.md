# Phase 12 Documentation: Multizone Closed-Loop Fuzzy Control

## 1. Objective and Overview

The objective of **Phase 12** is to extend the verified single-zone closed-loop feedback architecture from Phase 11 to the system's **three agricultural zones operating in parallel**. Each zone is characterized by distinct crop genetics, root depth, soil texture, water retention capacity, infiltration limits, and agronomic setpoints:
- **Zone 1**: Tomato (*Solanum lycopersicum*), Loam soil, Area = 100 m², Mid-season ($K_c = 1.15$, $Z_r = 0.70\text{ m}$), $FC = 70.0\%$, $WP = 25.0\%$, Initial $SM = 55.0\%$, Target $SM = 60.0\%$.
- **Zone 2**: Wheat (*Triticum aestivum*), Sandy soil, Area = 120 m², Development ($K_c = 0.85$, $Z_r = 0.90\text{ m}$), $FC = 60.0\%$, $WP = 18.0\%$, Initial $SM = 42.0\%$, Target $SM = 55.0\%$.
- **Zone 3**: Maize (*Zea mays*), Clay soil, Area = 80 m², Mid-season ($K_c = 1.20$, $Z_r = 1.00\text{ m}$), $FC = 75.0\%$, $WP = 30.0\%$, Initial $SM = 65.0\%$, Target $SM = 65.0\%$.

The system executes at a discrete 1-minute time step over a 24-hour horizon (1,440 timesteps) across all six environmental scenarios, generating 25,920 records in `data/processed/multizone_closed_loop.csv`.

---

## 2. Multizone Architecture

```
                             METEOROLOGICAL MODEL
                    (T, RH, Rs, u2, P) → FAO-56 Reference ET0(t)
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
            ZONE 1                  ZONE 2                  ZONE 3
        Tomato / Loam           Wheat / Sandy            Maize / Clay
          (100 m²)                (120 m²)                 (80 m²)
              │                       │                       │
              ▼                       ▼                       ▼
          ETc1 = 1.15*ET0         ETc2 = 0.85*ET0         ETc3 = 1.20*ET0
              │                       │                       │
              ▼                       ▼                       ▼
          Soil State 1            Soil State 2            Soil State 3
          SM1(t), S1(t)           SM2(t), S2(t)           SM3(t), S3(t)
              │                       │                       │
              ▼                       ▼                       ▼
          e1(t), RSM1(t)          e2(t), RSM2(t)          e3(t), RSM3(t)
              │                       │                       │
              ▼                       ▼                       ▼
          SoilStress 1            SoilStress 2            SoilStress 3
              │                       │                       │
              ▼                       ▼                       ▼
        WeatherStress(t)        WeatherStress(t)        WeatherStress(t)
              │                       │                       │
              ▼                       ▼                       ▼
         WaterDemand 1           WaterDemand 2           WaterDemand 3
              │                       │                       │
              ▼                       ▼                       ▼
       MainIrrigation 1        MainIrrigation 2        MainIrrigation 3
              │                       │                       │
              ▼                       ▼                       ▼
         Command u1(t)           Command u2(t)           Command u3(t)
              │                       │                       │
              ▼                       ▼                       ▼
       Application I1(t)       Application I2(t)       Application I3(t)
       Volume V1(t) [L]        Volume V2(t) [L]        Volume V3(t) [L]
              │                       │                       │
              ▼                       ▼                       ▼
       Water Balance 1         Water Balance 2         Water Balance 3
              │                       │                       │
              ▼                       ▼                       ▼
         SM1(t+1) ↺              SM2(t+1) ↺              SM3(t+1) ↺
```

---

## 3. Parallel Per-Zone Control Pipeline

For each zone $z \in \{1, 2, 3\}$ at timestep $t$:
1. **Current State Read**: Retrieve $SM_z(t)$ and root storage $S_z(t) = 1000 \cdot \frac{SM_z(t)}{100} \cdot Z_{r, z}\text{ mm}$.
2. **Tracking Error**:
   $$e_z(t) = SM_{\text{target}, z} - SM_z(t)$$
3. **Relative Soil Moisture**:
   $$RSM_z(t) = \frac{SM_z(t) - WP_z}{FC_z - WP_z}$$
4. **Soil Stress FIS**:
   $$SS_z(t) = \text{SoilStressFIS}(RSM_z(t), e_z(t))$$
5. **Crop Evapotranspiration**:
   $$ET_{c, z}(t) = K_{c, z} \cdot ET_0(t)$$
6. **Effective Rainfall & Water Deficit**:
   $$P_{\text{eff}, z}(t) = \text{calculate\_effective\_rainfall}(P(t), \Delta t)$$
   $$D_{\text{crop}, z}(t) = \max(ET_{c, z}(t) - P_{\text{eff}, z}(t), 0.0)$$
7. **Water Demand FIS**:
   $$WD_z(t) = \text{WaterDemandFIS}(ET_{c, z}(t), D_{\text{crop}, z}(t), P_{\text{eff}, z}(t))$$
8. **Main Irrigation FIS**:
   $$u_z(t) = \text{MainIrrigationFIS}(SS_z(t), WS(t), WD_z(t), e_z(t)) \in [0.0, 100.0]\%$$
9. **Actuator Mapping**:
   $$I_{\text{app}, z}(t) = \left(\frac{u_z(t)}{100.0}\right) \times I_{\max, z} \times \left(\frac{\Delta t}{60}\right)\text{ mm}$$
   $$V_{\text{app}, z}(t) = I_{\text{app}, z}(t) \times \text{Area}_z\text{ Liters}$$
10. **Dynamic Soil-Water Balance Update**:
    $$S_z(t+1) = S_z(t) + W_{\text{inf}, z}(t) - ET_{\text{act}, z}(t) - D_z(t)$$
11. **State Update**: $SM_z(t+1) = \frac{S_z(t+1)}{1000 \cdot Z_{r, z}} \times 100\%$, feeding strictly into step $t+1$.

---

## 4. Physical Distinction: Depth vs Volume

Because zone surface areas differ substantially ($100\text{ m}^2$, $120\text{ m}^2$, $80\text{ m}^2$):
- **Irrigation Depth ($I_{\text{app}, z}$, mm)**: Height of water applied across the field surface. Reflects soil profile deficit replenishment and crop $ET_c$ replacement.
- **Irrigation Volume ($V_{\text{app}, z}$, Liters)**: Physical volumetric quantity of water delivered:
  $$V\text{ [Liters]} = I\text{ [mm]} \times \text{Area [m}^2\text{]}$$
  (Since $1\text{ mm} = 10^{-3}\text{ m}$, $10^{-3}\text{ m} \times 1\text{ m}^2 = 10^{-3}\text{ m}^3 = 1\text{ Liter}$).

System-wide water consumption must be aggregated in Liters ($V_{\text{total}} = \sum V_z$). For depth aggregation, area-weighted average depth is used:
$$I_{\text{weighted}} = \frac{\sum (I_z \cdot \text{Area}_z)}{\sum \text{Area}_z} = \frac{V_{\text{total}}}{\text{Area}_{\text{total}}}$$

---

## 5. Strict Zone Isolation and Independence

Phase 12 guarantees absolute isolation between zones:
1. **Zero Cross-Zone Coupling**: No zone state enters the calculation of another zone's error, stress, demand, or irrigation command.
2. **Perturbation Invariance Verified**:
   - Perturbing Zone 1 initial moisture leaves Zone 2 and Zone 3 trajectories identical within numerical tolerance ($10^{-10}$).
   - Perturbing Zone 2 target setpoint leaves Zone 1 and Zone 3 trajectories strictly invariant.
   - Perturbing Zone 3 crop coefficient $K_c$ leaves Zone 1 and Zone 2 trajectories strictly invariant.

---

## 6. Architectural Boundary: Control Demand vs Supply Allocation

In Phase 12:
- Each zone controller evaluates its **unconstrained agronomic control demand** ($u_z(t)$) independently.
- In the Water Scarcity scenario ($WAF = 0.30$), the controller does **NOT** apply water rationing or priority weighting.
- Shared reservoir constraints, multizone priority scheduling (e.g. Tomato Priority 2, Wheat Priority 1, Maize Priority 3), and constrained water rationing are strictly deferred to **Phase 13 (Water Allocation FIS)**.
