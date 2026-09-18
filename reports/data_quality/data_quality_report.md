# Data Quality & Integrity Report — Phase 1

> **Project**: Smart Multizone Irrigation and Water Resource Management Using Hierarchical Adaptive Fuzzy Control  
> **Scope**: Phase 1 Dataset & Agricultural Parameter Foundation  
> **Evaluation Status**: Cleaned, Standardized, and Validated

---

## 1. Executive Summary

This report provides formal statistical profiling and validation metrics for the datasets powering the
smart multizone irrigation system. In accordance with Phase 1 directives, all data assets are strictly separated
into **Measured/Observed**, **Model Assumptions**, and **Derived Parameters**, establishing a physically grounded
numerical foundation without premature fuzzy membership evaluation.

---

## 2. Dataset Inventories & Quality Metrics

| Dataset Name | File Path | Records | Features | Missing Values | Duplicate Timestamps | Source | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :---: |
| **Crop Agronomic Database** | `data/crop_database.csv` | 14 | 10 | 0 | 0 | FAO-56 Table 12 | **VERIFIED** |
| **Soil Hydraulic Database** | `data/soil_database.csv` | 5 | 9 | 0 | 0 | USDA-NRCS / FAO Land & Water | **VERIFIED** |
| **Raw Meteorological Records** | `data/raw/weather_raw.csv` | 25 | 7 | 0 | 0 | NASA POWER / NOAA ISD Baseline | **VERIFIED** |
| **Clean Meteorological Dataset** | `data/processed/weather_clean.csv` | 1441 | 6 | 0 | 0 | Preprocessed & Resampled (1-min) | **VERIFIED** |
| **Unified Multizone Dataset** | `data/processed/irrigation_dataset.csv` | 4323 | 21 | 25938 | 0 | Synthesized Multizone Observations | **VERIFIED** |

---

## 3. Statistical Distribution & Physical Ranges

### 3.1 Cleaned Weather Observations (1440-step, 24-hour Diurnal Profile)

| Variable | Unit | Min | Mean | Max | Std Dev | Physical Validity |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `temperature` | °C | 18.00 | 25.24 | 34.20 | 5.62 | PASS (Within Bounds) |
| `humidity` | % | 42.50 | 67.44 | 87.50 | 15.78 | PASS (Within Bounds) |
| `solar_radiation` | W/m² | 0.00 | 306.95 | 915.20 | 350.22 | PASS (Within Bounds) |
| `wind_speed` | m/s | 1.40 | 2.32 | 3.60 | 0.71 | PASS (Within Bounds) |
| `rainfall` | mm | 0.00 | 0.00 | 0.00 | 0.00 | PASS (Within Bounds) |

### 3.2 Crop Agronomic Parameters (FAO-56)

| Crop | Growth Stage | $K_{c,\text{ini}}$ | $K_{c,\text{mid}}$ | $K_{c,\text{end}}$ | Root Depth (m) | Depletion Fraction ($p$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Tomato** | Initial | 0.6 | 1.15 | 0.8 | 0.7–1.5 | 0.4 |
| **Tomato** | Development | 0.6 | 1.15 | 0.8 | 0.7–1.5 | 0.4 |
| **Tomato** | Mid-season | 0.6 | 1.15 | 0.8 | 0.7–1.5 | 0.4 |
| **Tomato** | Late-season | 0.6 | 1.15 | 0.8 | 0.7–1.5 | 0.4 |
| **Wheat** | Initial | 0.3 | 1.15 | 0.25 | 1.0–1.8 | 0.55 |
| **Wheat** | Development | 0.3 | 1.15 | 0.25 | 1.0–1.8 | 0.55 |
| **Wheat** | Mid-season | 0.3 | 1.15 | 0.25 | 1.0–1.8 | 0.55 |
| **Wheat** | Late-season | 0.3 | 1.15 | 0.25 | 1.0–1.8 | 0.55 |
| **Maize** | Initial | 0.3 | 1.2 | 0.35 | 1.0–1.7 | 0.55 |
| **Maize** | Development | 0.3 | 1.2 | 0.35 | 1.0–1.7 | 0.55 |
| **Maize** | Mid-season | 0.3 | 1.2 | 0.35 | 1.0–1.7 | 0.55 |
| **Maize** | Late-season | 0.3 | 1.2 | 0.35 | 1.0–1.7 | 0.55 |
| **Potato** | Initial | 0.5 | 1.15 | 0.75 | 0.4–0.6 | 0.35 |
| **Cotton** | Initial | 0.35 | 1.2 | 0.6 | 1.0–1.7 | 0.65 |

### 3.3 Soil Hydraulic Properties (USDA/FAO Baseline)

| Soil Texture | Field Capacity ($FC$) | Wilting Point ($WP$) | Available Water ($AWC$) | Saturation | Infiltration Rate ($mm/h$) | Drainage Coeff |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Loam** | 28.0% | 14.0% | 14.0% | 46.0% | 20.0 | 0.08 |
| **Sandy** | 18.0% | 8.0% | 10.0% | 38.0% | 45.0 | 0.18 |
| **Clay** | 36.0% | 20.0% | 16.0% | 52.0% | 5.0 | 0.03 |
| **Sandy Loam** | 22.0% | 10.0% | 12.0% | 42.0% | 30.0 | 0.12 |
| **Silty Clay** | 34.0% | 19.0% | 15.0% | 50.0% | 6.0 | 0.04 |

---

## 4. Multi-Zone Model Assumptions (Section 6 Specification)

| Zone ID | Label | Crop | Soil | Area ($m^2$) | Field Capacity | Wilting Point | Initial Moisture | Target Moisture | Priority |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | Zone 1 | Tomato | Loam | 100 | 70.0% | 25.0% | 55.0% | 60.0% | 2 |
| **2** | Zone 2 | Wheat | Sandy | 120 | 60.0% | 18.0% | 42.0% | 55.0% | 1 |
| **3** | Zone 3 | Maize | Clay | 80 | 75.0% | 30.0% | 65.0% | 65.0% | 3 |

> **Note**: These initial zone values represent explicit model simulation assumptions to be validated against empirical dynamics in subsequent phases.

---

## 5. Data Pipeline Transformations Performed

1. **Header Standardization**: Normalizing heterogeneous meteorological column notations (`TEMP_2M_C` -> `temperature`, etc.).
2. **Temporal Alignment & Resampling**: Ingesting 25 hourly observations (00:00 to 24:00) and performing continuous time interpolation to standard 1-minute steps (1441 timestamps spanning 24 full hours).
3. **Boundary Verification**: Physical domain validation preventing negative solar radiation or impossible humidities.
4. **Multi-Zone Denormalization**: Replicating meteorological time-series for each zone with bound-checked pedological parameters into `data/processed/irrigation_dataset.csv`.
5. **Strict Constraint Preservation**: No dummy calculation of ET0, ETc, or soil-water balances; downstream fields explicitly kept as uncomputed (`NaN`) awaiting future phases.