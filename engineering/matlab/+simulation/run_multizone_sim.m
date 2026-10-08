function results = run_multizone_sim(scenario_name, duration_hours, dt_minutes, custom_pso_params)
% RUN_MULTIZONE_SIM Executes 3-Zone Hierarchical Closed-Loop Irrigation Simulation
%
% Integrates:
%   1. Dynamic Meteorology (WeatherEngine)
%   2. FAO-56 Penman-Monteith Evapotranspiration (ET0)
%   3. Crop ETc & USDA Soil-Water Deficit
%   4. FIS 1: Soil Stress FIS
%   5. FIS 2: Weather Stress FIS
%   6. FIS 3: Water Demand FIS
%   7. FIS 4: Main Supervisory Irrigation FIS (Optionally PSO tuned)
%   8. FIS 5: Supervisory Water Allocation FIS
%   9. Bounded Priority-Weighted Water Filling Arbitrator
%  10. Root-Zone Hydrology & Soil-Water Balance State Transitions S(t+1)
%
% Usage:
%   results = simulation.run_multizone_sim('Normal', 24, 1);
%   results = simulation.run_multizone_sim('Water Scarcity', 24, 1);

if nargin < 1 || isempty(scenario_name)
    scenario_name = 'Normal';
end
if nargin < 2 || isempty(duration_hours)
    duration_hours = 24;
end
if nargin < 3 || isempty(dt_minutes)
    dt_minutes = 60; % Standard hourly decision cycle for fast execution
end
if nargin < 4
    custom_pso_params = [];
end

% 1. Load configuration and systems
zones = config.load_default_zones();
alloc_cfg = config.load_allocation_defaults();
num_zones = numel(zones);

% Build or load FIS systems
fis_soil = fuzzy_builder.build_soil_stress_fis();
fis_weather = fuzzy_builder.build_weather_stress_fis();
fis_demand = fuzzy_builder.build_water_demand_fis();
fis_main = fuzzy_builder.build_main_irrigation_fis(custom_pso_params);
fis_alloc = fuzzy_builder.build_water_allocation_fis();

% 2. Synthesize weather timeline
w_engine = weather.WeatherEngine(scenario_name, 42);
timeline = w_engine.generate_timeline(duration_hours, dt_minutes);
total_steps = timeline.total_steps;

% 3. Pre-allocate state and telemetry matrices
time_min = timeline.minutes;
time_hr = timeline.hours;

% Atmospheric telemetry
et0_daily = zeros(total_steps, 1);
weather_stress_ts = zeros(total_steps, 1);

% Zone telemetry arrays [steps x num_zones]
sm_ts = zeros(total_steps, num_zones);
rsm_ts = zeros(total_steps, num_zones);
error_ts = zeros(total_steps, num_zones);
soil_stress_ts = zeros(total_steps, num_zones);
etc_daily_ts = zeros(total_steps, num_zones);
water_demand_ts = zeros(total_steps, num_zones);
cmd_ts = zeros(total_steps, num_zones);
req_vol_ts = zeros(total_steps, num_zones);
alloc_vol_ts = zeros(total_steps, num_zones);
unmet_vol_ts = zeros(total_steps, num_zones);
irrig_depth_ts = zeros(total_steps, num_zones);
peff_depth_ts = zeros(total_steps, num_zones);
drainage_depth_ts = zeros(total_steps, num_zones);
actual_et_depth_ts = zeros(total_steps, num_zones);
residuals_ts = zeros(total_steps, num_zones);

% Initialize moisture states
for z = 1:num_zones
    sm_ts(1, z) = zones(z).initial_moisture;
end

% Maximum delivery rate: calibrated at 4.0 mm/h for discrete hourly control cycle
max_rate_mm_h = 4.0;
cutoff_cmd = 18.0; % Deadband threshold corresponding to linguistic term 'Off'
priorities_pct = [zones.priority];

% 4. Master Time-Stepping Simulation Loop
for t = 1:total_steps
    % Sample weather
    T = timeline.temperature(t);
    RH = timeline.humidity(t);
    Rs = timeline.solar_radiation(t);
    u2 = timeline.wind_speed(t);
    P = timeline.rainfall(t);
    waf = timeline.water_availability_factor;

    % Subsystem 1: FAO-56 ET0
    et0_val = models.calculate_fao56_et0(T, RH, Rs, u2);
    et0_daily(t) = et0_val;

    % Subsystem 2: Weather Stress FIS
    w_stress = evalfis(fis_weather, [T, RH, Rs, u2, P]);
    weather_stress_ts(t) = w_stress;

    % Available shared water in Liters for current minute
    avail_supply_vol = alloc_cfg.nominal_flow_rate_l_min * waf * dt_minutes;
    avail_water_pct = waf * 100.0;

    % Step A: Local per-zone inference
    raw_req_vol = zeros(1, num_zones);
    for z = 1:num_zones
        curr_sm = sm_ts(t, z);
        [rsm, err] = models.calculate_soil_indices(curr_sm, zones(z).target_moisture, ...
                                                   zones(z).field_capacity, zones(z).wilting_point);
        rsm_ts(t, z) = rsm;
        error_ts(t, z) = err;

        % FIS 1: Soil Stress
        s_stress = evalfis(fis_soil, [rsm, err]);
        soil_stress_ts(t, z) = s_stress;

        % Crop ETc & Deficit
        peff_step = models.calculate_effective_rain(P, zones(z).field_capacity, zones(z).wilting_point);
        peff_depth_ts(t, z) = peff_step;
        peff_daily_equiv = peff_step * (1440.0 / dt_minutes);
        [etc_d, deficit_d] = models.calculate_crop_etc(et0_val, zones(z).kc, peff_daily_equiv);
        etc_daily_ts(t, z) = etc_d;

        % FIS 3: Water Demand
        w_demand = evalfis(fis_demand, [etc_d, deficit_d, peff_daily_equiv]);
        water_demand_ts(t, z) = w_demand;

        % FIS 4: Main Supervisory Irrigation FIS
        cmd = evalfis(fis_main, [s_stress, w_stress, w_demand, err]);
        if cmd < cutoff_cmd
            eff_cmd = 0.0;
        else
            eff_cmd = cmd;
        end
        cmd_ts(t, z) = eff_cmd;

        % Raw unconstrained volumetric request (Liters)
        req_l = (eff_cmd / 100.0) * (max_rate_mm_h * zones(z).area_m2 * dt_minutes / 60.0);
        raw_req_vol(z) = req_l;
        req_vol_ts(t, z) = req_l;
    end

    % Step B: Supervisory Water Allocation FIS (FIS 5)
    fuzzy_req_vol = zeros(1, num_zones);
    for z = 1:num_zones
        alloc_ratio = evalfis(fis_alloc, [avail_water_pct, water_demand_ts(t, z), soil_stress_ts(t, z), zones(z).priority]);
        fuzzy_req_vol(z) = raw_req_vol(z) * (alloc_ratio / 100.0);
    end

    % Step C: Priority-Weighted Bounded Arbitrator
    [granted_vol, unmet_l, is_constrained] = models.bounded_water_allocation(...
        fuzzy_req_vol, priorities_pct, avail_supply_vol);

    alloc_vol_ts(t, :) = granted_vol;
    unmet_vol_ts(t, :) = unmet_l;

    % Step D: Physical soil dynamics update (Closed-Loop Feedback S(t+1))
    for z = 1:num_zones
        applied_depth_mm = granted_vol(z) / zones(z).area_m2;
        irrig_depth_ts(t, z) = applied_depth_mm;

        % Step ETc depth (mm)
        step_etc_mm = (etc_daily_ts(t, z) / 24.0) * (dt_minutes / 60.0);

        [next_sm, next_storage, fluxes, res] = models.update_soil_water_balance(...
            sm_ts(t, z), applied_depth_mm, peff_depth_ts(t, z), step_etc_mm, ...
            zones(z).field_capacity, zones(z).wilting_point, zones(z).saturation, ...
            zones(z).root_depth_m, zones(z).drainage_coefficient, ...
            zones(z).infiltration_rate_mm_h, dt_minutes);

        drainage_depth_ts(t, z) = fluxes.drainage_mm;
        actual_et_depth_ts(t, z) = fluxes.actual_et_mm;
        residuals_ts(t, z) = res;

        % Feedback state update to next step t+1 (Closed Loop)
        if t < total_steps
            sm_ts(t + 1, z) = next_sm;
        end
    end
end

% 5. Assemble Structured Results
results.scenario = scenario_name;
results.duration_hours = duration_hours;
results.time_min = time_min;
results.time_hr = time_hr;
results.weather = timeline;
results.et0_daily = et0_daily;
results.weather_stress = weather_stress_ts;

results.soil_moisture = sm_ts;
results.rsm = rsm_ts;
results.error = error_ts;
results.soil_stress = soil_stress_ts;
results.etc_daily = etc_daily_ts;
results.water_demand = water_demand_ts;
results.command = cmd_ts;

results.requested_vol_l = req_vol_ts;
results.allocated_vol_l = alloc_vol_ts;
results.unmet_vol_l = unmet_vol_ts;
results.irrigation_depth_mm = irrig_depth_ts;
results.drainage_depth_mm = drainage_depth_ts;
results.actual_et_depth_mm = actual_et_depth_ts;
results.residuals_mm = residuals_ts;

% Summary Metrics Per Zone
for z = 1:num_zones
    m.zone_id = z;
    m.crop = zones(z).crop_name;
    m.soil = zones(z).soil_name;
    m.target_sm = zones(z).target_moisture;
    m.final_sm = sm_ts(end, z);
    m.mae = mean(abs(error_ts(:, z)));
    m.rmse = sqrt(mean(error_ts(:, z).^2));
    m.total_req_l = sum(req_vol_ts(:, z));
    m.total_alloc_l = sum(alloc_vol_ts(:, z));
    m.total_unmet_l = sum(unmet_vol_ts(:, z));
    if m.total_req_l > 0
        m.fulfillment_ratio = m.total_alloc_l / m.total_req_l;
    else
        m.fulfillment_ratio = 1.0;
    end
    m.max_balance_residual = max(residuals_ts(:, z));
    results.zone_metrics(z) = m;
end

results.total_system_allocated_l = sum(alloc_vol_ts(:));
results.total_system_unmet_l = sum(unmet_vol_ts(:));
end
