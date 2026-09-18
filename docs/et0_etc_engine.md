# FAO-56 Penman-Monteith ET0 / ETc Engineering Documentation

This document provides the mathematical, physical, and agronomic foundation for the reference evapotranspiration ($ET_0$), crop evapotranspiration ($ET_c$), effective precipitation ($P_{\text{eff}}$), and atmospheric crop water deficit ($D_{\text{crop}}$) engine of the **Smart Multizone Irrigation System**.

---

## 1. Parameter Table

| Parameter | Symbol | Standard Unit | Source / Physical Meaning |
| :--- | :--- | :--- | :--- |
| **Air Temperature** | $T$ | $^\circ\text{C}$ | Ambient temperature at 2 m height (`WeatherEngine`) |
| **Relative Humidity** | $RH$ | $\%$ | Ratio of actual to saturation vapor pressure (`WeatherEngine`) |
| **Solar Irradiance** | $R_s$ | $\text{W/m}^2$ | Global downward solar irradiance at surface |
| **Wind Speed** | $u_2$ | $\text{m/s}$ | Horizontal wind speed measured at 2 m elevation |
| **Raw Precipitation** | $P$ | $\text{mm}$ | Unfiltered surface precipitation (`WeatherEngine`) |
| **Station Elevation** | $z$ | $\text{m}$ | Site height above mean sea level (Ahmedabad: $53.0\text{ m}$) |
| **Geographic Latitude** | $\phi$ | $^\circ\text{N}$ | Station latitude (Ahmedabad: $23.02^\circ\text{N}$) |
| **Atmospheric Pressure** | $P_{\text{atm}}$ | $\text{kPa}$ | Barometric pressure derived from elevation (FAO-56 Eq. 7) |
| **Psychrometric Constant** | $\gamma$ | $\text{kPa}/^\circ\text{C}$ | Psychrometric constant (FAO-56 Eq. 8) |
| **Saturation Vapor Pressure** | $e_s$ | $\text{kPa}$ | Saturation vapor pressure at temperature $T$ (FAO-56 Eq. 11) |
| **Actual Vapor Pressure** | $e_a$ | $\text{kPa}$ | Vapor pressure at temperature $T$ and $RH$ (FAO-56 Eq. 17) |
| **Vapor Pressure Deficit** | $VPD$ | $\text{kPa}$ | Atmospheric evaporative dryness $e_s - e_a$ |
| **Slope of Vapor Pressure** | $\Delta$ | $\text{kPa}/^\circ\text{C}$ | Derivative $\frac{de_s}{dT}$ at temperature $T$ (FAO-56 Eq. 13) |
| **Extraterrestrial Radiation**| $R_a$ | $\text{MJ}/(\text{m}^2\cdot\text{h})$ | Solar radiation at top of atmosphere (FAO-56 Eq. 28, 48) |
| **Clear-Sky Radiation** | $R_{so}$ | $\text{MJ}/\text{m}^2$ | Theoretical maximum solar radiation at surface (FAO-56 Eq. 37) |
| **Net Shortwave Radiation**| $R_{ns}$ | $\text{MJ}/\text{m}^2$ | Net absorbed solar energy with albedo $\alpha = 0.23$ (FAO-56 Eq. 38) |
| **Net Longwave Radiation** | $R_{nl}$ | $\text{MJ}/\text{m}^2$ | Net upward thermal radiation loss (FAO-56 Eq. 39 & 55) |
| **Net Radiation** | $R_n$ | $\text{MJ}/\text{m}^2$ | Surface net radiation balance $R_{ns} - R_{nl}$ |
| **Soil Heat Flux Density** | $G$ | $\text{MJ}/\text{m}^2$ | Thermal conduction into ground (FAO-56 Eq. 42, 45, 46) |
| **Reference ET** | $ET_0$ | $\text{mm/day}$ or $\text{mm/step}$ | Evapotranspiration from hypothetical grass reference crop |
| **Crop Coefficient** | $K_c$ | Dimensionless | Phenological crop coefficient from FAO-56 Table 12 |
| **Crop Evapotranspiration**| $ET_c$ | $\text{mm/step}$ or $\text{mm/day}$| Non-stressed crop water requirement $K_c \times ET_0$ |
| **Effective Precipitation** | $P_{\text{eff}}$| $\text{mm}$ | Infiltrated rainfall retained in root zone (USDA-SCS) |
| **Crop Water Deficit** | $D_{\text{crop}}$| $\text{mm}$ | Atmospheric unfulfilled demand $\max(0, ET_c - P_{\text{eff}})$ |

---

## 2. Atmospheric and Thermodynamic Equations

### 2.1 Atmospheric Pressure ($P$)
According to FAO-56 Eq. 7, barometric pressure decreases with elevation $z$ (m):
$$P = 101.3 \left( \frac{293 - 0.0065 z}{293} \right)^{5.26}$$
For the Ahmedabad baseline testbed ($z = 53\text{ m}$):
$$P = 101.3 \left( \frac{293 - 0.0065 \times 53}{293} \right)^{5.26} = 100.675\text{ kPa}$$

### 2.2 Psychrometric Constant ($\gamma$)
According to FAO-56 Eq. 8:
$$\gamma = \frac{c_p P}{\epsilon \lambda} \approx 0.665 \times 10^{-3} P = 0.000665 \times P$$
For $P = 100.675\text{ kPa}$:
$$\gamma = 0.06695\text{ kPa}/^\circ\text{C}$$

### 2.3 Saturation Vapor Pressure ($e_s$)
FAO-56 Eq. 11 defines saturation vapor pressure over liquid water:
$$e_s(T) = 0.6108 \exp\left( \frac{17.27 T}{T + 237.3} \right)$$
Where $T$ is air temperature in $^\circ\text{C}$.

### 2.4 Actual Vapor Pressure ($e_a$) and Vapor Pressure Deficit ($VPD$)
From relative humidity $RH$ (FAO-56 Eq. 17):
$$e_a = e_s(T) \times \frac{RH}{100}$$
Atmospheric evaporative suction (Vapor Pressure Deficit):
$$VPD = \max(0.0, e_s - e_a) = e_s \left(1 - \frac{RH}{100}\right)$$

### 2.5 Slope of Saturation Vapor Pressure Curve ($\Delta$)
The tangent slope $\frac{de_s}{dT}$ at temperature $T$ (FAO-56 Eq. 13):
$$\Delta = \frac{4098 \cdot e_s(T)}{(T + 237.3)^2} = \frac{4098 \times 0.6108 \exp\left(\frac{17.27 T}{T + 237.3}\right)}{(T + 237.3)^2}$$

---

## 3. Surface Radiation and Energy Balance Equations

### 3.1 Unit Conversions for Solar Irradiance
The weather engine generates instantaneous global irradiance $R_s$ in $\text{W/m}^2$.
Over a discrete simulation timestep of $\Delta t$ minutes ($\Delta t = 1\text{ min}$):
$$\text{Energy } [\text{MJ}/\text{m}^2] = R_s [\text{W}/\text{m}^2] \times (\Delta t \times 60\text{ s}) \times 10^{-6} = R_s \times \Delta t \times 6 \times 10^{-5}$$
For hourly equivalent rate:
$$R_{s,\text{hourly}} [\text{MJ}/(\text{m}^2\cdot\text{h})] = R_s [\text{W}/\text{m}^2] \times 3600 \times 10^{-6} = R_s \times 0.0036$$
For 24-hour daily energy:
$$R_{s,\text{daily}} [\text{MJ}/(\text{m}^2\cdot\text{day})] = R_s [\text{W}/\text{m}^2] \times 86400 \times 10^{-6} = R_s \times 0.0864$$

### 3.2 Net Shortwave Radiation ($R_{ns}$)
Reflected radiation is governed by the hypothetical grass reference albedo ($\alpha = 0.23$) (FAO-56 Eq. 38):
$$R_{ns} = (1 - \alpha) R_s = 0.77 R_s$$

### 3.3 Net Longwave Radiation ($R_{nl}$)
FAO-56 Eq. 39 and Eq. 55 compute upward thermal blackbody radiation minus downward atmospheric counter-radiation:
$$R_{nl} = \sigma (T + 273.16)^4 \left( 0.34 - 0.14 \sqrt{e_a} \right) \left( 1.35 \frac{R_s}{R_{so}} - 0.35 \right)$$
Where:
- $\sigma = 2.043 \times 10^{-10}\text{ MJ}/(\text{K}^4\cdot\text{m}^2\cdot\text{h})$ for hourly periods ($\sigma_{\text{daily}} = 4.903 \times 10^{-9}\text{ MJ}/(\text{K}^4\cdot\text{m}^2\cdot\text{day})$).
- $\left( 0.34 - 0.14 \sqrt{e_a} \right)$ models atmospheric emissivity.
- $\left( 1.35 \frac{R_s}{R_{so}} - 0.35 \right)$ represents the cloudiness factor (clamped between $0.05$ and $1.0$). At night, $R_s / R_{so}$ defaults to $0.75$ representing clear/semi-clear nocturnal radiation loss.

### 3.4 Net Radiation ($R_n$)
$$R_n = R_{ns} - R_{nl}$$
- During the day: $R_{ns} > R_{nl} \implies R_n > 0$.
- At night: $R_{ns} = 0 \implies R_n = -R_{nl} < 0$ (radiative cooling).

### 3.5 Soil Heat Flux Density ($G$)
In accordance with FAO-56 Chapter 3 & 4:
- **Daily timescale** (FAO-56 Eq. 42): Over a 24-hour cycle, heat stored in soil during daylight is returned to the air at night:
  $$G_{\text{daily}} \approx 0.0\text{ MJ}/(\text{m}^2\cdot\text{day})$$
- **Sub-daily / hourly timestep** (FAO-56 Eq. 45 & 46):
  - Daylight ($R_n > 0$): $G = 0.10 \times R_n$
  - Nighttime ($R_n \le 0$): $G = 0.50 \times R_n$

---

## 4. FAO-56 Penman-Monteith Reference Evapotranspiration ($ET_0$)

### 4.1 Sub-Daily Formulation (Simulation Timestep Resolution)
For sub-daily periods ($\Delta t = 1$ to $60\text{ min}$), FAO-56 Eq. 53 defines:
$$ET_{0,\text{hr}} [\text{mm/hour}] = \frac{0.408 \Delta (R_{n,\text{hr}} - G_{\text{hr}}) + \gamma \frac{37}{T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}$$
Where $R_{n,\text{hr}}$ and $G_{\text{hr}}$ are net radiation and soil heat flux expressed in $\text{MJ}/(\text{m}^2\cdot\text{hour})$.
The depth accumulated over the simulation timestep ($\Delta t = 1\text{ min}$) is:
$$ET_{0,\text{step}} [\text{mm/step}] = ET_{0,\text{hr}} \times \frac{\Delta t}{60}$$
The equivalent instantaneous 24-hour rate is:
$$ET_{0,\text{rate}} [\text{mm/day}] = ET_{0,\text{hr}} \times 24$$

### 4.2 Standard 24-Hour Daily Formulation
$$ET_{0,\text{daily}} [\text{mm/day}] = \frac{0.408 \Delta (R_{n,\text{daily}} - G_{\text{daily}}) + \gamma \frac{900}{T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}$$
Where the aerodynamic coefficient $900 \approx 37.5 \times 24$.

---

## 5. Crop Evapotranspiration ($ET_c$) and Phenology

### 5.1 Single Crop Coefficient Method (FAO-56 Eq. 56)
$$ET_c(t) = K_c \times ET_0(t)$$
Where $K_c$ incorporates crop aerodynamic resistance, leaf area index, and canopy resistance.

### 5.2 Phenological Growth Stages and Interpolation
The four developmental phases (FAO-56 Chapter 6):
1. **Initial**: Emergence to $10\%$ canopy ground cover.
   $$K_c = K_{c,\text{ini}}$$
2. **Development**: From $10\%$ to effective full ground cover ($70\text{--}80\%$). Linear interpolation as progress fraction $p \in [0.0, 1.0]$:
   $$K_c(p) = K_{c,\text{ini}} + p \cdot (K_{c,\text{mid}} - K_{c,\text{ini}})$$
3. **Mid-season**: Peak reproductive phase, flowering, and fruit setting:
   $$K_c = K_{c,\text{mid}}$$
4. **Late-season**: Ripening, senescence, and harvest maturity:
   $$K_c(p) = K_{c,\text{mid}} + p \cdot (K_{c,\text{end}} - K_{c,\text{mid}})$$

### 5.3 Initial 3 Agricultural Zones
- **Zone 1: Tomato** (Loam, $100\text{ m}^2$): Mid-season $\implies K_c = 1.15$
- **Zone 2: Wheat** (Sandy, $120\text{ m}^2$): Development stage ($p = 0.50$, $K_{c,\text{ini}}=0.30, K_{c,\text{mid}}=1.15$) $\implies K_c = 0.85$
- **Zone 3: Maize** (Clay, $80\text{ m}^2$): Mid-season $\implies K_c = 1.20$

---

## 6. Hydrological Precipitation and Water Deficit

### 6.1 Effective Precipitation ($P_{\text{eff}}$)
Precipitation that enters and is retained in the root zone, excluding surface runoff and canopy interception.
- **USDA Soil Conservation Service (SCS) method**:
  For daily rainfall $P$ (mm/day):
  $$P_{\text{eff}} = \begin{cases}
  P \times \left( \frac{125 - 0.2 P}{125} \right) & \text{if } P \le 83.3\text{ mm/day} \\
  \frac{125}{3} + 0.1 P & \text{if } P > 83.3\text{ mm/day}
  \end{cases}$$
- **Sub-daily timestep implementation**: Events smaller than the canopy interception threshold ($0.2\text{ mm}$) are evaporated directly. Events exceeding interception retain an $80\%$ infiltration efficiency:
  $$P_{\text{eff}} = \max\left(0.0, 0.80 \times (P - P_{\text{thresh}})\right)$$

### 6.2 Atmospheric Crop Water Deficit ($D_{\text{crop}}$)
The atmospheric water demand unsatisfied by effective natural rainfall:
$$D_{\text{crop}} = \max\left(0.0, ET_c - P_{\text{eff}}\right)$$

### 6.3 CRITICAL CONCEPTUAL DISTINCTION
It is crucial to distinguish between the two deficit quantities in this system:
1. **Atmospheric / Crop Water Deficit** ($D_{\text{crop}}$):
   $$D_{\text{crop}} = \max(ET_c - P_{\text{eff}}, 0.0) \quad [\text{mm}]$$
   A meteorological and crop-canopy demand parameter feeding the **Water Demand FIS**.
2. **Soil Moisture Control Error** ($e(t)$):
   $$e(t) = SM_{\text{target}} - SM(t) \quad [\% \text{ or } \text{m}^3/\text{m}^3]$$
   A closed-loop state tracking deviation in the root zone feeding the **Main Irrigation FIS**.

These variables operate on different domains, physical units, and dynamical timescales.
