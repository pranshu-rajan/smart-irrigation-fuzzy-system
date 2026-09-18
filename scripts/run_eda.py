#!/usr/bin/env python3
"""Reproducible Exploratory Data Analysis (EDA) CLI script.

Executes:
1. Weather statistics, correlations, and distribution/trend plots.
2. Crop and soil comparative evaluations and figures.
3. Multi-zone parameter and RSM analysis.
4. Compilation of reports/eda/EDA_REPORT.md.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.generate_eda_report import generate_all_eda


def main() -> int:
    print("=" * 70)
    print(" Smart Multizone Irrigation System - Exploratory Data Analysis (EDA)")
    print("=" * 70)

    try:
        generate_all_eda()
        print("\n" + "=" * 70)
        print(" EDA PIPELINE COMPLETED SUCCESSFULLY")
        print(" All figures saved under: reports/eda/figures/")
        print(" Comprehensive report: reports/eda/EDA_REPORT.md")
        print("=" * 70)
        return 0
    except Exception as e:
        print(f"\nERROR running EDA pipeline: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
