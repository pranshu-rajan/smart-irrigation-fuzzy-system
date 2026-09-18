"""
Phase 10: Main Irrigation Fuzzy Inference System Analysis & Visualization Script.

Generates:
1. 5 Pairwise 3D Control Surfaces & 2D Contour Maps (reports/main_irrigation/figures/):
   - soil_stress_vs_moisture_error_surface.png / contour
   - water_demand_vs_moisture_error_surface.png / contour
   - weather_stress_vs_moisture_error_surface.png / contour
   - soil_stress_vs_water_demand_surface.png / contour
   - weather_stress_vs_soil_stress_surface.png / contour
2. Membership Function Visualizations (reports/main_irrigation/figures/):
   - mf_soil_stress.png
   - mf_weather_stress.png
   - mf_water_demand.png
   - mf_moisture_error.png
   - mf_irrigation_command.png
3. Step-by-Step Mamdani Inference Example (reports/main_irrigation/figures/main_irrigation_inference_example.png)
4. Comprehensive 25,920-Record Multizone Integration Dataset (data/processed/main_irrigation.csv)
5. Multizone Diurnal Scenario Comparison Plot (reports/main_irrigation/figures/main_irrigation_scenarios.png)
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import pandas as pd

from config.schemas import SimulationScenario
from fuzzy_engine.soil_stress import SoilStressFIS
from fuzzy_engine.weather_stress import WeatherStressFIS
from fuzzy_engine.water_demand import WaterDemandFIS
from fuzzy_engine.main_irrigation import MainIrrigationFIS
from simulation.weather import WeatherEngine
from simulation.engine import SimulationEngine

FIGURES_DIR = PROJECT_ROOT / "reports" / "main_irrigation" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

COLOR_PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]


def generate_control_surfaces(fis: MainIrrigationFIS) -> None:
    """Generate the 5 pairwise 3D control surfaces and 2D contour maps."""
    print("Generating 5 pairwise 3D control surfaces and 2D contours...")
    n_pts = 50

    ss_vals = np.linspace(0.0, 100.0, n_pts)
    ws_vals = np.linspace(0.0, 100.0, n_pts)
    wd_vals = np.linspace(0.0, 100.0, n_pts)
    me_vals = np.linspace(-30.0, 30.0, n_pts)

    surfaces = [
        # (X_vals, Y_vals, X_name, Y_name, title, filename_base, fixed_desc, eval_func)
        (
            ss_vals, me_vals, "Soil Stress [%]", "Moisture Error $e(t)$ [%]",
            "Irrigation Command: Soil Stress × Moisture Error",
            "soil_stress_vs_moisture_error",
            "Weather Stress = 40%, Water Demand = 50%",
            lambda x, y: fis.evaluate(soil_stress=x, weather_stress=40.0, water_demand=50.0, moisture_error=y),
            "viridis"
        ),
        (
            wd_vals, me_vals, "Water Demand [%]", "Moisture Error $e(t)$ [%]",
            "Irrigation Command: Water Demand × Moisture Error",
            "water_demand_vs_moisture_error",
            "Soil Stress = 40%, Weather Stress = 40%",
            lambda x, y: fis.evaluate(soil_stress=40.0, weather_stress=40.0, water_demand=x, moisture_error=y),
            "magma"
        ),
        (
            ws_vals, me_vals, "Weather Stress [%]", "Moisture Error $e(t)$ [%]",
            "Irrigation Command: Weather Stress × Moisture Error",
            "weather_stress_vs_moisture_error",
            "Soil Stress = 40%, Water Demand = 40%",
            lambda x, y: fis.evaluate(soil_stress=40.0, weather_stress=x, water_demand=40.0, moisture_error=y),
            "plasma"
        ),
        (
            ss_vals, wd_vals, "Soil Stress [%]", "Water Demand [%]",
            "Irrigation Command: Soil Stress × Water Demand",
            "soil_stress_vs_water_demand",
            "Moisture Error = +5%, Weather Stress = 40%",
            lambda x, y: fis.evaluate(soil_stress=x, weather_stress=40.0, water_demand=y, moisture_error=5.0),
            "coolwarm"
        ),
        (
            ws_vals, ss_vals, "Weather Stress [%]", "Soil Stress [%]",
            "Irrigation Command: Weather Stress × Soil Stress",
            "weather_stress_vs_soil_stress",
            "Moisture Error = +5%, Water Demand = 50%",
            lambda x, y: fis.evaluate(soil_stress=y, weather_stress=x, water_demand=50.0, moisture_error=5.0),
            "inferno"
        ),
    ]

    for X_arr, Y_arr, x_label, y_label, title, fname_base, fixed_desc, eval_fn, cmap in surfaces:
        X, Y = np.meshgrid(X_arr, Y_arr)
        Z = np.zeros_like(X)
        for i in range(n_pts):
            for j in range(n_pts):
                Z[i, j] = eval_fn(X[i, j], Y[i, j])

        # 3D Surface
        fig = plt.figure(figsize=(9, 6), dpi=300)
        ax = fig.add_subplot(111, projection="3d")
        surf = ax.plot_surface(X, Y, Z, cmap=cmap, edgecolor="none", alpha=0.92)
        ax.set_title(f"{title}\n({fixed_desc})", fontsize=11, fontweight="bold")
        ax.set_xlabel(x_label, fontsize=9, labelpad=7)
        ax.set_ylabel(y_label, fontsize=9, labelpad=7)
        ax.set_zlabel("Irrigation Command [%]", fontsize=9, labelpad=7)
        ax.set_zlim(0, 100)
        ax.view_init(elev=28, azim=-125)
        fig.colorbar(surf, shrink=0.55, aspect=12, pad=0.08)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / f"{fname_base}_surface.png", dpi=300)
        plt.close(fig)

        # 2D Contour
        fig, ax = plt.subplots(figsize=(7.5, 6), dpi=300)
        cs = ax.contourf(X, Y, Z, levels=20, cmap=cmap)
        cbar = fig.colorbar(cs, ax=ax)
        cbar.set_label("Irrigation Command [%]", fontsize=9)
        lines = ax.contour(X, Y, Z, levels=10, colors="white", alpha=0.35, linewidths=0.8)
        ax.clabel(lines, inline=True, fontsize=8, fmt="%.0f%%")
        ax.set_title(f"{title}\n({fixed_desc})", fontsize=11, fontweight="bold")
        ax.set_xlabel(x_label, fontsize=9)
        ax.set_ylabel(y_label, fontsize=9)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / f"{fname_base}_contour.png", dpi=300)
        plt.close(fig)

    print("Saved 5 pairwise 3D control surfaces and 2D contour maps successfully.")


def generate_membership_plots(fis: MainIrrigationFIS) -> None:
    """Generate individual membership function plots for all 4 inputs and 1 output."""
    print("Generating membership function figures...")
    vars_to_plot = [
        (fis.soil_stress_var, "Soil Stress [%]", "mf_soil_stress.png"),
        (fis.weather_stress_var, "Weather Stress [%]", "mf_weather_stress.png"),
        (fis.water_demand_var, "Crop Water Demand [%]", "mf_water_demand.png"),
        (fis.moisture_error_var, "Moisture Tracking Error $e(t)$ [%]", "mf_moisture_error.png"),
        (fis.command_var, "Normalized Irrigation Command [%]", "mf_irrigation_command.png"),
    ]

    for var, xlabel, fname in vars_to_plot:
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


def generate_inference_example(fis: MainIrrigationFIS) -> None:
    """Generate comprehensive Mamdani step-by-step inference diagram."""
    print("Generating Mamdani inference step-by-step example diagram...")
    # Representative inputs:
    # Soil Stress = 65% (moderate/high), Weather Stress = 55% (moderate/high),
    # Water Demand = 60% (moderate/high), Moisture Error = +8% (positive deficit)
    ss_in = 65.0
    ws_in = 55.0
    wd_in = 60.0
    me_in = 8.0

    detailed = fis.evaluate_detailed(ss_in, ws_in, wd_in, me_in)
    cmd_val = detailed["irrigation_command"]

    fig, axs = plt.subplots(3, 2, figsize=(12, 11), dpi=300)

    # 1. Soil Stress Fuzzification
    ax_ss = axs[0, 0]
    x_ss = np.linspace(0, 100, 300)
    for idx, (sname, s) in enumerate(fis.soil_stress_var.sets.items()):
        y = s.evaluate(x_ss)
        ax_ss.plot(x_ss, y, label=sname.title(), color=COLOR_PALETTE[idx % len(COLOR_PALETTE)], lw=1.6)
    ax_ss.axvline(ss_in, color="black", linestyle="--", lw=1.8, label=f"Input = {ss_in:.1f}%")
    for sname, mu in detailed["soil_stress_membership"].items():
        if mu > 0:
            ax_ss.plot(ss_in, mu, "ro", markersize=6)
            ax_ss.annotate(f"{sname}: {mu:.2f}", (ss_in + 2.0, mu + 0.03), fontsize=7.5)
    ax_ss.set_title("Step 1a: Soil Stress Fuzzification", fontsize=10, fontweight="bold")
    ax_ss.set_xlabel("Soil Stress [%]", fontsize=8.5)
    ax_ss.set_ylabel("$\\mu(x)$", fontsize=8.5)
    ax_ss.set_ylim(-0.05, 1.1)
    ax_ss.grid(True, linestyle=":", alpha=0.5)
    ax_ss.legend(loc="upper right", fontsize=7)

    # 2. Weather Stress Fuzzification
    ax_ws = axs[0, 1]
    x_ws = np.linspace(0, 100, 300)
    for idx, (sname, s) in enumerate(fis.weather_stress_var.sets.items()):
        y = s.evaluate(x_ws)
        ax_ws.plot(x_ws, y, label=sname.title(), color=COLOR_PALETTE[idx % len(COLOR_PALETTE)], lw=1.6)
    ax_ws.axvline(ws_in, color="black", linestyle="--", lw=1.8, label=f"Input = {ws_in:.1f}%")
    for sname, mu in detailed["weather_stress_membership"].items():
        if mu > 0:
            ax_ws.plot(ws_in, mu, "ro", markersize=6)
            ax_ws.annotate(f"{sname}: {mu:.2f}", (ws_in + 2.0, mu + 0.03), fontsize=7.5)
    ax_ws.set_title("Step 1b: Weather Stress Fuzzification", fontsize=10, fontweight="bold")
    ax_ws.set_xlabel("Weather Stress [%]", fontsize=8.5)
    ax_ws.set_ylabel("$\\mu(x)$", fontsize=8.5)
    ax_ws.set_ylim(-0.05, 1.1)
    ax_ws.grid(True, linestyle=":", alpha=0.5)
    ax_ws.legend(loc="upper right", fontsize=7)

    # 3. Water Demand Fuzzification
    ax_wd = axs[1, 0]
    x_wd = np.linspace(0, 100, 300)
    for idx, (sname, s) in enumerate(fis.water_demand_var.sets.items()):
        y = s.evaluate(x_wd)
        ax_wd.plot(x_wd, y, label=sname.title(), color=COLOR_PALETTE[idx % len(COLOR_PALETTE)], lw=1.6)
    ax_wd.axvline(wd_in, color="black", linestyle="--", lw=1.8, label=f"Input = {wd_in:.1f}%")
    for sname, mu in detailed["water_demand_membership"].items():
        if mu > 0:
            ax_wd.plot(wd_in, mu, "ro", markersize=6)
            ax_wd.annotate(f"{sname}: {mu:.2f}", (wd_in + 2.0, mu + 0.03), fontsize=7.5)
    ax_wd.set_title("Step 1c: Water Demand Fuzzification", fontsize=10, fontweight="bold")
    ax_wd.set_xlabel("Water Demand [%]", fontsize=8.5)
    ax_wd.set_ylabel("$\\mu(x)$", fontsize=8.5)
    ax_wd.set_ylim(-0.05, 1.1)
    ax_wd.grid(True, linestyle=":", alpha=0.5)
    ax_wd.legend(loc="upper right", fontsize=7)

    # 4. Moisture Error Fuzzification
    ax_me = axs[1, 1]
    x_me = np.linspace(-30, 30, 300)
    for idx, (sname, s) in enumerate(fis.moisture_error_var.sets.items()):
        y = s.evaluate(x_me)
        ax_me.plot(x_me, y, label=sname.title(), color=COLOR_PALETTE[idx % len(COLOR_PALETTE)], lw=1.6)
    ax_me.axvline(me_in, color="black", linestyle="--", lw=1.8, label=f"Input = {me_in:+.1f}%")
    for sname, mu in detailed["moisture_error_membership"].items():
        if mu > 0:
            ax_me.plot(me_in, mu, "ro", markersize=6)
            ax_me.annotate(f"{sname}: {mu:.2f}", (me_in + 1.2, mu + 0.03), fontsize=7.5)
    ax_me.set_title("Step 1d: Moisture Tracking Error $e(t)$ Fuzzification", fontsize=10, fontweight="bold")
    ax_me.set_xlabel("Moisture Error $e(t)$ [%]", fontsize=8.5)
    ax_me.set_ylabel("$\\mu(x)$", fontsize=8.5)
    ax_me.set_ylim(-0.05, 1.1)
    ax_me.grid(True, linestyle=":", alpha=0.5)
    ax_me.legend(loc="upper right", fontsize=7)

    # 5. Output Rule Implication & Centroid Defuzzification
    ax_out = axs[2, 0]
    z_grid = fis.z_grid
    for idx, (sname, s) in enumerate(fis.command_var.sets.items()):
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
    ax_out.axvline(cmd_val, color="navy", linestyle="-", lw=2.4, label=f"Centroid Output $z^* = {cmd_val:.1f}\\%$")

    ax_out.set_title("Step 2-4: Rule Aggregation & Centroid Defuzzification", fontsize=10, fontweight="bold")
    ax_out.set_xlabel("Irrigation Command [%]", fontsize=8.5)
    ax_out.set_ylabel("$\\mu_{agg}(z)$", fontsize=8.5)
    ax_out.set_xlim(0, 100)
    ax_out.set_ylim(0, 1.05)
    ax_out.grid(True, linestyle=":", alpha=0.5)
    ax_out.legend(loc="upper left", fontsize=7.5)

    # 6. Active Rules Summary Table in sixth subplot
    ax_tbl = axs[2, 1]
    ax_tbl.axis("off")
    tbl_text = "ACTIVE RULES & ACTIVATION WEIGHTS:\n" + "-" * 55 + "\n"
    for r in detailed["active_rules"][:6]:
        tbl_text += f"Rule {r['rule_id']:2d}: {r['description']}\n"
        tbl_text += f"  Firing Strength $\\beta = {r['weight']:.2f}$ -> Consequent: {r['consequent'].upper()}\n\n"
    tbl_text += f"Final Centroid Irrigation Command: {cmd_val:.2f}%\n"
    ax_tbl.text(0.02, 0.98, tbl_text, transform=ax_tbl.transAxes, verticalalignment="top",
                fontsize=8, family="monospace", bbox=dict(boxstyle="round", facecolor="#f8f9fa", alpha=0.9))

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "main_irrigation_inference_example.png", dpi=300)
    plt.close(fig)
    print("Saved: main_irrigation_inference_example.png")


def generate_multizone_dataset_and_plot(
    fis_main: MainIrrigationFIS,
    fis_soil: SoilStressFIS,
    fis_weather: WeatherStressFIS,
    fis_water: WaterDemandFIS,
) -> pd.DataFrame:
    """
    Run multizone simulation pipeline across 6 scenarios and 3 zones,
    evaluate MainIrrigationFIS, compile data/processed/main_irrigation.csv (25,920 records),
    and plot diurnal comparison curves.
    """
    print("Executing full multizone simulation pipeline across 6 scenarios...")
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

    zone_titles = {
        1: "Zone 1: Tomato (Mid-season, Kc=1.15, Loam Soil)",
        2: "Zone 2: Wheat (Development, Kc=0.85, Sandy Soil)",
        3: "Zone 3: Maize (Mid-season, Kc=1.20, Clay Soil)",
    }

    fig, axs = plt.subplots(3, 1, figsize=(11, 8.5), dpi=300, sharex=True)

    t0_start = time.perf_counter()

    for sc in scenarios:
        # Step 1: Weather timeline
        w_engine = WeatherEngine(scenario=sc, seed=42)
        weather_df = w_engine.generate_timeline(duration_hours=24, timestep_minutes=1)

        # Weather stress
        w_stress_arr = fis_weather.evaluate_array(
            weather_df["temperature"].values,
            weather_df["humidity"].values,
            weather_df["solar_radiation"].values,
            weather_df["wind_speed"].values,
            weather_df["rainfall"].values,
        )

        # Step 2: SimulationEngine for Multizone Soil Water Dynamics
        sim_engine = SimulationEngine(scenario=sc, seed=42)
        sim_df = sim_engine.run(duration_hours=24, timestep_minutes=1)
        sim_df["scenario"] = sc.value

        # Step 3: Compute Subsystem FIS outputs
        # Soil stress
        soil_stress_arr = fis_soil.evaluate_array(sim_df["rsm"].values, sim_df["moisture_error"].values)
        sim_df["soil_stress"] = np.round(soil_stress_arr, 2)

        # Water demand (crop evapotranspiration and deficit)
        crop_deficit_arr = np.maximum(0.0, sim_df["etc"].values - sim_df["effective_rainfall"].values)
        sim_df["crop_water_deficit"] = np.round(crop_deficit_arr, 6)

        water_demand_arr = fis_water.evaluate_array(
            sim_df["etc"].values,
            crop_deficit_arr,
            sim_df["effective_rainfall"].values,
        )
        sim_df["water_demand"] = np.round(water_demand_arr, 2)

        # Broadcast weather stress across the 3 zones (step-aligned)
        # sim_df is sorted by (step, zone_id)
        # Each step has 3 zones
        sim_df["weather_stress"] = np.repeat(np.round(w_stress_arr, 2), 3)

        # Step 4: Evaluate Main Irrigation FIS
        t_batch_start = time.perf_counter()
        cmd_arr = fis_main.evaluate_array(
            sim_df["soil_stress"].values,
            sim_df["weather_stress"].values,
            sim_df["water_demand"].values,
            sim_df["moisture_error"].values,
        )
        t_batch_elapsed = time.perf_counter() - t_batch_start

        sim_df["irrigation_command"] = np.round(cmd_arr, 2)
        all_dfs.append(sim_df)

        # Plot curves for each zone
        for zid in [1, 2, 3]:
            sub = sim_df[sim_df["zone_id"] == zid]
            hrs = np.arange(len(sub)) / 60.0
            axs[zid - 1].plot(hrs, sub["irrigation_command"].values, label=sc.value, color=scenario_colors[sc], lw=1.6)

    total_integration_time = time.perf_counter() - t0_start

    for zid in [1, 2, 3]:
        axs[zid - 1].set_title(zone_titles[zid], fontsize=11, fontweight="bold")
        axs[zid - 1].set_ylabel("Irrigation Command [%]", fontsize=9.5)
        axs[zid - 1].set_ylim(-2, 102)
        axs[zid - 1].grid(True, linestyle="--", alpha=0.5)

    axs[0].legend(loc="upper right", ncol=3, fontsize=8, framealpha=0.92)
    axs[2].set_xlabel("Simulation Time [hours]", fontsize=10, fontweight="semibold")

    sc_path = FIGURES_DIR / "main_irrigation_scenarios.png"
    plt.tight_layout()
    plt.savefig(sc_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {sc_path.name}")

    # Combine all scenario records
    df_combined = pd.concat(all_dfs, ignore_index=True)
    out_cols = [
        "timestamp", "scenario", "zone_id", "crop", "soil_type",
        "soil_moisture", "rsm", "moisture_error",
        "soil_stress", "weather_stress", "water_demand",
        "et0", "etc", "rainfall", "effective_rainfall", "crop_water_deficit",
        "irrigation_command"
    ]
    df_out = df_combined[out_cols]
    out_csv = DATA_PROCESSED_DIR / "main_irrigation.csv"
    df_out.to_csv(out_csv, index=False)
    print(f"Generated {out_csv.name} with {len(df_out)} records in {total_integration_time:.2f} seconds.")

    # Print Scenario Summaries
    print("\n============================================================")
    print("SCENARIO-WISE IRRIGATION COMMAND SUMMARY")
    print("============================================================")
    for sc in scenarios:
        sub_sc = df_out[df_out["scenario"] == sc.value]
        mean_cmd = sub_sc["irrigation_command"].mean()
        min_cmd = sub_sc["irrigation_command"].min()
        max_cmd = sub_sc["irrigation_command"].max()
        print(f"Scenario: {sc.value:15s} | Mean Command: {mean_cmd:5.2f}% | Min: {min_cmd:5.2f}% | Max: {max_cmd:5.2f}%")

    print("\n============================================================")
    print("ZONE-WISE IRRIGATION COMMAND SUMMARY")
    print("============================================================")
    for zid in [1, 2, 3]:
        sub_z = df_out[df_out["zone_id"] == zid]
        crop = sub_z["crop"].iloc[0]
        soil = sub_z["soil_type"].iloc[0]
        mean_cmd = sub_z["irrigation_command"].mean()
        min_cmd = sub_z["irrigation_command"].min()
        max_cmd = sub_z["irrigation_command"].max()
        print(f"Zone {zid} ({crop} / {soil}): Mean={mean_cmd:5.2f}%, Min={min_cmd:5.2f}%, Max={max_cmd:5.2f}%")

    return df_out


def main():
    fis_soil = SoilStressFIS()
    fis_weather = WeatherStressFIS()
    fis_water = WaterDemandFIS()
    fis_main = MainIrrigationFIS()

    generate_control_surfaces(fis_main)
    generate_membership_plots(fis_main)
    generate_inference_example(fis_main)
    generate_multizone_dataset_and_plot(fis_main, fis_soil, fis_weather, fis_water)

    # Measure benchmarks
    t0 = time.perf_counter()
    for _ in range(1000):
        fis_main.evaluate(50.0, 50.0, 50.0, 5.0)
    scalar_time = (time.perf_counter() - t0) / 1000.0 * 1000.0  # ms
    print(f"\nScalar evaluation time: {scalar_time:.4f} ms / evaluation")
    print("Phase 10 Main Irrigation FIS Analysis & Visualization Complete!")


if __name__ == "__main__":
    main()
