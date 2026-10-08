function systems = build_all_systems(output_dir)
% BUILD_ALL_SYSTEMS Constructs and exports all 5 Mamdani Fuzzy Inference Systems
%
% Usage:
%   systems = fuzzy_builder.build_all_systems();
%   systems = fuzzy_builder.build_all_systems('path/to/custom_dir');
%
% Returns a struct containing all 5 initialized FIS objects:
%   .soil_stress
%   .weather_stress
%   .water_demand
%   .main_irrigation
%   .water_allocation

if nargin < 1 || isempty(output_dir)
    % Default to fis_models folder under matlab/
    this_dir = fileparts(mfilename('fullpath'));
    output_dir = fullfile(this_dir, '..', 'fis_models');
end

if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end

fprintf('=================================================================\n');
fprintf('   SMART MULTIZONE IRRIGATION - FUZZY LOGIC TOOLBOX BUILDER      \n');
fprintf('=================================================================\n');

% 1. Soil Stress FIS
fprintf('[1/5] Building Soil Stress FIS (2 inputs, 1 output, 25 rules)...\n');
systems.soil_stress = fuzzy_builder.build_soil_stress_fis();
writeFIS(systems.soil_stress, fullfile(output_dir, 'soil_stress.fis'));

% 2. Weather Stress FIS
fprintf('[2/5] Building Weather Stress FIS (5 inputs, 1 output, 34 rule layers)...\n');
systems.weather_stress = fuzzy_builder.build_weather_stress_fis();
writeFIS(systems.weather_stress, fullfile(output_dir, 'weather_stress.fis'));

% 3. Water Demand FIS
fprintf('[3/5] Building Water Demand FIS (3 inputs, 1 output, 39 rule layers)...\n');
systems.water_demand = fuzzy_builder.build_water_demand_fis();
writeFIS(systems.water_demand, fullfile(output_dir, 'water_demand.fis'));

% 4. Main Supervisory Irrigation FIS
fprintf('[4/5] Building Main Supervisory Irrigation FIS (4 inputs, 1 output, 32 rule layers)...\n');
systems.main_irrigation = fuzzy_builder.build_main_irrigation_fis();
writeFIS(systems.main_irrigation, fullfile(output_dir, 'main_irrigation.fis'));

% 5. Water Allocation FIS
fprintf('[5/5] Building Supervisory Water Allocation FIS (4 inputs, 1 output, 32 rule layers)...\n');
systems.water_allocation = fuzzy_builder.build_water_allocation_fis();
writeFIS(systems.water_allocation, fullfile(output_dir, 'water_allocation.fis'));

fprintf('All 5 Fuzzy Inference Systems built and exported successfully to:\n');
fprintf('  %s\n', output_dir);
fprintf('=================================================================\n');
end
