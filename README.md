# EDMS (Week 1–4 Setup)

This repository now contains the **Week 1–4 project foundation** for an oil & gas EDMS MVP.

## What is included
- FastAPI backend scaffold
- PostgreSQL local dependency via Docker Compose
- Starter domain entities (`User`, `Document`, `Branch`, `DocumentRevision`, `Approval`)
- Starter auth endpoint with role-based demo users
- Week 2 versioning endpoints for document commit/push/pull/history
- Week 3 revision comparison endpoint for metadata-level diffing
- Week 4 workflow approval endpoints with status transitions (WIP/IFA/IFR/IFC)
- Basic tests for health, auth, versioning flow, revision comparison, and approvals

## Quick start
1. Start PostgreSQL:
   ```bash
   docker compose up -d postgres
   ```
2. Create Python environment and install dependencies:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
3. Run API:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Open docs:
   - http://127.0.0.1:8000/docs

## Week 2 API highlights
- `POST /documents` create document
- `POST /documents/{document_id}/branches` create branch
- `POST /documents/{document_id}/commit?branch=...` commit revision
- `POST /documents/branches/{branch_id}/push` push branch revisions
- `POST /documents/branches/{branch_id}/pull` pull latest pushed revisions
- `GET /documents/{document_id}/history` revision history

## Week 3 API highlight
- `GET /documents/{document_id}/compare?from_revision_id=...&to_revision_id=...`
  - Compares two revisions and returns changed metadata fields plus same/different file hash signal.

## Week 4 API highlights
- `POST /documents/{document_id}/submit-for-approval`
  - Creates an approval task and changes document status to `IFA`.
- `POST /documents/{document_id}/approvals/{approval_id}/decision`
  - Records `approved` or `rejected` decision and sets status to `IFC` or `IFR`.

## Planned next steps (Week 5+)
- Real JWT/OIDC authentication
- Search indexing
- File-level diff integrations (CAD/PDF-specific)
- Transmittal management
