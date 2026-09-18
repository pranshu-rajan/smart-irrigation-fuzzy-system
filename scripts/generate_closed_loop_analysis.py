"""Phase 11: Single-Zone Closed-Loop Analysis and Visualizations.

Executes the dynamic single-zone closed-loop feedback simulation across all 6 scenarios,
compiles `data/processed/closed_loop_single_zone.csv` (8,640 records), runs Baseline A
(No irrigation) and Baseline B (Fixed irrigation), calculates all agronomic and control
performance metrics, and produces publication-quality figures at 300 DPI.
"""

import os
import sys
from pathlib import Path
import time
from typing import Dict, List, Tuple

# Output directory configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config.schemas import SimulationScenario
from simulation.closed_loop import (
    ClosedLoopConfig,
    ClosedLoopMetrics,
    ClosedLoopSimulator,
    simulate_single_zone,
)

# Output directory configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports" / "closed_loop"
FIGURES_DIR = REPORTS_DIR / "figures"

DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Visual styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8

SCENARIO_COLORS = {
    SimulationScenario.NORMAL.value: "#1f77b4",        # Blue
    SimulationScenario.HOT_AND_DRY.value: "#ff7f0e",    # Orange
    SimulationScenario.RAINY.value: "#2ca02c",         # Green
    SimulationScenario.CLOUDY.value: "#7f7f7f",        # Gray
    SimulationScenario.HEATWAVE.value: "#d62728",      # Red
    SimulationScenario.WATER_SCARCITY.value: "#9467bd", # Purple
}


def run_all_scenarios() -> Tuple[pd.DataFrame, Dict[str, ClosedLoopMetrics]]:
    """Execute 24-hour simulation across all 6 environmental scenarios.

    Returns:
        Tuple[pd.DataFrame, Dict[str, ClosedLoopMetrics]]:
            - Consolidated DataFrame of 8,640 rows.
            - Dictionary mapping scenario name to ClosedLoopMetrics.
    """
    print("=" * 70)
    print("EXECUTING PHASE 11 SINGLE-ZONE CLOSED-LOOP SIMULATION ACROSS 6 SCENARIOS")
    print("=" * 70)

    scenarios = list(SimulationScenario)
    all_dfs: List[pd.DataFrame] = []
    scenario_metrics: Dict[str, ClosedLoopMetrics] = {}

    t0_all = time.perf_counter()

    for sc in scenarios:
        t0 = time.perf_counter()
        cfg = ClosedLoopConfig(scenario=sc, seed=42)
        sim = ClosedLoopSimulator(config=cfg)
        df_sc, metrics_sc = sim.run(mode="fuzzy")
        t_elap = time.perf_counter() - t0

        all_dfs.append(df_sc)
        scenario_metrics[sc.value] = metrics_sc

        print(f"[{sc.value:14s}] Elapsed: {t_elap:.2f}s | "
              f"Final SM: {metrics_sc.final_soil_moisture:5.2f}% | "
              f"MAE: {metrics_sc.mae:4.2f}% | "
              f"Irrig: {metrics_sc.total_irrigation_applied_mm:5.2f} mm | "
              f"In-Band: {metrics_sc.percentage_in_target_band:5.1f}%")

    t_total = time.perf_counter() - t0_all
    print(f"\nTotal 6-Scenario Runtime: {t_total:.2f}s ({t_total/6:.2f}s per 1440-step run)")

    master_df = pd.concat(all_dfs, ignore_index=True)
    csv_path = DATA_PROCESSED_DIR / "closed_loop_single_zone.csv"
    master_df.to_csv(csv_path, index=False)
    print(f"\nSaved consolidated dataset: {csv_path} ({len(master_df)} rows, {len(master_df.columns)} columns)")

    return master_df, scenario_metrics


def run_canonical_baselines() -> Tuple[pd.DataFrame, ClosedLoopMetrics, pd.DataFrame, ClosedLoopMetrics, pd.DataFrame, ClosedLoopMetrics]:
    """Run Baseline A (None), Baseline B (Fixed), and Control (Fuzzy) on Normal scenario."""
    cfg = ClosedLoopConfig(scenario=SimulationScenario.NORMAL, seed=42)
    sim = ClosedLoopSimulator(config=cfg)

    df_fuzzy, m_fuzzy = sim.run(mode="fuzzy")
    df_none, m_none = sim.run(mode="none")
    df_fixed, m_fixed = sim.run(mode="fixed")

    return df_fuzzy, m_fuzzy, df_none, m_none, df_fixed, m_fixed


def generate_master_response_plot(df_fuzzy: pd.DataFrame, metrics_fuzzy: ClosedLoopMetrics) -> None:
    """Generate Figure 1: Master Closed-Loop Feedback Timeline (Soil Moisture, Target, Command)."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), dpi=300, sharex=True,
                                   gridspec_kw={"height_ratios": [2.2, 1.2]})

    hours = df_fuzzy["step"] / 60.0

    # Top panel: Soil Moisture vs Target Band
    ax1.plot(hours, df_fuzzy["soil_moisture"], color="#1f77b4", lw=2.2, label="Soil Moisture $SM(t)$")
    ax1.axhline(60.0, color="#d62728", lw=1.8, ls="--", label="Target Setpoint ($60.0\\%$)")
    ax1.axhline(55.0, color="#7f7f7f", lw=1.0, ls=":", label="Initial State ($55.0\\%$)")
    ax1.fill_between(hours, 58.0, 62.0, color="#2ca02c", alpha=0.15, label="Target Band ($60.0 \\pm 2.0\\%$)")

    ax1.set_ylabel("Soil Moisture Content (% vol)", fontsize=11, fontweight="bold")
    ax1.set_ylim(53.5, 63.5)
    ax1.set_title("Single-Zone Dynamic Closed-Loop Feedback Control Response (Zone 1: Tomato / Loam)\n"
                  f"Normal Scenario | Initial SM = 55.0% | Final SM = {metrics_fuzzy.final_soil_moisture:.2f}% | MAE = {metrics_fuzzy.mae:.2f}%",
                  fontsize=12, fontweight="bold", pad=12)
    ax1.legend(loc="lower right", framealpha=0.9, fontsize=10)
    ax1.grid(True, alpha=0.3)

    # Bottom panel: Controller Irrigation Command
    ax2.plot(hours, df_fuzzy["irrigation_command"], color="#2ca02c", lw=1.8, label="Irrigation Command (%)")
    ax2.fill_between(hours, 0, df_fuzzy["irrigation_command"], color="#2ca02c", alpha=0.25)
    ax2.set_xlabel("Simulation Timeline (Hours)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Command (%)", fontsize=11, fontweight="bold")
    ax2.set_xlim(0, 24)
    ax2.set_ylim(-2, 102)
    ax2.legend(loc="upper right", framealpha=0.9, fontsize=10)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = FIGURES_DIR / "closed_loop_response_master.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved Figure: {out_path.name}")


def generate_baseline_comparison_plots(
    df_fuzzy: pd.DataFrame,
    m_fuzzy: ClosedLoopMetrics,
    df_none: pd.DataFrame,
    m_none: ClosedLoopMetrics,
    df_fixed: pd.DataFrame,
    m_fixed: ClosedLoopMetrics,
) -> None:
    """Generate Baseline comparison figures (Fuzzy vs No-Irrigation vs Fixed-Irrigation)."""
    hours = df_fuzzy["step"] / 60.0

    # 1. Trajectory comparison plot
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    ax.plot(hours, df_none["soil_moisture"], color="#7f7f7f", ls="--", lw=1.8,
            label=f"Baseline A: No Irrigation (Final SM = {m_none.final_soil_moisture:.2f}%, MAE = {m_none.mae:.2f}%)")
    ax.plot(hours, df_fixed["soil_moisture"], color="#ff7f0e", ls="-.", lw=1.8,
            label=f"Baseline B: Fixed Irrigation 1.5 mm/h (Final SM = {m_fixed.final_soil_moisture:.2f}%, MAE = {m_fixed.mae:.2f}%)")
    ax.plot(hours, df_fuzzy["soil_moisture"], color="#1f77b4", lw=2.4,
            label=f"Control: Fuzzy Closed-Loop (Final SM = {m_fuzzy.final_soil_moisture:.2f}%, MAE = {m_fuzzy.mae:.2f}%)")

    ax.axhline(60.0, color="#d62728", ls=":", lw=1.5, label="Target Setpoint ($60.0\\%$)")
    ax.fill_between(hours, 58.0, 62.0, color="#2ca02c", alpha=0.12, label="Target Tolerance Band ($\\pm 2.0\\%$)")

    ax.set_title("Controller vs. Baseline Hydraulic Performance Comparison (Normal Scenario)\n"
                 "Zone 1: Tomato / Loam Root-Zone (24-Hour Horizon)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Time (Hours)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Soil Moisture Content (% vol)", fontsize=11, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.legend(loc="lower right", framealpha=0.9, fontsize=9.5)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = FIGURES_DIR / "closed_loop_baseline_comparison.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved Figure: {out_path.name}")

    # 2. Individual comparison: Controller vs No Irrigation
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.plot(hours, df_none["soil_moisture"], color="#d62728", ls="--", lw=2.0, label="Baseline A (No Irrigation)")
    ax.plot(hours, df_fuzzy["soil_moisture"], color="#1f77b4", lw=2.2, label="Fuzzy Closed-Loop Controller")
    ax.axhline(60.0, color="#2ca02c", ls=":", lw=1.5, label="Target (60.0%)")
    ax.fill_between(hours, 58.0, 62.0, color="#2ca02c", alpha=0.12)
    ax.set_title("Controller vs. No-Irrigation Baseline: Deficit Depletion vs Regulated Replenishment",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Soil Moisture (% vol)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "closed_loop_vs_no_irrigation.png", dpi=300)
    plt.close()

    # 3. Individual comparison: Controller vs Fixed Irrigation
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.plot(hours, df_fixed["soil_moisture"], color="#ff7f0e", ls="-.", lw=2.0, label="Baseline B (Fixed 1.5 mm/h)")
    ax.plot(hours, df_fuzzy["soil_moisture"], color="#1f77b4", lw=2.2, label="Fuzzy Closed-Loop Controller")
    ax.axhline(60.0, color="#2ca02c", ls=":", lw=1.5, label="Target (60.0%)")
    ax.fill_between(hours, 58.0, 62.0, color="#2ca02c", alpha=0.12)
    ax.set_title("Controller vs. Fixed-Irrigation Baseline: Dynamic Damping vs Open-Loop Overshoot",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Soil Moisture (% vol)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "closed_loop_vs_fixed_irrigation.png", dpi=300)
    plt.close()


def generate_scenario_comparison_plots(master_df: pd.DataFrame) -> None:
    """Generate comparative trajectory curves across all 6 environmental scenarios."""
    scenarios = list(SimulationScenario)

    # 1. Soil Moisture across scenarios
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    for sc in scenarios:
        sc_data = master_df[master_df["scenario"] == sc.value]
        hours = sc_data["step"] / 60.0
        ax.plot(hours, sc_data["soil_moisture"], color=SCENARIO_COLORS[sc.value],
                lw=1.8, label=sc.value)

    ax.axhline(60.0, color="#000000", ls="--", lw=1.2, label="Target Setpoint ($60.0\\%$)")
    ax.fill_between([0, 24], 58.0, 62.0, color="#2ca02c", alpha=0.12, label="Target Band ($\\pm 2.0\\%$)")

    ax.set_title("Single-Zone Closed-Loop Soil Moisture Trajectories across 6 Environmental Scenarios",
                 fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Timeline (Hours)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Soil Moisture (% vol)", fontsize=11, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.legend(loc="lower right", framealpha=0.9, fontsize=9.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "closed_loop_scenarios_comparison.png", dpi=300)
    plt.close()

    # 2. Irrigation Command across scenarios
    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)
    for sc in scenarios:
        sc_data = master_df[master_df["scenario"] == sc.value]
        hours = sc_data["step"] / 60.0
        ax.plot(hours, sc_data["irrigation_command"], color=SCENARIO_COLORS[sc.value],
                lw=1.6, label=sc.value)

    ax.set_title("Controller Irrigation Command Modulation across 6 Environmental Scenarios",
                 fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Timeline (Hours)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Irrigation Command (%)", fontsize=11, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.set_ylim(-2, 102)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "closed_loop_scenarios_commands.png", dpi=300)
    plt.close()


def generate_diurnal_state_flux_plots(df_norm: pd.DataFrame) -> None:
    """Generate individual diagnostic state and flux curves for the canonical Normal scenario."""
    hours = df_norm["step"] / 60.0

    # 1. Soil Moisture vs Target Band
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax.plot(hours, df_norm["soil_moisture"], color="#1f77b4", lw=2.2, label="Soil Moisture $SM(t)$")
    ax.axhline(60.0, color="#d62728", ls="--", lw=1.5, label="Target (60.0%)")
    ax.fill_between(hours, 58.0, 62.0, color="#2ca02c", alpha=0.15, label="Target Band ($\\pm 2\\%$)")
    ax.set_title("Single-Zone Dynamic Soil Moisture Response vs Target Band (Normal Scenario)",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Soil Moisture (% vol)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "closed_loop_soil_moisture_vs_target.png", dpi=300)
    plt.close()

    # 1b. Irrigation Command vs Time
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax.plot(hours, df_norm["irrigation_command"], color="#2ca02c", lw=1.8, label="Irrigation Command (%)")
    ax.fill_between(hours, 0, df_norm["irrigation_command"], color="#2ca02c", alpha=0.25)
    ax.set_title("Normalized Irrigation Command vs Time (Normal Scenario)",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Command (%)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.set_ylim(-2, 102)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "closed_loop_irrigation_command.png", dpi=300)
    plt.close()

    # 1c. Moisture Error vs Time
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax.plot(hours, df_norm["moisture_error"], color="#d62728", lw=2.0)
    ax.axhline(0.0, color="#000000", ls="--", lw=1.0)
    ax.fill_between(hours, -2.0, 2.0, color="#2ca02c", alpha=0.15, label="Tolerance Band ($\\pm 2\\%$)")
    ax.set_title("Closed-Loop Soil Moisture Tracking Error $e(t) = SM_{\\text{target}} - SM(t)$",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Moisture Error (%)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "closed_loop_moisture_error.png", dpi=300)
    plt.close()

    # 2. Individual Subsystems (Soil Stress, Weather Stress, Water Demand)
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax.plot(hours, df_norm["soil_stress"], color="#8c564b", lw=2.0)
    ax.set_title("Soil Stress FIS Output vs Time (Normal Scenario)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Soil Stress (%)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.set_ylim(-2, 102)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "closed_loop_soil_stress.png", dpi=300)
    plt.close()

    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax.plot(hours, df_norm["weather_stress"], color="#e377c2", lw=2.0)
    ax.set_title("Weather Stress FIS Output vs Time (Normal Scenario)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Weather Stress (%)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.set_ylim(-2, 102)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "closed_loop_weather_stress.png", dpi=300)
    plt.close()

    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax.plot(hours, df_norm["water_demand"], color="#17becf", lw=2.0)
    ax.set_title("Water Demand FIS Output vs Time (Normal Scenario)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Water Demand (%)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.set_ylim(-2, 102)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "closed_loop_water_demand.png", dpi=300)
    plt.close()

    # 2. Irrigation Application vs Time
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax.plot(hours, df_norm["irrigation_application"], color="#1f77b4", lw=1.8)
    ax.fill_between(hours, 0, df_norm["irrigation_application"], color="#1f77b4", alpha=0.25)
    ax.set_title("Physical Actuator Water Delivery $I_{\\text{app}}(t)$ (mm / step)",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Applied Water Depth (mm)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "closed_loop_irrigation_application.png", dpi=300)
    plt.close()

    # 3. Subsystem Stresses vs Time (Soil Stress, Weather Stress, Water Demand)
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.plot(hours, df_norm["soil_stress"], color="#8c564b", lw=1.8, label="Soil Stress FIS")
    ax.plot(hours, df_norm["weather_stress"], color="#e377c2", lw=1.8, label="Weather Stress FIS")
    ax.plot(hours, df_norm["water_demand"], color="#17becf", lw=1.8, label="Water Demand FIS")
    ax.set_title("Hierarchical Fuzzy Subsystem Indices Feeding Main Irrigation FIS",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Fuzzy Stress / Demand Index (%)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.set_ylim(-2, 102)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "closed_loop_fuzzy_subsystems.png", dpi=300)
    plt.close()

    # 4. ETc vs Rainfall
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax.plot(hours, df_norm["etc"], color="#ff7f0e", lw=1.8, label="Crop ETc (mm/step)")
    ax.plot(hours, df_norm["rainfall"], color="#2ca02c", lw=1.5, ls="--", label="Rainfall (mm/step)")
    ax.plot(hours, df_norm["effective_rainfall"], color="#1f77b4", lw=1.5, ls=":", label="Effective Rainfall (mm/step)")
    ax.set_title("Diurnal Crop Evapotranspiration vs Atmospheric Precipitation",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Water Depth (mm / step)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "closed_loop_etc_vs_rainfall.png", dpi=300)
    plt.close()

    # 5. Cumulative Fluxes (Irrigation, ETc, Actual ET, Drainage)
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    cum_irrig = np.cumsum(df_norm["irrigation_application"])
    cum_etc = np.cumsum(df_norm["etc"])
    cum_aet = np.cumsum(df_norm["actual_et"])
    cum_rain = np.cumsum(df_norm["rainfall"])
    cum_drain = np.cumsum(df_norm["drainage"])

    ax.plot(hours, cum_irrig, color="#1f77b4", lw=2.2, label=f"Cumulative Irrigation ({cum_irrig.iloc[-1]:.2f} mm)")
    ax.plot(hours, cum_etc, color="#ff7f0e", lw=1.8, label=f"Cumulative ETc ({cum_etc.iloc[-1]:.2f} mm)")
    ax.plot(hours, cum_aet, color="#2ca02c", lw=1.8, ls="--", label=f"Cumulative Actual ET ({cum_aet.iloc[-1]:.2f} mm)")
    if cum_rain.iloc[-1] > 0.01:
        ax.plot(hours, cum_rain, color="#9467bd", lw=1.8, label=f"Cumulative Rainfall ({cum_rain.iloc[-1]:.2f} mm)")
    ax.plot(hours, cum_drain, color="#d62728", lw=1.5, ls=":", label=f"Cumulative Drainage ({cum_drain.iloc[-1]:.2f} mm)")

    ax.set_title("Cumulative Root-Zone Hydrological Water Balance Fluxes (Normal Scenario)",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Cumulative Water Depth (mm)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "closed_loop_cumulative_fluxes.png", dpi=300)
    plt.close()


def main() -> None:
    """Execute complete Phase 11 analysis, dataset generation, and figure plotting."""
    # 1. Run full 6-scenario suite and generate CSV
    master_df, scenario_metrics = run_all_scenarios()

    # 2. Run Baselines on canonical Normal scenario
    df_fuzzy, m_fuzzy, df_none, m_none, df_fixed, m_fixed = run_canonical_baselines()

    # 3. Generate Master Section 27 Plot
    generate_master_response_plot(df_fuzzy, m_fuzzy)

    # 4. Generate Baseline Comparisons
    generate_baseline_comparison_plots(df_fuzzy, m_fuzzy, df_none, m_none, df_fixed, m_fixed)

    # 5. Generate Multi-Scenario Comparisons
    generate_scenario_comparison_plots(master_df)

    # 6. Generate Diagnostic State/Flux Plots
    generate_diurnal_state_flux_plots(df_fuzzy)

    print("\n" + "=" * 70)
    print("PHASE 11 CLOSED-LOOP ANALYSIS AND FIGURE GENERATION COMPLETE")
    print(f"Generated figures located in: {FIGURES_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
