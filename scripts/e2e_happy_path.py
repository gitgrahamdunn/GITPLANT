import json
import subprocess
import time
import urllib.request
from urllib.error import URLError


def wait_for(url: str, timeout: int = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url) as resp:
                if resp.status < 500:
                    return
        except URLError:
            pass
        time.sleep(1)
    raise RuntimeError(f"Timed out waiting for {url}")


def request(url: str, method: str = "GET", headers: dict | None = None, payload: dict | None = None):
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, method=method, headers=headers or {}, data=body)
    with urllib.request.urlopen(req) as resp:
        raw = resp.read().decode()
        return resp.status, json.loads(raw) if raw else {}


def main() -> None:
    backend = subprocess.Popen(["bash", "-lc", "cd backend && APP_ENV=dev ENABLE_DEMO_ENDPOINTS=true uvicorn app.main:app --host 127.0.0.1 --port 8000"])
    frontend = subprocess.Popen(["bash", "-lc", "cd frontend && npm run dev -- --host 127.0.0.1 --port 5173"])
    try:
        wait_for("http://127.0.0.1:8000/health/live")
        wait_for("http://127.0.0.1:5173")

        with urllib.request.urlopen("http://127.0.0.1:5173") as resp:
            html = resp.read().decode()
            assert resp.status == 200
            assert "<div id=\"root\">" in html

        code, login = request(
            "http://127.0.0.1:8000/auth/login",
            method="POST",
            headers={"Content-Type": "application/json"},
            payload={"email": "user@edms.local", "password": "user123"},
        )
        assert code == 200
        auth = {"Authorization": f"Bearer {login['access_token']}", "Content-Type": "application/json"}

        code, _ = request("http://127.0.0.1:8000/dev/seed", method="POST", headers=auth)
        assert code == 200

        code, docs = request("http://127.0.0.1:8000/documents", headers=auth)
        assert code == 200 and docs["total"] > 0
        doc_id = docs["items"][0]["id"]

        project_number = f"PRJ-{int(time.time()) % 100000}"
        code, project = request(
            "http://127.0.0.1:8000/projects",
            method="POST",
            headers=auth,
            payload={"project_number": project_number, "name": "E2E Project"},
        )
        assert code == 200

        code, _ = request(
            f"http://127.0.0.1:8000/projects/{project['id']}/pull",
            method="POST",
            headers=auth,
            payload={"document_ids": [doc_id]},
        )
        assert code == 200

        code, detail = request(f"http://127.0.0.1:8000/projects/{project_number}", headers=auth)
        assert code == 200 and len(detail["working_docs"]) >= 1
        wr_id = detail["working_docs"][0]["id"]

        code, _ = request(f"http://127.0.0.1:8000/projects/{project_number}/working/{wr_id}/ready", method="POST", headers=auth)
        assert code == 200

        code, merged = request(f"http://127.0.0.1:8000/projects/{project_number}/merge", method="POST", headers=auth)
        assert code == 200 and merged["merged_count"] >= 1

        print("E2E happy path passed")
    finally:
        backend.terminate()
        frontend.terminate()


if __name__ == "__main__":
    main()
