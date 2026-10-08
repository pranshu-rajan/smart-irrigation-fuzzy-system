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
    EndToEndArchitectureRequest,
    EndToEndArchitectureResponse,
    ZoneAllocationOutput,
)
from fuzzy_engine.soil_stress import SoilStressFIS
from fuzzy_engine.weather_stress import WeatherStressFIS
from fuzzy_engine.water_demand import WaterDemandFIS
from fuzzy_engine.irrigation import MainIrrigationFIS
from fuzzy_engine.water_allocation import WaterAllocationFIS
from optimization.active_parameters import build_active_main_irrigation_fis
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
            "main_irrigation": build_active_main_irrigation_fis() or MainIrrigationFIS(),
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

    def _canonical_controller(self, name: str) -> str:
        key = str(name or "").strip().lower().replace("-", "_").replace(" ", "_")
        return key.removeprefix("controllers_")

    def get_rules_for_controller(self, name: str) -> List[FuzzyRuleSchema]:
        """Extract all explicit linguistic rules for a controller."""
        name = self._canonical_controller(name)
        meta = self.CONTROLLERS.get(name)
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
        name = self._canonical_controller(name)
        meta = self.CONTROLLERS.get(name)
        if not meta:
            raise ValueError(f"Unknown controller '{name}'")

        fis_inst = self.instances[name]

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


    def evaluate_architecture(
        self,
        req: Any,
    ) -> Any:
        """Execute end-to-end 5-stage hierarchical fuzzy architecture evaluation.
        
        Matches MATLAB evaluate_fuzzy_architecture.m with 100% mathematical parity.
        """
        from backend.app.schemas.fuzzy import (
            EndToEndArchitectureResponse,
            ZoneAllocationOutput,
        )
        from simulation.water_allocation import bounded_priority_weighted_allocation

        sm_curr = float(req.soil_moisture)
        target_sm = float(req.target_moisture)
        t_c = float(req.temperature)
        rh_pct = float(req.humidity)
        rs_w_m2 = float(req.solar_radiation)
        u2_m_s = float(req.wind_speed)
        p_mm = float(req.rainfall)
        res_pct = float(req.reservoir_storage_pct)

        # 1. Instantaneous FAO-56 Reference ET0
        z = max(-100.0, 53.0)
        p_kpa = 101.3 * (((293.0 - 0.0065 * z) / 293.0) ** 5.26)
        gamma = 0.665e-3 * p_kpa
        es = 0.6108 * np.exp((17.27 * t_c) / (t_c + 237.3))
        ea = es * (max(0.0, min(100.0, rh_pct)) / 100.0)
        delta = (4098.0 * es) / ((t_c + 237.3) ** 2)
        rs_mj = rs_w_m2 * 0.0036
        rns = 0.77 * rs_mj
        sigma = 2.043e-10
        t_k = t_c + 273.16
        f_cloud = max(0.05, min(1.0, rs_w_m2 / 1000.0))
        rnl = sigma * (t_k ** 4) * (0.34 - 0.14 * np.sqrt(max(0.0, ea))) * (1.35 * f_cloud - 0.35)
        rn = rns - rnl
        g = 0.10 * rn if rn > 0 else 0.50 * rn
        u2_clamped = max(0.1, u2_m_s)
        num = 0.408 * delta * (rn - g) + gamma * (37.0 / (t_c + 273.0)) * u2_clamped * (es - ea)
        den = delta + gamma * (1.0 + 0.34 * u2_clamped)
        et0_val = max(0.0, (num / den) * 24.0)

        # 2. Stage 2: Weather Stress FIS
        weather_stress = float(self.instances["weather_stress"].evaluate(
            temperature=t_c,
            humidity=rh_pct,
            solar_radiation=rs_w_m2,
            wind_speed=u2_m_s,
            rainfall=p_mm,
        ))

        # 3. Stage 1 & 3 baseline reference (Loam / Tomato)
        fc_ref, wp_ref = 70.0, 25.0
        rsm_ref = max(0.0, min(1.0, (sm_curr - wp_ref) / (fc_ref - wp_ref)))
        err_ref = max(-30.0, min(30.0, target_sm - sm_curr))

        soil_stress = float(self.instances["soil_stress"].evaluate(
            rsm=rsm_ref,
            moisture_error=err_ref,
        ))

        # Effective rainfall
        peff = max(0.0, p_mm * 0.8) if p_mm > 0 else 0.0
        kc_ref = 1.15
        etc_ref = kc_ref * et0_val
        def_ref = max(0.0, etc_ref - peff)

        water_demand = float(self.instances["water_demand"].evaluate(
            etc=etc_ref,
            crop_water_deficit=def_ref,
            effective_rainfall=peff,
        ))

        # 4. Stage 4: Main Supervisory FIS
        main_cmd = float(self.instances["main_irrigation"].evaluate(
            soil_stress=soil_stress,
            weather_stress=weather_stress,
            water_demand=water_demand,
            moisture_error=err_ref,
        ))

        # 5. Stage 5: Multi-Zone Arbitration & Bounded Allocation
        zones = [
            {"id": 1, "name": "Zone 1 - Tomato / Loam", "crop": "Tomato", "area": 100.0, "fc": 70.0, "wp": 25.0, "target": target_sm, "priority": 70.0, "kc": 1.15},
            {"id": 2, "name": "Zone 2 - Wheat / Sandy", "crop": "Wheat", "area": 120.0, "fc": 60.0, "wp": 18.0, "target": 55.0, "priority": 40.0, "kc": 0.85},
            {"id": 3, "name": "Zone 3 - Maize / Clay", "crop": "Maize", "area": 80.0, "fc": 75.0, "wp": 30.0, "target": 65.0, "priority": 85.0, "kc": 1.20},
        ]

        raw_reqs: Dict[int, float] = {}
        fuzzy_reqs: Dict[int, float] = {}
        alloc_factors: Dict[int, float] = {}
        priorities: Dict[int, float] = {}

        for z_info in zones:
            zid = z_info["id"]
            z_rsm = max(0.0, min(1.0, (sm_curr - z_info["wp"]) / (z_info["fc"] - z_info["wp"])))
            z_err = max(-30.0, min(30.0, z_info["target"] - sm_curr))
            z_ss = float(self.instances["soil_stress"].evaluate(rsm=z_rsm, moisture_error=z_err))

            z_etc = z_info["kc"] * et0_val
            z_def = max(0.0, z_etc - peff)
            z_wd = float(self.instances["water_demand"].evaluate(etc=z_etc, crop_water_deficit=z_def, effective_rainfall=peff))

            z_cmd = float(self.instances["main_irrigation"].evaluate(
                soil_stress=z_ss,
                weather_stress=weather_stress,
                water_demand=z_wd,
                moisture_error=z_err,
            ))

            req_l = (z_cmd / 100.0) * (12.0 * z_info["area"])
            raw_reqs[zid] = req_l

            af = float(self.instances["water_allocation"].evaluate(
                available_water=res_pct,
                zone_demand=z_wd,
                zone_stress=z_ss,
                zone_priority=z_info["priority"],
            ))
            alloc_factors[zid] = af
            fuzzy_reqs[zid] = req_l * (af / 100.0)
            priorities[zid] = z_info["priority"]

        # Available supply (60 L/min nominal capacity * 60 min * reservoir fraction)
        total_avail_l = 60.0 * 60.0 * (res_pct / 100.0)
        granted_dict = bounded_priority_weighted_allocation(
            raw_requests_l=fuzzy_reqs,
            priorities_pct=priorities,
            available_supply_l=total_avail_l,
        )

        zone_outputs: List[ZoneAllocationOutput] = []
        for z_info in zones:
            zid = z_info["id"]
            r_l = raw_reqs[zid]
            g_l = granted_dict.get(zid, 0.0)
            ratio = (g_l / r_l * 100.0) if r_l > 0 else 100.0

            if ratio >= 99.0:
                st = "FULL (Optimal)"
            elif ratio >= 60.0:
                st = "PARTIAL (Rationed)"
            else:
                st = "DEFICIT (Protected)"

            zone_outputs.append(
                ZoneAllocationOutput(
                    zone_id=zid,
                    name=z_info["name"],
                    crop=z_info["crop"],
                    priority_pct=z_info["priority"],
                    fis_alloc_factor=round(alloc_factors[zid], 1),
                    requested_l=round(r_l, 1),
                    allocated_l=round(g_l, 1),
                    fulfillment_ratio=round(ratio, 1),
                    status=st,
                )
            )

        def get_lvl(val: float) -> str:
            if val < 20.0: return "VERY LOW"
            if val < 40.0: return "LOW"
            if val < 60.0: return "MODERATE"
            if val < 80.0: return "HIGH"
            return "CRITICAL / VERY HIGH"

        tot_req = sum(raw_reqs.values())
        tot_alloc = sum(granted_dict.values())
        is_constr = (tot_req > total_avail_l + 1e-6) or (tot_alloc < tot_req - 1e-3)

        summary_text = (
            f"Supervisory fuzzy valve command is {main_cmd:.1f}% ({get_lvl(main_cmd)}). "
            f"Root-zone soil stress is {soil_stress:.1f}% ({get_lvl(soil_stress)}), with atmospheric evaporative "
            f"stress at {weather_stress:.1f}% ({get_lvl(weather_stress)}, ET0 = {et0_val:.2f} mm/day). "
            f"Reservoir storage is at {res_pct:.1f}%. "
            f"Allocated {tot_alloc:.1f} L out of {tot_req:.1f} L requested across 3 zones."
        )

        return EndToEndArchitectureResponse(
            inputs={
                "soil_moisture": sm_curr,
                "target_moisture": target_sm,
                "temperature": t_c,
                "humidity": rh_pct,
                "solar_radiation": rs_w_m2,
                "wind_speed": u2_m_s,
                "rainfall": p_mm,
                "reservoir_storage_pct": res_pct,
            },
            soil_stress=round(soil_stress, 1),
            soil_stress_level=get_lvl(soil_stress),
            weather_stress=round(weather_stress, 1),
            weather_stress_level=get_lvl(weather_stress),
            water_demand=round(water_demand, 1),
            water_demand_level=get_lvl(water_demand),
            etc_mm_day=round(etc_ref, 2),
            main_command=round(main_cmd, 1),
            main_command_level=get_lvl(main_cmd),
            zone_allocations=zone_outputs,
            total_requested_l=round(tot_req, 1),
            total_allocated_l=round(tot_alloc, 1),
            available_supply_l=round(total_avail_l, 1),
            is_constrained=is_constr,
            decision_summary=summary_text,
        )


fuzzy_service = FuzzyService()


def evaluate_architecture(request: EndToEndArchitectureRequest) -> EndToEndArchitectureResponse:
    """Module-level helper to evaluate end-to-end 5-stage architecture cascade."""
    return fuzzy_service.evaluate_architecture(request)

