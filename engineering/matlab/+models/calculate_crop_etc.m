function [etc, crop_deficit] = calculate_crop_etc(et0, kc, peff)
% CALCULATE_CROP_ETC Computes Crop ETc and Net Water Deficit
%
% Inputs:
%   et0: Reference evapotranspiration [mm/day]
%   kc: Single crop coefficient (dimensionless)
%   peff: Effective rainfall [mm/day]
%
% Outputs:
%   etc: Crop evapotranspiration [mm/day]
%   crop_deficit: Crop water deficit max(ETc - Peff, 0) [mm/day]

if nargin < 3 || isempty(peff)
    peff = 0.0;
end

etc = max(0.0, et0 .* kc);
crop_deficit = max(0.0, etc - peff);
end
