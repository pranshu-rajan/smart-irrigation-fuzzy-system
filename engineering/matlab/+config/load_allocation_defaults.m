function cfg = load_allocation_defaults()
% LOAD_ALLOCATION_DEFAULTS Returns shared irrigation supply parameters
%
% Total Cultivated Area = 100 + 120 + 80 = 300 m²
% Max Delivery Rate = 12.0 mm/h = 0.2 mm/min
% Nominal Flow Capacity = 0.2 mm/min * 300 m² = 60.0 Liters/minute

cfg.total_area_m2 = 300.0;
cfg.nominal_max_rate_mm_h = 12.0;
cfg.nominal_flow_rate_l_min = 60.0;

% Shared supply scenarios and availability factors
cfg.supply_factors.Abundant = 100.0;
cfg.supply_factors.Normal = 100.0;
cfg.supply_factors.ModerateScarcity = 50.0;
cfg.supply_factors.SevereScarcity = 30.0;
cfg.supply_factors.ExtremeScarcity = 10.0;
cfg.supply_factors.ZeroSupply = 0.0;
end
