function theta_repaired = pso_repair_vector(theta)
% PSO_REPAIR_VECTOR Repairs candidate parameter vector to preserve membership order
%
% Enforces physical constraints:
%   1. Parameter bounds lb <= theta <= ub
%   2. Non-decreasing coordinates: a <= b <= c for trimf and a <= b <= c <= d for trapmf

[lb, ub] = optimization.pso_parameter_bounds();
theta_clamped = max(lb, min(ub, theta(:)));
theta_repaired = theta_clamped;

% Enforce internal geometric spacing
% Error Zero halfwidth >= 2.0
theta_repaired(3) = max(2.0, theta_repaired(3));

% Soil Stress: low_d < mod_center < high_center
theta_repaired(7) = max(theta_repaired(6) + 1.0, theta_repaired(7));
theta_repaired(8) = max(theta_repaired(7) + 5.0, theta_repaired(8));

% Water Demand: vlow_d < low_c < mod_c < high_c
theta_repaired(11) = max(theta_repaired(10) + 1.0, theta_repaired(11));
theta_repaired(12) = max(theta_repaired(11) + 5.0, theta_repaired(12));
theta_repaired(13) = max(theta_repaired(12) + 5.0, theta_repaired(13));

% Command: off_d < low_c < mod_c < high_c
theta_repaired(16) = max(theta_repaired(15) + 1.0, theta_repaired(16));
theta_repaired(17) = max(theta_repaired(16) + 5.0, theta_repaired(17));
theta_repaired(18) = max(theta_repaired(17) + 5.0, theta_repaired(18));
end
