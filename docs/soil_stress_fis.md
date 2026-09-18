# Phase 7 Documentation: Soil Stress Fuzzy Inference System (SoilStressFIS)

## 1. Overview & Purpose

The **Soil Stress Fuzzy Inference System (`SoilStressFIS`)** is the primary diagnostic subsystem in the hierarchical irrigation architecture. Its objective is to evaluate real-time crop root-zone water stress by synthesizing:
1. **Physical water availability** via Relative Soil Moisture (RSM).
2. **Control tracking deviation** via Moisture Tracking Error ($e(t)$).

The resulting **Soil Stress index** $[0.0, 100.0]\%$ feeds directly into the downstream **Main Irrigation FIS** (Phase 9) to govern closed-loop irrigation scheduling.

```
+-------------------------------------------------------------------------+
|                        SOIL STRESS FIS (Phase 7)                        |
|                                                                         |
|   Relative Soil Moisture (RSM) [0 - 1]                                  |
|   ("How much plant-available water is present?") ────┐                  |
|                                                      ▼                  |
|                                               +---------------+         |
|                                               |  25-Rule      |         |
|                                               |  Mamdani FIS  |──────►  |  Soil Stress [0 - 100]%
|                                               +---------------+         |  ("How severe is the root stress?")
|                                                      ▲                  |
|   Moisture Tracking Error e(t) [-30 to +30]%         │                  |
|   ("How far is moisture from desired target?") ──────┘                  |
+-------------------------------------------------------------------------+
```

---

## 2. Fundamental Semantic Distinctions

To ensure clarity during academic examinations and viva defense, the controller strictly distinguishes three physical/fuzzy concepts:

1. **Relative Soil Moisture (RSM)** answers:
   > *"How much plant-available water is currently stored in the root zone relative to field capacity and wilting point?"*
   - $\text{RSM} = 0.0$: Permanent Wilting Point ($\theta_{\text{wp}}$) — water is held under high tension and cannot be extracted by roots.
   - $\text{RSM} = 1.0$: Field Capacity ($\theta_{\text{fc}}$) — optimal gravitational limit of capillary water.
   - $\text{RSM} > 1.0$: Saturation zone ($\theta_{\text{sat}}$) — risk of hypoxia and root waterlogging.

2. **Moisture Tracking Error ($e(t)$)** answers:
   > *"How far is current soil moisture from the agronomically commanded setpoint?"*
   - Formulation: $e(t) = \theta_{\text{target}} - \theta(t)$.
   - $e(t) > 0$: Moisture deficit (under-watered).
   - $e(t) = 0$: Operating precisely at setpoint.
   - $e(t) < 0$: Moisture surplus (over-watered).

3. **Soil Stress** answers:
   > *"How biologically urgent is the current soil water condition for the crop?"*
   - Range: $0.0\%$ (no water stress, ample root moisture) to $100.0\%$ (critical water depletion / severe wilting danger).

---

## 3. Mathematical Inference Specification

`SoilStressFIS` implements a zero-order Mamdani fuzzy inference pipeline:

### 3.1 Fuzzification
Inputs $(r, e)$ are evaluated against triangular and trapezoidal membership functions:
$$\mu_{A_i}(r) \in [0, 1], \quad \mu_{B_j}(e) \in [0, 1]$$

### 3.2 Antecedent Conjunction (T-Norm)
The rule antecedent uses the Mamdani **minimum** operator:
$$\alpha_k = \min\left(\mu_{A_k}(r), \mu_{B_k}(e)\right)$$

### 3.3 Implication
Mamdani **minimum-truncation** implication clips the output fuzzy set for each rule:
$$\mu_{C_k}'(z) = \min\left(\alpha_k, \mu_{C_k}(z)\right), \quad \forall z \in [0, 100]\%$$

### 3.4 Consequent Aggregation (S-Norm)
Individual rule outputs are aggregated using the **maximum** operator:
$$\mu_{\text{agg}}(z) = \max_{k=1}^K \mu_{C_k}'(z), \quad \forall z \in [0, 100]\%$$

Equivalently, grouping by the four consequent linguistic terms:
$$\beta_L = \max_{\{k \mid C_k = L\}} \alpha_k, \quad L \in \{\text{Low}, \text{Moderate}, \text{High}, \text{Very High}\}$$
$$\mu_{\text{agg}}(z) = \max_L \left(\min(\beta_L, \mu_L(z))\right)$$

### 3.5 Defuzzification
Centroid (Center of Gravity / Area) defuzzification converts $\mu_{\text{agg}}(z)$ to a scalar index $z^*$:
$$z^* = \frac{\int_0^{100} z \cdot \mu_{\text{agg}}(z) \, dz}{\int_0^{100} \mu_{\text{agg}}(z) \, dz} \approx \frac{\sum_{m=1}^M z_m \cdot \mu_{\text{agg}}(z_m)}{\sum_{m=1}^M \mu_{\text{agg}}(z_m)}$$

Where $M = 501$ uniform grid points across $[0, 100]\%$ ($dz = 0.2\%$).

### 3.6 Edge-Case & Zero-Area Fallback
If $\sum_m \mu_{\text{agg}}(z_m) < 10^{-9}$ (empty fuzzy set due to pathological input), the defuzzifier gracefully falls back to $0.0\%$ to prevent division by zero or NaN propagation.

---

## 4. Engineering Rule Base (25 Rules)

The rule matrix exhaustively covers all combinations of the 5 RSM sets $\times$ 5 Moisture Error sets:

| Rule ID | Antecedent: RSM | Antecedent: Moisture Error | Consequent: Soil Stress | Engineering Rationale |
| :---: | :---: | :---: | :---: | :--- |
| **R1** | Very Dry | Large Positive | **Very High** | Soil near wilting point with massive deficit; catastrophic drought stress. |
| **R2** | Very Dry | Positive | **Very High** | Low moisture with persistent deficit; severe water stress. |
| **R3** | Very Dry | Zero | **High** | At wilting point despite meeting target; absolute water scarcity. |
| **R4** | Very Dry | Negative | **High** | High absolute dryness even with local negative error; high stress. |
| **R5** | Very Dry | Large Negative | **Moderate** | Soil is dry but large negative error indicates substantial recent irrigation. |
| **R6** | Dry | Large Positive | **Very High** | Depleted root zone with expanding deficit; emergency replenishment needed. |
| **R7** | Dry | Positive | **High** | Under target and below optimal moisture; significant crop stress. |
| **R8** | Dry | Zero | **Moderate** | Crop is at dry target; moderate stress level. |
| **R9** | Dry | Negative | **Low** | Sufficient water buffer prevents immediate stress. |
| **R10** | Dry | Large Negative | **Low** | Surplus water eliminates stress condition. |
| **R11** | Adequate | Large Positive | **High** | Root moisture dropping fast toward threshold deficit. |
| **R12** | Adequate | Positive | **Moderate** | Mild deficit within buffer capacity; moderate priority. |
| **R13** | Adequate | Zero | **Low** | Ideal target conditions; optimal low-stress transpiration. |
| **R14** | Adequate | Negative | **Low** | Mild excess in root zone; zero water deficit. |
| **R15** | Adequate | Large Negative | **Low** | Substantial moisture buffer; no water stress. |
| **R16** | Wet | Large Positive | **Moderate** | High soil moisture dampens impact of target error. |
| **R17** | Wet | Positive | **Low** | Ample available soil moisture; no stress. |
| **R18** | Wet | Zero | **Low** | Ideal wet conditions; zero stress. |
| **R19** | Wet | Negative | **Low** | Approaching field capacity; zero stress. |
| **R20** | Wet | Large Negative | **Low** | Saturated root zone; zero deficit stress. |
| **R21** | Very Wet | Large Positive | **Low** | High soil storage cushions any demand fluctuation. |
| **R22** | Very Wet | Positive | **Low** | Abundant root water; zero stress. |
| **R23** | Very Wet | Zero | **Low** | Target at field capacity; zero stress. |
| **R24** | Very Wet | Negative | **Low** | Above field capacity; zero deficit stress. |
| **R25** | Very Wet | Large Negative | **Low** | Waterlogged conditions; zero deficit stress. |

---

## 5. API Reference & Usage

### 5.1 Basic Crisp Evaluation

```python
from fuzzy_engine.soil_stress import SoilStressFIS

# Initialize FIS (resolution=501 integration points)
fis = SoilStressFIS()

# Evaluate crisp soil stress
stress = fis.evaluate(rsm=0.35, moisture_error=8.0)
print(f"Soil Stress: {stress:.2f}%")
# Output: Soil Stress: 66.85%
```

### 5.2 Detailed Telemetry Evaluation

```python
# Execute full inference with diagnostic introspection
details = fis.evaluate_detailed(rsm=0.28, moisture_error=8.0)

print("RSM Fuzzification:", details["rsm_membership"])
print("Active Rules Count:", len(details["active_rules"]))
print("Consequent Activations:", details["consequent_activations"])
print("Crisp Soil Stress:", details["soil_stress"])
```

### 5.3 Batch Vectorized Timeseries Evaluation

```python
import numpy as np

# Evaluate 1,440 timesteps across an array
rsm_series = np.linspace(0.8, 0.2, 1440)
error_series = np.linspace(-5.0, 15.0, 1440)

stress_series = fis.evaluate_array(rsm_series, error_series)
assert stress_series.shape == (1440,)
```

---

## 6. Input Validation & Error Handling

1. **Rejection of Invalid Numerics**: Passing `NaN`, `+inf`, or `-inf` immediately raises a descriptive `ValueError`.
2. **Clamping Strategy**: Input values outside the physical universe (e.g. $\text{RSM} = 1.25$ or $e(t) = -35.0\%$) are clamped to universe boundaries $[0.0, 1.0]$ and $[-30.0, 30.0]\%$ before evaluating memberships. Physical simulation variables remain completely untouched.
