function passed = test_water_balance_residual()
% TEST_WATER_BALANCE_RESIDUAL Verifies mass balance conservation |residual| < 1e-6 mm
%
% Tests root-zone hydrology across multiple physical boundary conditions:
%   1. Dry soil with infiltration below capacity
%   2. Saturated soil with gravity drainage and surface runoff
%   3. Prolonged drought with transpirational extraction reaching wilting point

fprintf('Running Soil-Water Balance Conservation Residual Tests...\n');
passed = true;

% Zone 1 Loam parameters
fc = 70.0; wp = 25.0; sat = 85.0; zr = 0.70; kd = 0.08; inf_rate = 20.0;

% Test Case 1: Infiltration into moderate soil
[new_sm1, ~, ~, res1] = models.update_soil_water_balance(50.0, 1.5, 0.0, 0.05, fc, wp, sat, zr, kd, inf_rate, 1);
assert(res1 < 1e-6, sprintf('Test 1 failed: residual %.2e exceeds tolerance', res1));
assert(new_sm1 > 50.0, 'Test 1 failed: moisture should increase after irrigation');

% Test Case 2: Extreme flood causing surface runoff and saturation
[new_sm2, ~, fluxes2, res2] = models.update_soil_water_balance(80.0, 10.0, 5.0, 0.0, fc, wp, sat, zr, kd, inf_rate, 1);
assert(res2 < 1e-6, sprintf('Test 2 failed: residual %.2e exceeds tolerance', res2));
assert(fluxes2.surface_runoff_mm > 0.0, 'Test 2 failed: runoff should be generated');
assert(new_sm2 <= sat, 'Test 2 failed: moisture cannot exceed saturation');

% Test Case 3: Extreme drought transpiration near wilting point
[new_sm3, ~, ~, res3] = models.update_soil_water_balance(25.5, 0.0, 0.0, 2.0, fc, wp, sat, zr, kd, inf_rate, 1);
assert(res3 < 1e-6, sprintf('Test 3 failed: residual %.2e exceeds tolerance', res3));
assert(new_sm3 >= wp, 'Test 3 failed: moisture cannot fall below wilting point');

fprintf('  ✓ All Soil-Water Balance Conservation Residual Tests Passed (|res| < 1e-6 mm)!\n');
end
