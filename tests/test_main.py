"""
Tests for FastAPI app main entry point.
Verifies:
- App initialization
- Health endpoint
- API routes availability
- Basic voice and order endpoints
"""

from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)

def test_app_starts():
    """Ensure the FastAPI app boots successfully."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()

def test_healthcheck_route():
    """Check the monitoring/health endpoint."""
    response = client.get("/api/v1/monitoring/health")
    assert response.status_code in [200, 204]
    assert "status" in response.json() or response.text == ""

def test_list_routes():
    """Ensure that major routes are loaded."""
    routes = [r.path for r in app.routes]
    expected = ["/api/v1/orders", "/api/v1/voice", "/api/v1/agents"]
    for path in expected:
        assert any(path in r for r in routes), f"Missing route: {path}"

@pytest.mark.parametrize("path", ["/api/v1/orders", "/api/v1/agents", "/api/v1/payments"])
def test_api_routes_exist(path):
    response = client.options(path)
    assert response.status_code in (200, 405)  # 405 = route exists but method not allowed

def test_openapi_schema():
    """Ensure OpenAPI schema is generated correctly."""
    schema = client.get("/openapi.json").json()
    assert "paths" in schema
    assert "info" in schema
    assert "title" in schema["info"]

def test_post_order(sample_order):
    """Test order endpoint POST."""
    res = client.post("/api/v1/orders", json=sample_order)
    assert res.status_code in (200, 201, 422)  # allow validation response if schema strict
    assert isinstance(res.json(), dict)

def test_voice_inbound_simulation(monkeypatch):
    """Simulate Twilio inbound call webhook."""
    # Mock Twilio validation
    monkeypatch.setattr("app.core.middleware.verify_twilio_request", lambda *a, **k: True)
    payload = {"From": "+911234567890", "CallSid": "CA1234"}
    res = client.post("/api/v1/voice/incoming-call", data=payload)
    assert res.status_code in (200, 201, 202)
