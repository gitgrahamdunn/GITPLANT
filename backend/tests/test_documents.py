from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.db import engine, init_db
from app.main import app
from app.models import Approval, AuditEvent, Branch, Document, DocumentRevision, Transmittal

client = TestClient(app)


def auth_headers(email: str, password: str) -> dict[str, str]:
    login = client.post("/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def reset_db() -> None:
    init_db()
    with Session(engine) as session:
        session.exec(delete(AuditEvent))
        session.exec(delete(Transmittal))
        session.exec(delete(Approval))
        session.exec(delete(DocumentRevision))
        session.exec(delete(Branch))
        session.exec(delete(Document))
        session.commit()


def test_commit_push_pull_and_history_flow():
    reset_db()
    engineer_headers = auth_headers("engineer@edms.local", "engineer123")

    doc = client.post(
        "/documents",
        headers=engineer_headers,
        json={
            "project_code": "PRJ-1",
            "document_number": "P-1001",
            "title": "Compressor P&ID",
            "discipline": "Process",
        },
    )
    assert doc.status_code == 200
    document_id = doc.json()["id"]

    main_branch = client.post(
        f"/documents/{document_id}/branches", headers=engineer_headers, json={"name": "main"}
    )
    assert main_branch.status_code == 200
    main_branch_id = main_branch.json()["id"]

    moc_branch = client.post(
        f"/documents/{document_id}/branches",
        headers=engineer_headers,
        json={"name": "moc-2026-014"},
    )
    assert moc_branch.status_code == 200
    moc_branch_id = moc_branch.json()["id"]

    commit = client.post(
        f"/documents/{document_id}/commit?branch=moc-2026-014",
        headers=engineer_headers,
        json={
            "revision": "B",
            "commit_message": "Updated PSV sizing basis",
            "file_hash": "hash-b",
            "author_email": "engineer@edms.local",
            "content_text": "line-1\nline-2",
        },
    )
    assert commit.status_code == 200
    assert commit.json()["is_pushed"] is False

    push = client.post(f"/documents/branches/{moc_branch_id}/push", headers=engineer_headers)
    assert push.status_code == 200
    assert push.json()["pushed_count"] == 1
    assert push.json()["latest_revision"] == "B"

    pull = client.post(f"/documents/branches/{main_branch_id}/pull")
    assert pull.status_code == 200
    assert len(pull.json()["updates"]) == 1


def test_workflow_permissions_and_week8_reports():
    reset_db()
    engineer_headers = auth_headers("engineer@edms.local", "engineer123")
    controller_headers = auth_headers("controller@edms.local", "controller123")
    approver_headers = auth_headers("approver@edms.local", "approver123")

    doc = client.post(
        "/documents",
        headers=engineer_headers,
        json={
            "project_code": "PRJ-8",
            "document_number": "ELEC-8001",
            "title": "SLD Revamp",
            "discipline": "Electrical",
        },
    )
    assert doc.status_code == 200
    doc_id = doc.json()["id"]

    branch = client.post(
        f"/documents/{doc_id}/branches", headers=engineer_headers, json={"name": "main"}
    )
    assert branch.status_code == 200

    rev = client.post(
        f"/documents/{doc_id}/commit?branch=main",
        headers=engineer_headers,
        json={
            "revision": "A",
            "commit_message": "Issue for approval",
            "file_hash": "hash-elec-8001-a",
            "author_email": "engineer@edms.local",
            "content_text": "old-value",
        },
    )
    assert rev.status_code == 200

    rev2 = client.post(
        f"/documents/{doc_id}/commit?branch=main",
        headers=engineer_headers,
        json={
            "revision": "B",
            "commit_message": "Issue for approval update",
            "file_hash": "hash-elec-8001-b",
            "author_email": "engineer@edms.local",
            "content_text": "new-value",
        },
    )
    assert rev2.status_code == 200

    text_diff = client.get(
        f"/documents/{doc_id}/compare/text",
        params={"from_revision_id": rev.json()["id"], "to_revision_id": rev2.json()["id"]},
    )
    assert text_diff.status_code == 200
    assert "-old-value" in text_diff.json()["diff"]
    assert "+new-value" in text_diff.json()["diff"]

    submit = client.post(
        f"/documents/{doc_id}/submit-for-approval",
        headers=engineer_headers,
        json={"revision_id": rev.json()["id"], "approver_email": "approver@edms.local"},
    )
    assert submit.status_code == 200

    # engineer should NOT be able to decide approval
    forbidden_decision = client.post(
        f"/documents/{doc_id}/approvals/{submit.json()['id']}/decision",
        headers=engineer_headers,
        json={"decision": "approved", "comments": "not allowed"},
    )
    assert forbidden_decision.status_code == 403

    allowed_decision = client.post(
        f"/documents/{doc_id}/approvals/{submit.json()['id']}/decision",
        headers=approver_headers,
        json={"decision": "approved", "comments": "approved by approver"},
    )
    assert allowed_decision.status_code == 200

    transmittal = client.post(
        f"/documents/{doc_id}/transmittals",
        headers=controller_headers,
        json={
            "revision_id": rev.json()["id"],
            "transmittal_number": "TRM-8001",
            "issued_to": "Vendor-Z",
            "vendor_code": "VZ",
            "notes": "IFC issue",
        },
    )
    assert transmittal.status_code == 200

    extended = client.get(
        "/documents/reports/dashboard-extended",
        headers=controller_headers,
    )
    assert extended.status_code == 200
    assert extended.json()["total_documents"] == 1

    export_csv = client.get(
        f"/documents/{doc_id}/audit-events/export",
        headers=controller_headers,
    )
    assert export_csv.status_code == 200
    assert export_csv.headers["content-type"].startswith("text/csv")
    assert "event_type" in export_csv.text

    export_jsonl = client.get(
        f"/documents/{doc_id}/audit-events/export-jsonl",
        headers=controller_headers,
    )
    assert export_jsonl.status_code == 200
    assert export_jsonl.headers["content-type"].startswith("application/x-ndjson")
    assert "\"event_type\"" in export_jsonl.text


def test_backup_and_restore_snapshot_roundtrip():
    reset_db()
    controller_headers = auth_headers("controller@edms.local", "controller123")
    engineer_headers = auth_headers("engineer@edms.local", "engineer123")

    doc = client.post(
        "/documents",
        headers=engineer_headers,
        json={
            "project_code": "PRJ-12",
            "document_number": "PROC-1200",
            "title": "Operating philosophy",
            "discipline": "Process",
        },
    )
    assert doc.status_code == 200

    backup = client.get("/documents/admin/backup", headers=controller_headers)
    assert backup.status_code == 200
    assert backup.json()["snapshot"]["documents"]

    with Session(engine) as session:
        session.exec(delete(AuditEvent))
        session.exec(delete(Transmittal))
        session.exec(delete(Approval))
        session.exec(delete(DocumentRevision))
        session.exec(delete(Branch))
        session.exec(delete(Document))
        session.commit()

    restore = client.post(
        "/documents/admin/restore",
        headers=controller_headers,
        json={"snapshot": backup.json()["snapshot"]},
    )
    assert restore.status_code == 200
    assert restore.json()["status"] == "restored"

    search_after = client.get("/documents/search", params={"q": "Operating"})
    assert search_after.status_code == 200
    assert search_after.json()["total"] == 1
