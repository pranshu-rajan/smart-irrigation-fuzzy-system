"""Database client and repository interface with Supabase integration and robust local persistence."""

import json
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import threading

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.database.models import (
    ProfileRecord,
    ZoneRecord,
    SimulationRunRecord,
    OptimizationRunRecord,
    ReportRecord,
    AIConversationRecord,
    AIMessageRecord,
)
from config.defaults import get_default_zones

logger = get_logger(__name__)


class DatabaseRepository:
    """Thread-safe SQLite & in-memory local repository with Supabase sync capabilities."""

    _instance = None
    _lock = threading.Lock()

    def __init__(self, db_path: str = "data/platform.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_sqlite()
        self._seed_default_zones()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self) -> None:
        """Create local schema mirror if not already existing."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS zones (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    zone_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    crop TEXT NOT NULL,
                    soil TEXT NOT NULL,
                    area_m2 REAL NOT NULL,
                    field_capacity REAL NOT NULL,
                    wilting_point REAL NOT NULL,
                    saturation REAL DEFAULT 85.0 NOT NULL,
                    initial_moisture REAL NOT NULL,
                    target_moisture REAL NOT NULL,
                    root_zone_depth REAL NOT NULL,
                    kc REAL NOT NULL,
                    priority REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, zone_id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simulation_runs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    scenario TEXT NOT NULL,
                    duration_hours INTEGER NOT NULL,
                    timestep_minutes INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    controller_type TEXT NOT NULL,
                    supply_scenario TEXT NOT NULL,
                    config_snapshot TEXT NOT NULL,
                    summary_metrics TEXT NOT NULL,
                    error_message TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simulation_timeseries (
                    simulation_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    PRIMARY KEY (simulation_id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS optimization_runs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    seed INTEGER NOT NULL,
                    swarm_size INTEGER NOT NULL,
                    max_iterations INTEGER NOT NULL,
                    objective_weights TEXT NOT NULL,
                    baseline_fitness REAL NOT NULL,
                    optimized_fitness REAL NOT NULL,
                    convergence_history TEXT NOT NULL,
                    optimized_parameters TEXT NOT NULL,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    simulation_id TEXT,
                    optimization_id TEXT,
                    report_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    grounded_context TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def _seed_default_zones(self) -> None:
        """Ensure standard 3 default agricultural zones exist for the default user."""
        default_user = "00000000-0000-0000-0000-000000000001"
        existing = self.list_zones(default_user)
        if not existing:
            default_zone_configs = get_default_zones()
            for z in default_zone_configs:
                rec = ZoneRecord(
                    user_id=default_user,
                    zone_id=z.zone_id,
                    name=z.name,
                    crop=z.crop.name,
                    soil=z.soil.soil_type.value,
                    area_m2=z.area_m2,
                    field_capacity=z.soil.field_capacity,
                    wilting_point=z.soil.wilting_point,
                    saturation=z.soil.saturation,
                    initial_moisture=z.initial_moisture,
                    target_moisture=z.target_moisture,
                    root_zone_depth=z.crop.root_depth_m,
                    kc=z.crop.kc,
                    priority=float(z.priority * 25.0),  # Scale priority 1..3 to %
                )
                self.save_zone(rec)

    # --- Zone Methods ---
    def list_zones(self, user_id: str) -> List[ZoneRecord]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM zones WHERE user_id = ? ORDER BY zone_id ASC", (user_id,))
            rows = cursor.fetchall()
            return [
                ZoneRecord(
                    id=r["id"],
                    user_id=r["user_id"],
                    zone_id=r["zone_id"],
                    name=r["name"],
                    crop=r["crop"],
                    soil=r["soil"],
                    area_m2=r["area_m2"],
                    field_capacity=r["field_capacity"],
                    wilting_point=r["wilting_point"],
                    saturation=r["saturation"],
                    initial_moisture=r["initial_moisture"],
                    target_moisture=r["target_moisture"],
                    root_zone_depth=r["root_zone_depth"],
                    kc=r["kc"],
                    priority=r["priority"],
                    created_at=datetime.fromisoformat(r["created_at"]),
                    updated_at=datetime.fromisoformat(r["updated_at"]),
                )
                for r in rows
            ]

    def get_all_zones(self, user_id: Optional[str] = None) -> List[ZoneRecord]:
        uid = user_id or "00000000-0000-0000-0000-000000000001"
        return self.list_zones(uid)

    def get_zone(self, arg1: Any, arg2: Any = None) -> Optional[ZoneRecord]:
        if arg2 is not None:
            user_id = str(arg1)
            zone_id = int(arg2)
            query = "SELECT * FROM zones WHERE user_id = ? AND zone_id = ?"
            params = (user_id, zone_id)
        else:
            zone_id = int(arg1)
            query = "SELECT * FROM zones WHERE zone_id = ? LIMIT 1"
            params = (zone_id,)
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            r = cursor.fetchone()
            if not r:
                return None
            return ZoneRecord(
                id=r["id"],
                user_id=r["user_id"],
                zone_id=r["zone_id"],
                name=r["name"],
                crop=r["crop"],
                soil=r["soil"],
                area_m2=r["area_m2"],
                field_capacity=r["field_capacity"],
                wilting_point=r["wilting_point"],
                saturation=r["saturation"],
                initial_moisture=r["initial_moisture"],
                target_moisture=r["target_moisture"],
                root_zone_depth=r["root_zone_depth"],
                kc=r["kc"],
                priority=r["priority"],
                created_at=datetime.fromisoformat(r["created_at"]),
                updated_at=datetime.fromisoformat(r["updated_at"]),
            )

    def delete_zone(self, zone_id: int, user_id: Optional[str] = None) -> bool:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("DELETE FROM zones WHERE user_id = ? AND zone_id = ?", (user_id, zone_id))
            else:
                cursor.execute("DELETE FROM zones WHERE zone_id = ?", (zone_id,))
            conn.commit()
            return cursor.rowcount > 0

    def save_zone(self, zone: ZoneRecord) -> ZoneRecord:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO zones (
                    id, user_id, zone_id, name, crop, soil, area_m2,
                    field_capacity, wilting_point, saturation, initial_moisture,
                    target_moisture, root_zone_depth, kc, priority, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, zone_id) DO UPDATE SET
                    name=excluded.name,
                    crop=excluded.crop,
                    soil=excluded.soil,
                    area_m2=excluded.area_m2,
                    field_capacity=excluded.field_capacity,
                    wilting_point=excluded.wilting_point,
                    saturation=excluded.saturation,
                    initial_moisture=excluded.initial_moisture,
                    target_moisture=excluded.target_moisture,
                    root_zone_depth=excluded.root_zone_depth,
                    kc=excluded.kc,
                    priority=excluded.priority,
                    updated_at=excluded.updated_at
            """, (
                zone.id, zone.user_id, zone.zone_id, zone.name, zone.crop, zone.soil, zone.area_m2,
                zone.field_capacity, zone.wilting_point, zone.saturation, zone.initial_moisture,
                zone.target_moisture, zone.root_zone_depth, zone.kc, zone.priority,
                zone.created_at.isoformat(), datetime.utcnow().isoformat()
            ))
            conn.commit()
            return zone

    # --- Simulation Methods ---
    def save_simulation_run(
        self,
        run: SimulationRunRecord,
        timeseries_df: Optional[Any] = None,
    ) -> None:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO simulation_runs (
                    id, user_id, scenario, duration_hours, timestep_minutes,
                    status, controller_type, supply_scenario, config_snapshot,
                    summary_metrics, error_message, started_at, completed_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run.id, run.user_id, run.scenario, run.duration_hours, run.timestep_minutes,
                run.status, run.controller_type, run.supply_scenario,
                json.dumps(run.config_snapshot), json.dumps(run.summary_metrics),
                run.error_message, run.started_at.isoformat(),
                run.completed_at.isoformat() if run.completed_at else None,
                run.created_at.isoformat()
            ))
            if timeseries_df is not None:
                # Store serialized records for fast retrieval
                records = timeseries_df.to_dict(orient="records") if hasattr(timeseries_df, "to_dict") else timeseries_df
                cursor.execute("""
                    INSERT OR REPLACE INTO simulation_timeseries (simulation_id, user_id, data_json)
                    VALUES (?, ?, ?)
                """, (run.id, run.user_id, json.dumps(records, default=str)))
            conn.commit()

    def get_simulation_run(self, arg1: str, arg2: Optional[str] = None) -> Optional[SimulationRunRecord]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if arg2 is not None:
                cursor.execute(
                    "SELECT * FROM simulation_runs WHERE (id = ? AND user_id = ?) OR (id = ? AND user_id = ?) OR id = ? LIMIT 1",
                    (arg1, arg2, arg2, arg1, arg1),
                )
            else:
                cursor.execute("SELECT * FROM simulation_runs WHERE id = ? LIMIT 1", (arg1,))
            r = cursor.fetchone()
            if not r:
                return None
            return SimulationRunRecord(
                id=r["id"],
                user_id=r["user_id"],
                scenario=r["scenario"],
                duration_hours=r["duration_hours"],
                timestep_minutes=r["timestep_minutes"],
                status=r["status"],
                controller_type=r["controller_type"],
                supply_scenario=r["supply_scenario"],
                config_snapshot=json.loads(r["config_snapshot"]),
                summary_metrics=json.loads(r["summary_metrics"]),
                error_message=r["error_message"],
                started_at=datetime.fromisoformat(r["started_at"]),
                completed_at=datetime.fromisoformat(r["completed_at"]) if r["completed_at"] else None,
                created_at=datetime.fromisoformat(r["created_at"]),
            )

    def list_simulation_runs(self, user_id: str, limit: int = 50) -> List[SimulationRunRecord]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM simulation_runs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            )
            rows = cursor.fetchall()
            return [
                SimulationRunRecord(
                    id=r["id"],
                    user_id=r["user_id"],
                    scenario=r["scenario"],
                    duration_hours=r["duration_hours"],
                    timestep_minutes=r["timestep_minutes"],
                    status=r["status"],
                    controller_type=r["controller_type"],
                    supply_scenario=r["supply_scenario"],
                    config_snapshot=json.loads(r["config_snapshot"]),
                    summary_metrics=json.loads(r["summary_metrics"]),
                    error_message=r["error_message"],
                    started_at=datetime.fromisoformat(r["started_at"]),
                    completed_at=datetime.fromisoformat(r["completed_at"]) if r["completed_at"] else None,
                    created_at=datetime.fromisoformat(r["created_at"]),
                )
                for r in rows
            ]

    def get_simulation_runs(self, limit: int = 50, user_id: Optional[str] = None) -> List[SimulationRunRecord]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT * FROM simulation_runs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
            else:
                cursor.execute("SELECT * FROM simulation_runs ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [
                SimulationRunRecord(
                    id=r["id"],
                    user_id=r["user_id"],
                    scenario=r["scenario"],
                    duration_hours=r["duration_hours"],
                    timestep_minutes=r["timestep_minutes"],
                    status=r["status"],
                    controller_type=r["controller_type"],
                    supply_scenario=r["supply_scenario"],
                    config_snapshot=json.loads(r["config_snapshot"]),
                    summary_metrics=json.loads(r["summary_metrics"]),
                    error_message=r["error_message"],
                    started_at=datetime.fromisoformat(r["started_at"]),
                    completed_at=datetime.fromisoformat(r["completed_at"]) if r["completed_at"] else None,
                    created_at=datetime.fromisoformat(r["created_at"]),
                )
                for r in rows
            ]

    def get_simulation_timeseries(self, user_id: str, simulation_id: str) -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data_json FROM simulation_timeseries WHERE user_id = ? AND simulation_id = ?",
                (user_id, simulation_id)
            )
            r = cursor.fetchone()
            if not r:
                return []
            return json.loads(r["data_json"])

    def get_timeseries(self, simulation_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute(
                    "SELECT data_json FROM simulation_timeseries WHERE user_id = ? AND simulation_id = ?",
                    (user_id, simulation_id),
                )
            else:
                cursor.execute(
                    "SELECT data_json FROM simulation_timeseries WHERE simulation_id = ?",
                    (simulation_id,),
                )
            r = cursor.fetchone()
            if not r:
                return []
            return json.loads(r["data_json"])

    # --- Optimization Methods ---
    def save_optimization_run(self, run: OptimizationRunRecord) -> None:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO optimization_runs (
                    id, user_id, status, seed, swarm_size, max_iterations,
                    objective_weights, baseline_fitness, optimized_fitness,
                    convergence_history, optimized_parameters, error_message,
                    created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run.id, run.user_id, run.status, run.seed, run.swarm_size, run.max_iterations,
                json.dumps(run.objective_weights), run.baseline_fitness, run.optimized_fitness,
                json.dumps(run.convergence_history), json.dumps(run.optimized_parameters),
                run.error_message, run.created_at.isoformat(),
                run.completed_at.isoformat() if run.completed_at else None
            ))
            conn.commit()

    def get_optimization_run(self, user_id: str, optimization_id: str) -> Optional[OptimizationRunRecord]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM optimization_runs WHERE user_id = ? AND id = ?", (user_id, optimization_id))
            r = cursor.fetchone()
            if not r:
                return None
            return OptimizationRunRecord(
                id=r["id"],
                user_id=r["user_id"],
                status=r["status"],
                seed=r["seed"],
                swarm_size=r["swarm_size"],
                max_iterations=r["max_iterations"],
                objective_weights=json.loads(r["objective_weights"]),
                baseline_fitness=r["baseline_fitness"],
                optimized_fitness=r["optimized_fitness"],
                convergence_history=json.loads(r["convergence_history"]),
                optimized_parameters=json.loads(r["optimized_parameters"]),
                error_message=r["error_message"],
                created_at=datetime.fromisoformat(r["created_at"]),
                completed_at=datetime.fromisoformat(r["completed_at"]) if r["completed_at"] else None,
            )

    def list_optimization_runs(self, user_id: str, limit: int = 20) -> List[OptimizationRunRecord]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM optimization_runs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            )
            rows = cursor.fetchall()
            return [
                OptimizationRunRecord(
                    id=r["id"],
                    user_id=r["user_id"],
                    status=r["status"],
                    seed=r["seed"],
                    swarm_size=r["swarm_size"],
                    max_iterations=r["max_iterations"],
                    objective_weights=json.loads(r["objective_weights"]),
                    baseline_fitness=r["baseline_fitness"],
                    optimized_fitness=r["optimized_fitness"],
                    convergence_history=json.loads(r["convergence_history"]),
                    optimized_parameters=json.loads(r["optimized_parameters"]),
                    error_message=r["error_message"],
                    created_at=datetime.fromisoformat(r["created_at"]),
                    completed_at=datetime.fromisoformat(r["completed_at"]) if r["completed_at"] else None,
                )
                for r in rows
            ]

    def get_optimization_runs(self, limit: int = 20, user_id: Optional[str] = None) -> List[OptimizationRunRecord]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT * FROM optimization_runs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
            else:
                cursor.execute("SELECT * FROM optimization_runs ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [
                OptimizationRunRecord(
                    id=r["id"],
                    user_id=r["user_id"],
                    status=r["status"],
                    seed=r["seed"],
                    swarm_size=r["swarm_size"],
                    max_iterations=r["max_iterations"],
                    objective_weights=json.loads(r["objective_weights"]),
                    baseline_fitness=r["baseline_fitness"],
                    optimized_fitness=r["optimized_fitness"],
                    convergence_history=json.loads(r["convergence_history"]),
                    optimized_parameters=json.loads(r["optimized_parameters"]),
                    error_message=r["error_message"],
                    created_at=datetime.fromisoformat(r["created_at"]),
                    completed_at=datetime.fromisoformat(r["completed_at"]) if r["completed_at"] else None,
                )
                for r in rows
            ]

    # --- Reports Methods ---
    def save_report(self, report: ReportRecord) -> None:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO reports (
                    id, user_id, simulation_id, optimization_id, report_type,
                    title, filename, file_path, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.id, report.user_id, report.simulation_id, report.optimization_id,
                report.report_type, report.title, report.filename, report.file_path,
                json.dumps(report.metadata), report.created_at.isoformat()
            ))
            conn.commit()

    def save_report_metadata(
        self,
        report_id: str,
        simulation_id: Optional[str],
        title: str,
        filename: str,
        file_path: str,
        metadata: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> ReportRecord:
        uid = user_id or "00000000-0000-0000-0000-000000000001"
        rec = ReportRecord(
            id=report_id,
            user_id=uid,
            simulation_id=simulation_id,
            report_type="pdf",
            title=title,
            filename=filename,
            file_path=file_path,
            metadata=metadata,
        )
        self.save_report(rec)
        return rec

    def get_report_metadata(self, report_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "id": r["id"],
                "user_id": r["user_id"],
                "simulation_id": r["simulation_id"],
                "title": r["title"],
                "filename": r["filename"],
                "file_path": r["file_path"],
                "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
                "created_at": r["created_at"],
            }

    def get_report(self, user_id: str, report_id: str) -> Optional[ReportRecord]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reports WHERE user_id = ? AND id = ?", (user_id, report_id))
            r = cursor.fetchone()
            if not r:
                return None
            return ReportRecord(
                id=r["id"],
                user_id=r["user_id"],
                simulation_id=r["simulation_id"],
                optimization_id=r["optimization_id"],
                report_type=r["report_type"],
                title=r["title"],
                filename=r["filename"],
                file_path=r["file_path"],
                metadata=json.loads(r["metadata"]),
                created_at=datetime.fromisoformat(r["created_at"]),
            )

    def list_reports(self, user_id: str) -> List[ReportRecord]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reports WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            rows = cursor.fetchall()
            return [
                ReportRecord(
                    id=r["id"],
                    user_id=r["user_id"],
                    simulation_id=r["simulation_id"],
                    optimization_id=r["optimization_id"],
                    report_type=r["report_type"],
                    title=r["title"],
                    filename=r["filename"],
                    file_path=r["file_path"],
                    metadata=json.loads(r["metadata"]),
                    created_at=datetime.fromisoformat(r["created_at"]),
                )
                for r in rows
            ]


# Global singleton repository instance
db = DatabaseRepository()


def get_db_repository() -> DatabaseRepository:
    """FastAPI dependency to inject the database repository."""
    return db
