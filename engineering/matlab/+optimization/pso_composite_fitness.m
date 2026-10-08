function cost = pso_composite_fitness(theta, scenario_name, duration_hours)
% PSO_COMPOSITE_FITNESS Computes multi-objective cost for candidate FIS parameters
%
% Composite Objective Components:
%   1. Root-Mean-Square Tracking Error (RMSE) across all zones
%   2. Normalized Water Volume Applied (efficiency incentive)
%   3. Unmet Water Demand Penalty
%   4. Actuator Command Smoothness (sum of absolute first differences |u(t) - u(t-1)|)

if nargin < 2 || isempty(scenario_name)
    scenario_name = 'Normal';
end
if nargin < 3 || isempty(duration_hours)
    duration_hours = 12; % Fast evaluation duration for optimization loop
end

theta_clean = optimization.pso_repair_vector(theta);

try
    res = simulation.run_multizone_sim(scenario_name, duration_hours, 1, theta_clean);

    % Component 1: Tracking RMSE
    all_errors = res.error(:);
    rmse = sqrt(mean(all_errors.^2));

    % Component 2: Total Water Volume (Liters)
    total_water = sum(res.allocated_vol_l(:));
    water_norm = total_water / 1000.0; % Scale to O(1)

    % Component 3: Unmet demand (Liters)
    total_unmet = sum(res.unmet_vol_l(:));
    unmet_norm = total_unmet / 1000.0;

    % Component 4: Command Chattering / Smoothness
    diff_cmd = diff(res.command, 1, 1);
    smoothness = mean(abs(diff_cmd(:))) / 10.0;

    % Composite Weighted Cost
    % Weights: w1=1.0 (RMSE), w2=0.15 (Water), w3=0.5 (Unmet), w4=0.05 (Smoothness)
    cost = (1.0 * rmse) + (0.15 * water_norm) + (0.50 * unmet_norm) + (0.05 * smoothness);

catch ME
    % High penalty if evaluation fails
    cost = 1e6;
end
end
