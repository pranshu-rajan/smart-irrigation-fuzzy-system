#!/usr/bin/env python3
"""Soil Water Balance Runner, Experiment Suite, and Visualization Generator.

Executes:
1. Canonical baseline multizone simulation (24 hours at 1-min resolution).
2. Controlled experiment suite:
   - Exp 1: No irrigation (natural depletion)
   - Exp 2: Fixed irrigation (continuous deficit compensation)
   - Exp 3: Periodic pulse irrigation (6h interval, 5mm delivery)
   - Exp 4: Heavy rainfall (Rainy scenario with infiltration and runoff)
   - Exp 5: Hot & Dry scenario
   - Exp 6: Heatwave scenario
   - Exp 7: Water Scarcity scenario (WAF = 0.30)
3. Generates data/processed/soil_water_balance.csv.
4. Generates 13 publication-quality diagnostic figures in reports/soil_water_balance/figures/.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.schemas import SimulationScenario, SystemConfig
from config.defaults import get_default_zones
from simulation.engine import SimulationEngine


def run_soil_water_balance_pipeline():
    """Execute complete Phase 5 soil water balance pipeline and experiments."""
    processed_dir = PROJECT_ROOT / "data" / "processed"
    figures_dir = PROJECT_ROOT / "reports" / "soil_water_balance" / "figures"

    processed_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 75)
    print("PHASE 5: EXECUTING DYNAMIC SOIL WATER BALANCE SIMULATION & EXPERIMENTS")
    print("=" * 75)

    # -------------------------------------------------------------
    # 1. Canonical Baseline Multizone Simulation (Normal + Periodic Pulse)
    # -------------------------------------------------------------
    print("\nRunning Canonical Baseline Simulation (Normal Scenario, Periodic Irrigation)...")
    baseline_engine = SimulationEngine(
        scenario=SimulationScenario.NORMAL,
        irrigation_mode="periodic",
        periodic_pulse_interval_hours=6.0,
        periodic_pulse_depth_mm=4.0,
        seed=42,
    )
    baseline_df = baseline_engine.run(duration_hours=24, timestep_minutes=1)

    # Reorder columns to canonical order
    canonical_cols = [
        "timestamp", "zone_id", "crop", "soil_type", "soil_moisture", "soil_storage_mm",
        "field_capacity", "wilting_point", "saturation", "root_depth_m", "rsm", "target_moisture", "moisture_error",
        "rainfall", "effective_rainfall", "et0", "etc", "irrigation", "infiltration",
        "drainage", "runoff", "water_stress_indicator", "water_balance_residual"
    ]
    baseline_df = baseline_df[canonical_cols]
    output_csv = processed_dir / "soil_water_balance.csv"
    baseline_df.to_csv(output_csv, index=False)
    print(f"[+] Saved baseline soil water balance dataset: {output_csv} ({len(baseline_df)} rows)")

    # -------------------------------------------------------------
    # 2. Run 7 Controlled Experiments
    # -------------------------------------------------------------
    print("\nExecuting 7 Controlled Agronomic Experiments...")
    experiments = {
        "Exp 1 (No Irrigation)": SimulationEngine(scenario=SimulationScenario.NORMAL, irrigation_mode="none", seed=42),
        "Exp 2 (Fixed Irrigation)": SimulationEngine(scenario=SimulationScenario.NORMAL, irrigation_mode="fixed", fixed_irrigation_rate_mm_h=0.35, seed=42),
        "Exp 3 (Periodic Pulse)": SimulationEngine(scenario=SimulationScenario.NORMAL, irrigation_mode="periodic", periodic_pulse_interval_hours=6.0, periodic_pulse_depth_mm=4.0, seed=42),
        "Exp 4 (Heavy Rainfall)": SimulationEngine(scenario=SimulationScenario.RAINY, irrigation_mode="none", seed=42),
        "Exp 5 (Hot & Dry)": SimulationEngine(scenario=SimulationScenario.HOT_AND_DRY, irrigation_mode="none", seed=42),
        "Exp 6 (Heatwave)": SimulationEngine(scenario=SimulationScenario.HEATWAVE, irrigation_mode="none", seed=42),
        "Exp 7 (Water Scarcity)": SimulationEngine(scenario=SimulationScenario.WATER_SCARCITY, irrigation_mode="periodic", periodic_pulse_interval_hours=6.0, periodic_pulse_depth_mm=4.0, seed=42),
    }

    exp_dfs: Dict[str, pd.DataFrame] = {}
    print("\n" + "-" * 105)
    print(f"{'Experiment':<25} | {'Initial SM%':<11} | {'Final SM%':<11} | {'Irrig (mm)':<10} | {'Rain (mm)':<9} | {'ETc (mm)':<9} | {'Drain (mm)':<10} | {'Max Residual':<12}")
    print("-" * 105)

    for name, eng in experiments.items():
        df = eng.run(duration_hours=24, timestep_minutes=1)
        exp_dfs[name] = df
        z1 = df[df["zone_id"] == 1]

        sm_i = z1["soil_moisture"].iloc[0]
        sm_f = z1["soil_moisture"].iloc[-1]
        tot_irr = z1["irrigation"].sum()
        tot_rain = z1["rainfall"].sum()
        tot_etc = z1["etc"].sum()
        tot_drain = z1["drainage"].sum()
        max_res = z1["water_balance_residual"].abs().max()

        print(f"{name:<25} | {sm_i:<11.2f} | {sm_f:<11.2f} | {tot_irr:<10.2f} | {tot_rain:<9.2f} | {tot_etc:<9.2f} | {tot_drain:<10.2f} | {max_res:<12.2e}")

    print("-" * 105)

    # -------------------------------------------------------------
    # 3. Generate 13 Publication-Quality Figures
    # -------------------------------------------------------------
    generate_figures(baseline_df, exp_dfs, figures_dir)
    return baseline_df, exp_dfs


def generate_figures(
    baseline_df: pd.DataFrame,
    exp_dfs: Dict[str, pd.DataFrame],
    figures_dir: Path,
):
    """Generate 13 diagnostic and comparative figures for Phase 5 report."""
    figures_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
        "axes.edgecolor": "#CCCCCC",
        "axes.linewidth": 0.8,
        "grid.color": "#E5E5E5",
        "grid.linestyle": "--",
        "grid.alpha": 0.7,
    })

    zone_colors = {1: "#E53935", 2: "#FB8C00", 3: "#43A047"}
    zone_names = {1: "Zone 1 (Tomato / Loam)", 2: "Zone 2 (Wheat / Sandy)", 3: "Zone 3 (Maize / Clay)"}

    # -------------------------------------------------------------
    # Figures 1 to 3: Soil Moisture vs Time (Zones 1, 2, 3)
    # -------------------------------------------------------------
    for z_id in [1, 2, 3]:
        df = baseline_df[baseline_df["zone_id"] == z_id]
        fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
        time_h = np.linspace(0, 24, len(df))

        ax.plot(time_h, df["soil_moisture"], color=zone_colors[z_id], lw=2.0, label=f"Soil Moisture SM(t) [%]")
        ax.axhline(df["target_moisture"].iloc[0], color="#1E88E5", lw=1.5, ls="--", label=f"Target Set-Point ({df['target_moisture'].iloc[0]:.1f}%)")
        ax.axhline(df["field_capacity"].iloc[0], color="#2E7D32", lw=1.2, ls=":", label=f"Field Capacity ({df['field_capacity'].iloc[0]:.1f}%)")
        ax.axhline(df["wilting_point"].iloc[0], color="#D32F2F", lw=1.2, ls=":", label=f"Wilting Point ({df['wilting_point'].iloc[0]:.1f}%)")

        ax.set_ylabel("Volumetric Soil Moisture [%]", fontsize=10, fontweight="bold")
        ax.set_xlabel("Time [Hours]", fontsize=10, fontweight="bold")
        ax.set_title(f"Dynamic Root-Zone Soil Moisture Trajectory — {zone_names[z_id]}", fontsize=11, fontweight="bold", pad=10)
        ax.set_xlim(0, 24)
        ax.set_xticks(np.arange(0, 25, 2))
        ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)])
        ax.grid(True)
        ax.legend(loc="upper right", frameon=True, fontsize=9)

        plt.tight_layout()
        out_path = figures_dir / f"soil_moisture_timeline_zone{z_id}.png"
        fig.savefig(out_path)
        plt.close(fig)
        print(f"[+] Saved figure: {out_path.name}")

    # -------------------------------------------------------------
    # Figures 4 to 6: Soil Moisture vs FC / WP Envelope (Zones 1, 2, 3)
    # -------------------------------------------------------------
    for z_id in [1, 2, 3]:
        df = baseline_df[baseline_df["zone_id"] == z_id]
        fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
        time_h = np.linspace(0, 24, len(df))

        wp = df["wilting_point"].iloc[0]
        fc = df["field_capacity"].iloc[0]
        sat = df["saturation"].iloc[0]

        # Fill plant available water band
        ax.axhspan(wp, fc, color="#C8E6C9", alpha=0.35, label="Plant Available Water (PAW = FC - WP)")
        # Fill gravitational water band
        ax.axhspan(fc, sat, color="#BBDEFB", alpha=0.35, label="Gravitational Water (Drainage Zone)")

        ax.plot(time_h, df["soil_moisture"], color=zone_colors[z_id], lw=2.2, label=f"Observed SM(t)")
        ax.axhline(fc, color="#2E7D32", lw=1.5, ls="--", label=f"Field Capacity (FC={fc}%)")
        ax.axhline(wp, color="#C62828", lw=1.5, ls="--", label=f"Wilting Point (WP={wp}%)")

        ax.set_ylabel("Soil Moisture [%]", fontsize=10, fontweight="bold")
        ax.set_xlabel("Time [Hours]", fontsize=10, fontweight="bold")
        ax.set_title(f"Soil Moisture within Physical Water Retention Envelope — {zone_names[z_id]}", fontsize=11, fontweight="bold", pad=10)
        ax.set_xlim(0, 24)
        ax.set_ylim(wp - 5, sat + 5)
        ax.set_xticks(np.arange(0, 25, 2))
        ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)])
        ax.grid(True)
        ax.legend(loc="upper right", frameon=True, fontsize=8.5)

        plt.tight_layout()
        out_path = figures_dir / f"soil_moisture_fc_wp_zone{z_id}.png"
        fig.savefig(out_path)
        plt.close(fig)
        print(f"[+] Saved figure: {out_path.name}")

    # -------------------------------------------------------------
    # Figure 7: Relative Soil Moisture (RSM) vs Time
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5), dpi=300)
    time_h = np.linspace(0, 24, 1440)

    for z_id in [1, 2, 3]:
        df = baseline_df[baseline_df["zone_id"] == z_id]
        ax.plot(time_h, df["rsm"], color=zone_colors[z_id], lw=2.0, label=f"{zone_names[z_id]} (RSM)")

    ax.axhline(1.0, color="#2E7D32", lw=1.2, ls="--", label="Field Capacity (RSM = 1.0)")
    ax.axhline(0.0, color="#C62828", lw=1.2, ls="--", label="Wilting Point (RSM = 0.0)")
    ax.set_ylabel("Relative Soil Moisture (RSM) [Dimensionless]", fontsize=10, fontweight="bold")
    ax.set_xlabel("Time [Hours]", fontsize=10, fontweight="bold")
    ax.set_title("Normalized Relative Soil Moisture RSM(t) = (SM - WP) / (FC - WP)", fontsize=11, fontweight="bold", pad=10)
    ax.set_xlim(0, 24)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xticks(np.arange(0, 25, 2))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)])
    ax.grid(True)
    ax.legend(loc="upper right", frameon=True, fontsize=9)

    plt.tight_layout()
    out_path = figures_dir / "rsm_timeline_multizone.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[+] Saved figure: {out_path.name}")

    # -------------------------------------------------------------
    # Figure 8: Moisture Tracking Error vs Time
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5), dpi=300)
    for z_id in [1, 2, 3]:
        df = baseline_df[baseline_df["zone_id"] == z_id]
        ax.plot(time_h, df["moisture_error"], color=zone_colors[z_id], lw=2.0, label=f"{zone_names[z_id]} Error e(t)")

    ax.axhline(0.0, color="black", lw=1.0, ls="-")
    ax.set_ylabel("Moisture Tracking Error e(t) = Target - Current [%]", fontsize=10, fontweight="bold")
    ax.set_xlabel("Time [Hours]", fontsize=10, fontweight="bold")
    ax.set_title("Closed-Loop Soil Moisture Tracking Error Dynamics", fontsize=11, fontweight="bold", pad=10)
    ax.set_xlim(0, 24)
    ax.set_xticks(np.arange(0, 25, 2))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)])
    ax.grid(True)
    ax.legend(loc="upper right", frameon=True, fontsize=9)

    plt.tight_layout()
    out_path = figures_dir / "moisture_error_timeline.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[+] Saved figure: {out_path.name}")

    # -------------------------------------------------------------
    # Figure 9: ETc vs Soil Moisture Depletion
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True, dpi=300)
    z1_no_irr = exp_dfs["Exp 1 (No Irrigation)"][exp_dfs["Exp 1 (No Irrigation)"]["zone_id"] == 1]

    ax1.plot(time_h, z1_no_irr["etc"], color="#E65100", lw=1.8, label="ETc Extraction Rate [mm/step]")
    ax1.set_ylabel("ETc [mm/min]", fontsize=10, fontweight="bold")
    ax1.set_title("Atmospheric Evaporative Demand (ETc) Driving Soil Moisture Depletion (No Irrigation)", fontsize=11, fontweight="bold")
    ax1.grid(True)
    ax1.legend(loc="upper right")

    ax2.plot(time_h, z1_no_irr["soil_moisture"], color="#C2185B", lw=2.0, label="Zone 1 Soil Moisture [%]")
    ax2.set_ylabel("Soil Moisture [%]", fontsize=10, fontweight="bold")
    ax2.set_xlabel("Time [Hours]", fontsize=10, fontweight="bold")
    ax2.set_xlim(0, 24)
    ax2.set_xticks(np.arange(0, 25, 2))
    ax2.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)])
    ax2.grid(True)
    ax2.legend(loc="upper right")

    plt.tight_layout()
    out_path = figures_dir / "etc_vs_soil_moisture.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[+] Saved figure: {out_path.name}")

    # -------------------------------------------------------------
    # Figure 10: Irrigation, Rainfall, Infiltration, and Runoff Flows
    # -------------------------------------------------------------
    rainy_z1 = exp_dfs["Exp 4 (Heavy Rainfall)"][exp_dfs["Exp 4 (Heavy Rainfall)"]["zone_id"] == 1]
    fig, ax = plt.subplots(figsize=(11, 5), dpi=300)

    ax.plot(time_h, rainy_z1["rainfall"], color="#42A5F5", lw=1.5, label="Total Precipitation (Raw Rain)")
    ax.plot(time_h, rainy_z1["infiltration"], color="#1565C0", lw=1.8, ls="--", label="Infiltrated Root-Zone Water")
    ax.plot(time_h, rainy_z1["runoff"], color="#E53935", lw=1.2, ls=":", label="Surface Runoff (Rejected Inflow)")

    ax.set_ylabel("Hydrological Water Flux [mm/step]", fontsize=10, fontweight="bold")
    ax.set_xlabel("Time [Hours]", fontsize=10, fontweight="bold")
    ax.set_title("Precipitation Partitioning: Infiltration Capacity Limiting and Surface Runoff (Rainy Scenario)", fontsize=11, fontweight="bold", pad=10)
    ax.set_xlim(0, 24)
    ax.set_xticks(np.arange(0, 25, 2))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)])
    ax.grid(True)
    ax.legend(loc="upper right", frameon=True)

    plt.tight_layout()
    out_path = figures_dir / "water_flows_partitioning.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[+] Saved figure: {out_path.name}")

    # -------------------------------------------------------------
    # Figure 11: Gravity Drainage Events
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True, dpi=300)
    # Simulate high irrigation event to induce sustained drainage
    eng_flood = SimulationEngine(scenario=SimulationScenario.NORMAL, irrigation_mode="fixed", fixed_irrigation_rate_mm_h=5.0, seed=42)
    df_flood = eng_flood.run(duration_hours=24, timestep_minutes=1)
    z1_flood = df_flood[df_flood["zone_id"] == 1]

    ax1.plot(time_h, z1_flood["soil_moisture"], color="#2E7D32", lw=2.0, label="Soil Moisture SM(t) [%]")
    ax1.axhline(z1_flood["field_capacity"].iloc[0], color="#D84315", lw=1.5, ls="--", label="Field Capacity FC (70%)")
    ax1.axhline(z1_flood["saturation"].iloc[0], color="#1565C0", lw=1.2, ls=":", label="Saturation SAT (85%)")
    ax1.set_ylabel("Soil Moisture [%]", fontsize=10, fontweight="bold")
    ax1.set_title("Percolation Trigger: Moisture Exceeding Field Capacity Induces Deep Drainage", fontsize=11, fontweight="bold")
    ax1.grid(True)
    ax1.legend(loc="upper right")

    ax2.plot(time_h, z1_flood["drainage"], color="#6A1B9A", lw=1.8, label="Deep Percolation / Drainage [mm/step]")
    ax2.set_ylabel("Drainage [mm/min]", fontsize=10, fontweight="bold")
    ax2.set_xlabel("Time [Hours]", fontsize=10, fontweight="bold")
    ax2.set_xlim(0, 24)
    ax2.set_xticks(np.arange(0, 25, 2))
    ax2.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)])
    ax2.grid(True)
    ax2.legend(loc="upper right")

    plt.tight_layout()
    out_path = figures_dir / "drainage_events.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[+] Saved figure: {out_path.name}")

    # -------------------------------------------------------------
    # Figure 12: Water Balance Conservation Residual
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 4.5), dpi=300)
    for z_id in [1, 2, 3]:
        df = baseline_df[baseline_df["zone_id"] == z_id]
        ax.plot(time_h, df["water_balance_residual"], color=zone_colors[z_id], lw=1.0, alpha=0.8, label=f"{zone_names[z_id]} Residual")

    ax.axhline(0.0, color="black", lw=0.8)
    ax.set_ylabel("Conservation Residual [mm]", fontsize=10, fontweight="bold")
    ax.set_xlabel("Time [Hours]", fontsize=10, fontweight="bold")
    ax.set_title("Water Balance Conservation Check: Residual = S_init + Inflow - Outflow - S_final", fontsize=11, fontweight="bold", pad=10)
    ax.set_xlim(0, 24)
    ax.set_ylim(-1e-8, 1e-8)
    ax.set_xticks(np.arange(0, 25, 2))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)])
    ax.grid(True)
    ax.legend(loc="upper right", frameon=True)

    plt.tight_layout()
    out_path = figures_dir / "water_balance_residual.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[+] Saved figure: {out_path.name}")

    # -------------------------------------------------------------
    # Figure 13: Six-Scenario Soil Moisture Comparison
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(12, 5.5), dpi=300)
    scenario_styles = {
        "Exp 1 (No Irrigation)": ("#2E7D32", "-", "Normal (Zero Irrig)"),
        "Exp 4 (Heavy Rainfall)": ("#1565C0", "-", "Rainy Scenario"),
        "Exp 5 (Hot & Dry)": ("#D84315", "--", "Hot & Dry"),
        "Exp 6 (Heatwave)": ("#C62828", "--", "Heatwave"),
        "Exp 3 (Periodic Pulse)": ("#6A1B9A", "-.", "Normal (Periodic Pulse)"),
        "Exp 7 (Water Scarcity)": ("#E65100", ":", "Water Scarcity (WAF=0.30)"),
    }

    for exp_key, (color, ls, label) in scenario_styles.items():
        if exp_key in exp_dfs:
            z1_data = exp_dfs[exp_key][exp_dfs[exp_key]["zone_id"] == 1]
            ax.plot(time_h, z1_data["soil_moisture"], color=color, ls=ls, lw=2.0, label=label)

    ax.axhline(70.0, color="#2E7D32", lw=1.2, ls=":", label="Field Capacity FC (70%)")
    ax.axhline(25.0, color="#C62828", lw=1.2, ls=":", label="Wilting Point WP (25%)")

    ax.set_ylabel("Zone 1 Soil Moisture [%]", fontsize=10, fontweight="bold")
    ax.set_xlabel("Time [Hours]", fontsize=10, fontweight="bold")
    ax.set_title("Cross-Scenario Comparison of Zone 1 Soil Moisture Dynamics", fontsize=11, fontweight="bold", pad=10)
    ax.set_xlim(0, 24)
    ax.set_xticks(np.arange(0, 25, 2))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)])
    ax.grid(True)
    ax.legend(loc="upper right", frameon=True, fontsize=8.5)

    plt.tight_layout()
    out_path = figures_dir / "cross_scenario_soil_moisture.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[+] Saved figure: {out_path.name}")


if __name__ == "__main__":
    run_soil_water_balance_pipeline()
