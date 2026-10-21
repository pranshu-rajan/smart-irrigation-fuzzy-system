"""Comprehensive test suite for India National-Level Precision Irrigation."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.india_location_service import india_location_service, INDIAN_SOIL_REGISTRY
from backend.app.services.india_weather_service import india_weather_service
from backend.app.services.india_irrigation_service import india_irrigation_service
from backend.app.schemas.india import IndiaEvaluationRequest


@pytest.fixture
def client():
    return TestClient(app)


class TestIndiaLocationIntelligence:
    """Test suite for Indian district lookup, geocoding, and agro-climatic resolution."""

    def test_district_count(self):
        districts = india_location_service.list_all_districts()
        assert len(districts) >= 30
        states = {d["state"] for d in districts}
        assert "Punjab" in states
        assert "Maharashtra" in states
        assert "Uttar Pradesh" in states
        assert "Karnataka" in states
        assert "Tamil Nadu" in states
        assert "Gujarat" in states
        assert "Rajasthan" in states

    def test_exact_district_lookup_ludhiana(self):
        resp = india_location_service.lookup(query="Ludhiana")
        assert resp.matched_district == "Ludhiana"
        assert resp.state == "Punjab"
        assert resp.agro_climatic_zone == "Trans-Gangetic Plain"
        assert resp.zone_number == 6
        assert resp.dominant_soil == "Alluvial Soil"
        assert resp.recommended_crops["Rabi (Winter)"] == "Wheat"
        assert resp.recommended_crops["Kharif (Monsoon)"] == "Basmati Rice"

    def test_exact_district_lookup_pune(self):
        resp = india_location_service.lookup(query="Pune")
        assert resp.matched_district == "Pune"
        assert resp.state == "Maharashtra"
        assert resp.agro_climatic_zone == "Western Plateau and Hills"
        assert resp.dominant_soil == "Black Cotton Soil (Vertisol)"
        assert resp.soil_properties["field_capacity_pct"] == 36.0
        assert resp.soil_properties["wilting_point_pct"] == 20.0

    def test_pincode_resolution(self):
        resp = india_location_service.lookup(pincode="141004")
        assert resp.matched_district == "Ludhiana"

        resp2 = india_location_service.lookup(pincode="411001")
        assert resp2.matched_district == "Pune"

    def test_nearest_coordinate_resolution(self):
        # Coordinates near Varanasi (25.3°N, 82.9°E)
        resp = india_location_service.lookup(lat=25.32, lon=82.98)
        assert resp.matched_district == "Varanasi"
        assert resp.state == "Uttar Pradesh"

    def test_soil_properties_physical_invariants(self):
        for soil_name, props in INDIAN_SOIL_REGISTRY.items():
            assert props["field_capacity_pct"] > props["wilting_point_pct"], f"Invalid FC/WP for {soil_name}"
            assert props["saturation_pct"] > props["field_capacity_pct"], f"Invalid Sat/FC for {soil_name}"
            assert props["infiltration_rate_mm_h"] > 0.0


class TestIndiaWeatherService:
    """Test suite for live and fallback meteorology ingestion."""

    def test_fallback_weather_generation(self):
        w = india_weather_service._generate_fallback_weather(latitude=28.6, longitude=77.2, elevation_m=216.0)
        assert 10.0 <= w.temperature_c <= 48.0
        assert 10.0 <= w.humidity_percent <= 100.0
        assert w.wind_speed_m_s > 0.0
        assert w.atmospheric_pressure_kpa > 80.0
        assert w.is_live is False
        assert "IMD" in w.source

    @pytest.mark.asyncio
    async def test_fetch_live_weather_returns_valid_structure(self):
        # Query for Ahmedabad (23.02°N, 72.57°E)
        w = await india_weather_service.fetch_live_weather(latitude=23.0225, longitude=72.5714, elevation_m=53.0)
        assert w.temperature_c > -10.0
        assert 0.0 <= w.humidity_percent <= 100.0
        assert w.solar_radiation_w_m2 >= 0.0
        assert w.wind_speed_m_s >= 0.0
        assert w.rainfall_mm >= 0.0


class TestIndiaEndToEndIrrigationOrchestration:
    """Test suite for full 5-stage cascaded fuzzy control execution on Indian locations."""

    @pytest.mark.asyncio
    async def test_evaluate_ludhiana_end_to_end(self):
        req = IndiaEvaluationRequest(location_query="Ludhiana", reservoir_storage_pct=70.0)
        resp = await india_irrigation_service.evaluate_location(req)

        assert resp.location.district == "Ludhiana"
        assert resp.location.state == "Punjab"
        assert resp.physics_agronomy["et0_fao56_mm_day"] > 0.0
        assert len(resp.zone_allocations) == 3

        # Verify all 5 fuzzy stages produced bounded outputs
        assert 0.0 <= resp.fuzzy_stages["stage1_soil_stress_pct"] <= 100.0
        assert 0.0 <= resp.fuzzy_stages["stage2_weather_stress_pct"] <= 100.0
        assert 0.0 <= resp.fuzzy_stages["stage3_water_demand_pct"] <= 100.0
        assert 0.0 <= resp.fuzzy_stages["stage4_main_command_pct"] <= 100.0

        # Verify mass conservation
        assert resp.total_allocated_liters <= resp.available_supply_liters + 1e-3
        assert resp.total_allocated_liters >= 0.0

        # Verify 24-hour predictive simulation
        assert len(resp.hourly_telemetry) == 24
        for step in resp.hourly_telemetry:
            assert resp.location.wilting_point_pct <= step.zone1_moisture <= resp.location.saturation_pct + 5.0

    @pytest.mark.asyncio
    async def test_evaluate_pune_black_soil_conservation(self):
        req = IndiaEvaluationRequest(location_query="Pune", reservoir_storage_pct=30.0)  # Drought conditions
        resp = await india_irrigation_service.evaluate_location(req)

        assert resp.location.district == "Pune"
        assert resp.location.dominant_soil == "Black Cotton Soil (Vertisol)"
        # Under low storage, available supply is strictly respected
        assert resp.total_allocated_liters <= resp.available_supply_liters + 1e-3


class TestIndiaAPIRoutes:
    """Contract verification for India API endpoints."""

    def test_get_districts_endpoint(self, client):
        r = client.get("/api/india/districts")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 30
        assert any(d["district"] == "Ludhiana" for d in data)

    def test_lookup_endpoint(self, client):
        r = client.get("/api/india/lookup?query=Nashik")
        assert r.status_code == 200
        data = r.json()
        assert data["matched_district"] == "Nashik"
        assert data["state"] == "Maharashtra"
        assert data["dominant_soil"] == "Black Cotton Soil (Vertisol)"

    def test_evaluate_endpoint(self, client):
        payload = {"location_query": "Varanasi", "reservoir_storage_pct": 60.0}
        r = client.post("/api/india/evaluate", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["location"]["district"] == "Varanasi"
        assert "weather" in data
        assert "fuzzy_stages" in data
        assert len(data["zone_allocations"]) == 3
        assert len(data["hourly_telemetry"]) == 24
        assert "decision_summary" in data

    def test_evaluate_with_climate_and_crop_overrides(self, client):
        payload = {
            "location_query": "Ludhiana",
            "reservoir_storage_pct": 45.0,
            "temperature_override": 42.0,
            "humidity_override": 20.0,
            "solar_radiation_override": 950.0,
            "rainfall_override": 0.0,
            "zone1_crop_override": "Sugarcane",
            "zone2_crop_override": "Cotton",
        }
        r = client.post("/api/india/evaluate", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["weather"]["temperature_c"] == 42.0
        assert data["weather"]["humidity_percent"] == 20.0
        assert data["zone_allocations"][0]["crop"] == "Sugarcane"
        assert data["zone_allocations"][1]["crop"] == "Cotton"
        # Under heatwave stress, weather stress FIS should be high
        assert data["fuzzy_stages"]["stage2_weather_stress_pct"] >= 50.0
