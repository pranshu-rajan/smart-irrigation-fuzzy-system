function peff = calculate_effective_rain(rainfall_mm, field_capacity, wilting_point)
% CALCULATE_EFFECTIVE_RAIN Estimates Infiltrated Precipitation
%
% Inputs:
%   rainfall_mm: Total precipitation in timestep [mm]
%   field_capacity: Soil Field Capacity [0, 100] %
%   wilting_point: Soil Permanent Wilting Point [0, 100] %
%
% Output:
%   peff: Effective rainfall [mm]

if nargin < 2 || isempty(field_capacity)
    field_capacity = 70.0;
end
if nargin < 3 || isempty(wilting_point)
    wilting_point = 25.0;
end

p = max(0.0, rainfall_mm);
awc = max(1.0, field_capacity - wilting_point);

% USDA Soil Conservation Service (SCS) method adapted for discrete events
% Light rain (<0.2 mm) is assumed lost to interception/evaporation
if p <= 0.2
    peff = 0.0;
else
    % Retention factor decays as rainfall exceeds soil water capacity
    retention_factor = max(0.4, 1.0 - 0.2 * (p / awc));
    peff = min(p, p * retention_factor);
end
end
