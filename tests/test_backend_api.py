"""Integration tests for FastAPI backend routes.

Verifies:
- Health and status
- Zone CRUD operations
- Crops and soils reference data
- Environmental scenarios
- Fuzzy inspection, membership variables, rules, and live step evaluation
- Multi-zone water allocation evaluation and supply sweep
- Offline PSO parameters and summary
- AI grounded chat advisor
- Multizone closed-loop simulation run and timeseries
- ReportLab PDF generation and CSV export
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_crops_reference():
    response = client.get("/api/crops")
    assert response.status_code == 200
    crops = response.json()
    assert len(crops) > 0
    crop_names = [c["crop"] for c in crops]
    assert "Tomato" in crop_names or any("Tomato" in str(c) for c in crops)


def test_soils_reference():
    response = client.get("/api/soils")
    assert response.status_code == 200
    soils = response.json()
    assert len(soils) > 0
    types = [s["soil_type"] for s in soils]
    assert "Loam" in types


def test_scenarios():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) == 6
    names = [s["id"] for s in scenarios]
    assert "Normal" in names
    assert "Hot & Dry" in names


def test_zones_crud():
    # 1. List initial default zones
    res = client.get("/api/zones")
    assert res.status_code == 200
    zones = res.json()
    assert len(zones) >= 3

    # 2. Update Zone 1
    update_res = client.put("/api/zones/1", json={"target_moisture": 68.0, "priority": 80.0})
    assert update_res.status_code == 200
    assert update_res.json()["target_moisture"] == 68.0

    # 3. Create Zone 4
    create_res = client.post(
        "/api/zones",
        json={
            "zone_id": 4,
            "name": "Zone 4 - Experimental",
            "crop": "Tomato",
            "soil": "Loam",
            "area_m2": 80.0,
            "field_capacity": 28.0,
            "wilting_point": 14.0,
            "saturation": 46.0,
            "initial_moisture": 50.0,
            "target_moisture": 65.0,
            "root_zone_depth": 0.7,
            "kc": 1.15,
            "priority": 60.0,
        },
    )
    assert create_res.status_code == 201
    assert create_res.json()["zone_id"] == 4

    # 4. Get Zone 4
    get_res = client.get("/api/zones/4")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Zone 4 - Experimental"

    # 5. Delete Zone 4
    del_res = client.delete("/api/zones/4")
    assert del_res.status_code == 204


def test_fuzzy_overview():
    res = client.get("/api/fuzzy/overview")
    assert res.status_code == 200
    overview = res.json()
    assert len(overview) == 5
    ids = [c["id"] for c in overview]
    assert "main_irrigation" in ids
    assert "water_allocation" in ids


def test_fuzzy_variables_and_rules():
    # Variables
    res_vars = client.get("/api/fuzzy/main_irrigation/variables")
    assert res_vars.status_code == 200
    vars_data = res_vars.json()
    assert len(vars_data) >= 4  # moisture_error, soil_stress, water_demand, irrigation_command

    # Rules
    res_rules = client.get("/api/fuzzy/main_irrigation/rules")
    assert res_rules.status_code == 200
    rules_data = res_rules.json()
    assert len(rules_data) > 0


def test_fuzzy_evaluate():
    payload = {
        "controller": "main_irrigation",
        "inputs": {
            "moisture_error": 5.0,
            "soil_stress": 60.0,
            "water_demand": 70.0,
        },
    }
    res = client.post("/api/fuzzy/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "irrigation_command" in data["outputs"]
    assert data["outputs"]["irrigation_command"] > 0.0
    assert len(data["firing_weights"]) > 0


def test_allocation_evaluate_and_sweep():
    eval_payload = {
        "available_water_pct": 50.0,
        "requests_mm": {"1": 4.0, "2": 5.0, "3": 3.0},
        "stresses_pct": {"1": 40.0, "2": 70.0, "3": 30.0},
        "priorities_pct": {"1": 50.0, "2": 90.0, "3": 40.0},
    }
    res = client.post("/api/allocation/evaluate", json=eval_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_supply_constrained"] is True
    assert data["total_allocated_l"] <= data["available_supply_l"] + 1e-4

    # Sweep
    res_sweep = client.post(
        "/api/allocation/sweep",
        json={"requests_mm": {"1": 4.0, "2": 5.0, "3": 3.0}},
    )
    assert res_sweep.status_code == 200
    sweep_data = res_sweep.json()
    assert len(sweep_data) == 10  # 10% to 100%


def test_optimization_endpoints():
    res_summary = client.get("/api/optimization/summary")
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["baseline_fitness"] > 0
    assert len(summary["convergence"]) > 0

    res_params = client.get("/api/optimization/parameters")
    assert res_params.status_code == 200
    params = res_params.json()
    assert len(params) == 18


def test_ai_chat():
    payload = {"prompt": "Why was water allocated to Zone 2 under drought?"}
    res = client.post("/api/ai/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["response"]) > 20
    assert data["source"] in ["groq", "rule_based_fallback"]


def test_simulation_run_timeseries_and_report():
    # 1. Run Normal Simulation
    run_payload = {
        "scenario": "Normal",
        "duration_hours": 24,
        "timestep_minutes": 15,
        "supply_scenario": "Normal Supply",
    }
    run_res = client.post("/api/simulations/run", json=run_payload)
    assert run_res.status_code == 200
    sim_data = run_res.json()
    sim_id = sim_data["id"]
    assert sim_data["summary_metrics"]["total_allocated_l"] > 0
    assert sim_data["summary_metrics"]["max_residual_mm"] < 1e-4

    # 2. Get Timeseries
    ts_res = client.get(f"/api/simulations/{sim_id}/timeseries?stride=4")
    assert ts_res.status_code == 200
    ts_data = ts_res.json()
    assert ts_data["total_records"] > 0

    # 3. Generate PDF Report
    rep_payload = {"simulation_id": sim_id, "include_ai_summary": True}
    rep_res = client.post("/api/reports/generate", json=rep_payload)
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert rep_data["filename"].endswith(".pdf")
    report_id = rep_data["id"]

    # 4. Download PDF Report
    dl_res = client.get(f"/api/reports/download/{report_id}")
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/pdf"
    assert len(dl_res.content) > 1000

    # 5. Export CSV
    csv_res = client.get(f"/api/reports/csv/{sim_id}")
    assert csv_res.status_code == 200
    assert "soil_moisture" in csv_res.text


def test_controllers_and_allocation_config():
    # 1. Test /api/fuzzy/controllers
    c_res = client.get("/api/fuzzy/controllers")
    assert c_res.status_code == 200
    controllers = c_res.json()
    assert len(controllers) == 5

    # 2. Test single controller
    single_res = client.get("/api/fuzzy/controllers/soil_stress")
    assert single_res.status_code == 200
    assert single_res.json()["name"] == "soil_stress"

    # 3. Test membership functions
    mf_res = client.get("/api/fuzzy/controllers/soil_stress/membership-functions")
    assert mf_res.status_code == 200
    mfs = mf_res.json()
    assert len(mfs) >= 2

    # 4. Test rules
    rules_res = client.get("/api/fuzzy/controllers/soil_stress/rules")
    assert rules_res.status_code == 200
    assert len(rules_res.json()) >= 9

    # 5. Test allocation config
    cfg_res = client.get("/api/allocation/config")
    assert cfg_res.status_code == 200
    assert "Two-Layer" in cfg_res.json()["engine"]

    # 6. Test optimization summary and parameters
    opt_sum = client.get("/api/optimization/summary")
    assert opt_sum.status_code == 200
    assert opt_sum.json()["status"] == "completed"

    opt_params = client.get("/api/optimization/parameters")
    assert opt_params.status_code == 200
    assert len(opt_params.json()) == 18

