"""
Phase 7: Soil Stress Fuzzy Inference System Analysis & Visualization Script.

Generates:
1. 3D Control Surface (reports/soil_stress/figures/soil_stress_surface.png)
2. 2D Contour Map (reports/soil_stress/figures/soil_stress_contour.png)
3. Input/Output Membership Plots (reports/soil_stress/figures/)
4. Step-by-Step Mamdani Inference Example (reports/soil_stress/figures/soil_stress_inference_example.png)
5. Soil Stress Dataset (data/processed/soil_stress.csv)
6. Multizone Scenario Comparison (reports/soil_stress/figures/soil_stress_scenarios.png)
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

from fuzzy_engine.soil_stress import SoilStressFIS
from config.schemas import SimulationScenario
from simulation.engine import SimulationEngine

FIGURES_DIR = PROJECT_ROOT / "reports" / "soil_stress" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Colors
COLOR_PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]


def generate_control_surface_and_contour(fis: SoilStressFIS) -> None:
    """Generate 3D surface and 2D contour maps of Soil Stress over RSM and Moisture Error."""
    print("Generating 3D Control Surface and 2D Contour Map...")
    rsm_vals = np.linspace(0.0, 1.0, 60)
    err_vals = np.linspace(-30.0, 30.0, 60)
    R, E = np.meshgrid(rsm_vals, err_vals)
    Z = fis.evaluate_array(R, E)

    # 1. 3D Surface Plot
    fig = plt.figure(figsize=(10, 7), dpi=300)
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(
        R, E, Z,
        cmap="viridis",
        edgecolor="none",
        alpha=0.92,
        antialiased=True,
    )
    ax.set_title("Soil Stress Control Surface (Mamdani Centroid)", fontsize=13, fontweight="bold", pad=15)
    ax.set_xlabel("Relative Soil Moisture (RSM) [0 - 1]", fontsize=10, labelpad=8)
    ax.set_ylabel("Moisture Error $e(t)$ [%]", fontsize=10, labelpad=8)
    ax.set_zlabel("Soil Stress [%]", fontsize=10, labelpad=8)
    ax.set_zlim(0, 100)
    ax.view_init(elev=28, azim=-125)
    cbar = fig.colorbar(surf, ax=ax, shrink=0.55, aspect=12, pad=0.08)
    cbar.set_label("Soil Stress [%]", fontsize=9)

    surface_path = FIGURES_DIR / "soil_stress_surface.png"
    plt.tight_layout()
    plt.savefig(surface_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {surface_path.name}")

    # 2. 2D Contour Plot
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    cp = ax.contourf(R, E, Z, levels=20, cmap="viridis")
    cbar = fig.colorbar(cp, ax=ax)
    cbar.set_label("Soil Stress [%]", fontsize=10)
    lines = ax.contour(R, E, Z, levels=10, colors="white", alpha=0.4, linewidths=0.8)
    ax.clabel(lines, inline=True, fontsize=8, fmt="%.0f%%")

    ax.set_title("Soil Stress Contour Map", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Relative Soil Moisture (RSM) [0 = WP, 1 = FC]", fontsize=10, fontweight="semibold")
    ax.set_ylabel("Moisture Error $e(t) = \\theta_{target} - \\theta(t)$ [%]", fontsize=10, fontweight="semibold")
    ax.grid(True, linestyle="--", alpha=0.4)

    # Annotate critical regimes
    ax.text(0.1, 22, "Extreme Stress\n(Low RSM + Deficit)", color="white", fontsize=9, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="red", alpha=0.6))
    ax.text(0.7, -22, "Minimal Stress\n(High RSM + Excess)", color="white", fontsize=9, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="navy", alpha=0.6))

    contour_path = FIGURES_DIR / "soil_stress_contour.png"
    plt.tight_layout()
    plt.savefig(contour_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {contour_path.name}")


def generate_membership_plots(fis: SoilStressFIS) -> None:
    """Generate input and output membership function plots."""
    print("Generating membership function plots for Soil Stress FIS...")
    for var, fname in [(fis.rsm_var, "rsm_membership.png"),
                       (fis.error_var, "moisture_error_membership.png"),
                       (fis.stress_var, "soil_stress_membership.png")]:
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


def generate_inference_example(fis: SoilStressFIS) -> None:
    """Generate a step-by-step visual demonstration of Mamdani inference and centroid defuzzification."""
    print("Generating representative Mamdani inference visualization...")
    # Example input: Mild drought condition: RSM = 0.28 (Dry/Very Dry), Error = +8.0% (Positive)
    rsm_in = 0.28
    err_in = 8.0
    details = fis.evaluate_detailed(rsm_in, err_in)

    fig, axs = plt.subplots(3, 1, figsize=(9, 8), dpi=300)

    # Subplot 1: RSM fuzzification
    x_rsm = fis.rsm_var.universe.points
    for idx, (sname, m_set) in enumerate(fis.rsm_var.sets.items()):
        color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]
        y = m_set.evaluate(x_rsm)
        axs[0].plot(x_rsm, y, label=m_set.display_name, color=color, lw=1.8)
    axs[0].axvline(rsm_in, color="black", linestyle="--", lw=2, label=f"Input RSM = {rsm_in}")
    axs[0].set_title(f"1. Input Fuzzification: RSM = {rsm_in}", fontsize=11, fontweight="bold")
    axs[0].set_ylabel("$\\mu(RSM)$", fontsize=9)
    axs[0].set_xlim(0, 1)
    axs[0].grid(True, linestyle=":", alpha=0.6)
    axs[0].legend(loc="upper right", fontsize=8)

    # Subplot 2: Moisture Error fuzzification
    x_err = fis.error_var.universe.points
    for idx, (sname, m_set) in enumerate(fis.error_var.sets.items()):
        color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]
        y = m_set.evaluate(x_err)
        axs[1].plot(x_err, y, label=m_set.display_name, color=color, lw=1.8)
    axs[1].axvline(err_in, color="black", linestyle="--", lw=2, label=f"Input Error = {err_in}%")
    axs[1].set_title(f"2. Input Fuzzification: Moisture Error = {err_in}%", fontsize=11, fontweight="bold")
    axs[1].set_ylabel("$\\mu(Error)$", fontsize=9)
    axs[1].set_xlim(-30, 30)
    axs[1].grid(True, linestyle=":", alpha=0.6)
    axs[1].legend(loc="upper right", fontsize=8)

    # Subplot 3: Aggregated Output and Centroid
    z = fis.z_grid
    agg_mu = np.zeros_like(z)
    for sname, beta in details["consequent_activations"].items():
        if beta > 0:
            clipped = np.minimum(beta, fis._output_mf_matrix[sname])
            axs[2].plot(z, clipped, linestyle=":", lw=1.5, label=f"{sname.title()} ($\\beta={beta:.2f}$)")
            agg_mu = np.maximum(agg_mu, clipped)

    axs[2].fill_between(z, 0, agg_mu, color="#9c27b0", alpha=0.25, label="Aggregated Fuzzy Area")
    axs[2].plot(z, agg_mu, color="#7b1fa2", lw=2.2)
    centroid = details["soil_stress"]
    axs[2].axvline(centroid, color="#d32f2f", lw=2.5, linestyle="-", label=f"Centroid $z^* = {centroid:.1f}\\%$")
    axs[2].set_title(f"3. Mamdani Aggregation & Centroid Defuzzification: Soil Stress = {centroid:.1f}%", fontsize=11, fontweight="bold")
    axs[2].set_xlabel("Soil Stress [%]", fontsize=9)
    axs[2].set_ylabel("$\\mu_{agg}(z)$", fontsize=9)
    axs[2].set_xlim(0, 100)
    axs[2].set_ylim(0, 1.05)
    axs[2].grid(True, linestyle=":", alpha=0.6)
    axs[2].legend(loc="upper left", fontsize=8)

    inf_path = FIGURES_DIR / "soil_stress_inference_example.png"
    plt.tight_layout()
    plt.savefig(inf_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {inf_path.name}")


def process_soil_water_balance_dataset(fis: SoilStressFIS) -> pd.DataFrame:
    """Process Phase 5 soil water balance dataset to generate data/processed/soil_stress.csv."""
    print("Processing simulation soil water balance dataset...")
    swb_path = DATA_PROCESSED_DIR / "soil_water_balance.csv"
    if not swb_path.exists():
        raise FileNotFoundError(f"Missing required dataset: {swb_path}")

    df_swb = pd.read_csv(swb_path)

    # Compute Soil Stress for every row
    rsm_arr = df_swb["rsm"].values
    err_arr = df_swb["moisture_error"].values
    stress_arr = fis.evaluate_array(rsm_arr, err_arr)

    df_stress = pd.DataFrame({
        "timestamp": df_swb["timestamp"],
        "zone_id": df_swb["zone_id"],
        "crop": df_swb["crop"],
        "soil_type": df_swb["soil_type"],
        "soil_moisture": df_swb["soil_moisture"],
        "rsm": df_swb["rsm"],
        "moisture_error": df_swb["moisture_error"],
        "soil_stress": np.round(stress_arr, 2),
        "fc": df_swb["field_capacity"],
        "wp": df_swb["wilting_point"],
        "target_moisture": df_swb["target_moisture"],
        "root_depth": df_swb["root_depth_m"],
        "etc": df_swb["etc"],
        "effective_rainfall": df_swb["effective_rainfall"],
    })

    out_csv = DATA_PROCESSED_DIR / "soil_stress.csv"
    df_stress.to_csv(out_csv, index=False)
    print(f"Generated {out_csv.name} with {len(df_stress)} records.")
    return df_stress


def generate_scenario_comparison(fis: SoilStressFIS) -> None:
    """Run Multizone simulation across all 6 weather scenarios and plot Soil Stress curves."""
    print("Generating scenario comparison across 6 scenarios...")
    scenarios = list(SimulationScenario)

    fig, axs = plt.subplots(3, 1, figsize=(11, 8.5), dpi=300, sharex=True)
    colors = {
        SimulationScenario.NORMAL: "#1f77b4",
        SimulationScenario.HOT_AND_DRY: "#ff7f0e",
        SimulationScenario.RAINY: "#2ca02c",
        SimulationScenario.CLOUDY: "#7f7f7f",
        SimulationScenario.HEATWAVE: "#d62728",
        SimulationScenario.WATER_SCARCITY: "#9467bd",
    }

    zone_names = {1: "Zone 1: Tomato (Loam)", 2: "Zone 2: Wheat (Sandy)", 3: "Zone 3: Maize (Clay)"}

    for sc in scenarios:
        engine = SimulationEngine(scenario=sc)
        df_sc = engine.run(duration_hours=24)

        for zid in [1, 2, 3]:
            df_z = df_sc[df_sc["zone_id"] == zid].copy()
            stresses = fis.evaluate_array(df_z["rsm"].values, df_z["moisture_error"].values)
            hrs = np.arange(len(stresses)) / 60.0
            axs[zid - 1].plot(hrs, stresses, label=sc.value, color=colors[sc], lw=1.6)

    for zid in [1, 2, 3]:
        axs[zid - 1].set_title(zone_names[zid], fontsize=11, fontweight="bold")
        axs[zid - 1].set_ylabel("Soil Stress [%]", fontsize=9)
        axs[zid - 1].set_ylim(-2, 102)
        axs[zid - 1].grid(True, linestyle="--", alpha=0.5)

    axs[0].legend(loc="upper right", ncol=3, fontsize=8, framealpha=0.9)
    axs[2].set_xlabel("Simulation Time [hours]", fontsize=10, fontweight="semibold")

    sc_path = FIGURES_DIR / "soil_stress_scenarios.png"
    plt.tight_layout()
    plt.savefig(sc_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {sc_path.name}")


def main():
    fis = SoilStressFIS()
    generate_control_surface_and_contour(fis)
    generate_membership_plots(fis)
    generate_inference_example(fis)
    df_stress = process_soil_water_balance_dataset(fis)
    generate_scenario_comparison(fis)

    print("\n--- Zone-Wise Stress Summary (Baseline) ---")
    for zid in [1, 2, 3]:
        sub = df_stress[df_stress["zone_id"] == zid]
        crop = sub["crop"].iloc[0]
        soil = sub["soil_type"].iloc[0]
        print(f"Zone {zid} ({crop}, {soil}):")
        print(f"  Initial Stress: {sub['soil_stress'].iloc[0]:.2f}%")
        print(f"  Min Stress:     {sub['soil_stress'].min():.2f}% (RSM={sub.loc[sub['soil_stress'].idxmin(), 'rsm']:.3f})")
        print(f"  Max Stress:     {sub['soil_stress'].max():.2f}% (RSM={sub.loc[sub['soil_stress'].idxmax(), 'rsm']:.3f})")
        print(f"  Mean Stress:    {sub['soil_stress'].mean():.2f}%")

    print("\nPhase 7 Analysis & Visualization Complete!")


if __name__ == "__main__":
    main()
