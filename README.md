# EDMS (Week 1–5 Setup)

This repository now contains the **Week 1–5 project foundation** for an oil & gas EDMS MVP.

## What is included
- FastAPI backend scaffold
- PostgreSQL local dependency via Docker Compose
- Starter domain entities (`User`, `Document`, `Branch`, `DocumentRevision`, `Approval`, `Transmittal`)
- Starter auth endpoint with role-based demo users
- Week 2 versioning endpoints for document commit/push/pull/history
- Week 3 revision comparison endpoint for metadata-level diffing
- Week 4 workflow approval endpoints with status transitions (WIP/IFA/IFR/IFC)
- Week 5 document search and transmittal endpoints
- Basic tests for health, auth, versioning flow, revision comparison, approvals, search, and transmittals

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

## Week 5 API highlights
- `GET /documents/search?q=...&project_code=...&discipline=...&status=...`
  - Metadata search for document title/number and optional filters.
- `POST /documents/{document_id}/transmittals`
  - Create transmittal records for a specific revision.
- `GET /documents/{document_id}/transmittals`
  - List transmittals issued for that document.

## Planned next steps (Week 6+)
- Real JWT/OIDC authentication
- File-level diff integrations (CAD/PDF-specific)
- Audit event streaming/export
- Dashboard/reporting for document controllers
