#!/usr/bin/env python3
"""FAO-56 Penman-Monteith ET0 / ETc Pipeline Runner and Visualizer.

Executes:
1. ET0 calculation across all 6 meteorological scenarios (1-min resolution, 24-hour horizon).
2. Multizone crop evapotranspiration (ETc) calculation for Zones 1 (Tomato), 2 (Wheat), 3 (Maize).
3. Effective rainfall (USDA-SCS and FAO empirical) and atmospheric crop water deficit evaluation.
4. Hourly and daily aggregation.
5. Dataset generation:
   - data/processed/et0_dataset.csv
   - data/processed/crop_water_demand.csv
   - Updates data/processed/irrigation_dataset.csv
6. High-fidelity publication-quality figures saved to reports/et0_etc/figures/.
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

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.schemas import SimulationScenario
from simulation.weather import WeatherEngine
from models.et0 import compute_et0_timeseries, calculate_atmospheric_pressure, calculate_psychrometric_constant
from models.etc import compute_multizone_crop_demand, CropCoefficientManager


def run_et_pipeline() -> Tuple[Dict[SimulationScenario, pd.DataFrame], Dict[SimulationScenario, pd.DataFrame]]:
    """Execute complete ET0 and ETc calculations across all 6 simulation scenarios."""
    data_dir = PROJECT_ROOT / "data" / "simulation"
    processed_dir = PROJECT_ROOT / "data" / "processed"
    figures_dir = PROJECT_ROOT / "reports" / "et0_etc" / "figures"

    processed_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    scenarios = [
        SimulationScenario.NORMAL,
        SimulationScenario.HOT_AND_DRY,
        SimulationScenario.RAINY,
        SimulationScenario.CLOUDY,
        SimulationScenario.HEATWAVE,
        SimulationScenario.WATER_SCARCITY,
    ]

    scenario_et0_dfs: Dict[SimulationScenario, pd.DataFrame] = {}
    scenario_demand_dfs: Dict[SimulationScenario, pd.DataFrame] = {}

    print("=" * 70)
    print("PHASE 4: EXECUTING FAO-56 PENMAN-MONTEITH ET0 / ETc PIPELINE")
    print("=" * 70)

    for sc in scenarios:
        filename_map = {
            SimulationScenario.NORMAL: "normal.csv",
            SimulationScenario.HOT_AND_DRY: "hot_dry.csv",
            SimulationScenario.RAINY: "rainy.csv",
            SimulationScenario.CLOUDY: "cloudy.csv",
            SimulationScenario.HEATWAVE: "heatwave.csv",
            SimulationScenario.WATER_SCARCITY: "water_scarcity.csv",
        }
        file_path = data_dir / filename_map[sc]

        if file_path.exists():
            weather_df = pd.read_csv(file_path)
            weather_df["timestamp"] = pd.to_datetime(weather_df["timestamp"])
        else:
            print(f"Generating missing scenario data for {sc.value}...")
            engine = WeatherEngine(scenario=sc, seed=42)
            weather_df = engine.generate_timeline(duration_hours=24, timestep_minutes=1)

        print(f"Processing ET0 for scenario: {sc.value:<15} ({len(weather_df)} records)...")
        et0_df = compute_et0_timeseries(weather_df, timestep_minutes=1)
        demand_df = compute_multizone_crop_demand(et0_df, timestep_minutes=1)

        scenario_et0_dfs[sc] = et0_df
        scenario_demand_dfs[sc] = demand_df

    # 1. Save canonical baseline Normal scenario datasets to data/processed/
    normal_et0 = scenario_et0_dfs[SimulationScenario.NORMAL]
    normal_demand = scenario_demand_dfs[SimulationScenario.NORMAL]

    et0_out_path = processed_dir / "et0_dataset.csv"
    demand_out_path = processed_dir / "crop_water_demand.csv"

    normal_et0.to_csv(et0_out_path, index=False)
    normal_demand.to_csv(demand_out_path, index=False)
    print(f"\n[+] Saved baseline ET0 dataset: {et0_out_path} ({len(normal_et0)} rows)")
    print(f"[+] Saved crop water demand dataset: {demand_out_path} ({len(normal_demand)} rows)")

    # 2. Update data/processed/irrigation_dataset.csv
    irrig_path = processed_dir / "irrigation_dataset.csv"
    if irrig_path.exists():
        irrig_df = pd.read_csv(irrig_path)
        irrig_df["timestamp"] = pd.to_datetime(irrig_df["timestamp"])
        normal_demand["timestamp"] = pd.to_datetime(normal_demand["timestamp"])

        # Merge calculated columns into irrigation_dataset
        merged = pd.merge(
            irrig_df.drop(columns=["et0", "etc", "effective_rainfall", "water_deficit"], errors="ignore"),
            normal_demand[["timestamp", "zone_id", "et0", "etc", "effective_rainfall", "water_deficit"]],
            on=["timestamp", "zone_id"],
            how="left"
        )
        merged.to_csv(irrig_path, index=False)
        print(f"[+] Updated irrigation dataset with computed ET variables: {irrig_path}")

    # 3. Print Daily Summary Table
    print("\n" + "=" * 80)
    print("SCENARIO DAILY AGGREGATIONS (24-Hour Horizon)")
    print("=" * 80)
    print(f"{'Scenario':<16} | {'ET0 (mm)':<9} | {'Rain (mm)':<9} | {'Peff (mm)':<9} | {'Z1 ETc':<8} | {'Z2 ETc':<8} | {'Z3 ETc':<8} | {'Z1 Def':<8}")
    print("-" * 80)

    for sc in scenarios:
        et0_sum = scenario_et0_dfs[sc]["et0"].sum()
        rain_sum = scenario_et0_dfs[sc]["rainfall"].sum()
        demand = scenario_demand_dfs[sc]
        peff_sum = demand[demand["zone_id"] == 1]["effective_rainfall"].sum()
        z1_etc = demand[demand["zone_id"] == 1]["etc"].sum()
        z2_etc = demand[demand["zone_id"] == 2]["etc"].sum()
        z3_etc = demand[demand["zone_id"] == 3]["etc"].sum()
        z1_def = demand[demand["zone_id"] == 1]["water_deficit"].sum()

        print(f"{sc.value:<16} | {et0_sum:<9.3f} | {rain_sum:<9.3f} | {peff_sum:<9.3f} | {z1_etc:<8.3f} | {z2_etc:<8.3f} | {z3_etc:<8.3f} | {z1_def:<8.3f}")

    print("=" * 80)

    # 4. Generate all 10 Visualization Figures
    generate_figures(scenario_et0_dfs, scenario_demand_dfs, figures_dir)

    return scenario_et0_dfs, scenario_demand_dfs


def generate_figures(
    et0_dfs: Dict[SimulationScenario, pd.DataFrame],
    demand_dfs: Dict[SimulationScenario, pd.DataFrame],
    figures_dir: Path,
) -> None:
    """Generate and save 10 publication-quality diagnostic plots."""
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

    scenario_palette = {
        SimulationScenario.NORMAL: "#2E7D32",       # Green
        SimulationScenario.HOT_AND_DRY: "#D84315",  # Deep Orange
        SimulationScenario.RAINY: "#1565C0",        # Blue
        SimulationScenario.CLOUDY: "#546E7A",       # Slate Grey
        SimulationScenario.HEATWAVE: "#C62828",      # Dark Crimson
        SimulationScenario.WATER_SCARCITY: "#E65100", # Amber
    }

    # -------------------------------------------------------------
    # Figures 1 to 5: ET0 Timelines for Individual Scenarios
    # -------------------------------------------------------------
    timeline_scenarios = [
        (SimulationScenario.NORMAL, "et0_timeline_normal.png", "Normal Scenario (Baseline)"),
        (SimulationScenario.HOT_AND_DRY, "et0_timeline_hot_dry.png", "Hot & Dry Scenario"),
        (SimulationScenario.RAINY, "et0_timeline_rainy.png", "Rainy Scenario"),
        (SimulationScenario.CLOUDY, "et0_timeline_cloudy.png", "Cloudy Scenario"),
        (SimulationScenario.HEATWAVE, "et0_timeline_heatwave.png", "Heatwave Scenario"),
    ]

    for sc, filename, title_suffix in timeline_scenarios:
        df = et0_dfs[sc]
        color = scenario_palette[sc]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True, dpi=300)
        time_hours = np.linspace(0, 24, len(df))

        # Panel 1: ET0 Rate (mm/day equivalent)
        ax1.plot(time_hours, df["et0_rate_mm_day"], color=color, lw=2.0, label="ET0 Rate (mm/day equivalent)")
        ax1.fill_between(time_hours, df["et0_rate_mm_day"], color=color, alpha=0.15)
        ax1.set_ylabel("ET0 Rate [mm/day]", fontsize=10, fontweight="bold")
        ax1.set_title(f"FAO-56 Reference Evapotranspiration (ET0) — {title_suffix}", fontsize=12, fontweight="bold", pad=10)
        ax1.grid(True)
        ax1.legend(loc="upper left", frameon=True)

        # Panel 2: Net Radiation and Solar Radiation
        ax2.plot(time_hours, df["solar_radiation"], color="#F57C00", lw=1.5, label="Solar Radiation [W/m²]")
        # Scale net radiation to equivalent W/m2 for visual comparison: Rn_mj / (60s * 1e-6)
        rn_wm2 = df["net_radiation"] / (60.0 * 1e-6)
        ax2.plot(time_hours, rn_wm2, color="#1976D2", lw=1.5, ls="--", label="Net Radiation Rn [W/m² equivalent]")
        ax2.axhline(0, color="black", lw=0.8, alpha=0.7)
        ax2.set_xlabel("Time of Day [Hours]", fontsize=10, fontweight="bold")
        ax2.set_ylabel("Radiation [W/m²]", fontsize=10, fontweight="bold")
        ax2.set_xlim(0, 24)
        ax2.set_xticks(np.arange(0, 25, 2))
        ax2.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)])
        ax2.grid(True)
        ax2.legend(loc="upper left", frameon=True)

        daily_total = df["et0"].sum()
        ax1.text(0.98, 0.88, f"24h Total ET0: {daily_total:.2f} mm", transform=ax1.transAxes,
                 ha="right", va="top", fontsize=10, bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#999", alpha=0.9))

        plt.tight_layout()
        out_path = figures_dir / filename
        fig.savefig(out_path)
        plt.close(fig)
        print(f"[+] Saved figure: {out_path.name}")

    # -------------------------------------------------------------
    # Figure 6: Daily ET0 Comparison Across All 6 Scenarios
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    scenario_names = [sc.value for sc in et0_dfs.keys()]
    daily_et0_vals = [et0_dfs[sc]["et0"].sum() for sc in et0_dfs.keys()]
    colors = [scenario_palette[sc] for sc in et0_dfs.keys()]

    bars = ax.bar(scenario_names, daily_et0_vals, color=colors, width=0.55, edgecolor="#333333", lw=1.0)
    for bar, val in zip(bars, daily_et0_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.12, f"{val:.2f} mm",
                ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    ax.set_ylabel("Daily Reference Evapotranspiration ET0 [mm/day]", fontsize=11, fontweight="bold")
    ax.set_title("Cross-Scenario Comparison of Daily Reference Evapotranspiration (ET0)", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylim(0, max(daily_et0_vals) * 1.18)
    ax.grid(axis="y", alpha=0.7)

    plt.tight_layout()
    out_path = figures_dir / "daily_et0_comparison_scenarios.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[+] Saved figure: {out_path.name}")

    # -------------------------------------------------------------
    # Figure 7: Daily ETc Comparison Across the Three Zones
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(12, 5.5), dpi=300)
    x = np.arange(len(et0_dfs))
    width = 0.25

    z1_vals = [demand_dfs[sc][demand_dfs[sc]["zone_id"] == 1]["etc"].sum() for sc in et0_dfs.keys()]
    z2_vals = [demand_dfs[sc][demand_dfs[sc]["zone_id"] == 2]["etc"].sum() for sc in et0_dfs.keys()]
    z3_vals = [demand_dfs[sc][demand_dfs[sc]["zone_id"] == 3]["etc"].sum() for sc in et0_dfs.keys()]

    rects1 = ax.bar(x - width, z1_vals, width, label="Zone 1: Tomato (Kc=1.15)", color="#E53935", edgecolor="#333", lw=0.8)
    rects2 = ax.bar(x, z2_vals, width, label="Zone 2: Wheat (Kc=0.85)", color="#FB8C00", edgecolor="#333", lw=0.8)
    rects3 = ax.bar(x + width, z3_vals, width, label="Zone 3: Maize (Kc=1.20)", color="#43A047", edgecolor="#333", lw=0.8)

    ax.set_ylabel("Daily Crop Evapotranspiration ETc [mm/day]", fontsize=11, fontweight="bold")
    ax.set_title("Multizone Crop Evapotranspiration (ETc = Kc × ET0) Across Environmental Scenarios", fontsize=12, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels([sc.value for sc in et0_dfs.keys()], fontsize=10, fontweight="medium")
    ax.legend(loc="upper left", frameon=True)
    ax.grid(axis="y", alpha=0.7)
    ax.set_ylim(0, max(z3_vals) * 1.20)

    # Add values on top of bars
    for rect in rects1:
        h = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2, h + 0.1, f"{h:.1f}", ha="center", va="bottom", fontsize=8)
    for rect in rects2:
        h = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2, h + 0.1, f"{h:.1f}", ha="center", va="bottom", fontsize=8)
    for rect in rects3:
        h = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2, h + 0.1, f"{h:.1f}", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    out_path = figures_dir / "daily_etc_comparison_zones.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[+] Saved figure: {out_path.name}")

    # -------------------------------------------------------------
    # Figure 8: Water Deficit Comparison Across Zones and Scenarios
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(12, 5.5), dpi=300)
    z1_def = [demand_dfs[sc][demand_dfs[sc]["zone_id"] == 1]["water_deficit"].sum() for sc in et0_dfs.keys()]
    z2_def = [demand_dfs[sc][demand_dfs[sc]["zone_id"] == 2]["water_deficit"].sum() for sc in et0_dfs.keys()]
    z3_def = [demand_dfs[sc][demand_dfs[sc]["zone_id"] == 3]["water_deficit"].sum() for sc in et0_dfs.keys()]

    rects1 = ax.bar(x - width, z1_def, width, label="Zone 1: Tomato Deficit", color="#C2185B", edgecolor="#333", lw=0.8)
    rects2 = ax.bar(x, z2_def, width, label="Zone 2: Wheat Deficit", color="#F57C00", edgecolor="#333", lw=0.8)
    rects3 = ax.bar(x + width, z3_def, width, label="Zone 3: Maize Deficit", color="#2E7D32", edgecolor="#333", lw=0.8)

    ax.set_ylabel("Atmospheric Crop Water Deficit D_crop [mm/day]", fontsize=11, fontweight="bold")
    ax.set_title("Atmospheric Crop Water Deficit D_crop = max(0, ETc - Peff) Across Scenarios", fontsize=12, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels([sc.value for sc in et0_dfs.keys()], fontsize=10, fontweight="medium")
    ax.legend(loc="upper left", frameon=True)
    ax.grid(axis="y", alpha=0.7)
    ax.set_ylim(0, max(max(z3_def), 1.0) * 1.25)

    plt.tight_layout()
    out_path = figures_dir / "water_deficit_comparison.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[+] Saved figure: {out_path.name}")

    # -------------------------------------------------------------
    # Figure 9: Rainfall vs Effective Rainfall
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    rain_totals = [et0_dfs[sc]["rainfall"].sum() for sc in et0_dfs.keys()]
    peff_totals = [demand_dfs[sc][demand_dfs[sc]["zone_id"] == 1]["effective_rainfall"].sum() for sc in et0_dfs.keys()]

    bar_x = np.arange(len(et0_dfs))
    b_width = 0.35

    ax.bar(bar_x - b_width / 2, rain_totals, b_width, label="Total Precipitation (Raw Rain)", color="#42A5F5", edgecolor="#333", lw=0.8)
    ax.bar(bar_x + b_width / 2, peff_totals, b_width, label="Effective Rainfall (Root Zone Infiltrated)", color="#1565C0", edgecolor="#333", lw=0.8)

    for i in range(len(bar_x)):
        if rain_totals[i] > 0.05:
            ax.text(bar_x[i] - b_width / 2, rain_totals[i] + 0.3, f"{rain_totals[i]:.1f}", ha="center", fontsize=9)
            ax.text(bar_x[i] + b_width / 2, peff_totals[i] + 0.3, f"{peff_totals[i]:.1f}", ha="center", fontsize=9)

    ax.set_ylabel("Water Depth [mm/day]", fontsize=11, fontweight="bold")
    ax.set_title("Precipitation Partitioning: Total Rainfall vs. Effective Infiltrated Rainfall", fontsize=12, fontweight="bold", pad=12)
    ax.set_xticks(bar_x)
    ax.set_xticklabels([sc.value for sc in et0_dfs.keys()], fontsize=10, fontweight="medium")
    ax.legend(loc="upper left", frameon=True)
    ax.grid(axis="y", alpha=0.7)
    ax.set_ylim(0, max(max(rain_totals), 1.0) * 1.25)

    plt.tight_layout()
    out_path = figures_dir / "rainfall_vs_effective_rainfall.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[+] Saved figure: {out_path.name}")

    # -------------------------------------------------------------
    # Figure 10: VPD vs Temperature Physical Relationship
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    for sc in et0_dfs.keys():
        df = et0_dfs[sc]
        color = scenario_palette[sc]
        ax.scatter(df["temperature"], df["vpd"], color=color, alpha=0.35, s=12, label=sc.value)

    # Theoretical saturation vapour pressure curve for reference
    t_span = np.linspace(15, 45, 100)
    es_span = 0.6108 * np.exp((17.27 * t_span) / (t_span + 237.3))
    # Reference lines for constant RH: 30%, 50%, 70%
    ax.plot(t_span, es_span * (1 - 0.30), "r--", lw=1.2, label="Theoretical VPD (RH = 30%)")
    ax.plot(t_span, es_span * (1 - 0.50), "g--", lw=1.2, label="Theoretical VPD (RH = 50%)")
    ax.plot(t_span, es_span * (1 - 0.70), "b--", lw=1.2, label="Theoretical VPD (RH = 70%)")

    ax.set_xlabel("Air Temperature T [°C]", fontsize=11, fontweight="bold")
    ax.set_ylabel("Vapour Pressure Deficit (VPD = es - ea) [kPa]", fontsize=11, fontweight="bold")
    ax.set_title("Psychrometric Driver: Vapour Pressure Deficit vs. Ambient Air Temperature", fontsize=12, fontweight="bold", pad=12)
    ax.grid(True, alpha=0.7)
    ax.legend(loc="upper left", frameon=True, fontsize=8.5)

    plt.tight_layout()
    out_path = figures_dir / "vpd_vs_temperature.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[+] Saved figure: {out_path.name}")


if __name__ == "__main__":
    run_et_pipeline()
