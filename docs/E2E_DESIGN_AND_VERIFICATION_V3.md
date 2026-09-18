# E2E Fuzzy Irrigation Designer & Verification — v3

## Purpose
The Architecture page is now the entry point for designing a software-only multizone fuzzy irrigation system from user requirements. It is a guided configuration workflow, not a static diagram.

## Design workflow
1. Requirements — zones, crop/soil, area, moisture targets, root depth, Kc and priority.
2. Environment/resource — weather scenario, shared water condition and simulation duration.
3. Plant model — ET0, ETc and dynamic soil-water state.
4. Fuzzy architecture — four zone-level Mamdani FIS plus one supervisory allocation FIS; fuzzification, rules, inference, aggregation and centroid defuzzification are explicitly exposed.
5. Closed loop — save the configuration and invoke the real multizone simulation engine.
6. Evidence — use the resulting run for telemetry, scenario benchmarking, PSO optimization and reporting.

## Live verification
`GET /api/verification/system` executes real repository components and returns PASS/FAIL checks for fuzzy rule bases, live inference, weather/ET0, the 3-zone closed loop and supply conservation. The Architecture page renders those results dynamically.

## Important design boundary
The guided designer configures the validated controller architecture; it does not pretend to synthesize arbitrary new membership functions/rules at runtime. Arbitrary FIS synthesis would require a versioned backend configuration schema, persistence, safety/coverage validation, and a simulation adapter.

## Current regression status
The repository currently collects 300 tests. A focused run reached 174 tests and passed through the allocation tests before the execution environment timeout. Therefore, do not label the whole suite as 300/300 PASS until a complete regression run finishes in CI/local development.
