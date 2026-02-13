from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.db import engine
from app.main import app
from app.models import Approval, Branch, Document, DocumentRevision

client = TestClient(app)


def reset_db() -> None:
    with Session(engine) as session:
        session.exec(delete(Approval))
        session.exec(delete(DocumentRevision))
        session.exec(delete(Branch))
        session.exec(delete(Document))
        session.commit()


def test_commit_push_pull_and_history_flow():
    reset_db()

    doc = client.post(
        "/documents",
        json={
            "project_code": "PRJ-1",
            "document_number": "P-1001",
            "title": "Compressor P&ID",
            "discipline": "Process",
        },
    )
    assert doc.status_code == 200
    document_id = doc.json()["id"]

    main_branch = client.post(f"/documents/{document_id}/branches", json={"name": "main"})
    assert main_branch.status_code == 200
    main_branch_id = main_branch.json()["id"]

    moc_branch = client.post(f"/documents/{document_id}/branches", json={"name": "moc-2026-014"})
    assert moc_branch.status_code == 200
    moc_branch_id = moc_branch.json()["id"]

    commit = client.post(
        f"/documents/{document_id}/commit?branch=moc-2026-014",
        json={
            "revision": "B",
            "commit_message": "Updated PSV sizing basis",
            "file_hash": "hash-b",
            "author_email": "engineer@edms.local",
        },
    )
    assert commit.status_code == 200
    assert commit.json()["is_pushed"] is False

    push = client.post(f"/documents/branches/{moc_branch_id}/push")
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

    doc = client.post(
        "/documents",
        json={
            "project_code": "PRJ-2",
            "document_number": "MECH-2201",
            "title": "Pump datasheet",
            "discipline": "Mechanical",
        },
    )
    document_id = doc.json()["id"]

    branch = client.post(f"/documents/{document_id}/branches", json={"name": "main"})
    assert branch.status_code == 200

    rev_a = client.post(
        f"/documents/{document_id}/commit?branch=main",
        json={
            "revision": "A",
            "commit_message": "Initial issue",
            "file_hash": "hash-a",
            "author_email": "engineer@edms.local",
        },
    )
    assert rev_a.status_code == 200

    rev_b = client.post(
        f"/documents/{document_id}/commit?branch=main",
        json={
            "revision": "B",
            "commit_message": "Updated nozzle orientation",
            "file_hash": "hash-b",
            "author_email": "engineer@edms.local",
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


def test_workflow_submit_and_approve_updates_status_to_ifc():
    reset_db()

    doc = client.post(
        "/documents",
        json={
            "project_code": "PRJ-3",
            "document_number": "ELEC-3001",
            "title": "Single line diagram",
            "discipline": "Electrical",
        },
    )
    assert doc.status_code == 200
    document_id = doc.json()["id"]
    assert doc.json()["status"] == "WIP"

    branch = client.post(f"/documents/{document_id}/branches", json={"name": "main"})
    assert branch.status_code == 200

    commit = client.post(
        f"/documents/{document_id}/commit?branch=main",
        json={
            "revision": "A",
            "commit_message": "Initial issue for approval",
            "file_hash": "hash-elec-a",
            "author_email": "engineer@edms.local",
        },
    )
    assert commit.status_code == 200

    submit = client.post(
        f"/documents/{document_id}/submit-for-approval",
        json={"revision_id": commit.json()["id"], "approver_email": "approver@edms.local"},
    )
    assert submit.status_code == 200
    assert submit.json()["decision"] == "pending"

    decision = client.post(
        f"/documents/{document_id}/approvals/{submit.json()['id']}/decision",
        json={"decision": "approved", "comments": "Looks good"},
    )
    assert decision.status_code == 200
    assert decision.json()["decision"] == "approved"

    doc_after = client.get(f"/documents/{document_id}/history")
    assert doc_after.status_code == 200

    # verify status moved to IFC
    with Session(engine) as session:
        stored_document = session.get(Document, document_id)
        assert stored_document is not None
        assert stored_document.status == "IFC"
