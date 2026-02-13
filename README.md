# EDMS (Week 1–10 Setup)

This repository now contains the **Week 1–10 project foundation** for an oil & gas EDMS MVP.
This PR re-issue includes a fresh commit to make merge/review tooling pick up a clean head for conflict resolution.


## What is included
- FastAPI backend scaffold
- PostgreSQL local dependency via Docker Compose
- Starter domain entities (`User`, `Document`, `Branch`, `DocumentRevision`, `Approval`, `Transmittal`, `AuditEvent`)
- Week 7 token-based auth context and role checks for protected operations
- Week 8 audit CSV export and extended dashboard breakdown reporting
- Week 9 signed bearer token issuance/verification for stronger auth than plain demo tokens
- Week 10 text-diff compare endpoint and JSONL audit export for external integration pipelines

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

## Week 9 API highlights
- `POST /auth/login`
  - Returns an HMAC-signed bearer token with expiration and role claims.
- `GET /auth/me`
  - Validates signature + expiry and returns authenticated user profile.

## Week 10 API highlights
- `GET /documents/{document_id}/compare/text?from_revision_id=...&to_revision_id=...`
  - Returns a unified text diff between revision contents.
- `GET /documents/{document_id}/audit-events/export-jsonl`
  - Exports audit events in JSONL format for external ingestion.

## Planned next steps (Week 11+)
- Real OIDC/SAML provider integration
- File-level CAD/PDF diff integrations
- Analytics dashboard frontend
- Policy-based retention and archival
