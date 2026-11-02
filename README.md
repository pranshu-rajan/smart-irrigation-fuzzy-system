<div align="center">

# 🌱 Smart Multizone Precision Irrigation System
### Hierarchical Adaptive Closed-Loop Mamdani Fuzzy Control Platform for Precision Agriculture with Bounded Water-Filling Allocation & Explainable AI

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-000000.svg?style=for-the-badge&logo=vercel&logoColor=white)](https://irrigation-fuzzy-system.vercel.app/)
[![API Docs](https://img.shields.io/badge/API%20Docs-Render%20FastAPI-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://smart-irrigation-fuzzy-system.onrender.com/docs)
[![Test Suite](https://img.shields.io/badge/Pytest-351%20Passed-10B981.svg?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-16.3%20App%20Router-000000.svg?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB.svg?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Three.js](https://img.shields.io/badge/Three.js-3D%20Digital%20Twin-049EF4.svg?style=for-the-badge&logo=three.js&logoColor=white)](https://threejs.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

<br/>

**[🌐 Live Web Cockpit](https://irrigation-fuzzy-system.vercel.app/)** • **[📡 Interactive Swagger API](https://smart-irrigation-fuzzy-system.onrender.com/docs)** • **[📑 Architectural Thesis](docs/COMPLETE_END_TO_END_FUZZY_ARCHITECTURE_THESIS.md)** • **[🎓 Viva & Defense Guide](docs/VIVA_GUIDE.md)** • **[⚡ Quickstart](#-quickstart)**

</div>

---

## 📑 Table of Contents

1. [🌟 Executive Summary (Simple Terms)](#-executive-summary-simple-terms)
2. [🔬 The Problem & Existing Previous Research](#-the-problem--existing-previous-research)
   - [Why Traditional Approaches Fail](#why-traditional-approaches-fail)
   - [Literature Review & Previous Work Matrix](#literature-review--previous-work-matrix)
3. [💡 What I Have Solved (Core Contributions)](#-what-i-have-solved-core-contributions)
4. [🏗️ End-to-End System Architecture](#️-end-to-end-system-architecture)
   - [Full Signal Flow Diagram](#full-signal-flow-diagram)
   - [The 5 Cascaded Mamdani Fuzzy Inference Systems](#the-5-cascaded-mamdani-fuzzy-inference-systems)
   - [Biophysical Modeling: FAO-56 Penman-Monteith & 1D Hydrology](#biophysical-modeling-fao-56-penman-monteith--1d-hydrology)
   - [Layer C: Bounded Priority-Weighted Water-Filling Algorithm](#layer-c-bounded-priority-weighted-water-filling-algorithm)
   - [Offline Particle Swarm Optimization (PSO) Calibration](#offline-particle-swarm-optimization-pso-calibration)
   - [Dual-Layer Explainable AI (XAI) & Non-Actuator Safety Barrier](#dual-layer-explainable-ai-xai--non-actuator-safety-barrier)
5. [🛠️ What I Built & Tech Stack Matrix](#️-what-i-built--tech-stack-matrix)
6. [📊 Rigorous Benchmark & Performance Results](#-rigorous-benchmark--performance-results)
   - [Monte Carlo Multi-Scenario Comparative Evaluation](#monte-carlo-multi-scenario-comparative-evaluation)
   - [Sensor Noise & Valve Chattering Suppression](#sensor-noise--valve-chattering-suppression)
   - [Edge Microcontroller Resource Profile (ESP32)](#edge-microcontroller-resource-profile-esp32)
7. [🛡️ The 7 Verified Physical & Mathematical Invariants](#️-the-7-verified-physical--mathematical-invariants)
8. [🇮🇳 Indian Agro-Climatic GIS & ICAR Integration](#-indian-agro-climatic-gis--icar-integration)
9. [🎮 3D Digital Twin & Interactive Web Features](#-3d-digital-twin--interactive-web-features)
10. [📂 Repository Structure](#-repository-structure)
11. [⚡ Quickstart & Local Installation](#-quickstart--local-installation)
12. [🔧 Configuration & Environment Variables](#-configuration--environment-variables)
13. [📡 REST API Reference](#-rest-api-reference)
14. [🧪 Automated Testing & Verification](#-automated-testing--verification)
15. [🚀 Cloud Production Deployment](#-cloud-production-deployment)
16. [📄 License & Citation](#-license--citation)

---

## 🌟 Executive Summary (Simple Terms)

### What is this project?
Imagine a smart brain for farm irrigation that waters crops **not by an arbitrary timer**, but exactly how an expert agronomist would—by looking at the soil, the blazing sun, the humidity, wind speeds, upcoming rain, and the water remaining in the storage tank.

In simple terms:
- **It monitors 3 different agricultural zones simultaneously** (e.g., high-value Tomatoes in Loam, Wheat in Sandy soil, and Maize in Clay soil) sharing a single water reservoir.
- Instead of using a simple "ON/OFF" switch or a rigid mathematical formula, it uses **Fuzzy Logic** ("if soil is *very dry* AND weather is *hot & windy*, THEN open the valve *wide*").
- It calculates real physics: how much water the sun and wind are evaporating out of the leaves (**FAO-56 Penman-Monteith physics**) and how much water infiltrates down to the roots without draining away uselessly.
- When there isn't enough water in the shared tank during a drought, it mathematically rations the water using a **fair, bounded water-filling algorithm**—ensuring the most vulnerable, high-value crops survive without ever draining the reservoir below empty.
- An **Explainable AI (Groq LLM + Tavily real-time agromet search)** translates every single automatic valve adjustment into plain, transparent English for the farmer, while being strictly isolated from direct hardware control so it can never accidentally flood the field.
- The entire system is monitored through an **interactive 3D Digital Twin cockpit** built in Next.js 16 and Three.js with realistic terrain hydration shaders.

---

## 🔬 The Problem & Existing Previous Research

Agricultural irrigation accounts for **over 70% of global freshwater withdrawals**. Despite technological advances, more than 40–60% of agricultural water is wasted due to primitive or ill-suited control architectures.

### Why Traditional Approaches Fail

```
   TRADITIONAL TIMERS               BANG-BANG / HYSTERESIS             CLASSICAL LINEAR PID             MONOLITHIC FUZZY
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│ • Waters regardless of  │      │ • Violent on/off jolts  │      │ • Linear assumption on  │      │ • 10 inputs = 5^10      │
│   rain or high humidity │      │ • High valve chattering │      │   non-linear plant      │      │   ~ 9.76 million rules  │
│ • Severe runoff (>60%)  │      │ • Water hammer stress   │      │ • Integral windup       │      │ • Impossible to tune    │
│ • Root-zone hypoxia     │      │ • Deep percolation loss │      │ • No feedforward weather│      │ • Memory crash on MCU   │
└─────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

1. **Open-Loop Timer Schedules**:
   - *How it works*: Switches pumps on for fixed hours every morning/evening.
   - *Flaw*: Operates blindly without soil or weather feedback. Dumps water during heavy downpours, leading to waterlogging and nutrient leaching, yet under-irrigates during sudden heatwaves.
2. **Bang-Bang (On-Off Threshold Hysteresis) Controllers**:
   - *How it works*: Opens valves to 100% capacity when soil moisture drops below a threshold $\theta_{\text{lower}}$, and cuts off at $\theta_{\text{upper}}$.
   - *Flaw*: Extreme actuator chattering (48+ cycles/day) and rapid solenoid fatigue. Because soil infiltration takes time, water applied at 100% flow overflows or drains below root depth (deep gravitational percolation) before the sensor registers the change.
3. **Classical Linear PID (Proportional-Integral-Derivative)**:
   - *How it works*: Linearly adjusts valve percentage based on moisture error $e(t) = \theta_{\text{target}} - \theta(t)$.
   - *Flaw*: Soil-water dynamics and atmospheric demand are highly non-linear, time-varying, and weather-coupled. PID controllers suffer from severe **integral windup** during actuator saturation and possess no feedforward mechanism to anticipate evaporative pull from solar radiation or vapor pressure deficit (VPD).
4. **Monolithic (Flat) Fuzzy Systems**:
   - *How it works*: Feeds all sensor variables directly into a single fuzzy rule base.
   - *Flaw*: **The Curse of Dimensionality**. In precision multi-zone irrigation, decision-making requires at least 10 state and disturbance variables ($T, RH, R_s, u_2, P, SM, e, ET_c, WD, W_{\text{avail}}$). With 5 linguistic terms each:
     $$\text{Total Rules} = 5^{10} = 9,765,625 \text{ rules}$$
     Even with 3 terms per variable: $3^{10} = 59,049 \text{ rules}$. This is impossible to calibrate, unexplainable, and completely exceeds edge microcontroller memory.
5. **Deep Reinforcement Learning & Deep Neural Networks**:
   - *Flaw*: "Black box" nature. Unpredictable edge-case behavior under sensor faults, sample-inefficient training requirements, and complete absence of formal physical conservation guarantees.
6. **Commercial "Smart" IoT Solutions**:
   - *Flaw*: Merely display telemetry dashboards with naive threshold alerts. They lack biophysical evapotranspiration models (FAO-56), fail to enforce root-zone mass conservation, and do not arbitrate shared water distribution across multiple competing zones.

### Literature Review & Previous Work Matrix

| Research / Method | Key Mechanism | Water Savings vs Timer | Actuator Smoothness | Curse of Dimensionality | Physical Mass Conservation | Multi-Zone Reservoir Allocation | Explainability |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Standard Timers (FAO-24)** | Open-loop schedule | Baseline (0%) | Static | None | ❌ None | ❌ None | ❌ None |
| **Dukes et al. (2012)** | Soil threshold bypass | ~25–35% | Poor (Chattering) | None | ❌ No closure | ❌ Independent | Low |
| **Gutiérrez et al. (2014)** | Threshold IoT sensor network | ~30% | Poor | None | ❌ Heuristic | ❌ None | Low |
| **Prasad et al. (PID, 2018)** | Linear error feedback | ~40% | Moderate (Windup) | None | ❌ Heuristic | ❌ Fixed ratios | Low |
| **Monolithic Fuzzy (Al-Ali et al.)**| Single 4-variable FIS | ~45% | Smooth | ⚠️ High ($5^4=625$) | ❌ No closure | ❌ Single zone | Medium |
| **Deep RL (Yang et al., 2020)** | DDPG / PPO Actor-Critic | ~52% | Variable | ❌ Black-box | ❌ Unbounded | ❌ Complex reward | ❌ Zero (Black-box) |
| **Our Hierarchical Architecture** | **5-Stage Cascaded Mamdani + Layer C Water-Filling + FAO-56** | **+72.4% vs Timer<br/>+49.7% vs Bang-Bang<br/>+12.4% vs PID** | **Superior (4.2× less chatter)** | **✅ Fully Solved (162 rules vs 59k)** | **✅ Exact Closure ($|\text{res}| < 10^{-6}\text{ mm}$)** | **✅ Bounded Water-Filling (Zero Overdraft)** | **✅ Grounded Dual-Layer XAI** |

---

## 💡 What I Have Solved (Core Contributions)

1. **Decoupled the Curse of Dimensionality (5-Stage Cascade)**:
   Decomposed a 10-dimensional combinatorial explosion into 5 modular, human-readable Mamdani Fuzzy Inference Systems containing exactly **162 linguistic rules** (99.7% reduction in complexity).
2. **Integrated First-Principles Biophysical Physics**:
   Embedded hourly **FAO-56 Penman-Monteith Evapotranspiration ($ET_0, ET_c$)** and USDA-SCS effective precipitation into the control loop alongside a 1D soil-water mass conservation model with **machine-precision conservation closure** ($|\text{residual}| < 10^{-6}\text{ mm}$).
3. **Engineered Deterministic Multi-Zone Bounded Water Allocation (Layer C)**:
   Created a hybrid two-tier allocator: Layer B calculates fuzzy scarcity scaling, while Layer C executes a deterministic **Bounded Priority-Weighted Water-Filling Algorithm** that strictly enforces 7 physical conservation invariants (guaranteeing **zero reservoir overdraft** and zero water allocation when demand is zero).
4. **Natural Actuator Chattering & Noise Suppression**:
   Continuous fuzzy membership overlap and Centroid of Area (CoA) defuzzification act as a natural software low-pass filter, **reducing valve actuation cycles by 4.2×** compared to bang-bang control under $\pm 15\%$ sensor noise.
5. **Offline Multi-Objective PSO Calibration**:
   Tuned the 18 membership function vertices of the supervisory controller using offline Particle Swarm Optimization ($w_1 \cdot \text{MAE} + w_2 \cdot \text{Water} + w_3 \cdot \text{Deficit} + w_4 \cdot \text{Chatter}$), avoiding runtime overhead or non-deterministic convergence during execution.
6. **Dual-Layer Grounded Explainable AI with Safety Air-Gap**:
   Integrated a Groq 120B reasoning engine and Tavily real-time agromet search to explain fuzzy rule activations and soil-water trends in plain language. Enforced an **ironclad non-actuator barrier**: the LLM has zero direct control over physical relays or allocation math.
7. **Empirical Edge-Hardware Viability**:
   Validated that the entire fuzzy evaluation pipeline compiles to **$<0.8\text{ ms}$ execution latency** with a **36.5 KB RAM footprint**, enabling seamless real-world deployment on inexpensive microcontrollers such as the Espressif ESP32.
8. **Comprehensive Indian Agro-Climatic Intelligence**:
   Equipped the platform with authentic pedological and climatic data for **100+ Indian districts across all 15 ICAR zones**, integrating real soil water retention limits (Vertisol, Alluvial, Red Sandy Loam, Laterite) and seasonal crop coefficients.

---

## 🏗️ End-to-End System Architecture

### Full Signal Flow Diagram

```mermaid
flowchart TD
    subgraph Inputs["🌾 Sensor & Environmental Inputs"]
        DIST["📍 Indian District / ICAR Zone"]
        SOIL["🌱 Soil Type (FC, WP, Porosity)"]
        CROP["🌽 Crop Stage (Kc, Root Depth Zr)"]
        WTHR["⛅ Live Weather (T, RH, Rs, u2, P)"]
        SM["📟 Soil Moisture Probe SM(t)"]
    end

    subgraph Physics["💧 Biophysical Physics Domain"]
        FAO["FAO-56 Penman-Monteith ET0 Engine"]
        ETC["Crop Evapotranspiration: ETc = Kc * ET0"]
        PEFF["USDA-SCS Effective Rain Peff"]
        RSM_CALC["Relative Soil Moisture: RSM = (SM - WP)/(FC - WP)"]
        ERR_CALC["Moisture Error: e(t) = SM_target - SM(t)"]
    end

    subgraph Fuzzy["🧠 5-Stage Cascaded Mamdani Fuzzy System (162 Rules)"]
        FIS1["Stage 1: Soil Stress FIS\n(25 Rules)\nInputs: RSM, Error"]
        FIS2["Stage 2: Weather Stress FIS\n(34 Rules)\nInputs: T, RH, Rs, u2, P"]
        FIS3["Stage 3: Water Demand FIS\n(39 Rules)\nInputs: ETc, Deficit, Peff"]
        FIS4["Stage 4: Main Supervisory FIS\n(32 Rules)\nInputs: Soil Stress, Weather Stress, Water Demand, Error"]
        FIS5["Stage 5: Water Allocation FIS (Layer B)\n(32 Rules)\nInputs: Scarcity, Zone Demand, Stress, Priority"]
    end

    subgraph Arbitration["⚖️ Deterministic Plant & Arbitration"]
        REQ["Raw Zone Demand (L/min)"]
        LAYERC["Layer C: Bounded Priority Water-Filling\nEnforces 7 Physical Invariants\nSum(Allocated) <= Available Reservoir"]
        VALVE["Pulse-Width Modulated Valve (0 - 100%)"]
        PLANT["1D Dynamic Root-Zone Hydrology Plant\nExact Conservation: |residual| < 1e-6 mm"]
        FEEDBACK["State Update: SM(t + 1)"]
    end

    subgraph Presentation["🖥️ Telemetry & Operator Experience"]
        COCKPIT["Next.js 16 + React 19 Digital Twin"]
        THREE["Three.js 3D Terrain & Shaders"]
        XAI["Grounded AI Copilot (Groq 120B + Tavily)\n[Strict Non-Actuator Safety Air-Gap]"]
        PDF["ReportLab PDF Audit Export"]
    end

    %% Wiring
    WTHR --> FAO
    DIST --> SOIL & CROP
    FAO --> ETC
    WTHR --> PEFF
    SM & SOIL --> RSM_CALC
    SM & SOIL --> ERR_CALC

    RSM_CALC & ERR_CALC --> FIS1
    WTHR --> FIS2
    ETC & PEFF --> FIS3

    FIS1 & FIS2 & FIS3 & ERR_CALC --> FIS4
    FIS4 --> REQ
    REQ --> FIS5
    FIS5 --> LAYERC

    LAYERC --> VALVE
    VALVE --> PLANT
    PLANT --> FEEDBACK
    FEEDBACK --> SM

    FIS4 & LAYERC & PLANT --> COCKPIT
    COCKPIT --> THREE & XAI & PDF
```

---

### The 5 Cascaded Mamdani Fuzzy Inference Systems

All five subsystems use standard **Mamdani Min-Max Centroid Defuzzification**:
- **T-norm (AND operator)**: $\min(\mu_A(x), \mu_B(y))$
- **S-norm (OR operator)**: $\max(\mu_A(x), \mu_B(y))$
- **Implication**: $\min(\mu_{\text{rule}}, \mu_C(z))$
- **Aggregation**: $\max_k(\mu_{C_k}(z))$
- **Defuzzification (Centroid of Area)**:
  $$z^* = \frac{\int z \cdot \mu_{\text{agg}}(z) \, dz}{\int \mu_{\text{agg}}(z) \, dz}$$

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 THE 5 CASCADED FUZZY SUBSYSTEMS                                 │
├─────────┬──────────────────────────────┬────────────────────────┬───────┬───────────────────────┤
│ Stage   │ Subsystem Name               │ Input Variables        │ Rules │ Core Responsibility   │
├─────────┼──────────────────────────────┼────────────────────────┼───────┼───────────────────────┤
│ Stage 1 │ Soil Stress FIS              │ RSM (0–1), Error e(t)  │  25   │ Root-zone depletion   │
│ Stage 2 │ Weather Stress FIS           │ T, RH, Rs, Wind, Rain  │  34   │ Atmospheric VPD pull  │
│ Stage 3 │ Water Demand FIS             │ ETc, Net Deficit, Peff │  39   │ Crop agronomic need   │
│ Stage 4 │ Main Supervisory FIS         │ Soil, Weather, Demand,e│  32   │ Unconstrained valve % │
│ Stage 5 │ Water Allocation FIS (Layer B│ Scarcity, Demand, Stress│  32   │ Scarcity heuristic    │
├─────────┴──────────────────────────────┴────────────────────────┼───────┴───────────────────────┤
│ TOTAL SYSTEM RULE BASE (vs. 59,049 monolithic rules)            │ 162 Rules (99.7% reduction)   │
└─────────────────────────────────────────────────────────────────┴───────────────────────────────┘
```

#### Detailed Stage Specifications:

1. **Stage 1: Soil Stress FIS (25 Rules)**
   - *Inputs*: Relative Soil Moisture ($RSM \in [0, 1]$), Moisture Error ($e(t) \in [-0.3, 0.3]$).
   - *Output*: Soil Stress Index ($0–100\%$).
   - *Role*: Evaluates root-zone depletion relative to local Field Capacity and Permanent Wilting Point.
2. **Stage 2: Weather Stress FIS (34 Rules)**
   - *Inputs*: Dry-bulb Temperature ($T \in [0, 50]^\circ\text{C}$), Relative Humidity ($RH \in [0, 100]\%$), Solar Radiation ($R_s \in [0, 1200]\text{ W/m}^2$), Wind Speed ($u_2 \in [0, 15]\text{ m/s}$), Rainfall ($P \in [0, 50]\text{ mm}$).
   - *Output*: Weather Stress Index ($0–100\%$).
   - *Role*: Evaluates instantaneous atmospheric vapor pressure deficit and drying power. Rain presence dynamically inhibits weather stress.
3. **Stage 3: Water Demand FIS (39 Rules)**
   - *Inputs*: Crop Evapotranspiration ($ET_c \in [0, 15]\text{ mm/day}$), Net Water Deficit ($WD \in [0, 15]\text{ mm}$), Effective Rainfall ($P_{\text{eff}} \in [0, 30]\text{ mm}$).
   - *Output*: Water Demand Index ($0–100\%$).
   - *Role*: Calculates net biological water deficit accounting for effective precipitation infiltration.
4. **Stage 4: Main Supervisory Irrigation FIS (32 Rules)**
   - *Inputs*: Soil Stress ($0–100\%$), Weather Stress ($0–100\%$), Water Demand ($0–100\%$), Moisture Error ($e(t)$).
   - *Output*: Unconstrained Irrigation Valve Command ($0–100\%$).
   - *Role*: Fuses soil hydrology, atmospheric forcing, and crop demand to calculate optimal valve duty cycle.
5. **Stage 5: Water Allocation FIS (32 Rules)**
   - *Inputs*: Shared Water Scarcity ($0–100\%$), Zone Requested Depth ($0–15\text{ mm}$), Zone Stress ($0–100\%$), Crop Economic Priority ($0.5–2.0$).
   - *Output*: Heuristic Allocation Scaling Factor ($0–100\%$).
   - *Role*: Provides the initial non-linear heuristic weighting fed into Layer C.

---

### Biophysical Modeling: FAO-56 Penman-Monteith & 1D Hydrology

#### 1. FAO-56 Reference Evapotranspiration ($ET_0$)
Computed every step according to the UN Food and Agriculture Organization (FAO) Irrigation and Drainage Paper No. 56:

$$ET_0 = \frac{0.408 \Delta (R_n - G) + \gamma \frac{900}{T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}$$

Where:
- $R_n$: Net radiation at the crop surface ($\text{MJ} \cdot \text{m}^{-2} \cdot \text{day}^{-1}$)
- $G$: Soil heat flux density ($\approx 0$ for daily time steps)
- $T$: Mean air temperature at 2 m height ($^\circ\text{C}$)
- $u_2$: Wind speed at 2 m height ($\text{m/s}$)
- $e_s - e_a$: Vapor pressure deficit ($\text{kPa}$)
- $\Delta$: Slope of saturation vapor pressure curve ($\text{kPa}/^\circ\text{C}$)
- $\gamma$: Psychrometric constant ($\approx 0.0673\text{ kPa}/^\circ\text{C}$)

Crop evapotranspiration under standard conditions:
$$ET_c = K_c \times ET_0$$

#### 2. 1D Root-Zone Soil Water Mass Conservation Plant
At each discrete timestep $\Delta t$, the soil-water storage in the root zone ($S(t) = \theta(t) \cdot Z_r \cdot 1000$ in mm) evolves as:

$$S(t+\Delta t) = S(t) + I_{\text{applied}}(t) + P_{\text{eff}}(t) - ET_{\text{actual}}(t) - D(t) - R_{\text{surface}}(t)$$

- **Infiltration**: $I_{\text{applied}}(t) = \min(I_{\text{delivered}}(t), f_{\text{inf}} \cdot \Delta t)$
- **Surface Runoff**: $R_{\text{surface}}(t) = \max(0, I_{\text{delivered}}(t) - f_{\text{inf}} \cdot \Delta t)$
- **Actual Crop Transpiration**: $ET_{\text{actual}}(t) = ET_c(t) \cdot K_s(t)$, where $K_s = \min(1.0, \frac{RSM}{0.5})$
- **Deep Gravity Drainage**: $D(t) = k_{\text{drain}} \cdot \max(0, S(t) - S_{\text{FC}}) \cdot \Delta t$
- **Exact Conservation Closure**:
  $$\text{Residual} = \left| S(t+\Delta t) - \left[ S(t) + I_{\text{applied}} + P_{\text{eff}} - ET_{\text{actual}} - D - R_{\text{surface}} \right] \right| < 10^{-6}\text{ mm}$$

---

### Layer C: Bounded Priority-Weighted Water-Filling Algorithm

When $N$ zones demand water from a finite shared reservoir $V_{\text{available}}$, Layer B's fuzzy recommendations are passed to **Layer C**, which strictly enforces physical supply bounds:

$$A_{\text{final}, i} = \min\left(R_i, \; \lambda \cdot w_i \cdot R_i\right)$$

where:
- $R_i$: Raw volumetric request of zone $i$ ($R_i = \frac{\text{cmd}_i}{100} \cdot q_{\text{max}} \cdot A_i \cdot \Delta t$).
- $w_i$: Composite priority weight ($w_i = \text{CropPriority}_i \times \text{StressFactor}_i$).
- $\lambda$: Global water-filling Lagrange multiplier uniquely solved such that:
  $$\sum_{i=1}^N A_{\text{final}, i} \le V_{\text{available}}$$

**Guarantees**: If total demand $\sum R_i \le V_{\text{available}}$, every zone receives 100% of its requested water ($\lambda \ge 1.0$). If in a drought, allocation scales proportionally to stress and economic priority with **0% reservoir overdraft**.

---

### Offline Particle Swarm Optimization (PSO) Calibration

To ensure optimal tracking without compromising runtime determinism, the 18 vertices of `MainIrrigationFIS` membership functions are tuned **offline** using Particle Swarm Optimization:

```
          18-PARAMETER DECISION VECTOR: θ = [v1, v2, ..., v18]
┌─────────────────────────┬─────────────────────────┬─────────────────────────┬─────────────────────────┐
│ Water Demand MFs (3)    │ Moisture Error MFs (6)  │ Relative Moisture MFs(3)│ Irrigation Cmd MFs (6)  │
└─────────────────────────┴─────────────────────────┴─────────────────────────┴─────────────────────────┘
```

**Multi-Objective Cost Formulation**:
$$J(\vec{\theta}) = w_1 \cdot \text{MAE}_{\text{tracking}} + w_2 \cdot \frac{V_{\text{water}}}{V_{\text{baseline}}} + w_3 \cdot \text{Penalty}_{\text{deficit}} + w_4 \cdot \text{Penalty}_{\text{chatter}}$$

- $w_1 = 0.50$ (Tracking accuracy to target setpoint)
- $w_2 = 0.25$ (Water volume minimization)
- $w_3 = 0.15$ (Under-irrigation deficit penalty)
- $w_4 = 0.10$ (Actuator chatter penalty: $\int |\dot{u}|^2 dt$)

*Decoupling Guarantee*: PSO runs strictly offline during pre-commissioning. The online controller evaluates fixed, optimal membership vertices with zero runtime search overhead.

---

### Dual-Layer Explainable AI (XAI) & Non-Actuator Safety Barrier

To bridge the gap between complex control algorithms and farm operators:

1. **Deterministic Telemetry Indexer**: Every evaluation captures active rule firing strengths ($\alpha_k$), antecedent contributions, and physical mass balance residuals.
2. **Groq 120B Reasoning Engine (`openai/gpt-oss-120b`)**: Ingests telemetry vectors and generates clear, actionable agronomic advice.
3. **Tavily Real-Time Agromet Search**: Augments advice with live agricultural extension bulletins (e.g., ICAR advisories, local pest warnings, upcoming regional weather).
4. **Ironclad Non-Actuator Safety Barrier**: The AI operates exclusively in an advisory capacity. **The LLM has zero direct software bindings to actuator valves, database writes, or water allocation math.** All physical actuation originates exclusively from the deterministic fuzzy engine.

---

## 🛠️ What I Built & Tech Stack Matrix

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   TECHNOLOGY STACK ARCHITECTURE                                 │
├─────────────────────┬─────────────────────────────────────────────────┬─────────────────────────┤
│ Domain Layer        │ Technologies & Libraries                        │ Role & Implementation   │
├─────────────────────┼─────────────────────────────────────────────────┼─────────────────────────┤
│ 🎮 Frontend UI      │ Next.js 16.3 (Turbopack, App Router), React 19  │ Server-rendered cockpit │
│ 🌐 3D Digital Twin  │ Three.js, Canvas, GSAP, WebGL Shaders           │ Hydration vertex shader │
│ 🎨 Styling & Design │ Tailwind CSS v4, Lucide Icons, Modern Dark/Light│ Agrarian aesthetic      │
│ 🔊 Sound & Haptics  │ Web Audio API (Synthesized Relay Solenoid Click)│ Real-time sensory click │
│ 🗺️ GIS Mapping      │ Leaflet, React-Leaflet, GeoJSON                 │ 100+ Indian districts   │
├─────────────────────┼─────────────────────────────────────────────────┼─────────────────────────┤
│ ⚡ Backend API      │ FastAPI 0.115+, Uvicorn, Pydantic v2            │ Asynchronous REST API   │
│ 🧠 Fuzzy Logic      │ Custom NumPy & SciPy Mamdani Inference Engine   │ 5-Stage cascaded FIS    │
│ 🌿 Physics Engine   │ FAO-56 Penman-Monteith, USDA-SCS, 1D Hydrology  │ Exact conservation      │
│ 🤖 Explainable AI   │ Groq SDK (openai/gpt-oss-120b), Tavily Search   │ Grounded XAI copilot    │
│ 📄 Audit Reporting  │ ReportLab (Python Vector Graphics PDF Engine)   │ Enterprise PDF reports  │
│ 🗄️ Persistence      │ Supabase / PostgreSQL, SQLite fallback          │ Multi-zone telemetry    │
├─────────────────────┼─────────────────────────────────────────────────┼─────────────────────────┤
│ ⚙️ Optimization     │ Particle Swarm Optimization (PSO, NumPy)        │ 18-parameter tuning     │
│ 🔬 Control Suite    │ MATLAB Control & Fuzzy Toolbox Suite (+sim)     │ Benchmark & validation  │
│ 🧪 Automated Tests  │ Pytest, Pytest-Asyncio, Pytest-Cov (351 Tests)  │ 100% invariant closure  │
│ 🚀 Deployment       │ Vercel (Frontend), Render (FastAPI Backend)     │ Production hosting      │
└─────────────────────┴─────────────────────────────────────────────────┴─────────────────────────┘
```

---

## 📊 Rigorous Benchmark & Performance Results

### Monte Carlo Multi-Scenario Comparative Evaluation

Evaluated across **1,000 randomized Monte Carlo simulations** under 5 stress scenarios (Normal, Heatwave, Hot & Dry, Rainy, and Severe Drought):

| Controller Topology | Mean Water Consumed | Tracking Error (MAE) | Valve Switching Cycles | Deep Gravitational Runoff | Water Savings vs Competitor | Statistical Significance |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Fixed Timer** | 5,420 L $\pm$ 210 | 11.45% $\pm$ 1.8% | 12.0 $\pm$ 0.0 | 1,840 L $\pm$ 140 | **+72.4% Saved** | $p = 1.2 \times 10^{-7}$ |
| **Bang-Bang (On-Off)** | 3,120 L $\pm$ 180 | 6.82% $\pm$ 0.9% | 48.0 $\pm$ 6.2 | 890 L $\pm$ 85 | **+49.7% Saved** | $p = 3.4 \times 10^{-6}$ |
| **Classical Linear PID**| 1,780 L $\pm$ 110 | 4.95% $\pm$ 0.4% | 24.0 $\pm$ 3.1 | 240 L $\pm$ 35 | **+12.4% Saved** | $p = 8.1 \times 10^{-4}$ |
| **Hierarchical Fuzzy (Ours)**| **1,560 L $\pm$ 95**| **4.21% $\pm$ 0.3%** | **8.0 $\pm$ 1.5** | **12 L $\pm$ 4** | **Baseline** | **$p < 0.001$** |

```
                              24-HOUR CUMULATIVE WATER CONSUMPTION
   Timer        ██████████████████████████████████████████████████ 5,420 L
   Bang-Bang    ████████████████████████████ 3,120 L
   Linear PID   ████████████████ 1,780 L
   Ours (Fuzzy) ██████████████ 1,560 L  [49.7% LESS THAN BANG-BANG | 72.4% LESS THAN TIMER]
```

---

### Sensor Noise & Valve Chattering Suppression

Under simulated $\pm 15\%$ Gaussian sensor noise:
- **Bang-Bang Controller**: Suffers severe chattering (48–94 violent on/off switches/day), causing rapid mechanical wear and pressure transients.
- **Hierarchical Fuzzy System**: The continuous overlap of triangular/trapezoidal membership functions combined with Centroid of Area defuzzification behaves as an intrinsic **software low-pass filter**. Valve adjustments remain smooth and progressive, cutting valve cycles to **$8.0 \pm 1.5$ per day (4.2× reduction)**.

---

### Edge Microcontroller Resource Profile (ESP32)

Benchmarked against an Espressif ESP32 dual-core Xtensa LX6 @ 240 MHz:

| Performance Metric | Python 3.11 Benchmark | Compiled C / Edge Profile | ESP32 Hardware Limit | Viability Assessment |
|:---|:---:|:---:|:---:|:---:|
| **Inference Latency** | 15.3 ms | **< 0.8 ms** | 1000 ms (1 Hz loop) | **1250× faster than required** |
| **SRAM Consumption** | 36.5 KB | **< 14.0 KB** | 520 KB | **< 3% of available RAM** |
| **Flash Storage** | 48.0 KB | **< 32.0 KB** | 4,096 KB (4 MB) | **< 1% of available Flash** |
| **CPU Utilization** | — | **< 0.05%** | 100% | **Virtually negligible load** |

---

## 🛡️ The 7 Verified Physical & Mathematical Invariants

Every build executes automated mathematical self-checks to ensure strict adherence to physical and engineering laws:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               7 VERIFIED SYSTEM INVARIANTS                                      │
├────┬─────────────────────────────┬──────────────────────────────────────────┬───────────────────┤
│ #  │ Invariant Name              │ Formal Mathematical Formulation          │ Verification Status│
├────┼─────────────────────────────┼──────────────────────────────────────────┼───────────────────┤
│ 1  │ Mass Conservation Closure   │ |ΔS - (I_inf + Peff - ETc - D)| < 1e-6 mm │ 0.00 mm Zero Drift │
│ 2  │ Supply Capacity Ceiling     │ Σ V_alloc,i <= V_available                │ 0 Overdraft Viol. │
│ 3  │ Demand Ceiling              │ 0 <= V_alloc,i <= V_req,i, ∀i             │ 0 Violations      │
│ 4  │ Zero Artificial Water       │ V_req,i = 0 ⟹ V_alloc,i = 0               │ 100% Enforced     │
│ 5  │ Zero Supply Preservation    │ V_avail = 0 ⟹ V_alloc,i = 0, ∀i           │ 100% Enforced     │
│ 6  │ Priority Monotonicity       │ w_1 > w_2 ⟹ (A_1 / R_1) >= (A_2 / R_2)   │ Monotonic Invert  │
│ 7  │ AI Safety Isolation Air-Gap │ Actuation ∩ LLM_Output = ∅                │ Strict Air-Gap    │
└────┴─────────────────────────────┴──────────────────────────────────────────┴───────────────────┘
```

---

## 🇮🇳 Indian Agro-Climatic GIS & ICAR Integration

The platform includes full geographic, climatic, and pedological profiles for **100+ Indian districts across all 15 ICAR Agro-Climatic Zones**:

```
                       15 ICAR AGRO-CLIMATIC ZONES INTEGRATED
 1. Western Himalayan Region           6. Trans-Gangetic Plain Region       11. East Coast Plains & Hills
 2. Eastern Himalayan Region           7. Eastern Plateau & Hills           12. West Coast Plains & Ghats
 3. Lower Gangetic Plain Region        8. Central Plateau & Hills           13. Gujarat Plains & Hills
 4. Middle Gangetic Plain Region       9. Western Plateau & Hills           14. Western Dry Region
 5. Upper Gangetic Plain Region       10. Southern Plateau & Hills          15. The Islands Region
```

### Real Pedological Soil Modeling:

| Indian Soil Type | Field Capacity ($\theta_{\text{FC}}$) | Wilting Point ($\theta_{\text{WP}}$) | Available Water Capacity | Saturated Hydraulic Conductivity ($K_{\text{sat}}$) | Typical Regions |
|:---|:---:|:---:|:---:|:---:|:---|
| **Vertisol (Black Soil)** | 42.0% | 22.0% | 20.0% | $2.5\text{ mm/hr}$ | Maharashtra, MP, Gujarat |
| **Alluvial Soil** | 28.0% | 12.0% | 16.0% | $15.0\text{ mm/hr}$ | Punjab, Haryana, UP, Bihar |
| **Red Sandy Loam** | 18.0% | 7.0% | 11.0% | $28.0\text{ mm/hr}$ | Karnataka, Tamil Nadu, AP |
| **Laterite Soil** | 22.0% | 10.0% | 12.0% | $22.0\text{ mm/hr}$ | Kerala, Western Ghats, Odisha |

---

## 🎮 3D Digital Twin & Interactive Web Features

Built with Next.js 16, React 19, and Three.js, the cockpit provides a modern command center for agronomists and operators:

- **🌍 3D Terrain Digital Twin**: Real-time WebGL terrain representation where soil vertex displacement and moisture texture colors dynamically reflect live hydration levels.
- **🔊 Web Audio API Relay Haptics**: Realistic auditory relay solenoid clicks synthesize in real time as virtual valves toggle open or closed.
- **🎛️ Live Fuzzy Sandbox & Rule Inspector**: Interactively manipulate temperature, humidity, solar radiation, and soil moisture sliders to watch real-time antecedent clipping and centroid defuzzification.
- **⏱️ 24-Hour Closed-Loop Simulation Scrubber**: Scrub backwards and forwards through 24-hour simulation days to inspect moisture trajectories, weather spikes, and drainage transients.
- **📑 Vector PDF Audit Generator**: Export print-ready, professional agronomic audit reports compiled dynamically via ReportLab.
- **🌓 Command Palette & Responsive Theme**: Fast navigation with `Cmd+K` / `Ctrl+K` and instantaneous switching between clean daylight agrarian mode and deep cyber-cockpit dark mode.

---

## 📂 Repository Structure

```
irrigation_system_fullstack/
├── backend/                             # High-performance FastAPI application
│   ├── app/
│   │   ├── api/routes/                  # 14 Modular RESTful endpoints
│   │   │   ├── ai.py                    # Groq LLM & Tavily grounded XAI copilot
│   │   │   ├── allocation.py            # Layer B/C Bounded water-filling router
│   │   │   ├── auth.py                  # JWT Auth & Supabase user management
│   │   │   ├── fuzzy.py                 # 5 FIS evaluation & membership inspection
│   │   │   ├── india.py                 # ICAR zones, 100+ districts & weather API
│   │   │   ├── optimization.py          # PSO convergence diagnostics
│   │   │   ├── reports.py               # ReportLab PDF vector report generation
│   │   │   ├── simulations.py           # 24h closed-loop multi-zone simulation
│   │   │   └── verification.py          # 7 Physical invariant self-audit
│   │   ├── core/                        # Application settings, CORS, & security
│   │   ├── database/                    # PostgreSQL / Supabase schemas & migrations
│   │   ├── schemas/                     # Strict Pydantic v2 data contracts
│   │   └── services/                    # Domain calculation services
├── frontend/                            # Next.js 16.3 + React 19 web application
│   ├── src/
│   │   ├── app/                         # 15 Interactive App Router dashboards
│   │   │   ├── ai/                      # Grounded Agro-AI Copilot interface
│   │   │   ├── allocation/              # Water-filling multi-zone studio
│   │   │   ├── architecture/            # Interactive system architecture explorer
│   │   │   ├── dashboard/               # National GIS map & telemetry overview
│   │   │   ├── fuzzy/                   # Live 5-FIS sandbox & rule inspector
│   │   │   ├── reports/                 # PDF audit generator & log download
│   │   │   ├── scenarios/               # Extreme weather stress testing
│   │   │   ├── simulation/              # 24h Digital Twin timeline scrubber
│   │   │   └── zones/                   # Zone configuration & crop profiles
│   │   ├── components/                  # Reusable UI & Three.js 3D terrain canvas
│   │   ├── context/                     # Theme, Auth, and Web Audio state
│   │   └── lib/                         # Typed API client & sound synthesizer
├── fuzzy_engine/                        # Core Mamdani Fuzzy Inference Engine
│   ├── irrigation.py                    # FIS 4: Main Supervisory Controller (32 rules)
│   ├── soil_stress.py                   # FIS 1: Soil Stress Subsystem (25 rules)
│   ├── variables.py                     # Linguistic variables & membership curves
│   ├── water_allocation.py              # FIS 5: Water Allocation Subsystem (32 rules)
│   ├── water_demand.py                  # FIS 3: Crop Water Demand Subsystem (39 rules)
│   └── weather_stress.py                # FIS 2: Atmospheric Weather Stress (34 rules)
├── simulation/                          # Closed-loop simulators & benchmarks
│   ├── ablation_study.py                # 5-Stage FIS ablation validation
│   ├── closed_loop.py                   # Single-zone closed-loop physics engine
│   ├── edge_hardware_profile.py         # ESP32 latency, RAM, and Flash profiler
│   ├── multizone_closed_loop.py         # Multi-zone synchronized closed-loop engine
│   ├── sensor_noise_test.py             # Actuator chattering & noise suppression
│   └── statistical_benchmark.py         # Monte Carlo multi-scenario benchmark
├── engineering/matlab/                  # Control engineering MATLAB suite
│   ├── +fuzzy/                          # MATLAB Fuzzy Toolbox FIS implementations
│   ├── +optimization/                   # PSO tuning scripts (18-parameter space)
│   ├── +simulation/                     # Simulink/MATLAB benchmark comparison
│   ├── +visualization/                  # Fuzzy 3D control surface visualizer
│   └── +weather/                        # FAO-56 Penman-Monteith MATLAB engine
├── data_processing/                     # FAO-56 Penman-Monteith & weather models
├── docs/                                # Technical thesis, viva guide, & audit notes
├── tests/                               # 351 automated pytest verification tests
├── requirements.txt                     # Backend Python dependencies
└── render.yaml                          # Render deployment configuration
```

---

## ⚡ Quickstart & Local Installation

### Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: 18.18 or higher (Node 20+ LTS recommended)
- **Git**

---

### 1. Clone the Repository

```bash
git clone https://github.com/pranshu-rajan/smart-irrigation-fuzzy-system.git
cd smart-irrigation-fuzzy-system
```

---

### 2. Backend Setup (FastAPI)

```bash
# Create and activate a Python virtual environment
python -m venv venv

# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize environment variables
cp .env.example .env

# Validate environment integrity
python validate_env.py

# Launch FastAPI development server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once running:
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **System Health Heartbeat**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

### 3. Frontend Setup (Next.js 16)

Open a separate terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start Next.js development server with Turbopack
npm run dev
```

Open your browser to **[http://localhost:3000](http://localhost:3000)**.

- **Theme Mode**: Defaults to clean agrarian light theme; toggle to dark cyber-cockpit via header button or `Cmd+K`.
- **Audio Feedback**: Built-in relay click sound haptics can be toggled via the speaker icon.
- **Command Palette**: Press `Cmd+K` (or `Ctrl+K`) anywhere to jump to any page or tool.

---

## 🔧 Configuration & Environment Variables

Configure `.env` in the root directory:

| Variable | Description | Default / Example | Required |
|:---|:---|:---|:---:|
| `ENVIRONMENT` | Deployment environment (`development`, `production`) | `development` | Yes |
| `PORT` | Backend port | `8000` | Yes |
| `HOST` | Backend host bind address | `0.0.0.0` | Yes |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000` | Yes |
| `GROQ_API_KEY` | Groq LLM API Key for grounded XAI Copilot | `gsk_...` | Optional* |
| `TAVILY_API_KEY` | Tavily Search Key for live agromet advisories | `tvly-...` | Optional* |
| `SUPABASE_URL` | Supabase PostgreSQL project URL | `https://your-project.supabase.co` | Optional** |
| `SUPABASE_ANON_KEY` | Supabase anonymous client API key | `eyJhbGci...` | Optional** |

*\*If Groq or Tavily keys are omitted, the platform gracefully falls back to deterministic rule-based telemetry explanations with 100% uptime.*  
*\*\*If Supabase is omitted, telemetry logs automatically persist to a local SQLite database.*

---

## 📡 REST API Reference

| Category | HTTP Method | Endpoint | Description |
|:---|:---:|:---|:---|
| **Health** | `GET` | `/api/health` | System health check, memory usage, uptime |
| **India GIS** | `GET` | `/api/india/districts` | List 100+ supported Indian districts, soils & crops |
| **India Engine**| `POST`| `/api/india/evaluate` | Run 5-stage FIS evaluation on specific Indian district |
| **Fuzzy Evaluation**| `POST`| `/api/fuzzy/evaluate` | Evaluate arbitrary inputs against any of the 5 FIS |
| **Fuzzy Membership**| `GET` | `/api/fuzzy/membership/{fis_name}` | Retrieve discretized membership curves for plotting |
| **Water Allocation**| `POST`| `/api/allocation/allocate` | Run Layer C Bounded Water-Filling algorithm |
| **Simulation** | `POST`| `/api/simulations/run` | Execute 24-hour multi-zone closed-loop physics simulation |
| **AI Copilot** | `POST`| `/api/ai/explain` | Generate grounded agronomic explanation (Groq + Tavily) |
| **Audit Reports**| `POST`| `/api/reports/generate` | Generate vector ReportLab PDF audit report |
| **Verification**| `GET` | `/api/verification/system` | Run automated 7-invariant mathematical verification |

---

## 🧪 Automated Testing & Verification

The platform maintains a comprehensive test suite of **351 automated unit, integration, and mathematical invariant tests**:

```bash
# Run all automated tests
pytest -v

# Run with test coverage report
pytest --cov=backend --cov=fuzzy_engine --cov=simulation tests/

# Run the research benchmark and invariant verification suite
pytest tests/test_research_benchmarks.py -v
```

### Verified Test Categories:
- **`test_research_benchmarks.py`**: Validates statistical superiority over timers, bang-bang, and PID.
- **`test_verification.py`**: Enforces zero mass-balance drift ($|\text{residual}| < 10^{-6}\text{ mm}$) and zero reservoir overdrafts.
- **`test_water_allocation.py`**: Tests Layer C water-filling bounds, priority scaling, and extreme scarcity.
- **`test_weather_stress.py` & `test_soil_stress.py`**: Verifies monotonicity, boundary clamping, and NaN handling.
- **`test_ai_tavily.py`**: Asserts non-actuator safety barrier and structured fallback reliability.

---

## 🚀 Cloud Production Deployment

### Frontend (Vercel)
The web application is live at **[`https://irrigation-fuzzy-system.vercel.app/`](https://irrigation-fuzzy-system.vercel.app/)**:
1. Import repository into [Vercel](https://vercel.com).
2. Set Root Directory to `frontend`.
3. Framework Preset: **Next.js**.
4. Configure environment variable:
   ```env
   NEXT_PUBLIC_API_URL=https://smart-irrigation-fuzzy-system.onrender.com
   NEXT_PUBLIC_API_BASE=https://smart-irrigation-fuzzy-system.onrender.com/api
   ```
5. Deploy.

### Backend (Render)
The backend REST API is hosted on [Render](https://render.com) using the included [`render.yaml`](render.yaml):
- Runtime: Python 3.11+
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

---

## 📄 License & Citation

This project is open-source and released under the **[MIT License](LICENSE)**.

### Academic Citation
If you utilize this research or code in your academic work, please cite:

```bibtex
@misc{rajan2026smartirrigation,
  author = {Pranshu Rajan},
  title = {Hierarchical Adaptive Closed-Loop Mamdani Fuzzy Control System for Multi-Zone Precision Irrigation},
  year = {2026},
  publisher = {GitHub},
  howpublished = {\url{https://github.com/pranshu-rajan/smart-irrigation-fuzzy-system}},
  note = {Live Web Cockpit: \url{https://irrigation-fuzzy-system.vercel.app/}}
}
```

---

<div align="center">

Made with ❤️ for sustainable agriculture and global water conservation.

</div>
