from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_live_ready_and_storage_checks():
    live = client.get("/health/live")
    ready = client.get("/health/ready")
    storage = client.get("/health/storage")

    assert live.status_code == 200
    assert live.json()["status"] == "alive"
    assert ready.status_code == 200
    assert ready.json()["status"] in {"ready", "not_ready"}
    assert storage.status_code == 200
    assert storage.json()["status"] == "ok"


def test_health_info_includes_storage_paths():
    response = client.get("/health/info")
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert "database_url" in payload
    assert "document_storage_dir" in payload
    assert "storage_checks" in payload
    assert payload["sqlite_path"] is None or payload["sqlite_path"].endswith(".db")
