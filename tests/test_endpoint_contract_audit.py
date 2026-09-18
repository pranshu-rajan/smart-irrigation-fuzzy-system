"""Fast endpoint-contract smoke audit for the deployed API surface.

This intentionally validates every route family with deterministic or
non-destructive calls. Expensive simulation/report flows are covered by the
full backend integration tests.
"""
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_endpoint_contract_audit():
    assert client.get('/api/health').status_code == 200
    assert client.get('/api/zones').status_code == 200
    assert client.get('/api/crops').status_code == 200
    assert client.get('/api/soils').status_code == 200
    assert client.get('/api/scenarios').status_code == 200
    assert client.get('/api/fuzzy/overview').status_code == 200
    assert client.get('/api/fuzzy/controllers').status_code == 200
    for name in ['soil_stress','weather_stress','water_demand','main_irrigation','water_allocation']:
        assert client.get(f'/api/fuzzy/{name}/variables').status_code == 200
        assert client.get(f'/api/fuzzy/{name}/rules').status_code == 200
    assert client.get('/api/allocation/config').status_code == 200
    assert client.get('/api/optimization/summary').status_code == 200
    assert client.get('/api/optimization/parameters').status_code == 200
    assert client.get('/api/verification/system').status_code == 200
