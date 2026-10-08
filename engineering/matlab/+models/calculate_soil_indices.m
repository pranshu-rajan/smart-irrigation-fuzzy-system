function [rsm, moisture_error] = calculate_soil_indices(current_sm, target_sm, fc, wp)
% CALCULATE_SOIL_INDICES Computes Relative Soil Moisture and Closed-Loop Error
%
% Inputs:
%   current_sm: Current soil moisture content [0, 100] %
%   target_sm: Target soil moisture setpoint [0, 100] %
%   fc: Field capacity [0, 100] %
%   wp: Permanent wilting point [0, 100] %
%
% Outputs:
%   rsm: Relative Soil Moisture in [0.0, 1.0]
%   moisture_error: e(t) = target_sm - current_sm in [-30, 30] %

% Compute RSM = (SM - WP) / (FC - WP), clamped to [0, 1]
awc = fc - wp;
if awc <= 0
    rsm = 0.5;
else
    rsm = max(0.0, min(1.0, (current_sm - wp) / awc));
end

% Moisture tracking error e(t) = target - current
moisture_error = max(-30.0, min(30.0, target_sm - current_sm));
end
