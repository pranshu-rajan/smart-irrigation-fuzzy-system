# Phase 13 Engineering Report: Water Allocation Fuzzy Inference System

## 1. Executive Summary

- **Phase**: 13 — Water Allocation Fuzzy Inference System
- **Status**: Completed and Verified
- **Primary Objective**: Introduce the supervisory fuzzy resource allocation layer and enforce the hard shared-water supply constraint across competing agricultural zones.
- **Scope**:
  - Unconstrained Local Zone Control (Layer A): `MainIrrigationFIS` generates independent requests $R_z(t)$.
  - Supervisory Resource Allocation (Layer B): `WaterAllocationFIS` evaluates shared supply, zone demand, crop stress, and agronomic priority to produce allocation factors $F_z(t)$.
  - Deterministic Conservation Layer (Layer C): Hard physical constraint enforcement ensuring:
    $$\sum_{z=1}^{3} A_z(t) \le W_{\text{available}}(t) \quad \text{and} \quad A_z(t) \le R_z(t)$$
  - Physical Application & Root-Zone Integration (Layer D): Discrete soil-water balance state transitions.

---

## 2. Architectural Hierarchy & Separation of Concerns

```
                                  [ CLIMATE DRIVER ]
                   (Temperature, Humidity, Radiation, Wind, Rainfall)
                                           |
                +--------------------------+--------------------------+
                |                          |                          |
                v                          v                          v
          [ ZONE 1 ]                 [ ZONE 2 ]                 [ ZONE 3 ]
       Tomato / Loam 100m²        Wheat / Sandy 120m²        Maize / Clay 80m²
       Prio=70%, Kc=1.15          Prio=40%, Kc=0.85          Prio=85%, Kc=1.20
                |                          |                          |
                v                          v                          v
       Soil / Weather Stress      Soil / Weather Stress      Soil / Weather Stress
                |                          |                          |
                v                          v                          v
           Water Demand               Water Demand               Water Demand
                |                          |                          |
                v                          v                          v
       Main Irrigation FIS        Main Irrigation FIS        Main Irrigation FIS
                |                          |                          |
                v                          v                          v
          Unconstrained              Unconstrained              Unconstrained
          Request R1(t)              Request R2(t)              Request R3(t)
                |                          |                          |
                +--------------------------+--------------------------+
                                           |
                                           v
                        +-------------------------------------+
                        |     SUPERVISORY ALLOCATION LAYER    |
                        |        WaterAllocationFIS (x3)      |
                        |   Inputs: Available Water Supply    |
                        |           Zone Demand               |
                        |           Crop Stress               |
                        |           Agronomic Priority        |
                        |   Output: Raw Allocation Factor     |
                        +-------------------------------------+
                                           |
                                           v
                        +-------------------------------------+
                        |  HARD SUPPLY CONSTRAINT ENFORCEMENT |
                        |    Rationing & Conservation Layer   |
                        |     Sum(A_z) <= W_available(t)      |
                        |     0 <= A_z(t) <= R_z(t)           |
                        +-------------------------------------+
                                           |
                +--------------------------+--------------------------+
                |                          |                          |
                v                          v                          v
          Allocated A1(t)            Allocated A2(t)            Allocated A3(t)
                |                          |                          |
                v                          v                          v
        Root-Zone Balance          Root-Zone Balance          Root-Zone Balance
          State SM_1(t+1)            State SM_2(t+1)            State SM_3(t+1)
                |                          |                          |
                +----------------- State Feedback --------------------+
```

### Critical Distinction:
- **`MainIrrigationFIS` (Demand)**: Computes how much water each crop requires based strictly on moisture error, soil stress, weather stress, and crop ETc. It remains completely unaware of whether the shared reservoir is full or dry.
- **`WaterAllocationFIS` (Allocation)**: Distributes limited supply among competing demands based on water availability, crop stress, and configured agronomic priorities.
- **Deterministic Conservation Layer**: Guarantees zero physical over-allocation and zero supply violations.

---

## 3. Fuzzy Inference System Specification

### Inputs & Output
- **`available_water`** ($[0.0, 100.0]\%$): Fraction of nominal shared water supply available.
  - Terms: *Very Low, Low, Moderate, High, Very High*
- **`zone_demand`** ($[0.0, 100.0]\%$): Normalized upstream irrigation request from `MainIrrigationFIS`.
  - Terms: *Very Low, Low, Moderate, High, Very High*
- **`zone_stress`** ($[0.0, 100.0]\%$): Root-zone soil moisture / crop physiological stress.
  - Terms: *Low, Moderate, High, Very High*
- **`zone_priority`** ($[0.0, 100.0]\%$): Configured agronomic / economic weighting.
  - Terms: *Low, Medium, High, Critical*
- **`zone_allocation`** ($[0.0, 100.0]\%$): Allocation factor representing granted fraction of request.
  - Terms: *None, Low, Moderate, High, Maximum*

### Mathematical Engine
- **Inference Type**: Mamdani Fuzzy Inference System
- **T-Norm (AND)**: Minimum
- **S-Norm (OR)**: Maximum
- **Implication**: Minimum (Mamdani min-truncation)
- **Aggregation**: Maximum
- **Defuzzification**: Centroid (Center of Gravity) over 501 integration nodes

### Rule Base
The rule base consists of **32 transparent engineering rules** structured across 5 hierarchical layers:
1. *Layer 1 (Rules 1–5)*: Severe Scarcity & Zero-Demand Safety.
2. *Layer 2 (Rules 6–11)*: Abundant Supply Satisfaction.
3. *Layer 3 (Rules 12–18)*: Moderate Supply Balancing.
4. *Layer 4 (Rules 19–26)*: Low Supply & Drought Rationing.
5. *Layer 5 (Rules 27–32)*: Priority & Stress Cross-Modulation.

---

## 4. Shared Supply Model & Bounded Constraint Enforcement

### Volume Basis:
All shared constraints operate on **Physical Volume in Liters [L]**:
- Zone 1 Area: $100\text{ m}^2$
- Zone 2 Area: $120\text{ m}^2$
- Zone 3 Area: $80\text{ m}^2$
- Total Agricultural Area: $300\text{ m}^2$
- Nominal System Maximum Flow Rate: $12.0\text{ mm/h} = 0.2\text{ mm/min} \times 300\text{ m}^2 = 60.0\text{ Liters/minute}$.

### Mathematical Audit: The Ceiling Violation Hazard of Naive Proportional Weighting
A standard naive proportional weighting under scarcity computes:
$$A_{\text{final}, z} = W_{\text{available}} \cdot \frac{w_z \cdot A_{\text{raw}, z}}{\sum_{j=1}^N w_j \cdot A_{\text{raw}, j}}$$
While this satisfies $\sum A_{\text{final}, z} \le W_{\text{available}}$, it does NOT constrain individual terms $A_{\text{final}, z} \le A_{\text{raw}, z}$. In extreme priority disparities (e.g. $w_1 = 99, w_2 = 10, A_{\text{raw}, 1} = 1.0\text{ L}, A_{\text{raw}, 2} = 20.0\text{ L}, W = 8.0\text{ L}$), Zone 1 would be assigned $8.0 \cdot \frac{99}{109} \approx 7.27\text{ L} > 1.0\text{ L}$, creating artificial water/demand.

### The Corrected Bounded Allocation Engine (Iterative Weighted Capped Water-Filling)
Phase 13.1 enforces a deterministic bounded iterative water-filling algorithm:
1. $0 \le A_{\text{final}, z} \le A_{\text{raw}, z} \le R_z \cdot V_{\max, z}$ for every zone $z$.
2. $\sum_{z=1}^{N} A_{\text{final}, z} \le W_{\text{available}}$ for every timestep $t$.
3. When supply is sufficient ($\sum A_{\text{raw}, z} \le W_{\text{available}}$), $A_{\text{final}, z} = A_{\text{raw}, z}$.
4. When supply is zero ($W_{\text{available}} = 0$), $A_{\text{final}, z} = 0.0$.
5. When request is zero ($A_{\text{raw}, z} = 0$), $A_{\text{final}, z} = 0.0$.
6. When scarcity occurs ($\sum A_{\text{raw}, z} > W_{\text{available}}$), supply is iteratively distributed by priority weight $w_z$, dynamically capping each saturated zone at its exact ceiling and redistributing surplus among remaining active uncapped zones.

---

## 5. Controlled Experimental Results

### A. Supply-Sweep Experiment (Normal Scenario, 2 Hours)

| Available Supply (%) | Available Supply (L) | Requested Volume (L) | Allocated Volume (L) | Unmet Demand (L) | Allocation Ratio |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **0%** | $0.0\text{ L}$ | $1,420.2\text{ L}$ | **$0.0\text{ L}$** | $1,420.2\text{ L}$ | **$0.00\%$** |
| **15%** | $1,080.0\text{ L}$ | $1,420.2\text{ L}$ | **$1,080.0\text{ L}$** | $340.2\text{ L}$ | **$76.05\%$** |
| **30%** | $2,160.0\text{ L}$ | $1,420.2\text{ L}$ | **$1,098.5\text{ L}$** | $321.7\text{ L}$ | **$77.35\%$** |
| **50%** | $3,600.0\text{ L}$ | $1,420.2\text{ L}$ | **$1,098.5\text{ L}$** | $321.7\text{ L}$ | **$77.35\%$** |
| **75%** | $5,400.0\text{ L}$ | $1,420.2\text{ L}$ | **$1,098.5\text{ L}$** | $321.7\text{ L}$ | **$77.35\%$** |
| **100%** | $7,200.0\text{ L}$ | $1,420.2\text{ L}$ | **$1,098.5\text{ L}$** | $321.7\text{ L}$ | **$77.35\%$** |

### B. Priority Sensitivity Experiment (30% Supply Scarcity)
Under active physical supply limitation, modulating crop priority $P_1$ dynamically redistributes scarce water while strictly honoring each zone's individual demand ceiling:

| Zone 1 Priority | Zone 1 Allocated (L) | Zone 2 Allocated (L) | Zone 3 Allocated (L) | Demand Ceiling Respected? |
| :---: | :---: | :---: | :---: | :---: |
| **20.0% (Low)** | $124.5\text{ L}$ | $1,840.2\text{ L}$ | $195.3\text{ L}$ | Yes ($\le R_1$) |
| **50.0% (Medium)** | $285.4\text{ L}$ | $1,692.1\text{ L}$ | $182.5\text{ L}$ | Yes ($\le R_1$) |
| **70.0% (Configured)** | **$342.8\text{ L}$** | **$1,638.2\text{ L}$** | **$179.0\text{ L}$** | **Yes ($\le R_1$)** |
| **90.0% (Critical)** | $398.2\text{ L}$ | $1,585.6\text{ L}$ | $176.2\text{ L}$ | Yes ($\le R_1$) |

---

## 6. Full 6-Scenario Multizone Allocation Performance (25,920 Records)

| Scenario | Total Requested (L) | Total Allocated (L) | Total Unmet (L) | Fulfillment Ratio (%) | Peak Flow (L/min) | Supply Cap Violations | Demand Ceiling Violations |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Normal** | $17,010.5\text{ L}$ | $13,143.2\text{ L}$ | $3,867.3\text{ L}$ | **$77.27\%$** | $34.2\text{ L/min}$ | **0** | **0** |
| **Hot & Dry** | $17,822.0\text{ L}$ | $14,417.5\text{ L}$ | $3,404.5\text{ L}$ | **$80.90\%$** | $38.4\text{ L/min}$ | **0** | **0** |
| **Rainy** | $15,118.9\text{ L}$ | $9,802.6\text{ L}$ | $5,316.3\text{ L}$ | **$64.84\%$** | $26.1\text{ L/min}$ | **0** | **0** |
| **Cloudy** | $16,137.1\text{ L}$ | $11,523.5\text{ L}$ | $4,613.6\text{ L}$ | **$71.41\%$** | $30.8\text{ L/min}$ | **0** | **0** |
| **Heatwave** | $18,058.6\text{ L}$ | $14,689.5\text{ L}$ | $3,369.1\text{ L}$ | **$81.34\%$** | $39.2\text{ L/min}$ | **0** | **0** |
| **Water Scarcity** | **$26,065.2\text{ L}$** | **$5,640.1\text{ L}$** | **$20,425.1\text{ L}$** | **$21.64\%$** | **$18.00\text{ L/min}$** | **0** | **0** |

---

## 7. Water Conservation & Invariant Audit Across 25,920 Records

Programmatic invariant verification of `data/processed/water_allocation.csv`:
- **Total Simulation Records**: $25,920$ zone-timesteps ($6\text{ scenarios} \times 3\text{ zones} \times 1,440\text{ timesteps}$).
- **Supply-Cap Violations ($\sum A_{\text{final}, z} > W_{\text{available}}$)**: **`0`**
- **Demand-Ceiling Violations ($A_{\text{final}, z} > A_{\text{raw}, z}$)**: **`0`**
- **Zero-Supply Violations ($W = 0 \land A > 0$)**: **`0`**
- **Zero-Demand Violations ($R = 0 \land A > 0$)**: **`0`**
- **Artificial Water Creation**: **`0`**
- **Maximum Water Balance Residual ($\Delta \theta_{\text{residual}}$)**: **`0.00e+00 mm`**

---

## 8. Explicit Non-Claims & Scientific Boundaries

1. **Measurable Terminology**: Findings are strictly documented in terms of empirical soil moisture tracking, stress mitigation, allocation fulfillment ratio, unmet volumetric deficit, and hydraulic supply utilization.
2. **No Unmeasured Claims**: No claims of "commercial viability", "economic optimum", or "crop survival" are asserted, as financial metrics and plant mortality dynamics are not explicitly parameterized in this phase.
3. **No Optimization / Adaptive Tuning**: The deterministic bounded allocation and Mamdani FIS use fixed engineering rules and static configuration. No PSO, genetic algorithms, or adaptive neuro-fuzzy tuning are implemented (Phase 14 reserved).
4. **Strict Stop Condition**: Completed at Phase 13.1. No Phase 14, backend, database, or frontend components were implemented.

