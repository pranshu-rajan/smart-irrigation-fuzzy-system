"""
Results Container, Persistence, and Comparative Analysis for Phase 14 PSO.

Manages:
- Serialization of discovered optimal parameters to `config/fuzzy_optimized_pso.json`.
- Export of convergence iteration logs to `data/processed/pso_convergence.csv`.
- Generation of detailed Markdown and console performance comparison tables
  (Baseline vs. PSO-Optimized) across training, validation, and all scenarios.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime
import pandas as pd
from pydantic import BaseModel, Field

from optimization.parameter_space import FuzzyParameterSpace, PARAM_SPECS
from optimization.fitness import CompositeFitnessResult, ScenarioFitness
from optimization.pso import PSOConfig


class OptimizationReportData(BaseModel):
    """Container for comprehensive optimization artifacts."""
    optimizer_name: str = "Particle Swarm Optimization (PSO)"
    timestamp: str
    pso_config: PSOConfig
    fitness_weights: Dict[str, float]
    training_scenarios: List[str]
    validation_scenarios: List[str]
    baseline_train_fitness: float
    optimized_train_fitness: float
    baseline_val_fitness: float
    optimized_val_fitness: float
    baseline_all_fitness: float
    optimized_all_fitness: float
    parameters: Dict[str, Dict[str, Any]]
    scenario_metrics: Dict[str, Dict[str, Any]]


def save_optimized_parameters_json(
    param_space: FuzzyParameterSpace,
    pso_config: PSOConfig,
    weights_dict: Dict[str, float],
    optimized_theta: Dict[str, float],
    baseline_train_fitness: float,
    optimized_train_fitness: float,
    baseline_val_fitness: float,
    optimized_val_fitness: float,
    baseline_all_fitness: float,
    optimized_all_fitness: float,
    filepath: Path,
) -> None:
    """Save versioned optimized parameters and metadata to JSON."""
    params_dict = {}
    for spec in param_space.specs:
        name = spec.name
        params_dict[name] = {
            "variable": spec.variable_name,
            "set": spec.set_name,
            "param_index": spec.param_index,
            "baseline_value": float(spec.baseline_val),
            "optimized_value": float(optimized_theta[name]),
            "min_bound": float(spec.min_val),
            "max_bound": float(spec.max_val),
            "description": spec.description,
        }

    data = {
        "metadata": {
            "optimizer": "Particle Swarm Optimization (PSO)",
            "timestamp": datetime.now().isoformat(),
            "target_system": "MainIrrigationFIS",
            "seed": pso_config.seed,
            "swarm_size": pso_config.swarm_size,
            "max_iterations": pso_config.max_iterations,
            "inertia_weight": pso_config.inertia_weight,
            "cognitive_coeff": pso_config.cognitive_coeff,
            "social_coeff": pso_config.social_coeff,
            "fitness_weights": weights_dict,
            "training_scenarios": ["Normal", "Hot & Dry", "Rainy", "Cloudy"],
            "validation_scenarios": ["Heatwave", "Water Scarcity"],
        },
        "performance_summary": {
            "training_fitness": {
                "baseline": baseline_train_fitness,
                "optimized": optimized_train_fitness,
                "improvement_pct": ((baseline_train_fitness - optimized_train_fitness) / baseline_train_fitness) * 100.0,
            },
            "validation_fitness": {
                "baseline": baseline_val_fitness,
                "optimized": optimized_val_fitness,
                "improvement_pct": ((baseline_val_fitness - optimized_val_fitness) / baseline_val_fitness) * 100.0,
            },
            "overall_fitness": {
                "baseline": baseline_all_fitness,
                "optimized": optimized_all_fitness,
                "improvement_pct": ((baseline_all_fitness - optimized_all_fitness) / baseline_all_fitness) * 100.0,
            },
        },
        "parameters": params_dict,
    }

    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_convergence_csv(convergence_history: List[Dict[str, Any]], filepath: Path) -> pd.DataFrame:
    """Save iteration-by-iteration convergence history to CSV."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(convergence_history)
    df.to_csv(filepath, index=False)
    return df


def generate_comparison_table(
    baseline_all: CompositeFitnessResult,
    optimized_all: CompositeFitnessResult,
) -> str:
    """
    Generate a formatted Markdown comparison table between baseline and PSO-optimized controller.
    """
    lines = [
        "| Scenario | Partition | Metric | Baseline | PSO-Optimized | Change | Status |",
        "| :--- | :--- | :--- | :---: | :---: | :---: | :---: |",
    ]

    training_names = ["Normal", "Hot & Dry", "Rainy", "Cloudy"]
    
    # Track aggregate sums
    base_mae_list, opt_mae_list = [], []
    base_rmse_list, opt_rmse_list = [], []
    base_vol_list, opt_vol_list = [], []
    base_j_list, opt_j_list = [], []

    for sc_name, b_sc in baseline_all.scenario_fitness.items():
        o_sc = optimized_all.scenario_fitness[sc_name]
        part = "Training" if sc_name in training_names else "Validation"

        base_mae_list.append(b_sc.mae_pct)
        opt_mae_list.append(o_sc.mae_pct)
        base_rmse_list.append(b_sc.rmse_pct)
        opt_rmse_list.append(o_sc.rmse_pct)
        base_vol_list.append(b_sc.water_volume_l)
        opt_vol_list.append(o_sc.water_volume_l)
        base_j_list.append(b_sc.total_fitness)
        opt_j_list.append(o_sc.total_fitness)

        j_diff = o_sc.total_fitness - b_sc.total_fitness
        j_status = "Improved" if j_diff < 0 else "Tradeoff"
        vol_diff = o_sc.water_volume_l - b_sc.water_volume_l
        vol_status = "Saved" if vol_diff < 0 else "Increased"

        lines.append(f"| **{sc_name}** | {part} | MAE (%) | {b_sc.mae_pct:.2f}% | {o_sc.mae_pct:.2f}% | {o_sc.mae_pct - b_sc.mae_pct:+.2f}% | {'Improved' if o_sc.mae_pct <= b_sc.mae_pct else 'Tradeoff'} |")
        lines.append(f"| **{sc_name}** | {part} | Water Volume | {b_sc.water_volume_l:.1f} L | {o_sc.water_volume_l:.1f} L | {vol_diff:+.1f} L | {vol_status} |")
        lines.append(f"| **{sc_name}** | {part} | Fitness J | {b_sc.total_fitness:.4f} | {o_sc.total_fitness:.4f} | {j_diff:+.4f} | {j_status} |")

    # Overall Summary Row
    mean_b_mae = float(np.mean(base_mae_list))
    mean_o_mae = float(np.mean(opt_mae_list))
    tot_b_vol = float(np.sum(base_vol_list))
    tot_o_vol = float(np.sum(opt_vol_list))
    mean_b_j = float(np.mean(base_j_list))
    mean_o_j = float(np.mean(opt_j_list))

    lines.append("| :--- | :--- | :--- | :---: | :---: | :---: | :---: |")
    lines.append(f"| **OVERALL** | All Scenarios | Mean MAE | {mean_b_mae:.2f}% | {mean_o_mae:.2f}% | {mean_o_mae - mean_b_mae:+.2f}% | {'Improved' if mean_o_mae <= mean_b_mae else 'Maintained'} |")
    lines.append(f"| **OVERALL** | All Scenarios | Total Volume | {tot_b_vol:.1f} L | {tot_o_vol:.1f} L | {tot_o_vol - tot_b_vol:+.1f} L | {'Saved' if tot_o_vol <= tot_b_vol else 'Higher'} |")
    lines.append(f"| **OVERALL** | All Scenarios | Composite J | {mean_b_j:.4f} | {mean_o_j:.4f} | {mean_o_j - mean_b_j:+.4f} | {'Improved' if mean_o_j <= mean_b_j else 'Tradeoff'} |")

    return "\n".join(lines)
