"""Agronomic and Pedological Exploratory Data Analysis (EDA) module.

Analyzes crop coefficients (Kc), rooting depth envelopes, depletion thresholds,
and soil hydraulic retention/drainage characteristics.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class AgricultureEDA:
    """Exploratory analysis engine for crop and soil database assets."""

    def __init__(
        self,
        crop_path: Path = Path("data/crop_database.csv"),
        soil_path: Path = Path("data/soil_database.csv"),
    ) -> None:
        """Initialize with paths to crop and soil databases."""
        self.crop_path = Path(crop_path)
        self.soil_path = Path(soil_path)

        if not self.crop_path.is_file():
            raise FileNotFoundError(f"Crop database not found at: {self.crop_path.resolve()}")
        if not self.soil_path.is_file():
            raise FileNotFoundError(f"Soil database not found at: {self.soil_path.resolve()}")

        self.crop_df = pd.read_csv(self.crop_path)
        self.soil_df = pd.read_csv(self.soil_path)

    def summarize_crops(self) -> pd.DataFrame:
        """Return structured summary of crop parameters."""
        return self.crop_df.copy()

    def summarize_soils(self) -> pd.DataFrame:
        """Calculate derived metrics and hydraulic characteristics for soils."""
        df = self.soil_df.copy()
        # Verify and re-compute available water
        df["calculated_awc_pct"] = df["field_capacity_pct"] - df["wilting_point_pct"]
        df["retention_ratio"] = df["wilting_point_pct"] / df["field_capacity_pct"]
        return df

    def plot_crop_comparisons(self, output_dir: Path) -> List[Path]:
        """Generate crop coefficient (Kc) and rooting depth comparative visualizations.

        Args:
            output_dir: Directory where figures will be written.

        Returns:
            List[Path]: List of saved figure paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_paths = []

        # 1. Kc Comparison by Crop and Phenological Stage
        fig, ax = plt.subplots(figsize=(10, 5.5))
        crops = self.crop_df["crop"].unique()
        stages = ["kc_initial", "kc_mid", "kc_end"]
        stage_labels = ["Initial", "Mid-Season", "Late-Season / End"]
        colors = ["#42A5F5", "#26A69A", "#FFA726"]

        x = np.arange(len(crops))
        width = 0.25

        for i, (stage, label, color) in enumerate(zip(stages, stage_labels, colors)):
            # Average Kc per crop for the stage
            stage_vals = [self.crop_df[self.crop_df["crop"] == c][stage].iloc[0] for c in crops]
            ax.bar(x + i * width, stage_vals, width, label=label, color=color, edgecolor="#37474F", alpha=0.9)

        ax.set_title("Crop Evapotranspiration Coefficient ($K_c$) Across Phenological Stages", fontsize=12, fontweight="bold")
        ax.set_ylabel("Crop Coefficient ($K_c$)", fontsize=11)
        ax.set_xticks(x + width)
        ax.set_xticklabels(crops, fontsize=11, fontweight="bold")
        ax.axhline(1.0, color="#E53935", linestyle=":", linewidth=1.5, label="Reference Grass ($K_c=1.0$)")
        ax.legend(loc="upper right", frameon=True)
        ax.grid(True, linestyle="--", alpha=0.5, axis="y")

        plt.tight_layout()
        out1 = output_dir / "crop_kc_comparison.png"
        plt.savefig(out1, dpi=200)
        plt.close(fig)
        saved_paths.append(out1)

        # 2. Rooting Depth Envelopes
        fig, ax = plt.subplots(figsize=(8, 5))
        # Unique crops
        crop_subset = self.crop_df.drop_duplicates(subset=["crop"]).copy()
        y_pos = np.arange(len(crop_subset))

        # Horizontal error bar / range plot
        for idx, (_, row) in enumerate(crop_subset.iterrows()):
            min_d = row["root_depth_min_m"]
            max_d = row["root_depth_max_m"]
            ax.barh(idx, max_d - min_d, left=min_d, height=0.45, color="#8D6E63", edgecolor="#3E2723", alpha=0.85)
            ax.scatter([min_d, max_d], [idx, idx], color="#3E2723", zorder=3)
            ax.text(max_d + 0.05, idx, f"{min_d} - {max_d} m", va="center", fontsize=9, fontweight="bold")

        ax.set_yticks(y_pos)
        ax.set_yticklabels(crop_subset["crop"], fontsize=11, fontweight="bold")
        ax.set_xlabel("Effective Root Zone Depth [m]", fontsize=11)
        ax.set_title("Effective Crop Root Zone Depth Envelopes (FAO-56 Table 22)", fontsize=12, fontweight="bold")
        ax.set_xlim(0, 2.5)
        ax.grid(True, linestyle="--", alpha=0.5, axis="x")

        plt.tight_layout()
        out2 = output_dir / "crop_rooting_depth.png"
        plt.savefig(out2, dpi=200)
        plt.close(fig)
        saved_paths.append(out2)

        return saved_paths

    def plot_soil_comparisons(self, output_dir: Path) -> List[Path]:
        """Generate soil water retention and hydraulic transmission visualizations.

        Args:
            output_dir: Directory where figures will be written.

        Returns:
            List[Path]: List of saved figure paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_paths = []

        # 1. Stacked Moisture Retention Bar Chart
        fig, ax = plt.subplots(figsize=(9, 5.5))
        soils = self.soil_df["soil_type"]
        wp = self.soil_df["wilting_point_pct"]
        awc = self.soil_df["field_capacity_pct"] - self.soil_df["wilting_point_pct"]
        drainable = self.soil_df["saturation_pct"] - self.soil_df["field_capacity_pct"]

        ax.bar(soils, wp, label="Hygroscopic / Unavailable Water ($WP$)", color="#B0BEC5", edgecolor="#37474F", alpha=0.9)
        ax.bar(soils, awc, bottom=wp, label="Plant-Available Water Capacity ($AWC$)", color="#4CAF50", edgecolor="#1B5E20", alpha=0.9)
        ax.bar(soils, drainable, bottom=wp + awc, label="Gravitational / Rapid Drainage ($Sat - FC$)", color="#64B5F6", edgecolor="#0D47A1", alpha=0.85)

        ax.set_title("Soil Volumetric Moisture Partitions by Textural Class", fontsize=12, fontweight="bold")
        ax.set_ylabel("Moisture Content [% Volumetric]", fontsize=11)
        ax.set_xticks(range(len(soils)))
        ax.set_xticklabels(soils, fontsize=10, fontweight="bold")
        ax.legend(loc="upper left", frameon=True)
        ax.grid(True, linestyle="--", alpha=0.5, axis="y")

        # Annotate AWC values
        for i, val in enumerate(awc):
            ax.text(i, wp.iloc[i] + val / 2, f"AWC:\n{val:.1f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=9)

        plt.tight_layout()
        out1 = output_dir / "soil_water_retention_awc.png"
        plt.savefig(out1, dpi=200)
        plt.close(fig)
        saved_paths.append(out1)

        # 2. Infiltration Rate and Drainage Coefficient
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

        # Infiltration
        ax1.bar(soils, self.soil_df["infiltration_rate_mm_h"], color="#FF7043", edgecolor="#BF360C", alpha=0.9)
        ax1.set_title("Surface Infiltration Rate ($mm/h$)", fontsize=11, fontweight="bold")
        ax1.set_ylabel("Intake Velocity [mm/h]", fontsize=10)
        ax1.set_xticks(range(len(soils)))
        ax1.set_xticklabels(soils, rotation=25, ha="right", fontsize=9)
        ax1.grid(True, linestyle="--", alpha=0.5, axis="y")

        # Drainage Parameter
        ax2.bar(soils, self.soil_df["drainage_parameter"], color="#AB47BC", edgecolor="#4A148C", alpha=0.9)
        ax2.set_title("Unsaturated Drainage Coefficient ($1/day$)", fontsize=11, fontweight="bold")
        ax2.set_ylabel("Percolation Factor [dimensionless]", fontsize=10)
        ax2.set_xticks(range(len(soils)))
        ax2.set_xticklabels(soils, rotation=25, ha="right", fontsize=9)
        ax2.grid(True, linestyle="--", alpha=0.5, axis="y")

        plt.tight_layout()
        out2 = output_dir / "soil_hydraulic_rates.png"
        plt.savefig(out2, dpi=200)
        plt.close(fig)
        saved_paths.append(out2)

        return saved_paths
