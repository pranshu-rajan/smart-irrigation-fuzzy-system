% DEMO_FUZZY_INTERACTIVE Interactive Viva & Professor Testing Script
%
% Designed for B.Tech Viva / Project Defense:
% Allows the student or professor to choose preset agricultural scenarios
% or input ANY custom values live, demonstrating the complete 5-stage
% hierarchical fuzzy system in under 0.1 seconds!
%
% Simply type:
%   demo_fuzzy_interactive

this_dir = fileparts(mfilename('fullpath'));
if ~isempty(this_dir)
    addpath(this_dir);
end

clc;
fprintf('========================================================================================\n');
fprintf('        SMART MULTIZONE IRRIGATION FUZZY LOGIC CONTROL SYSTEM (MATLAB VIVA DEMO)        \n');
fprintf('========================================================================================\n\n');
fprintf(' Choose an evaluation mode:\n');
fprintf('   [1] Normal Spring Day (Mild weather, 55%% SM, 25°C, Reservoir 85%%)\n');
fprintf('   [2] Severe Heatwave & Drought (Extreme evaporation, 22%% SM, 42°C, Reservoir 60%%)\n');
fprintf('   [3] Torrential Rainstorm Event (Monsoon rain 30 mm, 50%% SM, 22°C, Reservoir 95%%)\n');
fprintf('   [4] Critical Water Scarcity / Low Reservoir (30%% SM, 36°C, Reservoir 20%%)\n');
fprintf('   [5] LIVE CUSTOM INPUTS (Enter your professor''s exact inputs on the fly!)\n');
fprintf('   [6] Run Full Benchmark Comparison (Fuzzy vs PID vs On-Off over 24 Hours)\n');
fprintf('   [0] Exit\n\n');

choice = input(' Enter your choice (1-6) [Default: 2]: ');
if isempty(choice)
    choice = 2;
end

switch choice
    case 1
        fprintf('\n>>> Executing Preset: Normal Spring Day...\n');
        evaluate_fuzzy_architecture(55.0, 60.0, 25.0, 55.0, 650.0, 2.5, 0.0, 85.0);

    case 2
        fprintf('\n>>> Executing Preset: Severe Heatwave & Drought...\n');
        evaluate_fuzzy_architecture(22.0, 60.0, 42.0, 18.0, 980.0, 4.5, 0.0, 60.0);

    case 3
        fprintf('\n>>> Executing Preset: Torrential Rainstorm Event...\n');
        evaluate_fuzzy_architecture(50.0, 60.0, 22.0, 92.0, 180.0, 5.0, 30.0, 95.0);

    case 4
        fprintf('\n>>> Executing Preset: Critical Water Scarcity / Low Reservoir...\n');
        evaluate_fuzzy_architecture(30.0, 60.0, 36.0, 28.0, 850.0, 3.5, 0.0, 20.0);

    case 5
        fprintf('\n>>> LIVE CUSTOM INPUT MODE (Enter parameters as requested by professor):\n');
        sm   = input('  Enter Current Soil Moisture Content (%) [e.g. 20.0]: ');
        if isempty(sm), sm = 25.0; end
        
        target = input('  Enter Target Soil Moisture Setpoint (%) [e.g. 60.0]: ');
        if isempty(target), target = 60.0; end

        temp = input('  Enter Air Temperature (°C) [e.g. 38.0]: ');
        if isempty(temp), temp = 38.0; end

        rh   = input('  Enter Relative Humidity (%) [e.g. 25.0]: ');
        if isempty(rh), rh = 25.0; end

        sol  = input('  Enter Solar Radiation (W/m²) [e.g. 900.0]: ');
        if isempty(sol), sol = 900.0; end

        wind = input('  Enter Wind Speed (m/s) [e.g. 3.5]: ');
        if isempty(wind), wind = 3.5; end

        rain = input('  Enter Rainfall Depth (mm) [e.g. 0.0]: ');
        if isempty(rain), rain = 0.0; end

        res  = input('  Enter Shared Reservoir Water Storage (%) [e.g. 30.0]: ');
        if isempty(res), res = 30.0; end

        fprintf('\n>>> Evaluating Fuzzy Architecture with Custom Professor Inputs...\n');
        evaluate_fuzzy_architecture(sm, target, temp, rh, sol, wind, rain, res);

    case 6
        fprintf('\n>>> Executing 24-Hour Benchmark Simulation (Fuzzy vs PID vs On-Off)...\n');
        sc_choice = input('  Select scenario (Normal / Heatwave / "Water Scarcity") [Default: Normal]: ', 's');
        if isempty(sc_choice), sc_choice = 'Normal'; end
        simulation.run_benchmark_comparison(sc_choice, 24, 60);

    otherwise
        fprintf('Exiting interactive demo.\n');
end
