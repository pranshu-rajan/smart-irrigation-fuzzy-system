"""Optimization (Offline PSO) Router."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.schemas.allocation import (
    OptimizationRunRequest,
    OptimizationSummaryResponse,
    ParameterComparisonItem,
)
from backend.app.services.optimization_service import OptimizationService
from backend.app.database.client import DatabaseRepository, get_db_repository
from backend.app.core.security import get_current_user, User

router = APIRouter(prefix="/optimization", tags=["Optimization"])
optimization_service = OptimizationService()


@router.get("", response_model=OptimizationSummaryResponse)
@router.get("/summary", response_model=OptimizationSummaryResponse)
def get_optimization_summary(
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Retrieve the latest PSO optimization summary, convergence history, and parameters."""
    return optimization_service.get_latest_summary(db=db)


@router.get("/parameters", response_model=List[ParameterComparisonItem])
def get_optimization_parameters():
    """Retrieve the 18-parameter space specifications with baseline vs optimized values."""
    return optimization_service.get_parameter_specs()


@router.get("/{run_id}", response_model=OptimizationSummaryResponse)
def get_optimization_by_id(
    run_id: str,
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Retrieve optimization summary by run ID (or 'latest')."""
    return optimization_service.get_latest_summary(db=db)


@router.get("/{run_id}/convergence")
def get_optimization_convergence(
    run_id: str,
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Retrieve the fitness convergence trajectory across iterations."""
    summary = optimization_service.get_latest_summary(db=db)
    return {
        "run_id": summary.id,
        "iterations": summary.iterations,
        "convergence_history": summary.convergence_history,
        "best_fitness": summary.best_fitness,
    }


@router.get("/{run_id}/comparison")
def get_optimization_comparison(
    run_id: str,
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Retrieve baseline vs optimized performance metric comparison."""
    summary = optimization_service.get_latest_summary(db=db)
    return {
        "run_id": summary.id,
        "comparison": summary.comparison,
    }


@router.get("/{run_id}/parameters", response_model=List[ParameterComparisonItem])
def get_optimization_parameters_for_run(run_id: str):
    """Retrieve 18 parameter bounds and values for an optimization run."""
    return optimization_service.get_parameter_specs()



@router.post("/run", response_model=OptimizationSummaryResponse)
def trigger_optimization_run(
    req: OptimizationRunRequest,
    async_mode: bool = Query(default=True, description="Run in background thread to avoid HTTP timeout"),
    user: User = Depends(get_current_user),
    db: DatabaseRepository = Depends(get_db_repository),
):
    """
    Trigger offline Particle Swarm Optimization (PSO) to tune the 18 parameters of MainIrrigationFIS.
    Enforces strict offline execution (never acts as an online controller).
    """
    try:
        return optimization_service.run_optimization(
            request=req,
            user_id=user.id,
            db=db,
            async_run=async_mode,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PSO execution error: {str(e)}")
