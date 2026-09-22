# End-to-End Completion Notes

## Production control path

The production multizone simulator is now explicitly:

Weather -> FAO-56 ET0 -> crop ETc/effective rainfall -> soil state ->
Soil Stress FIS -> Weather Stress FIS -> Water Demand FIS -> Main Irrigation FIS ->
zone requests -> Water Allocation FIS -> bounded priority water-filling ->
root-zone water balance -> next soil state -> feedback.

All five controllers are Mamdani FIS using minimum AND/implication, maximum OR/aggregation,
and centroid defuzzification.

## PSO adaptation model

PSO remains an **offline** optimizer. A completed PSO run writes its validated 18-parameter
Main Irrigation calibration to `config/active_fuzzy_parameters.json`. Subsequent production
simulations automatically load that active calibration. Until a PSO run is activated, the
expert baseline controller is used.

This is correctly described as **offline PSO-based adaptive/calibrated fuzzy control**, not
online self-adaptive control.

## Corrected simulation bug

The allocation simulator previously reused the last zone's soil infiltration/drainage
parameters when updating every zone. The loop now retrieves `zone_params[z_id]` for each zone,
so each zone's root-zone water balance is physically independent.

Telemetry now records the post-update soil moisture (`t+1`) for each step, matching the
closed-loop state transition.

## Frontend/backend FIS diagnostics

The FIS explorer now supports both current and legacy backend rule endpoints and safely uses
backend rule counts. This prevents a stale/deployed backend contract from rendering `0 Rules`
when the backend actually exposes a populated rule base.
