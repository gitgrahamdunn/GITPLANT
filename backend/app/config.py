import os
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
TMP_ROOT = Path("/tmp")


def _resolve_writable_dir(*, env_var: str, default_dir_name: str) -> Path:
    configured_dir = os.getenv(env_var)
    if configured_dir:
        configured_path = Path(configured_dir)
        if not configured_path.is_absolute():
            return TMP_ROOT / configured_path
        return configured_path
    return TMP_ROOT / default_dir_name


def get_data_dir() -> Path:
    candidate = _resolve_writable_dir(env_var="DATA_DIR", default_dir_name="gitplant-data")

    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError:
        return candidate

    return TMP_ROOT / "gitplant-data"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_data_dir() -> Path:
    path = get_data_dir()
    try:
        return ensure_dir(path)
    except OSError:
        fallback = TMP_ROOT / "gitplant-data"
        return ensure_dir(fallback)


# Vercel serverless functions run on a read-only filesystem except for /tmp.
DEFAULT_DATA_DIR = get_data_dir()
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


def _resolve_path(path: str) -> Path:
    configured = Path(path)
    if not configured.is_absolute():
        configured = (TMP_ROOT / configured).resolve()
    return configured


def _ensure_path(path: str) -> Path:
    configured = _resolve_path(path)
    return ensure_dir(configured)


def get_storage_dir(*, ensure_exists: bool = True) -> Path:
    path = _resolve_writable_dir(env_var="STORAGE_DIR", default_dir_name="gitplant-storage")
    return ensure_dir(path) if ensure_exists else path


def get_document_storage_path(*, ensure_exists: bool = True) -> Path:
    if settings.document_storage_dir == str(DEFAULT_STORAGE_DIR):
        base_path = ensure_data_dir() / "documents" if ensure_exists else get_data_dir() / "documents"
        return ensure_dir(base_path) if ensure_exists else base_path
    return _ensure_path(settings.document_storage_dir) if ensure_exists else _resolve_path(settings.document_storage_dir)


def get_plant_storage_path(*, ensure_exists: bool = True) -> Path:
    if settings.plant_storage_dir == str(DEFAULT_PLANT_STORAGE_DIR):
        base_path = ensure_data_dir() / "plant" if ensure_exists else get_data_dir() / "plant"
        return ensure_dir(base_path) if ensure_exists else base_path
    return _ensure_path(settings.plant_storage_dir) if ensure_exists else _resolve_path(settings.plant_storage_dir)


def get_working_storage_path(*, ensure_exists: bool = True) -> Path:
    configured = os.getenv("WORKING_STORAGE_DIR")
    if configured:
        path = _ensure_path(configured) if ensure_exists else _resolve_path(configured)
        return path

    base = get_storage_dir(ensure_exists=ensure_exists)
    path = base / "projects"
    return ensure_dir(path) if ensure_exists else path
