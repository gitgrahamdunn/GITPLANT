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
