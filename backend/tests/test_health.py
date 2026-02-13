from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_live_and_ready_checks():
    live = client.get("/health/live")
    ready = client.get("/health/ready")

    assert live.status_code == 200
    assert live.json()["status"] == "alive"
    assert ready.status_code == 200
    assert ready.json()["status"] in {"ready", "not_ready"}
