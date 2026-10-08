% SMART_MULTIZONE_INIT Initializes Base Workspace for Simulink Simulation
%
% Defines parameters, loaded FIS objects, and zone constants required by:
%   engineering/simulink/smart_multizone_irrigation.slx

clear; clc;
fprintf('Initializing Simulink Smart Multizone Irrigation Model Workspace...\n');

% 1. Simulation Parameters
Ts = 60; % Base sample time = 60 seconds (1 minute)
T_sim = 24 * 3600; % 24 hours in seconds (86,400s)

% 2. Load the 5 Mamdani Fuzzy Inference Systems
fis_path = fullfile(fileparts(mfilename('fullpath')), '..', 'matlab', 'fis_models');
fis_soil = readfis(fullfile(fis_path, 'soil_stress.fis'));
fis_weather = readfis(fullfile(fis_path, 'weather_stress.fis'));
fis_demand = readfis(fullfile(fis_path, 'water_demand.fis'));
fis_main = readfis(fullfile(fis_path, 'main_irrigation.fis'));
fis_alloc = readfis(fullfile(fis_path, 'water_allocation.fis'));

% 3. Agricultural Zone Parameters
matlab_dir = fullfile(fileparts(mfilename('fullpath')), '..', 'matlab');
addpath(matlab_dir);
zones = config.load_default_zones();
Zone1 = zones(1);
Zone2 = zones(2);
Zone3 = zones(3);

% 4. System Capacity Constants
alloc_cfg = config.load_allocation_defaults();
MaxFlowRate_L_min = alloc_cfg.nominal_flow_rate_l_min;
MaxRate_mm_h = alloc_cfg.nominal_max_rate_mm_h;

fprintf('  ✓ FIS Models Loaded from: %s\n', fis_path);
fprintf('  ✓ 3 Agricultural Zones Initialized (Tomato, Wheat, Maize)\n');
fprintf('  ✓ Ready to run Simulink model: smart_multizone_irrigation.slx\n');
