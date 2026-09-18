# End-to-End Verification Protocol — v5

## Purpose

The platform is verified as a requirement-driven, predefined-FIS irrigation control system. Users configure the irrigation problem; the platform supplies the validated fuzzy architecture and executes the physical-model/control pipeline.

## User journey

Requirements → Environment → Crop/Soil Plant Model → ET0/ETc → Soil-Water Balance → 4 Zone-Level Mamdani FIS → Zone Requests → Supervisory Allocation FIS + bounded water filling → Virtual Actuation → Soil-State Feedback → Closed-Loop Simulation → Validation → PSO → Scenario Benchmark → Report.

## Verification layers

1. **Mathematical** — ET0, ETc, effective rainfall, crop deficit, soil storage and conservation residuals.
2. **Fuzzy** — all five predefined controllers expose variables, membership functions and rules; representative inference outputs are finite and within the declared output range.
3. **Control** — commands are bounded, zone states evolve through feedback, and allocation respects supply/demand constraints.
4. **Multizone** — three zones are simulated with shared supply and zone-specific state/parameters.
5. **API contract** — every route family and all five FIS inspection endpoints have deterministic smoke coverage; expensive stateful flows remain covered by integration tests.
6. **UI/E2E** — every frontend page must load, resolve its backend dependencies, accept its controls, and display the returned state/results. This layer must be executed against the deployed frontend/backend before claiming release PASS.

## Release evidence

The Architecture page's live verification console uses `/api/verification/system`. It reports actual execution results and must never use hard-coded PASS labels as evidence.

The current focused backend audit passes the endpoint-contract and live-system verification checks. The complete repository suite currently contains 301 tests; a full suite run should be completed in a sufficiently long CI/deployment environment before publishing a 301/301 claim.
