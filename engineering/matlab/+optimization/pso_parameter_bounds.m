function [lb, ub, baseline, names] = pso_parameter_bounds()
% PSO_PARAMETER_BOUNDS Returns 18-dimensional bounds for Main Irrigation FIS tuning
%
% 1. Error (5 params):
%    - error_large_neg_d: [-25.0, -5.0], base: -10.0
%    - error_neg_center:  [-14.0, -2.0], base: -7.5
%    - error_zero_halfw:  [2.0, 8.0],    base: 5.0
%    - error_pos_center:  [2.0, 14.0],   base: 7.5
%    - error_large_pos_a: [5.0, 25.0],   base: 10.0
% 2. Soil Stress (4 params):
%    - soil_low_d:        [20.0, 45.0],  base: 35.0
%    - soil_mod_center:   [35.0, 55.0],  base: 45.0
%    - soil_high_center:  [65.0, 85.0],  base: 75.0
%    - soil_vhigh_a:      [65.0, 85.0],  base: 75.0
% 3. Water Demand (5 params):
%    - demand_vlow_d:     [15.0, 35.0],  base: 25.0
%    - demand_low_center: [20.0, 40.0],  base: 30.0
%    - demand_mod_center: [40.0, 60.0],  base: 50.0
%    - demand_high_center:[60.0, 80.0],  base: 70.0
%    - demand_vhigh_a:    [65.0, 85.0],  base: 75.0
% 4. Command Output (4 params):
%    - cmd_off_d:         [8.0, 22.0],   base: 15.0
%    - cmd_low_center:    [18.0, 35.0],  base: 25.0
%    - cmd_mod_center:    [40.0, 60.0],  base: 50.0
%    - cmd_high_center:   [65.0, 85.0],  base: 75.0

lb = [
    -25.0; -14.0; 2.0; 2.0; 5.0; ...       % Error
    20.0; 35.0; 65.0; 65.0; ...            % Soil Stress
    15.0; 20.0; 40.0; 60.0; 65.0; ...      % Water Demand
    8.0; 18.0; 40.0; 65.0                  % Command
];

ub = [
    -5.0; -2.0; 8.0; 14.0; 25.0; ...       % Error
    45.0; 55.0; 85.0; 85.0; ...            % Soil Stress
    35.0; 40.0; 60.0; 80.0; 85.0; ...      % Water Demand
    22.0; 35.0; 60.0; 85.0                 % Command
];

baseline = [
    -10.0; -7.5; 5.0; 7.5; 10.0; ...       % Error
    35.0; 45.0; 75.0; 75.0; ...            % Soil Stress
    25.0; 30.0; 50.0; 70.0; 75.0; ...      % Water Demand
    15.0; 25.0; 50.0; 75.0                 % Command
];

names = {
    'error_large_neg_d'; 'error_neg_center'; 'error_zero_halfw'; 'error_pos_center'; 'error_large_pos_a'; ...
    'soil_low_d'; 'soil_mod_center'; 'soil_high_center'; 'soil_vhigh_a'; ...
    'demand_vlow_d'; 'demand_low_center'; 'demand_mod_center'; 'demand_high_center'; 'demand_vhigh_a'; ...
    'cmd_off_d'; 'cmd_low_center'; 'cmd_mod_center'; 'cmd_high_center'
};
end
