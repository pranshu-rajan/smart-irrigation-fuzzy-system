"""
Multi-Objective Closed-Loop Fitness Function for Phase 14 PSO.

Evaluates the actual closed-loop dynamic irrigation simulation across canonical scenarios.
Balances 4 interpretable engineering objectives:
1. E_tracking: Normalized Root Mean Square Error (RMSE) of soil moisture from target setpoint.
2. E_water: Normalized volumetric water consumption relative to reference ceiling.
3. E_deficit: Penalty for time spent below the allowable moisture depletion threshold.
4. E_smoothness: Penalty for high-frequency control chatter / actuator command oscillation.

Formulation:
    J = w_tracking * E_tracking + w_water * E_water + w_deficit * E_deficit + w_smoothness * E_smoothness
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from config.schemas import SimulationScenario
from simulation.closed_loop import ClosedLoopMetrics


class FitnessWeights(BaseModel):
    """Normalized weights for multi-objective fitness calculation."""
    w_tracking: float = Field(default=0.40, ge=0.0, le=1.0, description="Weight for moisture tracking error")
    w_water: float = Field(default=0.30, ge=0.0, le=1.0, description="Weight for water conservation")
    w_deficit: float = Field(default=0.20, ge=0.0, le=1.0, description="Weight for moisture deficit penalty")
    w_smoothness: float = Field(default=0.10, ge=0.0, le=1.0, description="Weight for control smoothness penalty")

    def __post_init__(self):
        total = self.w_tracking + self.w_water + self.w_deficit + self.w_smoothness
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"Fitness weights must sum to 1.0. Got: {total}")


class ScenarioFitness(BaseModel):
    """Decomposed fitness components for a single simulation scenario."""
    scenario: str
    total_fitness: float
    e_tracking: float
    e_water: float
    e_deficit: float
    e_smoothness: float
    mae_pct: float
    rmse_pct: float
    water_volume_l: float
    deficit_minutes: int
    control_variation: float


class CompositeFitnessResult(BaseModel):
    """Aggregated multi-scenario evaluation result."""
    composite_fitness: float
    scenario_fitness: Dict[str, ScenarioFitness]


def compute_scenario_fitness(
    df: pd.DataFrame,
    metrics: ClosedLoopMetrics,
    weights: Optional[FitnessWeights] = None,
    target_moisture: float = 60.0,
    wilting_point: float = 25.0,
    field_capacity: float = 70.0,
    reference_max_volume_l: float = 8000.0,
) -> ScenarioFitness:
    """
    Compute decomposed and weighted fitness for a 24-hour closed-loop simulation trajectory.

    Args:
        df: Simulation DataFrame with columns ['soil_moisture', 'irrigation_command', 'applied_irrigation_l']
        metrics: Pre-computed ClosedLoopMetrics from simulation run.
        weights: Objective weighting parameters (default: 0.40/0.30/0.20/0.10).
        target_moisture: Target moisture setpoint (%).
        wilting_point: Permanent wilting point (%).
        field_capacity: Soil field capacity (%).
        reference_max_volume_l: Normalization ceiling for 24h water volume.

    Returns:
        ScenarioFitness containing decomposed normalized objectives and total scalar J.
    """
    if weights is None:
        weights = FitnessWeights()

    sm = df["soil_moisture"].to_numpy(dtype=float)
    cmd = df["irrigation_command"].to_numpy(dtype=float)

    if "applied_irrigation_l" in df.columns:
        vol_l = float(df["applied_irrigation_l"].sum())
    elif hasattr(metrics, "total_applied_volume_l"):
        vol_l = float(getattr(metrics, "total_applied_volume_l"))
    else:
        vol_l = float(metrics.total_irrigation_applied_mm * 100.0)

    # 1. E_tracking: Normalized RMSE relative to available range (FC - WP)
    available_range = max(1.0, field_capacity - wilting_point)
    e_tracking = float(metrics.rmse / available_range)
    e_tracking = min(2.0, e_tracking)

    # 2. E_water: Normalized volumetric consumption [0, 1]
    e_water = float(vol_l / max(1.0, reference_max_volume_l))
    e_water = min(2.0, e_water)

    # 3. E_deficit: Severe root stress penalty (time below target - 3.0%)
    critical_threshold = target_moisture - 3.0
    deficit_mask = sm < critical_threshold
    deficit_minutes = int(np.sum(deficit_mask))
    if deficit_minutes > 0:
        deficit_depths = critical_threshold - sm[deficit_mask]
        e_deficit = float(np.mean(deficit_depths) / available_range) * (deficit_minutes / len(sm))
    else:
        e_deficit = 0.0
    e_deficit = min(2.0, e_deficit)

    # 4. E_smoothness: High-frequency command jitter penalty
    if len(cmd) > 1:
        cmd_diffs = np.abs(np.diff(cmd))
        control_variation = float(np.mean(cmd_diffs))
        # Normalize: average step change of 10% command = 0.10
        e_smoothness = float(control_variation / 50.0)
    else:
        control_variation = 0.0
        e_smoothness = 0.0
    e_smoothness = min(2.0, e_smoothness)

    # Composite weighted objective J
    j_scenario = (
        weights.w_tracking * e_tracking
        + weights.w_water * e_water
        + weights.w_deficit * e_deficit
        + weights.w_smoothness * e_smoothness
    )

    return ScenarioFitness(
        scenario=metrics.scenario,
        total_fitness=float(j_scenario),
        e_tracking=e_tracking,
        e_water=e_water,
        e_deficit=e_deficit,
        e_smoothness=e_smoothness,
        mae_pct=float(metrics.mae),
        rmse_pct=float(metrics.rmse),
        water_volume_l=vol_l,
        deficit_minutes=deficit_minutes,
        control_variation=control_variation,
    )
