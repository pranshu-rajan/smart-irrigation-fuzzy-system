function fis = build_main_irrigation_fis(custom_params)
% BUILD_MAIN_IRRIGATION_FIS Constructs FIS 4: Main Supervisory Irrigation FIS
%
% Inputs:
%   1. soil_stress: Soil Moisture Stress [0.0, 100.0] %
%   2. weather_stress: Atmospheric Weather Stress [0.0, 100.0] %
%   3. water_demand: Crop Water Demand [0.0, 100.0] %
%   4. moisture_error: Moisture Tracking Error [-30.0, 30.0] %
%
% Output:
%   1. irrigation_command: Normalized Irrigation Output [0.0, 100.0] %
%
% Optional Argument:
%   custom_params: Vector of 18 parameters calibrated by PSO

if nargin < 1
    custom_params = [];
end

fis = mamfis('Name', 'main_irrigation', ...
             'AndMethod', 'min', ...
             'OrMethod', 'max', ...
             'ImplicationMethod', 'min', ...
             'AggregationMethod', 'max', ...
             'DefuzzificationMethod', 'centroid');

% Default parameters
err_large_neg_d = -10.0;
err_neg_c = -7.5;
err_zero_w = 5.0;
err_pos_c = 7.5;
err_large_pos_a = 10.0;

soil_low_d = 35.0;
soil_mod_c = 45.0;
soil_high_c = 75.0;
soil_vhigh_a = 75.0;

wd_vlow_d = 25.0;
wd_low_c = 30.0;
wd_mod_c = 50.0;
wd_high_c = 70.0;
wd_vhigh_a = 75.0;

cmd_off_d = 15.0;
cmd_low_c = 25.0;
cmd_mod_c = 50.0;
cmd_high_c = 75.0;

% Override if custom PSO parameter vector provided
if ~isempty(custom_params) && numel(custom_params) == 18
    err_large_neg_d = custom_params(1);
    err_neg_c       = custom_params(2);
    err_zero_w      = custom_params(3);
    err_pos_c       = custom_params(4);
    err_large_pos_a = custom_params(5);

    soil_low_d      = custom_params(6);
    soil_mod_c      = custom_params(7);
    soil_high_c     = custom_params(8);
    soil_vhigh_a    = custom_params(9);

    wd_vlow_d       = custom_params(10);
    wd_low_c        = custom_params(11);
    wd_mod_c        = custom_params(12);
    wd_high_c       = custom_params(13);
    wd_vhigh_a      = custom_params(14);

    cmd_off_d       = custom_params(15);
    cmd_low_c       = custom_params(16);
    cmd_mod_c       = custom_params(17);
    cmd_high_c      = custom_params(18);
end

% Input 1: soil_stress [0, 100]
fis = addInput(fis, [0 100], 'Name', 'soil_stress');
fis = addMF(fis, 'soil_stress', 'trapmf', [0.0 0.0 15.0 soil_low_d], 'Name', 'Low');
fis = addMF(fis, 'soil_stress', 'trimf',  [soil_low_d-10.0 soil_mod_c soil_mod_c+20.0], 'Name', 'Moderate');
fis = addMF(fis, 'soil_stress', 'trimf',  [soil_mod_c+10.0 soil_high_c 85.0], 'Name', 'High');
fis = addMF(fis, 'soil_stress', 'trapmf', [soil_vhigh_a 85.0 100.0 100.0], 'Name', 'Very_High');

% Input 2: weather_stress [0, 100]
fis = addInput(fis, [0 100], 'Name', 'weather_stress');
fis = addMF(fis, 'weather_stress', 'trapmf', [0.0 0.0 15.0 35.0],       'Name', 'Low');
fis = addMF(fis, 'weather_stress', 'trimf',  [25.0 45.0 65.0],          'Name', 'Moderate');
fis = addMF(fis, 'weather_stress', 'trimf',  [55.0 75.0 85.0],          'Name', 'High');
fis = addMF(fis, 'weather_stress', 'trapmf', [75.0 85.0 100.0 100.0],   'Name', 'Very_High');

% Input 3: water_demand [0, 100]
fis = addInput(fis, [0 100], 'Name', 'water_demand');
fis = addMF(fis, 'water_demand', 'trapmf', [0.0 0.0 10.0 wd_vlow_d],    'Name', 'Very_Low');
fis = addMF(fis, 'water_demand', 'trimf',  [wd_vlow_d-10.0 wd_low_c wd_low_c+15.0], 'Name', 'Low');
fis = addMF(fis, 'water_demand', 'trimf',  [wd_low_c+5.0 wd_mod_c wd_mod_c+15.0], 'Name', 'Moderate');
fis = addMF(fis, 'water_demand', 'trimf',  [wd_mod_c+5.0 wd_high_c 85.0], 'Name', 'High');
fis = addMF(fis, 'water_demand', 'trapmf', [wd_vhigh_a 90.0 100.0 100.0], 'Name', 'Very_High');

% Input 4: moisture_error [-30, 30]
fis = addInput(fis, [-30 30], 'Name', 'moisture_error');
fis = addMF(fis, 'moisture_error', 'trapmf', [-30.0 -30.0 -20.0 err_large_neg_d], 'Name', 'Large_Negative');
fis = addMF(fis, 'moisture_error', 'trimf',  [-15.0 err_neg_c 0.0],               'Name', 'Negative');
fis = addMF(fis, 'moisture_error', 'trimf',  [-err_zero_w 0.0 err_zero_w],         'Name', 'Zero');
fis = addMF(fis, 'moisture_error', 'trimf',  [0.0 err_pos_c 15.0],                'Name', 'Positive');
fis = addMF(fis, 'moisture_error', 'trapmf', [err_large_pos_a 20.0 30.0 30.0],    'Name', 'Large_Positive');

% Output: irrigation_command [0, 100]
fis = addOutput(fis, [0 100], 'Name', 'irrigation_command');
fis = addMF(fis, 'irrigation_command', 'trapmf', [0.0 0.0 5.0 cmd_off_d], 'Name', 'Off');
fis = addMF(fis, 'irrigation_command', 'trimf',  [cmd_off_d-5.0 cmd_low_c cmd_low_c+15.0], 'Name', 'Low');
fis = addMF(fis, 'irrigation_command', 'trimf',  [cmd_low_c+5.0 cmd_mod_c cmd_mod_c+20.0], 'Name', 'Moderate');
fis = addMF(fis, 'irrigation_command', 'trimf',  [cmd_mod_c+10.0 cmd_high_c 90.0], 'Name', 'High');
fis = addMF(fis, 'irrigation_command', 'trapmf', [80.0 90.0 100.0 100.0], 'Name', 'Maximum');

% Rules matrix [SoilStress, WeatherStress, WaterDemand, MoistureError, OutputCmd, Weight, Conn]
rules = [];

% Layer 1: Oversaturation Suppression (Error < 0)
% R1: error Large Neg -> Off(1)
rules = [rules; 0 0 0 1 1 1 1];
% R2: error Neg(2), soil low/mod(1,2) -> Off(1)
rules = [rules; 1 0 0 2 1 1 1; 2 0 0 2 1 1 1];
% R3: error Neg(2), soil high/vhigh(3,4), demand vlow/low/mod(1,2,3) -> Off(1)
for s = [3 4]
    for d = [1 2 3]
        rules = [rules; s 0 d 2 1 1 1];
    end
end
% R4: error Neg(2), soil high/vhigh(3,4), demand high/vhigh(4,5) -> Low(2)
for s = [3 4]
    for d = [4 5]
        rules = [rules; s 0 d 2 2 1 1];
    end
end

% Layer 2: At-Target Regulation (Error = Zero(3))
rules = [rules;
    1 0 1 3 1 1 1; % R5: soil low, demand vlow -> Off(1)
    1 0 2 3 2 1 1; % R6: soil low, demand low/mod -> Low(2)
    1 0 3 3 2 1 1;
    1 0 4 3 3 1 1; % R7: soil low, demand high/vhigh -> Mod(3)
    1 0 5 3 3 1 1;
    2 0 1 3 2 1 1; % R8: soil mod, demand vlow/low -> Low(2)
    2 0 2 3 2 1 1;
    2 0 3 3 3 1 1; % R9: soil mod, demand mod -> Mod(3)
    2 0 4 3 4 1 1; % R10: soil mod, demand high/vhigh -> High(4)
    2 0 5 3 4 1 1;
    3 0 1 3 3 1 1; % R11: soil high, demand vlow/low -> Mod(3)
    3 0 2 3 3 1 1;
    3 0 3 3 4 1 1; % R12: soil high, demand mod/high -> High(4)
    3 0 4 3 4 1 1;
    3 0 5 3 5 1 1; % R13: soil high, demand vhigh -> Max(5)
    4 0 1 3 4 1 1; % R14: soil vhigh, demand vlow/low -> High(4)
    4 0 2 3 4 1 1;
    4 0 3 3 5 1 1; % R15: soil vhigh, demand mod/high/vhigh -> Max(5)
    4 0 4 3 5 1 1;
    4 0 5 3 5 1 1;
];

% Layer 3: Positive Error Deficit Replacement (Error = Positive(4))
rules = [rules;
    1 0 1 4 2 1 1; % R16: soil low, demand vlow/low -> Low(2)
    1 0 2 4 2 1 1;
    1 0 3 4 3 1 1; % R17: soil low, demand mod -> Mod(3)
    1 0 4 4 4 1 1; % R18: soil low, demand high/vhigh -> High(4)
    1 0 5 4 4 1 1;
    2 0 1 4 3 1 1; % R19: soil mod, demand vlow/low -> Mod(3)
    2 0 2 4 3 1 1;
    2 0 3 4 3 1 1; % R20: soil mod, demand mod -> Mod(3)
    2 0 4 4 4 1 1; % R21: soil mod, demand high/vhigh -> High(4)
    2 0 5 4 4 1 1;
    3 0 1 4 4 1 1; % R22: soil high, demand vlow/low -> High(4)
    3 0 2 4 4 1 1;
    3 0 3 4 4 1 1; % R23: soil high, demand mod/high -> High(4)
    3 0 4 4 4 1 1;
    3 0 5 4 5 1 1; % R24: soil high, demand vhigh -> Max(5)
    4 0 0 4 5 1 1; % R25: soil vhigh -> Max(5)
];

% Layer 4: Severe Depletion Override (Error = Large Positive(5))
rules = [rules;
    1 0 0 5 3 1 1; % R26: soil low -> Mod(3)
    2 0 0 5 4 1 1; % R27: soil mod -> High(4)
    3 0 0 5 5 1 1; % R28: soil high/vhigh -> Max(5)
    4 0 0 5 5 1 1;
];

% Layer 5: Climatic Forcing & Environmental Modulation
% R29: weather vhigh(4), error pos/large_pos(4,5), soil mod/high/vhigh(2,3,4) -> Max(5)
for e = [4 5]
    for s = [2 3 4]
        rules = [rules; s 4 0 e 5 1 1];
    end
end
% R30: weather vhigh(4), error zero(3), soil high/vhigh(3,4) -> Max(5)
for s = [3 4]
    rules = [rules; s 4 0 3 5 1 1];
end
% R31: weather high(3), error pos/large_pos(4,5), demand high/vhigh(4,5) -> High(4)
for e = [4 5]
    for d = [4 5]
        rules = [rules; 0 3 d e 4 1 1];
    end
end
% R32: weather low(1), soil low(1), demand vlow(1) -> Off(1)
rules = [rules; 1 1 1 0 1 1 1];

fis = addRule(fis, rules);
end
