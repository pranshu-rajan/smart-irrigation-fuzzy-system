function run_all_matlab_tests()
% RUN_ALL_MATLAB_TESTS Master Test Runner for MATLAB Engineering Suite

fprintf('=================================================================\n');
fprintf('     SMART MULTIZONE IRRIGATION - MATLAB TEST SUITE AUDIT        \n');
fprintf('=================================================================\n');

t_start = tic;
all_passed = true;

try
    p1 = tests.test_water_allocation_invariants();
    p2 = tests.test_water_balance_residual();
    p3 = tests.test_fis_inference_parity();
    all_passed = p1 && p2 && p3;
catch ME
    all_passed = false;
    fprintf('  ✗ TEST SUITE FAILED with error:\n    %s\n', ME.message);
end

t_elapsed = toc(t_start);
fprintf('=================================================================\n');
if all_passed
    fprintf('   STATUS: 100%% ALL TESTS PASSED SUCCESSFULLY (Elapsed: %.2fs)\n', t_elapsed);
else
    fprintf('   STATUS: TEST SUITE FAILED\n');
end
fprintf('=================================================================\n');
end
