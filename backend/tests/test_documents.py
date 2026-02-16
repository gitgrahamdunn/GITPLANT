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
    engineer_headers = auth_headers("user@edms.local", "user123")

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
            "author_email": "user@edms.local",
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
    assert pull.json()["updates"][0]["revision"] == "B"

    history = client.get(f"/documents/{document_id}/history")
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["commit_message"] == "Updated PSV sizing basis"


def test_compare_revisions_returns_changed_fields():
    reset_db()
    engineer_headers = auth_headers("user@edms.local", "user123")

    doc = client.post(
        "/documents",
        headers=engineer_headers,
        json={
            "project_code": "PRJ-2",
            "document_number": "MECH-2201",
            "title": "Pump datasheet",
            "discipline": "Mechanical",
        },
    )
    document_id = doc.json()["id"]

    branch = client.post(
        f"/documents/{document_id}/branches", headers=engineer_headers, json={"name": "main"}
    )
    assert branch.status_code == 200

    rev_a = client.post(
        f"/documents/{document_id}/commit?branch=main",
        headers=engineer_headers,
        json={
            "revision": "A",
            "commit_message": "Initial issue",
            "file_hash": "hash-a",
            "author_email": "user@edms.local",
        },
    )
    assert rev_a.status_code == 200

    rev_b = client.post(
        f"/documents/{document_id}/commit?branch=main",
        headers=engineer_headers,
        json={
            "revision": "B",
            "commit_message": "Updated nozzle orientation",
            "file_hash": "hash-b",
            "author_email": "user@edms.local",
        },
    )
    assert rev_b.status_code == 200

    comparison = client.get(
        f"/documents/{document_id}/compare",
        params={"from_revision_id": rev_a.json()["id"], "to_revision_id": rev_b.json()["id"]},
    )
    assert comparison.status_code == 200

    payload = comparison.json()
    changed_field_names = {field["field"] for field in payload["changed_fields"]}
    assert "revision" in changed_field_names
    assert "commit_message" in changed_field_names
    assert "file_hash" in changed_field_names
    assert payload["is_same_file"] is False


def test_workflow_permissions_and_week8_reports():
    reset_db()
    engineer_headers = auth_headers("user@edms.local", "user123")
    controller_headers = auth_headers("user@edms.local", "user123")
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
            "author_email": "user@edms.local",
            "content_text": "old-value",
        },
    )
    assert rev.status_code == 200

    submit = client.post(
        f"/documents/{doc_id}/submit-for-approval",
        headers=engineer_headers,
        json={"revision_id": rev.json()["id"], "approver_email": "user@edms.local"},
    )
    assert submit.status_code == 200

    allowed_decision = client.post(
        f"/documents/{doc_id}/approvals/{submit.json()['id']}/decision",
        headers=engineer_headers,
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

    # verify status updated in DB
    with Session(engine) as session:
        stored_document = session.get(Document, doc_id)
        assert stored_document is not None
        assert stored_document.status == "IFC"


def test_document_search_transmittal_audit_and_dashboard_flow():
    reset_db()
    controller_headers = auth_headers("user@edms.local", "user123")

    doc = client.post(
        "/documents",
        headers=controller_headers,
        json={
            "project_code": "PRJ-6",
            "document_number": "MECH-6002",
            "title": "Pump GA drawing",
            "discipline": "Mechanical",
        },
    )
    assert doc.status_code == 200
    doc_id = doc.json()["id"]

    search = client.get("/documents/search", params={"q": "Pump", "discipline": "Mechanical"})
    assert search.status_code == 200
    assert search.json()["total"] == 1

    branch = client.post(
        f"/documents/{doc_id}/branches", headers=controller_headers, json={"name": "main"}
    )
    assert branch.status_code == 200

    rev = client.post(
        f"/documents/{doc_id}/commit?branch=main",
        headers=controller_headers,
        json={
            "revision": "A",
            "commit_message": "Issue for vendor",
            "file_hash": "hash-mech-a",
            "author_email": "user@edms.local",
        },
    )
    assert rev.status_code == 200

    transmittal = client.post(
        f"/documents/{doc_id}/transmittals",
        headers=controller_headers,
        json={
            "revision_id": rev.json()["id"],
            "transmittal_number": "TRM-0001",
            "issued_to": "Vendor-X",
            "vendor_code": "VX",
            "notes": "For quote",
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
    assert '"event_type"' in export_jsonl.text

    # keep these main-branch checks too
    audit = client.get(f"/documents/{doc_id}/audit-events")
    assert audit.status_code == 200
    assert len(audit.json()) >= 3

    summary = client.get("/documents/reports/dashboard-summary", headers=controller_headers)
    assert summary.status_code == 200
    assert summary.json()["total_documents"] == 1
    assert summary.json()["total_transmittals"] == 1

