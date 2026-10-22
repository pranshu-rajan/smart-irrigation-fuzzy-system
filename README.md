# Smart Multizone Irrigation & Water Resource Management Platform
### Hierarchical Adaptive Fuzzy Control (HAFC) & Digital Twin Ecosystem

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.3.5_(Turbopack)-000000.svg?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Three.js](https://img.shields.io/badge/Three.js-WebGL_3D-black.svg?style=flat&logo=three.js&logoColor=white)](https://threejs.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v4-38B2AC.svg?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Test Suite](https://img.shields.io/badge/Tests-300_Passed-10B981.svg?style=flat&logo=pytest&logoColor=white)](https://docs.pytest.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat)](LICENSE)

> **Academic Foundation**: B.Tech 3rd-Year Electronics & Instrumentation Engineering / Fuzzy Systems.  
> **Core Principle**: The **Fuzzy Control System** provides the deterministic, mathematical, and control-theoretic foundation of this platform. It is not replaced by black-box machine learning or crude hysteresis thresholds.

---

## 1. Executive Summary & Problem Context

Agricultural irrigation accounts for approximately **70% of global freshwater withdrawals**. Conventional irrigation strategies operate either via open-loop timers or crude hysteresis thresholds (bang-bang switching). These approaches lead to excessive water waste, deep nutrient percolation, and crop stress resulting from over- or under-irrigation.

This project delivers a production-grade, closed-loop **Hierarchical Adaptive Mamdani Fuzzy Control Architecture (HAFC)** coupled with a **real-time 3D WebGL Digital Twin**, **interactive 24-hour simulation playback**, and a **National-Scale Indian GIS Engine** spanning 15 ICAR agro-climatic zones and 700+ districts.

### Key Capabilities
- **Physics-Based Evapotranspiration**: Dynamic FAO-56 Penman-Monteith reference evapotranspiration ($ET_0$) driven by solar radiation, temperature, relative humidity, and wind speed.
- **Hierarchical 5-FIS Control**: Decomposes complex multidimensional decisions into 5 modular Mamdani Fuzzy Inference Systems to prevent rule-base explosion.
- **Strict Conservation Constraints**: Closed-loop 1D soil-water mass balance with physical bounds ($WP \le SM \le FC$) and guaranteed $0.00\text{ mm}$ mathematical residual closure.
- **Supervisory Resource Allocation**: Deterministic water-filling algorithm with priority weighting, guaranteeing zero supply violations under severe reservoir scarcity.
- **Living 3D WebGL Digital Twin**: Real-time Three.js field topology with dynamic soil hydration shaders, camera slerp interpolation, and proportional emitter spray.
- **Simulation Playback Engine**: Scrubbable 24-hour ($1440\text{ min}$) timeline with variable speeds ($1\times$ to $30\times$), diurnal curve modeling, and live solenoid actuator telemetry.
- **2026 UI Design System**: Clean, light agronomy theme by default with seamless toggle to dark cyber-cockpit mode, custom frosted glassmorphism, Web Audio synthesized haptic feedback, and a global keyboard command palette (`Cmd+K` / `Ctrl+K`).
- **Explainable AI Advisory**: Grounded RAG agronomic copilot powered by Groq LLM and live web intelligence (Tavily), strictly bounded as an explanatory layer.

---

## 2. Control System Architecture

The platform implements a closed-loop hierarchical topology that separates local zone dynamics from supervisory resource allocation:

```
                         SMART MULTIZONE
                        IRRIGATION SYSTEM
                               │
                               ▼
                        WEATHER MODEL
                  Temp, Humidity, Solar,
                     Wind, Rainfall
                               │
                               ▼
                     WEATHER STRESS FIS
                               │
                               ├──────────────────────┐
                               ▼                      ▼
                        ZONE INFORMATION       ET0 / ETC MODEL
                  Crop, Soil, Area, FC, WP     ET0, Kc, ETc,
                               │               Effective Rain,
                               ▼               Water Demand
                         SOIL DYNAMICS                │
                         Soil Moisture                ▼
                               │               WATER DEMAND FIS
                               ▼                      │
                        SOIL STRESS FIS               │
                               │                      │
                               ├──────────────────────┘
                               ▼
                     MAIN IRRIGATION FIS
           Soil Stress + Weather Stress +
           Water Demand + Moisture Error
                               │
                               ▼
                      Irrigation Demand
                               │
                               ▼
                    WATER ALLOCATION FIS
            Available Water + Zone Demand
            + Zone Stress + Zone Priority
                               │
                  ┌────────────┼────────────┐
                  ▼            ▼            ▼
                ZONE 1       ZONE 2       ZONE 3
                  │            │            │
                  └────────────┼────────────┘
                               ▼
                     SOIL WATER MODEL
                               │
                               ▼
                     UPDATED SOIL MOISTURE
                               │
                               └──────► FEEDBACK LOOP (1-Minute Timestep)
```

---

## 3. The 5 Hierarchical Fuzzy Inference Systems (FIS)

To eliminate the combinatorial curse of dimensionality ($5^4 = 625$ rules in a monolithic design), the system partitions decision-making into 5 modular Mamdani FIS layers using **minimum implication**, **maximum aggregation**, and **centroid defuzzification**:

| FIS Subsystem | Input Parameters | Linguistic Universe | Output Variable | Defuzzification |
| :--- | :--- | :--- | :--- | :--- |
| **1. Soil Stress FIS** | Soil Moisture ($SM$), Moisture Error ($e(t)$) | $SM$: Very Dry, Dry, Moderate, Wet, Very Wet<br>Error: Negative, Zero, Positive | Soil Stress ($0 \to 1$) | Centroid |
| **2. Weather Stress FIS** | Air Temp ($T$), Relative Humidity ($RH$), Solar Radiation ($R_s$), Wind ($u_2$), Rainfall ($P$) | Temp, Humidity, Solar, Wind (4-5 sets each)<br>Rainfall: None, Light, Moderate, Heavy | Weather Stress ($0 \to 1$) | Centroid |
| **3. Water Demand FIS** | Crop Evapotranspiration ($ET_c$), Soil Moisture Deficit, Effective Rain ($P_{\text{eff}}$) | $ET_c$: Low, Moderate, High<br>Deficit: None, Low, High<br>Rain: None, Moderate, Heavy | Water Demand ($0 \to 1$) | Centroid |
| **4. Main Irrigation FIS** | Soil Stress, Weather Stress, Water Demand, Moisture Error | Stress/Demand: Low, Medium, High<br>Error: Neg, Zero, Pos | Irrigation Request ($0 \to 100\%$) | Centroid |
| **5. Supervisory Allocation FIS** | Total Available Reservoir, Zone Demands, Zone Stresses, Crop Priorities | Resource Availability, Relative Urgency, Priority Weighting | Bounded Zone Volume ($L$) | Constrained Water-Filling |

---

## 4. Mathematical Foundations

### 4.1 FAO-56 Penman-Monteith Evapotranspiration
Reference crop evapotranspiration $ET_0$ ($\text{mm}\cdot\text{day}^{-1}$) is computed using the standard FAO-56 equation:

$$ET_0 = \frac{0.408 \Delta (R_n - G) + \gamma \frac{900}{T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}$$

Where:
- $R_n$: Net radiation at crop surface ($\text{MJ}\cdot\text{m}^{-2}\cdot\text{day}^{-1}$)
- $G$: Soil heat flux density ($\text{MJ}\cdot\text{m}^{-2}\cdot\text{day}^{-1}$, modeled near 0 for daily steps)
- $T$: Mean air temperature at 2 m ($^\circ\text{C}$)
- $u_2$: Wind speed at 2 m ($\text{m}\cdot\text{s}^{-1}$)
- $e_s - e_a$: Vapor pressure deficit ($\text{kPa}$)
- $\Delta$: Slope of saturation vapor pressure curve ($\text{kPa}\cdot^\circ\text{C}^{-1}$)
- $\gamma$: Psychrometric constant ($\text{kPa}\cdot^\circ\text{C}^{-1}$)

Crop evapotranspiration:
$$ET_c = K_c \times ET_0$$

### 4.2 Relative Soil Moisture & Error State
- **Normalized Relative Soil Moisture ($RSM$)**:
  $$RSM = \frac{SM(t) - WP}{FC - WP}$$
- **Closed-Loop Moisture Error**:
  $$e(t) = SM_{\text{target}} - SM(t)$$

### 4.3 Discrete Soil-Water Mass Balance
For discrete simulation step $t \to t+1$ ($\Delta t = 1\text{ min}$):

$$SM(t+1) = SM(t) + I(t) + P_{\text{eff}}(t) - ET_c(t) - D(t)$$

Subject to boundary conservation:
$$WP \le SM(t) \le FC$$

Where $D(t) = \max(0, SM(t) + I(t) + P_{\text{eff}}(t) - ET_c(t) - FC)$ represents deep percolation drainage beyond field capacity.

### 4.4 Supervisory Bounded Water-Filling Allocation
When total reservoir supply $W_{\text{avail}}$ is insufficient to satisfy total demand $\sum_i D_i$:

$$\text{Alloc}_i = \min\left(D_i, \; W_{\text{avail}} \cdot \frac{w_i}{\sum_j w_j}\right), \quad w_i = f(\text{Stress}_i, \text{Priority}_i)$$

Subject to hard invariants:
1. **Supply-Cap Invariant**: $\sum_{i=1}^N \text{Alloc}_i \le W_{\text{avail}}$
2. **Demand-Ceiling Invariant**: $\text{Alloc}_i \le D_i \quad \forall i$
3. **Zero Supply Invariant**: $W_{\text{avail}} = 0 \implies \text{Alloc}_i = 0 \quad \forall i$

---

## 5. Agricultural Zone Specifications

The system ships with default agricultural zones covering distinct soil hydrologies and crop growth stages:

| Zone | Crop Type | Soil Texture | Area ($m^2$) | Field Capacity ($FC$) | Wilting Point ($WP$) | Growth Stage | Base $K_c$ | Target $SM$ |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Zone 1** | Tomato | Sandy Loam | 100 | 0.28 | 0.14 | Mid-Season | 1.15 | 0.24 |
| **Zone 2** | Wheat | Loamy Sand | 120 | 0.18 | 0.08 | Vegetative | 0.85 | 0.15 |
| **Zone 3** | Maize | Clay Loam | 80 | 0.36 | 0.20 | Tasseling | 1.20 | 0.31 |

All parameters are dynamically configurable via `config/config.json` and validated through `backend/app/schemas/`.

---

## 6. Repository Structure

```
irrigation_system_fullstack/
├── backend/                        # FastAPI REST service & core engines
│   └── app/
│       ├── main.py                 # FastAPI application entrypoint & middleware
│       ├── api/routes/             # Modular REST route handlers
│       │   ├── fuzzy.py            # FIS evaluation endpoints
│       │   ├── simulation.py       # Closed-loop simulation execution
│       │   ├── allocation.py       # Multi-zone water allocation
│       │   ├── optimization.py     # PSO parameter tuning
│       │   ├── india.py            # National India GIS & weather data
│       │   ├── ai.py               # Groq LLM agronomy copilot
│       │   └── reports.py          # PDF generation & CSV export
│       ├── database/               # Supabase & SQLite persistence
│       │   └── migrations/         # PostgreSQL schema & RLS policies
│       ├── schemas/                # Pydantic v2 input/output schemas
│       └── services/               # Core business & computation logic
├── frontend/                       # Next.js 16 (App Router) + React 19 UI
│   ├── src/
│   │   ├── app/                    # 15 interactive application routes
│   │   │   ├── page.tsx            # End-to-End Architecture Studio
│   │   │   ├── dashboard/          # National GIS & FIS Dashboard
│   │   │   ├── simulation/         # 1440m Playback & Digital Twin
│   │   │   ├── fuzzy/              # 5 FIS Diagnostics & Membership Viewers
│   │   │   ├── allocation/         # Water-Filling Allocation Sandbox
│   │   │   ├── optimization/       # PSO Parameter Convergence Studio
│   │   │   ├── scenarios/          # 6 Environmental Benchmark Scenarios
│   │   │   ├── zones/              # Soil Hydrology & Crop Profiles
│   │   │   ├── ai/                 # Grounded AI Advisory Copilot
│   │   │   ├── reports/            # PDF Audit Reports & Telemetry
│   │   │   └── globals.css         # 2026 Design Tokens (Light/Dark)
│   │   ├── components/             # Reusable engineering components
│   │   │   ├── DigitalTwin3D.tsx   # Three.js WebGL Living Twin
│   │   │   ├── SimulationScrubberBar.tsx # 24h Playback Scrubber
│   │   │   ├── CommandPalette.tsx  # Global Cmd+K Search Palette
│   │   │   ├── Sidebar.tsx         # Responsive Cockpit Navigation
│   │   │   └── TopHeader.tsx       # Live Telemetry & Theme Switcher
│   │   ├── context/                # Theme, Auth, & Sidebar Contexts
│   │   ├── hooks/                  # useSimulationPlayback timeline hook
│   │   └── lib/                    # API client & audio haptic engine
├── fuzzy_engine/                   # Scikit-Fuzzy core membership & FIS logic
├── simulation/                     # 24-hr closed-loop physics simulation
├── optimization/                   # Offline Particle Swarm Optimization (PSO)
├── data_processing/                # Weather generator & FAO-56 calculator
├── config/                         # System JSON configs & agronomic constants
├── docs/                           # 24 comprehensive mathematical thesis docs
├── tests/                          # 300 automated pytest test cases
└── requirements.txt                # Python production dependencies
```

---

## 7. Getting Started

### 7.1 Prerequisites
- Python 3.11+
- Node.js 18.18+ (or Node 20+)
- Git

### 7.2 Backend Setup (FastAPI)
```bash
# Clone the repository
git clone https://github.com/pranshu-rajan/smart-irrigation-fuzzy-system.git
cd smart-irrigation-fuzzy-system

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server (runs on port 8000)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 7.3 Frontend Setup (Next.js 16)
```bash
# In a separate terminal, navigate to the frontend directory
cd frontend

# Install dependencies
npm ci

# Start Next.js development server with Turbopack (runs on port 3000)
npm run dev
```
Open `http://localhost:3000` in your browser.

- **Theme**: Launches in clean, light agronomy mode by default. Click the Moon icon in the top header or use `Cmd+K` to toggle the dark cyber-cockpit mode.
- **Audio Feedback**: Synthesized relay clicks and haptics are enabled by default and can be toggled via the speaker icon in the header.
- **Keyboard Navigation**: Press `Cmd+K` (or `Ctrl+K`) anywhere to open the global command palette.

---

## 8. Automated Testing & Verification

The test suite validates every layer of the platform across 300 automated tests:

```bash
# Run the complete test suite
pytest -v

# Run with coverage report
pytest --cov=backend --cov=fuzzy_engine --cov=simulation tests/
```

### Verification Invariant Matrix

| Verification Criterion | Mathematical / Engineering Invariant | Test Status |
| :--- | :--- | :--- |
| **Full Regression Suite** | 300 automated tests covering all 5 FIS and closed loops | **300 Passed, 0 Failed** |
| **Water Balance Residual** | 1D soil mass balance residual: $\vert \Delta SM - (I + P_{\text{eff}} - ET_c - D) \vert < 10^{-6}\text{ mm}$ | **Exact $0.00\text{ mm}$ closure** |
| **Supply-Cap Invariant** | Total allocation under scarcity: $\sum \text{Alloc}_i \le W_{\text{avail}}$ | **0 violations across 1,000 cases** |
| **Demand-Ceiling Invariant** | No zone receives more than requested: $\text{Alloc}_i \le D_i$ | **0 violations** |
| **Zero Supply Invariant** | Empty reservoir: $W_{\text{avail}} = 0 \implies \text{Alloc}_i = 0$ | **Verified** |
| **Zero Demand Invariant** | Satiated zone: $D_i = 0 \implies \text{Alloc}_i = 0$ | **Verified** |
| **Offline PSO Decoupling** | Optimization is decoupled and strictly offline (never online) | **Verified** |
| **Frontend Production Build** | Next.js 16.3.5 Turbopack production compilation | **15/15 routes static built, 0 errors** |

---

## 9. Production Deployment Guide

### 9.1 Database (Supabase)
1. Create a Supabase project at [supabase.com](https://supabase.com).
2. Execute `backend/app/database/migrations/001_initial_schema.sql` in the Supabase SQL Editor.
3. Retrieve the `Project URL` and API keys from **Project Settings > API**.

### 9.2 Backend (Render / Railway / AWS)
1. Deploy `smart-irrigation-fuzzy-system` as a Python Web Service.
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
4. Set environment variables:
   ```env
   ENVIRONMENT=production
   CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
   GROQ_API_KEY=your_groq_api_key
   TAVILY_API_KEY=your_tavily_api_key
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   ```

### 9.3 Frontend (Vercel)
1. Import repository on [vercel.com](https://vercel.com) and set Root Directory to `frontend`.
2. Configure Environment Variables:
   ```env
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
   NEXT_PUBLIC_API_BASE=https://your-backend.onrender.com/api
   ```
3. Deploy.

---

## 10. Citation & Academic References

1. **Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998)**. *Crop evapotranspiration - Guidelines for computing crop water requirements*. FAO Irrigation and drainage paper 56. Rome: FAO.
2. **Mamdani, E. H., & Assilian, S. (1975)**. *An experiment in linguistic synthesis with a fuzzy logic controller*. International Journal of Man-Machine Studies, 7(1), 1-13.
3. **Kennedy, J., & Eberhart, R. (1995)**. *Particle swarm optimization*. Proceedings of ICNN'95 - International Conference on Neural Networks, 4, 1942-1948.
4. **ICAR (Indian Council of Agricultural Research)**. *Agro-Climatic Zones of India and Crop Water Requirements*.

---

## 11. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
