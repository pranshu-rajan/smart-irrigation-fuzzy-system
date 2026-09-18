"""Fuzzy Service exposing the five FIS controllers, MFs, rules, and live diagnostic evaluation."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np

from backend.app.schemas.fuzzy import (
    ControllerOverview,
    FuzzyVariableSchema,
    LinguisticSetSchema,
    FuzzyRuleSchema,
    FuzzyEvaluateResponse,
    RuleActivationDetail,
)
from fuzzy_engine.soil_stress import SoilStressFIS
from fuzzy_engine.weather_stress import WeatherStressFIS
from fuzzy_engine.water_demand import WaterDemandFIS
from fuzzy_engine.irrigation import MainIrrigationFIS
from fuzzy_engine.water_allocation import WaterAllocationFIS
from fuzzy_engine.universes import get_fuzzy_variable


class FuzzyService:
    """Service providing read-only inspection and live diagnostics for all 5 FIS."""

    CONTROLLERS: Dict[str, Dict[str, Any]] = {
        "soil_stress": {
            "name": "soil_stress",
            "title": "FIS 1: Soil Stress FIS",
            "description": "Evaluates root-zone moisture stress based on Relative Soil Moisture (RSM) and Tracking Error.",
            "class": SoilStressFIS,
            "inputs": ["rsm", "moisture_error"],
            "output": "soil_stress",
            "unit": "%",
        },
        "weather_stress": {
            "name": "weather_stress",
            "title": "FIS 2: Weather Stress FIS",
            "description": "Assesses atmospheric evaporative demand and climate stress across 5 meteorological inputs.",
            "class": WeatherStressFIS,
            "inputs": ["temperature", "humidity", "solar_radiation", "wind_speed", "rainfall"],
            "output": "weather_stress",
            "unit": "%",
        },
        "water_demand": {
            "name": "water_demand",
            "title": "FIS 3: Water Demand FIS",
            "description": "Synthesizes crop evapotranspiration (ETc), water deficit, and effective rainfall into water demand.",
            "class": WaterDemandFIS,
            "inputs": ["etc", "crop_water_deficit", "effective_rainfall"],
            "output": "water_demand",
            "unit": "%",
        },
        "main_irrigation": {
            "name": "main_irrigation",
            "title": "FIS 4: Main Irrigation FIS",
            "description": "Supervisory controller fusing soil stress, weather stress, water demand, and error into an actuator command.",
            "class": MainIrrigationFIS,
            "inputs": ["soil_stress", "weather_stress", "water_demand", "moisture_error"],
            "output": "irrigation_command",
            "unit": "%",
        },
        "water_allocation": {
            "name": "water_allocation",
            "title": "FIS 5: Water Allocation FIS",
            "description": "Arbitrates shared constrained water supply among competing zones based on priority and stress.",
            "class": WaterAllocationFIS,
            "inputs": ["available_water", "zone_demand", "zone_stress", "zone_priority"],
            "output": "zone_allocation",
            "unit": "%",
        },
    }

    def __init__(self, config_path: str = "config/fuzzy_config.json") -> None:
        self.config_path = Path(config_path)
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.fuzzy_config = json.load(f)

        # Pre-instantiate singletons for fast diagnostic evaluations
        self.instances: Dict[str, Any] = {
            "soil_stress": SoilStressFIS(),
            "weather_stress": WeatherStressFIS(),
            "water_demand": WaterDemandFIS(),
            "main_irrigation": MainIrrigationFIS(),
            "water_allocation": WaterAllocationFIS(),
        }

    def list_controllers(self) -> List[ControllerOverview]:
        """Return high-level metadata for all five controllers."""
        controllers = []
        for key, meta in self.CONTROLLERS.items():
            fis_inst = self.instances[key]
            controllers.append(
                ControllerOverview(
                    id=key,
                    name=key,
                    title=meta["title"],
                    description=meta["description"],
                    inputs=meta["inputs"],
                    output=meta["output"],
                    rule_count=len(fis_inst.RULES),
                )
            )
        return controllers

    def get_controller_overview(self, name: str) -> Optional[ControllerOverview]:
        meta = self.CONTROLLERS.get(name.lower())
        if not meta:
            return None
        fis_inst = self.instances[name.lower()]
        return ControllerOverview(
            name=name.lower(),
            title=meta["title"],
            description=meta["description"],
            inputs=meta["inputs"],
            output=meta["output"],
            rule_count=len(fis_inst.RULES),
        )

    def get_variables_for_controller(self, name: str) -> List[FuzzyVariableSchema]:
        """Generate mathematical membership function curve coordinates for a controller's variables."""
        meta = self.CONTROLLERS.get(name.lower())
        if not meta:
            return []

        var_names = meta["inputs"] + [meta["output"]]
        var_schemas = []

        for vname in var_names:
            vconfig = self.fuzzy_config["variables"].get(vname)
            if not vconfig:
                continue

            # Generate plotting coordinates across universe
            min_val = float(vconfig["min"])
            max_val = float(vconfig["max"])
            x_vals = np.linspace(min_val, max_val, 150)

            var_obj = get_fuzzy_variable(vname)
            curve_points: Dict[str, List[List[float]]] = {}
            set_schemas: Dict[str, LinguisticSetSchema] = {}

            for set_name, mf_set in var_obj.sets.items():
                y_vals = mf_set.evaluate(x_vals)
                curve_points[set_name] = [
                    [round(float(x), 4), round(float(y), 4)]
                    for x, y in zip(x_vals, y_vals)
                ]
                raw_params = getattr(mf_set, "params", None) or getattr(mf_set, "parameters", [])
                set_schemas[set_name] = LinguisticSetSchema(
                    name=set_name,
                    type=mf_set.mf_type,
                    parameters=[round(float(p), 4) for p in raw_params],
                )

            var_schemas.append(
                FuzzyVariableSchema(
                    name=vconfig["name"],
                    display_name=vconfig["display_name"],
                    unit=vconfig["unit"],
                    min=min_val,
                    max=max_val,
                    resolution=vconfig["resolution"],
                    fis_role=vconfig["fis_role"],
                    associated_fis=vconfig["associated_fis"],
                    sets=set_schemas,
                    curve_points=curve_points,
                )
            )
        return var_schemas

    def get_rules_for_controller(self, name: str) -> List[FuzzyRuleSchema]:
        """Extract all explicit linguistic rules for a controller."""
        meta = self.CONTROLLERS.get(name.lower())
        if not meta:
            return []

        fis_inst = self.instances[name.lower()]
        rules: List[FuzzyRuleSchema] = []

        if name.lower() == "soil_stress":
            # SoilStressFIS uses tuple RULES: (rsm_term, error_term, consequent)
            for idx, r in enumerate(fis_inst.RULES, start=1):
                cond = f"IF Relative Soil Moisture is {r[0].replace('_', ' ').title()} AND Moisture Error is {r[1].replace('_', ' ').title()}"
                rules.append(
                    FuzzyRuleSchema(
                        id=idx,
                        conditions_text=cond,
                        antecedents={"rsm": r[0], "moisture_error": r[1]},
                        consequent=r[2],
                        description=f"Rule {idx}: {cond} THEN Soil Stress is {r[2].replace('_', ' ').title()}",
                    )
                )
        else:
            # Other FIS use Dict rule definitions
            for r in fis_inst.RULES:
                cond_parts = []
                for var, term in r["antecedents"].items():
                    if isinstance(term, list):
                        term_str = " OR ".join(t.replace("_", " ").title() for t in term)
                    else:
                        term_str = str(term).replace("_", " ").title()
                    cond_parts.append(f"{var.replace('_', ' ').title()} is ({term_str})")
                cond_text = "IF " + " AND ".join(cond_parts)
                rules.append(
                    FuzzyRuleSchema(
                        id=r["id"],
                        conditions_text=cond_text,
                        antecedents=r["antecedents"],
                        consequent=r["consequent"],
                        description=r.get("desc"),
                    )
                )
        return rules

    def evaluate_controller(
        self,
        name: str,
        inputs: Dict[str, float],
    ) -> FuzzyEvaluateResponse:
        """Execute real Python Mamdani inference with detailed activation telemetry."""
        meta = self.CONTROLLERS.get(name.lower())
        if not meta:
            raise ValueError(f"Unknown controller '{name}'")

        fis_inst = self.instances[name.lower()]

        # 1. Compute crisp evaluation
        if name.lower() == "soil_stress":
            val = fis_inst.evaluate(
                rsm=inputs.get("rsm", 0.5),
                moisture_error=inputs.get("moisture_error", 0.0),
            )
        elif name.lower() == "weather_stress":
            val = fis_inst.evaluate(
                temperature=inputs.get("temperature", 28.0),
                humidity=inputs.get("humidity", 50.0),
                solar_radiation=inputs.get("solar_radiation", 600.0),
                wind_speed=inputs.get("wind_speed", 3.0),
                rainfall=inputs.get("rainfall", 0.0),
            )
        elif name.lower() == "water_demand":
            val = fis_inst.evaluate(
                etc=inputs.get("etc", 5.0),
                crop_water_deficit=inputs.get("crop_water_deficit", 3.0),
                effective_rainfall=inputs.get("effective_rainfall", 0.0),
            )
        elif name.lower() == "main_irrigation":
            val = fis_inst.evaluate(
                soil_stress=inputs.get("soil_stress", 40.0),
                weather_stress=inputs.get("weather_stress", 40.0),
                water_demand=inputs.get("water_demand", 50.0),
                moisture_error=inputs.get("moisture_error", 0.0),
            )
        elif name.lower() == "water_allocation":
            val = fis_inst.evaluate(
                available_water=inputs.get("available_water", 100.0),
                zone_demand=inputs.get("zone_demand", 50.0),
                zone_stress=inputs.get("zone_stress", 40.0),
                zone_priority=inputs.get("zone_priority", 70.0),
            )
        else:
            raise ValueError(f"Controller {name} not supported for evaluate")

        # 2. Extract fuzzified memberships for all inputs
        fuzzified: Dict[str, Dict[str, float]] = {}
        for in_name in meta["inputs"]:
            var_obj = get_fuzzy_variable(in_name)
            in_val = inputs.get(in_name, float(var_obj.universe.min_val))
            fuzzified[in_name] = {
                set_name: round(float(mf_set.evaluate(in_val)), 4)
                for set_name, mf_set in var_obj.sets.items()
            }

        # 3. Compute active rule firings
        all_rules = self.get_rules_for_controller(name.lower())
        active_rules = []

        for r in all_rules:
            # Compute firing strength (minimum T-norm)
            firing_strengths = []
            for ant_var, ant_term in r.antecedents.items():
                if isinstance(ant_term, list):
                    # OR within set
                    s_val = max(fuzzified.get(ant_var, {}).get(t, 0.0) for t in ant_term)
                else:
                    s_val = fuzzified.get(ant_var, {}).get(ant_term, 0.0)
                firing_strengths.append(s_val)

            w = min(firing_strengths) if firing_strengths else 0.0
            if w > 1e-4:
                active_rules.append(
                    RuleActivationDetail(
                        rule_id=r.id,
                        conditions=r.conditions_text,
                        consequent=r.consequent,
                        weight=round(float(w), 4),
                        is_active=True,
                    )
                )

        active_rules.sort(key=lambda x: x.weight, reverse=True)

        return FuzzyEvaluateResponse(
            controller_name=name.lower(),
            inputs=inputs,
            fuzzified_inputs=fuzzified,
            active_rules=active_rules[:15],  # Top active rules
            aggregated_output_name=meta["output"],
            crisp_output=round(float(val), 2),
            outputs={meta["output"]: round(float(val), 2)},
            firing_weights=[r.weight for r in active_rules],
            unit=meta["unit"],
        )


fuzzy_service = FuzzyService()
