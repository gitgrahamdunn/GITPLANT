import os
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent


def _default_data_dir() -> Path:
    configured_data_dir = os.getenv("DATA_DIR")
    if configured_data_dir:
        candidate = Path(configured_data_dir)
        if not candidate.is_absolute():
            candidate = Path("/tmp") / candidate
    else:
        candidate = Path("/tmp/gitplant-data")

    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError:
        return candidate

    return Path("/tmp/gitplant-data")


def _ensure_writable_data_dir(path: Path) -> Path:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError:
        fallback = Path("/tmp/gitplant-data")
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


# Vercel serverless functions run on a read-only filesystem except for /tmp.
DEFAULT_DATA_DIR = _ensure_writable_data_dir(_default_data_dir())
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "edms.db"
DEFAULT_DATABASE_URL = f"sqlite:///{quote(str(DEFAULT_DB_PATH), safe='/')}"
DEFAULT_STORAGE_DIR = DEFAULT_DATA_DIR / "documents"
DEFAULT_PLANT_STORAGE_DIR = DEFAULT_DATA_DIR / "plant"


class Settings(BaseSettings):
    app_name: str = "EDMS API"
    app_env: str = "dev"
    database_url: str = DEFAULT_DATABASE_URL
    document_storage_dir: str = str(DEFAULT_STORAGE_DIR)
    plant_storage_dir: str = str(DEFAULT_PLANT_STORAGE_DIR)
    enable_demo_endpoints: bool | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def demo_endpoints_enabled(self) -> bool:
        if self.enable_demo_endpoints is not None:
            return self.enable_demo_endpoints
        return self.app_env.lower() in {"dev", "development", "local", "test"}

    @property
    def demo_endpoints_reason(self) -> str:
        if self.enable_demo_endpoints is not None:
            return "enabled by ENABLE_DEMO_ENDPOINTS" if self.enable_demo_endpoints else "disabled by ENABLE_DEMO_ENDPOINTS"
        return f"derived from APP_ENV={self.app_env}"


settings = Settings()


def resolve_sqlite_path(database_url: str) -> Path | None:
    if not database_url.startswith("sqlite"):
        return None

    parsed = urlparse(database_url)
    db_path = unquote(parsed.path)

    if not db_path or db_path == ":memory:":
        return None

    path_obj = Path(db_path)
    if not path_obj.is_absolute():
        path_obj = (Path.cwd() / path_obj).resolve()

    return path_obj


def sanitize_database_url(database_url: str) -> str:
    parsed = urlparse(database_url)
    if parsed.username is None and parsed.password is None:
        return database_url

    username = parsed.username or ""
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    auth = username
    if parsed.password:
        auth = f"{auth}:***"

    netloc = f"{auth}@{host}{port}" if auth else f"{host}{port}"
    return parsed._replace(netloc=netloc).geturl()


def _ensure_path(path: str) -> Path:
    configured = Path(path)
    if not configured.is_absolute():
        configured = (BACKEND_ROOT / configured).resolve()
    configured.mkdir(parents=True, exist_ok=True)
    return configured


def get_document_storage_path() -> Path:
    return _ensure_path(settings.document_storage_dir)


def get_plant_storage_path() -> Path:
    return _ensure_path(settings.plant_storage_dir)
