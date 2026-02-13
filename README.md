# EDMS (Week 1–8 Setup)

This repository now contains the **Week 1–8 project foundation** for an oil & gas EDMS MVP.

## What is included
- FastAPI backend scaffold
- PostgreSQL local dependency via Docker Compose
- Starter domain entities (`User`, `Document`, `Branch`, `DocumentRevision`, `Approval`, `Transmittal`, `AuditEvent`)
- Week 7 token-based auth context and role checks for protected operations
- Week 2 versioning endpoints for document commit/push/pull/history
- Week 3 revision comparison endpoint for metadata-level diffing
- Week 4 workflow approval endpoints with status transitions (WIP/IFA/IFR/IFC)
- Week 5 document search and transmittal endpoints
- Week 6 audit trail and dashboard summary endpoints
- Week 8 audit CSV export and extended dashboard breakdown reporting

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

## Week 7 API highlights
- `POST /auth/login`
  - Returns demo bearer token including role context.
- `GET /auth/me`
  - Returns authenticated user profile from bearer token.
- Protected role checks on document create/commit/push/approval/transmittal/reporting endpoints.

## Week 8 API highlights
- `GET /documents/{document_id}/audit-events/export`
  - Exports audit events as CSV.
- `GET /documents/reports/dashboard-extended`
  - Returns total docs with status and discipline breakdown.

## Planned next steps (Week 9+)
- Real JWT/OIDC integration
- File-level diff integrations (CAD/PDF-specific)
- Audit export integrations to external compliance stores
- Dashboard/reporting UI
