from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_project_status():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "project": "insurance-product-recommendation",
    }
