"""
Phase 13: Water Allocation Analysis and Visualization Generator.

Executes:
1. Complete 6-scenario multizone allocation simulation (25,920 records / 12,960 zone-timesteps).
2. Generates 'data/processed/water_allocation.csv'.
3. Dedicated Controlled Experiments:
   - Supply-Sweep Experiment (100%, 75%, 50%, 30%, 15%, 0% available water).
   - Zone Priority Experiment under scarcity.
   - Zone Stress Experiment under scarcity.
   - Zone Demand Experiment under scarcity.
4. Generates 22 publication-grade figures at 300 DPI in 'reports/water_allocation/figures/':
   - Fig 01: Requested vs Allocated Water — Zone 1
   - Fig 02: Requested vs Allocated Water — Zone 2
   - Fig 03: Requested vs Allocated Water — Zone 3
   - Fig 04: Total Requested vs Available Shared Supply
   - Fig 05: Total Allocated vs Available Shared Supply
   - Fig 06: Unmet Demand by Zone
   - Fig 07: Allocation Ratio by Zone
   - Fig 08: Allocation Factor vs Available Water Control Surface
   - Fig 09: Allocation Factor vs Zone Demand Control Surface
   - Fig 10: Allocation Factor vs Zone Stress Control Surface
   - Fig 11: Allocation Factor vs Zone Priority Control Surface
   - Fig 12: Supply-Sweep Experiment Analysis
   - Fig 13: Priority Sensitivity Experiment Analysis
   - Fig 14: Stress Sensitivity Experiment Analysis
   - Fig 15: Demand Sensitivity Experiment Analysis
   - Fig 16: Water Scarcity Scenario Evaluation
   - Fig 17: Zone-wise Allocation Distribution & Metrics
   - Fig 18: Cumulative Requested vs Allocated Volume
   - Fig 19: System Water Conservation Invariant Verification
   - Fig 20: Step-by-Step Mamdani Allocation Inference Example
   - Fig 21: Master Allocation Figure (Available, Requested, Allocated, Unmet)
   - Fig 22: Centralized Membership Functions for Water Allocation FIS
"""

import sys
from pathlib import Path
import time

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from config.schemas import SimulationScenario
from config.allocation_defaults import (
    SupplyScenario,
    DEFAULT_ZONE_PRIORITIES_PCT,
    NOMINAL_MAX_SYSTEM_RATE_L_MIN,
)
from fuzzy_engine.water_allocation import WaterAllocationFIS
from simulation.water_allocation import (
    simulate_multizone_allocation,
    allocate_water,
)

# Output directories
ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
FIGURES_DIR = ROOT_DIR / "reports" / "water_allocation" / "figures"

PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.size"] = 10
plt.rcParams["axes.linewidth"] = 1.0


def run_full_scenario_simulations() -> pd.DataFrame:
    """Run all 6 scenarios and save data/processed/water_allocation.csv."""
    print("\n--- Running Multizone Allocation Simulations across 6 Scenarios ---")
    scenarios = [
        SimulationScenario.NORMAL,
        SimulationScenario.HOT_AND_DRY,
        SimulationScenario.RAINY,
        SimulationScenario.CLOUDY,
        SimulationScenario.HEATWAVE,
        SimulationScenario.WATER_SCARCITY,
    ]

    all_records = []

    for sc in scenarios:
        t0 = time.time()
        print(f"Simulating scenario: {sc.value}...", end="", flush=True)
        res = simulate_multizone_allocation(scenario=sc, seed=42)
        all_records.extend(res.telemetry_records)
        elapsed = time.time() - t0
        print(f" done in {elapsed:.2f}s (Req: {res.total_requested_volume_l:.1f}L, Alloc: {res.total_allocated_volume_l:.1f}L, Ratio: {res.system_allocation_ratio:.2%})")

    df = pd.DataFrame(all_records)
    csv_path = PROCESSED_DATA_DIR / "water_allocation.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n[OK] Saved complete allocation dataset to {csv_path} ({len(df)} records, {len(df.columns)} columns)")
    return df


def plot_membership_functions(fis: WaterAllocationFIS):
    """Figure 22: Centralized Membership Functions."""
    fig, axs = plt.subplots(3, 2, figsize=(14, 12), dpi=300)
    fig.suptitle("Phase 13: WaterAllocationFIS Membership Functions (Centralized Specification)", fontsize=14, fontweight="bold", y=0.98)

    vars_info = [
        (fis.available_water_var, axs[0, 0], "Available Water Supply", "%"),
        (fis.zone_demand_var, axs[0, 1], "Zone Irrigation Demand", "%"),
        (fis.zone_stress_var, axs[1, 0], "Zone Crop Stress", "%"),
        (fis.zone_priority_var, axs[1, 1], "Zone Agronomic Priority", "%"),
        (fis.allocation_var, axs[2, 0], "Zone Allocation Factor (Output)", "%"),
    ]

    for var, ax, title, unit in vars_info:
        u_grid = np.linspace(var.universe.min_val, var.universe.max_val, 500)
        for name, mf_set in var.sets.items():
            ax.plot(u_grid, mf_set.evaluate(u_grid), label=name, lw=2)
        ax.set_title(f"{title} ({var.name}) [{var.universe.min_val}, {var.universe.max_val}] {unit}", fontsize=11, fontweight="bold")
        ax.set_xlabel(f"Universe ({unit})")
        ax.set_ylabel("Membership Degree μ")
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, alpha=0.3, ls="--")
        ax.legend(loc="upper right", framealpha=0.9)

    # Empty sixth subplot for legend / summary
    axs[2, 1].axis("off")
    summary_text = (
        "WaterAllocationFIS Configuration Architecture:\n\n"
        "• Inputs: 4 Heterogeneous Physical/Diagnostic Signals\n"
        "  1. available_water: [0, 100] %\n"
        "  2. zone_demand: [0, 100] %\n"
        "  3. zone_stress: [0, 100] %\n"
        "  4. zone_priority: [0, 100] %\n\n"
        "• Output: 1 Supervisory Allocation Command\n"
        "  1. zone_allocation: [0, 100] %\n\n"
        "• Inference Engine: Mamdani Minimum / Centroid\n"
        "• Hierarchical Rules: 32 Transparent Engineering Rules\n"
        "• Deterministic Layer: Hard Conservation Enforced Separately"
    )
    axs[2, 1].text(0.1, 0.2, summary_text, fontsize=11, family="monospace",
                   bbox=dict(boxstyle="round,pad=0.8", facecolor="#f8f9fa", edgecolor="#ced4da"))

    plt.tight_layout()
    out_path = FIGURES_DIR / "fig22_membership_functions.png"
    plt.savefig(out_path)
    plt.close()
    print(f"[Figure 22] Saved {out_path}")


def plot_step_by_step_inference(fis: WaterAllocationFIS):
    """Figure 20: Step-by-Step Mamdani Inference Demonstration."""
    sample_inputs = {
        "available_water": 45.0,
        "zone_demand": 75.0,
        "zone_stress": 65.0,
        "zone_priority": 70.0,
    }
    telemetry = fis.evaluate_detailed(**sample_inputs)

    fig, axs = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
    fig.suptitle(
        f"Figure 20: Step-by-Step Mamdani Water Allocation Inference Example\n"
        f"(Inputs: Supply={sample_inputs['available_water']}%, Demand={sample_inputs['zone_demand']}%, "
        f"Stress={sample_inputs['zone_stress']}%, Priority={sample_inputs['zone_priority']}%)",
        fontsize=13, fontweight="bold"
    )

    # Subplot 1: Input Memberships
    ax1 = axs[0, 0]
    bars = []
    labels = []
    for vname, mdict in telemetry["memberships"].items():
        for tname, mu in mdict.items():
            if mu > 0.01:
                bars.append(mu)
                labels.append(f"{vname}\n({tname})")
    y_pos = np.arange(len(bars))
    ax1.barh(y_pos, bars, color="#2b5c8f", alpha=0.85, edgecolor="black")
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(labels, fontsize=9)
    ax1.set_xlabel("Fuzzified Membership Degree μ")
    ax1.set_title("1. Fuzzification of Crisp Inputs", fontweight="bold")
    ax1.set_xlim(0, 1.05)
    ax1.grid(True, alpha=0.3, ls="--")

    # Subplot 2: Fired Rules & Firing Strengths
    ax2 = axs[0, 1]
    active_rules = telemetry["active_rules"][:8]  # top 8 rules
    r_labels = [f"R{r['rule_id']}: -> {r['consequent']}" for r in active_rules]
    r_strengths = [r["firing_strength"] for r in active_rules]
    y_r = np.arange(len(r_labels))
    ax2.barh(y_r, r_strengths, color="#d95f02", alpha=0.85, edgecolor="black")
    ax2.set_yticks(y_r)
    ax2.set_yticklabels(r_labels, fontsize=9)
    ax2.set_xlabel("Rule Firing Strength β")
    ax2.set_title(f"2. Rule Evaluation & Implication ({len(telemetry['active_rules'])} Active Rules)", fontweight="bold")
    ax2.set_xlim(0, 1.05)
    ax2.grid(True, alpha=0.3, ls="--")

    # Subplot 3: Consequent Term Activations
    ax3 = axs[1, 0]
    act_names = list(telemetry["consequent_activations"].keys())
    act_vals = [telemetry["consequent_activations"][k] for k in act_names]
    ax3.bar(act_names, act_vals, color="#7570b3", alpha=0.85, edgecolor="black", width=0.5)
    ax3.set_ylabel("Maximum Consequent Activation")
    ax3.set_title("3. Fuzzy Term Aggregation (Max)", fontweight="bold")
    ax3.set_ylim(0, 1.05)
    ax3.grid(True, alpha=0.3, ls="--")

    # Subplot 4: Output Defuzzification (Centroid)
    ax4 = axs[1, 1]
    z_grid = fis.z_grid
    agg_mu = np.zeros_like(z_grid)
    for tname, beta in telemetry["consequent_activations"].items():
        if beta > 0.0:
            agg_mu = np.maximum(agg_mu, np.minimum(beta, fis._output_mf_matrix[tname]))

    ax4.plot(z_grid, agg_mu, label="Aggregated Fuzzy Set μ_agg(z)", color="#1b9e77", lw=2)
    ax4.fill_between(z_grid, 0, agg_mu, color="#1b9e77", alpha=0.25)
    crisp = telemetry["defuzzified_output"]
    ax4.axvline(crisp, color="crimson", lw=2.5, ls="--", label=f"Centroid Output = {crisp:.2f}%")
    ax4.set_xlabel("Zone Allocation Factor (%)")
    ax4.set_ylabel("Membership Degree μ")
    ax4.set_title("4. Centroid Defuzzification", fontweight="bold")
    ax4.set_ylim(-0.05, 1.05)
    ax4.grid(True, alpha=0.3, ls="--")
    ax4.legend(loc="upper left")

    plt.tight_layout()
    out_path = FIGURES_DIR / "fig20_step_by_step_inference.png"
    plt.savefig(out_path)
    plt.close()
    print(f"[Figure 20] Saved {out_path}")


def plot_control_surfaces(fis: WaterAllocationFIS):
    """Figures 8-11: 3D Control Surfaces and Contours."""
    grid_n = 50

    # Fig 8: Available Water vs Zone Demand
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300, subplot_kw={"projection": "3d"})
    X, Y = np.meshgrid(np.linspace(0, 100, grid_n), np.linspace(0, 100, grid_n))
    Z = np.zeros_like(X)
    for i in range(grid_n):
        for j in range(grid_n):
            Z[i, j] = fis.evaluate(available_water=X[i, j], zone_demand=Y[i, j], zone_stress=50.0, zone_priority=70.0)
    surf = ax.plot_surface(X, Y, Z, cmap="viridis", edgecolor="none", alpha=0.9)
    ax.set_title("Figure 08: Allocation Factor vs Available Water & Demand\n(Fixed: Stress=50%, Priority=70%)", fontweight="bold", fontsize=11)
    ax.set_xlabel("Available Water (%)")
    ax.set_ylabel("Zone Demand (%)")
    ax.set_zlabel("Allocation Factor (%)")
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label="Allocation (%)")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig08_surface_water_vs_demand.png")
    plt.close()

    # Fig 9: Available Water vs Zone Stress
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300, subplot_kw={"projection": "3d"})
    for i in range(grid_n):
        for j in range(grid_n):
            Z[i, j] = fis.evaluate(available_water=X[i, j], zone_demand=70.0, zone_stress=Y[i, j], zone_priority=70.0)
    surf = ax.plot_surface(X, Y, Z, cmap="plasma", edgecolor="none", alpha=0.9)
    ax.set_title("Figure 09: Allocation Factor vs Available Water & Stress\n(Fixed: Demand=70%, Priority=70%)", fontweight="bold", fontsize=11)
    ax.set_xlabel("Available Water (%)")
    ax.set_ylabel("Zone Stress (%)")
    ax.set_zlabel("Allocation Factor (%)")
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label="Allocation (%)")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig09_surface_water_vs_stress.png")
    plt.close()

    # Fig 10: Available Water vs Zone Priority
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300, subplot_kw={"projection": "3d"})
    for i in range(grid_n):
        for j in range(grid_n):
            Z[i, j] = fis.evaluate(available_water=X[i, j], zone_demand=70.0, zone_stress=60.0, zone_priority=Y[i, j])
    surf = ax.plot_surface(X, Y, Z, cmap="cividis", edgecolor="none", alpha=0.9)
    ax.set_title("Figure 10: Allocation Factor vs Available Water & Priority\n(Fixed: Demand=70%, Stress=60%)", fontweight="bold", fontsize=11)
    ax.set_xlabel("Available Water (%)")
    ax.set_ylabel("Zone Priority (%)")
    ax.set_zlabel("Allocation Factor (%)")
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label="Allocation (%)")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig10_surface_water_vs_priority.png")
    plt.close()

    # Fig 11: Zone Demand vs Zone Priority
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300, subplot_kw={"projection": "3d"})
    for i in range(grid_n):
        for j in range(grid_n):
            Z[i, j] = fis.evaluate(available_water=50.0, zone_demand=X[i, j], zone_stress=50.0, zone_priority=Y[i, j])
    surf = ax.plot_surface(X, Y, Z, cmap="coolwarm", edgecolor="none", alpha=0.9)
    ax.set_title("Figure 11: Allocation Factor vs Demand & Priority\n(Fixed: Available Supply=50%, Stress=50%)", fontweight="bold", fontsize=11)
    ax.set_xlabel("Zone Demand (%)")
    ax.set_ylabel("Zone Priority (%)")
    ax.set_zlabel("Allocation Factor (%)")
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label="Allocation (%)")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig11_surface_demand_vs_priority.png")
    plt.close()
    print("[Figures 8-11] Saved 3D control surfaces")


def plot_controlled_experiments():
    """Figures 12-15: Supply, Priority, Stress, Demand sweep experiments."""
    print("Running controlled parameter sweep experiments...")

    # Fig 12: Supply Sweep Experiment
    supplies = [0.0, 15.0, 30.0, 50.0, 75.0, 100.0]
    sweep_req = []
    sweep_alloc = []
    sweep_unmet = []
    sweep_z1 = []
    sweep_z2 = []
    sweep_z3 = []

    for s in supplies:
        r = simulate_multizone_allocation(scenario=SimulationScenario.NORMAL, supply_factor_override=s, seed=42)
        sweep_req.append(r.total_requested_volume_l)
        sweep_alloc.append(r.total_allocated_volume_l)
        sweep_unmet.append(r.total_unmet_volume_l)
        sweep_z1.append(r.zone_metrics[1]["total_allocated_l"])
        sweep_z2.append(r.zone_metrics[2]["total_allocated_l"])
        sweep_z3.append(r.zone_metrics[3]["total_allocated_l"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=300)
    ax1.plot(supplies, sweep_req, "o--", color="gray", label="Total Requested Volume (L)", lw=2)
    ax1.plot(supplies, sweep_alloc, "s-", color="blue", label="Total Allocated Volume (L)", lw=2.5)
    ax1.plot(supplies, sweep_unmet, "^-", color="crimson", label="Total Unmet Volume (L)", lw=2)
    ax1.set_title("System Volume Response to Supply Availability", fontweight="bold")
    ax1.set_xlabel("Available Shared Water (% of Nominal Capacity)")
    ax1.set_ylabel("Volume (Liters)")
    ax1.grid(True, alpha=0.3, ls="--")
    ax1.legend()

    ax2.plot(supplies, sweep_z1, "o-", color="#e41a1c", label="Zone 1 (Tomato / Loam, Prio=70%)", lw=2)
    ax2.plot(supplies, sweep_z2, "s-", color="#377eb8", label="Zone 2 (Wheat / Sandy, Prio=40%)", lw=2)
    ax2.plot(supplies, sweep_z3, "^-", color="#4daf4a", label="Zone 3 (Maize / Clay, Prio=85%)", lw=2)
    ax2.set_title("Zone-Wise Allocation Response under Supply Scarcity", fontweight="bold")
    ax2.set_xlabel("Available Shared Water (%)")
    ax2.set_ylabel("Allocated Volume (Liters)")
    ax2.grid(True, alpha=0.3, ls="--")
    ax2.legend()

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig12_supply_sweep_experiment.png")
    plt.close()

    # Fig 13: Priority Experiment (Zone 1 sensitivity under 30% scarcity)
    prio_levels = [10.0, 30.0, 50.0, 70.0, 90.0]
    z1_p_alloc = []
    z2_p_alloc = []
    z3_p_alloc = []

    for p1 in prio_levels:
        custom_prio = {1: p1, 2: 40.0, 3: 85.0}
        r = simulate_multizone_allocation(scenario=SimulationScenario.NORMAL, supply_factor_override=30.0, zone_priorities_pct=custom_prio, seed=42)
        z1_p_alloc.append(r.zone_metrics[1]["total_allocated_l"])
        z2_p_alloc.append(r.zone_metrics[2]["total_allocated_l"])
        z3_p_alloc.append(r.zone_metrics[3]["total_allocated_l"])

    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.plot(prio_levels, z1_p_alloc, "o-", color="#e41a1c", label="Zone 1 (Priority Varied 10-90%)", lw=2.5)
    ax.plot(prio_levels, z2_p_alloc, "s--", color="#377eb8", label="Zone 2 (Priority Fixed 40%)", lw=2)
    ax.plot(prio_levels, z3_p_alloc, "^--", color="#4daf4a", label="Zone 3 (Priority Fixed 85%)", lw=2)
    ax.set_title("Figure 13: Allocation Redistribution Under Priority Modulation\n(Water Scarcity Supply = 30%)", fontweight="bold")
    ax.set_xlabel("Zone 1 Priority (%)")
    ax.set_ylabel("Allocated Volume (Liters)")
    ax.grid(True, alpha=0.3, ls="--")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig13_priority_experiment.png")
    plt.close()

    # Fig 14: Stress Sensitivity (FIS Level)
    fis = WaterAllocationFIS()
    stress_levels = np.linspace(0, 100, 50)
    alloc_prio_low = [fis.evaluate(30.0, 70.0, s, 25.0) for s in stress_levels]
    alloc_prio_med = [fis.evaluate(30.0, 70.0, s, 50.0) for s in stress_levels]
    alloc_prio_high = [fis.evaluate(30.0, 70.0, s, 85.0) for s in stress_levels]

    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.plot(stress_levels, alloc_prio_low, color="#377eb8", label="Low Priority (25%)", lw=2)
    ax.plot(stress_levels, alloc_prio_med, color="#ff7f00", label="Medium Priority (50%)", lw=2)
    ax.plot(stress_levels, alloc_prio_high, color="#e41a1c", label="Critical Priority (85%)", lw=2.5)
    ax.set_title("Figure 14: Allocation Factor Response to Soil Moisture Stress\n(Supply=30%, Demand=70%)", fontweight="bold")
    ax.set_xlabel("Crop Physiological / Soil Stress (%)")
    ax.set_ylabel("Allocation Factor (%)")
    ax.grid(True, alpha=0.3, ls="--")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig14_stress_experiment.png")
    plt.close()

    # Fig 15: Demand Sensitivity (FIS Level)
    demand_levels = np.linspace(0, 100, 50)
    alloc_d_scarce = [fis.evaluate(20.0, d, 60.0, 70.0) for d in demand_levels]
    alloc_d_mod = [fis.evaluate(50.0, d, 60.0, 70.0) for d in demand_levels]
    alloc_d_abund = [fis.evaluate(90.0, d, 60.0, 70.0) for d in demand_levels]

    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.plot(demand_levels, alloc_d_scarce, color="#e41a1c", label="Supply Scarcity (20%)", lw=2)
    ax.plot(demand_levels, alloc_d_mod, color="#ff7f00", label="Moderate Supply (50%)", lw=2)
    ax.plot(demand_levels, alloc_d_abund, color="#2ca02c", label="Abundant Supply (90%)", lw=2.5)
    ax.set_title("Figure 15: Allocation Factor Response to Crop Demand\n(Stress=60%, Priority=70%)", fontweight="bold")
    ax.set_xlabel("Zone Irrigation Demand (%)")
    ax.set_ylabel("Allocation Factor (%)")
    ax.grid(True, alpha=0.3, ls="--")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig15_demand_experiment.png")
    plt.close()
    print("[Figures 12-15] Saved controlled experiment figures")


def plot_scenario_and_timeseries(df: pd.DataFrame):
    """Figures 1-7, 16-19, 21: Timeseries, Scenarios, and System Telemetry."""
    print("Generating scenario timeseries and master allocation plots...")

    # Filter Normal and Water Scarcity
    df_normal = df[df["scenario"] == "Normal"]
    df_scarcity = df[df["scenario"] == "Water Scarcity"]

    # Figures 1-3: Requested vs Allocated per Zone (Water Scarcity Scenario)
    for z_id in [1, 2, 3]:
        df_z = df_scarcity[df_scarcity["zone_id"] == z_id]
        fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
        t_hours = df_z["timestep"] / 60.0
        ax.plot(t_hours, df_z["irrigation_request_mm"], color="gray", ls="--", label="Requested Depth (mm)", lw=1.5)
        ax.plot(t_hours, df_z["allocated_irrigation_mm"], color="#1f77b4", label="Allocated Depth (mm)", lw=2)
        ax.fill_between(t_hours, df_z["allocated_irrigation_mm"], df_z["irrigation_request_mm"], color="crimson", alpha=0.2, label="Unmet Demand (mm)")
        crop_name = df_z["crop"].iloc[0]
        soil_name = df_z["soil_type"].iloc[0]
        prio = df_z["zone_priority"].iloc[0]
        ax.set_title(f"Figure 0{z_id}: Zone {z_id} ({crop_name} / {soil_name}, Priority={prio}%) — Requested vs Allocated Depth (Water Scarcity)", fontweight="bold")
        ax.set_xlabel("Simulation Time (Hours)")
        ax.set_ylabel("Water Depth (mm / step)")
        ax.grid(True, alpha=0.3, ls="--")
        ax.legend()
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / f"fig0{z_id}_zone{z_id}_requested_vs_allocated.png")
        plt.close()

    # Fig 4: Total Requested vs Available Shared Supply
    df_step_scarcity = df_scarcity.groupby("timestep").agg({
        "water_volume_requested_L": "sum",
        "water_volume_allocated_L": "sum",
        "available_water": "first",
    }).reset_index()
    t_h = df_step_scarcity["timestep"] / 60.0
    avail_l = (df_step_scarcity["available_water"] / 100.0) * NOMINAL_MAX_SYSTEM_RATE_L_MIN

    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax.plot(t_h, df_step_scarcity["water_volume_requested_L"], color="#d95f02", label="Total System Request (L/min)", lw=2)
    ax.plot(t_h, avail_l, color="black", ls="--", label="Available Supply Limit (L/min)", lw=2)
    ax.set_title("Figure 04: Total System Request vs Available Supply Limit (Water Scarcity)", fontweight="bold")
    ax.set_xlabel("Simulation Time (Hours)")
    ax.set_ylabel("Flow Rate (Liters / minute)")
    ax.grid(True, alpha=0.3, ls="--")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig04_total_requested_vs_available.png")
    plt.close()

    # Fig 5: Total Allocated vs Available Shared Supply
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax.plot(t_h, df_step_scarcity["water_volume_allocated_L"], color="#1b9e77", label="Total System Allocated (L/min)", lw=2)
    ax.plot(t_h, avail_l, color="black", ls="--", label="Available Supply Limit (L/min)", lw=2)
    ax.set_title("Figure 05: Total Allocated Water vs Available Shared Supply (Water Scarcity)", fontweight="bold")
    ax.set_xlabel("Simulation Time (Hours)")
    ax.set_ylabel("Flow Rate (Liters / minute)")
    ax.grid(True, alpha=0.3, ls="--")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig05_total_allocated_vs_available.png")
    plt.close()

    # Fig 6 & 7: Unmet Demand and Allocation Ratio by Zone
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=300)
    scenarios_list = df["scenario"].unique()
    x_pos = np.arange(len(scenarios_list))
    width = 0.25

    for idx, z_id in enumerate([1, 2, 3]):
        z_df = df[df["zone_id"] == z_id]
        unmet_by_sc = [z_df[z_df["scenario"] == sc]["water_volume_unmet_L"].sum() for sc in scenarios_list]
        ratio_by_sc = [
            z_df[z_df["scenario"] == sc]["water_volume_allocated_L"].sum() /
            max(1e-6, z_df[z_df["scenario"] == sc]["water_volume_requested_L"].sum())
            for sc in scenarios_list
        ]
        crop = z_df["crop"].iloc[0]
        ax1.bar(x_pos + (idx - 1) * width, unmet_by_sc, width=width, label=f"Zone {z_id} ({crop})")
        ax2.bar(x_pos + (idx - 1) * width, ratio_by_sc, width=width, label=f"Zone {z_id} ({crop})")

    ax1.set_title("Figure 06: Cumulative Unmet Demand by Scenario (Liters)", fontweight="bold")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(scenarios_list, rotation=20, ha="right")
    ax1.set_ylabel("Unmet Volume (Liters)")
    ax1.grid(True, alpha=0.3, ls="--")
    ax1.legend()

    ax2.set_title("Figure 07: Effective Allocation Ratio by Scenario", fontweight="bold")
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(scenarios_list, rotation=20, ha="right")
    ax2.set_ylabel("Allocation Ratio (Allocated / Requested)")
    ax2.set_ylim(0, 1.05)
    ax2.grid(True, alpha=0.3, ls="--")
    ax2.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig06_07_unmet_and_allocation_ratio.png")
    plt.close()

    # Fig 16: Water Scarcity Comprehensive Telemetry
    fig, axs = plt.subplots(3, 1, figsize=(12, 10), dpi=300, sharex=True)
    axs[0].plot(t_h, df_step_scarcity["water_volume_requested_L"], color="#d95f02", label="Requested (L/min)", lw=1.8)
    axs[0].plot(t_h, df_step_scarcity["water_volume_allocated_L"], color="#1b9e77", label="Allocated (L/min)", lw=2)
    axs[0].plot(t_h, avail_l, color="black", ls="--", label="Available Supply (L/min)")
    axs[0].set_ylabel("System Volume (L/min)")
    axs[0].set_title("Figure 16: Water Scarcity Scenario — Comprehensive Allocation Telemetry", fontweight="bold")
    axs[0].grid(True, alpha=0.3, ls="--")
    axs[0].legend()

    for z_id, color in [(1, "#e41a1c"), (2, "#377eb8"), (3, "#4daf4a")]:
        df_z = df_scarcity[df_scarcity["zone_id"] == z_id]
        axs[1].plot(t_h, df_z["allocation_factor"], color=color, label=f"Zone {z_id} ({df_z['crop'].iloc[0]})", lw=1.8)
        axs[2].plot(t_h, df_z["soil_moisture"], color=color, label=f"Zone {z_id} SM (%)", lw=1.8)

    axs[1].set_ylabel("Allocation Factor (%)")
    axs[1].set_ylim(0, 105)
    axs[1].grid(True, alpha=0.3, ls="--")
    axs[1].legend()

    axs[2].set_ylabel("Soil Moisture (%)")
    axs[2].set_xlabel("Simulation Time (Hours)")
    axs[2].grid(True, alpha=0.3, ls="--")
    axs[2].legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig16_water_scarcity_scenario.png")
    plt.close()

    # Fig 17: Zone-wise Allocation Summary Comparison
    zone_totals = df.groupby(["scenario", "zone_id"]).agg({
        "water_volume_requested_L": "sum",
        "water_volume_allocated_L": "sum",
        "water_volume_unmet_L": "sum",
    }).reset_index()

    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    sc_order = scenarios_list
    labels = []
    req_vals = []
    alloc_vals = []
    unmet_vals = []
    for sc in sc_order:
        for z in [1, 2, 3]:
            sub = zone_totals[(zone_totals["scenario"] == sc) & (zone_totals["zone_id"] == z)]
            labels.append(f"{sc}\nZ{z}")
            req_vals.append(sub["water_volume_requested_L"].iloc[0])
            alloc_vals.append(sub["water_volume_allocated_L"].iloc[0])
            unmet_vals.append(sub["water_volume_unmet_L"].iloc[0])

    x = np.arange(len(labels))
    w = 0.28
    ax.bar(x - w, req_vals, width=w, label="Requested (L)", color="#ff7f00", alpha=0.85)
    ax.bar(x, alloc_vals, width=w, label="Allocated (L)", color="#2ca02c", alpha=0.85)
    ax.bar(x + w, unmet_vals, width=w, label="Unmet (L)", color="#d62728", alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90, fontsize=8)
    ax.set_ylabel("Water Volume (Liters)")
    ax.set_title("Figure 17: Comprehensive Zone-Wise Allocation & Unmet Demands Across All Scenarios", fontweight="bold")
    ax.grid(True, alpha=0.3, ls="--")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig17_zone_wise_comparison.png")
    plt.close()

    # Fig 18: Cumulative Requested vs Allocated Volume
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    cum_req = np.cumsum(df_step_scarcity["water_volume_requested_L"])
    cum_alloc = np.cumsum(df_step_scarcity["water_volume_allocated_L"])
    cum_avail = np.cumsum(avail_l)

    ax.plot(t_h, cum_req, color="#ff7f00", lw=2.2, label="Cumulative Requested Volume (L)")
    ax.plot(t_h, cum_alloc, color="#2ca02c", lw=2.5, label="Cumulative Allocated Volume (L)")
    ax.plot(t_h, cum_avail, color="black", ls="--", lw=1.8, label="Cumulative Available Supply Limit (L)")
    ax.fill_between(t_h, cum_alloc, cum_req, color="crimson", alpha=0.2, label="Cumulative Unmet Demand (L)")
    ax.set_title("Figure 18: Cumulative Requested, Allocated, and Available Supply (Water Scarcity)", fontweight="bold")
    ax.set_xlabel("Simulation Time (Hours)")
    ax.set_ylabel("Cumulative Volume (Liters)")
    ax.grid(True, alpha=0.3, ls="--")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig18_cumulative_volumes.png")
    plt.close()

    # Fig 19: Conservation Invariant Verification
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    diff_from_limit = avail_l - df_step_scarcity["water_volume_allocated_L"]
    ax.plot(t_h, diff_from_limit, color="navy", lw=1.8, label="Unused Supply Margin (Available - Allocated) [L/min]")
    ax.axhline(0.0, color="crimson", ls="--", lw=2, label="Conservation Violation Threshold (0 L/min)")
    ax.set_title("Figure 19: Physical Supply Conservation Invariant Verification\n(Allocated <= Available Supply at Every Timestep)", fontweight="bold")
    ax.set_xlabel("Simulation Time (Hours)")
    ax.set_ylabel("Supply Margin (L/min)")
    ax.set_ylim(-1.0, max(diff_from_limit) * 1.1)
    ax.grid(True, alpha=0.3, ls="--")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig19_conservation_verification.png")
    plt.close()

    # Fig 21: Master Allocation Figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), dpi=300, sharex=True)
    ax1.plot(t_h, avail_l, color="black", ls=":", lw=2, label="Available Shared Supply Limit (L/min)")
    ax1.plot(t_h, df_step_scarcity["water_volume_requested_L"], color="#ff7f00", lw=2, label="Total Requested Flow (L/min)")
    ax1.plot(t_h, df_step_scarcity["water_volume_allocated_L"], color="#2ca02c", lw=2.2, label="Total Allocated Flow (L/min)")
    ax1.fill_between(t_h, df_step_scarcity["water_volume_allocated_L"], df_step_scarcity["water_volume_requested_L"], color="crimson", alpha=0.25, label="Instantaneous Unmet Demand (L/min)")
    ax1.set_ylabel("Flow Rate (L/min)")
    ax1.set_title("Figure 21: Master Allocation Figure — Shared Supply Constraint & Multizone Delivery (Water Scarcity)", fontweight="bold")
    ax1.grid(True, alpha=0.3, ls="--")
    ax1.legend(loc="upper right")

    # Stacked zone allocations
    z1_v = df_scarcity[df_scarcity["zone_id"] == 1]["water_volume_allocated_L"].values
    z2_v = df_scarcity[df_scarcity["zone_id"] == 2]["water_volume_allocated_L"].values
    z3_v = df_scarcity[df_scarcity["zone_id"] == 3]["water_volume_allocated_L"].values

    ax2.stackplot(t_h, z1_v, z2_v, z3_v, labels=["Zone 1 (Tomato, Prio=70%)", "Zone 2 (Wheat, Prio=40%)", "Zone 3 (Maize, Prio=85%)"],
                  colors=["#e41a1c", "#377eb8", "#4daf4a"], alpha=0.85)
    ax2.set_ylabel("Zone Allocation (L/min)")
    ax2.set_xlabel("Simulation Time (Hours)")
    ax2.grid(True, alpha=0.3, ls="--")
    ax2.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fig21_master_allocation_figure.png")
    plt.close()
    print("[Figures 1-7, 16-19, 21] Saved timeseries, scenario, and master figures")


def main():
    print("================================================================")
    print("PHASE 13: WATER ALLOCATION ANALYSIS & VISUALIZATION PIPELINE")
    print("================================================================")
    fis = WaterAllocationFIS()

    # 1. Full 6-scenario simulations -> CSV
    df = run_full_scenario_simulations()

    # 2. Membership Functions
    plot_membership_functions(fis)

    # 3. Step-by-Step Mamdani Demonstration
    plot_step_by_step_inference(fis)

    # 4. Control Surfaces
    plot_control_surfaces(fis)

    # 5. Controlled Experiments
    plot_controlled_experiments()

    # 6. Timeseries, Scenarios & Master Figure
    plot_scenario_and_timeseries(df)

    print("\n================================================================")
    print("PHASE 13 ANALYSIS COMPLETE: All 22 Figures & Dataset Generated!")
    print("================================================================")


if __name__ == "__main__":
    main()
