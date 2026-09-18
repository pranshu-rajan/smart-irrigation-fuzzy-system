# Dynamic Soil-Water Balance and Soil Moisture Model Documentation

This document specifies the hydrological, physical, and agronomic principles governing the discrete-time dynamic root-zone soil water balance model for the **Smart Multizone Irrigation System**.

---

## 1. Parameter and Units Table

| Parameter | Symbol | Dimension / Unit | Physical Meaning |
| :--- | :--- | :--- | :--- |
| **Volumetric Soil Moisture** | $\theta$ | $\text{m}^3/\text{m}^3$ (or $\%$) | Volume of water per bulk volume of soil |
| **Working Soil Moisture** | $SM$ | $\%$ | Scaled sensor / control moisture representation ($0 - 100\%$) |
| **Field Capacity** | $FC$ | $\%$ (or $\text{m}^3/\text{m}^3$) | Moisture content retained against gravity after 24–48h drainage |
| **Permanent Wilting Point** | $WP$ | $\%$ (or $\text{m}^3/\text{m}^3$) | Moisture content below which plants can no longer extract water |
| **Saturation Capacity** | $SAT$ | $\%$ (or $\text{m}^3/\text{m}^3$) | Total pore space completely occupied by water |
| **Effective Root Depth** | $Z_r$ | $\text{m}$ | Depth of active root-zone water extraction |
| **Root-Zone Storage** | $S$ | $\text{mm}$ | Equivalent depth of water stored in root zone ($1000 \cdot \theta \cdot Z_r$) |
| **Total Available Water** | $TAW$ | $\text{mm}$ | Plant available water capacity $1000 \cdot (FC - WP) \cdot Z_r$ |
| **Readily Available Water**| $RAW$ | $\text{mm}$ | Water extractable without stress $p \cdot TAW$ |
| **Depletion Fraction** | $p$ | Dimensionless | Crop-specific fraction of TAW extractable without stress (FAO-56 Table 22) |
| **Relative Soil Moisture** | $RSM$ | Dimensionless $[0, 1]$ | Normalized moisture position $\frac{SM - WP}{FC - WP}$ |
| **Moisture Tracking Error**| $e(t)$ | $\%$ | Set-point control error $SM_{\text{target}} - SM(t)$ |
| **Applied Irrigation** | $I$ | $\text{mm/step}$ | External irrigation depth delivered to surface |
| **Effective Precipitation** | $P_{\text{eff}}$| $\text{mm/step}$ | Precipitation delivered to soil surface (from Phase 4) |
| **Infiltration Capacity** | $I_{\max}$| $\text{mm/step}$ | Maximum rate of water entry into soil matrix |
| **Surface Runoff** | $RO$ | $\text{mm/step}$ | Surface water rejected due to infiltration or saturation excess |
| **Infiltrated Water** | $W_{\text{inf}}$| $\text{mm/step}$ | Water successfully entering root zone ($\min(I + P_{\text{eff}}, I_{\max})$) |
| **Crop Evapotranspiration**| $ET_c$ | $\text{mm/step}$ | Potential crop evapotranspiration water loss (from Phase 4) |
| **Actual Evapotranspiration**| $ET_{\text{actual}}$| $\text{mm/step}$ | Actual water extracted (bounded so $S \ge S_{WP}$) |
| **Gravity Drainage** | $D$ | $\text{mm/step}$ | Deep percolation water loss below root zone ($SM > FC$) |
| **Drainage Parameter** | $\alpha_d$ | Dimensionless $[0, 1]$ | Empirical daily/timestep drainage fraction rate |
| **Conservation Residual** | $\epsilon$ | $\text{mm}$ | Water conservation residual error $|S_{\text{init}} + W_{\text{inf}} - ET - D - S_{\text{final}}|$ |

---

## 2. Soil Moisture Representation and Consistency Reconciliation

### 2.1 The Two Scales in the Codebase
The repository contains two parameter contexts:
1. **Empirical USDA Agronomic Database** (`data/soil_database.csv`):
   - Loam: $FC = 28.0\%$, $WP = 14.0\%$, Saturation = $46.0\%$ ($0.28, 0.14, 0.46\text{ m}^3/\text{m}^3$)
   - Sandy: $FC = 18.0\%$, $WP = 8.0\%$, Saturation = $38.0\%$ ($0.18, 0.08, 0.38\text{ m}^3/\text{m}^3$)
   - Clay: $FC = 36.0\%$, $WP = 20.0\%$, Saturation = $52.0\%$ ($0.36, 0.20, 0.52\text{ m}^3/\text{m}^3$)
   These represent natural soil core volumetric moisture fractions measured in laboratories.

2. **Expanded Working Operational Percentage Scale** (`config/defaults.py` & Section 6):
   - Zone 1 (Tomato / Loam): $FC = 70.0\%$, $WP = 25.0\%$, Initial $SM_0 = 55.0\%$, Target = $60.0\%$
   - Zone 2 (Wheat / Sandy): $FC = 60.0\%$, $WP = 18.0\%$, Initial $SM_0 = 42.0\%$, Target = $55.0\%$
   - Zone 3 (Maize / Clay): $FC = 75.0\%$, $WP = 30.0\%$, Initial $SM_0 = 65.0\%$, Target = $65.0\%$
   These represent calibrated sensor output scales ($0 - 100\%$) used in instrumentation dashboards.

### 2.2 Scale-Invariance Through Relative Soil Moisture ($RSM$)
Relative Soil Moisture ($RSM$) is dimensionless and intrinsically normalized:
$$RSM = \frac{SM - WP}{FC - WP}$$
Whether evaluated using physical fractions or working percentages, $RSM$ evaluates identically:
$$\frac{0.55 - 0.25}{0.70 - 0.25} = \frac{55 - 25}{70 - 25} = \frac{30}{45} = 0.6667$$

### 2.3 Internal Conversion Formulation
- If $SM > 1.0$: treated as working percentage ($\theta = SM / 100.0$).
- If $SM \le 1.0$: treated as volumetric fraction ($\theta = SM$).
- Water Storage Depth:
  $$S [\text{mm}] = 1000 \times \theta \times Z_r = 10 \times SM_{\%} \times Z_r$$
- Inverting Storage to Moisture:
  $$\theta = \frac{S [\text{mm}]}{1000 \times Z_r}, \quad SM_{\%} = \frac{S [\text{mm}]}{10 \times Z_r}$$

---

## 3. Total and Readily Available Water

### 3.1 Total Available Water ($TAW$)
The maximum water depth the root zone can store between Field Capacity and Permanent Wilting Point (FAO-56 Eq. 82):
$$TAW = 1000 \times (\theta_{FC} - \theta_{WP}) \times Z_r \quad [\text{mm}]$$

### 3.2 Readily Available Water ($RAW$)
The portion of $TAW$ that can be extracted without causing water stress (FAO-56 Eq. 83):
$$RAW = p \times TAW \quad [\text{mm}]$$
Where $p$ is the crop depletion fraction from FAO-56 Table 22:
- Tomato: $p = 0.40$
- Wheat: $p = 0.55$
- Maize: $p = 0.55$

When soil water depletion exceeds $RAW$ (i.e. $S < S_{FC} - RAW$), plant stomata partially close, transpiration is restricted, and the **Water Stress Indicator** activates.

---

## 4. Hydraulic Fluxes and Constraints

### 4.1 Infiltration Capacity and Surface Runoff
Water entering the soil cannot exceed the hydraulic infiltration rate $I_{\max}$:
$$I_{\max} [\text{mm/step}] = \text{infiltration\_rate\_mm\_h} \times \frac{\Delta t}{60}$$
- Infiltrated water:
  $$W_{\text{inf}} = \min(I + P_{\text{eff}}, I_{\max})$$
- Surface runoff:
  $$RO = \max(0.0, I + P_{\text{eff}} - I_{\max})$$
- Saturation Block: If the soil is at Saturation ($SM \ge SAT$), all incoming water is rejected as runoff ($W_{\text{inf}} = 0, RO = I + P_{\text{eff}}$).

### 4.2 Gravity Drainage / Deep Percolation
Drainage occurs exclusively when root-zone storage exceeds Field Capacity ($S > S_{FC}$):
$$D = \alpha_d \times \max(0.0, S_{\text{temp}} - S_{FC})$$
Where $\alpha_d$ is the soil-specific drainage rate parameter:
- Loam: $\alpha_d = 0.08$
- Sandy: $\alpha_d = 0.18$ (rapid percolation)
- Clay: $\alpha_d = 0.03$ (slow percolation, waterlogging prone)

If storage exceeds Saturation ($S > S_{SAT}$), any water above $S_{SAT}$ drains immediately:
$$D_{\text{sat}} = \max(D, S_{\text{temp}} - S_{SAT})$$

### 4.3 Actual Evapotranspiration Extraction ($ET_{\text{actual}}$)
Plant roots cannot draw moisture below the Permanent Wilting Point ($WP$):
$$S_{\text{available\_to\_ET}} = \max(0.0, S_{\text{after\_inflow}} - S_{WP})$$
$$ET_{\text{actual}} = \min(ET_c, S_{\text{available\_to\_ET}})$$

---

## 5. Discrete Water Conservation Equation

At each discrete timestep $\Delta t = 1\text{ min}$:
$$S(t+1) = S(t) + W_{\text{inf}}(t) - ET_{\text{actual}}(t) - D(t)$$

### Conservation Check:
$$\text{Residual } \epsilon = S(t) + W_{\text{inf}}(t) - ET_{\text{actual}}(t) - D(t) - S(t+1) \equiv 0.0$$
The simulation engine tracks this residual at every single step, guaranteeing exact conservation within machine precision ($< 10^{-10}\text{ mm}$).

---

## 6. Three-Zone Agricultural Testbed Configuration

Each zone maintains a completely independent hydrological state vector:

| Parameter | Zone 1 | Zone 2 | Zone 3 |
| :--- | :--- | :--- | :--- |
| **Assigned Crop** | Tomato | Wheat | Maize |
| **Soil Texture** | Loam | Sandy | Clay |
| **Plot Area** | $100\text{ m}^2$ | $120\text{ m}^2$ | $80\text{ m}^2$ |
| **Root Depth $Z_r$** | $0.70\text{ m}$ | $0.90\text{ m}$ | $1.00\text{ m}$ |
| **Field Capacity $FC$** | $70.0\%$ | $60.0\%$ | $75.0\%$ |
| **Wilting Point $WP$** | $25.0\%$ | $18.0\%$ | $30.0\%$ |
| **Saturation $SAT$** | $85.0\%$ | $78.0\%$ | $90.0\%$ |
| **Initial Moisture $SM_0$** | $55.0\%$ | $42.0\%$ | $65.0\%$ |
| **Initial Storage $S_0$** | $385.0\text{ mm}$ | $378.0\text{ mm}$ | $650.0\text{ mm}$ |
| **Target Moisture** | $60.0\%$ | $55.0\%$ | $65.0\%$ |
| **Total Available Water**| $315.0\text{ mm}$ | $378.0\text{ mm}$ | $450.0\text{ mm}$ |
| **Depletion Fraction $p$**| $0.40$ | $0.55$ | $0.55$ |
| **Readily Available Water**| $126.0\text{ mm}$ | $207.9\text{ mm}$ | $247.5\text{ mm}$ |
| **Infiltration Rate** | $20.0\text{ mm/h}$ | $45.0\text{ mm/h}$ | $5.0\text{ mm/h}$ |
| **Drainage Parameter** | $0.08$ | $0.18$ | $0.03$ |
| **Allocation Priority** | 2 | 1 | 3 |

---

## 7. Assumptions and Limitations

1. **One-Dimensional Uniform Root Zone**: Assumes a single lumped soil layer with depth $Z_r$. Vertical root distribution gradients and multiple soil horizons are not modeled.
2. **Homogeneous Textural Profile**: Soil hydraulic conductivity and porosity are assumed uniform throughout the active root zone.
3. **Piston-Flow Infiltration Model**: Water in excess of the infiltration capacity generates surface runoff; infiltrated water enters root storage instantaneously within the 1-minute epoch.
4. **No Capillary Upflow from Deep Groundwater**: The water table is assumed to be sufficiently deep ($> 3\text{ m}$) such that upward capillary flux is negligible.

---

## 8. Interface with Future Fuzzy Controllers

Phase 5 creates the physical plant model. In Phases 6 through 10, the fuzzy control hierarchy will interface directly with this state:
- **Soil Stress FIS (FIS 1)**: Consumes $RSM(t)$ and $e(t) = SM_{\text{target}} - SM(t)$.
- **Main Irrigation FIS (FIS 4)**: Consumes outputs of FIS 1, FIS 2 (Weather Stress), FIS 3 (Water Demand), and $e(t)$, outputting the physical irrigation depth command $I(t)$.
- **Closed-Loop Feedback**: The irrigation command $I(t)$ feeds into $W_{\text{inf}}(t)$, updating $S(t+1)$, completing the closed loop.
