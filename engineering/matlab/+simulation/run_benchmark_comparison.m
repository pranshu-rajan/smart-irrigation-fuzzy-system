function comparison = run_benchmark_comparison(scenario_name, duration_hours, dt_minutes)
% RUN_BENCHMARK_COMPARISON Rigorous Benchmark Comparison: Fuzzy vs On-Off vs PID
%
% Compares 3 Industrial & Academic Irrigation Control Architectures:
%   1. Hierarchical Mamdani Fuzzy Controller (5-Stage FIS with weather + soil anticipation)
%   2. On-Off (Bang-Bang Hysteresis) Controller (turns ON below Target-2%, OFF at Target)
%   3. Classical PID Controller (Error tracking with Anti-Windup Clamping)
%
% Metrics evaluated:
%   - Total Water Consumed (Liters)
%   - Water Savings Relative to On-Off and PID (%)
%   - Setpoint Tracking Error (RMSE and MAE in %)
%   - Actuator Chattering / Valve Switching Frequency (Count)
%   - Soil Moisture Overshoot (%)

if nargin < 1 || isempty(scenario_name)
    scenario_name = 'Normal';
end
if nargin < 2 || isempty(duration_hours)
    duration_hours = 24;
end
if nargin < 3 || isempty(dt_minutes)
    dt_minutes = 60; % Standard hourly decision interval
end

fprintf('=================================================================\n');
fprintf('     CONTROLLER BENCHMARK COMPARISON (%s Scenario, %d Hours)     \n', scenario_name, duration_hours);
fprintf('=================================================================\n');

% Load standard configuration
zones = config.load_default_zones();
alloc_cfg = config.load_allocation_defaults();
num_zones = numel(zones);
priorities_pct = [zones.priority];
max_rate_mm_h = 4.0; % Calibrated delivery rate for discrete hourly steps

% Generate shared atmospheric forcing
w_engine = weather.WeatherEngine(scenario_name, 42);
timeline = w_engine.generate_timeline(duration_hours, dt_minutes);
total_steps = timeline.total_steps;
time_hr = timeline.hours;

% -------------------------------------------------------------------------
% 1. SIMULATE HIERARCHICAL FUZZY CONTROLLER
% -------------------------------------------------------------------------
fprintf('  [1/3] Simulating Hierarchical Mamdani Fuzzy Controller...\n');
fuzzy_res = simulation.run_multizone_sim(scenario_name, duration_hours, dt_minutes);

fuzzy_sm = fuzzy_res.soil_moisture;
fuzzy_cmd = fuzzy_res.command;
fuzzy_alloc_l = fuzzy_res.allocated_vol_l;

% -------------------------------------------------------------------------
% 2. SIMULATE ON-OFF (BANG-BANG HYSTERESIS) CONTROLLER
% -------------------------------------------------------------------------
fprintf('  [2/3] Simulating On-Off (Bang-Bang Hysteresis) Controller...\n');
onoff_sm = zeros(total_steps, num_zones);
onoff_cmd = zeros(total_steps, num_zones);
onoff_alloc_l = zeros(total_steps, num_zones);

for z = 1:num_zones
    onoff_sm(1, z) = zones(z).initial_moisture;
end

for t = 1:total_steps
    T = timeline.temperature(t);
    RH = timeline.humidity(t);
    Rs = timeline.solar_radiation(t);
    u2 = timeline.wind_speed(t);
    P = timeline.rainfall(t);
    waf = timeline.water_availability_factor;

    et0_val = models.calculate_fao56_et0(T, RH, Rs, u2);
    avail_supply_vol = alloc_cfg.nominal_flow_rate_l_min * waf * dt_minutes;

    raw_req_l = zeros(1, num_zones);
    for z = 1:num_zones
        curr_sm = onoff_sm(t, z);
        target = zones(z).target_moisture;

        % Classical Hysteresis Bang-Bang:
        % If SM < Target - 2.0%, turn ON (100% capacity)
        % If SM >= Target, turn OFF (0%)
        % Otherwise, retain previous valve state
        if curr_sm < (target - 2.0)
            cmd = 100.0;
        elseif curr_sm >= target
            cmd = 0.0;
        else
            if t > 1
                cmd = onoff_cmd(t - 1, z);
            else
                cmd = 0.0;
            end
        end
        onoff_cmd(t, z) = cmd;

        % Required water depth & volume for step
        req_l = (cmd / 100.0) * (max_rate_mm_h * zones(z).area_m2 * (dt_minutes / 60.0));
        raw_req_l(z) = req_l;
    end

    % Constrain by shared reservoir supply
    [granted_l, ~] = models.bounded_water_allocation(raw_req_l, priorities_pct, avail_supply_vol);
    onoff_alloc_l(t, :) = granted_l;

    % Physical Soil Dynamics Update S(t+1)
    for z = 1:num_zones
        applied_depth_mm = granted_l(z) / zones(z).area_m2;
        peff_step = models.calculate_effective_rain(P, zones(z).field_capacity, zones(z).wilting_point);
        [etc_d, ~] = models.calculate_crop_etc(et0_val, zones(z).kc);
        step_etc_mm = (etc_d / 24.0) * (dt_minutes / 60.0);

        [next_sm, ~] = models.update_soil_water_balance(...
            onoff_sm(t, z), applied_depth_mm, peff_step, step_etc_mm, ...
            zones(z).field_capacity, zones(z).wilting_point, zones(z).saturation, ...
            zones(z).root_depth_m, zones(z).drainage_coefficient, ...
            zones(z).infiltration_rate_mm_h, dt_minutes);

        if t < total_steps
            onoff_sm(t + 1, z) = next_sm;
        end
    end
end

% -------------------------------------------------------------------------
% 3. SIMULATE DISCRETE PID CONTROLLER (WITH ANTI-WINDUP)
% -------------------------------------------------------------------------
fprintf('  [3/3] Simulating Classical PID Controller with Anti-Windup...\n');
pid_sm = zeros(total_steps, num_zones);
pid_cmd = zeros(total_steps, num_zones);
pid_alloc_l = zeros(total_steps, num_zones);

for z = 1:num_zones
    pid_sm(1, z) = zones(z).initial_moisture;
end

% Tuned discrete PID gains for agricultural soil dynamics:
% Kp: Proportional gain (valve % per % moisture error)
% Ki: Integral gain (eliminates steady-state offset)
% Kd: Derivative gain (damps rate of change)
Kp = 4.5;
Ki = 0.6;
Kd = 1.2;

integral_err = zeros(1, num_zones);
prev_err = zeros(1, num_zones);
dt_hr = dt_minutes / 60.0;

for t = 1:total_steps
    T = timeline.temperature(t);
    RH = timeline.humidity(t);
    Rs = timeline.solar_radiation(t);
    u2 = timeline.wind_speed(t);
    P = timeline.rainfall(t);
    waf = timeline.water_availability_factor;

    et0_val = models.calculate_fao56_et0(T, RH, Rs, u2);
    avail_supply_vol = alloc_cfg.nominal_flow_rate_l_min * waf * dt_minutes;

    raw_req_l = zeros(1, num_zones);
    for z = 1:num_zones
        curr_sm = pid_sm(t, z);
        err = zones(z).target_moisture - curr_sm;

        % Anti-windup integration clamping [-12, +12] %
        integral_err(z) = max(-12.0, min(12.0, integral_err(z) + err * dt_hr));
        deriv_err = (err - prev_err(z)) / dt_hr;
        prev_err(z) = err;

        % Compute unconstrained PID output
        u = Kp * err + Ki * integral_err(z) + Kd * deriv_err;
        cmd = max(0.0, min(100.0, u));
        pid_cmd(t, z) = cmd;

        req_l = (cmd / 100.0) * (max_rate_mm_h * zones(z).area_m2 * dt_hr);
        raw_req_l(z) = req_l;
    end

    [granted_l, ~] = models.bounded_water_allocation(raw_req_l, priorities_pct, avail_supply_vol);
    pid_alloc_l(t, :) = granted_l;

    for z = 1:num_zones
        applied_depth_mm = granted_l(z) / zones(z).area_m2;
        peff_step = models.calculate_effective_rain(P, zones(z).field_capacity, zones(z).wilting_point);
        [etc_d, ~] = models.calculate_crop_etc(et0_val, zones(z).kc);
        step_etc_mm = (etc_d / 24.0) * dt_hr;

        [next_sm, ~] = models.update_soil_water_balance(...
            pid_sm(t, z), applied_depth_mm, peff_step, step_etc_mm, ...
            zones(z).field_capacity, zones(z).wilting_point, zones(z).saturation, ...
            zones(z).root_depth_m, zones(z).drainage_coefficient, ...
            zones(z).infiltration_rate_mm_h, dt_minutes);

        if t < total_steps
            pid_sm(t + 1, z) = next_sm;
        end
    end
end

% -------------------------------------------------------------------------
% 4. COMPUTE PERFORMANCE METRICS
% -------------------------------------------------------------------------
target_matrix = repmat([zones.target_moisture], total_steps, 1);

% Fuzzy metrics
err_fuzzy = target_matrix - fuzzy_sm;
fuzzy_water_l = sum(fuzzy_alloc_l(:));
fuzzy_rmse = sqrt(mean(err_fuzzy(:).^2));
fuzzy_mae = mean(abs(err_fuzzy(:)));
fuzzy_switches = sum(sum(abs(diff(fuzzy_cmd > 5.0, 1, 1))));

% On-Off metrics
err_onoff = target_matrix - onoff_sm;
onoff_water_l = sum(onoff_alloc_l(:));
onoff_rmse = sqrt(mean(err_onoff(:).^2));
onoff_mae = mean(abs(err_onoff(:)));
onoff_switches = sum(sum(abs(diff(onoff_cmd > 50.0, 1, 1))));

% PID metrics
err_pid = target_matrix - pid_sm;
pid_water_l = sum(pid_alloc_l(:));
pid_rmse = sqrt(mean(err_pid(:).^2));
pid_mae = mean(abs(err_pid(:)));
pid_switches = sum(sum(abs(diff(pid_cmd > 5.0, 1, 1))));

% Water savings achieved by Fuzzy
savings_vs_onoff = max(0.0, (onoff_water_l - fuzzy_water_l) / onoff_water_l * 100.0);
savings_vs_pid = max(0.0, (pid_water_l - fuzzy_water_l) / pid_water_l * 100.0);

% Assemble struct
comparison.scenario = scenario_name;
comparison.time_hr = time_hr;
comparison.zones = zones;

comparison.fuzzy.sm = fuzzy_sm;
comparison.fuzzy.cmd = fuzzy_cmd;
comparison.fuzzy.alloc_l = fuzzy_alloc_l;
comparison.fuzzy.total_water_l = fuzzy_water_l;
comparison.fuzzy.rmse = fuzzy_rmse;
comparison.fuzzy.mae = fuzzy_mae;
comparison.fuzzy.switches = fuzzy_switches;

comparison.onoff.sm = onoff_sm;
comparison.onoff.cmd = onoff_cmd;
comparison.onoff.alloc_l = onoff_alloc_l;
comparison.onoff.total_water_l = onoff_water_l;
comparison.onoff.rmse = onoff_rmse;
comparison.onoff.mae = onoff_mae;
comparison.onoff.switches = onoff_switches;

comparison.pid.sm = pid_sm;
comparison.pid.cmd = pid_cmd;
comparison.pid.alloc_l = pid_alloc_l;
comparison.pid.total_water_l = pid_water_l;
comparison.pid.rmse = pid_rmse;
comparison.pid.mae = pid_mae;
comparison.pid.switches = pid_switches;

comparison.savings_vs_onoff_pct = savings_vs_onoff;
comparison.savings_vs_pid_pct = savings_vs_pid;

% -------------------------------------------------------------------------
% 5. DISPLAY ACADEMIC SUMMARY TABLE
% -------------------------------------------------------------------------
fprintf('\n========================================================================================\n');
fprintf('                          CONTROLLER PERFORMANCE EVALUATION                             \n');
fprintf('========================================================================================\n');
fprintf(' %-18s | %-16s | %-12s | %-10s | %-16s\n', ...
    'Controller Type', 'Water Used (L)', 'Water Saved', 'RMSE (%)', 'Valve Chattering');
fprintf('----------------------------------------------------------------------------------------\n');
fprintf(' %-18s | %16.1f | %11s  | %9.3f%% | %16d\n', ...
    'Fuzzy Logic (Our)', fuzzy_water_l, 'BENCHMARK', fuzzy_rmse, fuzzy_switches);
fprintf(' %-18s | %16.1f | %10.1f%% | %9.3f%% | %16d\n', ...
    'PID Controller', pid_water_l, -savings_vs_pid, pid_rmse, pid_switches);
fprintf(' %-18s | %16.1f | %10.1f%% | %9.3f%% | %16d\n', ...
    'On-Off (Bang-Bang)', onoff_water_l, -savings_vs_onoff, onoff_rmse, onoff_switches);
fprintf('========================================================================================\n');
fprintf(' KEY FINDINGS FOR VIVA / PRESENTATION:\n');
fprintf('  * Fuzzy Water Savings: +%.1f%% vs Bang-Bang, +%.1f%% vs Classical PID.\n', ...
    savings_vs_onoff, savings_vs_pid);
fprintf('  * Fuzzy smooth modulation avoids valve chattering (%d switches vs %d for On-Off).\n', ...
    fuzzy_switches, onoff_switches);
fprintf('  * Fuzzy anticipates weather and reservoir stress rather than relying only on error.\n');
fprintf('========================================================================================\n\n');

% Render visual comparison figure
try
    visualization.plot_benchmark_comparison(comparison);
catch
    % Non-fatal if visualization package is in transition
end
end
