"""
Simulation and Deterministic Constraint Enforcement for Phase 13 Water Allocation.

Integrates the hierarchical fuzzy control architecture:
1. Layer A (Local): MainIrrigationFIS produces unconstrained zone irrigation requests.
2. Layer B (Supervisory): WaterAllocationFIS computes raw allocation factors.
3. Layer C (Deterministic): Strict physical shared-supply constraint enforcement:
   Sum(Allocated_z) <= Available_Supply and Allocated_z <= Requested_z.
4. Physical application & root-zone soil-water balance integration.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from config.schemas import SimulationScenario, ZoneConfig, CropType, SoilType
from config.defaults import get_default_zones
from config.allocation_defaults import (
    SupplyScenario,
    DEFAULT_ZONE_PRIORITIES_PCT,
    SUPPLY_SCENARIO_FACTORS,
    NOMINAL_MAX_SYSTEM_RATE_L_MIN,
)
from simulation.weather import WeatherEngine
from models.et0 import compute_et0_timeseries
from models.etc import (
    CropCoefficientManager,
    calculate_effective_rainfall,
    calculate_crop_water_deficit,
)
from models.soil import (
    calculate_relative_soil_moisture,
    calculate_moisture_error,
)
from models.water_balance import (
    SoilState,
    initialize_soil_state,
    update_water_balance,
)
from fuzzy_engine.soil_stress import SoilStressFIS
from fuzzy_engine.weather_stress import WeatherStressFIS
from fuzzy_engine.water_demand import WaterDemandFIS
from fuzzy_engine.main_irrigation import MainIrrigationFIS
from fuzzy_engine.water_allocation import WaterAllocationFIS


class AllocationResult(BaseModel):
    """Container for instantaneous multizone allocation step."""

    # Volume accounting (Liters)
    requested_volumes_l: Dict[int, float] = Field(..., description="Requested water volume per zone (L)")
    allocated_volumes_l: Dict[int, float] = Field(..., description="Allocated water volume per zone (L)")
    unmet_volumes_l: Dict[int, float] = Field(..., description="Unmet water volume per zone (L)")

    # Depth accounting (mm)
    requested_depths_mm: Dict[int, float] = Field(..., description="Requested water depth per zone (mm)")
    allocated_depths_mm: Dict[int, float] = Field(..., description="Allocated water depth per zone (mm)")
    unmet_depths_mm: Dict[int, float] = Field(..., description="Unmet water depth per zone (mm)")

    # Controller factors (%)
    allocation_factors_pct: Dict[int, float] = Field(..., description="Raw fuzzy allocation factor per zone (%)")
    allocation_ratios: Dict[int, float] = Field(..., description="Effective allocation ratio (Allocated / Requested)")

    # System aggregates (Liters)
    total_requested_l: float = Field(..., description="Total system requested volume (L)")
    total_allocated_l: float = Field(..., description="Total system allocated volume (L)")
    total_unmet_l: float = Field(..., description="Total system unmet volume (L)")
    available_supply_l: float = Field(..., description="Available shared supply in Liters")
    available_water_pct: float = Field(..., description="Available supply percentage of nominal capacity (%)")
    is_supply_constrained: bool = Field(..., description="True if available supply strictly capped total requests")


def bounded_priority_weighted_allocation(
    raw_requests_l: Dict[Any, float],
    priorities_pct: Dict[Any, float],
    available_supply_l: float,
) -> Dict[Any, float]:
    """
    Perform deterministic bounded priority-weighted allocation (iterative weighted water-filling).

    Satisfies all physical invariants:
    - Invariant A (Zero supply): W_available == 0 -> A_final,z == 0 for all z.
    - Invariant B (Zero request): raw_requests_l[z] == 0 -> A_final,z == 0.
    - Invariant C (Demand ceiling): 0 <= A_final,z <= raw_requests_l[z] for all z.
    - Invariant D (Supply ceiling): sum(A_final,z) <= available_supply_l.
    - Invariant E (Full satisfaction): sum(raw_requests_l) <= available_supply_l -> A_final,z == raw_requests_l[z].
    - Invariant F (Priority-sensitive scarcity): under scarcity, higher priority receives greater allocation up to ceiling.
    - Invariant G (No artificial water creation): A_final,z never exceeds raw_requests_l[z].

    Algorithm (Iterative Weighted Capped Allocation):
    1. Validate non-negative bounds: available supply and raw request ceilings.
    2. If available supply <= 0: return 0 for all zones.
    3. If total raw request <= available supply: allocate full raw requests for all zones.
    4. Otherwise (scarcity):
       a. Identify active uncapped zones with positive remaining requests (ceiling > 0).
       b. Initialize allocations to 0.0, remaining supply to available_supply_l.
       c. While remaining supply > 1e-12 and active zones exist:
          i.   Compute total priority weight among active zones.
          ii.  Calculate proposed incremental shares proportional to priority weights:
               delta_A_z = remaining_supply * (w_z / total_active_weight).
          iii. Identify zones where allocation + delta_A_z >= ceiling_z (capped zones).
          iv.  If no zones hit ceiling:
               Allocate proposed delta_A_z to all active zones, set remaining supply to 0, break.
          v.   If one or more zones hit ceiling:
               For each capped zone, set allocation = ceiling_z, subtract (ceiling_z - current_allocation)
               from remaining supply, and remove the zone from the active set.
               Iterate with the remaining active zones and remaining supply.
    5. Numerical safety clamping: enforce 0 <= A_z <= raw_requests_l[z] and sum(A_z) <= available_supply_l.
    """
    w_avail = max(0.0, float(available_supply_l))
    ceilings = {z: max(0.0, float(req)) for z, req in raw_requests_l.items()}
    total_ceil = sum(ceilings.values())

    # Invariant A: Zero supply
    if w_avail <= 1e-12:
        return {z: 0.0 for z in raw_requests_l}

    # Invariant E: Total request <= available supply
    if total_ceil <= w_avail + 1e-12:
        return {z: ceilings[z] for z in raw_requests_l}

    # Invariant B: Identify active zones with positive request
    allocations = {z: 0.0 for z in raw_requests_l}
    active_zones = [z for z in raw_requests_l if ceilings[z] > 1e-12]

    # Priority weights (>= 0.0)
    weights = {z: max(0.0, float(priorities_pct.get(z, 50.0))) for z in raw_requests_l}

    rem_supply = w_avail

    # Iterative capped water-filling
    while rem_supply > 1e-12 and active_zones:
        total_active_weight = sum(weights[z] for z in active_zones)

        if total_active_weight > 1e-12:
            shares = {z: rem_supply * (weights[z] / total_active_weight) for z in active_zones}
        else:
            shares = {z: rem_supply / len(active_zones) for z in active_zones}

        capped = []
        for z in active_zones:
            if allocations[z] + shares[z] >= ceilings[z] - 1e-12:
                capped.append(z)

        if not capped:
            for z in active_zones:
                allocations[z] += shares[z]
            rem_supply = 0.0
            break
        else:
            for z in capped:
                alloc_to_cap = ceilings[z] - allocations[z]
                allocations[z] = ceilings[z]
                rem_supply = max(0.0, rem_supply - alloc_to_cap)
                active_zones.remove(z)

    # Numerical cleanup & strict physical clamping
    for z in raw_requests_l:
        allocations[z] = min(ceilings[z], max(0.0, allocations[z]))

    total_alloc = sum(allocations.values())
    if total_alloc > w_avail + 1e-9:
        excess = total_alloc - w_avail
        for z in sorted(raw_requests_l.keys(), key=lambda k: -allocations[k]):
            if allocations[z] >= excess:
                allocations[z] -= excess
                break
            else:
                excess -= allocations[z]
                allocations[z] = 0.0

    return allocations


def allocate_water(
    requests_mm: Dict[int, float],
    areas_m2: Dict[int, float],
    stresses_pct: Dict[int, float],
    priorities_pct: Dict[int, float],
    available_water_pct: float,
    available_supply_l: Optional[float] = None,
    demands_pct: Optional[Dict[int, float]] = None,
    fis: Optional[WaterAllocationFIS] = None,
) -> AllocationResult:
    """
    Perform supervisory fuzzy water allocation and enforce hard physical supply conservation.
    """
    if fis is None:
        fis = WaterAllocationFIS()

    # Determine available supply volume in Liters
    if available_supply_l is None:
        available_supply_l = (available_water_pct / 100.0) * NOMINAL_MAX_SYSTEM_RATE_L_MIN

    # Ensure non-negative physical supply
    available_supply_l = max(0.0, float(available_supply_l))

    # Convert mm requests to Volume in Liters (1 mm over 1 m² = 1 Liter)
    requested_volumes_l = {
        z_id: max(0.0, float(req_mm * areas_m2[z_id]))
        for z_id, req_mm in requests_mm.items()
    }
    total_requested_l = sum(requested_volumes_l.values())

    zone_ids = list(requests_mm.keys())

    # HARD SAFETY 1: Zero supply available
    if available_supply_l <= 1e-9 or available_water_pct <= 1e-4:
        zero_alloc_l = {z_id: 0.0 for z_id in zone_ids}
        zero_alloc_mm = {z_id: 0.0 for z_id in zone_ids}
        unmet_l = {z_id: requested_volumes_l[z_id] for z_id in zone_ids}
        unmet_mm = {z_id: requests_mm[z_id] for z_id in zone_ids}
        factors = {z_id: 0.0 for z_id in zone_ids}
        ratios = {z_id: 0.0 if requested_volumes_l[z_id] > 0 else 1.0 for z_id in zone_ids}
        return AllocationResult(
            requested_volumes_l=requested_volumes_l,
            allocated_volumes_l=zero_alloc_l,
            unmet_volumes_l=unmet_l,
            requested_depths_mm=requests_mm,
            allocated_depths_mm=zero_alloc_mm,
            unmet_depths_mm=unmet_mm,
            allocation_factors_pct=factors,
            allocation_ratios=ratios,
            total_requested_l=total_requested_l,
            total_allocated_l=0.0,
            total_unmet_l=total_requested_l,
            available_supply_l=available_supply_l,
            available_water_pct=available_water_pct,
            is_supply_constrained=(total_requested_l > 0.0),
        )

    # HARD SAFETY 2: Zero requests from all zones
    if total_requested_l <= 1e-9:
        zero_alloc_l = {z_id: 0.0 for z_id in zone_ids}
        zero_alloc_mm = {z_id: 0.0 for z_id in zone_ids}
        factors = {z_id: 0.0 for z_id in zone_ids}
        ratios = {z_id: 1.0 for z_id in zone_ids}
        return AllocationResult(
            requested_volumes_l=requested_volumes_l,
            allocated_volumes_l=zero_alloc_l,
            unmet_volumes_l=zero_alloc_l,
            requested_depths_mm=requests_mm,
            allocated_depths_mm=zero_alloc_mm,
            unmet_depths_mm=zero_alloc_mm,
            allocation_factors_pct=factors,
            allocation_ratios=ratios,
            total_requested_l=0.0,
            total_allocated_l=0.0,
            total_unmet_l=0.0,
            available_supply_l=available_supply_l,
            available_water_pct=available_water_pct,
            is_supply_constrained=False,
        )

    # STEP 2: Evaluate WaterAllocationFIS independently for each zone
    raw_allocation_factors: Dict[int, float] = {}
    raw_allocated_volumes_l: Dict[int, float] = {}

    for z_id in zone_ids:
        # Use explicit percentage demand if provided, else normalize from depth
        max_rate_mm_min = 12.0 / 60.0
        if demands_pct is not None and z_id in demands_pct:
            norm_demand_pct = float(demands_pct[z_id])
        else:
            norm_demand_pct = min(100.0, (requests_mm[z_id] / max_rate_mm_min) * 100.0)

        factor = fis.evaluate(
            available_water=available_water_pct,
            zone_demand=norm_demand_pct,
            zone_stress=stresses_pct.get(z_id, 0.0),
            zone_priority=priorities_pct.get(z_id, 50.0),
        )
        raw_allocation_factors[z_id] = float(factor)
        # Raw allocation = requested * (factor / 100)
        raw_allocated_volumes_l[z_id] = requested_volumes_l[z_id] * (factor / 100.0)

    total_raw_allocated_l = sum(raw_allocated_volumes_l.values())

    # STEP 3: Deterministic Supply Constraint Enforcement
    # Apply bounded priority-weighted allocation (iterative weighted water-filling)
    is_constrained = (total_requested_l > available_supply_l + 1e-9) or (total_raw_allocated_l > available_supply_l + 1e-9)

    final_allocated_volumes_l = bounded_priority_weighted_allocation(
        raw_requests_l=raw_allocated_volumes_l,
        priorities_pct=priorities_pct,
        available_supply_l=available_supply_l,
    )

    # Convert allocated volume back to mm depth: Depth = Volume_L / Area_m2
    allocated_depths_mm = {
        z_id: final_allocated_volumes_l[z_id] / areas_m2[z_id]
        for z_id in zone_ids
    }

    # Calculate unmet metrics
    unmet_volumes_l = {
        z_id: max(0.0, requested_volumes_l[z_id] - final_allocated_volumes_l[z_id])
        for z_id in zone_ids
    }
    unmet_depths_mm = {
        z_id: max(0.0, requests_mm[z_id] - allocated_depths_mm[z_id])
        for z_id in zone_ids
    }
    allocation_ratios = {
        z_id: (final_allocated_volumes_l[z_id] / requested_volumes_l[z_id])
        if requested_volumes_l[z_id] > 1e-6 else 1.0
        for z_id in zone_ids
    }

    return AllocationResult(
        requested_volumes_l=requested_volumes_l,
        allocated_volumes_l=final_allocated_volumes_l,
        unmet_volumes_l=unmet_volumes_l,
        requested_depths_mm=requests_mm,
        allocated_depths_mm=allocated_depths_mm,
        unmet_depths_mm=unmet_depths_mm,
        allocation_factors_pct=raw_allocation_factors,
        allocation_ratios=allocation_ratios,
        total_requested_l=total_requested_l,
        total_allocated_l=sum(final_allocated_volumes_l.values()),
        total_unmet_l=sum(unmet_volumes_l.values()),
        available_supply_l=available_supply_l,
        available_water_pct=available_water_pct,
        is_supply_constrained=is_constrained,
    )


class MultizoneAllocationConfig(BaseModel):
    """Configuration for multizone simulation under shared supply constraints."""

    scenario: SimulationScenario = Field(default=SimulationScenario.NORMAL)
    supply_scenario: SupplyScenario = Field(default=SupplyScenario.NORMAL)
    supply_factor_override: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=150.0,
        description="Explicit supply factor override [0, 100]%"
    )
    duration_hours: int = Field(default=24, ge=1, le=720)
    timestep_minutes: int = Field(default=1, ge=1, le=60)
    seed: Optional[int] = Field(default=42)
    effective_rainfall_method: str = Field(default="usda_scs")
    zone_priorities_pct: Optional[Dict[int, float]] = Field(
        default=None,
        description="Configured priority percentage per zone"
    )


class MultizoneAllocationSimulationResult(BaseModel):
    """Complete telemetry and aggregated metrics for Phase 13 simulation."""

    scenario: str
    supply_scenario: str
    supply_factor_pct: float
    total_requested_volume_l: float
    total_allocated_volume_l: float
    total_unmet_volume_l: float
    system_allocation_ratio: float
    constrained_timesteps_count: int
    constrained_timesteps_pct: float
    max_instantaneous_allocation_l: float
    total_water_supplied_l: float
    total_water_unused_l: float
    zone_metrics: Dict[int, Dict[str, Any]]
    telemetry_records: List[Dict[str, Any]]


class MultizoneAllocationSimulator:
    """
    Orchestrates the 24-hour simulation across 3 zones under dynamic shared supply constraints.
    """

    def __init__(
        self,
        config: Optional[MultizoneAllocationConfig] = None,
        zones: Optional[List[ZoneConfig]] = None,
    ) -> None:
        self.config = config or MultizoneAllocationConfig()
        self.zones = zones or get_default_zones()
        self.total_timesteps = (self.config.duration_hours * 60) // self.config.timestep_minutes
        self.dt_hours = self.config.timestep_minutes / 60.0

        # Subsystems
        self.soil_stress_fis = SoilStressFIS()
        self.weather_stress_fis = WeatherStressFIS()
        self.water_demand_fis = WaterDemandFIS()
        self.main_irrigation_fis = MainIrrigationFIS()
        self.water_allocation_fis = WaterAllocationFIS()

        # Zone metadata maps
        self.areas_m2 = {z.zone_id: z.area_m2 for z in self.zones}
        self.priorities = (
            self.config.zone_priorities_pct or DEFAULT_ZONE_PRIORITIES_PCT.copy()
        )

        # Weather Engine
        self.weather_engine = WeatherEngine(seed=self.config.seed)

    def run(self) -> MultizoneAllocationSimulationResult:
        """Execute the 24-hour simulation with supervisory fuzzy allocation."""
        # 1. Determine available water supply factor
        if self.config.supply_factor_override is not None:
            supply_factor = float(self.config.supply_factor_override)
        elif self.config.scenario == SimulationScenario.WATER_SCARCITY:
            supply_factor = 30.0  # Physical constraint active in water scarcity
        else:
            supply_factor = SUPPLY_SCENARIO_FACTORS.get(self.config.supply_scenario, 100.0)

        # Available supply per minute in Liters
        supply_per_min_l = (supply_factor / 100.0) * NOMINAL_MAX_SYSTEM_RATE_L_MIN

        # 2. Generate meteorology & ET0
        weather_engine = WeatherEngine(
            scenario=self.config.scenario,
            seed=self.config.seed,
        )
        weather_df = weather_engine.generate_timeline(
            duration_hours=self.config.duration_hours,
            timestep_minutes=self.config.timestep_minutes,
        )
        et0_df = compute_et0_timeseries(
            weather_df,
            timestep_minutes=self.config.timestep_minutes,
        )

        # 3. Initialize soil states & zone parameters
        crop_db = CropCoefficientManager.load_crop_database()
        soil_states: Dict[int, SoilState] = {}
        zone_params: Dict[int, Dict[str, Any]] = {}

        for z in self.zones:
            z_id = z.zone_id
            crop_match = crop_db[crop_db["crop"].str.capitalize() == z.crop.name.capitalize()]
            p_frac = float(crop_match.iloc[0]["depletion_fraction_p"]) if not crop_match.empty else 0.50

            initial_state = initialize_soil_state(
                zone_config=z,
                depletion_fraction_p=p_frac,
                timestamp=str(weather_df["timestamp"].iloc[0]),
            )
            soil_states[z_id] = initial_state
            zone_params[z_id] = {
                "config": z,
                "kc": z.crop.kc,
                "zr": z.crop.root_depth_m,
                "fc": z.soil.field_capacity,
                "wp": z.soil.wilting_point,
                "sat": z.soil.saturation,
                "target_sm": z.target_moisture,
                "infilt_cap": z.soil.infiltration_rate_mm_h,
                "drain_param": z.soil.drainage_parameter,
                "area_m2": z.area_m2,
                "max_rate": 12.0,
            }

        # Telemetry storage
        records: List[Dict[str, Any]] = []

        total_requested_sys_l = 0.0
        total_allocated_sys_l = 0.0
        total_unmet_sys_l = 0.0
        constrained_timesteps = 0
        max_inst_alloc_l = 0.0

        zone_cumulative: Dict[int, Dict[str, float]] = {
            z.zone_id: {
                "requested_mm": 0.0,
                "allocated_mm": 0.0,
                "unmet_mm": 0.0,
                "requested_l": 0.0,
                "allocated_l": 0.0,
                "unmet_l": 0.0,
                "allocation_factor_sum": 0.0,
                "stress_sum": 0.0,
                "demand_sum": 0.0,
            }
            for z in self.zones
        }

        # 4. Simulation Loop (1,440 timesteps)
        for t in range(self.total_timesteps):
            row_w = weather_df.iloc[t]
            row_et = et0_df.iloc[t]
            ts = str(row_w["timestamp"])
            et0_val = float(row_et["et0"])
            p_val = float(row_w["rainfall"])

            # Compute weather stress common to all zones
            ws_val = self.weather_stress_fis.evaluate(
                temperature=float(row_w["temperature"]),
                humidity=float(row_w["humidity"]),
                solar_radiation=float(row_w["solar_radiation"]),
                wind_speed=float(row_w["wind_speed"]),
                rainfall=p_val,
            )

            # Effective rainfall common to the step
            peff_step_mm = calculate_effective_rainfall(
                rainfall_mm=p_val,
                method=self.config.effective_rainfall_method,
                timestep_minutes=self.config.timestep_minutes,
            )

            # Local Layer A: Compute unconstrained requests per zone
            step_requests_mm: Dict[int, float] = {}
            step_stresses_pct: Dict[int, float] = {}
            step_demands_pct: Dict[int, float] = {}
            step_commands_pct: Dict[int, float] = {}
            step_state_data: Dict[int, Dict[str, float]] = {}

            for z in self.zones:
                z_id = z.zone_id
                s_state = soil_states[z_id]
                zp = zone_params[z_id]
                sm_t = s_state.soil_moisture

                rsm_t = calculate_relative_soil_moisture(sm_t, zp["wp"], zp["fc"])
                err_t = calculate_moisture_error(zp["target_sm"], sm_t)

                # Soil stress
                ss_val = self.soil_stress_fis.evaluate(rsm=rsm_t, moisture_error=err_t)
                step_stresses_pct[z_id] = ss_val

                # Crop demand
                etc_z_mm = float(zp["kc"] * et0_val)
                c_deficit = calculate_crop_water_deficit(
                    etc_mm=etc_z_mm,
                    effective_rainfall_mm=peff_step_mm,
                )

                wd_val = self.water_demand_fis.evaluate(
                    etc=etc_z_mm,
                    crop_water_deficit=c_deficit,
                    effective_rainfall=peff_step_mm,
                )
                step_demands_pct[z_id] = wd_val

                # Main Irrigation FIS: unconstrained irrigation command [0, 100]%
                cmd_val = self.main_irrigation_fis.evaluate(
                    soil_stress=ss_val,
                    weather_stress=ws_val,
                    water_demand=wd_val,
                    moisture_error=err_t,
                )
                step_commands_pct[z_id] = cmd_val

                # Request in mm depth: u(t)/100 * max_rate (12.0 mm/h) * dt
                req_mm = (cmd_val / 100.0) * zp["max_rate"] * self.dt_hours
                step_requests_mm[z_id] = req_mm

                step_state_data[z_id] = {
                    "sm_t": sm_t,
                    "rsm_t": rsm_t,
                    "err_t": err_t,
                    "etc_mm": etc_z_mm,
                    "pe_mm": peff_step_mm,
                }

            # Supervisory Layer B & C: Water Allocation & Hard Constraint Enforcement
            alloc_res = allocate_water(
                requests_mm=step_requests_mm,
                areas_m2=self.areas_m2,
                stresses_pct=step_stresses_pct,
                priorities_pct=self.priorities,
                available_water_pct=supply_factor,
                available_supply_l=supply_per_min_l,
                demands_pct=step_commands_pct,
                fis=self.water_allocation_fis,
            )

            if alloc_res.is_supply_constrained:
                constrained_timesteps += 1

            total_requested_sys_l += alloc_res.total_requested_l
            total_allocated_sys_l += alloc_res.total_allocated_l
            total_unmet_sys_l += alloc_res.total_unmet_l
            if alloc_res.total_allocated_l > max_inst_alloc_l:
                max_inst_alloc_l = alloc_res.total_allocated_l

            # Layer D: Apply allocated water to each zone root-zone balance
            for z in self.zones:
                z_id = z.zone_id
                actual_app_mm = alloc_res.allocated_depths_mm[z_id]
                s_state = soil_states[z_id]

                # Update root zone water balance
                next_state = update_water_balance(
                    current_state=s_state,
                    irrigation_mm=actual_app_mm,
                    effective_rainfall_mm=peff_step_mm,
                    etc_mm=step_state_data[z_id]["etc_mm"],
                    timestep_minutes=self.config.timestep_minutes,
                    infiltration_rate_mm_h=zp["infilt_cap"],
                    drainage_parameter=zp["drain_param"],
                    timestamp=ts,
                )
                residual = next_state.water_balance_residual
                soil_states[z_id] = next_state

                # Accumulate per-zone telemetry
                zone_cumulative[z_id]["requested_mm"] += step_requests_mm[z_id]
                zone_cumulative[z_id]["allocated_mm"] += actual_app_mm
                zone_cumulative[z_id]["unmet_mm"] += alloc_res.unmet_depths_mm[z_id]
                zone_cumulative[z_id]["requested_l"] += alloc_res.requested_volumes_l[z_id]
                zone_cumulative[z_id]["allocated_l"] += alloc_res.allocated_volumes_l[z_id]
                zone_cumulative[z_id]["unmet_l"] += alloc_res.unmet_volumes_l[z_id]
                zone_cumulative[z_id]["allocation_factor_sum"] += alloc_res.allocation_factors_pct[z_id]
                zone_cumulative[z_id]["stress_sum"] += step_stresses_pct[z_id]
                zone_cumulative[z_id]["demand_sum"] += step_demands_pct[z_id]

                # Append telemetry record per zone-timestep
                records.append({
                    "timestep": t,
                    "timestamp": row_w.get("timestamp", f"2026-06-15 {t//60:02d}:{t%60:02d}:00"),
                    "scenario": self.config.scenario.value,
                    "supply_scenario": self.config.supply_scenario.value,
                    "zone_id": z_id,
                    "crop": z.crop.name,
                    "soil_type": z.soil.soil_type.value,
                    "area_m2": z.area_m2,
                    "available_water": supply_factor,
                    "zone_priority": self.priorities[z_id],
                    "zone_stress": round(step_stresses_pct[z_id], 4),
                    "zone_demand": round(step_demands_pct[z_id], 4),
                    "irrigation_command": round(step_commands_pct[z_id], 4),
                    "irrigation_request_mm": round(step_requests_mm[z_id], 4),
                    "allocation_factor": round(alloc_res.allocation_factors_pct[z_id], 4),
                    "allocated_irrigation_mm": round(actual_app_mm, 4),
                    "unmet_demand_mm": round(alloc_res.unmet_depths_mm[z_id], 4),
                    "allocation_ratio": round(alloc_res.allocation_ratios[z_id], 4),
                    "water_volume_requested_L": round(alloc_res.requested_volumes_l[z_id], 4),
                    "water_volume_allocated_L": round(alloc_res.allocated_volumes_l[z_id], 4),
                    "water_volume_unmet_L": round(alloc_res.unmet_volumes_l[z_id], 4),
                    "rainfall_mm": p_val,
                    "effective_rainfall_mm": round(step_state_data[z_id]["pe_mm"], 4),
                    "soil_moisture": round(s_state.soil_moisture, 4),
                    "moisture_error": round(step_state_data[z_id]["err_t"], 4),
                    "et0_mm_day": round(et0_val, 4),
                    "etc_mm_step": round(step_state_data[z_id]["etc_mm"], 4),
                    "water_balance_residual_mm": round(residual, 6),
                })

        # Compile Zone Summary Metrics
        zone_metrics_summary: Dict[int, Dict[str, Any]] = {}
        for z in self.zones:
            z_id = z.zone_id
            c = zone_cumulative[z_id]
            req_l = c["requested_l"]
            alloc_l = c["allocated_l"]
            unmet_l = c["unmet_l"]
            ratio = alloc_l / req_l if req_l > 0 else 1.0
            zone_metrics_summary[z_id] = {
                "zone_id": z_id,
                "crop": z.crop.name,
                "soil": z.soil.soil_type.value,
                "area_m2": z.area_m2,
                "priority_pct": self.priorities[z_id],
                "total_requested_mm": round(c["requested_mm"], 4),
                "total_allocated_mm": round(c["allocated_mm"], 4),
                "total_unmet_mm": round(c["unmet_mm"], 4),
                "total_requested_l": round(req_l, 2),
                "total_allocated_l": round(alloc_l, 2),
                "total_unmet_l": round(unmet_l, 2),
                "allocation_ratio": round(ratio, 4),
                "mean_allocation_factor": round(c["allocation_factor_sum"] / self.total_timesteps, 4),
                "mean_stress_pct": round(c["stress_sum"] / self.total_timesteps, 4),
                "mean_demand_pct": round(c["demand_sum"] / self.total_timesteps, 4),
                "final_soil_moisture": round(soil_states[z_id].soil_moisture, 4),
            }

        total_supplied_l = supply_per_min_l * self.total_timesteps
        total_unused_l = max(0.0, total_supplied_l - total_allocated_sys_l)
        sys_ratio = (
            total_allocated_sys_l / total_requested_sys_l
            if total_requested_sys_l > 0 else 1.0
        )

        return MultizoneAllocationSimulationResult(
            scenario=self.config.scenario.value,
            supply_scenario=self.config.supply_scenario.value,
            supply_factor_pct=supply_factor,
            total_requested_volume_l=round(total_requested_sys_l, 2),
            total_allocated_volume_l=round(total_allocated_sys_l, 2),
            total_unmet_volume_l=round(total_unmet_sys_l, 2),
            system_allocation_ratio=round(sys_ratio, 4),
            constrained_timesteps_count=constrained_timesteps,
            constrained_timesteps_pct=round((constrained_timesteps / self.total_timesteps) * 100.0, 2),
            max_instantaneous_allocation_l=round(max_inst_alloc_l, 4),
            total_water_supplied_l=round(total_supplied_l, 2),
            total_water_unused_l=round(total_unused_l, 2),
            zone_metrics=zone_metrics_summary,
            telemetry_records=records,
        )


def simulate_multizone_allocation(
    scenario: SimulationScenario = SimulationScenario.NORMAL,
    supply_scenario: SupplyScenario = SupplyScenario.NORMAL,
    supply_factor_override: Optional[float] = None,
    duration_hours: int = 24,
    timestep_minutes: int = 1,
    seed: int = 42,
    zone_priorities_pct: Optional[Dict[int, float]] = None,
) -> MultizoneAllocationSimulationResult:
    """
    Public functional interface for Phase 13 multizone allocation simulation.
    """
    cfg = MultizoneAllocationConfig(
        scenario=scenario,
        supply_scenario=supply_scenario,
        supply_factor_override=supply_factor_override,
        duration_hours=duration_hours,
        timestep_minutes=timestep_minutes,
        seed=seed,
        zone_priorities_pct=zone_priorities_pct,
    )
    simulator = MultizoneAllocationSimulator(config=cfg)
    return simulator.run()
