#!/usr/bin/env python3
"""Environment and Architecture Validation Script for Phase 0.

Verifies:
1. Python version compatibility (>= 3.11).
2. Essential scientific, control, and API dependencies.
3. Directory layout compliance with Section 14 specifications.
4. Configuration integrity and Pydantic schema validation.
5. Clean importability of all core packages.
"""

import sys
import importlib
from pathlib import Path

REQUIRED_DIRS = [
    "config",
    "engineering/matlab",
    "engineering/simulink",
    "data/raw",
    "data/processed",
    "data/simulation",
    "data_processing",
    "fuzzy_engine",
    "models",
    "simulation",
    "optimization",
    "backend/app/api",
    "backend/app/ai",
    "backend/app/database",
    "frontend",
    "tests",
    "reports",
    "docs",
    "scripts",
]

CORE_PACKAGES = [
    ("numpy", "Core scientific computing"),
    ("pandas", "Data manipulation & time-series"),
    ("scipy", "Scientific calculations"),
    ("matplotlib", "Plotting & visualization"),
    ("plotly", "Interactive charting"),
    ("pydantic", "Data modeling & validation"),
    ("fastapi", "Production API framework"),
    ("uvicorn", "ASGI web server"),
    ("pytest", "Testing framework"),
    ("skfuzzy", "Fuzzy logic engine (scikit-fuzzy)"),
]

INTERNAL_MODULES = [
    "config",
    "config.schemas",
    "config.defaults",
    "data_processing",
    "data_processing.weather_preprocessor",
    "data_processing.dataset_builder",
    "data_processing.validator",
    "analysis",
    "analysis.eda_weather",
    "analysis.eda_agriculture",
    "analysis.eda_multizone",
    "analysis.generate_eda_report",
    "models",
    "models.et0",
    "models.etc",
    "models.soil",
    "models.water_balance",
    "fuzzy_engine",
    "fuzzy_engine.membership_functions",
    "fuzzy_engine.rules",
    "fuzzy_engine.soil_stress",
    "fuzzy_engine.weather_stress",
    "fuzzy_engine.water_demand",
    "fuzzy_engine.irrigation",
    "fuzzy_engine.allocation",
    "simulation",
    "simulation.engine",
    "simulation.weather",
    "simulation.scenarios",
    "simulation.validator",
    "optimization",
    "optimization.objective",
    "optimization.pso",
    "backend.app.main",
]


def check_python_version() -> bool:
    """Verify Python >= 3.11."""
    major, minor = sys.version_info.major, sys.version_info.minor
    print(f"[1/5] Python Version Check: {sys.version.split()[0]}")
    if (major, minor) < (3, 11):
        print(f"      FAIL: Python 3.11 or higher is required (found {major}.{minor}).")
        return False
    print(f"      PASS: Python {major}.{minor} meets >= 3.11 requirement.")
    return True


def check_directories() -> bool:
    """Verify all project directories exist."""
    print("\n[2/5] Directory Structure Integrity Check:")
    all_ok = True
    base = Path(__file__).resolve().parent
    for rel_dir in REQUIRED_DIRS:
        target = base / rel_dir
        if target.is_dir():
            print(f"      PASS: {rel_dir}/")
        else:
            print(f"      FAIL: Missing directory {rel_dir}/")
            all_ok = False
    return all_ok


def check_dependencies() -> bool:
    """Check third-party dependencies."""
    print("\n[3/5] Core Package Availability:")
    all_ok = True
    for pkg_name, desc in CORE_PACKAGES:
        try:
            mod = importlib.import_module(pkg_name)
            version = getattr(mod, "__version__", "installed")
            print(f"      PASS: {pkg_name:<15} v{version:<12} ({desc})")
        except ImportError:
            if pkg_name == "skfuzzy":
                print(f"      WARN: {pkg_name:<15} NOT INSTALLED   ({desc}) [Required for Phase 6+]")
            else:
                print(f"      FAIL: {pkg_name:<15} NOT INSTALLED   ({desc})")
                all_ok = False
    return all_ok


def check_config() -> bool:
    """Verify config/config.json loads and conforms to schema."""
    print("\n[4/5] Configuration & Schema Validation:")
    try:
        from config import load_config
        cfg = load_config()
        print(f"      PASS: config.json loaded successfully.")
        print(f"            - Duration: {cfg.simulation.duration_hours}h, Timestep: {cfg.simulation.timestep_minutes}m")
        print(f"            - Active Zones: {cfg.zones}")
        print(f"            - Controller: {cfg.controller.type.value} ({cfg.controller.defuzzification.value})")
        print(f"            - Pre-configured Zones: {len(cfg.zone_configs or [])}")
        return True
    except Exception as e:
        print(f"      FAIL: Failed to load/validate configuration: {e}")
        return False


def check_module_imports() -> bool:
    """Verify all internal modules can be cleanly imported."""
    print("\n[5/5] Internal Package Importability:")
    all_ok = True
    for mod_name in INTERNAL_MODULES:
        try:
            importlib.import_module(mod_name)
            print(f"      PASS: {mod_name}")
        except Exception as e:
            print(f"      FAIL: {mod_name} -> {e}")
            all_ok = False
    return all_ok


def main() -> int:
    """Main validation runner."""
    print("=" * 70)
    print(" Smart Multizone Irrigation System - Phase 0 Environment Validator")
    print("=" * 70)

    py_ok = check_python_version()
    dirs_ok = check_directories()
    deps_ok = check_dependencies()
    cfg_ok = check_config()
    imports_ok = check_module_imports()

    print("\n" + "=" * 70)
    if py_ok and dirs_ok and cfg_ok and imports_ok:
        print(" PHASE 0 VALIDATION RESULT: SUCCESS")
        print(" Foundation, schemas, directories, and module contracts are sound.")
        print(" Ready to proceed to Phase 1.")
        print("=" * 70)
        return 0
    else:
        print(" PHASE 0 VALIDATION RESULT: FAILED (Review errors above)")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
