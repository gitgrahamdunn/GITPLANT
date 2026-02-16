from pathlib import Path
from urllib.parse import quote, unquote, urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = BACKEND_ROOT / ".data"
DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "edms.db"
DEFAULT_DATABASE_URL = f"sqlite:///{quote(str(DEFAULT_DB_PATH), safe='/')}"
DEFAULT_STORAGE_DIR = BACKEND_ROOT / "storage" / "documents"


class Settings(BaseSettings):
    app_name: str = "EDMS API"
    app_env: str = "development"
    database_url: str = DEFAULT_DATABASE_URL
    document_storage_dir: str = str(DEFAULT_STORAGE_DIR)
    enable_demo_tools: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


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


def get_document_storage_path() -> Path:
    configured = Path(settings.document_storage_dir)
    if not configured.is_absolute():
        configured = (BACKEND_ROOT / configured).resolve()
    configured.mkdir(parents=True, exist_ok=True)
    return configured
