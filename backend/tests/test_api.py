from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_system_status() -> None:
    response = client.get("/api/system/status")
    assert response.status_code == 200
    assert "camera_status" in response.json()


def test_api_zone_creation() -> None:
    zone_id = f"test-zone-{uuid4()}"
    payload = {"id": zone_id, "name": "Test Zone", "type": "restricted", "polygon": [[0, 0], [100, 0], [100, 100], [0, 100]]}
    response = client.post("/api/zones", json=payload)
    assert response.status_code == 201
    assert response.json()["id"] == zone_id
    delete_response = client.delete(f"/api/zones/{zone_id}")
    assert delete_response.status_code == 200
