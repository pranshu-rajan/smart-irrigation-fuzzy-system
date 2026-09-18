"""
Generate Publication-Quality Membership Function Visualizations.

Plots membership functions for all 19 fuzzy variables across the 5 FIS architectures
and creates an overview architecture diagram.
Saves all figures to reports/fuzzy_variables/figures/.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from fuzzy_engine.universes import FUZZY_VARIABLES, FIS_ARCHITECTURE

# Output directory
FIGURES_DIR = Path(__file__).resolve().parent.parent / "reports" / "fuzzy_variables" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Curated harmonious color palette for membership sets
COLOR_PALETTE = [
    "#1f77b4",  # Muted blue
    "#ff7f0e",  # Safety orange
    "#2ca02c",  # Cooked asparagus green
    "#d62728",  # Brick red
    "#9467bd",  # Muted purple
    "#8c564b",  # Chestnut brown
]


def plot_fuzzy_variable(var_name: str, var_obj, output_path: Path) -> None:
    """
    Plot membership functions for a single fuzzy variable.
    """
    universe = var_obj.universe
    x = universe.points

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)

    # Plot each membership set
    for idx, (set_name, m_set) in enumerate(var_obj.sets.items()):
        color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]
        y = m_set.evaluate(x)

        # Plot curve and light shaded area
        ax.plot(x, y, label=m_set.display_name, color=color, linewidth=2.2)
        ax.fill_between(x, 0, y, color=color, alpha=0.15)

    # Styling and annotations
    unit_str = f" [{var_obj.unit}]" if var_obj.unit else ""
    ax.set_title(f"Fuzzy Variable: {var_obj.display_name}{unit_str}", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel(f"{var_obj.display_name}{unit_str}", fontsize=11, fontweight="semibold")
    ax.set_ylabel("Degree of Membership ($\mu$)", fontsize=11, fontweight="semibold")
    ax.set_xlim(universe.min_val, universe.max_val)
    ax.set_ylim(-0.02, 1.05)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", framealpha=0.92, fontsize=10)

    # Engineering parameter text box
    info_text = (
        f"Universe: [{universe.min_val:.1f}, {universe.max_val:.1f}]\n"
        f"Role: {var_obj.role.upper()}\n"
        f"Sets: {len(var_obj.sets)}"
    )
    ax.text(
        0.02, 0.95, info_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#f8f9fa", edgecolor="#ced4da", alpha=0.88),
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {output_path.name}")


def plot_architecture_overview(output_path: Path) -> None:
    """
    Create a clean, publication-grade diagram showing the 5 FIS modules,
    their inputs, outputs, and hierarchical interconnection.
    """
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8.5)
    ax.axis("off")

    # Title
    ax.text(
        6.0, 8.1,
        "Hierarchical Adaptive Fuzzy Control Architecture",
        ha="center", va="center", fontsize=15, fontweight="bold", color="#1a252c"
    )
    ax.text(
        6.0, 7.7,
        "5 Coordinated Fuzzy Inference Systems (19 Variables)",
        ha="center", va="center", fontsize=11, fontstyle="italic", color="#495057"
    )

    # Box drawer helper
    def draw_box(x, y, w, h, title, inputs, output, bg_color="#e3f2fd", border_color="#1976d2"):
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.15,rounding_size=0.2",
            facecolor=bg_color, edgecolor=border_color, linewidth=1.8, zorder=2
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h - 0.28, title, ha="center", va="center", fontsize=10.5, fontweight="bold", color="#0d47a1")

        # Inputs list
        in_str = "Inputs:\n• " + "\n• ".join(inputs)
        ax.text(x + 0.18, y + h / 2 - 0.1, in_str, ha="left", va="center", fontsize=8.2, color="#212529")

        # Output badge
        out_rect = patches.FancyBboxPatch(
            (x + 0.15, y + 0.15), w - 0.3, 0.35,
            boxstyle="round,pad=0.05,rounding_size=0.1",
            facecolor="#ffffff", edgecolor=border_color, linewidth=1.2, zorder=3
        )
        ax.add_patch(out_rect)
        ax.text(x + w / 2, y + 0.32, f"Output: {output}", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#1565c0")

    # Level 1: Pre-Processors (Soil Stress, Weather Stress, Water Demand)
    draw_box(0.5, 4.4, 3.2, 2.7, "1. SOIL STRESS FIS", ["RSM", "Moisture Error"], "Soil Stress", "#e8f5e9", "#2e7d32")
    draw_box(4.4, 4.2, 3.2, 3.1, "2. WEATHER STRESS FIS", ["Temperature", "Humidity", "Solar Radiation", "Wind Speed", "Rainfall"], "Weather Stress", "#fff3e0", "#e65100")
    draw_box(8.3, 4.4, 3.2, 2.7, "3. WATER DEMAND FIS", ["ETc", "Water Deficit", "Effective Rain"], "Water Demand", "#e1f5fe", "#0277bd")

    # Level 2: Main Irrigation Controller
    draw_box(3.5, 2.2, 5.0, 1.6, "4. MAIN IRRIGATION FIS", ["Soil Stress", "Weather Stress", "Water Demand", "Moisture Error"], "Irrigation Command", "#f3e5f5", "#7b1fa2")

    # Level 3: Water Allocation FIS
    draw_box(3.5, 0.3, 5.0, 1.5, "5. WATER ALLOCATION FIS", ["Zone Demand", "Zone Stress", "Available Water", "Zone Priority"], "Zone Allocation", "#fce4ec", "#c2185b")

    # Connecting Arrows
    arrow_props = dict(arrowstyle="->", lw=1.8, color="#37474f", mutation_scale=15)

    # Soil Stress -> Main
    ax.annotate("", xy=(4.5, 3.8), xytext=(2.1, 4.4), arrowprops=arrow_props)
    # Weather Stress -> Main
    ax.annotate("", xy=(6.0, 3.8), xytext=(6.0, 4.2), arrowprops=arrow_props)
    # Water Demand -> Main
    ax.annotate("", xy=(7.5, 3.8), xytext=(9.9, 4.4), arrowprops=arrow_props)
    # Main Irrigation -> Allocation
    ax.annotate("", xy=(6.0, 1.8), xytext=(6.0, 2.2), arrowprops=arrow_props)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {output_path.name}")


def main():
    print(f"Generating membership visualizations for {len(FUZZY_VARIABLES)} variables...")
    for name, var_obj in FUZZY_VARIABLES.items():
        filename = f"{name}_membership.png"
        output_path = FIGURES_DIR / filename
        plot_fuzzy_variable(name, var_obj, output_path)

    # Generate architecture diagram
    arch_path = FIGURES_DIR / "fuzzy_architecture_overview.png"
    plot_architecture_overview(arch_path)
    print("All Phase 6 visualizations generated successfully!")


if __name__ == "__main__":
    main()
