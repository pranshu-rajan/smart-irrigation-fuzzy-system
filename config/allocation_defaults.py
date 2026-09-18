"""
Centralized Configuration Defaults for Phase 13 Water Allocation.

Defines:
1. Configured agricultural zone priorities (percentage [0.0, 100.0]%).
2. Configured shared water supply scenarios and availability factors.
3. System nominal delivery capacity constants.
"""

from typing import Dict
from enum import Enum
from pydantic import BaseModel, Field


class SupplyScenario(str, Enum):
    """Deterministic shared water supply availability scenarios."""
    ABUNDANT = "Abundant"            # 100% capacity available, surplus reserves
    NORMAL = "Normal Supply"         # 100% nominal capacity available
    MODERATE_SCARCITY = "Moderate Scarcity"  # 50% capacity available
    SEVERE_SCARCITY = "Severe Scarcity"      # 30% capacity available (matches Phase 12 Water Scarcity)
    EXTREME_SCARCITY = "Extreme Scarcity"    # 10% capacity available
    ZERO_SUPPLY = "Zero Supply"              # 0% capacity available (hard drought / dry reservoir)


# Agronomic justification for zone priorities:
# - Zone 1 (Tomato / Loam): 70.0% (High-value cash crop; mid-season flowering/fruit development; high drought sensitivity)
# - Zone 2 (Wheat / Sandy): 40.0% (Hardy staple cereal; early vegetative development; lower moisture stress vulnerability)
# - Zone 3 (Maize / Clay): 85.0% (Critical grain staple; mid-season silking/tasseling; irreversible yield reduction under moisture stress)
DEFAULT_ZONE_PRIORITIES_PCT: Dict[int, float] = {
    1: 70.0,
    2: 40.0,
    3: 85.0,
}

# Equal-priority baseline for controlled fairness experiments
EQUAL_ZONE_PRIORITIES_PCT: Dict[int, float] = {
    1: 50.0,
    2: 50.0,
    3: 50.0,
}

# Mapping of supply scenarios to percentage of nominal supply available [0.0, 100.0]%
SUPPLY_SCENARIO_FACTORS: Dict[SupplyScenario, float] = {
    SupplyScenario.ABUNDANT: 100.0,
    SupplyScenario.NORMAL: 100.0,
    SupplyScenario.MODERATE_SCARCITY: 50.0,
    SupplyScenario.SEVERE_SCARCITY: 30.0,
    SupplyScenario.EXTREME_SCARCITY: 10.0,
    SupplyScenario.ZERO_SUPPLY: 0.0,
}

# Nominal maximum system irrigation flow rate:
# Total Area = 100 (Z1) + 120 (Z2) + 80 (Z3) = 300 m²
# Max rate = 12.0 mm/h = 0.2 mm/min
# In volume: 0.2 mm/min * 300 m² = 60.0 Liters/minute
NOMINAL_MAX_SYSTEM_RATE_L_MIN: float = 60.0
NOMINAL_MAX_SYSTEM_RATE_MM_H: float = 12.0
