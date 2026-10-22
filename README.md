# 🌾 Smart Multizone Irrigation & Water Resource Management Platform
### Hierarchical Adaptive Fuzzy Control (HAFC) & Digital Twin Ecosystem

[![Frontend Vercel](https://img.shields.io/badge/Frontend-Vercel_Production-000000.svg?style=for-the-badge&logo=vercel&logoColor=white)](https://irrigation-fuzzy-system.vercel.app/)
[![Backend Render](https://img.shields.io/badge/Backend-Render_Live_API-46E3B7.svg?style=for-the-badge&logo=render&logoColor=white)](https://smart-irrigation-fuzzy-system.onrender.com/)
[![Swagger Docs](https://img.shields.io/badge/API_Docs-Swagger_UI-85EA2D.svg?style=for-the-badge&logo=swagger&logoColor=black)](https://smart-irrigation-fuzzy-system.onrender.com/docs)
[![Test Suite](https://img.shields.io/badge/Tests-346_Passed-10B981.svg?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org)

> 🌐 **Live Deployments:**
> - **Production Web Application (Next.js)**: [https://irrigation-fuzzy-system.vercel.app/](https://irrigation-fuzzy-system.vercel.app/)
> - **Production Backend Engine (FastAPI)**: [https://smart-irrigation-fuzzy-system.onrender.com/](https://smart-irrigation-fuzzy-system.onrender.com/)
> - **Interactive Swagger / OpenAPI Docs**: [https://smart-irrigation-fuzzy-system.onrender.com/docs](https://smart-irrigation-fuzzy-system.onrender.com/docs)

---

## 📖 1. What is this Project? (In Simple Terms)

Imagine you are managing a modern farm with multiple crops—say **Tomato**, **Wheat**, and **Maize**—growing in different types of soils (**Loam**, **Sand**, and **Clay**). 

### The Problem in Traditional Farming:
1. **Dumb Timers**: Most irrigation systems just turn water valves ON for 30 minutes every morning. If it rains, water is wasted and roots rot. If a severe heatwave hits, crops wither because 30 minutes isn't nearly enough.
2. **Brutal Droughts**: When water in your shared tank or canal drops to 30%, dumb timers still try to irrigate everything equally until the tank runs completely dry, killing both your cash crops and your grain.
3. **Black-Box AI Risks**: You cannot trust an unpredictable black-box neural network to operate expensive industrial water pumps, because if it hallucinates, crops can die overnight.

### The Solution:
This project is an **autonomous, mathematical, and explainable brain** for farm irrigation. 
Instead of crude ON/OFF timers or unpredictable black-box neural networks, it uses **Hierarchical Mamdani Fuzzy Logic**. Just like an experienced human agronomist thinks:
> *"If the soil is somewhat dry, and today's weather is scorching with heavy wind, but we have limited water in the reservoir, give 85% water to the high-priority Tomato cash crop and only 30% survival water to the drought-tolerant Maize."*

The system runs **every single minute**, tracking real physics, calculating exact crop evapotranspiration, and actuating valves smoothly between **0% and 100%**.

---

## 🏛️ 2. High-Level Architecture & Information Flow

Where does data come from, how does it move through the system, and what happens at each stage?

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   EXTERNAL DATA SOURCES                                │
├─────────────────────────┬──────────────────────────┬───────────────────────────────────┤
│    Weather Data         │       Soil Physics       │       Crop Agronomy               │
│ • Air Temperature       │ • Field Capacity (FC)    │ • Crop Coefficient (Kc)           │
│ • Relative Humidity     │ • Wilting Point (WP)     │ • Growth Stage                    │
│ • Solar Radiation       │ • Current Moisture       │ • Root Zone Depth                 │
│ • Wind Speed & Rain     │ • Saturation Limit       │ • Economic Priority               │
└────────────┬────────────┴─────────────┬────────────┴─────────────────┬─────────────────┘
             │                          │                              │
             ▼                          ▼                              ▼
┌─────────────────────────┐  ┌───────────────────────────────────────────────────────────┐
│ Atmospheric Physics     │  │ Soil-Water Tracking                                       │
│ FAO-56 Penman-Monteith  │  │ Error = Target Moisture - Current Moisture                │
│ Reference ET (ET0)      │  │ Relative Soil Moisture: RSM = (SM - WP) / (FC - WP)       │
└────────────┬────────────┘  └──────────────────────────┬────────────────────────────────┘
             │                                          │
             └──────────────────┬───────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        THE 5 HIERARCHICAL FUZZY ENGINES (FIS)                          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [Input: RSM, Error]            [Input: Temp, Humidity, Solar, Wind, Rain]            │
│            │                                           │                               │
│            ▼                                           ▼                               │
│  ┌───────────────────┐                       ┌───────────────────┐                     │
│  │ FIS 1:            │                       │ FIS 2:            │                     │
│  │ Soil Stress FIS   │                       │ Weather Stress FIS│                     │
│  │ (25 Rules)        │                       │ (34 Rules)        │                     │
│  └─────────┬─────────┘                       └─────────┬─────────┘                     │
│            │                                           │                               │
│            │           ┌───────────────────────────────┘                               │
│            │           │                                                               │
│            │           ▼               [Input: ETc, Deficit, Rain]                     │
│            │   ┌───────────────┐                       │                               │
│            │   │ Crop Demand   │                       ▼                               │
│            │   │ Calculation   │             ┌───────────────────┐                     │
│            │   │ ETc = Kc * ET0│             │ FIS 3:            │                     │
│            │   └───────┬───────┘             │ Water Demand FIS  │                     │
│            │           │                     │ (39 Rules)        │                     │
│            │           │                     └─────────┬─────────┘                     │
│            │           │                               │                               │
│            ▼           ▼                               ▼                               │
│  ┌───────────────────────────────────────────────────────────────┐                     │
│  │ FIS 4: Main Irrigation Supervisory Controller (32 Rules)      │                     │
│  │ Fuses Soil Stress + Weather Stress + Water Demand + Error     │                     │
│  │ Output: Raw Zone Irrigation Demand (0 - 100%)                 │                     │
│  └───────────────────────────────┬───────────────────────────────┘                     │
│                                  │                                                     │
│                                  ▼                                                     │
│                [Input: Shared Reservoir Supply % & Priority]                           │
│                                  │                                                     │
│                                  ▼                                                     │
│  ┌───────────────────────────────────────────────────────────────┐                     │
│  │ FIS 5: Shared Water Allocation Arbitrator (32 Rules)          │                     │
│  │ Prioritizes high-value & distressed crops under drought       │                     │
│  │ Guarantees: Total Allocated Water <= Total Available Supply   │                     │
│  └───────────────────────────────┬───────────────────────────────┘                     │
│                                  │                                                     │
└──────────────────────────────────┼─────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PHYSICAL ACTUATION & CLOSED LOOP SIMULATION                     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ • Converts % command into physical flow rate (Liters / minute)                         │
│ • Applies water to 1D Soil Water Balance Model:                                        │
│     Soil_Moisture(t+1) = Soil_Moisture(t) + Rain + Irrigation - ETc - Drainage         │
│ • Verifies physical conservation: Mathematical residual error <= 10⁻⁶ mm (Zero waste)  │
│ • Feeds new soil moisture back into next minute's loop (1440 steps = 24 hours)         │
└──────────────────────────────────┬─────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                       USER EXPERIENCE & REPORTING INTERFACE                            │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ • 3D WebGL Digital Twin (Three.js real-time crop hydration & valve spray)              │
│ • 24-Hour Telemetry Playback with Variable Speed Scrubber (1x - 30x)                   │
│ • Interactive Fuzzy Sandbox with real-time antecedent sliders & rule highlighting      │
│ • Explainable AI Agronomist Copilot (Groq LLM + Tavily ICAR live search)               │
│ • Industrial ReportLab Engineering PDF Audits & CSV Telemetry Export                   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📥 3. Where Do the Inputs Come From?

The system accepts 4 distinct groups of real-world inputs:

### A. Real-Time Meteorological Inputs (The Weather)
* **Where it comes from**: Live Open-Meteo API, India Meteorological Department (IMD) agromet feeds, or synthetic climate benchmark scenarios (Normal, Hot & Dry, Rainy, Cloudy, Heatwave, Water Scarcity).
* **Parameters**:
  * **Temperature ($^\circ\text{C}$)**: Ambient air temperature at 2-meter elevation.
  * **Relative Humidity ($\%$)**: Ambient atmospheric moisture.
  * **Solar Radiation ($\text{W}/\text{m}^2$)**: Solar energy driving photosynthesis and evaporation.
  * **Wind Speed ($\text{m}/\text{s}$)**: Air movement carrying vapor away from leaves.
  * **Rainfall ($\text{mm}$)**: Natural precipitation directly infiltrating the topsoil.

### B. Soil Physics Inputs (The Ground)
* **Where it comes from**: Physical capacitive sensor readings or the built-in ICAR/USDA Soil Database (`data/soil_database.csv`).
* **Parameters**:
  * **Soil Moisture ($SM$)**: Volumetric water content ($\%$ or fraction).
  * **Field Capacity ($FC$)**: Maximum water the soil can hold against gravity (excess drains away as deep percolation).
  * **Wilting Point ($WP$)**: The moisture level below which plant roots cannot extract water (leading to permanent wilting).
  * **Root Zone Depth ($Z_r$)**: Effective root depth (e.g., $0.6\text{ m}$ for tomato, $0.8\text{ m}$ for cotton).

### C. Crop Agronomy Inputs (The Plant)
* **Where it comes from**: Food and Agriculture Organization (FAO-56) crop database (`data/crop_database.csv`).
* **Parameters**:
  * **Crop Coefficient ($K_c$)**: Multiplier reflecting transpiration across growth stages (e.g., Initial $0.6$, Mid-Season $1.15$, Maturity $0.8$).
  * **Target Moisture**: Optimal root-zone hydration level set by the farmer.
  * **Crop Economic Priority**: User-defined importance (e.g., high-value cash crop Tomato = 90, staple Wheat = 60, pasture Grass = 30).

### D. Shared Reservoir / Water Supply Inputs
* **Where it comes from**: Farm tank level sensors, canal water meters, or municipal quotas.
* **Parameters**:
  * **Available Water Supply ($\%$)**: From $100\%$ (abundant) down to $20\%$ (emergency drought conditions).

---

## 🧠 4. The 5 Fuzzy Inference Systems (FIS) Explained

Instead of one gigantic unmanageable table with thousands of rules, the system splits human expertise into **5 specialized fuzzy engines**:

| Engine | Inputs | What It Evaluates | Output |
| :--- | :--- | :--- | :--- |
| **FIS 1: Soil Stress** | Relative Soil Moisture (RSM), Moisture Tracking Error | How desperately does the soil need water right now? | **Soil Stress** ($0 - 100\%$) |
| **FIS 2: Weather Stress** | Temp, Humidity, Solar Radiation, Wind Speed, Rain | How rapidly is the atmosphere sucking water from the field? | **Weather Stress** ($0 - 100\%$) |
| **FIS 3: Water Demand** | Crop ET ($ET_c$), Water Deficit, Effective Rainfall | How much water does this specific crop need today? | **Water Demand** ($0 - 100\%$) |
| **FIS 4: Main Controller** | Soil Stress, Weather Stress, Water Demand, Moisture Error | Overall decision: How wide should we open this zone's valve? | **Raw Irrigation Command** ($0 - 100\%$) |
| **FIS 5: Water Allocation** | Total Reservoir Water, Zone Demand, Crop Stress, Priority | If water is scarce, who gets water first and how much? | **Constrained Allocation** ($0 - 100\%$) |

### Defuzzification Standard:
Every FIS uses the **Mamdani Min-Max Inference** mechanism with **501-point Centroid (Center of Area)** defuzzification. This ensures smooth, continuous valve actuation (e.g., $43.2\%$ duty cycle) rather than jarring ON/OFF valve shocks.

---

## ⏱️ 5. Real-Time End-to-End Implementation & Execution Loop

How does the whole system actually run in real time? Here is the exact **minute-by-minute ($t \to t+1$) execution cycle** as implemented across the codebase:

```
                                REAL-TIME 60-SECOND CONTROL CYCLE
═══════════════════════════════════════════════════════════════════════════════════════════════
  [00s] SENSOR INGESTION       [10s] ATMOSPHERIC PHYSICS    [20s] STAGE 1 & 2 FUZZY
  • Read Weather (T, RH,       • FAO-56 Penman-Monteith     • FIS 1: Soil Stress (RSM, Error)
    Solar, Wind, Rain)           ET0 (mm/min)               • FIS 2: Weather Stress (Weather)
  • Read Soil Moisture         • ETc = Kc * ET0             • FIS 3: Water Demand (ETc, Deficit)
    Sensors for each Zone      • Effective Rain Peff (USDA)
                               • Deficit = max(0, ETc-Peff)
                                      │                            │
                                      ▼                            ▼
  [30s] STAGE 3 SUPERVISORY    [40s] STAGE 4 CONSTRAINED    [50s] ACTUATION & TELEMETRY
  • FIS 4: Main Irrigation       ALLOCATION (FIS 5)         • Dispatch Solenoid Valve Flow
    Command (%) for each zone  • Check Reservoir Budget     • Run 1D Soil Balance Conservation
  • Convert to Physical          Available Water (Liters)   • Zero-Residual Check (|err| <= 1e-6mm)
    Volume: V_req = Depth*Area • Water-Filling Arbitrator:  • Stream to Next.js 3D Digital Twin
                                 Alloc <= Budget Ceiling      (Update Soil Color & Particle Spray)
═══════════════════════════════════════════════════════════════════════════════════════════════
                                      │
                                      └──────► LOOP ADVANCES: t = t + 1 minute (1440 steps/day)
```

### Step-by-Step Code Execution Trace:

#### Step 1: Real-Time Environmental & Sensor Ingestion (`simulation/weather.py`)
At timestep $t$, the system samples atmospheric conditions:
* Temperature $T(t)$, Humidity $RH(t)$, Solar Radiation $R_s(t)$, Wind Speed $u_2(t)$, and Precipitation $P(t)$.
* For each agricultural zone $i$, capacitive moisture probes report volumetric water content $SM_i(t)$.

#### Step 2: Atmospheric Evapotranspiration Engine (`models/et0.py`, `models/etc.py`)
1. Computes instantaneous reference evapotranspiration $ET_0(t)$ via the FAO-56 Penman-Monteith equation:
   $$ET_0(t) = \frac{0.408 \Delta (R_n - G) + \gamma \frac{900}{T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}$$
2. Computes crop-specific evapotranspiration using the crop coefficient $K_{c, i}$:
   $$ET_{c, i}(t) = K_{c, i} \times ET_0(t)$$
3. Computes effective precipitation $P_{\text{eff}}(t)$ and unmitigated crop deficit:
   $$\text{Deficit}_i(t) = \max\Big(0, \; ET_{c, i}(t) - P_{\text{eff}}(t)\Big)$$

#### Step 3: Local Physiological Stress Evaluation (FIS 1 & FIS 2)
In parallel for every active zone:
1. **Relative Soil Moisture (RSM)** is normalized between Wilting Point ($WP$) and Field Capacity ($FC$):
   $$RSM_i(t) = \frac{SM_i(t) - WP_i}{FC_i - WP_i}$$
2. Closed-loop tracking error: $e_i(t) = SM_{\text{target}, i} - SM_i(t)$.
3. **`SoilStressFIS.evaluate(RSM, Error)`** (`fuzzy_engine/soil_stress.py`):
   * Fuses RSM and moisture error across 25 Mamdani rules.
   * Produces crisp physiological root stress index: $\text{SoilStress}_i(t) \in [0, 100]\%$.
4. **`WeatherStressFIS.evaluate(T, RH, Rs, Wind, Rain)`** (`fuzzy_engine/weather_stress.py`):
   * Fuses 5 meteorological variables across 34 Mamdani rules.
   * Produces crisp atmospheric drying stress: $\text{WeatherStress}(t) \in [0, 100]\%$.

#### Step 4: Crop Water Demand Estimation (FIS 3)
* **`WaterDemandFIS.evaluate(ETc, Deficit, Peff)`** (`fuzzy_engine/water_demand.py`):
  * Synthesizes plant transpiration demand across 39 Mamdani rules.
  * Produces normalized demand: $\text{WaterDemand}_i(t) \in [0, 100]\%$.

#### Step 5: Supervisory Valve Command Calculation (FIS 4)
* **`MainIrrigationFIS.evaluate(SoilStress, WeatherStress, WaterDemand, Error)`** (`fuzzy_engine/irrigation.py`):
  * Synthesizes all 4 stress & demand inputs across 32 Mamdani rules.
  * Defuzzifies via 501-point centroid into raw valve duty cycle: $\text{DutyCycle}_i(t) \in [0, 100]\%$.
  * Converts percentage duty cycle into requested water depth and physical volume:
    $$\text{Depth}_{\text{req}, i}(t) = \frac{\text{DutyCycle}_i(t)}{100} \times \text{MaxApplicationRate} \quad (\text{mm})$$
    $$V_{\text{req}, i}(t) = \text{Depth}_{\text{req}, i}(t) \times \text{Area}_i \quad (\text{Liters})$$

#### Step 6: Multi-Zone Shared Supply Arbitration (FIS 5)
When shared reservoir supply $W_{\text{avail}}(t)$ is constrained (e.g. drought or pump capacity limits):
* **`WaterAllocationFIS.allocate_multizone(...)`** (`fuzzy_engine/water_allocation.py`):
  * Synthesizes available water percentage, each zone's raw demand $V_{\text{req}, i}$, current crop stress, and economic priority $w_i$.
  * Solves priority water-filling allocation:
    $$V_{\text{alloc}, i}(t) = \min\left(V_{\text{req}, i}(t), \; W_{\text{avail}}(t) \times \frac{w_i \cdot \text{SoilStress}_i(t)}{\sum_j (w_j \cdot \text{SoilStress}_j(t))}\right)$$
  * **Hard Invariant Guarantee**: $\sum_{i=1}^N V_{\text{alloc}, i}(t) \le W_{\text{avail}}(t)$ strictly enforced at every minute.

#### Step 7: Physical Actuation & Soil Conservation Feedback
1. **Physical Actuation**: Dispatches flow command to physical solenoid valves / relays:
   $$\text{FlowRate}_i(t) = \frac{V_{\text{alloc}, i}(t)}{\Delta t} \quad (\text{L/min})$$
2. **Dynamic 1D Soil Balance Update** (`models/water_balance.py`):
   $$SM_i(t+1) = SM_i(t) + \frac{I_i(t) + P_{\text{eff}}(t) - ET_{c, i}(t) - D_i(t)}{Z_{r, i} \times 1000}$$
3. **Conservation Check**: Validates that the mathematical water balance closure residual:
   $$|\text{Residual}| = \Big|SM_i(t+1) - \Big(SM_i(t) + \text{Inflow} - \text{Outflow}\Big)\Big| \le 10^{-6}\text{ mm}$$

#### Step 8: Real-Time Telemetry Streaming & 3D Digital Twin Update
* Backend writes the 1-minute telemetry record to SQLite `platform.db` / Supabase.
* Next.js frontend updates:
  * **Three.js WebGL Digital Twin** ([`DigitalTwin3D.tsx`](file:///c:/Users/pranshu/Desktop/PROJECTS/irrigation_system_fullstack/frontend/src/components/DigitalTwin3D.tsx)): Terrain shader dynamically blends vertex colors from dry tan (`#D4A373`) to moist dark brown (`#3E2723`), and valve emitter particle systems spray water droplets proportional to flow rate.
  * **Live Scrubber Timeline** ([`SimulationScrubberBar.tsx`](file:///c:/Users/pranshu/Desktop/PROJECTS/irrigation_system_fullstack/frontend/src/components/SimulationScrubberBar.tsx)): Scrubber advances smoothly with Web Audio relay clicks.
  * **Explainable AI Advisor** ([`api.chatAI`](file:///c:/Users/pranshu/Desktop/PROJECTS/irrigation_system_fullstack/backend/app/api/routes/ai.py)): Farmer can click any minute on the timeline to ask *"Why did Zone 1 receive 42% water here?"* and receive a clear agronomist breakdown.

---

## ⚖️ 6. Physical Invariants & Mathematical Proofs

The platform enforces strict scientific conservation laws at every minute of simulation:

1. **Exact 1D Soil Water Mass Balance**:
   $$\Delta \text{Soil Moisture} = \text{Rainfall} + \text{Irrigation} - \text{Evapotranspiration} (ET_c) - \text{Drainage}$$
   Every single simulation step verifies that the balance residual satisfies:
   $$|\text{Residual}| \le 10^{-6}\text{ mm}$$
   Water never appears from nowhere or vanishes without a physical trace.

2. **Strict Supply-Cap Conservation**:
   $$\sum_{i=1}^{N} \text{Allocated Volume}_i \le \text{Available Reservoir Volume}$$
   Under severe water scarcity (e.g. $40\%$ reservoir level), the supervisory allocation engine scales back water systematically, protecting high-priority cash crops while strictly respecting the reservoir ceiling.

---

## 💻 7. Technology Stack

### Backend
* **Python 3.11+**
* **FastAPI**: Asynchronous high-performance RESTful API with automated OpenAPI / Swagger documentation.
* **NumPy & Pandas**: Vectorized mathematical simulations and time-series aggregation.
* **Scikit-Fuzzy & SciPy**: Scientific fuzzy inference, membership curves, and numeric integration.
* **ReportLab**: Server-side vector PDF generation for engineering audits.
* **SQLite + Supabase PostgreSQL**: Dual-tier storage (instant offline local mirror + cloud sync).
* **Groq LLM + Tavily Search**: Agronomic advisory copilot with live IMD/ICAR advisory search.

### Frontend
* **Next.js 16.3.5 (Turbopack)**: State-of-the-art React 19 framework with fast compilation.
* **TypeScript 5**: Complete type safety across all schemas and API responses.
* **Tailwind CSS v4**: Modern CSS design system with custom dark and light agronomy themes.
* **Three.js**: 3D WebGL Digital Twin rendering dynamic soil hydration and valve spray.
* **Leaflet GIS**: Interactive satellite mapping with real-time Indian agro-climatic district data.
* **Web Audio API**: Synthesized relay sound effects and haptic audio cues.

---

## 📁 8. Repository Directory Structure

```
irrigation_system_fullstack/
├── backend/                        # FastAPI REST API & Core Services
│   └── app/
│       ├── main.py                 # Application entrypoint & CORS middleware
│       ├── api/routes/             # 14 REST routes (fuzzy, zones, sim, auth, ai, etc.)
│       ├── core/                   # Security, settings, and logging configuration
│       ├── database/               # Dual-tier persistence (SQLite + Supabase sync)
│       ├── schemas/                # Pydantic v2 data contracts
│       └── services/               # Fuzzy service, Tavily search, and PDF generation
├── frontend/                       # Next.js 16 App Router UI
│   ├── src/
│   │   ├── app/                    # 15 application pages (fuzzy, sim, dashboard, etc.)
│   │   ├── components/             # Reusable UI widgets (3D Twin, charts, sidebar)
│   │   ├── context/                # Theme, sidebar, and auth state providers
│   │   ├── hooks/                  # Simulation playback and timeline hooks
│   │   └── lib/                    # API client, utilities, and Web Audio engine
├── fuzzy_engine/                   # 5 Mamdani Fuzzy Inference Systems & MF Factory
├── models/                         # FAO-56 Penman-Monteith ET0, ETc, and Soil Balance
├── simulation/                     # 24h/7d multizone closed-loop simulation engine
├── optimization/                   # Offline 18-D Particle Swarm Optimization (PSO)
├── data/                           # Crop & soil databases, local SQLite platform.db
├── data_processing/                # Weather preprocessors and dataset builders
├── docs/                           # Architectural thesis documents & UX audit reports
├── tests/                          # 346 automated pytest unit and integration tests
├── scripts/                        # Master verification, analysis, and data scripts
├── validate_env.py                 # Phase 0 environment & architecture validator
├── requirements.txt                # Python backend dependencies
└── render.yaml                     # Cloud deployment configuration
```

---

## 🚀 9. Quickstart Guide (How to Run Locally)

### Prerequisites:
* **Python 3.11+** installed (`python --version`)
* **Node.js 18+** installed (`node --version`)
* **Git**

### Step 1: Clone the Repository
```bash
git clone https://github.com/pranshu-rajan/smart-irrigation-fuzzy-system.git
cd smart-irrigation-fuzzy-system
```

### Step 2: Start the Backend (Terminal 1)
```bash
# Create and activate virtual environment
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run environment validator
python validate_env.py

# Launch FastAPI server (Port 8000)
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
* Interactive Swagger Docs: `http://localhost:8000/docs`
* Live System Verification: `http://localhost:8000/api/verification/system`

### Step 3: Start the Frontend (Terminal 2)
```bash
cd frontend

# Install npm dependencies
npm install

# Start Next.js development server with Turbopack (Port 3000)
npm run dev
```
* Open your browser at: `http://localhost:3000`

---

## 🧪 10. Automated Testing & Verification

The codebase includes an extensive suite of **346 automated tests** covering every mathematical property, physical boundary, fuzzy rule, and API endpoint:

```bash
# Run the entire test suite
pytest -q

# Run specific subsystem tests
pytest tests/test_fuzzy_variables.py
pytest tests/test_water_allocation.py
pytest tests/test_multizone_closed_loop.py
pytest tests/test_pso.py
```

### Verification Matrix Summary:
* **Total Automated Tests**: **346 Passed (100%)**
* **Frontend Static Pages**: **15/15 Prerendered with 0 Errors**
* **Soil Water Balance Residual**: **$\le 10^{-6}\text{ mm}$ (Exact physical closure)**
* **Shared Supply Conservation**: **Zero violations under drought & scarcity**

---

## 📜 11. Academic Citations & Standards

1. **FAO-56**: Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). *Crop evapotranspiration - Guidelines for computing crop water requirements*. FAO Irrigation and Drainage Paper 56. Rome: Food and Agriculture Organization.
2. **Fuzzy Logic**: Mamdani, E. H., & Assilian, S. (1975). *An experiment in linguistic synthesis with a fuzzy logic controller*. International Journal of Man-Machine Studies, 7(1), 1-13.
3. **PSO Optimization**: Kennedy, J., & Eberhart, R. (1995). *Particle swarm optimization*. Proceedings of IEEE International Conference on Neural Networks.
4. **Agro-Climatology**: Indian Council of Agricultural Research (ICAR), *Package of Practices & Agro-Climatic Zones of India*.

---

## 📄 12. License

This project is open-source and licensed under the **MIT License**. Feel free to use, adapt, and build upon it for academic and commercial applications.
