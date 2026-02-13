from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_login_success():
    response = client.post(
        "/auth/login",
        json={"email": "engineer@edms.local", "password": "engineer123"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "engineer"


def test_login_failure():
    response = client.post(
        "/auth/login",
        json={"email": "engineer@edms.local", "password": "wrong"},
    )
    assert response.status_code == 401
