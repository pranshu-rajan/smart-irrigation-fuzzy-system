"""Meteorological Exploratory Data Analysis (EDA) module.

Performs statistical profiling, outlier detection, cross-variable correlation,
and diurnal time-series plotting on cleaned weather data.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt


class WeatherEDA:
    """Exploratory analysis engine for meteorological observations."""

    WEATHER_VARS = ["temperature", "humidity", "solar_radiation", "wind_speed", "rainfall"]

    UNITS = {
        "temperature": "°C",
        "humidity": "%",
        "solar_radiation": "W/m²",
        "wind_speed": "m/s",
        "rainfall": "mm",
    }

    def __init__(self, data_path: Path = Path("data/processed/weather_clean.csv")) -> None:
        """Initialize with path to cleaned weather CSV."""
        self.data_path = Path(data_path)
        if not self.data_path.is_file():
            raise FileNotFoundError(f"Clean weather data not found at: {self.data_path.resolve()}")

        self.df = pd.read_csv(self.data_path)
        self.df["timestamp"] = pd.to_datetime(self.df["timestamp"])

    def compute_summary_statistics(self) -> pd.DataFrame:
        """Calculate comprehensive univariate summary statistics for weather variables.

        Returns:
            pd.DataFrame: Table of statistics per weather variable.
        """
        records = []
        for col in self.WEATHER_VARS:
            if col not in self.df.columns:
                continue
            series = self.df[col].dropna()
            q25 = series.quantile(0.25)
            q75 = series.quantile(0.75)
            iqr = q75 - q25
            lower_bound = q25 - 1.5 * iqr
            upper_bound = q75 + 1.5 * iqr
            iqr_outliers = ((series < lower_bound) | (series > upper_bound)).sum()

            mean_v = series.mean()
            std_v = series.std()
            z_scores = (series - mean_v) / (std_v if std_v > 0 else 1.0)
            z_outliers = (z_scores.abs() > 3.0).sum()

            records.append({
                "variable": col,
                "unit": self.UNITS.get(col, ""),
                "count": len(series),
                "min": series.min(),
                "max": series.max(),
                "mean": mean_v,
                "median": series.median(),
                "std": std_v,
                "variance": series.var(),
                "p05": series.quantile(0.05),
                "p25": q25,
                "p75": q75,
                "p95": series.quantile(0.95),
                "missing": self.df[col].isnull().sum(),
                "iqr_outliers": int(iqr_outliers),
                "z_score_outliers": int(z_outliers),
            })

        return pd.DataFrame(records)

    def compute_correlations(self, method: str = "pearson", drop_constant: bool = False) -> pd.DataFrame:
        """Calculate pairwise correlation matrix between continuous weather parameters.

        Args:
            method: 'pearson' or 'spearman'.
            drop_constant: If True, columns with zero variance (e.g. constant 0.0 rainfall) are omitted.

        Returns:
            pd.DataFrame: Symmetric correlation matrix.
        """
        cols = [c for c in self.WEATHER_VARS if c in self.df.columns]
        if drop_constant:
            cols = [c for c in cols if self.df[c].std() > 0]
        return self.df[cols].corr(method=method)

    def plot_distributions(self, output_dir: Path) -> List[Path]:
        """Generate and save univariate distribution histogram and box plots.

        Args:
            output_dir: Directory where figures will be written.

        Returns:
            List[Path]: List of generated image paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_paths = []

        for col in self.WEATHER_VARS:
            if col not in self.df.columns:
                continue

            fig, (ax_box, ax_hist) = plt.subplots(
                2, 1, figsize=(8, 6), gridspec_kw={"height_ratios": [0.25, 0.75]}, sharex=True
            )

            # Boxplot
            ax_box.boxplot(self.df[col], vert=False, patch_artist=True,
                           boxprops=dict(facecolor="#4A90E2", color="#1B365D"),
                           medianprops=dict(color="#D0021B", linewidth=2))
            ax_box.set_yticks([])
            ax_box.set_title(f"{col.replace('_', ' ').title()} Distribution ({self.UNITS.get(col, '')})",
                             fontsize=13, fontweight="bold")
            ax_box.grid(True, linestyle="--", alpha=0.5)

            # Histogram
            n, bins, patches = ax_hist.hist(self.df[col], bins=30, color="#50E3C2", edgecolor="#1B365D", alpha=0.85)
            ax_hist.set_xlabel(f"{col.replace('_', ' ').title()} [{self.UNITS.get(col, '')}]", fontsize=11)
            ax_hist.set_ylabel("Frequency (Count)", fontsize=11)
            ax_hist.grid(True, linestyle="--", alpha=0.5)

            mean_val = self.df[col].mean()
            median_val = self.df[col].median()
            ax_hist.axvline(mean_val, color="#D0021B", linestyle="--", linewidth=1.8, label=f"Mean: {mean_val:.2f}")
            ax_hist.axvline(median_val, color="#9013FE", linestyle="-.", linewidth=1.8, label=f"Median: {median_val:.2f}")
            ax_hist.legend(loc="upper right", frameon=True)

            plt.tight_layout()
            out_file = output_dir / f"{col}_distribution.png"
            plt.savefig(out_file, dpi=200)
            plt.close(fig)
            saved_paths.append(out_file)

        return saved_paths

    def plot_bivariate_relationships(self, output_dir: Path) -> List[Path]:
        """Generate bivariate relationship scatter plots with trend lines.

        Args:
            output_dir: Directory where figures will be written.

        Returns:
            List[Path]: List of generated image paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_paths = []

        # 1. Temperature vs Humidity (Psychrometric coupling)
        fig, ax = plt.subplots(figsize=(8, 5.5))
        scatter = ax.scatter(
            self.df["temperature"],
            self.df["humidity"],
            c=self.df["solar_radiation"],
            cmap="viridis",
            alpha=0.75,
            edgecolors="none",
        )
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label("Solar Radiation [W/m²]", fontsize=10)
        ax.set_title("Temperature vs. Relative Humidity (Colored by Solar Radiation)", fontsize=12, fontweight="bold")
        ax.set_xlabel("Temperature [°C]", fontsize=11)
        ax.set_ylabel("Relative Humidity [%]", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.5)

        # Trend line
        z = np.polyfit(self.df["temperature"], self.df["humidity"], 1)
        p = np.poly1d(z)
        x_vals = np.linspace(self.df["temperature"].min(), self.df["temperature"].max(), 100)
        ax.plot(x_vals, p(x_vals), color="#E65100", linestyle="--", linewidth=2, label=f"Trend (slope={z[0]:.2f})")
        ax.legend(loc="upper right")

        plt.tight_layout()
        out1 = output_dir / "scatter_temp_vs_humidity.png"
        plt.savefig(out1, dpi=200)
        plt.close(fig)
        saved_paths.append(out1)

        # 2. Temperature vs Solar Radiation
        fig, ax = plt.subplots(figsize=(8, 5.5))
        scatter2 = ax.scatter(
            self.df["solar_radiation"],
            self.df["temperature"],
            c=self.df["humidity"],
            cmap="plasma_r",
            alpha=0.75,
            edgecolors="none",
        )
        cbar2 = plt.colorbar(scatter2, ax=ax)
        cbar2.set_label("Relative Humidity [%]", fontsize=10)
        ax.set_title("Solar Radiation vs. Temperature (Colored by Humidity)", fontsize=12, fontweight="bold")
        ax.set_xlabel("Solar Radiation [W/m²]", fontsize=11)
        ax.set_ylabel("Temperature [°C]", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        out2 = output_dir / "scatter_temp_vs_solar.png"
        plt.savefig(out2, dpi=200)
        plt.close(fig)
        saved_paths.append(out2)

        return saved_paths

    def plot_temporal_trends(self, output_dir: Path) -> Path:
        """Generate multi-panel 24-hour diurnal timeline plot across all weather variables.

        Args:
            output_dir: Directory where figure will be written.

        Returns:
            Path: Path to saved timeline plot.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        fig, axes = plt.subplots(5, 1, figsize=(12, 12), sharex=True)

        # Temperature
        axes[0].plot(self.df["timestamp"], self.df["temperature"], color="#D32F2F", linewidth=2.0)
        axes[0].set_ylabel("Temp [°C]", fontsize=10, fontweight="bold")
        axes[0].grid(True, linestyle="--", alpha=0.5)
        axes[0].set_title("24-Hour Diurnal Meteorological Profile (1-Minute Simulation Timesteps)", fontsize=13, fontweight="bold")

        # Humidity
        axes[1].plot(self.df["timestamp"], self.df["humidity"], color="#1976D2", linewidth=2.0)
        axes[1].set_ylabel("RH [%]", fontsize=10, fontweight="bold")
        axes[1].grid(True, linestyle="--", alpha=0.5)

        # Solar Radiation
        axes[2].plot(self.df["timestamp"], self.df["solar_radiation"], color="#F57C00", linewidth=2.0)
        axes[2].set_ylabel("Solar [W/m²]", fontsize=10, fontweight="bold")
        axes[2].grid(True, linestyle="--", alpha=0.5)

        # Wind Speed
        axes[3].plot(self.df["timestamp"], self.df["wind_speed"], color="#388E3C", linewidth=2.0)
        axes[3].set_ylabel("Wind [m/s]", fontsize=10, fontweight="bold")
        axes[3].grid(True, linestyle="--", alpha=0.5)

        # Rainfall
        axes[4].plot(self.df["timestamp"], self.df["rainfall"], color="#7B1FA2", linewidth=2.0)
        axes[4].set_ylabel("Rain [mm]", fontsize=10, fontweight="bold")
        axes[4].set_xlabel("Simulation Timeline [Hours:Minutes]", fontsize=11, fontweight="bold")
        axes[4].grid(True, linestyle="--", alpha=0.5)

        # Format X-axis
        import matplotlib.dates as mdates
        axes[4].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        axes[4].xaxis.set_major_locator(mdates.HourLocator(interval=2))
        plt.xticks(rotation=0)

        plt.tight_layout()
        out_file = output_dir / "weather_timeline_24h.png"
        plt.savefig(out_file, dpi=200)
        plt.close(fig)
        return out_file

    def plot_correlation_heatmap(self, output_dir: Path) -> Path:
        """Plot pairwise correlation heatmap.

        Args:
            output_dir: Directory where figure will be written.

        Returns:
            Path: Path to saved heatmap plot.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        corr = self.compute_correlations(drop_constant=True)

        fig, ax = plt.subplots(figsize=(7, 6))
        cax = ax.imshow(corr, cmap="coolwarm", vmin=-1.0, vmax=1.0)
        cbar = fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("Pearson Correlation Coefficient", fontsize=10)

        cols = [c.replace("_", " ").title() for c in corr.columns]
        ax.set_xticks(range(len(cols)))
        ax.set_yticks(range(len(cols)))
        ax.set_xticklabels(cols, rotation=35, ha="right", fontsize=9)
        ax.set_yticklabels(cols, fontsize=9)
        ax.set_title("Pairwise Meteorological Correlation Matrix", fontsize=12, fontweight="bold")

        # Annotate text values
        for i in range(len(cols)):
            for j in range(len(cols)):
                val = corr.iloc[i, j]
                text_color = "white" if abs(val) > 0.55 else "black"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", color=text_color, fontweight="bold", fontsize=10)

        plt.tight_layout()
        out_file = output_dir / "correlation_heatmap.png"
        plt.savefig(out_file, dpi=200)
        plt.close(fig)
        return out_file
