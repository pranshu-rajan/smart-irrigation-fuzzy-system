"""Simulations Router."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.schemas.simulation import (
    SimulationRunRequest,
    SimulationSummaryResponse,
    TimeseriesResponse,
)
from backend.app.database.models import SimulationRunRecord
from backend.app.core.security import get_current_user, User
from backend.app.database.client import DatabaseRepository, get_db_repository
from backend.app.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulations", tags=["Simulations"])
simulation_service = SimulationService()


def _to_summary_response(r: SimulationRunRecord) -> SimulationSummaryResponse:
    started_str = r.started_at.isoformat() if hasattr(r.started_at, "isoformat") else str(r.started_at)
    completed_str = (
        r.completed_at.isoformat()
        if r.completed_at and hasattr(r.completed_at, "isoformat")
        else (str(r.completed_at) if r.completed_at else None)
    )
    created_str = r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at)

    return SimulationSummaryResponse(
        id=r.id,
        user_id=r.user_id,
        scenario=r.scenario,
        duration_hours=r.duration_hours,
        timestep_minutes=r.timestep_minutes,
        status=r.status,
        controller_type=r.controller_type,
        supply_scenario=r.supply_scenario,
        summary_metrics=r.summary_metrics or {},
        started_at=started_str,
        completed_at=completed_str,
        created_at=created_str,
    )


@router.post("/run", response_model=SimulationSummaryResponse)
@router.post("", response_model=SimulationSummaryResponse)
def run_simulation(
    req: SimulationRunRequest,
    user: User = Depends(get_current_user),
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Execute a closed-loop multizone simulation run."""
    try:
        record = simulation_service.run_simulation(
            request=req,
            user_id=user.id,
        )
        return _to_summary_response(record)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@router.post("/scenario", response_model=SimulationSummaryResponse)
def run_single_scenario(
    scenario_name: str = Query(..., description="Scenario name e.g. Normal, Heatwave, Water Scarcity"),
    user: User = Depends(get_current_user),
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Execute a closed-loop multizone simulation for a specific named scenario."""
    try:
        req = SimulationRunRequest(scenario=scenario_name)
        record = simulation_service.run_simulation(request=req, user_id=user.id)
        return _to_summary_response(record)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario simulation error: {str(e)}")


@router.post("/all-scenarios", response_model=Dict[str, Any])
def run_all_scenarios_comparison(
    user: User = Depends(get_current_user),
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Execute simulation across all 6 environmental scenarios and generate comparative analytics."""
    scenarios = ["Normal", "Hot & Dry", "Rainy", "Cloudy", "Heatwave", "Water Scarcity"]
    results = {}
    for s in scenarios:
        req = SimulationRunRequest(scenario=s)
        record = simulation_service.run_simulation(request=req, user_id=user.id)
        results[s] = {
            "simulation_id": record.id,
            "summary_metrics": record.summary_metrics,
            "status": record.status,
        }
    return {
        "status": "success",
        "scenarios_evaluated": len(scenarios),
        "results": results,
    }



@router.get("", response_model=List[SimulationSummaryResponse])
def list_simulations(
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: DatabaseRepository = Depends(get_db_repository),
):
    """List past simulation summaries."""
    records = db.get_simulation_runs(limit=limit, user_id=user.id)
    return [_to_summary_response(r) for r in records]


@router.get("/{sim_id}", response_model=SimulationSummaryResponse)
def get_simulation(
    sim_id: str,
    user: User = Depends(get_current_user),
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Get simulation summary by ID."""
    r = db.get_simulation_run(sim_id, user.id)
    if not r:
        raise HTTPException(status_code=404, detail=f"Simulation {sim_id} not found")
    return _to_summary_response(r)


@router.get("/{sim_id}/timeseries", response_model=TimeseriesResponse)
def get_simulation_timeseries(
    sim_id: str,
    zone_id: Optional[int] = Query(default=None, description="Optional zone ID filter"),
    stride: int = Query(default=1, ge=1, le=10, description="Step downsample stride"),
    user: User = Depends(get_current_user),
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Retrieve time-series records for plotting."""
    sim = db.get_simulation_run(sim_id, user.id)
    if not sim:
        raise HTTPException(status_code=404, detail=f"Simulation {sim_id} not found")

    raw_records = db.get_timeseries(sim_id, user.id)
    if zone_id is not None:
        raw_records = [r for r in raw_records if r.get("zone_id") == zone_id]

    if stride > 1:
        raw_records = raw_records[::stride]

    zone_ids = set(r.get("zone_id") for r in raw_records if "zone_id" in r)
    timesteps = len(set(r.get("step") for r in raw_records if "step" in r))

    return TimeseriesResponse(
        simulation_id=sim_id,
        total_records=len(raw_records),
        zone_count=len(zone_ids) or 3,
        timesteps=timesteps or len(raw_records),
        records=raw_records,
    )
