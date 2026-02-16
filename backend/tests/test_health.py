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


def test_health_info_includes_storage_paths():
    response = client.get("/health/info")
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert "database_url" in payload
    assert "document_storage_dir" in payload
    assert payload["sqlite_path"] is None or payload["sqlite_path"].endswith(".db")
