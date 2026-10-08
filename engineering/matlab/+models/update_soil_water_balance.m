function [new_sm, new_storage, fluxes, residual] = update_soil_water_balance(...
    current_sm, irrigation_mm, peff_mm, etc_mm, ...
    fc, wp, sat, root_depth_m, kd, inf_rate_mm_h, dt_min)
% UPDATE_SOIL_WATER_BALANCE Discrete-time dynamic root-zone water balance model
%
% Governing equation:
%   S(t+1) = S(t) + Infiltration - ETc_actual - Drainage
%
% Inputs:
%   current_sm: Soil moisture at step t [0, 100] %
%   irrigation_mm: Applied irrigation depth in step [mm]
%   peff_mm: Effective rainfall depth in step [mm]
%   etc_mm: Crop evapotranspiration demand in step [mm]
%   fc: Field capacity [0, 100] %
%   wp: Permanent wilting point [0, 100] %
%   sat: Saturation capacity [0, 100] %
%   root_depth_m: Root-zone depth Zr [m]
%   kd: Drainage rate coefficient (dimensionless, e.g. 0.08)
%   inf_rate_mm_h: Maximum infiltration capacity [mm/h] (e.g. 20.0)
%   dt_min: Discretization timestep [minutes] (default: 1)
%
% Outputs:
%   new_sm: Updated soil moisture SM(t+1) [%]
%   new_storage: Updated root-zone storage S(t+1) [mm]
%   fluxes: Struct of fluxes (infiltration, runoff, actual_et, drainage)
%   residual: Mass balance conservation error [mm]

if nargin < 11 || isempty(dt_min)
    dt_min = 1;
end

% 1. Convert soil moisture percentages to equivalent storage depths [mm]
% S = 1000 * theta * Zr, where theta = SM / 100
zr_mm = root_depth_m * 1000.0;
s_current = (current_sm / 100.0) * zr_mm;
s_fc      = (fc / 100.0) * zr_mm;
s_wp      = (wp / 100.0) * zr_mm;
s_sat     = (sat / 100.0) * zr_mm;

% 2. Surface Infiltration & Runoff Partitioning
total_surface_water = max(0.0, irrigation_mm) + max(0.0, peff_mm);
max_step_infiltration = inf_rate_mm_h * (dt_min / 60.0);
actual_infiltration = min(total_surface_water, max_step_infiltration);
surface_runoff = total_surface_water - actual_infiltration;

% 3. Transpirational extraction bounded by Wilting Point
s_available_et = max(0.0, s_current + actual_infiltration - s_wp);
actual_et = min(etc_mm, s_available_et);

% 4. Gravity deep drainage above Field Capacity
storage_pre_drainage = s_current + actual_infiltration - actual_et;
if storage_pre_drainage > s_fc
    drainage = kd * (storage_pre_drainage - s_fc);
else
    drainage = 0.0;
end

% 5. Saturation ceiling enforcement (waterlogging rejection)
storage_candidate = storage_pre_drainage - drainage;
if storage_candidate > s_sat
    excess_saturation = storage_candidate - s_sat;
    surface_runoff = surface_runoff + excess_saturation;
    s_next = s_sat;
else
    s_next = max(s_wp, storage_candidate);
end

% 6. Mass conservation check & updated moisture percentage
new_storage = s_next;
new_sm = (new_storage / zr_mm) * 100.0;

% Physical water balance residual: S(t) + Inflows - Outflows - S(t+1)
% Outflows: actual_et + drainage + runoff_from_saturation
inflow = actual_infiltration;
outflow = actual_et + drainage + max(0.0, storage_candidate - s_next);
residual = abs((s_current + inflow - outflow) - s_next);

fluxes.infiltration_mm = actual_infiltration;
fluxes.surface_runoff_mm = surface_runoff;
fluxes.actual_et_mm = actual_et;
fluxes.drainage_mm = drainage;
end
