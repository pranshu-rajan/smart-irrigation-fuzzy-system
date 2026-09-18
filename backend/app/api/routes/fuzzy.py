"""Fuzzy Controller Diagnostics and Explorer Router."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Body

from backend.app.schemas.fuzzy import (
    ControllerOverview,
    FuzzyVariableSchema,
    FuzzyRuleSchema,
    FuzzyEvaluateRequest,
    FuzzyEvaluateResponse,
)
from backend.app.services.fuzzy_service import FuzzyService

router = APIRouter(prefix="/fuzzy", tags=["Fuzzy Inference"])
fuzzy_service = FuzzyService()


@router.get("/overview", response_model=List[ControllerOverview])
@router.get("/controllers", response_model=List[ControllerOverview])
def get_controllers_overview():
    """List all 5 Fuzzy Inference Subsystems with inputs, outputs, rule counts, and descriptions."""
    return fuzzy_service.list_controllers()


@router.get("/controllers/{controller}", response_model=ControllerOverview)
def get_single_controller_overview(controller: str):
    """Retrieve metadata overview of a single fuzzy inference subsystem."""
    controllers = fuzzy_service.list_controllers()
    for c in controllers:
        if c.name.lower() == controller.lower() or c.name.replace("_", "").lower() == controller.replace("_", "").lower():
            return c
    raise HTTPException(
        status_code=404,
        detail=f"Controller '{controller}' not found. Valid: {[c.name for c in controllers]}",
    )


@router.get("/{controller}/variables", response_model=List[FuzzyVariableSchema])
@router.get("/controllers/{controller}/membership-functions", response_model=List[FuzzyVariableSchema])
def get_controller_variables(controller: str):
    """Retrieve membership function curves and universe ranges for a fuzzy controller."""
    vars_list = fuzzy_service.get_variables_for_controller(controller)
    if not vars_list:
        raise HTTPException(
            status_code=404,
            detail=f"Controller '{controller}' not recognized. Valid options: {list(fuzzy_service.CONTROLLERS.keys())}",
        )
    return vars_list


@router.get("/{controller}/rules", response_model=List[FuzzyRuleSchema])
@router.get("/controllers/{controller}/rules", response_model=List[FuzzyRuleSchema])
def get_controller_rules(controller: str):
    """Retrieve the linguistic rule base of a specific fuzzy subsystem."""
    rules_list = fuzzy_service.get_rules_for_controller(controller)
    if not rules_list:
        raise HTTPException(
            status_code=404,
            detail=f"Controller '{controller}' not recognized. Valid options: {list(fuzzy_service.CONTROLLERS.keys())}",
        )
    return rules_list


@router.post("/evaluate", response_model=FuzzyEvaluateResponse)
def evaluate_fuzzy_step(req: FuzzyEvaluateRequest):
    """Execute live fuzzy inference step, returning defuzzified output and rule activation weights."""
    try:
        controller_name = req.resolved_controller
        return fuzzy_service.evaluate_controller(controller_name, req.inputs)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


@router.post("/controllers/{controller}/evaluate", response_model=FuzzyEvaluateResponse)
def evaluate_named_controller(controller: str, inputs: Dict[str, float] = Body(...)):
    """Execute live fuzzy inference step for a named controller."""
    try:
        return fuzzy_service.evaluate_controller(controller, inputs)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

