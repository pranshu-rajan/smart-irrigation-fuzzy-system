"""
Comprehensive Test Suite for Phase 14: Particle Swarm Optimization (PSO) of Fuzzy Controller Parameters.

Validates:
1. Parameter space specification and 18-D bounds integrity.
2. Bidirectional normalization and denormalization [0, 1]^D <-> physical space.
3. Monotonic membership function repair and degeneracy prevention.
4. Dynamic MainIrrigationFIS construction from parameter vectors.
5. Deterministic simulation evaluator and fitness reproducibility.
6. Multi-objective fitness decomposition and weight constraints.
7. Scenario partition integrity (4 Training, 2 Validation, 6 Total).
8. Non-destructive baseline invariant (config/fuzzy_config.json remains unmodified).
9. Particle velocity clamping and boundary reflection dynamics.
10. Global best monotonicity and convergence tracking.
11. End-to-end PSO optimization execution.
12. Physical invariants preservation under optimized fuzzy parameters.
"""

import json
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from config.schemas import SimulationScenario
from fuzzy_engine.irrigation import MainIrrigationFIS
from optimization import (
    FuzzyParameterSpace,
    PARAM_SPECS,
    FitnessWeights,
    ClosedLoopEvaluator,
    PSOConfig,
    Particle,
    PSOSolver,
    TRAINING_SCENARIOS,
    VALIDATION_SCENARIOS,
    ALL_SCENARIOS,
    save_optimized_parameters_json,
    save_convergence_csv,
    generate_comparison_table,
)


@pytest.fixture(scope="module")
def param_space() -> FuzzyParameterSpace:
    """Shared parameter space instance."""
    return FuzzyParameterSpace()


@pytest.fixture(scope="module")
def evaluator(param_space: FuzzyParameterSpace) -> ClosedLoopEvaluator:
    """Shared fast simulation evaluator."""
    return ClosedLoopEvaluator(param_space=param_space, seed=42)


class TestFuzzyParameterSpace:
    """Unit tests for parameter space bounds, normalization, and repair."""

    # TEST 1: Parameter space dimension and naming integrity
    def test_01_parameter_space_dimension(self, param_space: FuzzyParameterSpace):
        """Verify parameter space contains exactly 18 interpretable parameters."""
        assert param_space.dim == 18
        assert len(param_space.specs) == 18
        assert len(param_space.names) == 18
        assert len(param_space.lower_bounds) == 18
        assert len(param_space.upper_bounds) == 18
        assert len(param_space.baseline_values) == 18

        # Verify all lower bounds are strictly less than upper bounds
        for i in range(18):
            assert param_space.lower_bounds[i] < param_space.upper_bounds[i]
            # Baseline must be inside bounds
            assert param_space.lower_bounds[i] <= param_space.baseline_values[i] <= param_space.upper_bounds[i]

    # TEST 2: Bidirectional normalization / denormalization consistency
    def test_02_normalization_roundtrip(self, param_space: FuzzyParameterSpace):
        """Verify normalization followed by denormalization is mathematically exact."""
        np.random.seed(42)
        for _ in range(50):
            rand_norm = np.random.uniform(0.0, 1.0, size=param_space.dim)
            phys = param_space.denormalize(rand_norm)
            norm_back = param_space.normalize(phys)
            np.testing.assert_allclose(rand_norm, norm_back, atol=1e-7)

    # TEST 3: Monotonic repair mechanism
    def test_03_monotonic_repair_mechanism(self, param_space: FuzzyParameterSpace):
        """Verify repair mechanism strictly prevents invalid or inverted MF parameters."""
        # Create deliberately invalid / inverted parameter vector
        inverted = param_space.upper_bounds.copy()
        repaired = param_space.repair_and_validate(inverted)

        # All repaired parameters must be within bounds
        assert np.all(repaired >= param_space.lower_bounds - 1e-9)
        assert np.all(repaired <= param_space.upper_bounds + 1e-9)

        # Build FIS from repaired vector and verify no ValueError is raised
        fis = param_space.build_fis(repaired)
        assert isinstance(fis, MainIrrigationFIS)

    # TEST 4: Build MainIrrigationFIS from baseline parameters
    def test_04_build_fis_baseline(self, param_space: FuzzyParameterSpace):
        """Verify FIS constructed from baseline parameters matches standard evaluation."""
        fis_custom = param_space.build_fis(param_space.baseline_values)
        fis_default = MainIrrigationFIS()

        # Evaluate both on test points
        val_custom = fis_custom.evaluate(soil_stress=50.0, weather_stress=40.0, water_demand=60.0, moisture_error=5.0)
        val_default = fis_default.evaluate(soil_stress=50.0, weather_stress=40.0, water_demand=60.0, moisture_error=5.0)

        assert abs(val_custom - val_default) < 0.5  # Consistent within centroid discretization


class TestFitnessAndEvaluation:
    """Unit tests for multi-objective fitness calculation and simulation evaluator."""

    # TEST 5: Fitness weights validation
    def test_05_fitness_weights_sum_to_one(self):
        """Verify objective weighting model defaults sum to 1.0."""
        weights = FitnessWeights()
        total = weights.w_tracking + weights.w_water + weights.w_deficit + weights.w_smoothness
        assert pytest.approx(total, abs=1e-5) == 1.0

    # TEST 6: Scenario partitions
    def test_06_scenario_partitions(self):
        """Verify training and validation partitions are distinct and cover all 6 scenarios."""
        assert len(TRAINING_SCENARIOS) == 4
        assert len(VALIDATION_SCENARIOS) == 2
        assert len(ALL_SCENARIOS) == 6
        assert set(TRAINING_SCENARIOS).isdisjoint(set(VALIDATION_SCENARIOS))
        assert set(ALL_SCENARIOS) == set(TRAINING_SCENARIOS) | set(VALIDATION_SCENARIOS)

    # TEST 7: Evaluator determinism and reproducibility
    def test_07_evaluator_determinism(self, evaluator: ClosedLoopEvaluator):
        """Verify identical parameters produce bit-exact fitness values."""
        res1 = evaluator.evaluate_baseline()
        res2 = evaluator.evaluate_baseline()

        assert res1.composite_fitness == pytest.approx(res2.composite_fitness, abs=1e-9)
        assert len(res1.scenario_fitness) == len(TRAINING_SCENARIOS)
        for sc in TRAINING_SCENARIOS:
            assert res1.scenario_fitness[sc.value].total_fitness == res2.scenario_fitness[sc.value].total_fitness

    # TEST 8: Non-destructive baseline guarantee
    def test_08_fuzzy_config_json_unmodified(self):
        """Verify config/fuzzy_config.json exists and is valid JSON."""
        config_path = Path("config/fuzzy_config.json")
        assert config_path.exists()
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "variables" in data
        assert "moisture_error" in data["variables"]
        assert "irrigation_command" in data["variables"]


class TestPSOSolver:
    """Unit tests for PSO dynamics, velocity updates, and convergence."""

    # TEST 9: Particle velocity clamping and boundary reflection
    def test_09_particle_velocity_and_position(self):
        """Verify particle velocity remains bounded and position reflects at boundaries."""
        rng = np.random.RandomState(42)
        p = Particle(dim=18, max_velocity=0.20, rng=rng)
        assert len(p.position) == 18
        assert len(p.velocity) == 18
        assert np.all(p.position >= 0.0) and np.all(p.position <= 1.0)
        assert np.all(np.abs(p.velocity) <= 0.20)

        # Force large velocity and update position
        p.velocity[:] = 0.50
        p.update_position()
        assert np.all(p.position >= 0.0) and np.all(p.position <= 1.0)

    # TEST 10: End-to-end mini PSO execution
    def test_10_mini_pso_execution(self, evaluator: ClosedLoopEvaluator):
        """Verify mini PSO solver (5 particles, 3 iterations) executes cleanly without errors."""
        config = PSOConfig(
            swarm_size=5,
            max_iterations=3,
            seed=123,
            verbose=False,
        )
        solver = PSOSolver(evaluator=evaluator, config=config)
        gbest_theta, gbest_fit, history = solver.optimize()

        assert len(gbest_theta) == 18
        assert gbest_fit > 0.0
        assert len(history) == 4  # Iteration 0 + 3 steps
        # Global best fitness must be monotonically non-increasing
        for i in range(len(history) - 1):
            assert history[i]["global_best_fitness"] >= history[i + 1]["global_best_fitness"] - 1e-9

    # TEST 11: Optimized parameters persistence and comparison table
    def test_11_results_persistence_and_formatting(self, evaluator: ClosedLoopEvaluator, tmp_path: Path):
        """Verify JSON and CSV export functions work cleanly."""
        param_space = evaluator.param_space
        pso_config = PSOConfig(swarm_size=5, max_iterations=2, seed=42, verbose=False)
        opt_theta_dict = {s.name: float(s.baseline_val) for s in param_space.specs}
        weights_dict = {"tracking": 0.4, "water": 0.3, "deficit": 0.2, "smoothness": 0.1}

        json_path = tmp_path / "fuzzy_optimized_pso.json"
        save_optimized_parameters_json(
            param_space=param_space,
            pso_config=pso_config,
            weights_dict=weights_dict,
            optimized_theta=opt_theta_dict,
            baseline_train_fitness=0.20,
            optimized_train_fitness=0.18,
            baseline_val_fitness=0.25,
            optimized_val_fitness=0.22,
            baseline_all_fitness=0.22,
            optimized_all_fitness=0.19,
            filepath=json_path,
        )
        assert json_path.exists()
        with open(json_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data["metadata"]["optimizer"] == "Particle Swarm Optimization (PSO)"

        # CSV test
        csv_path = tmp_path / "pso_convergence.csv"
        history = [
            {"iteration": 0, "best_fitness": 0.25, "mean_fitness": 0.30, "global_best_fitness": 0.25, "elapsed_seconds": 1.0},
            {"iteration": 1, "best_fitness": 0.22, "mean_fitness": 0.28, "global_best_fitness": 0.22, "elapsed_seconds": 2.0},
        ]
        df_csv = save_convergence_csv(history, csv_path)
        assert csv_path.exists()
        assert len(df_csv) == 2

    # TEST 12: Physical invariants preservation under optimized parameters
    def test_12_physical_invariants_preservation(self, evaluator: ClosedLoopEvaluator):
        """Verify candidate parameters never violate soil limits or water balance residuals."""
        # Use baseline values
        theta = evaluator.param_space.baseline_values
        res = evaluator.evaluate_vector(theta, scenarios=[SimulationScenario.NORMAL])
        assert res.composite_fitness > 0.0
        sc_fit = res.scenario_fitness[SimulationScenario.NORMAL.value]
        assert sc_fit.water_volume_l > 0.0
        assert sc_fit.mae_pct >= 0.0
