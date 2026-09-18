"""
Particle Swarm Optimization (PSO) Module for Smart Irrigation Fuzzy Controller Tuning.

Phase 14 offline metaheuristic optimization:
- Parameter space definition and constraints
- Multi-objective closed-loop fitness evaluation
- Standard PSO solver with convergence telemetry
- Baseline vs. optimized comparison persistence
"""

from optimization.parameter_space import FuzzyParameterSpace, PARAM_SPECS, ParameterSpec
from optimization.fitness import FitnessWeights, ScenarioFitness, CompositeFitnessResult, compute_scenario_fitness
from optimization.evaluation import ClosedLoopEvaluator, TRAINING_SCENARIOS, VALIDATION_SCENARIOS, ALL_SCENARIOS
from optimization.pso import PSOConfig, Particle, PSOSolver
from optimization.results import (
    save_optimized_parameters_json,
    save_convergence_csv,
    generate_comparison_table,
)

__all__ = [
    "FuzzyParameterSpace",
    "PARAM_SPECS",
    "ParameterSpec",
    "FitnessWeights",
    "ScenarioFitness",
    "CompositeFitnessResult",
    "compute_scenario_fitness",
    "ClosedLoopEvaluator",
    "TRAINING_SCENARIOS",
    "VALIDATION_SCENARIOS",
    "ALL_SCENARIOS",
    "PSOConfig",
    "Particle",
    "PSOSolver",
    "save_optimized_parameters_json",
    "save_convergence_csv",
    "generate_comparison_table",
]
