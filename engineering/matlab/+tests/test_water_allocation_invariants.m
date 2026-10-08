function passed = test_water_allocation_invariants()
% TEST_WATER_ALLOCATION_INVARIANTS Verifies all 7 physical water invariants
%
% Tests:
%   A. Zero supply invariant: W_avail == 0 -> A_z == 0
%   B. Zero request invariant: R_z == 0 -> A_z == 0
%   C. Demand ceiling invariant: A_z <= R_z
%   D. Supply ceiling invariant: sum(A_z) <= W_avail
%   E. Full satisfaction: sum(R_z) <= W_avail -> A_z == R_z
%   F. Priority sensitivity under scarcity
%   G. Non-negativity invariant: A_z >= 0

fprintf('Running Water Allocation Invariant Tests...\n');
passed = true;

priorities = [70.0, 40.0, 85.0]; % Z1, Z2, Z3

% Invariant A: Zero supply
req1 = [10.0, 15.0, 20.0];
[alloc1, ~, ~] = models.bounded_water_allocation(req1, priorities, 0.0);
assert(all(alloc1 == 0.0), 'Invariant A failed: non-zero allocation under zero supply');

% Invariant B: Zero request
req2 = [0.0, 15.0, 20.0];
[alloc2, ~, ~] = models.bounded_water_allocation(req2, priorities, 50.0);
assert(alloc2(1) == 0.0, 'Invariant B failed: allocated water to zero-request zone');

% Invariant C: Demand ceiling
req3 = [12.0, 18.0, 25.0];
[alloc3, ~, ~] = models.bounded_water_allocation(req3, priorities, 100.0);
assert(all(alloc3 <= req3 + 1e-12), 'Invariant C failed: allocation exceeded demand ceiling');

% Invariant D: Supply ceiling
supply4 = 20.0;
[alloc4, ~, constr4] = models.bounded_water_allocation(req3, priorities, supply4);
assert(sum(alloc4) <= supply4 + 1e-12, 'Invariant D failed: total allocation exceeded supply');
assert(constr4 == true, 'Invariant D failed: is_constrained flag should be true');

% Invariant E: Full satisfaction
supply5 = 100.0;
[alloc5, ~, constr5] = models.bounded_water_allocation(req3, priorities, supply5);
assert(all(abs(alloc5 - req3) < 1e-12), 'Invariant E failed: requests not fully satisfied');
assert(constr5 == false, 'Invariant E failed: is_constrained flag should be false');

% Invariant F: Priority sensitivity under scarcity (equal requests, unequal priorities)
req6 = [10.0, 10.0, 10.0];
supply6 = 15.0; % Scarcity
[alloc6, ~, ~] = models.bounded_water_allocation(req6, priorities, supply6);
% Priorities are Z2(40) < Z1(70) < Z3(85) -> Expect Alloc(2) < Alloc(1) < Alloc(3)
assert(alloc6(2) < alloc6(1) && alloc6(1) < alloc6(3), ...
    'Invariant F failed: allocation ordering did not respect priority weights');

% Invariant G: Non-negativity
assert(all(alloc6 >= 0.0), 'Invariant G failed: negative allocation produced');

fprintf('  ✓ All 7 Water Allocation Invariants Passed Successfully!\n');
end
