# Simulink Smart Multizone Irrigation Architecture

This directory contains the Simulink block diagram and setup scripts for the **Smart Multizone Irrigation Closed-Loop Control System**.

---

## 1. Top-Level Model Architecture

The multizone model represents the closed-loop control topology:

```text
                        WEATHER ENGINE (T, RH, Rs, u2, P)
                                       │
                                       ▼
                             ET0 SUBSYSTEM (FAO-56)
                                       │
                   ┌───────────────────┼───────────────────┐
                   ▼                   ▼                   ▼
                ZONE 1              ZONE 2              ZONE 3
             Tomato / Loam       Wheat / Sandy        Maize / Clay
            (Crop ETc, Soil)    (Crop ETc, Soil)    (Crop ETc, Soil)
                   │                   │                   │
                   ▼                   ▼                   ▼
             Local FIS 1/3       Local FIS 1/3       Local FIS 1/3
                   │                   │                   │
                   ▼                   ▼                   ▼
              FIS 4 (Main)        FIS 4 (Main)        FIS 4 (Main)
             Request R_1 (L)     Request R_2 (L)     Request R_3 (L)
                   │                   │                   │
                   └───────────────────┼───────────────────┘
                                       │
                                       ▼
                       SUPERVISORY ARBITRATOR (FIS 5)
                      + Bounded Water-Filling Algorithm
                                       │
                   ┌───────────────────┼───────────────────┐
                   ▼                   ▼                   ▼
              Allocated A_1       Allocated A_2       Allocated A_3
                   │                   │                   │
                   ▼                   ▼                   ▼
             SOIL RESERVOIR      SOIL RESERVOIR      SOIL RESERVOIR
             Infiltration/Drain  Infiltration/Drain  Infiltration/Drain
                   │                   │                   │
                   └───────────────────┴───────────────────┘
                                       │
                                       ▼
                           FEEDBACK: SM(t+1) TO STEP t+1
```

---

## 2. Model Initialization

Before opening or running the Simulink model, run the initialization script to populate the base workspace:
```matlab
smart_multizone_init
```
This loads:
1. `fis_soil`: Loaded from `soil_stress.fis`
2. `fis_weather`: Loaded from `weather_stress.fis`
3. `fis_demand`: Loaded from `water_demand.fis`
4. `fis_main`: Loaded from `main_irrigation.fis`
5. `fis_alloc`: Loaded from `water_allocation.fis`
6. `Zone1`, `Zone2`, `Zone3` parameter structures.
