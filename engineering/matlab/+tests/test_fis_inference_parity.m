function passed = test_fis_inference_parity()
% TEST_FIS_INFERENCE_PARITY Tests edge cases across all 5 Fuzzy Inference Systems

fprintf('Running FIS Inference Boundary and Monotonicity Tests...\n');
passed = true;

% 1. Test FIS 1: Soil Stress
fis1 = fuzzy_builder.build_soil_stress_fis();
s_dry = evalfis(fis1, [0.05, 25.0]); % Very dry, large positive error
s_wet = evalfis(fis1, [0.95, -20.0]); % Very wet, large negative error
assert(s_dry >= 75.0, sprintf('FIS 1 failed: dry stress %.2f expected >= 75', s_dry));
assert(s_wet <= 25.0, sprintf('FIS 1 failed: wet stress %.2f expected <= 25', s_wet));

% 2. Test FIS 2: Weather Stress
fis2 = fuzzy_builder.build_weather_stress_fis();
w_heat = evalfis(fis2, [45.0, 15.0, 1000.0, 12.0, 0.0]); % Heatwave
w_rain = evalfis(fis2, [22.0, 95.0, 100.0, 2.0, 35.0]);   % Heavy rain
assert(w_heat >= 75.0, sprintf('FIS 2 failed: heatwave stress %.2f expected >= 75', w_heat));
assert(w_rain <= 25.0, sprintf('FIS 2 failed: rain stress %.2f expected <= 25', w_rain));

% 3. Test FIS 3: Water Demand
fis3 = fuzzy_builder.build_water_demand_fis();
d_flood = evalfis(fis3, [2.0, 0.0, 40.0]); % Torrential rain, zero deficit
d_parch = evalfis(fis3, [12.0, 12.0, 0.0]); % Parched dry day
assert(d_flood <= 25.0, sprintf('FIS 3 failed: rain demand %.2f expected <= 25', d_flood));
assert(d_parch >= 70.0, sprintf('FIS 3 failed: parched demand %.2f expected >= 70', d_parch));

% 4. Test FIS 4: Main Irrigation FIS
fis4 = fuzzy_builder.build_main_irrigation_fis();
cmd_oversat = evalfis(fis4, [10.0, 10.0, 10.0, -25.0]); % Saturated soil
cmd_depleted = evalfis(fis4, [85.0, 85.0, 85.0, 20.0]); % Severely depleted
assert(cmd_oversat <= 15.0, sprintf('FIS 4 failed: oversaturated command %.2f expected <= 15 (Off)', cmd_oversat));
assert(cmd_depleted >= 75.0, sprintf('FIS 4 failed: depleted command %.2f expected >= 75 (High/Max)', cmd_depleted));

% 5. Test FIS 5: Water Allocation FIS
fis5 = fuzzy_builder.build_water_allocation_fis();
alloc_zero = evalfis(fis5, [0.0, 50.0, 80.0, 85.0]);  % Zero available water
alloc_abundant = evalfis(fis5, [100.0, 80.0, 80.0, 85.0]); % Abundant water, high priority
assert(alloc_zero <= 15.0, sprintf('FIS 5 failed: zero water allocation %.2f expected <= 15', alloc_zero));
assert(alloc_abundant >= 75.0, sprintf('FIS 5 failed: abundant allocation %.2f expected >= 75', alloc_abundant));

fprintf('  ✓ All 5 Fuzzy Inference Systems Passed Functional Boundary Audits!\n');
end
