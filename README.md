# EDMS (Week 1 Setup)

This repository now contains the **Week 1 project foundation** for an oil & gas EDMS MVP.

## What is included
- FastAPI backend scaffold
- PostgreSQL local dependency via Docker Compose
- Starter domain entities (`User`, `Document`, `DocumentRevision`)
- Starter auth endpoint with role-based demo users
- Basic tests for health and login endpoints

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

## Planned next steps (Week 2+)
- Real JWT/OIDC authentication
- Git-like commit/push/pull document revision endpoints
- Workflow states and approvals
- Search indexing
