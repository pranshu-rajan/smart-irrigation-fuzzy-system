"""
Phase 9: Water Demand Fuzzy Inference System Analysis & Visualization Script.

Generates:
1. 3 Pairwise 3D Control Surfaces & 2D Contour Maps (reports/water_demand/figures/):
   - etc_deficit_surface.png / etc_deficit_contour.png
   - etc_rainfall_surface.png / etc_rainfall_contour.png
   - deficit_rainfall_surface.png / deficit_rainfall_contour.png
2. Membership Function Visualizations (reports/water_demand/figures/):
   - mf_etc.png
   - mf_crop_water_deficit.png
   - mf_effective_rainfall.png
   - mf_water_demand.png
3. Step-by-Step Mamdani Inference Example (reports/water_demand/figures/water_demand_inference_example.png)
4. Comprehensive Water Demand Dataset across 6 Scenarios x 3 Zones (data/processed/water_demand.csv):
   - Exact row count: 6 scenarios * 3 zones * 1440 timesteps = 25,920 rows.
5. Scenario Comparison Visualization (reports/water_demand/figures/water_demand_scenarios.png)
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import pandas as pd

from config.schemas import SimulationScenario
from fuzzy_engine.water_demand import WaterDemandFIS
from simulation.weather import WeatherEngine
from models.et0 import compute_et0_timeseries
from models.etc import compute_multizone_crop_demand

FIGURES_DIR = PROJECT_ROOT / "reports" / "water_demand" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

COLOR_PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]


def generate_control_surfaces(fis: WaterDemandFIS) -> None:
    """Generate the 3 pairwise 3D control surfaces and 2D contour maps."""
    print("Generating pairwise 3D control surfaces and 2D contour maps...")
    n_pts = 60

    # 1. ETc x Crop Water Deficit (holding Effective Rainfall = 0.0 mm)
    etc_vals = np.linspace(0.0, 15.0, n_pts)
    def_vals = np.linspace(0.0, 15.0, n_pts)
    E1, D1 = np.meshgrid(etc_vals, def_vals)
    Z1 = np.zeros_like(E1)
    for i in range(n_pts):
        for j in range(n_pts):
            Z1[i, j] = fis.evaluate(E1[i, j], D1[i, j], 0.0)

    # 3D Surface: ETc x Deficit
    fig = plt.figure(figsize=(9, 6), dpi=300)
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(E1, D1, Z1, cmap="viridis", edgecolor="none", alpha=0.92)
    ax.set_title("Water Demand Control Surface: ETc × Deficit\n(Effective Rainfall = 0.0 mm)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Crop Evapotranspiration (ETc) [mm/day]", fontsize=9, labelpad=7)
    ax.set_ylabel("Crop Water Deficit [mm/day]", fontsize=9, labelpad=7)
    ax.set_zlabel("Water Demand [%]", fontsize=9, labelpad=7)
    ax.set_zlim(0, 100)
    ax.view_init(elev=28, azim=-125)
    fig.colorbar(surf, shrink=0.55, aspect=12, pad=0.08)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "etc_deficit_surface.png", dpi=300)
    plt.close(fig)

    # 2D Contour: ETc x Deficit
    fig, ax = plt.subplots(figsize=(7.5, 6), dpi=300)
    cs = ax.contourf(E1, D1, Z1, levels=20, cmap="viridis")
    cbar = fig.colorbar(cs, ax=ax)
    cbar.set_label("Water Demand [%]", fontsize=9)
    lines = ax.contour(E1, D1, Z1, levels=10, colors="white", alpha=0.35, linewidths=0.8)
    ax.clabel(lines, inline=True, fontsize=8, fmt="%.0f%%")
    ax.set_title("Water Demand Contour: ETc × Deficit (Rain = 0 mm)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Crop Evapotranspiration (ETc) [mm/day]", fontsize=9)
    ax.set_ylabel("Crop Water Deficit [mm/day]", fontsize=9)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "etc_deficit_contour.png", dpi=300)
    plt.close(fig)

    # 2. ETc x Effective Rainfall (holding Crop Water Deficit = 3.0 mm/day)
    rain_vals = np.linspace(0.0, 50.0, n_pts)
    E2, R2 = np.meshgrid(etc_vals, rain_vals)
    Z2 = np.zeros_like(E2)
    for i in range(n_pts):
        for j in range(n_pts):
            Z2[i, j] = fis.evaluate(E2[i, j], 3.0, R2[i, j])

    # 3D Surface: ETc x Rainfall
    fig = plt.figure(figsize=(9, 6), dpi=300)
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(E2, R2, Z2, cmap="plasma", edgecolor="none", alpha=0.92)
    ax.set_title("Water Demand Control Surface: ETc × Effective Rainfall\n(Crop Water Deficit = 3.0 mm/day)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Crop Evapotranspiration (ETc) [mm/day]", fontsize=9, labelpad=7)
    ax.set_ylabel("Effective Rainfall [mm]", fontsize=9, labelpad=7)
    ax.set_zlabel("Water Demand [%]", fontsize=9, labelpad=7)
    ax.set_zlim(0, 100)
    ax.view_init(elev=28, azim=-120)
    fig.colorbar(surf, shrink=0.55, aspect=12, pad=0.08)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "etc_rainfall_surface.png", dpi=300)
    plt.close(fig)

    # 2D Contour: ETc x Rainfall
    fig, ax = plt.subplots(figsize=(7.5, 6), dpi=300)
    cs = ax.contourf(E2, R2, Z2, levels=20, cmap="plasma")
    cbar = fig.colorbar(cs, ax=ax)
    cbar.set_label("Water Demand [%]", fontsize=9)
    lines = ax.contour(E2, R2, Z2, levels=10, colors="white", alpha=0.35, linewidths=0.8)
    ax.clabel(lines, inline=True, fontsize=8, fmt="%.0f%%")
    ax.set_title("Water Demand Contour: ETc × Effective Rainfall (Deficit = 3.0 mm/day)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Crop Evapotranspiration (ETc) [mm/day]", fontsize=9)
    ax.set_ylabel("Effective Rainfall [mm]", fontsize=9)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "etc_rainfall_contour.png", dpi=300)
    plt.close(fig)

    # 3. Deficit x Effective Rainfall (holding ETc = 6.0 mm/day)
    D3, R3 = np.meshgrid(def_vals, rain_vals)
    Z3 = np.zeros_like(D3)
    for i in range(n_pts):
        for j in range(n_pts):
            Z3[i, j] = fis.evaluate(6.0, D3[i, j], R3[i, j])

    # 3D Surface: Deficit x Rainfall
    fig = plt.figure(figsize=(9, 6), dpi=300)
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(D3, R3, Z3, cmap="coolwarm", edgecolor="none", alpha=0.92)
    ax.set_title("Water Demand Control Surface: Deficit × Effective Rainfall\n(ETc = 6.0 mm/day)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Crop Water Deficit [mm/day]", fontsize=9, labelpad=7)
    ax.set_ylabel("Effective Rainfall [mm]", fontsize=9, labelpad=7)
    ax.set_zlabel("Water Demand [%]", fontsize=9, labelpad=7)
    ax.set_zlim(0, 100)
    ax.view_init(elev=28, azim=-125)
    fig.colorbar(surf, shrink=0.55, aspect=12, pad=0.08)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "deficit_rainfall_surface.png", dpi=300)
    plt.close(fig)

    # 2D Contour: Deficit x Rainfall
    fig, ax = plt.subplots(figsize=(7.5, 6), dpi=300)
    cs = ax.contourf(D3, R3, Z3, levels=20, cmap="coolwarm")
    cbar = fig.colorbar(cs, ax=ax)
    cbar.set_label("Water Demand [%]", fontsize=9)
    lines = ax.contour(D3, R3, Z3, levels=10, colors="white", alpha=0.35, linewidths=0.8)
    ax.clabel(lines, inline=True, fontsize=8, fmt="%.0f%%")
    ax.set_title("Water Demand Contour: Deficit × Effective Rainfall (ETc = 6.0 mm/day)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Crop Water Deficit [mm/day]", fontsize=9)
    ax.set_ylabel("Effective Rainfall [mm]", fontsize=9)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "deficit_rainfall_contour.png", dpi=300)
    plt.close(fig)

    print("Saved 3D control surfaces and 2D contours successfully.")


def generate_membership_plots(fis: WaterDemandFIS) -> None:
    """Generate individual membership function plots for the 3 inputs and 1 output."""
    print("Generating membership function figures...")
    vars_to_plot = [
        (fis.etc_var, "etc", "Crop Evapotranspiration (ETc) [mm/day]", "mf_etc.png"),
        (fis.deficit_var, "crop_water_deficit", "Crop Water Deficit [mm/day]", "mf_crop_water_deficit.png"),
        (fis.rainfall_var, "effective_rainfall", "Effective Infiltrated Rain [mm]", "mf_effective_rainfall.png"),
        (fis.demand_var, "water_demand", "Crop Water Demand [%]", "mf_water_demand.png"),
    ]

    for var, key, xlabel, fname in vars_to_plot:
        fig, ax = plt.subplots(figsize=(8, 4), dpi=300)
        x = np.linspace(var.universe.min_val, var.universe.max_val, 400)
        for idx, (set_name, mf_set) in enumerate(var.sets.items()):
            y = mf_set.evaluate(x)
            color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]
            ax.plot(x, y, label=set_name.replace("_", " ").title(), lw=2.2, color=color)
            ax.fill_between(x, y, alpha=0.12, color=color)

        ax.set_title(f"Fuzzy Membership Functions: {var.display_name}", fontsize=11, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=9.5)
        ax.set_ylabel("Membership Degree $\\mu(x)$", fontsize=9.5)
        ax.set_ylim(-0.02, 1.08)
        ax.set_xlim(var.universe.min_val, var.universe.max_val)
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="upper right", framealpha=0.9, fontsize=8.5)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / fname, dpi=300)
        plt.close(fig)
        print(f"Saved: {fname}")


def generate_inference_example(fis: WaterDemandFIS) -> None:
    """Generate detailed Mamdani step-by-step inference diagram."""
    print("Generating Mamdani inference step-by-step example diagram...")
    # Representative inputs: ETc = 7.0 mm/day, Deficit = 5.0 mm/day, Rain = 2.0 mm
    etc_in = 7.0
    def_in = 5.0
    rain_in = 2.0

    detailed = fis.evaluate_detailed(etc_in, def_in, rain_in)
    demand_val = detailed["water_demand"]

    fig, axs = plt.subplots(2, 2, figsize=(11, 7.5), dpi=300)

    # 1. ETc Fuzzification
    ax_etc = axs[0, 0]
    x_etc = np.linspace(0, 15, 300)
    for idx, (sname, s) in enumerate(fis.etc_var.sets.items()):
        y = s.evaluate(x_etc)
        color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]
        ax_etc.plot(x_etc, y, label=sname.title(), color=color, lw=1.6)
    ax_etc.axvline(etc_in, color="black", linestyle="--", lw=1.8, label=f"Input = {etc_in:.1f} mm/day")
    for sname, mu in detailed["etc_membership"].items():
        if mu > 0:
            ax_etc.plot(etc_in, mu, "ro", markersize=6)
            ax_etc.annotate(f"{sname}: {mu:.2f}", (etc_in + 0.3, mu + 0.03), fontsize=7.5)
    ax_etc.set_title("Step 1a: ETc Fuzzification", fontsize=10, fontweight="bold")
    ax_etc.set_xlabel("ETc [mm/day]", fontsize=8.5)
    ax_etc.set_ylabel("$\\mu(x)$", fontsize=8.5)
    ax_etc.set_ylim(-0.05, 1.1)
    ax_etc.grid(True, linestyle=":", alpha=0.5)
    ax_etc.legend(loc="upper right", fontsize=7)

    # 2. Deficit Fuzzification
    ax_def = axs[0, 1]
    x_def = np.linspace(0, 15, 300)
    for idx, (sname, s) in enumerate(fis.deficit_var.sets.items()):
        y = s.evaluate(x_def)
        color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]
        ax_def.plot(x_def, y, label=sname.title(), color=color, lw=1.6)
    ax_def.axvline(def_in, color="black", linestyle="--", lw=1.8, label=f"Input = {def_in:.1f} mm/day")
    for sname, mu in detailed["deficit_membership"].items():
        if mu > 0:
            ax_def.plot(def_in, mu, "ro", markersize=6)
            ax_def.annotate(f"{sname}: {mu:.2f}", (def_in + 0.3, mu + 0.03), fontsize=7.5)
    ax_def.set_title("Step 1b: Crop Water Deficit Fuzzification", fontsize=10, fontweight="bold")
    ax_def.set_xlabel("Deficit [mm/day]", fontsize=8.5)
    ax_def.set_ylabel("$\\mu(x)$", fontsize=8.5)
    ax_def.set_ylim(-0.05, 1.1)
    ax_def.grid(True, linestyle=":", alpha=0.5)
    ax_def.legend(loc="upper right", fontsize=7)

    # 3. Effective Rainfall Fuzzification
    ax_rain = axs[1, 0]
    x_rain = np.linspace(0, 50, 300)
    for idx, (sname, s) in enumerate(fis.rainfall_var.sets.items()):
        y = s.evaluate(x_rain)
        color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]
        ax_rain.plot(x_rain, y, label=sname.title(), color=color, lw=1.6)
    ax_rain.axvline(rain_in, color="black", linestyle="--", lw=1.8, label=f"Input = {rain_in:.1f} mm")
    for sname, mu in detailed["effective_rainfall_membership"].items():
        if mu > 0:
            ax_rain.plot(rain_in, mu, "ro", markersize=6)
            ax_rain.annotate(f"{sname}: {mu:.2f}", (rain_in + 1.0, mu + 0.03), fontsize=7.5)
    ax_rain.set_title("Step 1c: Effective Rainfall Fuzzification", fontsize=10, fontweight="bold")
    ax_rain.set_xlabel("Effective Rainfall [mm]", fontsize=8.5)
    ax_rain.set_ylabel("$\\mu(x)$", fontsize=8.5)
    ax_rain.set_ylim(-0.05, 1.1)
    ax_rain.grid(True, linestyle=":", alpha=0.5)
    ax_rain.legend(loc="upper right", fontsize=7)

    # 4. Consequent Aggregation & Centroid Defuzzification
    ax_out = axs[1, 1]
    z_grid = fis.z_grid
    for idx, (sname, s) in enumerate(fis.demand_var.sets.items()):
        y = s.evaluate(z_grid)
        ax_out.plot(z_grid, y, linestyle=":", color="gray", alpha=0.6, lw=1.2)

    agg_mu = np.zeros_like(z_grid)
    for sname, beta in detailed["consequent_activations"].items():
        if beta > 0.0:
            clipped = np.minimum(beta, fis._output_mf_matrix[sname])
            agg_mu = np.maximum(agg_mu, clipped)
            ax_out.axhline(beta, color="purple", linestyle="--", alpha=0.3, lw=0.9)

    ax_out.plot(z_grid, agg_mu, color="crimson", lw=2.2, label="Aggregated Fuzzy Set $\\mu_{agg}(z)$")
    ax_out.fill_between(z_grid, agg_mu, color="crimson", alpha=0.25)
    ax_out.axvline(demand_val, color="navy", linestyle="-", lw=2.4, label=f"Centroid Output $z^* = {demand_val:.1f}\\%$")

    ax_out.set_title(f"Step 2-4: Rule Aggregation & Defuzzification", fontsize=10, fontweight="bold")
    ax_out.set_xlabel("Water Demand [%]", fontsize=8.5)
    ax_out.set_ylabel("$\\mu_{agg}(z)$", fontsize=8.5)
    ax_out.set_xlim(0, 100)
    ax_out.set_ylim(0, 1.05)
    ax_out.grid(True, linestyle=":", alpha=0.5)
    ax_out.legend(loc="upper left", fontsize=7.5)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "water_demand_inference_example.png", dpi=300)
    plt.close(fig)
    print("Saved: water_demand_inference_example.png")


def generate_scenario_dataset_and_plot(fis: WaterDemandFIS) -> pd.DataFrame:
    """
    Run simulation pipeline across 6 scenarios and 3 zones,
    compute Water Demand, save data/processed/water_demand.csv,
    and generate scenario diurnal comparison plot.
    """
    print("Processing real multizone scenario datasets...")
    scenarios = list(SimulationScenario)
    all_dfs = []

    scenario_colors = {
        SimulationScenario.NORMAL: "#1f77b4",
        SimulationScenario.HOT_AND_DRY: "#ff7f0e",
        SimulationScenario.RAINY: "#2ca02c",
        SimulationScenario.CLOUDY: "#7f7f7f",
        SimulationScenario.HEATWAVE: "#d62728",
        SimulationScenario.WATER_SCARCITY: "#9467bd",
    }

    # Tracking metrics
    scenario_metrics = {}
    zone_metrics = {1: [], 2: [], 3: []}

    # Multi-zone metadata
    zones_metadata = [
        {"zone_id": 1, "crop": "Tomato", "growth_stage": "Mid-season", "kc": 1.15},
        {"zone_id": 2, "crop": "Wheat", "growth_stage": "Development", "kc": 0.85},
        {"zone_id": 3, "crop": "Maize", "growth_stage": "Mid-season", "kc": 1.20},
    ]

    fig, axs = plt.subplots(3, 1, figsize=(11, 8.5), dpi=300, sharex=True)
    zone_titles = {
        1: "Zone 1: Tomato (Mid-season, Kc=1.15, Loam Soil)",
        2: "Zone 2: Wheat (Development, Kc=0.85, Sandy Soil)",
        3: "Zone 3: Maize (Mid-season, Kc=1.20, Clay Soil)",
    }

    for sc in scenarios:
        # Step 1: Dynamic Weather Generation
        w_engine = WeatherEngine(scenario=sc, seed=42)
        weather_df = w_engine.generate_timeline(duration_hours=24, timestep_minutes=1)

        # Step 2: FAO-56 Penman-Monteith ET0
        et0_df = compute_et0_timeseries(weather_df, timestep_minutes=1)

        # Step 3: Multizone Crop Demand (ETc, Peff, Deficit)
        crop_demand_df = compute_multizone_crop_demand(
            et0_df=et0_df,
            zones_info=zones_metadata,
            timestep_minutes=1,
            effective_rainfall_method="usda_scs",
        )

        crop_demand_df["scenario"] = sc.value

        # Step 4: Evaluate Water Demand via WaterDemandFIS
        etc_arr = crop_demand_df["etc"].values
        def_arr = crop_demand_df["water_deficit"].values
        rain_arr = crop_demand_df["effective_rainfall"].values

        demand_arr = fis.evaluate_array(etc_arr, def_arr, rain_arr)
        crop_demand_df["water_demand"] = np.round(demand_arr, 2)
        crop_demand_df["crop_water_deficit"] = crop_demand_df["water_deficit"]

        all_dfs.append(crop_demand_df)

        # Record scenario-level stats
        scenario_metrics[sc.value] = {
            "mean_etc": float(np.mean(etc_arr)),
            "mean_deficit": float(np.mean(def_arr)),
            "mean_effective_rainfall": float(np.mean(rain_arr)),
            "total_rainfall": float(np.sum(crop_demand_df["rainfall"].values) / 3.0),
            "mean_demand": float(np.mean(demand_arr)),
            "min_demand": float(np.min(demand_arr)),
            "max_demand": float(np.max(demand_arr)),
        }

        # Plot zone curves
        for zid in [1, 2, 3]:
            sub = crop_demand_df[crop_demand_df["zone_id"] == zid]
            hrs = np.arange(len(sub)) / 60.0
            axs[zid - 1].plot(hrs, sub["water_demand"].values, label=sc.value, color=scenario_colors[sc], lw=1.6)
            zone_metrics[zid].append({
                "scenario": sc.value,
                "mean_demand": float(np.mean(sub["water_demand"].values)),
                "min_demand": float(np.min(sub["water_demand"].values)),
                "max_demand": float(np.max(sub["water_demand"].values)),
            })

    for zid in [1, 2, 3]:
        axs[zid - 1].set_title(zone_titles[zid], fontsize=11, fontweight="bold")
        axs[zid - 1].set_ylabel("Water Demand [%]", fontsize=9.5)
        axs[zid - 1].set_ylim(-2, 102)
        axs[zid - 1].grid(True, linestyle="--", alpha=0.5)

    axs[0].legend(loc="upper right", ncol=3, fontsize=8, framealpha=0.92)
    axs[2].set_xlabel("Simulation Time [hours]", fontsize=10, fontweight="semibold")

    sc_path = FIGURES_DIR / "water_demand_scenarios.png"
    plt.tight_layout()
    plt.savefig(sc_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {sc_path.name}")

    # Combine all records
    df_combined = pd.concat(all_dfs, ignore_index=True)
    out_cols = [
        "timestamp", "scenario", "zone_id", "crop", "growth_stage",
        "kc", "et0", "etc", "rainfall", "effective_rainfall",
        "crop_water_deficit", "water_demand"
    ]
    df_out = df_combined[out_cols]
    out_csv = DATA_PROCESSED_DIR / "water_demand.csv"
    df_out.to_csv(out_csv, index=False)
    print(f"Generated {out_csv.name} with {len(df_out)} records.")

    # Summary reports
    print("\n============================================================")
    print("SCENARIO-WISE WATER DEMAND SUMMARY")
    print("============================================================")
    for sc_name, m in scenario_metrics.items():
        print(f"Scenario: {sc_name:15s} | Mean ETc: {m['mean_etc']:.3f} mm/day | Deficit: {m['mean_deficit']:.3f} mm/day | Rain: {m['mean_effective_rainfall']:.3f} mm | Demand: {m['mean_demand']:.2f}% (Min: {m['min_demand']:.2f}%, Max: {m['max_demand']:.2f}%)")

    print("\n============================================================")
    print("ZONE-WISE WATER DEMAND SUMMARY (Baseline Across All Scenarios)")
    print("============================================================")
    for zid in [1, 2, 3]:
        z_sub = df_out[df_out["zone_id"] == zid]
        print(f"Zone {zid} ({z_sub['crop'].iloc[0]}):")
        print(f"  Overall Mean Demand: {z_sub['water_demand'].mean():.2f}%")
        print(f"  Minimum Demand:      {z_sub['water_demand'].min():.2f}%")
        print(f"  Maximum Demand:      {z_sub['water_demand'].max():.2f}%")
        print(f"  Peak Timestep:       {z_sub.loc[z_sub['water_demand'].idxmax(), 'timestamp']}")

    return df_out


def main():
    fis = WaterDemandFIS()
    generate_control_surfaces(fis)
    generate_membership_plots(fis)
    generate_inference_example(fis)
    generate_scenario_dataset_and_plot(fis)
    print("\nPhase 9 Water Demand FIS Analysis & Visualization Complete!")


if __name__ == "__main__":
    main()
