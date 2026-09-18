"""Water Allocation Router."""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Body

from backend.app.schemas.allocation import (
    AllocationEvaluateRequest,
    AllocationEvaluateResponse,
    AllocationSweepRequest,
)
from backend.app.services.allocation_service import AllocationService
from backend.app.database.client import DatabaseRepository, get_db_repository

router = APIRouter(prefix="/allocation", tags=["Water Allocation"])
allocation_service = AllocationService()


@router.get("/config")
def get_allocation_config():
    """Return supervisory allocation engine configuration and default zone properties."""
    return {
        "engine": "Two-Layer Hierarchical Supervisory Water Allocation",
        "layer_b": "Mamdani Water Allocation FIS (Scarcity x Request -> Scaling)",
        "layer_c": "Deterministic Bounded Priority-Weighted Water-Filling",
        "invariants": [
            "Sum of final allocations <= Available supply (tolerance 1e-6)",
            "Allocated water per zone <= Requested water",
            "Zero artificial water creation",
            "Zero allocation when available supply is zero",
            "Zero allocation when requested water is zero",
        ],
        "default_zones": [
            {"id": 1, "crop": "Tomato", "soil": "Loam", "area_m2": 100.0, "priority_weight": 1.0},
            {"id": 2, "crop": "Potato", "soil": "Sandy Loam", "area_m2": 150.0, "priority_weight": 0.8},
            {"id": 3, "crop": "Maize", "soil": "Clay Loam", "area_m2": 200.0, "priority_weight": 0.6},
        ],
    }


@router.post("/evaluate", response_model=AllocationEvaluateResponse)
def evaluate_allocation(
    req: AllocationEvaluateRequest,
    db: DatabaseRepository = Depends(get_db_repository),
):
    """
    Evaluate multi-zone water allocation under constrained shared supply.
    Enforces Layer B fuzzy inference and Layer C deterministic bounded priority-weighted water-filling.
    """
    try:
        return allocation_service.evaluate(req, db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Allocation evaluation error: {str(e)}")


@router.get("/results/{simulation_id}")
def get_simulation_allocation_results(
    simulation_id: str,
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Retrieve allocation time-series and summary results for a completed simulation run."""
    sim = db.get_simulation_run(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
    
    timeseries = db.get_timeseries(simulation_id)
    return {
        "simulation_id": simulation_id,
        "scenario": sim.scenario,
        "supply_scenario": sim.supply_scenario,
        "summary_metrics": sim.summary_metrics,
        "records_count": len(timeseries),
    }


@router.post("/sweep")
def simulate_supply_sweep(
    req: AllocationSweepRequest,
    db: DatabaseRepository = Depends(get_db_repository),
):
    """
    Simulate allocation curves as available supply sweeps from 10% to 100%.
    Demonstrates priority-weighted scarcity partitioning.
    """
    try:
        return allocation_service.compute_supply_sweep(
            requests_mm=req.requests_mm,
            priorities_pct=req.priorities_pct,
            db=db,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supply sweep error: {str(e)}")

