
# EDMS (Week 1–12 MVP)

This repository now contains the **Week 1–12 MVP** foundation for an oil & gas EDMS. 

## What is included
- FastAPI backend scaffold + PostgreSQL local dependency via Docker Compose
- Core entities: `User`, `Document`, `Branch`, `DocumentRevision`, `Approval`, `Transmittal`, `AuditEvent`
- Versioning workflows (`commit`, `push`, `pull`, history, metadata compare, text diff)
- Workflow approvals with status transitions (`WIP` → `IFA` → `IFC`/`IFR`)
- Search, transmittals, audit trail, CSV/JSONL audit exports
- Dashboard summary + extended breakdown reporting
- Signed bearer-token auth and role-based endpoint protections
- Week 11 hardening middleware (security headers, request id, response timing)
- Week 12 backup/restore snapshot endpoints for MVP operational drills


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
2. Setup backend:
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

5. Run frontend:
   ```bash
   cd frontend
   npm install
   cp .env.example .env
   npm run dev
   ```
6. Open frontend:
   - http://127.0.0.1:5173


## Week 11–12 MVP completion highlights
- `GET /health/live` and `GET /health/ready`
- Security hardening headers and request tracing middleware
- `GET /documents/admin/backup`
- `POST /documents/admin/restore`

## Next steps after MVP
- OIDC/SAML integration
- CAD/PDF specialized diffing
- Frontend dashboards and document controller UI
- Policy-based archival/retention

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
