"""Tests for the live engineering verification endpoint."""

from fastapi.testclient import TestClient

from backend.app.main import app


def test_system_verification_endpoint_passes():
    result = TestClient(app).get("/api/verification/system")
    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "PASS"
    assert len(body["checks"]) >= 5
    assert all(check["status"] == "PASS" for check in body["checks"])
    assert body["simulation"]["zones"] == [1, 2, 3]
    assert body["simulation"]["telemetry_rows"] == 180
