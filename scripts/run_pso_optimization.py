"""
Phase 14: PSO-Based Optimization of Fuzzy Controller Parameters.

Executes:
1. Baseline evaluation across all 6 scenarios (Training + Validation).
2. Offline Particle Swarm Optimization (PSO) on 4 training scenarios.
3. Post-optimization evaluation on Training, Validation, and All 6 scenarios.
4. Non-destructive parameter export to 'config/fuzzy_optimized_pso.json'.
5. Convergence telemetry export to 'data/processed/pso_convergence.csv'.
6. Full 24-hour closed-loop trajectory comparison across all 6 scenarios.
7. Generates 12 publication-grade figures at 300 DPI in 'reports/pso/figures/':
   - Fig 01: PSO Convergence Trajectory (Global Best & Mean Swarm Fitness)
   - Fig 02: Closed-Loop Soil Moisture Tracking — Normal Scenario
   - Fig 03: Closed-Loop Soil Moisture Tracking — Hot & Dry Scenario
   - Fig 04: Closed-Loop Soil Moisture Tracking — Rainy Scenario
   - Fig 05: Closed-Loop Soil Moisture Tracking — Cloudy Scenario
   - Fig 06: Closed-Loop Soil Moisture Tracking — Heatwave (Validation)
   - Fig 07: Closed-Loop Soil Moisture Tracking — Water Scarcity (Validation)
   - Fig 08: Volumetric Water Consumption Comparison (L) Across 6 Scenarios
   - Fig 09: Tracking Error Comparison (MAE & RMSE %) Across 6 Scenarios
   - Fig 10: Multi-Objective Fitness Decomposition Radar / Bar Comparison
   - Fig 11: Actuator Command Trajectory and Smoothness Comparison
   - Fig 12: Expert Baseline vs PSO-Optimized Fuzzy Membership Functions
"""

import sys
from pathlib import Path
import time
import json

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from config.schemas import SimulationScenario
from config.defaults import get_default_zones
from simulation.closed_loop import ClosedLoopConfig, ClosedLoopSimulator
from fuzzy_engine.irrigation import MainIrrigationFIS
from optimization import (
    FuzzyParameterSpace,
    FitnessWeights,
    ClosedLoopEvaluator,
    PSOConfig,
    PSOSolver,
    TRAINING_SCENARIOS,
    VALIDATION_SCENARIOS,
    ALL_SCENARIOS,
    save_optimized_parameters_json,
    save_convergence_csv,
    generate_comparison_table,
)

# Output directories
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
CONFIG_DIR = ROOT_DIR / "config"
FIGURES_DIR = ROOT_DIR / "reports" / "pso" / "figures"
REPORTS_DIR = ROOT_DIR / "reports" / "pso"

PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#CCCCCC"
plt.rcParams["axes.linewidth"] = 0.8


def plot_convergence(history: list, filepath: Path) -> None:
    """Fig 01: PSO Convergence Curve."""
    iters = [h["iteration"] for h in history]
    bests = [h["global_best_fitness"] for h in history]
    means = [h["mean_fitness"] for h in history]

    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    ax.plot(iters, means, color="#FF9800", linestyle="--", linewidth=2.0, label="Swarm Mean Fitness", alpha=0.85)
    ax.plot(iters, bests, color="#2196F3", linewidth=2.5, marker="o", markersize=5, label="Global Best Fitness $J^*$")
    ax.fill_between(iters, bests, means, color="#2196F3", alpha=0.10, label="Swarm Variance Band")

    ax.set_title("Particle Swarm Optimization Convergence Trajectory", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("PSO Iteration", fontsize=11, labelpad=8)
    ax.set_ylabel("Multi-Objective Composite Fitness $J$", fontsize=11, labelpad=8)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(frameon=True, facecolor="white", edgecolor="#DDD", fontsize=10, loc="upper right")

    # Annotate initial and final best
    ax.annotate(
        f"Initial Best: {bests[0]:.4f}",
        xy=(iters[0], bests[0]),
        xytext=(iters[0] + 1.5, bests[0] + 0.01),
        arrowprops=dict(facecolor="#555", arrowstyle="->", lw=1.0),
        fontsize=9,
        fontweight="semibold",
    )
    ax.annotate(
        f"Optimized Best: {bests[-1]:.4f}\n(Reduction: {(bests[0]-bests[-1])/bests[0]*100:.1f}%)",
        xy=(iters[-1], bests[-1]),
        xytext=(iters[-1] - 5.5, bests[-1] + 0.015),
        arrowprops=dict(facecolor="#2196F3", arrowstyle="->", lw=1.2),
        fontsize=9,
        fontweight="bold",
        color="#0D47A1",
    )

    plt.tight_layout()
    fig.savefig(filepath, dpi=300)
    plt.close(fig)
    print(f"  [Fig 01] Saved: {filepath.name}")


def plot_scenario_tracking(
    scenario: SimulationScenario,
    df_base: pd.DataFrame,
    df_opt: pd.DataFrame,
    target_moisture: float,
    filepath: Path,
    fig_num: str,
) -> None:
    """Figs 02-07: Moisture Tracking Trajectory Comparison."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True, dpi=300, gridspec_kw={"height_ratios": [2.5, 1.2]})

    t_hours = np.arange(len(df_base)) / 60.0

    # Top panel: Soil moisture
    ax1.plot(t_hours, df_base["soil_moisture"], color="#757575", linestyle="--", linewidth=1.8, label="Baseline Fuzzy (Unoptimized)")
    ax1.plot(t_hours, df_opt["soil_moisture"], color="#2E7D32", linewidth=2.2, label="PSO-Optimized Fuzzy")
    ax1.axhline(target_moisture, color="#D32F2F", linestyle=":", linewidth=1.8, label=f"Target Setpoint ({target_moisture:.1f}%)")
    ax1.axhline(target_moisture - 3.0, color="#FF9800", linestyle="--", linewidth=1.2, alpha=0.7, label="Depletion Limit (Target - 3%)")
    ax1.fill_between(t_hours, target_moisture - 1.0, target_moisture + 1.0, color="#4CAF50", alpha=0.12, label="Comfort Band (±1%)")

    sc_title = scenario.value.replace("_", " ").title()
    ax1.set_title(f"Zone 1 Soil Moisture Tracking: {sc_title} Scenario", fontsize=12, fontweight="bold", pad=10)
    ax1.set_ylabel("Soil Moisture (%)", fontsize=10, labelpad=8)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(frameon=True, facecolor="white", edgecolor="#DDD", fontsize=9, loc="upper right", ncol=2)

    # Bottom panel: Actuator commands
    ax2.plot(t_hours, df_base["irrigation_command"], color="#9E9E9E", linestyle="--", linewidth=1.2, label="Baseline Command")
    ax2.plot(t_hours, df_opt["irrigation_command"], color="#1565C0", linewidth=1.5, label="Optimized Command")
    ax2.set_title("Irrigation Actuator Command (%)", fontsize=10, fontweight="semibold", pad=6)
    ax2.set_xlabel("Time (Hours)", fontsize=10, labelpad=8)
    ax2.set_ylabel("Command (%)", fontsize=10, labelpad=8)
    ax2.set_ylim(-2, 105)
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(frameon=True, facecolor="white", edgecolor="#DDD", fontsize=8, loc="upper right", ncol=2)

    plt.tight_layout()
    fig.savefig(filepath, dpi=300)
    plt.close(fig)
    print(f"  [{fig_num}] Saved: {filepath.name}")


def plot_water_consumption(scenarios: list, vol_base: list, vol_opt: list, filepath: Path) -> None:
    """Fig 08: Volumetric Water Consumption Comparison."""
    x = np.arange(len(scenarios))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    rects1 = ax.bar(x - width / 2, vol_base, width, label="Baseline Fuzzy", color="#78909C", edgecolor="#455A64", alpha=0.9)
    rects2 = ax.bar(x + width / 2, vol_opt, width, label="PSO-Optimized Fuzzy", color="#2E7D32", edgecolor="#1B5E20", alpha=0.9)

    ax.set_title("24-Hour Total Water Consumption Across Scenarios (Liters)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Simulation Scenario", fontsize=11, labelpad=8)
    ax.set_ylabel("Applied Water Volume (L)", fontsize=11, labelpad=8)
    ax.set_xticks(x)
    ax.set_xticklabels([s.replace("_", "\n").title() for s in scenarios], fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.6, axis="y")
    ax.legend(frameon=True, facecolor="white", edgecolor="#DDD", fontsize=10)

    # Annotate savings percentage
    for i in range(len(scenarios)):
        diff_pct = (vol_opt[i] - vol_base[i]) / max(1.0, vol_base[i]) * 100.0
        y_pos = max(vol_base[i], vol_opt[i]) + 150
        sign = "+" if diff_pct > 0 else ""
        col = "#C62828" if diff_pct > 1.0 else ("#2E7D32" if diff_pct < -1.0 else "#555")
        ax.annotate(
            f"{sign}{diff_pct:.1f}%",
            xy=(x[i], y_pos),
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color=col,
        )

    ax.set_ylim(0, max(max(vol_base), max(vol_opt)) * 1.18)
    plt.tight_layout()
    fig.savefig(filepath, dpi=300)
    plt.close(fig)
    print(f"  [Fig 08] Saved: {filepath.name}")


def plot_tracking_errors(scenarios: list, mae_base: list, mae_opt: list, rmse_base: list, rmse_opt: list, filepath: Path) -> None:
    """Fig 09: Tracking Error Comparison."""
    x = np.arange(len(scenarios))
    width = 0.20

    fig, ax = plt.subplots(figsize=(11, 5), dpi=300)
    ax.bar(x - 1.5 * width, mae_base, width, label="Baseline MAE", color="#90CAF9", edgecolor="#1976D2")
    ax.bar(x - 0.5 * width, mae_opt, width, label="Optimized MAE", color="#1976D2", edgecolor="#0D47A1")
    ax.bar(x + 0.5 * width, rmse_base, width, label="Baseline RMSE", color="#FFCC80", edgecolor="#F57C00")
    ax.bar(x + 1.5 * width, rmse_opt, width, label="Optimized RMSE", color="#E65100", edgecolor="#BF360C")

    ax.set_title("Soil Moisture Tracking Errors Across Scenarios (% Moisture)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Simulation Scenario", fontsize=11, labelpad=8)
    ax.set_ylabel("Tracking Error (% Moisture)", fontsize=11, labelpad=8)
    ax.set_xticks(x)
    ax.set_xticklabels([s.replace("_", "\n").title() for s in scenarios], fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.6, axis="y")
    ax.legend(frameon=True, facecolor="white", edgecolor="#DDD", fontsize=9, ncol=2)

    plt.tight_layout()
    fig.savefig(filepath, dpi=300)
    plt.close(fig)
    print(f"  [Fig 09] Saved: {filepath.name}")


def plot_objective_breakdown(scenarios: list, res_base: dict, res_opt: dict, filepath: Path) -> None:
    """Fig 10: Multi-Objective Fitness Decomposition."""
    obj_labels = ["Tracking\n($E_e$)", "Water\n($E_w$)", "Deficit\n($E_d$)", "Smoothness\n($E_u$)"]
    
    # Compute mean across scenarios for baseline and opt
    base_e = [
        np.mean([res_base[s].e_tracking for s in scenarios]),
        np.mean([res_base[s].e_water for s in scenarios]),
        np.mean([res_base[s].e_deficit for s in scenarios]),
        np.mean([res_base[s].e_smoothness for s in scenarios]),
    ]
    opt_e = [
        np.mean([res_opt[s].e_tracking for s in scenarios]),
        np.mean([res_opt[s].e_water for s in scenarios]),
        np.mean([res_opt[s].e_deficit for s in scenarios]),
        np.mean([res_opt[s].e_smoothness for s in scenarios]),
    ]

    x = np.arange(len(obj_labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.bar(x - width / 2, base_e, width, label="Baseline Controller", color="#78909C", edgecolor="#37474F")
    ax.bar(x + width / 2, opt_e, width, label="PSO-Optimized Controller", color="#00897B", edgecolor="#004D40")

    ax.set_title("Normalized Multi-Objective Cost Component Comparison", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Normalized Objective Cost (Lower is Better)", fontsize=11, labelpad=8)
    ax.set_xticks(x)
    ax.set_xticklabels(obj_labels, fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.6, axis="y")
    ax.legend(frameon=True, facecolor="white", edgecolor="#DDD", fontsize=10)

    for i in range(len(obj_labels)):
        diff = (opt_e[i] - base_e[i]) / max(1e-5, base_e[i]) * 100
        sign = "+" if diff > 0 else ""
        y_max = max(base_e[i], opt_e[i])
        ax.annotate(f"{sign}{diff:.1f}%", xy=(x[i], y_max + 0.01), ha="center", fontsize=9, fontweight="bold", color="#004D40" if diff <= 0 else "#D32F2F")

    ax.set_ylim(0, max(max(base_e), max(opt_e)) * 1.25)
    plt.tight_layout()
    fig.savefig(filepath, dpi=300)
    plt.close(fig)
    print(f"  [Fig 10] Saved: {filepath.name}")


def plot_command_smoothness(df_base: pd.DataFrame, df_opt: pd.DataFrame, filepath: Path) -> None:
    """Fig 11: Command Smoothness and Actuator Chatter Comparison."""
    cmd_base = df_base["irrigation_command"].values
    cmd_opt = df_opt["irrigation_command"].values

    diff_base = np.abs(np.diff(cmd_base))
    diff_opt = np.abs(np.diff(cmd_opt))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), dpi=300)

    # Left: Command step difference histogram
    bins = np.linspace(0, 15, 31)
    ax1.hist(diff_base, bins=bins, alpha=0.6, color="#757575", label=f"Baseline (Mean: {np.mean(diff_base):.2f}%)", density=True)
    ax1.hist(diff_opt, bins=bins, alpha=0.7, color="#1E88E5", label=f"Optimized (Mean: {np.mean(diff_opt):.2f}%)", density=True)
    ax1.set_title("Distribution of Actuator Step Variations (|Δu|)", fontsize=11, fontweight="bold", pad=10)
    ax1.set_xlabel("Step Change Magnitude |u(t) - u(t-1)| (%)", fontsize=10)
    ax1.set_ylabel("Probability Density", fontsize=10)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(frameon=True, facecolor="white", edgecolor="#DDD", fontsize=9)

    # Right: Cumulative variance
    ax2.plot(np.cumsum(diff_base), color="#757575", linestyle="--", linewidth=1.8, label="Baseline Cumulative Variation")
    ax2.plot(np.cumsum(diff_opt), color="#1E88E5", linewidth=2.2, label="Optimized Cumulative Variation")
    ax2.set_title("Cumulative Actuator Variation (Total Chatter)", fontsize=11, fontweight="bold", pad=10)
    ax2.set_xlabel("Simulation Timestep (Minutes)", fontsize=10)
    ax2.set_ylabel("Cumulative |Δu| (%)", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(frameon=True, facecolor="white", edgecolor="#DDD", fontsize=9)

    plt.tight_layout()
    fig.savefig(filepath, dpi=300)
    plt.close(fig)
    print(f"  [Fig 11] Saved: {filepath.name}")


def plot_membership_functions_comparison(
    param_space: FuzzyParameterSpace,
    opt_theta: np.ndarray,
    filepath: Path,
) -> None:
    """Fig 12: Expert Baseline vs PSO-Optimized Membership Functions."""
    fis_base = param_space.build_fis(param_space.baseline_values)
    fis_opt = param_space.build_fis(opt_theta)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), dpi=300)
    variables = [
        ("moisture_error", "Moisture Error $e$ [%]", axes[0, 0]),
        ("soil_stress", "Soil Stress Index [0, 100]", axes[0, 1]),
        ("water_demand", "Water Demand Index [0, 100]", axes[1, 0]),
        ("irrigation_command", "Irrigation Command $u$ [%]", axes[1, 1]),
    ]

    colors = ["#1976D2", "#388E3C", "#F57C00", "#D32F2F", "#7B1FA2"]

    for var_name, label_str, ax in variables:
        var_base = getattr(fis_base, f"{var_name}_var" if hasattr(fis_base, f"{var_name}_var") else "command_var")
        var_opt = getattr(fis_opt, f"{var_name}_var" if hasattr(fis_opt, f"{var_name}_var") else "command_var")

        x_grid = np.linspace(var_base.universe.min_val, var_base.universe.max_val, 401)

        set_names = list(var_base.sets.keys())
        for idx, sname in enumerate(set_names):
            c = colors[idx % len(colors)]
            mf_base = var_base.sets[sname].evaluate(x_grid)
            mf_opt = var_opt.sets[sname].evaluate(x_grid)

            # Plot baseline dashed, opt solid
            ax.plot(x_grid, mf_base, color=c, linestyle="--", linewidth=1.2, alpha=0.5)
            ax.plot(x_grid, mf_opt, color=c, linewidth=2.0, label=f"{sname}")

        ax.set_title(f"Variable: {var_name.replace('_', ' ').title()}", fontsize=11, fontweight="bold", pad=8)
        ax.set_xlabel(label_str, fontsize=10)
        ax.set_ylabel("Membership Degree μ", fontsize=10)
        ax.set_ylim(-0.05, 1.15)
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(frameon=True, facecolor="white", edgecolor="#DDD", fontsize=8, loc="upper right")

    # Overall legend explanation
    fig.suptitle("Expert Baseline (Dashed) vs PSO-Optimized (Solid) Membership Functions", fontsize=13, fontweight="bold", y=0.99)
    plt.tight_layout()
    fig.savefig(filepath, dpi=300)
    plt.close(fig)
    print(f"  [Fig 12] Saved: {filepath.name}")


def main() -> None:
    t_start_total = time.time()
    print("=" * 70)
    print("PHASE 14: PSO METAHEURISTIC TUNING OF FUZZY CONTROLLER PARAMETERS")
    print("=" * 70)

    # 1. Initialize Parameter Space & Fast Evaluator
    param_space = FuzzyParameterSpace()
    weights = FitnessWeights(w_tracking=0.40, w_water=0.30, w_deficit=0.20, w_smoothness=0.10)
    evaluator = ClosedLoopEvaluator(param_space=param_space, weights=weights, seed=42)

    # 2. Baseline Evaluation
    print("\n--- STEP 1: EVALUATING BASELINE (EXPERT) FUZZY CONTROLLER ---")
    base_train = evaluator.evaluate_baseline(scenarios=TRAINING_SCENARIOS)
    base_val = evaluator.evaluate_baseline(scenarios=VALIDATION_SCENARIOS)
    base_all = evaluator.evaluate_baseline(scenarios=ALL_SCENARIOS)

    print(f"  Baseline Training Fitness   : J = {base_train.composite_fitness:.5f}")
    print(f"  Baseline Validation Fitness : J = {base_val.composite_fitness:.5f}")
    print(f"  Baseline Overall Fitness    : J = {base_all.composite_fitness:.5f}")

    # 3. Configure and Run PSO
    print("\n--- STEP 2: LAUNCHING OFFLINE PARTICLE SWARM OPTIMIZATION ---")
    pso_config = PSOConfig(
        swarm_size=16,
        max_iterations=20,
        inertia_weight=0.729,
        cognitive_coeff=1.494,
        social_coeff=1.494,
        seed=42,
        verbose=True,
    )
    solver = PSOSolver(evaluator=evaluator, config=pso_config)
    gbest_theta, gbest_fit, history = solver.optimize()

    print("\n--- STEP 3: EVALUATING PSO-OPTIMIZED CONTROLLER ---")
    opt_train = evaluator.evaluate_vector(gbest_theta, scenarios=TRAINING_SCENARIOS)
    opt_val = evaluator.evaluate_vector(gbest_theta, scenarios=VALIDATION_SCENARIOS)
    opt_all = evaluator.evaluate_vector(gbest_theta, scenarios=ALL_SCENARIOS)

    print(f"  Optimized Training Fitness   : J = {opt_train.composite_fitness:.5f} (Δ = {(opt_train.composite_fitness - base_train.composite_fitness)/base_train.composite_fitness*100:+.2f}%)")
    print(f"  Optimized Validation Fitness : J = {opt_val.composite_fitness:.5f} (Δ = {(opt_val.composite_fitness - base_val.composite_fitness)/base_val.composite_fitness*100:+.2f}%)")
    print(f"  Optimized Overall Fitness    : J = {opt_all.composite_fitness:.5f} (Δ = {(opt_all.composite_fitness - base_all.composite_fitness)/base_all.composite_fitness*100:+.2f}%)")

    # 4. Save JSON and CSV Artefacts
    print("\n--- STEP 4: PERSISTING OPTIMIZED PARAMETERS AND TELEMETRY ---")
    opt_theta_dict = {name: float(val) for name, val in zip(param_space.names, gbest_theta)}
    json_path = CONFIG_DIR / "fuzzy_optimized_pso.json"
    save_optimized_parameters_json(
        param_space=param_space,
        pso_config=pso_config,
        weights_dict=weights.model_dump(),
        optimized_theta=opt_theta_dict,
        baseline_train_fitness=base_train.composite_fitness,
        optimized_train_fitness=opt_train.composite_fitness,
        baseline_val_fitness=base_val.composite_fitness,
        optimized_val_fitness=opt_val.composite_fitness,
        baseline_all_fitness=base_all.composite_fitness,
        optimized_all_fitness=opt_all.composite_fitness,
        filepath=json_path,
    )
    print(f"  Saved parameters to: {json_path}")

    csv_path = PROCESSED_DATA_DIR / "pso_convergence.csv"
    save_convergence_csv(history, filepath=csv_path)
    print(f"  Saved telemetry to: {csv_path}")

    # 5. Generate High-Resolution Trajectories & Figures
    print("\n--- STEP 5: GENERATING 12 PUBLICATION-GRADE FIGURES ---")
    plot_convergence(history, FIGURES_DIR / "fig01_pso_convergence_curve.png")

    # Full simulation trajectories for figures
    fis_base = param_space.build_fis(param_space.baseline_values)
    fis_opt = param_space.build_fis(gbest_theta)
    zone_cfg = get_default_zones()[0]

    sc_names = [s.value for s in ALL_SCENARIOS]
    vol_base, vol_opt = [], []
    mae_base, mae_opt = [], []
    rmse_base, rmse_opt = [], []

    fig_map = {
        SimulationScenario.NORMAL: ("fig02_moisture_tracking_normal.png", "Fig 02"),
        SimulationScenario.HOT_AND_DRY: ("fig03_moisture_tracking_hot_dry.png", "Fig 03"),
        SimulationScenario.RAINY: ("fig04_moisture_tracking_rainy.png", "Fig 04"),
        SimulationScenario.CLOUDY: ("fig05_moisture_tracking_cloudy.png", "Fig 05"),
        SimulationScenario.HEATWAVE: ("fig06_moisture_tracking_heatwave.png", "Fig 06"),
        SimulationScenario.WATER_SCARCITY: ("fig07_moisture_tracking_water_scarcity.png", "Fig 07"),
    }

    df_base_normal = None
    df_opt_normal = None

    for sc in ALL_SCENARIOS:
        w_df, et0_df = evaluator._scenario_cache[sc]
        sim_base = ClosedLoopSimulator(
            config=ClosedLoopConfig(scenario=sc, zone_id=zone_cfg.zone_id, seed=42),
            zone_config=zone_cfg,
            fis_main=fis_base,
        )
        sim_opt = ClosedLoopSimulator(
            config=ClosedLoopConfig(scenario=sc, zone_id=zone_cfg.zone_id, seed=42),
            zone_config=zone_cfg,
            fis_main=fis_opt,
        )
        df_b, met_b = sim_base.run(mode="fuzzy", weather_df=w_df, et0_df=et0_df)
        df_o, met_o = sim_opt.run(mode="fuzzy", weather_df=w_df, et0_df=et0_df)

        if sc == SimulationScenario.NORMAL:
            df_base_normal = df_b
            df_opt_normal = df_o

        fn, fnum = fig_map[sc]
        plot_scenario_tracking(
            scenario=sc,
            df_base=df_b,
            df_opt=df_o,
            target_moisture=zone_cfg.target_moisture,
            filepath=FIGURES_DIR / fn,
            fig_num=fnum,
        )

        vol_base.append(float(df_b["applied_irrigation_l"].sum()))
        vol_opt.append(float(df_o["applied_irrigation_l"].sum()))
        mae_base.append(float(met_b.mae))
        mae_opt.append(float(met_o.mae))
        rmse_base.append(float(met_b.rmse))
        rmse_opt.append(float(met_o.rmse))

    plot_water_consumption(sc_names, vol_base, vol_opt, FIGURES_DIR / "fig08_volumetric_water_comparison.png")
    plot_tracking_errors(sc_names, mae_base, mae_opt, rmse_base, rmse_opt, FIGURES_DIR / "fig09_tracking_mae_rmse_comparison.png")
    plot_objective_breakdown(sc_names, base_all.scenario_fitness, opt_all.scenario_fitness, FIGURES_DIR / "fig10_fitness_objective_radar_decomposition.png")
    plot_command_smoothness(df_base_normal, df_opt_normal, FIGURES_DIR / "fig11_command_smoothness_and_jitter.png")
    plot_membership_functions_comparison(param_space, gbest_theta, FIGURES_DIR / "fig12_membership_functions_before_after.png")

    # 6. Print Comparison Table
    table_md = generate_comparison_table(param_space, opt_theta_dict)
    print("\n--- STEP 6: PARAMETER COMPARISON TABLE ---")
    print(table_md)

    elapsed_total = time.time() - t_start_total
    print("\n" + "=" * 70)
    print(f"PHASE 14 PSO COMPLETE IN {elapsed_total / 60:.1f} MINUTES ({elapsed_total:.1f}s)")
    print("=" * 70)


if __name__ == "__main__":
    main()
