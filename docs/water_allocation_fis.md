# Water Allocation Fuzzy Inference System (WaterAllocationFIS)

## 1. Executive Summary & Objective

The **Water Allocation Fuzzy Inference System (`WaterAllocationFIS`)** represents Phase 13 of the Smart Multizone Irrigation and Water Resource Management project. It constitutes the supervisory decision-making layer responsible for distributing scarce, shared water supplies among competing agricultural zones.

Prior to Phase 13 (Phases 11 and 12), zone irrigation commands operated under an implicit assumption of infinite water availability. In Phase 13, the system explicitly introduces the **Shared Water Supply Constraint**, coupling local root-zone feedback loops through a common, physically bounded reservoir/source infrastructure.

```
+-------------------------------------------------------------------------+
|                  SHARED ENVIRONMENTAL DRIVER (Scenario)                 |
+-------------------------------------------------------------------------+
                                    |
       +----------------------------+----------------------------+
       |                            |                            |
       v                            v                            v
  [ ZONE 1 ]                   [ ZONE 2 ]                   [ ZONE 3 ]
Tomato / Loam 100m²         Wheat / Sandy 120m²          Maize / Clay 80m²
       |                            |                            |
       v                            v                            v
Soil / Weather Stress        Soil / Weather Stress        Soil / Weather Stress
       |                            |                            |
       v                            v                            v
  Water Demand                 Water Demand                 Water Demand
       |                            |                            |
       v                            v                            v
Main Irrigation FIS          Main Irrigation FIS          Main Irrigation FIS
       |                            |                            |
       v                            v                            v
Unconstrained Request R1     Unconstrained Request R2     Unconstrained Request R3
       |                            |                            |
       +----------------------------+----------------------------+
                                    |
                                    v
                 +--------------------------------------+
                 |      SHARED WATER ALLOCATION FIS     |
                 |  Inputs: Available Water Supply      |
                 |          Zone Demands (R1, R2, R3)   |
                 |          Zone Stresses (S1, S2, S3)  |
                 |          Zone Priorities (P1, P2, P3)|
                 +--------------------------------------+
                                    |
                                    v
                 +--------------------------------------+
                 |   HARD SUPPLY CONSTRAINT ENFORCEMENT |
                 |     Sum(A_z) <= W_available          |
                 |     A_z <= R_z                       |
                 +--------------------------------------+
                                    |
       +----------------------------+----------------------------+
       |                            |                            |
       v                            v                            v
Allocated Water A1           Allocated Water A2           Allocated Water A3
       |                            |                            |
       v                            v                            v
Physical Application I1      Physical Application I2      Physical Application I3
       |                            |                            |
       v                            v                            v
Zone 1 Soil Water Balance    Zone 2 Soil Water Balance    Zone 3 Soil Water Balance
       |                            |                            |
       +------- State Feedback -----+------- State Feedback -----+
```

---

## 2. Critical Architectural Distinction: Demand vs Allocation

A foundational scientific principle of this hierarchical architecture is the strict separation between **Control Demand** (Layer A) and **Resource Allocation** (Layer B):

1. **Layer A — Main Irrigation FIS (Local Demand)**:
   - **Question Answered**: *"How much water does this specific crop/soil root zone need to eliminate moisture deficit and thermal stress?"*
   - **Inputs**: Soil stress, weather stress, crop water demand, moisture error.
   - **Nature**: Unconstrained, purely physiological and agronomic. It must remain completely uninfluenced by whether the reservoir is full or dry.
   - **Output**: Unconstrained irrigation command / request $R_z(t) \in [0.0, 100.0]\%$.

2. **Layer B — Water Allocation FIS (Supervisory Allocation)**:
   - **Question Answered**: *"Given the available shared water supply and competing claims, how much of the requested water can each zone receive?"*
   - **Inputs**: Available water supply, zone demand, zone stress, zone priority.
   - **Nature**: Resource-constrained, prioritizing critical and high-value crops under scarcity.
   - **Output**: Relative allocation factor $F_z(t) \in [0.0, 100.0]\%$.

3. **Layer C — Deterministic Hard Constraint Enforcement**:
   - **Role**: Mathematical guarantee of physical conservation laws. Fuzzy inference produces intelligent, continuous prioritization tendencies, while deterministic logic guarantees that total allocated volume never exceeds available source capacity:
     $$\sum_{z=1}^{N} A_z(t) \le W_{\text{available}}(t)$$
     $$0 \le A_z(t) \le R_z(t)$$

---

## 3. Variable Universes & Membership Functions

All fuzzy variables utilize centralized definitions from `config/fuzzy_config.json`:

| Variable | Role | Universe | Unit | Linguistic Sets |
| :--- | :---: | :---: | :---: | :--- |
| **`available_water`** | Input | $[0.0, 100.0]$ | % | Very Low, Low, Moderate, High, Very High |
| **`zone_demand`** | Input | $[0.0, 100.0]$ | % | Very Low, Low, Moderate, High, Very High |
| **`zone_stress`** | Input | $[0.0, 100.0]$ | % | Low, Moderate, High, Very High |
| **`zone_priority`** | Input | $[0.0, 100.0]$ | % | Low, Medium, High, Critical |
| **`zone_allocation`** | Output | $[0.0, 100.0]$ | % | None, Low, Moderate, High, Maximum |

### Set Parameterization:
- **`available_water`**:
  - Very Low: $\text{trapmf}(0.0, 0.0, 10.0, 25.0)$
  - Low: $\text{trimf}(15.0, 30.0, 45.0)$
  - Moderate: $\text{trimf}(35.0, 50.0, 65.0)$
  - High: $\text{trimf}(55.0, 70.0, 85.0)$
  - Very High: $\text{trapmf}(75.0, 90.0, 100.0, 100.0)$
- **`zone_demand`**:
  - Very Low: $\text{trapmf}(0.0, 0.0, 10.0, 25.0)$
  - Low: $\text{trimf}(15.0, 30.0, 45.0)$
  - Moderate: $\text{trimf}(35.0, 50.0, 65.0)$
  - High: $\text{trimf}(55.0, 70.0, 85.0)$
  - Very High: $\text{trapmf}(75.0, 90.0, 100.0, 100.0)$
- **`zone_stress`**:
  - Low: $\text{trapmf}(0.0, 0.0, 15.0, 35.0)$
  - Moderate: $\text{trimf}(25.0, 45.0, 65.0)$
  - High: $\text{trimf}(55.0, 75.0, 85.0)$
  - Very High: $\text{trapmf}(75.0, 85.0, 100.0, 100.0)$
- **`zone_priority`**:
  - Low: $\text{trapmf}(0.0, 0.0, 15.0, 35.0)$
  - Medium: $\text{trimf}(25.0, 45.0, 65.0)$
  - High: $\text{trimf}(55.0, 75.0, 85.0)$
  - Critical: $\text{trapmf}(75.0, 85.0, 100.0, 100.0)$
- **`zone_allocation`**:
  - None: $\text{trapmf}(0.0, 0.0, 5.0, 15.0)$
  - Low: $\text{trimf}(10.0, 25.0, 40.0)$
  - Moderate: $\text{trimf}(30.0, 50.0, 70.0)$
  - High: $\text{trimf}(60.0, 75.0, 90.0)$
  - Maximum: $\text{trapmf}(80.0, 90.0, 100.0, 100.0)$

---

## 4. Rule Architecture & Engineering Justification

The rule base comprises **32 hierarchical Mamdani rules** organized across 5 functional layers:

1. **Layer 1: Severe Scarcity & Zero-Demand Safety (Rules 1-5)**:
   - *Rule 1*: IF demand is very low $\to$ allocation is none. (No water allocated without active crop request).
   - *Rules 2-3*: IF supply is very low AND (priority is low/medium OR stress is low/moderate) $\to$ allocation is none. (Eliminates non-essential water consumption during emergency droughts).
   - *Rule 4*: IF supply is very low AND stress is high/very high AND priority is high/critical $\to$ allocation is low. (Provides vital emergency maintenance to prevent crop death).
   - *Rule 5*: IF supply is very low AND demand is high AND priority is low $\to$ allocation is none.
2. **Layer 2: Abundant Supply Satisfaction (Rules 6-11)**:
   - When available water is high or very high, zone demand is granted without artificial restriction.
   - Low demand receives low allocation; high demand receives high/maximum allocation.
3. **Layer 3: Moderate Supply Balancing (Rules 12-18)**:
   - Under moderate reservoir levels, low-priority zones are throttled, while high-priority and stressed crops receive full allocations.
4. **Layer 4: Low Supply & Drought Rationing (Rules 19-26)**:
   - Low-priority zones are cut entirely. Stressed, critical crops receive priority allocation.
5. **Layer 5: Priority & Stress Cross-Modulation (Rules 27-32)**:
   - Explicit handling of extreme combinations (e.g. Critical Priority + Very High Stress commands Maximum allocation whenever water exists).

---

## 5. Physical Shared Supply & Unit Conversion

To eliminate area distortions between different agricultural zones ($100\text{ m}^2$, $120\text{ m}^2$, $80\text{ m}^2$), all supply constraints are evaluated in **Physical Volume (Liters)**:

$$\text{Volume } V_z\text{ [L]} = I_z\text{ [mm]} \times \text{Area}_z\text{ [m}^2\text{]}$$
$$I_z\text{ [mm]} = \frac{V_z\text{ [L]}}{\text{Area}_z\text{ [m}^2\text{]}}$$

The nominal maximum system capacity across the $300\text{ m}^2$ total testbed (at $12.0\text{ mm/h} = 0.2\text{ mm/min}$) is:
$$V_{\max, \text{sys}} = 0.2\text{ mm/min} \times 300\text{ m}^2 = 60.0\text{ Liters/minute}$$

For any timestep $t$:
$$W_{\text{available, L}}(t) = \left(\frac{\text{available\_water}(t)}{100.0}\right) \times 60.0\text{ Liters/min}$$

---

## 6. Deterministic Supply Constraint & Bounded Priority-Weighted Allocation

### 6.1 Audit of Naive Priority Proportional Allocation
A common heuristic for rationing scarce resources under competing claims is single-pass priority weighting:
$$A_{\text{final}, z} = W_{\text{available}} \cdot \frac{w_z \cdot A_{\text{raw}, z}}{\sum_{j=1}^N w_j \cdot A_{\text{raw}, j}}$$

While this formula guarantees that the total allocated volume matches available supply ($\sum A_{\text{final}, z} \le W_{\text{available}}$), it possesses a critical mathematical vulnerability: **it can violate individual zone demand ceilings** ($A_{\text{final}, z} > A_{\text{raw}, z}$).
For instance, if Zone 1 requests a small volume ($A_{\text{raw}, 1} = 1.0\text{ L}$) with a high priority weight ($w_1 = 100$), and Zone 2 requests a large volume ($A_{\text{raw}, 2} = 15.0\text{ L}$) with a low priority weight ($w_2 = 1$), under scarce supply $W_{\text{available}} = 10.0\text{ L}$:
$$A_{\text{final}, 1} = 10.0 \cdot \frac{100 \cdot 1.0}{(100 \cdot 1.0) + (1 \cdot 15.0)} = 10.0 \cdot \frac{100}{115} \approx 8.696\text{ Liters}$$
Zone 1 would receive $8.70\text{ L}$, which is **$770\%$ of its actual requested demand of $1.0\text{ L}$**, creating fictitious artificial demand and starving Zone 2 unnecessarily.

### 6.2 The Corrected Algorithm: Bounded Iterative Weighted Water-Filling
To eliminate this failure mode, Phase 13.1 implements an **Iterative Weighted Capped Allocation (Water-Filling)** algorithm:

```
Algorithm: Bounded Priority-Weighted Allocation
Inputs:
  - raw_requests: {z: A_raw,z} (Liters)
  - priorities: {z: P_z} [0, 100]%
  - available_supply: W_available (Liters)

1. Enforce Non-Negative Ceilings:
   C_z = max(0.0, A_raw,z) for all z ∈ Z
   
2. Invariant A (Zero Supply):
   If W_available ≤ 0: Return {z: 0.0 for all z}

3. Invariant E (Sufficient Supply):
   If Σ C_z ≤ W_available: Return {z: C_z for all z}

4. Iterative Water-Filling under Scarcity (Σ C_z > W_available):
   - Initialize: A_final,z = 0.0 for all z
   - Active uncapped set: U = {z ∈ Z | C_z > 0}
   - Remaining supply: W_rem = W_available
   
   While W_rem > 0 and U is not empty:
     a. Compute active priority sum: W_prio = Σ_{j ∈ U} w_j
     b. Compute proposed incremental shares:
        ΔA_z = W_rem · (w_z / W_prio) for each z ∈ U
     c. Identify saturating zones:
        Capped = {z ∈ U | A_final,z + ΔA_z ≥ C_z}
     d. If Capped is empty:
        For all z ∈ U: A_final,z ← A_final,z + ΔA_z
        W_rem = 0; Break
     e. If Capped is not empty:
        For each z ∈ Capped:
          Δalloc = C_z - A_final,z
          A_final,z = C_z
          W_rem ← W_rem - Δalloc
          Remove z from U
          
5. Final Safety Projection:
   A_final,z = min(C_z, max(0.0, A_final,z)) for all z
   If Σ A_final,z > W_available: shave residual numerical excess
```

### 6.3 Mathematical Invariants Guaranteed
The bounded allocation engine rigorously satisfies all 7 mathematical invariants:
1. **Invariant A (Zero Supply)**: $W_{\text{available}} = 0 \implies A_{\text{final}, z} = 0 \quad \forall z$.
2. **Invariant B (Zero Request)**: $A_{\text{raw}, z} = 0 \implies A_{\text{final}, z} = 0 \quad \forall z$.
3. **Invariant C (Demand Ceiling)**: $0 \le A_{\text{final}, z} \le A_{\text{raw}, z} \le R_z \cdot V_{\max, z} \quad \forall z$.
4. **Invariant D (Supply Ceiling)**: $\sum_{z=1}^{N} A_{\text{final}, z} \le W_{\text{available}}$.
5. **Invariant E (Full Satisfaction)**: $\sum_{z=1}^{N} A_{\text{raw}, z} \le W_{\text{available}} \implies A_{\text{final}, z} = A_{\text{raw}, z} \quad \forall z$.
6. **Invariant F (Priority-Sensitive Scarcity)**: When $\sum A_{\text{raw}, z} > W_{\text{available}}$, water is distributed strictly in proportion to priority weights $w_z$, subject to each zone's individual request ceiling $C_z$.
7. **Invariant G (No Artificial Water Creation)**: $A_{\text{final}, z} > A_{\text{raw}, z}$ is strictly impossible under any combination of inputs.

