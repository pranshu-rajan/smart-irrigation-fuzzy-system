import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import numpy as np
import pandas as pd

from config.schemas import SimulationScenario
from simulation.closed_loop import ClosedLoopSimulator, ClosedLoopConfig
from config.defaults import get_default_zones
from simulation.weather import WeatherEngine
from models.et0 import compute_et0_timeseries
from models.etc import (
    CropCoefficientManager,
    calculate_effective_rainfall,
    calculate_crop_water_deficit,
)
from models.soil import (
    calculate_relative_soil_moisture,
    calculate_moisture_error,
)
from models.water_balance import (
    SoilState,
    initialize_soil_state,
    update_water_balance,
)
from fuzzy_engine.irrigation import MainIrrigationFIS
from fuzzy_engine.soil_stress import SoilStressFIS
from fuzzy_engine.weather_stress import WeatherStressFIS
from fuzzy_engine.water_demand import WaterDemandFIS
from optimization.fitness import compute_scenario_fitness, FitnessWeights

zone = get_default_zones()[0]
scenario = SimulationScenario.NORMAL

w_engine = WeatherEngine(scenario=scenario, seed=42)
w_df = w_engine.generate_timeline(duration_hours=24, timestep_minutes=1)
et0_df = compute_et0_timeseries(w_df, timestep_minutes=1)

fis_main = MainIrrigationFIS(resolution=501)

# 1. Standard ClosedLoopSimulator run
t0 = time.time()
cfg = ClosedLoopConfig(scenario=scenario, zone_id=zone.zone_id, seed=42)
sim = ClosedLoopSimulator(config=cfg, zone_config=zone, fis_main=fis_main)
df_orig, met_orig = sim.run(mode="fuzzy", weather_df=w_df, et0_df=et0_df)
fit_orig = compute_scenario_fitness(
    df=df_orig,
    metrics=met_orig,
    weights=FitnessWeights(),
    target_moisture=zone.target_moisture,
    wilting_point=zone.soil.wilting_point,
    field_capacity=zone.soil.field_capacity,
)
t_orig = time.time() - t0
print(f"Original simulator: {t_orig:.3f}s | J = {fit_orig.total_fitness:.6f} | MAE = {fit_orig.mae_pct:.4f} | Vol = {fit_orig.water_volume_l:.2f}L")

# 2. Precomputing weather_stress and water_demand
fis_weather = WeatherStressFIS(resolution=501)
fis_water = WaterDemandFIS(resolution=501)
fis_soil = SoilStressFIS(resolution=501)

n = len(w_df)
weather_stress_arr = np.zeros(n)
water_demand_arr = np.zeros(n)
peff_arr = np.zeros(n)
etc_arr = np.zeros(n)
rain_arr = w_df["rainfall"].values
et0_arr = et0_df["et0"].values
temp_arr = w_df["temperature"].values
hum_arr = w_df["humidity"].values
sol_arr = w_df["solar_radiation"].values
wind_arr = w_df["wind_speed"].values

kc = zone.crop.kc
for t in range(n):
    weather_stress_arr[t] = fis_weather.evaluate(
        temperature=float(temp_arr[t]),
        humidity=float(hum_arr[t]),
        solar_radiation=float(sol_arr[t]),
        wind_speed=float(wind_arr[t]),
        rainfall=float(rain_arr[t]),
    )
    etc_t = kc * float(et0_arr[t])
    etc_arr[t] = etc_t
    peff_t = calculate_effective_rainfall(float(rain_arr[t]), timestep_minutes=1)
    peff_arr[t] = peff_t
    deficit_t = calculate_crop_water_deficit(etc_t, peff_t)
    water_demand_arr[t] = fis_water.evaluate(
        etc=etc_t,
        crop_water_deficit=deficit_t,
        effective_rainfall=peff_t,
    )

print(f"Precomputed weather & water stress arrays for {n} timesteps.")

# Now test fast step loop
t1 = time.time()
crop_db = CropCoefficientManager.load_crop_database()
crop_match = crop_db[crop_db["crop"].str.capitalize() == zone.crop.name.capitalize()]
p_frac = float(crop_match.iloc[0]["depletion_fraction_p"]) if not crop_match.empty else 0.50

current_state = initialize_soil_state(
    zone_config=zone,
    depletion_fraction_p=p_frac,
    timestamp=str(w_df["timestamp"].iloc[0]),
)

target_sm = zone.target_moisture
wp = zone.soil.wilting_point
fc = zone.soil.field_capacity
sat = zone.soil.saturation
infilt_cap = zone.soil.infiltration_rate_mm_h
drain_param = zone.soil.drainage_parameter
zr = zone.crop.root_depth_m
dt_min = 1
timestep_hours = dt_min / 60.0

moisture_errors = np.zeros(n)
applied_vols_l = np.zeros(n)
soil_moistures = np.zeros(n)
commands = np.zeros(n)

for step in range(n):
    sm_t = current_state.soil_moisture
    error_t = calculate_moisture_error(target_sm, sm_t)
    moisture_errors[step] = error_t
    soil_moistures[step] = sm_t
    
    rsm_t = calculate_relative_soil_moisture(sm_t, wp, fc)
    soil_stress_t = fis_soil.evaluate(rsm=rsm_t, moisture_error=error_t)
    
    cmd_t = fis_main.evaluate(
        soil_stress=soil_stress_t,
        weather_stress=weather_stress_arr[step],
        water_demand=water_demand_arr[step],
        moisture_error=error_t,
    )
    commands[step] = cmd_t
    
    fractional_cmd = float(cmd_t) / 100.0
    eff_infilt = float(fractional_cmd * cfg.max_irrigation_rate_mm_h * timestep_hours)
    app_vol_l = eff_infilt * zone.area_m2
    applied_vols_l[step] = app_vol_l
    
    current_state = update_water_balance(
        current_state=current_state,
        irrigation_mm=eff_infilt,
        effective_rainfall_mm=peff_arr[step],
        etc_mm=etc_arr[step],
        timestep_minutes=dt_min,
        infiltration_rate_mm_h=infilt_cap,
        drainage_parameter=drain_param,
        timestamp=str(w_df["timestamp"].iloc[step]),
    )

t_fast = time.time() - t1
print(f"Fast step loop: {t_fast:.3f}s (Speedup: {t_orig / t_fast:.1f}x)")

mae_fast = float(np.mean(np.abs(moisture_errors)))
rmse_fast = float(np.sqrt(np.mean(moisture_errors ** 2)))
vol_fast = float(np.sum(applied_vols_l))

print(f"Fast MAE: {mae_fast:.4f} vs Orig MAE: {fit_orig.mae_pct:.4f}")
print(f"Fast RMSE: {rmse_fast:.4f} vs Orig RMSE: {fit_orig.rmse_pct:.4f}")
print(f"Fast Vol: {vol_fast:.2f}L vs Orig Vol: {fit_orig.water_volume_l:.2f}L")
