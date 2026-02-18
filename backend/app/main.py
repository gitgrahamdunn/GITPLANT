import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_db
from app.routers import auth, dev, documents, health, projects

app = FastAPI(title=settings.app_name)

if settings.app_env.lower() in {"dev", "development", "local", "test"}:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(projects.router)
app.include_router(dev.router)


@app.middleware("http")
async def hardening_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Process-Time-ms"] = str(duration_ms)
    return response


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", tags=["root"])
def read_root():
    return {
        "name": settings.app_name,
        "environment": settings.app_env,
        "message": "EDMS backend is running",
    }


frontend_dist = (Path(__file__).resolve().parents[2] / "frontend" / "dist").resolve()
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith(("auth", "documents", "projects", "dev", "health", "docs", "openapi.json")):
            return {"detail": "Not Found"}
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"detail": "Not Found"}
