function [allocated_vol, unmet_vol, is_constrained] = bounded_water_allocation(requests_vol, priorities_pct, available_supply_vol)
% BOUNDED_WATER_ALLOCATION Deterministic Priority-Weighted Water Filling
%
% Enforces all 7 physical water conservation invariants:
%   A. Zero supply: W_avail == 0 -> A_z == 0 for all z
%   B. Zero request: R_z == 0 -> A_z == 0
%   C. Demand ceiling: 0 <= A_z <= R_z for all z
%   D. Supply ceiling: sum(A_z) <= available_supply_vol
%   E. Full satisfaction: sum(R_z) <= available_supply_vol -> A_z == R_z
%   F. Priority sensitivity under scarcity: higher priority gets larger allocation up to ceiling
%   G. No artificial water creation: A_z never exceeds R_z
%
% Inputs:
%   requests_vol: Vector of unconstrained raw requested volumes (Liters) [1 x N]
%   priorities_pct: Vector of zone priority weights [0, 100] % [1 x N]
%   available_supply_vol: Total shared water available in timestep (Liters)
%
% Outputs:
%   allocated_vol: Vector of physically granted volumes (Liters) [1 x N]
%   unmet_vol: Vector of unfulfilled water requests R_z - A_z (Liters) [1 x N]
%   is_constrained: Boolean flag indicating if supply strictly limited total requests

num_zones = numel(requests_vol);
allocated_vol = zeros(size(requests_vol));
w_avail = max(0.0, available_supply_vol);
ceilings = max(0.0, requests_vol);
total_request = sum(ceilings);

% Invariant A: Zero supply
if w_avail <= 1e-12
    unmet_vol = ceilings;
    is_constrained = total_request > 0;
    return;
end

% Invariant E: Supply exceeds or meets all requests in full
if total_request <= w_avail
    allocated_vol = ceilings;
    unmet_vol = zeros(size(ceilings));
    is_constrained = false;
    return;
end

% Scarcity: Iterative Priority-Weighted Water-Filling
is_constrained = true;
active_mask = (ceilings > 1e-12);
rem_supply = w_avail;

while rem_supply > 1e-12 && any(active_mask)
    active_indices = find(active_mask);
    active_weights = max(1.0, priorities_pct(active_indices));
    total_active_w = sum(active_weights);
    
    % Proposed incremental shares
    delta_shares = rem_supply * (active_weights / total_active_w);
    
    % Check if any active zone hits or exceeds its ceiling
    new_tentative = allocated_vol(active_indices) + delta_shares;
    hits_ceiling = (new_tentative >= ceilings(active_indices) - 1e-12);
    
    if ~any(hits_ceiling)
        % No zone reached ceiling: allocate all proposed shares and terminate
        allocated_vol(active_indices) = new_tentative;
        rem_supply = 0.0;
        break;
    else
        % Cap the saturated zones and iterate with surplus supply
        for k = 1:numel(active_indices)
            idx = active_indices(k);
            if hits_ceiling(k)
                added = ceilings(idx) - allocated_vol(idx);
                allocated_vol(idx) = ceilings(idx);
                rem_supply = max(0.0, rem_supply - added);
                active_mask(idx) = false; % Remove from active set
            end
        end
    end
end

% Final numerical safety clamping
allocated_vol = min(ceilings, max(0.0, allocated_vol));
if sum(allocated_vol) > w_avail
    allocated_vol = allocated_vol * (w_avail / sum(allocated_vol));
end

unmet_vol = max(0.0, ceilings - allocated_vol);
end
