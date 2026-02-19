from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.db import init_db

client = TestClient(app)


def auth_headers() -> dict[str, str]:
    login = client.post("/auth/login", json={"email": "user@edms.local", "password": "user123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dev_status_and_seed_reset_cycle() -> None:
    init_db()
    headers = auth_headers()
    status = client.get('/dev/status', headers=headers)
    assert status.status_code == 200
    assert 'enabled' in status.json()

    seed = client.post('/dev/seed', headers=headers)
    assert seed.status_code == 200
    assert seed.json()['documents_created'] >= 25

    reset = client.post('/dev/reset', headers=headers)
    assert reset.status_code == 200
    assert reset.json()['documents_created'] == 0


def test_dev_endpoints_disabled_message() -> None:
    headers = auth_headers()
    original = settings.enable_demo_endpoints
    settings.enable_demo_endpoints = False
    try:
        response = client.post('/dev/seed', headers=headers)
        assert response.status_code == 403
        assert 'ENABLE_DEMO_ENDPOINTS' in response.json()['detail']
    finally:
      settings.enable_demo_endpoints = original


def test_cors_preflight_allows_vercel_production_origin() -> None:
    response = client.options(
        '/projects',
        headers={
            'Origin': 'https://gitplant-oggy.vercel.app',
            'Access-Control-Request-Method': 'POST',
        },
    )
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'https://gitplant-oggy.vercel.app'


def test_cors_preflight_allows_vercel_preview_origin() -> None:
    response = client.options(
        '/projects',
        headers={
            'Origin': 'https://preview-123.vercel.app',
            'Access-Control-Request-Method': 'POST',
        },
    )
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'https://preview-123.vercel.app'


def test_cors_debug_reports_origin_and_allowed_origins() -> None:
    origin = 'https://gitplant-oggy.vercel.app'
    response = client.get('/cors-debug', headers={'Origin': origin})
    assert response.status_code == 200
    body = response.json()
    assert body['origin'] == origin
    assert 'https://gitplant-oggy.vercel.app' in body['allowed_origins']
    assert body['allowed_origin_regex'] == r'https://.*\.vercel\.app'
