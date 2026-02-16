from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.db import engine, init_db
from app.main import app
from app.models import (
    Approval,
    AuditEvent,
    Branch,
    Document,
    DocumentRevision,
    Project,
    ProjectWorkingRevision,
    Transmittal,
)

client = TestClient(app)


def auth_headers(email: str, password: str) -> dict[str, str]:
    login = client.post("/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def reset_db() -> None:
    init_db()
    with Session(engine) as session:
        session.exec(delete(ProjectWorkingRevision))
        session.exec(delete(Project))
        session.exec(delete(AuditEvent))
        session.exec(delete(Transmittal))
        session.exec(delete(Approval))
        session.exec(delete(DocumentRevision))
        session.exec(delete(Branch))
        session.exec(delete(Document))
        session.commit()


def _create_document(headers: dict[str, str], document_number: str) -> int:
    response = client.post(
        "/documents",
        headers=headers,
        json={
            "project_code": "PLANT",
            "document_number": document_number,
            "title": f"Title {document_number}",
            "discipline": "Process",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_project_working_set_pull_ready_merge_flow():
    reset_db()
    headers = auth_headers("user@edms.local", "user123")

    doc1_id = _create_document(headers, "DOC-001")
    doc2_id = _create_document(headers, "DOC-002")

    project_create = client.post(
        "/projects",
        headers=headers,
        json={"project_number": "PRJ-100", "name": "Test"},
    )
    assert project_create.status_code == 200
    project_id = project_create.json()["id"]

    pull = client.post(
        f"/projects/{project_id}/pull",
        headers=headers,
        json={"document_ids": [doc1_id, doc2_id]},
    )
    assert pull.status_code == 200
    assert len(pull.json()["created"]) == 2

    active_projects = client.get("/projects?status=ACTIVE", headers=headers)
    assert active_projects.status_code == 200
    assert len(active_projects.json()) == 1

    projects_summary = client.get("/projects", headers=headers)
    assert projects_summary.status_code == 200
    prj = next(
        item for item in projects_summary.json() if item["project_number"] == "PRJ-100"
    )
    assert prj["working_doc_count"] == 2

    detail = client.get("/projects/PRJ-100", headers=headers)
    assert detail.status_code == 200
    assert len(detail.json()["working_docs"]) == 2
    doc1_working = next(
        item
        for item in detail.json()["working_docs"]
        if item["document_number"] == "DOC-001"
    )

    upload = client.post(
        f"/projects/{project_id}/working/{doc1_working['id']}/upload",
        headers=headers,
        files={"file": ("updated.pdf", b"%PDF-1.4 project content", "application/pdf")},
    )
    assert upload.status_code == 200

    ready = client.post(
        f"/projects/PRJ-100/working/{doc1_working['id']}/ready",
        headers=headers,
    )
    assert ready.status_code == 200
    assert ready.json()["status"] == "READY"

    merge = client.post("/projects/PRJ-100/merge", headers=headers)
    assert merge.status_code == 200
    assert merge.json()["merged_count"] == 1
    assert merge.json()["merged_items"][0]["document_number"] == "DOC-001"

    plant_upload = client.post(
        f"/documents/{doc2_id}/plant/upload",
        headers=headers,
        files={"file": ("plant.pdf", b"%PDF-1.4 plant content", "application/pdf")},
    )
    assert plant_upload.status_code == 200

    documents = client.get("/documents", headers=headers)
    assert documents.status_code == 200
    doc1 = next(
        item
        for item in documents.json()["items"]
        if item["document_number"] == "DOC-001"
    )
    doc2 = next(
        item
        for item in documents.json()["items"]
        if item["document_number"] == "DOC-002"
    )
    assert doc1["current_revision"] != "A"
    assert doc2["current_revision"] != "A"

    detail_after = client.get("/projects/PRJ-100", headers=headers)
    doc1_after = next(
        item
        for item in detail_after.json()["working_docs"]
        if item["document_number"] == "DOC-001"
    )
    assert doc1_after["status"] == "MERGED"

    audit_events = client.get(f"/documents/{doc1_id}/audit-events")
    assert audit_events.status_code == 200
    event_types = {event["event_type"] for event in audit_events.json()}
    assert "project_pull" in event_types
    assert "project_ready" in event_types
    assert "project_merged" in event_types
