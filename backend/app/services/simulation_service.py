"""Simulation Service wrapping existing closed-loop and multizone engineering engines."""

from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
import numpy as np

from backend.app.core.logging import get_logger
from backend.app.database.client import db
from backend.app.database.models import SimulationRunRecord, ZoneRecord
from backend.app.schemas.simulation import SimulationRunRequest
from config.schemas import (
    SimulationScenario,
    ZoneConfig,
    CropParameters,
    SoilParameters,
    CropType,
    SoilType,
    GrowthStage,
)
from config.defaults import DEFAULT_CROPS, DEFAULT_SOILS
from simulation.scenarios import ScenarioManager
from simulation.water_allocation import (
    MultizoneAllocationSimulator,
    MultizoneAllocationConfig,
    SupplyScenario,
)
from simulation.multizone_closed_loop import (
    MultizoneClosedLoopSimulator,
    MultizoneClosedLoopConfig,
)

logger = get_logger(__name__)


class SimulationService:
    """Orchestrates closed-loop simulations using verified engineering core."""

    @staticmethod
    def _parse_scenario(name: str) -> SimulationScenario:
        normalized = name.strip().lower().replace(" ", "_").replace("&", "and")
        for sc in SimulationScenario:
            if sc.value.lower() == normalized or sc.name.lower() == normalized:
                return sc
        return SimulationScenario.NORMAL

    @staticmethod
    def _parse_supply_scenario(name: str) -> SupplyScenario:
        for s in SupplyScenario:
            if s.value.lower() == name.strip().lower() or s.name.lower() == name.strip().lower():
                return s
        return SupplyScenario.NORMAL

    @staticmethod
    def _zone_records_to_configs(records: List[ZoneRecord]) -> List[ZoneConfig]:
        """Convert database zone records into validated Pydantic ZoneConfig instances."""
        configs = []
        for r in records:
            # Match crop
            crop_name_clean = r.crop.strip().lower()
            crop_param = None
            for ct, cp in DEFAULT_CROPS.items():
                if ct.value.lower() == crop_name_clean:
                    crop_param = cp.model_copy()
                    break
            if not crop_param:
                crop_param = CropParameters(
                    name=r.crop,
                    growth_stage=GrowthStage.MID_SEASON,
                    kc=r.kc,
                    root_depth_m=r.root_zone_depth,
                )
            else:
                crop_param.kc = r.kc
                crop_param.root_depth_m = r.root_zone_depth

            # Match soil
            soil_name_clean = r.soil.strip().lower()
            soil_param = None
            for st, sp in DEFAULT_SOILS.items():
                if st.value.lower() == soil_name_clean:
                    soil_param = sp.model_copy()
                    break
            if not soil_param:
                soil_param = SoilParameters(
                    soil_type=SoilType.LOAM,
                    field_capacity=r.field_capacity,
                    wilting_point=r.wilting_point,
                    saturation=r.saturation,
                    infiltration_rate_mm_h=20.0,
                    drainage_parameter=0.08,
                )
            else:
                soil_param.field_capacity = r.field_capacity
                soil_param.wilting_point = r.wilting_point
                soil_param.saturation = r.saturation

            configs.append(
                ZoneConfig(
                    zone_id=r.zone_id,
                    name=r.name,
                    crop=crop_param,
                    soil=soil_param,
                    area_m2=r.area_m2,
                    initial_moisture=r.initial_moisture,
                    target_moisture=r.target_moisture,
                    priority=max(1, min(10, int(round(r.priority / 25.0)))) if r.priority > 10 else int(r.priority),
                )
            )
        return configs

    def execute_simulation(
        self,
        user_id: str,
        request: SimulationRunRequest,
    ) -> SimulationRunRecord:
        """Run complete multizone closed-loop simulation with bounded water allocation."""
        scenario_enum = self._parse_scenario(request.scenario)
        supply_enum = self._parse_supply_scenario(request.supply_scenario)

        # Retrieve user configured zones
        zone_records = db.list_zones(user_id)
        if not zone_records:
            # Fallback to default user zones if empty
            zone_records = db.list_zones("00000000-0000-0000-0000-000000000001")

        if request.zone_ids:
            zone_records = [z for z in zone_records if z.zone_id in request.zone_ids]

        zone_configs = self._zone_records_to_configs(zone_records)
        priorities_pct = {z.zone_id: float(z_rec.priority) for z, z_rec in zip(zone_configs, zone_records)}

        logger.info(f"Executing simulation for user {user_id}: scenario={scenario_enum.value}, supply={supply_enum.value}, zones={len(zone_configs)}")

        start_time = datetime.utcnow()

        # Build simulation configuration
        alloc_config = MultizoneAllocationConfig(
            scenario=scenario_enum,
            supply_scenario=supply_enum,
            supply_factor_override=request.supply_factor_override,
            duration_hours=request.duration_hours,
            timestep_minutes=request.timestep_minutes,
            seed=request.seed,
            zone_priorities_pct=priorities_pct,
        )

        simulator = MultizoneAllocationSimulator(
            config=alloc_config,
            zones=zone_configs,
        )

        # Run full simulation through engineering engine
        result = simulator.run()

        df = pd.DataFrame(result.telemetry_records)
        completed_time = datetime.utcnow()
        total_area = sum(z.area_m2 for z in zone_configs)

        # Prepare summary metrics dictionary
        summary_metrics = {
            "total_requested_l": round(float(result.total_requested_volume_l), 2),
            "total_allocated_l": round(float(result.total_allocated_volume_l), 2),
            "total_unmet_l": round(float(result.total_unmet_volume_l), 2),
            "system_fulfillment_ratio": round(float(result.system_allocation_ratio), 4),
            "total_system_area_m2": round(float(total_area), 2),
            "max_residual_mm": round(float(np.max(np.abs(df["water_balance_residual_mm"].values))), 8) if "water_balance_residual_mm" in df.columns else 0.0,
            "zone_summaries": {
                str(z_id): {
                    "zone_id": z_id,
                    "crop": m["crop"],
                    "soil": m["soil"],
                    "area_m2": m["area_m2"],
                    "mean_soil_moisture": round(float(np.mean(df[df["zone_id"] == z_id]["soil_moisture"])), 2) if "soil_moisture" in df.columns and len(df[df["zone_id"] == z_id]) > 0 else round(float(m.get("final_soil_moisture", 50.0)), 2),
                    "mean_mae_pct": round(float(np.mean(np.abs(df[df["zone_id"] == z_id]["moisture_error"]))), 2) if "moisture_error" in df.columns and len(df[df["zone_id"] == z_id]) > 0 else 0.0,
                    "rmse_pct": round(float(np.sqrt(np.mean(df[df["zone_id"] == z_id]["moisture_error"]**2))), 2) if "moisture_error" in df.columns and len(df[df["zone_id"] == z_id]) > 0 else 0.0,
                    "min_moisture_pct": round(float(np.min(df[df["zone_id"] == z_id]["soil_moisture"])), 2) if "soil_moisture" in df.columns and len(df[df["zone_id"] == z_id]) > 0 else 0.0,
                    "max_moisture_pct": round(float(np.max(df[df["zone_id"] == z_id]["soil_moisture"])), 2) if "soil_moisture" in df.columns and len(df[df["zone_id"] == z_id]) > 0 else 0.0,
                    "total_requested_l": round(float(m["total_requested_l"]), 2),
                    "total_allocated_l": round(float(m["total_allocated_l"]), 2),
                    "total_unmet_l": round(float(m["total_unmet_l"]), 2),
                    "fulfillment_ratio": round(float(m["allocation_ratio"]), 4),
                }
                for z_id, m in result.zone_metrics.items()
            },
        }

        # Map DataFrame columns to standardized response naming
        clean_df = pd.DataFrame()
        clean_df["step"] = df["timestep"] if "timestep" in df.columns else np.arange(len(df))
        clean_df["timestamp"] = df["timestamp"].astype(str)
        clean_df["zone_id"] = df["zone_id"]
        clean_df["soil_moisture"] = df["soil_moisture"]
        clean_df["target_moisture"] = df.get("target_moisture", 60.0)
        clean_df["moisture_error"] = df["moisture_error"]
        clean_df["rsm"] = df.get("rsm", 0.5)
        clean_df["soil_stress"] = df["zone_stress"]
        clean_df["weather_stress"] = df.get("weather_stress", 35.0)
        clean_df["water_demand"] = df["zone_demand"]
        clean_df["irrigation_command"] = df["irrigation_command"]
        clean_df["raw_request_mm"] = df["irrigation_request_mm"]
        clean_df["allocated_irrigation_mm"] = df["allocated_irrigation_mm"]
        clean_df["unmet_demand_mm"] = df["unmet_demand_mm"]
        clean_df["water_volume_requested_l"] = df["water_volume_requested_L"]
        clean_df["water_volume_allocated_l"] = df["water_volume_allocated_L"]
        clean_df["water_volume_unmet_l"] = df["water_volume_unmet_L"]
        clean_df["et0_mm"] = df.get("et0_mm_day", 5.0)
        clean_df["etc_mm"] = df.get("etc_mm_step", 0.005)
        clean_df["rainfall_mm"] = df["rainfall_mm"]
        clean_df["effective_rainfall_mm"] = df["effective_rainfall_mm"]
        clean_df["water_balance_residual"] = df["water_balance_residual_mm"]

        record = SimulationRunRecord(
            user_id=user_id,
            scenario=request.scenario,
            duration_hours=request.duration_hours,
            timestep_minutes=request.timestep_minutes,
            status="completed",
            controller_type=request.controller_type,
            supply_scenario=request.supply_scenario,
            config_snapshot=request.model_dump(),
            summary_metrics=summary_metrics,
            started_at=start_time,
            completed_at=completed_time,
        )

        db.save_simulation_run(record, clean_df)
        logger.info(f"Simulation run {record.id} completed successfully.")
        return record

    def run_simulation(
        self,
        request: SimulationRunRequest,
        user_id: str,
        db: Optional[Any] = None,
    ) -> SimulationRunRecord:
        return self.execute_simulation(user_id=user_id, request=request)


simulation_service = SimulationService()
