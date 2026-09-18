#!/usr/bin/env python3
"""Weather Scenario Generator and Visualization Script.

Generates 24-hour baseline time-series (1,440 steps at 1-min resolution) for all 6 scenarios:
1. Normal
2. Hot & Dry
3. Rainy
4. Cloudy
5. Heatwave
6. Water Scarcity

Saves output CSVs to data/simulation/ and creates comparative plots in reports/weather_engine/figures/.
"""

import sys
from pathlib import Path
from typing import Dict, List
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.schemas import SimulationScenario
from simulation.weather import WeatherEngine


def generate_all_scenarios(
    output_dir: Path = Path("data/simulation"),
    figures_dir: Path = Path("reports/weather_engine/figures"),
    seed: int = 42,
) -> Dict[SimulationScenario, pd.DataFrame]:
    """Generate and save all 6 scenario datasets and comparative figures."""
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    scenarios = [
        SimulationScenario.NORMAL,
        SimulationScenario.HOT_AND_DRY,
        SimulationScenario.RAINY,
        SimulationScenario.CLOUDY,
        SimulationScenario.HEATWAVE,
        SimulationScenario.WATER_SCARCITY,
    ]

    filename_map = {
        SimulationScenario.NORMAL: "normal.csv",
        SimulationScenario.HOT_AND_DRY: "hot_dry.csv",
        SimulationScenario.RAINY: "rainy.csv",
        SimulationScenario.CLOUDY: "cloudy.csv",
        SimulationScenario.HEATWAVE: "heatwave.csv",
        SimulationScenario.WATER_SCARCITY: "water_scarcity.csv",
    }

    colors = {
        SimulationScenario.NORMAL: "#2E7D32",        # Green
        SimulationScenario.HOT_AND_DRY: "#E65100",    # Orange
        SimulationScenario.RAINY: "#0277BD",          # Blue
        SimulationScenario.CLOUDY: "#546E7A",         # Slate Grey
        SimulationScenario.HEATWAVE: "#C62828",       # Crimson Red
        SimulationScenario.WATER_SCARCITY: "#6A1B9A", # Purple
    }

    scenario_dfs: Dict[SimulationScenario, pd.DataFrame] = {}

    print("=" * 70)
    print(" Generating 6 Environmental Weather Scenarios (24 Hours, 1-min Timesteps)")
    print("=" * 70)

    for sc in scenarios:
        engine = WeatherEngine(scenario=sc, seed=seed)
        df = engine.generate_timeline(duration_hours=24, timestep_minutes=1)
        scenario_dfs[sc] = df

        out_csv = output_dir / filename_map[sc]
        df.to_csv(out_csv, index=False)
        print(f"  [SAVED] {sc.value:<15} -> {out_csv} ({len(df)} records)")

    print("\nGenerating Cross-Scenario Comparative Visualizations...")

    # 1. Temperature Comparison
    fig, ax = plt.subplots(figsize=(11, 5))
    for sc in scenarios:
        df = scenario_dfs[sc]
        ax.plot(df["timestamp"], df["temperature"], label=sc.value, color=colors[sc], linewidth=2.0)
    ax.set_title("Cross-Scenario Diurnal Temperature Comparison (°C)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Temperature [°C]", fontsize=11)
    ax.set_xlabel("Simulation Time [Hours:Minutes]", fontsize=11)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(figures_dir / "temperature_comparison.png", dpi=200)
    plt.close(fig)

    # 2. Humidity Comparison
    fig, ax = plt.subplots(figsize=(11, 5))
    for sc in scenarios:
        df = scenario_dfs[sc]
        ax.plot(df["timestamp"], df["humidity"], label=sc.value, color=colors[sc], linewidth=2.0)
    ax.set_title("Cross-Scenario Diurnal Relative Humidity Comparison (%)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Relative Humidity [%]", fontsize=11)
    ax.set_xlabel("Simulation Time [Hours:Minutes]", fontsize=11)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    ax.legend(loc="lower right", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(figures_dir / "humidity_comparison.png", dpi=200)
    plt.close(fig)

    # 3. Solar Radiation Comparison
    fig, ax = plt.subplots(figsize=(11, 5))
    for sc in scenarios:
        df = scenario_dfs[sc]
        ax.plot(df["timestamp"], df["solar_radiation"], label=sc.value, color=colors[sc], linewidth=2.0)
    ax.set_title("Cross-Scenario Solar Radiation Comparison (W/m²)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Solar Irradiance [W/m²]", fontsize=11)
    ax.set_xlabel("Simulation Time [Hours:Minutes]", fontsize=11)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(figures_dir / "solar_radiation_comparison.png", dpi=200)
    plt.close(fig)

    # 4. Wind Speed Comparison
    fig, ax = plt.subplots(figsize=(11, 5))
    for sc in scenarios:
        df = scenario_dfs[sc]
        ax.plot(df["timestamp"], df["wind_speed"], label=sc.value, color=colors[sc], linewidth=1.8, alpha=0.85)
    ax.set_title("Cross-Scenario Wind Speed Comparison (m/s)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Wind Speed [m/s]", fontsize=11)
    ax.set_xlabel("Simulation Time [Hours:Minutes]", fontsize=11)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(figures_dir / "wind_speed_comparison.png", dpi=200)
    plt.close(fig)

    # 5. Rainfall Comparison (Cumulative & Events)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    for sc in scenarios:
        df = scenario_dfs[sc]
        ax1.plot(df["timestamp"], df["rainfall"], label=sc.value, color=colors[sc], linewidth=1.5)
        ax2.plot(df["timestamp"], df["rainfall"].cumsum(), label=sc.value, color=colors[sc], linewidth=2.0)

    ax1.set_title("Rainfall Intensity per Timestep (mm/min)", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Rate [mm/min]", fontsize=10)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right")

    ax2.set_title("Cumulative Precipitation Depth (mm)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Cumulative [mm]", fontsize=10)
    ax2.set_xlabel("Simulation Time [Hours:Minutes]", fontsize=11)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax2.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper left")

    plt.tight_layout()
    plt.savefig(figures_dir / "rainfall_comparison.png", dpi=200)
    plt.close(fig)

    # 6 to 11. Individual Profiles for each Scenario
    print("Generating Individual Scenario Detailed Multi-Panel Profiles...")
    profile_names = {
        SimulationScenario.NORMAL: "profile_normal.png",
        SimulationScenario.HOT_AND_DRY: "profile_hot_dry.png",
        SimulationScenario.RAINY: "profile_rainy.png",
        SimulationScenario.CLOUDY: "profile_cloudy.png",
        SimulationScenario.HEATWAVE: "profile_heatwave.png",
        SimulationScenario.WATER_SCARCITY: "profile_water_scarcity.png",
    }

    for sc in scenarios:
        df = scenario_dfs[sc]
        fig, axes = plt.subplots(5, 1, figsize=(11, 10), sharex=True)
        waf = df["water_availability_factor"].iloc[0]

        # Temp
        axes[0].plot(df["timestamp"], df["temperature"], color="#D32F2F", linewidth=1.8)
        axes[0].set_ylabel("Temp [°C]", fontsize=9, fontweight="bold")
        axes[0].set_title(
            f"Scenario: {sc.value} — 24-Hour Profile (Water Availability Factor: {waf*100:.0f}%)",
            fontsize=12, fontweight="bold",
        )
        axes[0].grid(True, linestyle="--", alpha=0.5)

        # Humidity
        axes[1].plot(df["timestamp"], df["humidity"], color="#1976D2", linewidth=1.8)
        axes[1].set_ylabel("RH [%]", fontsize=9, fontweight="bold")
        axes[1].grid(True, linestyle="--", alpha=0.5)

        # Solar
        axes[2].plot(df["timestamp"], df["solar_radiation"], color="#F57C00", linewidth=1.8)
        axes[2].set_ylabel("Solar [W/m²]", fontsize=9, fontweight="bold")
        axes[2].grid(True, linestyle="--", alpha=0.5)

        # Wind
        axes[3].plot(df["timestamp"], df["wind_speed"], color="#388E3C", linewidth=1.8)
        axes[3].set_ylabel("Wind [m/s]", fontsize=9, fontweight="bold")
        axes[3].grid(True, linestyle="--", alpha=0.5)

        # Rain
        axes[4].plot(df["timestamp"], df["rainfall"], color="#7B1FA2", linewidth=1.8)
        axes[4].set_ylabel("Rain [mm]", fontsize=9, fontweight="bold")
        axes[4].set_xlabel("Simulation Time [Hours:Minutes]", fontsize=10, fontweight="bold")
        axes[4].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        axes[4].xaxis.set_major_locator(mdates.HourLocator(interval=2))
        axes[4].grid(True, linestyle="--", alpha=0.5)

        plt.tight_layout()
        plt.savefig(figures_dir / profile_names[sc], dpi=200)
        plt.close(fig)

    print("All 11 visualization figures generated in reports/weather_engine/figures/")
    return scenario_dfs


def main() -> int:
    generate_all_scenarios()
    return 0


if __name__ == "__main__":
    sys.exit(main())
