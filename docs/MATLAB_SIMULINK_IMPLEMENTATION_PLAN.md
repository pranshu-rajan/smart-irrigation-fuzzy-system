# MATLAB + Simulink Implementation Plan

## Target

Reproduce the complete software-only Python architecture in MATLAB/Simulink without hardware:

`Weather -> ET0 -> ETc/Rain -> Soil State -> 3 local FIS -> Main Irrigation FIS -> Multizone Requests -> Allocation FIS -> bounded water allocation -> soil water balance -> feedback`

PSO is an offline calibration workflow; the active optimized parameters are loaded into the Main Irrigation FIS before simulation.

---

## Phase 0 — MATLAB project setup

Recommended products:

- MATLAB
- Simulink
- Fuzzy Logic Toolbox
- Global Optimization Toolbox (for PSO)
- Statistics and Machine Learning Toolbox (optional, for analysis)
- Simulink Control Design (optional, for control analysis)

Folder structure:

```text
matlab_irrigation_system/
├── models/
│   ├── weather/
│   ├── et/
│   ├── soil/
│   └── allocation/
├── fuzzy/
│   ├── soil_stress/
│   ├── weather_stress/
│   ├── water_demand/
│   ├── main_irrigation/
│   └── water_allocation/
├── optimization/
├── data/
├── scripts/
├── tests/
└── simulink/
    └── smart_multizone_irrigation.slx
```

Use a 1-minute base sample time and a 24-hour simulation by default: 1,440 steps.

---

## Phase 1 — Data/configuration layer

Create MATLAB structs/tables for:

- Zone ID
- crop type
- Kc
- growth stage
- root depth
- soil type
- field capacity
- wilting point
- saturation
- infiltration rate
- drainage parameter
- target moisture
- area
- priority

Create `loadDefaultConfiguration.m` and return a 3-zone baseline configuration.

Validate every zone before simulation.

---

## Phase 2 — Weather Engine

Implement a MATLAB `WeatherEngine` function/class producing a timetable at 1-minute resolution.

Outputs:

- temperature (°C)
- RH (%)
- solar radiation (W/m²)
- wind speed (m/s)
- rainfall (mm/step)

Implement scenarios matching Python:

1. Normal
2. Hot & Dry
3. Rainy
4. Cloudy
5. Heatwave
6. Water Scarcity

Use a deterministic RNG seed so Python and MATLAB scenarios can be compared reproducibly.

---

## Phase 3 — FAO-56 ET0 subsystem

Implement Penman-Monteith in MATLAB:

```text
Weather
  -> saturation vapor pressure
  -> actual vapor pressure
  -> VPD
  -> delta
  -> psychrometric constant
  -> net radiation
  -> FAO-56 Penman-Monteith
  -> ET0
```

Create:

`models/et/computeET0.m`

Unit-test it against known Python outputs, including:

- maximum hourly ET0
- mean hourly ET0
- daily total ET0

---

## Phase 4 — Crop ETc and effective rainfall

Implement:

```text
ETc = Kc * ET0
```

and the selected effective-rainfall method.

Create a zone-wise ETc block in Simulink so each zone can have a different Kc.

Outputs per zone:

- ET0
- Kc
- ETc
- rainfall
- effective rainfall
- crop water deficit

---

## Phase 5 — Soil/root-zone model

Create a MATLAB function and a Simulink subsystem for each zone:

```text
S(k+1) = S(k)
       + effective rainfall
       + irrigation infiltration
       - actual ET
       - drainage
       - runoff
```

Track:

- soil storage
- relative soil moisture
- soil moisture percentage
- moisture error
- infiltration
- drainage
- runoff
- water-balance residual

Enforce physical limits between wilting point and saturation.

---

## Phase 6 — FIS 1: Soil Stress

Build with Fuzzy Logic Designer or programmatically using `mamfis`.

Inputs:

- RSM
- moisture error

Output:

- soil stress [%]

Use:

- Mamdani inference
- minimum AND
- maximum OR
- minimum implication
- maximum aggregation
- centroid defuzzification

Import the exact Python membership-function parameters first. Do not redesign them during the first MATLAB port.

---

## Phase 7 — FIS 2: Weather Stress

Inputs:

- temperature
- humidity
- solar radiation
- wind speed
- rainfall

Output:

- weather stress [%]

Implement the exact Python rule base and membership functions.

Verify output parity on a fixed matrix of weather conditions.

---

## Phase 8 — FIS 3: Water Demand

Inputs:

- ETc
- crop water deficit
- effective rainfall

Output:

- water demand [%]

Implement the exact Python Mamdani rules and verify against Python.

---

## Phase 9 — FIS 4: Main Irrigation Controller

Inputs:

- soil stress
- weather stress
- water demand
- moisture error

Output:

- irrigation command [%]

Implement all 32 rules.

Organize the rule viewer into the same five logical layers:

1. oversaturation suppression
2. at-target maintenance
3. deficit replacement
4. severe depletion override
5. climate modulation

This becomes the primary local controller for every zone.

---

## Phase 10 — FIS 5: Supervisory Water Allocation

Inputs per zone:

- available water
- zone demand
- zone stress
- zone priority

Output:

- allocation factor [%]

Important: retain the architecture's two-stage safety design:

```text
Water Allocation FIS
        |
        v
raw allocation factors
        |
        v
bounded priority-weighted water filling
        |
        v
physically feasible allocations
```

Do not allow fuzzy inference to violate the hard supply constraint.

---

## Phase 11 — Multizone Simulink architecture

Build the top-level model:

```text
                         WEATHER ENGINE
                              |
                              v
                           ET0 MODEL
                              |
               +--------------+--------------+
               |              |              |
             ZONE 1         ZONE 2         ZONE 3
               |              |              |
         +-----+-----+  +-----+-----+  +-----+-----+
         |           |  |           |  |           |
       Soil       Crop Soil      Crop Soil       Crop
       Model      ETc  Model     ETc  Model      ETc
         |           |  |           |  |           |
         +-----+-----+  +-----+-----+  +-----+-----+
               |              |              |
          FIS 1/2/3      FIS 1/2/3      FIS 1/2/3
               |              |              |
             FIS 4          FIS 4          FIS 4
               |              |              |
             Req 1          Req 2          Req 3
               +--------------+--------------+
                              |
                       FIS 5 Allocation
                              |
                 Bounded Water Allocation
                              |
               +--------------+--------------+
               |              |              |
             Alloc 1        Alloc 2        Alloc 3
               |              |              |
             Soil           Soil           Soil
             State          State          State
               |              |              |
               +--------------+--------------+
                              |
                           FEEDBACK
```

Use Bus Objects for clean telemetry transport.

---

## Phase 12 — Closed-loop feedback

Every simulation step must follow:

```text
State(k)
 -> fuzzy inference
 -> requested irrigation
 -> allocation
 -> actual irrigation
 -> soil balance
 -> State(k+1)
```

Use Unit Delay/Memory blocks where appropriate to make state transitions explicit.

Log every intermediate variable to the MATLAB workspace and Simulink Data Inspector.

---

## Phase 13 — PSO optimization

Use Global Optimization Toolbox `particleswarm`.

Tune the same 18 Main Irrigation membership-function parameters.

Objective should reproduce the Python composite fitness:

- soil moisture tracking error
- water use
- unmet demand
- command smoothness
- constraint penalties

Training scenarios:

- Normal
- Hot & Dry
- Rainy
- Cloudy

Validation scenarios:

- Heatwave
- Water Scarcity

Do not optimize directly on the validation scenarios.

After optimization:

```text
PSO theta*
   -> validate constraints
   -> save MAT/JSON parameter file
   -> load into Main Irrigation FIS
   -> rerun all scenarios
```

---

## Phase 14 — Verification and parity testing

Create a fixed test vector file shared by Python and MATLAB.

Compare:

- membership degrees
- individual FIS outputs
- fired-rule strengths
- ET0
- ETc
- soil balance
- water allocation
- final moisture
- total water used
- unmet demand
- conservation residual

Target numerical tolerance:

```text
FIS outputs: <= 1e-3 to 1e-2 depending on discretization
water balance residual: near machine precision
allocation: exact within numerical tolerance
```

---

## Phase 15 — MATLAB visualization/dashboard

Create figures for:

1. Weather variables
2. ET0/ETc
3. Soil moisture by zone
4. Soil stress
5. Weather stress
6. Water demand
7. Irrigation command
8. Requested vs allocated water
9. Unmet demand
10. Allocation priority
11. Water-balance residual
12. PSO convergence
13. Baseline vs optimized membership functions
14. Baseline vs optimized closed-loop tracking

Use Simulink Data Inspector for step-by-step debugging.

---

## Phase 16 — Final validation scenarios

Run all six scenarios for 24 hours at 1-minute resolution.

For each scenario report:

- total requested water
- total allocated water
- unmet water
- fulfillment ratio
- mean MAE
- RMSE
- minimum moisture
- maximum moisture
- final moisture
- constrained timestep percentage
- maximum water-balance residual

The final MATLAB report should contain a scenario comparison table and controller-response plots.

---

## Phase 17 — Final Simulink deliverable

Final deliverables:

```text
smart_multizone_irrigation.slx
smart_multizone_irrigation_init.m
run_all_scenarios.m
run_pso_optimization.m
verify_python_matlab_parity.m
README_MATLAB_SIMULINK.md
```

The final model should be demonstrable without hardware and should run entirely from simulated weather, crop, soil, fuzzy-control, and water-supply models.
