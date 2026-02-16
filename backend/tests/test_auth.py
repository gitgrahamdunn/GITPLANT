from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_login_success():
    response = client.post(
        "/auth/login",
        json={"email": "user@edms.local", "password": "user123"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "user"
    assert "." in response.json()["access_token"]


def test_login_failure():
    response = client.post(
        "/auth/login",
        json={"email": "user@edms.local", "password": "wrong"},
    )
    assert response.status_code == 401


def test_auth_me_returns_user():
    login = client.post(
        "/auth/login",
        json={"email": "user@edms.local", "password": "user123"},
    )
    token = login.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "user@edms.local"
    assert me.json()["role"] == "user"
