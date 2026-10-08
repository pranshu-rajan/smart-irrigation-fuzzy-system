function results = evaluate_fuzzy_architecture(sm_curr, target_sm, T, RH, Rs, u2, P, reservoir_pct)
% EVALUATE_FUZZY_ARCHITECTURE Direct End-to-End Evaluation of Fuzzy Architecture
%
% Designed specifically for Professor Viva / Lab Demonstration:
% Allows arbitrary sensor inputs to be fed into the end-to-end fuzzy
% pipeline, instantaneously evaluating all 5 FIS stages and rendering
% an interactive diagnostic dashboard in < 0.1 seconds.
%
% Usage:
%   evaluate_fuzzy_architecture(); % Runs standard baseline demo
%   evaluate_fuzzy_architecture(18, 28, 40, 15, 950, 4.5, 0, 30); % Custom heatwave
%   results = evaluate_fuzzy_architecture(sm, target, T, RH, Rs, u2, P, res);
%
% Inputs:
%   sm_curr:       Current Soil Moisture Content [0 - 100] % (Default: 45.0)
%   target_sm:     Target Soil Moisture Setpoint [0 - 100] % (Default: 60.0)
%   T:             Air Temperature [°C] (Default: 32.0)
%   RH:            Relative Humidity [0 - 100] % (Default: 38.0)
%   Rs:            Solar Radiation [0 - 1500] W/m² (Default: 820.0)
%   u2:            Wind Speed [0 - 50] m/s (Default: 3.2)
%   P:             Rainfall Depth [0 - 50] mm (Default: 0.0)
%   reservoir_pct: Shared Reservoir Water Storage [0 - 100] % (Default: 50.0)

% Default values if omitted
if nargin < 1 || isempty(sm_curr),       sm_curr = 45.0;       end
if nargin < 2 || isempty(target_sm),     target_sm = 60.0;     end
if nargin < 3 || isempty(T),             T = 32.0;             end
if nargin < 4 || isempty(RH),            RH = 38.0;            end
if nargin < 5 || isempty(Rs),            Rs = 820.0;           end
if nargin < 6 || isempty(u2),            u2 = 3.2;             end
if nargin < 7 || isempty(P),             P = 0.0;              end
if nargin < 8 || isempty(reservoir_pct), reservoir_pct = 50.0; end

% Clamp inputs to physical valid domains
sm_curr = max(0.0, min(100.0, sm_curr));
target_sm = max(0.0, min(100.0, target_sm));
T = max(-10.0, min(60.0, T));
RH = max(0.0, min(100.0, RH));
Rs = max(0.0, min(1500.0, Rs));
u2 = max(0.1, min(50.0, u2));
P = max(0.0, min(50.0, P));
reservoir_pct = max(0.0, min(100.0, reservoir_pct));

% Ensure current directory is on MATLAB path
this_dir = fileparts(mfilename('fullpath'));
if ~isempty(this_dir)
    addpath(this_dir);
end

% Load FIS models and testbed configurations
fis_soil = fuzzy_builder.build_soil_stress_fis();
fis_weather = fuzzy_builder.build_weather_stress_fis();
fis_demand = fuzzy_builder.build_water_demand_fis();
fis_main = fuzzy_builder.build_main_irrigation_fis();
fis_alloc = fuzzy_builder.build_water_allocation_fis();

zones = config.load_default_zones();
alloc_cfg = config.load_allocation_defaults();
num_zones = numel(zones);

% -------------------------------------------------------------------------
% STAGE 1: SOIL STRESS INFERENCE (FIS 1)
% -------------------------------------------------------------------------
fc_ref = 70.0; % Loam reference Field Capacity
wp_ref = 25.0; % Loam reference Wilting Point
[rsm, moisture_err] = models.calculate_soil_indices(sm_curr, target_sm, fc_ref, wp_ref);
soil_stress = evalfis(fis_soil, [rsm, moisture_err]);

% -------------------------------------------------------------------------
% STAGE 2: ATMOSPHERIC WEATHER STRESS INFERENCE (FIS 2)
% -------------------------------------------------------------------------
weather_stress = evalfis(fis_weather, [T, RH, Rs, u2, P]);
et0_val = models.calculate_fao56_et0(T, RH, Rs, u2);

% -------------------------------------------------------------------------
% STAGE 3: CROP WATER DEMAND INFERENCE (FIS 3)
% -------------------------------------------------------------------------
peff = models.calculate_effective_rain(P, fc_ref, wp_ref);
[etc_val, deficit_val] = models.calculate_crop_etc(et0_val, zones(1).kc, peff);
water_demand = evalfis(fis_demand, [etc_val, deficit_val, peff]);

% -------------------------------------------------------------------------
% STAGE 4: MAIN SUPERVISORY IRRIGATION DECISION (FIS 4)
% -------------------------------------------------------------------------
main_cmd = evalfis(fis_main, [soil_stress, weather_stress, water_demand, moisture_err]);

% -------------------------------------------------------------------------
% STAGE 5: MULTI-ZONE ARBITRATION & RESERVOIR ALLOCATION (FIS 5)
% -------------------------------------------------------------------------
% Compute per-zone demands based on each crop's specific parameters
raw_requests_l = zeros(1, num_zones);
zone_stresses = zeros(1, num_zones);
zone_demands = zeros(1, num_zones);
zone_cmds = zeros(1, num_zones);

for z = 1:num_zones
    [z_rsm, z_err] = models.calculate_soil_indices(sm_curr, zones(z).target_moisture, ...
                                                   zones(z).field_capacity, zones(z).wilting_point);
    z_s_stress = evalfis(fis_soil, [z_rsm, z_err]);
    zone_stresses(z) = z_s_stress;

    [z_etc, z_def] = models.calculate_crop_etc(et0_val, zones(z).kc, peff);
    z_demand = evalfis(fis_demand, [z_etc, z_def, peff]);
    zone_demands(z) = z_demand;

    z_cmd = evalfis(fis_main, [z_s_stress, weather_stress, z_demand, z_err]);
    zone_cmds(z) = z_cmd;

    % Hourly water request in Liters: (cmd/100) * (max_rate * Area)
    req_l = (z_cmd / 100.0) * (alloc_cfg.nominal_max_rate_mm_h * zones(z).area_m2);
    raw_requests_l(z) = req_l;
end

% Stage 5 Fuzzy Allocation Evaluation (FIS 5)
alloc_factors = zeros(1, num_zones);
fuzzy_requests_l = zeros(1, num_zones);
for z = 1:num_zones
    alloc_ratio = evalfis(fis_alloc, [reservoir_pct, zone_demands(z), zone_stresses(z), zones(z).priority]);
    alloc_factors(z) = alloc_ratio;
    fuzzy_requests_l(z) = raw_requests_l(z) * (alloc_ratio / 100.0);
end

% Total available flow capacity scaled by reservoir storage percentage
total_avail_l = alloc_cfg.nominal_flow_rate_l_min * 60.0 * (reservoir_pct / 100.0);
priorities_pct = [zones.priority];

[granted_l, unmet_l, is_constrained] = models.bounded_water_allocation(...
    fuzzy_requests_l, priorities_pct, total_avail_l);

% -------------------------------------------------------------------------
% CONSOLE REPORT FOR PROFESSOR VIVA
% -------------------------------------------------------------------------
fprintf('\n========================================================================================\n');
fprintf('                 SMART MULTIZONE FUZZY IRRIGATION ARCHITECTURE                          \n');
fprintf('                             LIVE INFERENCE REPORT                                      \n');
fprintf('========================================================================================\n');
fprintf(' SENSOR INPUTS (CURRENT CONDITIONS):\n');
fprintf('   Soil Moisture Content : %6.1f %%  (Target Setpoint: %.1f %%, Deficit Error: %+5.1f %%)\n', ...
    sm_curr, target_sm, moisture_err);
fprintf('   Air Temperature       : %6.1f °C  |  Relative Humidity: %5.1f %%\n', T, RH);
fprintf('   Solar Radiation       : %6.1f W/m²|  Wind Speed       : %5.1f m/s\n', Rs, u2);
fprintf('   Precipitation / Rain  : %6.1f mm  |  Reservoir Storage: %5.1f %%\n', P, reservoir_pct);
fprintf('----------------------------------------------------------------------------------------\n');
fprintf(' HIERARCHICAL FUZZY INFERENCE PIPELINE EVALUATION:\n');
fprintf('   [Stage 1] Soil Stress FIS      : %5.1f %%  [%s]\n', ...
    soil_stress, get_linguistic_level(soil_stress));
fprintf('   [Stage 2] Weather Stress FIS   : %5.1f %%  [%s]\n', ...
    weather_stress, get_linguistic_level(weather_stress));
fprintf('   [Stage 3] Water Demand FIS     : %5.1f %%  [%s] (Crop ETc: %.2f mm/day)\n', ...
    water_demand, get_linguistic_level(water_demand), etc_val);
fprintf('   [Stage 4] Main Supervisory FIS : %5.1f %%  [%s Valve Command]\n', ...
    main_cmd, get_linguistic_level(main_cmd));
fprintf('----------------------------------------------------------------------------------------\n');
fprintf(' STAGE 5: MULTI-ZONE ARBITRATION & RESOURCE ALLOCATION (Reservoir Level: %.1f%%):\n', reservoir_pct);
fprintf('   Zone Name              | Priority | FIS 5 Alloc | Req Water (L) | Granted (L) | Fulfillment | Status\n');
fprintf('   ---------------------- | -------- | ----------- | ------------- | ----------- | ----------- | ------\n');
for z = 1:num_zones
    if raw_requests_l(z) > 0
        ratio = (granted_l(z) / raw_requests_l(z)) * 100.0;
    else
        ratio = 100.0;
    end
    if ratio >= 99.0
        status_str = 'FULL (Optimal)';
    elseif ratio >= 60.0
        status_str = 'PARTIAL (Rationed)';
    else
        status_str = 'DEFICIT (Protected)';
    end
    fprintf('   %-22s |   %3.0f%%   |   %5.1f%%   |   %7.1f L   |   %7.1f L |   %5.1f%%   | %s\n', ...
        zones(z).name, zones(z).priority, alloc_factors(z), raw_requests_l(z), granted_l(z), ratio, status_str);
end
fprintf('   -------------------------------------------------------------------------------------\n');
fprintf('   TOTAL SYSTEM WATER     : Requested: %7.1f L  |  Allocated: %7.1f L (Avail: %.1f L)\n', ...
    sum(raw_requests_l), sum(granted_l), total_avail_l);
fprintf('========================================================================================\n\n');

% Pack results struct
results.inputs.sm = sm_curr;
results.inputs.target_sm = target_sm;
results.inputs.T = T;
results.inputs.RH = RH;
results.inputs.Rs = Rs;
results.inputs.u2 = u2;
results.inputs.P = P;
results.inputs.reservoir_pct = reservoir_pct;

results.soil_stress = soil_stress;
results.weather_stress = weather_stress;
results.water_demand = water_demand;
results.main_command = main_cmd;
results.raw_requests_l = raw_requests_l;
results.granted_l = granted_l;
results.unmet_l = unmet_l;
results.is_constrained = is_constrained;

% Render interactive visual dashboard
fig = render_interactive_dashboard(results, zones);
results.figure = fig;
end

% -------------------------------------------------------------------------
% HELPER: Linguistic Level Categorizer
% -------------------------------------------------------------------------
function str = get_linguistic_level(val)
if val < 20.0
    str = 'VERY LOW';
elseif val < 40.0
    str = 'LOW';
elseif val < 60.0
    str = 'MODERATE';
elseif val < 80.0
    str = 'HIGH';
else
    str = 'CRITICAL / VERY HIGH';
end
end

% -------------------------------------------------------------------------
% HELPER: Render 4-Panel Interactive Viva Dashboard
% -------------------------------------------------------------------------
function fig = render_interactive_dashboard(res, zones)
fig = figure('Name', 'Fuzzy Irrigation Architecture - Live Viva Dashboard', ...
             'Position', [60 60 1300 800], 'Color', 'w');

% Subplot 1: Hierarchical Inference Pipeline Bar Chart
subplot(2, 2, 1);
stages = {'Stage 1:\nSoil Stress', 'Stage 2:\nWeather Stress', 'Stage 3:\nWater Demand', 'Stage 4:\nMain Command'};
vals = [res.soil_stress, res.weather_stress, res.water_demand, res.main_command];
b1 = bar(categorical(stages), vals, 0.5);
b1.FaceColor = 'flat';
b1.CData(1, :) = [0.85 0.35 0.25]; % Red-Orange
b1.CData(2, :) = [0.95 0.65 0.15]; % Amber
b1.CData(3, :) = [0.25 0.70 0.85]; % Cyan
b1.CData(4, :) = [0.15 0.55 0.90]; % Deep Blue
ylabel('Fuzzy Output Rating (0 - 100%)');
title('Hierarchical Fuzzy Inference Chain Outputs', 'FontSize', 12, 'FontWeight', 'bold');
grid on; ylim([0 115]);
for i = 1:4
    text(i, vals(i) + 4, sprintf('%.1f%%', vals(i)), 'HorizontalAlignment', 'center', 'FontWeight', 'bold');
end

% Subplot 2: Multi-Zone Water Allocation (Requested vs Granted)
subplot(2, 2, 2);
zone_names = {zones.crop_name};
bar_data = [res.raw_requests_l(:), res.granted_l(:)];
b2 = bar(categorical(zone_names), bar_data, 0.65);
b2(1).FaceColor = [0.7 0.7 0.7]; % Gray (Requested)
b2(2).FaceColor = [0.2 0.7 0.3]; % Green (Allocated)
ylabel('Water Volume (Liters / Hour)');
title(sprintf('Multi-Zone Arbitration under Reservoir (%.0f%% Capacity)', res.inputs.reservoir_pct), ...
      'FontSize', 12, 'FontWeight', 'bold');
legend({'Requested Water (Unconstrained)', 'Granted Water (Arbitrated)'}, 'Location', 'northeast');
grid on;

% Subplot 3: Environmental & Physical Sensor Readout
subplot(2, 2, 3);
sensor_names = {'Soil Moisture', 'Target Setpoint', 'Temperature', 'Humidity', 'Solar Radiation/15', 'Reservoir'};
sensor_vals = [res.inputs.sm, res.inputs.target_sm, res.inputs.T, res.inputs.RH, res.inputs.Rs/15.0, res.inputs.reservoir_pct];
b3 = barh(categorical(sensor_names), sensor_vals, 0.6);
b3.FaceColor = [0.3 0.6 0.8];
xlabel('Sensor Parameter Scale (%)');
title('Operating Sensor Environmental Telemetry', 'FontSize', 12, 'FontWeight', 'bold');
grid on; xlim([0 110]);
for i = 1:numel(sensor_vals)
    text(sensor_vals(i) + 2, i, sprintf('%.1f', sensor_vals(i)), 'VerticalAlignment', 'middle', 'FontWeight', 'bold');
end

% Subplot 4: Academic Interpretation & Agronomic Decision Card
subplot(2, 2, 4);
axis off;
card_text = {
    sprintf('\\bf SMART FUZZY CONTROLLER DECISION CARD\\rm')
    '-------------------------------------------------------------'
    sprintf('\\bfActuator Action:\\rm Valve Opening = \\bf%.1f%%\\rm', res.main_command)
    sprintf('\\bfPrimary Trigger:\\rm %s (Stress: %.1f%%)', get_linguistic_level(max(res.soil_stress, res.weather_stress)), max(res.soil_stress, res.weather_stress))
    ''
    sprintf('\\bfPhysical Interpretation:\\rm')
    sprintf('  - Soil Deficit Error: %+5.1f%% (Current: %.1f%%, Target: %.1f%%)', res.inputs.sm - res.inputs.target_sm, res.inputs.sm, res.inputs.target_sm)
    sprintf('  - Evaporative Demand: ET0 = %.2f mm/day, Weather Stress = %.1f%%', models.calculate_fao56_et0(res.inputs.T, res.inputs.RH, res.inputs.Rs, res.inputs.u2), res.weather_stress)
    ''
    sprintf('\\bfArbitration Policy:\\rm')
    sprintf('  - Shared Reservoir Level: %.1f%% (State: %s)', res.inputs.reservoir_pct, ternary(res.inputs.reservoir_pct < 40, 'SCARCITY MODE', 'NORMAL MODE'))
    sprintf('  - Zone 1 (Tomato): %.1f L granted (High Priority cash crop)', res.granted_l(1))
    sprintf('  - Zone 2 (Wheat) : %.1f L granted (Hardy cereal crop)', res.granted_l(2))
    sprintf('  - Zone 3 (Maize) : %.1f L granted (Critical staple grain)', res.granted_l(3))
};
text(0.05, 0.5, card_text, 'FontSize', 10, 'Interpreter', 'tex', ...
     'BackgroundColor', [0.96 0.98 1.0], 'EdgeColor', [0.7 0.8 0.9], 'Margin', 12);
end

function out = ternary(cond, true_val, false_val)
if cond
    out = true_val;
else
    out = false_val;
end
end
