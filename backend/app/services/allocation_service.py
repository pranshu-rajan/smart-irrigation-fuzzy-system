"""Water Allocation Service.

Orchestrates Phase 13 Multi-Zone Resource Management:
1. Layer A: Zone demands & physiological stress input.
2. Layer B: WaterAllocationFIS fuzzy inference for unconstrained allocation factor.
3. Layer C: Deterministic bounded priority-weighted water-filling enforcing strict conservation:
   - Sum(Allocated_z) <= Available_Supply
   - Allocated_z <= Requested_z
   - No water creation out of thin air.
"""

from typing import Dict, List, Optional, Any
import numpy as np

from fuzzy_engine.water_allocation import WaterAllocationFIS
from simulation.water_allocation import bounded_priority_weighted_allocation
from backend.app.schemas.allocation import (
    AllocationEvaluateRequest,
    AllocationEvaluateResponse,
    ZoneAllocationDetail,
)
from backend.app.database.client import DatabaseRepository


class AllocationService:
    def __init__(self):
        self.allocation_fis = WaterAllocationFIS()

    def evaluate(
        self,
        request: AllocationEvaluateRequest,
        db: Optional[DatabaseRepository] = None,
    ) -> AllocationEvaluateResponse:
        """
        Evaluate multi-zone water allocation given zone requests, stresses, and priorities.
        """
        # Fetch zones to get area_m2
        zone_configs = {}
        if db:
            zones_db = db.get_all_zones()
            for z in zones_db:
                zone_configs[z.zone_id] = z
        
        # Prepare zone data
        zones_detail: List[ZoneAllocationDetail] = []
        raw_requests_l: Dict[int, float] = {}
        priorities_pct: Dict[int, float] = {}
        stresses_pct: Dict[int, float] = {}
        raw_allocation_factors: Dict[int, float] = {}

        total_requested_l = 0.0

        for zone_id, req_mm in request.requests_mm.items():
            zid = int(zone_id)
            z_cfg = zone_configs.get(zid)
            area_m2 = float(z_cfg.area_m2) if z_cfg else 100.0
            
            # Request volume (L) = mm * m2
            req_vol_l = max(0.0, float(req_mm)) * area_m2
            raw_requests_l[zid] = req_vol_l
            total_requested_l += req_vol_l

            priority = 50.0
            if request.priorities_pct and zid in request.priorities_pct:
                priority = float(request.priorities_pct[zid])
            elif z_cfg:
                raw_p = float(getattr(z_cfg, 'priority_weight', getattr(z_cfg, 'priority', 50.0)))
                priority = raw_p * 10.0 if raw_p <= 10.0 else raw_p
            priorities_pct[zid] = min(100.0, max(0.0, priority))

            stress = 40.0
            if request.stresses_pct and zid in request.stresses_pct:
                stress = float(request.stresses_pct[zid])
            stresses_pct[zid] = min(100.0, max(0.0, stress))

            # Run FIS Layer B
            # Inputs: available_water [0-100], zone_demand [0-100], zone_stress [0-100], zone_priority [0-100]
            # Map request_mm to demand % (e.g., 0 to 10mm -> 0 to 100%)
            norm_demand = min(100.0, max(0.0, (req_mm / 10.0) * 100.0 if req_mm > 0 else 0.0))
            raw_factor = self.allocation_fis.evaluate(
                available_water=request.available_water_pct,
                zone_demand=norm_demand,
                zone_stress=stresses_pct[zid],
                zone_priority=priorities_pct[zid],
            )
            raw_allocation_factors[zid] = float(raw_factor)

        # Available supply in Liters
        if request.available_supply_l is not None:
            available_supply_l = max(0.0, float(request.available_supply_l))
        else:
            # Fraction of total requests or nominal system capacity
            available_supply_l = total_requested_l * (request.available_water_pct / 100.0)

        # Layer C: Deterministic bounded priority-weighted allocation
        allocated_volumes_l = bounded_priority_weighted_allocation(
            raw_requests_l=raw_requests_l,
            priorities_pct=priorities_pct,
            available_supply_l=available_supply_l,
        )

        total_allocated_l = sum(allocated_volumes_l.values())
        total_unmet_l = max(0.0, total_requested_l - total_allocated_l)
        is_constrained = available_supply_l < total_requested_l - 1e-6

        # Assemble details
        for zid, req_vol_l in raw_requests_l.items():
            z_cfg = zone_configs.get(zid)
            area_m2 = float(z_cfg.area_m2) if z_cfg else 100.0
            req_mm = req_vol_l / area_m2 if area_m2 > 0 else 0.0
            alloc_l = allocated_volumes_l.get(zid, 0.0)
            alloc_mm = alloc_l / area_m2 if area_m2 > 0 else 0.0
            unmet_l = max(0.0, req_vol_l - alloc_l)
            unmet_mm = unmet_l / area_m2 if area_m2 > 0 else 0.0
            fulfillment = (alloc_l / req_vol_l) if req_vol_l > 1e-6 else 1.0

            zones_detail.append(
                ZoneAllocationDetail(
                    zone_id=zid,
                    area_m2=area_m2,
                    requested_depth_mm=round(req_mm, 2),
                    requested_volume_l=round(req_vol_l, 2),
                    raw_allocation_factor_pct=round(raw_allocation_factors.get(zid, 0.0), 2),
                    allocated_depth_mm=round(alloc_mm, 2),
                    allocated_volume_l=round(alloc_l, 2),
                    unmet_depth_mm=round(unmet_mm, 2),
                    unmet_volume_l=round(unmet_l, 2),
                    fulfillment_ratio=round(min(1.0, fulfillment), 4),
                )
            )

        sys_fulfillment = (total_allocated_l / total_requested_l) if total_requested_l > 1e-6 else 1.0

        return AllocationEvaluateResponse(
            available_water_pct=round(request.available_water_pct, 2),
            available_supply_l=round(available_supply_l, 2),
            total_requested_l=round(total_requested_l, 2),
            total_allocated_l=round(total_allocated_l, 2),
            total_unmet_l=round(total_unmet_l, 2),
            system_fulfillment_ratio=round(min(1.0, sys_fulfillment), 4),
            is_supply_constrained=is_constrained,
            zones=sorted(zones_detail, key=lambda z: z.zone_id),
        )

    def compute_supply_sweep(
        self,
        requests_mm: Dict[int, float],
        priorities_pct: Optional[Dict[int, float]] = None,
        db: Optional[DatabaseRepository] = None,
    ) -> List[Dict[str, Any]]:
        """
        Sweeps available supply from 10% to 100% and returns allocation trajectories per zone.
        """
        sweep_points = []
        for supply_pct in range(10, 110, 10):
            req = AllocationEvaluateRequest(
                available_water_pct=float(supply_pct),
                requests_mm=requests_mm,
                priorities_pct=priorities_pct,
            )
            res = self.evaluate(req, db=db)
            point = {
                "available_water_pct": supply_pct,
                "available_supply_l": res.available_supply_l,
                "total_allocated_l": res.total_allocated_l,
                "fulfillment_ratio": res.system_fulfillment_ratio,
                "zones": {z.zone_id: z.allocated_volume_l for z in res.zones},
            }
            sweep_points.append(point)
        return sweep_points
