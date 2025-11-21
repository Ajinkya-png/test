import pytest
from fastapi.testclient import TestClient
from app.main import app  # Ensure app.main:app exists and includes routers

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/monitoring/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"
