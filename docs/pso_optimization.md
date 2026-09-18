# Phase 14 — PSO-Based Optimization of Fuzzy Controller Parameters

## 1. Executive Summary & Optimization Philosophy

The **Particle Swarm Optimization (PSO) Controller Tuning Layer** represents **Phase 14** of the *Smart Multizone Irrigation and Water Resource Management Using Hierarchical Adaptive Fuzzy Control* architecture.

In Phases 0 through 13.1, a complete 5-subsystem hierarchical Mamdani Fuzzy Inference architecture was designed, deployed, and verified:
1. `SoilStressFIS` (Root-zone depletion and moisture error)
2. `WeatherStressFIS` (Atmospheric evaporative forcing)
3. `WaterDemandFIS` (Crop-water deficit and effective rainfall)
4. `MainIrrigationFIS` (Actuator control policy)
5. `WaterAllocationFIS` (Shared-supply constraint arbitration)

While the fuzzy rule bases encapsulate expert agronomic and hydraulic heuristic knowledge, the precise placement of membership function (MF) breakpoints (the semantic partitions across universes of discourse) was initially set through expert intuition. 

Phase 14 introduces a **metaheuristic optimization layer** using continuous **Particle Swarm Optimization (PSO)** to systematically tune the parameters of `MainIrrigationFIS` (the central actuator controller).

```
+=============================================================================+
|                      OFFLINE METAHEURISTIC TUNING (Phase 14)                |
|                                                                             |
|   +-------------------+       Candidate Vector theta in R^18                |
|   |    Continuous     | -------------------------------------> [ Param Space]
|   |    PSO Solver     |                                             |       |
|   | (w, c1, c2, Vmax) | <-------------------------------------      |       |
|   +-------------------+       Composite Fitness J(theta)            v       |
|            ^                                                    [ Repaired ]|
|            |                                                    [  FIS     ]|
|            |                                                        |       |
|            +--------------------------------------------------------+       |
|                                     |                                       |
|             +-----------------------+-----------------------+               |
|             |                       |                       |               |
|             v                       v                       v               |
|     [ Normal 24h ]           [ Hot & Dry 24h ]       [ Rainy 24h / ... ]    |
|   Closed-Loop Simul.       Closed-Loop Simul.      Closed-Loop Simul.       |
|             |                       |                       |               |
|             +-----------------------+-----------------------+               |
|                                     |                                       |
|                                     v                                       |
|                       [ Multi-Objective Evaluator ]                         |
|                         J = 0.40*Ee + 0.30*Ew                               |
|                           + 0.20*Ed + 0.10*Eu                               |
+=============================================================================+
                                      |
                                      v (Optimal theta*)
+=============================================================================+
|                      ONLINE INFERENCE RUNTIME (Phases 10-13)                |
|                                                                             |
|     Sensor Inputs -> Hierarchical Mamdani FIS Engine -> Actuator Pulse      |
|                      (Deterministic Centroid Defuzzification)              |
|                      Execution Latency: < 1.0 ms (Zero Metaheuristic)       |
+=============================================================================+
```

### Architectural Axiom: Strict Offline Separation
A fundamental tenet of industrial process control is maintained:
> **The PSO metaheuristic executes strictly offline as a design-time calibration tool.**
> Under no circumstances does PSO run online or inside the per-minute closed-loop simulation loop. At runtime, the controller evaluates standard Mamdani min-max inference and centroid defuzzification with optimized, frozen membership functions, ensuring sub-millisecond deterministic control latency.

---

## 2. Mathematical Formulation of the Optimization Problem

The optimization problem seeks an optimal 18-dimensional parameter vector $\boldsymbol{\theta}^* \in \Omega \subset \mathbb{R}^{18}$ that minimizes the multi-scenario composite cost functional $J(\boldsymbol{\theta})$:

$$\boldsymbol{\theta}^* = \arg\min_{\boldsymbol{\theta} \in \Omega} J(\boldsymbol{\theta})$$

subject to structural membership ordering and physical universe constraints:

$$\mathbf{L}_k \le \theta_k \le \mathbf{U}_k, \quad \forall k \in \{1, 2, \dots, 18\}$$

$$a_j < b_j < c_j \quad \text{(for triangular sets)}$$

$$a_j \le b_j \le c_j \le d_j \quad \text{(for trapezoidal sets)}$$

### 2.1 Multi-Objective Closed-Loop Fitness Functional

The objective functional $J(\boldsymbol{\theta})$ balances four conflicting engineering goals across $S$ evaluation scenarios:

$$J(\boldsymbol{\theta}) = \frac{1}{|S|} \sum_{s \in S} \left[ w_e E_{e,s}(\boldsymbol{\theta}) + w_w E_{w,s}(\boldsymbol{\theta}) + w_d E_{d,s}(\boldsymbol{\theta}) + w_u E_{u,s}(\boldsymbol{\theta}) \right]$$

with normalized objective weights:

$$w_e = 0.40, \quad w_w = 0.30, \quad w_d = 0.20, \quad w_u = 0.10, \quad \sum w = 1.0$$

#### 1. Moisture Tracking Error Component ($E_e$)
Measures the Root Mean Square Error (RMSE) between actual root-zone soil moisture $\text{SM}(t)$ and target setpoint $\text{SM}_{\text{target}}$, normalized by available soil moisture capacity $(FC - WP)$:

$$E_{e,s} = \min\left(2.0, \, \frac{\text{RMSE}_s}{FC - WP}\right), \quad \text{RMSE}_s = \sqrt{\frac{1}{T}\sum_{t=1}^T \left(\text{SM}(t) - \text{SM}_{\text{target}}\right)^2}$$

#### 2. Water Conservation Component ($E_w$)
Measures total 24-hour volumetric water applied relative to a reference normalization ceiling ($V_{\text{ref}} = 8{,}000\text{ L}$ for $100\text{ m}^2$ tomato):

$$E_{w,s} = \min\left(2.0, \, \frac{V_{\text{applied},s}}{V_{\text{ref}}}\right), \quad V_{\text{applied},s} = \sum_{t=1}^T I_{\text{app}}(t) \cdot A_{\text{zone}}$$

#### 3. Root-Zone Moisture Deficit Penalty ($E_d$)
Severely penalizes prolonged excursions below the critical agronomic threshold $(\text{SM}_{\text{target}} - 3.0\%)$, preventing crop stress:

$$E_{d,s} = \begin{cases} 
\min\left(2.0, \, \frac{\overline{\Delta\text{SM}}_{\text{deficit}}}{FC - WP} \cdot \frac{T_{\text{deficit}}}{T}\right) & \text{if } T_{\text{deficit}} > 0 \\
0.0 & \text{otherwise}
\end{cases}$$

where $T_{\text{deficit}} = \sum_{t=1}^T \mathbf{1}_{\{\text{SM}(t) < \text{SM}_{\text{target}} - 3.0\}}$.

#### 4. Actuator Smoothness and Chatter Penalty ($E_u$)
Penalizes high-frequency command jitter and aggressive valve cycling to preserve physical actuator lifespan:

$$E_{u,s} = \min\left(2.0, \, \frac{\frac{1}{T-1}\sum_{t=2}^T |u(t) - u(t-1)|}{50.0\%}\right)$$

---

## 3. The 18-Dimensional Tunable Parameter Space

To ensure physical interpretability and avoid the curse of dimensionality, optimization is restricted to 18 key transition breakpoints across the 4 input/output variables of `MainIrrigationFIS`:

| # | Variable | Fuzzy Set | Parameter Description | Baseline | Lower Bound | Upper Bound |
|---|---|---|---|---|---|---|
| 0 | `moisture_error` | `negative` | Right shoulder transition | -2.00 | -10.00 | -0.50 |
| 1 | `moisture_error` | `zero` | Triangle lower foot $a$ | -4.00 | -12.00 | -1.00 |
| 2 | `moisture_error` | `zero` | Triangle upper foot $c$ | 4.00 | 1.00 | 12.00 |
| 3 | `moisture_error` | `positive` | Triangle peak $b$ | 6.00 | 2.00 | 15.00 |
| 4 | `moisture_error` | `large_positive` | Left shoulder transition | 8.00 | 4.00 | 20.00 |
| 5 | `soil_stress` | `low` | Right shoulder transition | 30.00 | 15.00 | 45.00 |
| 6 | `soil_stress` | `moderate` | Triangle peak $b$ | 45.00 | 30.00 | 60.00 |
| 7 | `soil_stress` | `high` | Triangle peak $b$ | 70.00 | 55.00 | 85.00 |
| 8 | `soil_stress` | `very_high` | Left shoulder transition | 80.00 | 65.00 | 92.00 |
| 9 | `water_demand` | `very_low` | Right shoulder transition | 25.00 | 10.00 | 40.00 |
| 10 | `water_demand` | `low` | Triangle peak $b$ | 35.00 | 20.00 | 50.00 |
| 11 | `water_demand` | `moderate` | Triangle peak $b$ | 55.00 | 40.00 | 70.00 |
| 12 | `water_demand` | `high` | Triangle peak $b$ | 75.00 | 60.00 | 85.00 |
| 13 | `water_demand` | `very_high` | Left shoulder transition | 80.00 | 65.00 | 92.00 |
| 14 | `irrigation_command` | `off` | Right shoulder transition | 5.00 | 1.00 | 15.00 |
| 15 | `irrigation_command` | `low` | Triangle peak $b$ | 25.00 | 15.00 | 40.00 |
| 16 | `irrigation_command` | `medium` | Triangle peak $b$ | 50.00 | 35.00 | 65.00 |
| 17 | `irrigation_command` | `high` | Triangle peak $b$ | 75.00 | 60.00 | 85.00 |

### 3.1 Normalization and Deterministic Repair
Particles navigate within the continuous unit hypercube $[0, 1]^{18}$ via min-max affine mapping:

$$\hat{\theta}_k = \frac{\theta_k - L_k}{U_k - L_k} \in [0, 1]$$

Prior to constructing the fuzzy membership sets, candidate vectors are deterministically repaired to strictly satisfy linguistic monotonic ordering:
- Triangular sets enforce $a_j + \epsilon \le b_j \le c_j - \epsilon$ ($\epsilon = 0.20$).
- Trapezoidal sets enforce $a_j \le b_j \le c_j \le d_j$.
- Semantic overlap between adjacent sets is strictly bounded to prevent dead zones or complete detachment.

---

## 4. Particle Swarm Optimization Dynamics

The swarm evolves according to the standard Clerc-Kennedy constriction-equivalent velocity update:

$$\mathbf{v}_i(t+1) = w \cdot \mathbf{v}_i(t) + c_1 r_1 (\mathbf{p}_{i,\text{best}} - \mathbf{x}_i(t)) + c_2 r_2 (\mathbf{g}_{\text{best}} - \mathbf{x}_i(t))$$

$$\mathbf{x}_i(t+1) = \mathbf{x}_i(t) + \mathbf{v}_i(t+1)$$

### Hyperparameter Specifications:
- **Inertia Weight ($w$):** $0.729$ (balances exploration and exploitation).
- **Cognitive Acceleration ($c_1$):** $1.494$ (attraction toward personal best).
- **Social Acceleration ($c_2$):** $1.494$ (attraction toward global swarm best).
- **Velocity Clamping ($V_{\max}$):** $0.20 \times (\mathbf{U} - \mathbf{L})$ (prevents swarm explosion).
- **Boundary Dynamics:** Hard position reflection with velocity reversal and dampening ($\mathbf{v}_d \leftarrow -0.5 \mathbf{v}_d$) when hitting boundary walls.
- **Swarm Size ($N$):** 16–20 particles.
- **Max Iterations ($T_{\max}$):** 20–30 iterations.
- **PRNG Seed:** Deterministic seed ($42$) for bit-exact reproducibility.

---

## 5. Scenario Generalization Strategy

To avoid overfitting to a single weather condition, optimization is structured around a strict **Training / Validation Scenario Partition**:

### Training Partition (Evaluated during PSO search):
1. **Normal:** Representative diurnal cycle, moderate evaporative demand.
2. **Hot & Dry:** High temperature, low humidity, elevated $ET_0$.
3. **Rainy:** High precipitation, reduced irrigation requirement, drainage risk.
4. **Cloudy:** Low solar irradiance, depressed $ET_0$, slow depletion.

### Validation Partition (Unseen during PSO search):
5. **Heatwave:** Extreme atmospheric stress ($T_{\max} > 38^\circ\text{C}$), high evapotranspiration.
6. **Water Scarcity:** Sustained supply drought testing conservation and deficit mitigation.

---

## 6. Non-Destructive Storage Architecture

In accordance with strict project guidelines, the baseline configuration is completely immutable:
- `config/fuzzy_config.json` is **never modified** and remains the permanent reference baseline.
- PSO-optimized parameters are serialized to `config/fuzzy_optimized_pso.json` with comprehensive audit metadata, objective weights, and baseline vs. optimized fitness scores.
- Convergence telemetry is logged per iteration to `data/processed/pso_convergence.csv`.
