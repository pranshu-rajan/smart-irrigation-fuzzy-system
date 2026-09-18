"""Phase 12: Multizone Closed-Loop Feedback Control Analysis and Visualizations.

Executes the dynamic 3-zone closed-loop feedback simulation across all 6 scenarios,
compiles `data/processed/multizone_closed_loop.csv` (25,920 records), runs Baselines
A (No irrigation) and B (Fixed irrigation at 1.5 mm/h), calculates per-zone and system-level
metrics, and generates 18 publication-quality figures at 300 DPI in `reports/multizone_closed_loop/figures/`.
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
from simulation.multizone_closed_loop import (
    MultizoneClosedLoopConfig,
    ZoneClosedLoopMetrics,
    SystemClosedLoopMetrics,
    MultizoneSimulationResult,
    MultizoneClosedLoopSimulator,
    simulate_multizone_closed_loop,
)

DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports" / "multizone_closed_loop"
FIGURES_DIR = REPORTS_DIR / "figures"

DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Visual styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8

ZONE_COLORS = {
    1: "#1f77b4",  # Zone 1: Tomato / Loam (Blue)
    2: "#ff7f0e",  # Zone 2: Wheat / Sandy (Orange)
    3: "#2ca02c",  # Zone 3: Maize / Clay (Green)
}

ZONE_LABELS = {
    1: "Zone 1: Tomato / Loam (100 m², Target 60%)",
    2: "Zone 2: Wheat / Sandy (120 m², Target 55%)",
    3: "Zone 3: Maize / Clay (80 m², Target 65%)",
}


def run_all_multizone_scenarios() -> Tuple[pd.DataFrame, Dict[str, MultizoneSimulationResult]]:
    """Execute 24-hour 3-zone simulation across all 6 environmental scenarios.

    Returns:
        Tuple[pd.DataFrame, Dict[str, MultizoneSimulationResult]]:
            - Consolidated DataFrame of 25,920 records (6 scenarios * 3 zones * 1440 steps).
            - Dictionary mapping scenario name to MultizoneSimulationResult.
    """
    print("=" * 75)
    print("EXECUTING PHASE 12 MULTIZONE CLOSED-LOOP SIMULATION ACROSS 6 SCENARIOS")
    print("=" * 75)

    scenarios = list(SimulationScenario)
    all_dfs: List[pd.DataFrame] = []
    scenario_results: Dict[str, MultizoneSimulationResult] = {}

    t0_all = time.perf_counter()

    for sc in scenarios:
        t0 = time.perf_counter()
        cfg = MultizoneClosedLoopConfig(scenario=sc, seed=42)
        sim = MultizoneClosedLoopSimulator(config=cfg)
        res = sim.run(mode="fuzzy")
        t_elap = time.perf_counter() - t0

        all_dfs.append(res.df)
        scenario_results[sc.value] = res

        print(f"[{sc.value:14s}] Runtime: {t_elap:5.2f}s | "
              f"Z1 SM: {res.zone_metrics[1].final_soil_moisture:5.2f}% | "
              f"Z2 SM: {res.zone_metrics[2].final_soil_moisture:5.2f}% | "
              f"Z3 SM: {res.zone_metrics[3].final_soil_moisture:5.2f}% | "
              f"Total Vol: {res.system_metrics.total_system_irrigation_volume_l:7.1f} L | "
              f"In-Band: {res.system_metrics.overall_target_band_occupancy_pct:5.1f}%")

    t_total = time.perf_counter() - t0_all
    print(f"\nTotal 6-Scenario Runtime: {t_total:.2f}s ({t_total/6:.2f}s per 4,320-record scenario run)")

    master_df = pd.concat(all_dfs, ignore_index=True)
    csv_path = DATA_PROCESSED_DIR / "multizone_closed_loop.csv"
    master_df.to_csv(csv_path, index=False)
    print(f"Saved consolidated dataset: {csv_path} ({len(master_df)} rows, {len(master_df.columns)} columns)")

    return master_df, scenario_results


def run_canonical_baselines() -> Tuple[MultizoneSimulationResult, MultizoneSimulationResult, MultizoneSimulationResult]:
    """Run Baseline A (None), Baseline B (Fixed), and Control (Fuzzy) on Normal scenario."""
    cfg = MultizoneClosedLoopConfig(scenario=SimulationScenario.NORMAL, seed=42)
    sim = MultizoneClosedLoopSimulator(config=cfg)

    res_fuzzy = sim.run(mode="fuzzy")
    res_none = sim.run(mode="none")
    res_fixed = sim.run(mode="fixed")

    return res_fuzzy, res_none, res_fixed


def generate_scenario_moisture_plots(scenario_results: Dict[str, MultizoneSimulationResult]) -> None:
    """Generate Figures 1-6: Multizone Soil Moisture vs Target for each of the 6 scenarios."""
    scenarios = list(SimulationScenario)

    filename_map = {
        SimulationScenario.NORMAL.value: "multizone_soil_moisture_normal.png",
        SimulationScenario.HOT_AND_DRY.value: "multizone_soil_moisture_hot_dry.png",
        SimulationScenario.RAINY.value: "multizone_soil_moisture_rainy.png",
        SimulationScenario.CLOUDY.value: "multizone_soil_moisture_cloudy.png",
        SimulationScenario.HEATWAVE.value: "multizone_soil_moisture_heatwave.png",
        SimulationScenario.WATER_SCARCITY.value: "multizone_soil_moisture_water_scarcity.png",
    }

    for sc in scenarios:
        res = scenario_results[sc.value]
        df = res.df
        hours = df[df["zone_id"] == 1]["step"].values / 60.0

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(11, 8.5), dpi=300, sharex=True)
        axs = {1: ax1, 2: ax2, 3: ax3}

        for z_id in (1, 2, 3):
            ax = axs[z_id]
            z_df = df[df["zone_id"] == z_id]
            zm = res.zone_metrics[z_id]
            target = zm.target_soil_moisture

            ax.plot(hours, z_df["soil_moisture"], color=ZONE_COLORS[z_id], lw=2.0,
                    label=f"Soil Moisture (Final: {zm.final_soil_moisture:.2f}%)")
            ax.axhline(target, color="#d62728", ls="--", lw=1.5, label=f"Target Setpoint ({target:.1f}%)")
            ax.fill_between(hours, target - 2.0, target + 2.0, color="#2ca02c", alpha=0.15,
                            label="Target Band ($\\pm 2.0\\%$)")

            ax.set_ylabel("SM (% vol)", fontsize=10, fontweight="bold")
            ax.set_ylim(min(z_df["soil_moisture"].min() - 3.0, target - 5.0),
                        max(z_df["soil_moisture"].max() + 3.0, target + 5.0))
            ax.set_title(ZONE_LABELS[z_id], fontsize=10.5, fontweight="bold", loc="left")
            ax.legend(loc="lower right", fontsize=8.5, framealpha=0.9)
            ax.grid(True, alpha=0.3)

        axs[3].set_xlabel("Timeline (Hours)", fontsize=11, fontweight="bold")
        axs[3].set_xlim(0, 24)

        fig.suptitle(f"Multizone Closed-Loop Soil Moisture Trajectories — {sc.value} Scenario\n"
                     f"System Volume: {res.system_metrics.total_system_irrigation_volume_l:.1f} L | "
                     f"Average MAE: {res.system_metrics.system_mean_mae:.2f}% | "
                     f"Band Occupancy: {res.system_metrics.overall_target_band_occupancy_pct:.1f}%",
                     fontsize=12, fontweight="bold", y=0.98)

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        out_name = filename_map[sc.value]
        plt.savefig(FIGURES_DIR / out_name, dpi=300)
        plt.close()
        print(f"Saved Figure: {out_name}")


def generate_master_multizone_figure(res_norm: MultizoneSimulationResult) -> None:
    """Generate Figure 15: Master Multizone Response Plot (Soil Moisture & Targets on unified axis)."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7.5), dpi=300, sharex=True,
                                   gridspec_kw={"height_ratios": [2.2, 1.2]})

    hours = np.arange(1440) / 60.0
    df = res_norm.df

    # Panel 1: Soil Moisture Trajectories vs Distinct Targets
    for z_id in (1, 2, 3):
        z_df = df[df["zone_id"] == z_id]
        zm = res_norm.zone_metrics[z_id]
        color = ZONE_COLORS[z_id]
        target = zm.target_soil_moisture

        ax1.plot(hours, z_df["soil_moisture"], color=color, lw=2.2,
                 label=f"Zone {z_id} ({zm.crop} / {zm.soil}): Final {zm.final_soil_moisture:.2f}%")
        ax1.axhline(target, color=color, ls="--", lw=1.4, alpha=0.8,
                    label=f"Zone {z_id} Target ({target:.0f}%)")
        ax1.fill_between(hours, target - 2.0, target + 2.0, color=color, alpha=0.08)

    ax1.set_ylabel("Soil Moisture Content (% vol)", fontsize=11, fontweight="bold")
    ax1.set_ylim(38.0, 68.0)
    ax1.set_title("Master Multizone Dynamic Closed-Loop Feedback Control Response (Normal Scenario)\n"
                  "Independent Zone Moisture Trajectories Converging to Heterogeneous Crop Setpoints",
                  fontsize=12, fontweight="bold", pad=12)
    ax1.legend(loc="lower right", framealpha=0.9, fontsize=9.0, ncol=2)
    ax1.grid(True, alpha=0.3)

    # Panel 2: Parallel Irrigation Commands
    for z_id in (1, 2, 3):
        z_df = df[df["zone_id"] == z_id]
        ax2.plot(hours, z_df["irrigation_command"], color=ZONE_COLORS[z_id], lw=1.8,
                 label=f"Zone {z_id} Command")

    ax2.set_xlabel("Simulation Timeline (Hours)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Command (%)", fontsize=11, fontweight="bold")
    ax2.set_xlim(0, 24)
    ax2.set_ylim(-2, 102)
    ax2.legend(loc="upper right", framealpha=0.9, fontsize=9.0)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = FIGURES_DIR / "multizone_master_response.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved Figure: {out_path.name}")


def generate_zonewise_diagnostic_plots(res_norm: MultizoneSimulationResult) -> None:
    """Generate Figures 7-14: Zone-wise command, application, error, stresses, demand, and cumulative fluxes."""
    hours = np.arange(1440) / 60.0
    df = res_norm.df

    # 7. Zone-wise Irrigation Command vs Time
    fig, ax = plt.subplots(figsize=(11, 5), dpi=300)
    for z_id in (1, 2, 3):
        z_df = df[df["zone_id"] == z_id]
        ax.plot(hours, z_df["irrigation_command"], color=ZONE_COLORS[z_id], lw=1.8,
                label=f"Zone {z_id}: {res_norm.zone_metrics[z_id].crop}")
    ax.set_title("Zone-Wise Normalized Irrigation Command Modulation $u_z(t)$ (Normal Scenario)",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Irrigation Command (%)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.set_ylim(-2, 102)
    ax.legend(loc="upper right", fontsize=9.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "multizone_irrigation_command.png", dpi=300)
    plt.close()

    # 8. Zone-wise Irrigation Application vs Time (mm)
    fig, ax = plt.subplots(figsize=(11, 5), dpi=300)
    for z_id in (1, 2, 3):
        z_df = df[df["zone_id"] == z_id]
        ax.plot(hours, z_df["irrigation_application"], color=ZONE_COLORS[z_id], lw=1.8,
                label=f"Zone {z_id}: {res_norm.zone_metrics[z_id].crop}")
    ax.set_title("Zone-Wise Physical Irrigation Delivery Rate $I_{\\text{app}, z}(t)$ (mm / step)",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Application Depth (mm / step)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.legend(loc="upper right", fontsize=9.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "multizone_irrigation_application.png", dpi=300)
    plt.close()

    # 9. Zone-wise Moisture Error vs Time
    fig, ax = plt.subplots(figsize=(11, 5), dpi=300)
    for z_id in (1, 2, 3):
        z_df = df[df["zone_id"] == z_id]
        ax.plot(hours, z_df["moisture_error"], color=ZONE_COLORS[z_id], lw=1.8,
                label=f"Zone {z_id}: {res_norm.zone_metrics[z_id].crop} (e(0) = +{z_df['moisture_error'].iloc[0]:.1f}%)")
    ax.axhline(0.0, color="#000000", ls="--", lw=1.0)
    ax.fill_between(hours, -2.0, 2.0, color="#2ca02c", alpha=0.10, label="Acceptable Error Band ($\\pm 2\\%$)")
    ax.set_title("Zone-Wise Soil Moisture Tracking Error $e_z(t) = SM_{\\text{target}, z} - SM_z(t)$",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Moisture Error (%)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.legend(loc="upper right", fontsize=9.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "multizone_moisture_error.png", dpi=300)
    plt.close()

    # 10. Zone-wise Soil Stress vs Time
    fig, ax = plt.subplots(figsize=(11, 4.5), dpi=300)
    for z_id in (1, 2, 3):
        z_df = df[df["zone_id"] == z_id]
        ax.plot(hours, z_df["soil_stress"], color=ZONE_COLORS[z_id], lw=1.8,
                label=f"Zone {z_id}: {res_norm.zone_metrics[z_id].crop}")
    ax.set_title("Zone-Wise Root-Zone Soil Moisture Stress $SS_z(t)$ (SoilStressFIS)",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Soil Stress (%)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.set_ylim(-2, 102)
    ax.legend(loc="upper right", fontsize=9.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "multizone_soil_stress.png", dpi=300)
    plt.close()

    # 11. Zone-wise Weather Stress vs Time (Shared atmospheric forcing)
    fig, ax = plt.subplots(figsize=(11, 4.5), dpi=300)
    ax.plot(hours, df[df["zone_id"] == 1]["weather_stress"], color="#e377c2", lw=2.0,
            label="Weather Stress FIS (Shared across zones)")
    ax.set_title("Atmospheric Climatic Stress $WS(t)$ across All Zones (WeatherStressFIS)",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Weather Stress (%)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.set_ylim(-2, 102)
    ax.legend(loc="upper right", fontsize=9.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "multizone_weather_stress.png", dpi=300)
    plt.close()

    # 12. Zone-wise Water Demand vs Time
    fig, ax = plt.subplots(figsize=(11, 4.5), dpi=300)
    for z_id in (1, 2, 3):
        z_df = df[df["zone_id"] == z_id]
        ax.plot(hours, z_df["water_demand"], color=ZONE_COLORS[z_id], lw=1.8,
                label=f"Zone {z_id}: {res_norm.zone_metrics[z_id].crop} (Kc={z_df['kc'].iloc[0]})")
    ax.set_title("Zone-Wise Crop Water Demand $WD_z(t)$ (WaterDemandFIS)",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Water Demand (%)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.set_ylim(-2, 102)
    ax.legend(loc="upper right", fontsize=9.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "multizone_water_demand.png", dpi=300)
    plt.close()

    # 13. Cumulative Irrigation Depth by Zone (mm)
    fig, ax = plt.subplots(figsize=(11, 5), dpi=300)
    for z_id in (1, 2, 3):
        z_df = df[df["zone_id"] == z_id]
        cum_depth = np.cumsum(z_df["irrigation_application"])
        ax.plot(hours, cum_depth, color=ZONE_COLORS[z_id], lw=2.2,
                label=f"Zone {z_id} ({res_norm.zone_metrics[z_id].crop}): {cum_depth.iloc[-1]:.2f} mm")
    ax.set_title("Cumulative Irrigation Water Depth Applied per Zone (mm)",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Cumulative Depth (mm)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.legend(loc="upper left", fontsize=9.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "multizone_cumulative_irrigation_depth.png", dpi=300)
    plt.close()

    # 14. Cumulative Irrigation Volume by Zone (Liters)
    fig, ax = plt.subplots(figsize=(11, 5), dpi=300)
    for z_id in (1, 2, 3):
        z_df = df[df["zone_id"] == z_id]
        cum_vol = np.cumsum(z_df["irrigation_volume_l"])
        ax.plot(hours, cum_vol, color=ZONE_COLORS[z_id], lw=2.2,
                label=f"Zone {z_id} ({res_norm.zone_metrics[z_id].crop}, {z_df['area_m2'].iloc[0]} m²): {cum_vol.iloc[-1]:.1f} L")
    ax.set_title("Cumulative Irrigation Physical Volume Delivered per Zone (Liters = mm × Area)",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (Hours)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Cumulative Volume (Liters)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    ax.legend(loc="upper left", fontsize=9.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "multizone_cumulative_irrigation_volume.png", dpi=300)
    plt.close()


def generate_system_water_use_plot(res_norm: MultizoneSimulationResult) -> None:
    """Generate Figure 16: System Water Use Comparison (Depth in mm vs Volume in Liters)."""
    zones = [1, 2, 3]
    crops = [res_norm.zone_metrics[z].crop for z in zones]
    areas = [res_norm.zone_metrics[z].area_m2 for z in zones]
    depths = [res_norm.zone_metrics[z].total_irrigation_applied_mm for z in zones]
    volumes = [res_norm.zone_metrics[z].total_irrigation_volume_l for z in zones]

    x = np.arange(len(zones))
    width = 0.35

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)

    # Left: Depths (mm)
    bars1 = ax1.bar(x, depths, width, color=[ZONE_COLORS[z] for z in zones], alpha=0.85, edgecolor="#333333")
    ax1.set_ylabel("Irrigation Depth (mm)", fontsize=11, fontweight="bold")
    ax1.set_title("Equivalent Irrigation Depth (mm)", fontsize=11, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"Zone {z}\n({crops[i]})\n{areas[i]} m²" for i, z in enumerate(zones)], fontsize=10)
    ax1.grid(True, alpha=0.3, axis="y")
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 0.8, f"{yval:.2f} mm", ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    # Right: Volumes (Liters)
    bars2 = ax2.bar(x, volumes, width, color=[ZONE_COLORS[z] for z in zones], alpha=0.85, edgecolor="#333333")
    ax2.set_ylabel("Irrigation Volume (Liters)", fontsize=11, fontweight="bold")
    ax2.set_title("Physical Delivered Water Volume ($V = \\text{depth} \\times \\text{area}$)", fontsize=11, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"Zone {z}\n({crops[i]})\n{areas[i]} m²" for i, z in enumerate(zones)], fontsize=10)
    ax2.grid(True, alpha=0.3, axis="y")
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 100, f"{yval:.1f} L", ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    fig.suptitle(f"Multizone System Water Consumption Summary (Normal Scenario)\n"
                 f"Total System Volume: {res_norm.system_metrics.total_system_irrigation_volume_l:.1f} L | "
                 f"Area-Weighted Depth: {res_norm.system_metrics.weighted_irrigation_depth_mm:.2f} mm",
                 fontsize=12, fontweight="bold")

    plt.tight_layout()
    out_path = FIGURES_DIR / "multizone_system_water_use.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved Figure: {out_path.name}")


def generate_baseline_comparison_figure(
    res_fuzzy: MultizoneSimulationResult,
    res_none: MultizoneSimulationResult,
    res_fixed: MultizoneSimulationResult,
) -> None:
    """Generate Figure 18: Multizone Baseline Comparison (Fuzzy vs No-Irrigation vs Fixed)."""
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(11, 8.5), dpi=300, sharex=True)
    axs = {1: ax1, 2: ax2, 3: ax3}
    hours = np.arange(1440) / 60.0

    for z_id in (1, 2, 3):
        ax = axs[z_id]
        zm_f = res_fuzzy.zone_metrics[z_id]
        zm_n = res_none.zone_metrics[z_id]
        zm_x = res_fixed.zone_metrics[z_id]
        target = zm_f.target_soil_moisture

        df_f = res_fuzzy.df[res_fuzzy.df["zone_id"] == z_id]
        df_n = res_none.df[res_none.df["zone_id"] == z_id]
        df_x = res_fixed.df[res_fixed.df["zone_id"] == z_id]

        ax.plot(hours, df_n["soil_moisture"], color="#7f7f7f", ls="--", lw=1.6,
                label=f"Baseline A: None (Final: {zm_n.final_soil_moisture:.2f}%, MAE: {zm_n.mae:.2f}%)")
        ax.plot(hours, df_x["soil_moisture"], color="#d62728", ls="-.", lw=1.6,
                label=f"Baseline B: Fixed 1.5mm/h (Final: {zm_x.final_soil_moisture:.2f}%, MAE: {zm_x.mae:.2f}%)")
        ax.plot(hours, df_f["soil_moisture"], color=ZONE_COLORS[z_id], lw=2.2,
                label=f"Control: Fuzzy Closed-Loop (Final: {zm_f.final_soil_moisture:.2f}%, MAE: {zm_f.mae:.2f}%)")

        ax.axhline(target, color="#000000", ls=":", lw=1.2, label=f"Target ({target:.1f}%)")
        ax.fill_between(hours, target - 2.0, target + 2.0, color="#2ca02c", alpha=0.10)

        ax.set_ylabel("SM (% vol)", fontsize=10, fontweight="bold")
        ax.set_title(ZONE_LABELS[z_id], fontsize=10.5, fontweight="bold", loc="left")
        ax.legend(loc="lower right", fontsize=8.5, framealpha=0.9)
        ax.grid(True, alpha=0.3)

    axs[3].set_xlabel("Timeline (Hours)", fontsize=11, fontweight="bold")
    axs[3].set_xlim(0, 24)

    fig.suptitle("Multizone Baseline Comparison across All 3 Zones (Normal Scenario)\n"
                 f"Fuzzy System MAE: {res_fuzzy.system_metrics.system_mean_mae:.2f}% | "
                 f"Fixed System MAE: {res_fixed.system_metrics.system_mean_mae:.2f}% | "
                 f"None System MAE: {res_none.system_metrics.system_mean_mae:.2f}%",
                 fontsize=12, fontweight="bold", y=0.98)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    out_path = FIGURES_DIR / "multizone_baseline_comparison.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved Figure: {out_path.name}")


def generate_causality_architecture_diagram() -> None:
    """Generate Figure 17: Closed-Loop Causality & Replicated Control Architecture Diagram."""
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=300)
    ax.axis("off")

    # Draw boxes and arrows demonstrating the 3 replicated parallel loops
    box_props = dict(boxstyle="round,pad=0.4", fc="#f0f4f8", ec="#2b5c8f", lw=1.5)
    header_props = dict(boxstyle="round,pad=0.5", fc="#2b5c8f", ec="#1b3c5f", lw=1.8)

    ax.text(0.5, 0.93, "Shared Environmental Meteorology (T, RH, Rs, u2, P) → FAO-56 Reference ET0(t)",
            ha="center", va="center", fontsize=11, fontweight="bold", color="white", bbox=header_props)

    zones_info = [
        (0.20, "ZONE 1: Tomato / Loam (100 m²)\nKc=1.15 | FC=70% | WP=25%\nInit=55% | Target=60%"),
        (0.50, "ZONE 2: Wheat / Sandy (120 m²)\nKc=0.85 | FC=60% | WP=18%\nInit=42% | Target=55%"),
        (0.80, "ZONE 3: Maize / Clay (80 m²)\nKc=1.20 | FC=75% | WP=30%\nInit=65% | Target=65%"),
    ]

    steps_text = [
        "1. Read SM_z(t)\n2. Compute e_z(t) & RSM_z(t)\n3. SoilStressFIS(RSM_z, e_z)\n4. WaterDemandFIS(ETc_z, Def_z, Peff)",
        "5. MainIrrigationFIS(SS, WS, WD, e) → u_z(t) [%]\n6. Actuator Mapping: I_app,z(t) [mm] & V_z(t) [L]",
        "7. Dynamic Soil-Water Balance:\n   S_z(t+1) = S_z(t) + W_inf - ET_act - D_z\n8. Updated Moisture SM_z(t+1)",
    ]

    for x_pos, title in zones_info:
        # Zone header
        ax.text(x_pos, 0.78, title, ha="center", va="center", fontsize=9.5, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.4", fc="#e8f0fe", ec="#4285f4", lw=1.5))
        # Arrow from meteorology to zone
        ax.annotate("", xy=(x_pos, 0.83), xytext=(x_pos, 0.89),
                    arrowprops=dict(arrowstyle="->", lw=1.5, color="#2b5c8f"))

        # Step block 1
        ax.text(x_pos, 0.58, steps_text[0], ha="center", va="center", fontsize=8.5, bbox=box_props)
        ax.annotate("", xy=(x_pos, 0.50), xytext=(x_pos, 0.66),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color="#555555"))

        # Step block 2
        ax.text(x_pos, 0.38, steps_text[1], ha="center", va="center", fontsize=8.5,
                bbox=dict(boxstyle="round,pad=0.4", fc="#e6f4ea", ec="#137333", lw=1.5))
        ax.annotate("", xy=(x_pos, 0.30), xytext=(x_pos, 0.44),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color="#555555"))

        # Step block 3
        ax.text(x_pos, 0.18, steps_text[2], ha="center", va="center", fontsize=8.5, bbox=box_props)

        # Feedback loop curved arrow
        ax.annotate("Dynamic Feedback ↺\n(SM_z(t+1) → Step t+1)", xy=(x_pos - 0.11, 0.65), xytext=(x_pos - 0.11, 0.18),
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.4", lw=1.5, color="#d93025"),
                    fontsize=8, fontweight="bold", color="#d93025", ha="right", va="center")

    ax.set_title("Phase 12 Parallel Multizone Closed-Loop Causality and Replicated Architecture",
                 fontsize=12, fontweight="bold", y=1.02)
    plt.tight_layout()
    out_path = FIGURES_DIR / "multizone_closed_loop_causality.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved Figure: {out_path.name}")


def main() -> None:
    """Execute complete Phase 12 analysis pipeline and figure generation."""
    # 1. Run all 6 scenarios across 3 zones and save CSV
    master_df, scenario_results = run_all_multizone_scenarios()

    # 2. Run Baselines on Normal scenario
    res_fuzzy, res_none, res_fixed = run_canonical_baselines()

    # 3. Generate 6 Scenario Soil Moisture Figures (Figures 1-6)
    generate_scenario_moisture_plots(scenario_results)

    # 4. Generate Master Multizone Figure (Figure 15)
    generate_master_multizone_figure(res_fuzzy)

    # 5. Generate Zone-wise Diagnostic Figures (Figures 7-14)
    generate_zonewise_diagnostic_plots(res_fuzzy)

    # 6. Generate System Water Use Figure (Figure 16)
    generate_system_water_use_plot(res_fuzzy)

    # 7. Generate Causality Architecture Flowchart (Figure 17)
    generate_causality_architecture_diagram()

    # 8. Generate Multizone Baseline Comparison (Figure 18)
    generate_baseline_comparison_figure(res_fuzzy, res_none, res_fixed)

    print("\n" + "=" * 75)
    print("PHASE 12 MULTIZONE CLOSED-LOOP ANALYSIS AND FIGURE GENERATION COMPLETE")
    print(f"Generated 18 figures located in: {FIGURES_DIR}")
    print("=" * 75)


if __name__ == "__main__":
    main()
