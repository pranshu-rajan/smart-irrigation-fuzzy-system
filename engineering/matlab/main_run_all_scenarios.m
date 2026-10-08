% MAIN_RUN_ALL_SCENARIOS Master Demonstration Script for MATLAB/Simulink
%
% Executes the complete closed-loop fuzzy multizone irrigation system across
% all 6 agricultural scenarios:
%   1. Normal
%   2. Hot & Dry
%   3. Rainy
%   4. Cloudy
%   5. Heatwave
%   6. Water Scarcity
%
% Fast, robust, and optimized for standard MATLAB & MATLAB Online execution (< 3 seconds total).

clear; clc; close all;

this_dir = fileparts(mfilename('fullpath'));
if ~isempty(this_dir)
    addpath(this_dir);
end

fprintf('=================================================================\n');
fprintf(' SMART MULTIZONE IRRIGATION & WATER MANAGEMENT (FUZZY CONTROL)   \n');
fprintf('       End-to-End MATLAB Closed-Loop Control Architecture        \n');
fprintf('=================================================================\n\n');

% 1. Step 1: Build / Verify all 5 FIS Models
fprintf('Step 1: Exporting & Verifying Fuzzy Inference Systems...\n');
systems = fuzzy_builder.build_all_systems();

% 2. Step 2: Execute Unit & Regression Test Suite
fprintf('\nStep 2: Running Engineering Unit Tests...\n');
tests.run_all_matlab_tests();

% 3. Step 3: Run All 6 Simulation Scenarios (Hourly Control Cycle: 24 steps in ~1 sec)
scenarios = {'Normal', 'Hot & Dry', 'Rainy', 'Cloudy', 'Heatwave', 'Water Scarcity'};
num_scenarios = numel(scenarios);
all_results = cell(num_scenarios, 1);

fprintf('\nStep 3: Simulating 24-Hour Closed-Loop Multizone Dynamics across 6 Scenarios...\n');
fprintf('----------------------------------------------------------------------------------------------------\n');
fprintf('%-15s | %-12s | %-12s | %-10s | %-10s | %-10s | %-12s\n', ...
    'Scenario', 'Req Water(L)', 'Alloc Water', 'Unmet (L)', 'Fulfill(%)', 'Mean RMSE', 'Max Residual');
fprintf('----------------------------------------------------------------------------------------------------\n');

for i = 1:num_scenarios
    sc_name = scenarios{i};
    % Hourly decision interval (dt_minutes = 60) for clean, fast simulation
    res = simulation.run_multizone_sim(sc_name, 24, 60);
    all_results{i} = res;

    total_req = sum(res.requested_vol_l(:));
    total_alloc = sum(res.allocated_vol_l(:));
    total_unmet = sum(res.unmet_vol_l(:));
    if total_req > 0
        fulfillment = (total_alloc / total_req) * 100.0;
    else
        fulfillment = 100.0;
    end
    mean_rmse = mean([res.zone_metrics.rmse]);
    max_res = max([res.zone_metrics.max_balance_residual]);

    fprintf('%-15s | %12.1f | %12.1f | %10.1f | %9.1f%% | %10.3f | %12.2e\n', ...
        sc_name, total_req, total_alloc, total_unmet, fulfillment, mean_rmse, max_res);
end
fprintf('----------------------------------------------------------------------------------------------------\n');

% 4. Step 4: Generate Diagnostic Technical Visualizations
fprintf('\nStep 4: Rendering Technical Diagnostic Visualizations...\n');
visualization.plot_fuzzy_surfaces();
visualization.plot_simulation_telemetry(all_results{1}); % Normal scenario
if numel(all_results) >= 6
    visualization.plot_simulation_telemetry(all_results{6}); % Water Scarcity scenario
end

% 5. Step 5: Run Benchmark Comparison (Fuzzy vs PID vs On-Off)
fprintf('\nStep 5: Executing Controller Benchmark Comparison (Fuzzy vs PID vs On-Off)...\n');
bench = simulation.run_benchmark_comparison('Normal', 24, 60);

fprintf('\n=================================================================\n');
fprintf(' Demonstration completed successfully! All figures rendered.\n');
fprintf(' NOTE FOR VIVA WITH PROFESSOR:\n');
fprintf('  * To test ANY custom inputs live in front of your professor, run:\n');
fprintf('       demo_fuzzy_interactive\n');
fprintf('    or directly call:\n');
fprintf('       evaluate_fuzzy_architecture(sm, target, temp, rh, solar, wind, rain, res);\n');
fprintf('=================================================================\n');
