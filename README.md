# Smart Multizone Irrigation and Water Resource Management Using Hierarchical Adaptive Fuzzy Control

> **Academic Context**: B.Tech 3rd-Year Electronics & Instrumentation Engineering / Fuzzy Systems Project.  
> **Core Principle**: The **Fuzzy Control System** is the mathematical and control-theoretic foundation of this project. It is not replaced by black-box machine learning or simple threshold switching.

---

## 1. Project Objective

Agricultural irrigation accounts for approximately 70% of global freshwater withdrawals. Traditional irrigation systems operate either on fixed time schedules (open-loop) or simple hysteresis thresholds (bang-bang control), leading to significant water waste, nutrient runoff, and crop stress from over- or under-irrigation.

This project implements a **closed-loop, intelligent multizone irrigation and water resource management system** using a **Hierarchical Adaptive Mamdani Fuzzy Control Architecture**. The system:
1. Ingests dynamic environmental (weather), soil, crop, and available water resource parameters.
2. Formulates reference evapotranspiration ($ET_0$) via the physics-based **FAO-56 Penman-Monteith** methodology.
3. Computes crop-specific evapotranspiration ($ET_c = K_c \times ET_0$).
4. Models dynamic soil-water balance considering infiltration, drainage, and saturation limits.
5. Evaluates normalized relative soil moisture ($RSM$) and closed-loop moisture error $e(t) = SM_{\text{target}} - SM(t)$.
6. Decomposes decision-making into **five modular Fuzzy Inference Systems (FIS)**:
   - Soil Stress FIS
   - Weather Stress FIS
   - Water Demand FIS
   - Main Irrigation Demand FIS
   - Water Allocation FIS
7. Resolves inter-zone competition for limited water reservoirs while maintaining plant health and strict soil moisture conservation.
8. Provides mathematical explainability, benchmark comparisons (vs. On-Off and PID controllers), and MATLAB/Simulink validation.

---

## 2. Core Architecture

The system enforces a hierarchical, closed-loop control topology:

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
                              └──────► FEEDBACK LOOP
```

---

## 3. The Five Fuzzy Inference Systems (FIS)

The control architecture avoids single-stage monolithic rule explosion by structuring decisions into five hierarchical subsystems using **Mamdani inference**, **Min-Max (Mamdani minimum implication, maximum aggregation)**, and **Centroid defuzzification**:

| FIS Subsystem | Inputs | Output | Linguistic Variables |
| :--- | :--- | :--- | :--- |
| **1. Soil Stress FIS** | • Soil Moisture ($SM$)<br>• Moisture Error ($e(t)$) | Soil Stress | **SM**: Very Dry, Dry, Moderate, Wet, Very Wet<br>**Error**: Very Negative, Negative, Zero, Positive, Very Positive<br>**Stress**: Very Low, Low, Moderate, High, Extreme |
| **2. Weather Stress FIS** | • Temperature ($T$)<br>• Relative Humidity ($RH$)<br>• Solar Radiation ($R_s$)<br>• Wind Speed ($u_2$)<br>• Rainfall ($P$) | Weather Stress | **Temp**: Low, Moderate, High, Very High<br>**Humidity**: Very Low, Low, Moderate, High, Very High<br>**Solar**: Very Low, Low, Moderate, High, Very High<br>**Wind**: Low, Moderate, High, Very High<br>**Rain**: None, Light, Moderate, Heavy<br>**Stress**: Low, Moderate, High, Extreme |
| **3. Water Demand FIS** | • Crop Evapotranspiration ($ET_c$)<br>• Water Deficit ($WD$)<br>• Effective Rainfall ($P_{\text{eff}}$) | Water Demand | **ETc**: Very Low, Low, Moderate, High, Very High<br>**Deficit**: None, Low, Moderate, High, Extreme<br>**Rain**: None, Low, Moderate, High<br>**Demand**: None, Low, Moderate, High, Very High |
| **4. Main Irrigation FIS** | • Soil Stress<br>• Weather Stress<br>• Water Demand<br>• Moisture Error | Irrigation Command | **Command**: OFF, Very Low, Low, Medium, High, Very High<br>*(Normalized 0–100 scale, translated to volume, flow rate, and duration)* |
| **5. Water Allocation FIS** | • Zone Demand<br>• Zone Stress<br>• Available Water<br>• Zone Priority | Zone Allocation | Constrained multi-zone optimization ensuring $\sum \text{Allocated}_i \le \text{Available Water}$ based on stress urgency and crop economic priority. |

---

## 4. Mathematical Foundations

### 4.1 FAO-56 Penman-Monteith Evapotranspiration
Reference crop evapotranspiration $ET_0$ ($\text{mm}\cdot\text{day}^{-1}$) is calculated using the standard FAO-56 equation:

$$ET_0 = \frac{0.408 \Delta (R_n - G) + \gamma \frac{900}{T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}$$

Where:
- $R_n$: Net radiation at the crop surface ($\text{MJ}\cdot\text{m}^{-2}\cdot\text{day}^{-1}$)
- $G$: Soil heat flux density ($\text{MJ}\cdot\text{m}^{-2}\cdot\text{day}^{-1}$)
- $T$: Mean daily air temperature at 2 m height ($^\circ\text{C}$)
- $u_2$: Wind speed at 2 m height ($\text{m}\cdot\text{s}^{-1}$)
- $e_s$: Saturation vapour pressure ($\text{kPa}$)
- $e_a$: Actual vapour pressure ($\text{kPa}$)
- $\Delta$: Slope of the vapour pressure curve ($\text{kPa}\cdot^\circ\text{C}^{-1}$)
- $\gamma$: Psychrometric constant ($\text{kPa}\cdot^\circ\text{C}^{-1}$)

Crop evapotranspiration under standard conditions:
$$ET_c = K_c \times ET_0$$

### 4.2 Soil Moisture Normalization & Error Dynamics
- **Relative Soil Moisture ($RSM$)**:
  $$RSM = \frac{SM(t) - WP}{FC - WP}$$
  Where $WP$ is Wilting Point and $FC$ is Field Capacity.
- **Moisture Error**:
  $$e(t) = SM_{\text{target}} - SM(t)$$

### 4.3 Soil Water Balance Equation
For discrete simulation step $t \to t+1$:
$$SM(t+1) = SM(t) + I(t) + P_{\text{eff}}(t) - ET_c(t) - D(t)$$
Subject to physical constraints:
$$WP \le SM(t) \le FC$$
Where:
- $I(t)$: Effective applied irrigation
- $P_{\text{eff}}(t)$: Effective precipitation
- $ET_c(t)$: Evapotranspiration loss
- $D(t)$: Deep percolation / drainage beyond field capacity

---

## 5. Agricultural Configuration (Default 3 Zones)

| Zone | Crop | Soil Type | Area ($m^2$) | Field Capacity ($FC$) | Wilting Point ($WP$) | Growth Stage | Base $K_c$ |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Zone 1** | Tomato | Loam | 100 | 0.28 | 0.14 | Mid-season | 1.15 |
| **Zone 2** | Wheat | Sandy | 120 | 0.18 | 0.08 | Development | 0.85 |
| **Zone 3** | Maize | Clay | 80 | 0.36 | 0.20 | Mid-season | 1.20 |

All parameters are fully configuration-driven via `config/config.json` and `config/schemas.py`.

---

## 6. Simulation Scenarios & Scope

- **Default Resolution**: 24 hours at 1-minute intervals ($1440$ simulation steps).
- **Scalable To**: 7-day and 30-day extended multi-crop cycles.
- **Six Deterministic/Stochastic Weather Profiles**:
  1. **Normal**: Moderate diurnal temperature and solar cycles.
  2. **Hot & Dry**: High temperature ($35^\circ\text{C}$+), low humidity ($<30\%$), elevated wind.
  3. **Rainy**: Intermittent precipitation events, saturated humidity, suppressed solar.
  4. **Cloudy**: Diminished solar irradiance, moderate temperatures.
  5. **Heatwave**: Persistent extreme thermal stress with acute vapour pressure deficit.
  6. **Water Scarcity**: Severely restricted reservoir volume triggering prioritization algorithms.

---

## 7. Technology Stack

- **Engineering Language**: Python 3.11+
- **Fuzzy Inference Engine**: `scikit-fuzzy`, `numpy`, `scipy`
- **Data Modeling & Validation**: `pydantic v2`
- **Data Analysis & Export**: `pandas`, `matplotlib`, `plotly`
- **API & Service Layer**: `fastapi`, `uvicorn`
- **Reference & Validation Environment**: MATLAB / Simulink Fuzzy Logic Toolbox
- **Testing**: `pytest`, `pytest-asyncio`

---

## 8. Development Roadmap (Phase 0 to 28)

- [x] **Phase 0**: Foundation, Project Skeleton, Config, Schemas, Validation Scripts, Smoke Tests
- [x] **Phase 1**: Dataset & Agricultural Parameter Foundation
- [x] **Phase 2**: Exploratory Data Analysis (EDA)
- [x] **Phase 3**: Dynamic Weather Engine
- [ ] **Phase 4**: FAO-56 Penman-Monteith ET0 / ETc Models
- [ ] **Phase 5**: Soil Dynamics & Water Balance Engine
- [ ] **Phase 6**: Fuzzy Variables & Membership Functions
- [ ] **Phase 7**: Soil Stress FIS
- [ ] **Phase 8**: Weather Stress FIS
- [x] **Phase 0–8**: Weather Model, FAO-56 ET0, Soil Balance, 4 Zone Mamdani FIS Subsystems
- [x] **Phase 9–10**: Water Demand FIS & Main Irrigation FIS
- [x] **Phase 11**: Single-Zone Closed-Loop Simulation (24h, 1440 timesteps)
- [x] **Phase 12**: Three-Zone Multizone Closed-Loop Simulation (12,960 records)
- [x] **Phase 13–13.1**: Supervisory Water Allocation FIS & Deterministic Bounded Priority Water-Filling Audit
- [x] **Phase 14**: Offline Particle Swarm Optimization (PSO) for 18 FIS Parameters
- [x] **Phase 15–18**: Production FastAPI Service Layer & REST Endpoints (`backend/app/`)
- [x] **Phase 19**: Supabase Database Schema (RLS) & SQLite Mirror (`backend/app/database/`)
- [x] **Phase 20**: Next.js 16 + React 19 Frontend Platform (12 Interactive Pages) (`frontend/`)
- [x] **Phase 21–22**: Groq LLM Advisory Copilot & Grounded RAG (`backend/app/services/ai_service.py`)
- [x] **Phase 23**: Automated Engineering Audit PDF Reports via ReportLab (`backend/app/services/report_service.py`)
- [x] **Phase 24**: Comprehensive Test Suite infrastructure and regression coverage (full suite includes long-running integration tests)

---

## 9. Platform Quickstart

### 9.1 Backend API Server (FastAPI)
```bash
# Run the FastAPI backend service on port 8000
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation is available at `http://localhost:8000/docs`.

### 9.2 Frontend Application (Next.js 16)
```bash
cd frontend
npm ci
npm run dev
```
Open `http://localhost:3000` to access the full-stack engineering platform.

For production, set `NEXT_PUBLIC_API_BASE` to the deployed Render API (see `frontend/.env.production.example`).

### 9.3 Running Automated Tests
```bash
# Run full automated regression suite (300 tests)
pytest -v
```

---

## 10. Deployment Guide

### 10.1 Database Deployment (Supabase)
1. Create a new project in [Supabase](https://supabase.com).
2. Navigate to the **SQL Editor** in your Supabase dashboard.
3. Open `backend/app/database/migrations/001_initial_schema.sql` and run it to create all tables (`profiles`, `zones`, `simulation_runs`, `simulation_results`, `optimization_runs`, `reports`, `ai_conversations`, `ai_messages`) along with Row-Level Security (RLS) policies and indexes.
4. Copy your `Project URL`, `anon public key`, and `service_role secret key` from **Project Settings > API**.

### 10.2 Backend Deployment (Render)
1. Push this repository to GitHub.
2. In [Render](https://render.com), click **New + > Blueprint** and link your GitHub repository. Render will automatically detect `render.yaml`.
3. Alternatively, create a **Web Service**:
   - **Environment**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
4. Configure Environment Variables on Render:
   - `ENVIRONMENT`: `production`
   - `CORS_ORIGINS`: `https://your-frontend.vercel.app,http://localhost:3000`
   - `GROQ_API_KEY`: your Groq API key
   - `SUPABASE_URL`: your Supabase Project URL
   - `SUPABASE_ANON_KEY`: your Supabase anon key
   - `SUPABASE_SERVICE_ROLE_KEY`: your Supabase service role key

### 10.3 Frontend Deployment (Vercel)
1. Import your GitHub repository into [Vercel](https://vercel.com).
2. Set the **Root Directory** to `frontend`.
3. Vercel automatically detects Next.js.
4. Add Environment Variables in Vercel:
   - `NEXT_PUBLIC_API_BASE`: `https://your-backend.onrender.com/api/v1`
   - `NEXT_PUBLIC_SUPABASE_URL`: `https://your-project.supabase.co`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`: `your_supabase_anon_key`
5. Click **Deploy**.

---

## 11. Platform Verification Matrix

| Verification Aspect | Specification | Verified Status |
| :--- | :--- | :--- |
| **Regression Tests** | Full engineering test suite | **300 Passed, 0 Failed, 0 Skipped** |
| **Water Balance Residual** | 1D soil mass balance closure | **0.00e+00 mm exact (< 1e-6 mm)** |
| **Supply-Cap Invariant** | Total allocation under scarcity | **Σ Alloc ≤ Supply (0 violations across 1,000 cases)** |
| **Demand-Ceiling Invariant** | No zone receives > request | **Alloc ≤ Req (0 violations)** |
| **Zero Supply Invariant** | Empty reservoir behavior | **Alloc = 0 when Supply = 0** |
| **Zero Demand Invariant** | Satiated zone behavior | **Alloc = 0 when Demand = 0** |
| **Offline Optimization** | PSO Decoupling guarantee | **Strictly offline (never online)** |
| **Advisory AI** | Groq LLM boundary | **Advisory / Explanatory only** |
| **Frontend Static Build** | Next.js 16.3.5 Turbopack | **15/15 routes built, 0 errors** |

---

*For detailed examination defense, see [docs/VIVA_GUIDE.md](docs/VIVA_GUIDE.md).*




