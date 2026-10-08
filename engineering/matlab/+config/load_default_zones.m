function zones = load_default_zones()
% LOAD_DEFAULT_ZONES Returns standard 3-zone agricultural testbed configuration
%
% Zone 1: Tomato / Loam (Area: 100 m², FC: 70%, WP: 25%, SAT: 85%, Priority: 70%)
% Zone 2: Wheat / Sandy (Area: 120 m², FC: 60%, WP: 18%, SAT: 78%, Priority: 40%)
% Zone 3: Maize / Clay  (Area:  80 m², FC: 75%, WP: 30%, SAT: 90%, Priority: 85%)

% Zone 1
z1.id = 1;
z1.name = 'Zone 1 - Tomato / Loam';
z1.crop_name = 'Tomato';
z1.soil_name = 'Loam';
z1.kc = 1.15;
z1.root_depth_m = 0.70;
z1.area_m2 = 100.0;
z1.field_capacity = 70.0;
z1.wilting_point = 25.0;
z1.saturation = 85.0;
z1.infiltration_rate_mm_h = 20.0;
z1.drainage_coefficient = 0.08;
z1.initial_moisture = 55.0;
z1.target_moisture = 60.0;
z1.priority = 70.0; % High-value cash crop

% Zone 2
z2.id = 2;
z2.name = 'Zone 2 - Wheat / Sandy';
z2.crop_name = 'Wheat';
z2.soil_name = 'Sandy';
z2.kc = 0.85;
z2.root_depth_m = 0.90;
z2.area_m2 = 120.0;
z2.field_capacity = 60.0;
z2.wilting_point = 18.0;
z2.saturation = 78.0;
z2.infiltration_rate_mm_h = 45.0;
z2.drainage_coefficient = 0.18;
z2.initial_moisture = 42.0;
z2.target_moisture = 55.0;
z2.priority = 40.0; % Hardy staple cereal

% Zone 3
z3.id = 3;
z3.name = 'Zone 3 - Maize / Clay';
z3.crop_name = 'Maize';
z3.soil_name = 'Clay';
z3.kc = 1.20;
z3.root_depth_m = 1.00;
z3.area_m2 = 80.0;
z3.field_capacity = 75.0;
z3.wilting_point = 30.0;
z3.saturation = 90.0;
z3.infiltration_rate_mm_h = 5.0;
z3.drainage_coefficient = 0.03;
z3.initial_moisture = 65.0;
z3.target_moisture = 65.0;
z3.priority = 85.0; % Critical staple grain

zones = [z1, z2, z3];
end
