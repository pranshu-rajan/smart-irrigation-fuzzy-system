"""
Phase 8: Weather Stress Fuzzy Inference System Analysis & Visualization Script.

Generates:
1. 5 Pairwise 3D/2D Control Surfaces (reports/weather_stress/figures/):
   - temperature_humidity_surface.png
   - temperature_solar_surface.png
   - temperature_wind_surface.png
   - humidity_rainfall_surface.png
   - solar_rainfall_surface.png
2. Membership Function Visualizations (reports/weather_stress/figures/)
3. Step-by-Step Mamdani Inference Example (reports/weather_stress/figures/weather_stress_inference_example.png)
4. Weather Stress Dataset across 6 scenarios (data/processed/weather_stress.csv)
5. Scenario Comparison Visualization (reports/weather_stress/figures/weather_stress_scenarios.png)
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
from fuzzy_engine.weather_stress import WeatherStressFIS
from simulation.weather import WeatherEngine

FIGURES_DIR = PROJECT_ROOT / "reports" / "weather_stress" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

COLOR_PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]


def generate_control_surfaces(fis: WeatherStressFIS) -> None:
    """Generate the 5 required pairwise control surfaces and contours."""
    print("Generating 5 pairwise control surfaces...")

    # Grid definition (50x50 resolution for smooth rendering)
    n_pts = 50

    # 1. Temperature x Humidity (Nominal: Solar=500 W/m², Wind=3 m/s, Rain=0 mm)
    t_vals = np.linspace(10.0, 50.0, n_pts)
    h_vals = np.linspace(0.0, 100.0, n_pts)
    T, H = np.meshgrid(t_vals, h_vals)
    Z1 = np.zeros_like(T)
    for i in range(n_pts):
        for j in range(n_pts):
            Z1[i, j] = fis.evaluate(T[i, j], H[i, j], 500.0, 3.0, 0.0)

    fig = plt.figure(figsize=(9, 6), dpi=300)
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(T, H, Z1, cmap="coolwarm", edgecolor="none", alpha=0.9)
    ax.set_title("Weather Stress: Temperature × Humidity\n(Solar=500 W/m², Wind=3 m/s, Rain=0 mm)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Temperature [°C]", fontsize=9, labelpad=7)
    ax.set_ylabel("Relative Humidity [%]", fontsize=9, labelpad=7)
    ax.set_zlabel("Weather Stress [%]", fontsize=9, labelpad=7)
    ax.set_zlim(0, 100)
    ax.view_init(elev=28, azim=-120)
    fig.colorbar(surf, shrink=0.55, aspect=12, pad=0.08)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "temperature_humidity_surface.png", dpi=300)
    plt.close(fig)

    # 2. Temperature x Solar Radiation (Nominal: Humidity=50%, Wind=3 m/s, Rain=0 mm)
    s_vals = np.linspace(0.0, 1200.0, n_pts)
    T, S = np.meshgrid(t_vals, s_vals)
    Z2 = np.zeros_like(T)
    for i in range(n_pts):
        for j in range(n_pts):
            Z2[i, j] = fis.evaluate(T[i, j], 50.0, S[i, j], 3.0, 0.0)

    fig = plt.figure(figsize=(9, 6), dpi=300)
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(T, S, Z2, cmap="plasma", edgecolor="none", alpha=0.9)
    ax.set_title("Weather Stress: Temperature × Solar Radiation\n(Humidity=50%, Wind=3 m/s, Rain=0 mm)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Temperature [°C]", fontsize=9, labelpad=7)
    ax.set_ylabel("Solar Radiation [W/m²]", fontsize=9, labelpad=7)
    ax.set_zlabel("Weather Stress [%]", fontsize=9, labelpad=7)
    ax.set_zlim(0, 100)
    ax.view_init(elev=28, azim=-120)
    fig.colorbar(surf, shrink=0.55, aspect=12, pad=0.08)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "temperature_solar_surface.png", dpi=300)
    plt.close(fig)

    # 3. Temperature x Wind Speed (Nominal: Humidity=40%, Solar=600 W/m², Rain=0 mm)
    w_vals = np.linspace(0.0, 15.0, n_pts)
    T, W = np.meshgrid(t_vals, w_vals)
    Z3 = np.zeros_like(T)
    for i in range(n_pts):
        for j in range(n_pts):
            Z3[i, j] = fis.evaluate(T[i, j], 40.0, 600.0, W[i, j], 0.0)

    fig = plt.figure(figsize=(9, 6), dpi=300)
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(T, W, Z3, cmap="inferno", edgecolor="none", alpha=0.9)
    ax.set_title("Weather Stress: Temperature × Wind Speed\n(Humidity=40%, Solar=600 W/m², Rain=0 mm)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Temperature [°C]", fontsize=9, labelpad=7)
    ax.set_ylabel("Wind Speed [m/s]", fontsize=9, labelpad=7)
    ax.set_zlabel("Weather Stress [%]", fontsize=9, labelpad=7)
    ax.set_zlim(0, 100)
    ax.view_init(elev=28, azim=-120)
    fig.colorbar(surf, shrink=0.55, aspect=12, pad=0.08)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "temperature_wind_surface.png", dpi=300)
    plt.close(fig)

    # 4. Humidity x Rainfall (Nominal: Temp=35°C, Solar=600 W/m², Wind=4 m/s)
    r_vals = np.linspace(0.0, 50.0, n_pts)
    H, R = np.meshgrid(h_vals, r_vals)
    Z4 = np.zeros_like(H)
    for i in range(n_pts):
        for j in range(n_pts):
            Z4[i, j] = fis.evaluate(35.0, H[i, j], 600.0, 4.0, R[i, j])

    fig = plt.figure(figsize=(9, 6), dpi=300)
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(H, R, Z4, cmap="viridis", edgecolor="none", alpha=0.9)
    ax.set_title("Weather Stress: Humidity × Rainfall\n(Temp=35°C, Solar=600 W/m², Wind=4 m/s)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Relative Humidity [%]", fontsize=9, labelpad=7)
    ax.set_ylabel("Rainfall [mm]", fontsize=9, labelpad=7)
    ax.set_zlabel("Weather Stress [%]", fontsize=9, labelpad=7)
    ax.set_zlim(0, 100)
    ax.view_init(elev=28, azim=-120)
    fig.colorbar(surf, shrink=0.55, aspect=12, pad=0.08)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "humidity_rainfall_surface.png", dpi=300)
    plt.close(fig)

    # 5. Solar Radiation x Rainfall (Nominal: Temp=35°C, Humidity=30%, Wind=4 m/s)
    S, R = np.meshgrid(s_vals, r_vals)
    Z5 = np.zeros_like(S)
    for i in range(n_pts):
        for j in range(n_pts):
            Z5[i, j] = fis.evaluate(35.0, 30.0, S[i, j], 4.0, R[i, j])

    fig = plt.figure(figsize=(9, 6), dpi=300)
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(S, R, Z5, cmap="cividis", edgecolor="none", alpha=0.9)
    ax.set_title("Weather Stress: Solar Radiation × Rainfall\n(Temp=35°C, Humidity=30%, Wind=4 m/s)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Solar Radiation [W/m²]", fontsize=9, labelpad=7)
    ax.set_ylabel("Rainfall [mm]", fontsize=9, labelpad=7)
    ax.set_zlabel("Weather Stress [%]", fontsize=9, labelpad=7)
    ax.set_zlim(0, 100)
    ax.view_init(elev=28, azim=-120)
    fig.colorbar(surf, shrink=0.55, aspect=12, pad=0.08)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "solar_rainfall_surface.png", dpi=300)
    plt.close(fig)
    print("Saved all 5 surface plots successfully.")


def generate_membership_plots(fis: WeatherStressFIS) -> None:
    """Generate input and output membership function plots."""
    print("Generating Weather Stress membership function plots...")
    vars_to_plot = [
        (fis.temp_var, "temperature_membership.png"),
        (fis.hum_var, "humidity_membership.png"),
        (fis.solar_var, "solar_radiation_membership.png"),
        (fis.wind_var, "wind_speed_membership.png"),
        (fis.rain_var, "rainfall_membership.png"),
        (fis.stress_var, "weather_stress_membership.png"),
    ]
    for var, fname in vars_to_plot:
        fig, ax = plt.subplots(figsize=(8, 4.2), dpi=300)
        x = var.universe.points
        for idx, (sname, m_set) in enumerate(var.sets.items()):
            color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]
            y = m_set.evaluate(x)
            ax.plot(x, y, label=m_set.display_name, color=color, linewidth=2.2)
            ax.fill_between(x, 0, y, color=color, alpha=0.15)

        unit_str = f" [{var.unit}]" if var.unit else ""
        ax.set_title(f"{var.display_name}{unit_str}", fontsize=12, fontweight="bold")
        ax.set_xlabel(f"{var.display_name}{unit_str}", fontsize=10)
        ax.set_ylabel("Degree of Membership ($\\mu$)", fontsize=10)
        ax.set_xlim(var.universe.min_val, var.universe.max_val)
        ax.set_ylim(-0.02, 1.05)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="upper right", framealpha=0.9, fontsize=9)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / fname, dpi=300)
        plt.close(fig)
        print(f"Saved: {fname}")


def generate_inference_example(fis: WeatherStressFIS) -> None:
    """Generate representative step-by-step visual demonstration of Mamdani inference."""
    print("Generating representative Weather Stress inference visualization...")
    # Representative hot sunny summer afternoon:
    # Temp = 36.0°C (High), Humidity = 28.0% (Low), Solar = 820 W/m² (High), Wind = 5.2 m/s (Moderate), Rain = 0 mm (None)
    details = fis.evaluate_detailed(36.0, 28.0, 820.0, 5.2, 0.0)

    fig, axs = plt.subplots(6, 1, figsize=(9.5, 11), dpi=300)

    inputs = [
        ("Temperature = 36.0°C", fis.temp_var, 36.0, axs[0]),
        ("Humidity = 28.0%", fis.hum_var, 28.0, axs[1]),
        ("Solar Radiation = 820 W/m²", fis.solar_var, 820.0, axs[2]),
        ("Wind Speed = 5.2 m/s", fis.wind_var, 5.2, axs[3]),
        ("Rainfall = 0.0 mm", fis.rain_var, 0.0, axs[4]),
    ]

    for title, var, val, ax in inputs:
        x = var.universe.points
        for idx, (sname, m_set) in enumerate(var.sets.items()):
            color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]
            y = m_set.evaluate(x)
            ax.plot(x, y, label=m_set.display_name, color=color, lw=1.5)
        ax.axvline(val, color="black", linestyle="--", lw=1.8, label=f"Input: {val}")
        ax.set_title(title, fontsize=10, fontweight="bold", pad=4)
        ax.set_ylabel("$\\mu$", fontsize=8)
        ax.set_xlim(var.universe.min_val, var.universe.max_val)
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.legend(loc="upper right", fontsize=7, ncol=3)

    # Output subplot
    ax_out = axs[5]
    z = fis.z_grid
    agg_mu = np.zeros_like(z)
    for sname, beta in details["consequent_activations"].items():
        if beta > 0:
            clipped = np.minimum(beta, fis._output_mf_matrix[sname])
            ax_out.plot(z, clipped, linestyle=":", lw=1.5, label=f"{sname.title()} ($\\beta={beta:.2f}$)")
            agg_mu = np.maximum(agg_mu, clipped)

    ax_out.fill_between(z, 0, agg_mu, color="#e65100", alpha=0.25, label="Aggregated Fuzzy Set")
    ax_out.plot(z, agg_mu, color="#bf360c", lw=2.2)
    centroid = details["weather_stress"]
    ax_out.axvline(centroid, color="#d50000", lw=2.5, linestyle="-", label=f"Centroid $z^* = {centroid:.1f}\\%$")
    ax_out.set_title(f"Aggregated Output & Centroid Defuzzification: Weather Stress = {centroid:.1f}%", fontsize=10, fontweight="bold", pad=4)
    ax_out.set_xlabel("Weather Stress [%]", fontsize=9)
    ax_out.set_ylabel("$\\mu_{agg}(z)$", fontsize=8)
    ax_out.set_xlim(0, 100)
    ax_out.set_ylim(0, 1.05)
    ax_out.grid(True, linestyle=":", alpha=0.5)
    ax_out.legend(loc="upper left", fontsize=7.5)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "weather_stress_inference_example.png", dpi=300)
    plt.close(fig)
    print("Saved: weather_stress_inference_example.png")


def generate_scenario_dataset_and_plot(fis: WeatherStressFIS) -> pd.DataFrame:
    """Run weather simulation for all 6 scenarios, compute stress, and plot comparison."""
    print("Processing real weather scenario datasets...")
    scenarios = list(SimulationScenario)
    all_dfs = []

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    colors = {
        SimulationScenario.NORMAL: "#1f77b4",
        SimulationScenario.HOT_AND_DRY: "#ff7f0e",
        SimulationScenario.RAINY: "#2ca02c",
        SimulationScenario.CLOUDY: "#7f7f7f",
        SimulationScenario.HEATWAVE: "#d62728",
        SimulationScenario.WATER_SCARCITY: "#9467bd",
    }

    scenario_summary = {}

    for sc in scenarios:
        w_engine = WeatherEngine(scenario=sc, seed=42)
        df_w = w_engine.generate_timeline(duration_hours=24, timestep_minutes=1)

        t_arr = df_w["temperature"].values
        h_arr = df_w["humidity"].values
        s_arr = df_w["solar_radiation"].values
        w_arr = df_w["wind_speed"].values
        r_arr = df_w["rainfall"].values

        stresses = fis.evaluate_array(t_arr, h_arr, s_arr, w_arr, r_arr)
        df_w["weather_stress"] = np.round(stresses, 2)
        df_w["scenario"] = sc.value
        all_dfs.append(df_w)

        hrs = np.arange(len(stresses)) / 60.0
        ax.plot(hrs, stresses, label=sc.value, color=colors[sc], lw=1.8)

        scenario_summary[sc.value] = {
            "mean": float(np.mean(stresses)),
            "min": float(np.min(stresses)),
            "max": float(np.max(stresses)),
            "peak_time_hr": float(hrs[np.argmax(stresses)]),
        }

    ax.set_title("24-Hour Atmospheric Weather Stress Dynamics Across 6 Scenarios", fontsize=12, fontweight="bold")
    ax.set_xlabel("Simulation Time [hours]", fontsize=10, fontweight="semibold")
    ax.set_ylabel("Weather Stress [%]", fontsize=10, fontweight="semibold")
    ax.set_xlim(0, 24)
    ax.set_ylim(-2, 102)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", framealpha=0.92, fontsize=9)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "weather_stress_scenarios.png", dpi=300)
    plt.close(fig)
    print("Saved: weather_stress_scenarios.png")

    # Combine and save dataset
    df_combined = pd.concat(all_dfs, ignore_index=True)
    out_cols = [
        "timestamp", "scenario", "temperature", "humidity",
        "solar_radiation", "wind_speed", "rainfall", "weather_stress"
    ]
    df_out = df_combined[out_cols]
    out_csv = DATA_PROCESSED_DIR / "weather_stress.csv"
    df_out.to_csv(out_csv, index=False)
    print(f"Generated {out_csv.name} with {len(df_out)} records.")

    print("\n--- Scenario Weather Stress Summary ---")
    for sc_name, s in scenario_summary.items():
        print(f"Scenario: {sc_name:15s} | Mean: {s['mean']:.2f}% | Min: {s['min']:.2f}% | Max: {s['max']:.2f}% | Peak at: {s['peak_time_hr']:.1f}h")

    return df_out


def main():
    fis = WeatherStressFIS()
    generate_control_surfaces(fis)
    generate_membership_plots(fis)
    generate_inference_example(fis)
    generate_scenario_dataset_and_plot(fis)
    print("\nPhase 8 Weather Stress FIS Analysis & Visualization Complete!")


if __name__ == "__main__":
    main()
