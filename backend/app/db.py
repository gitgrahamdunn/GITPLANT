from sqlmodel import SQLModel, Session, create_engine

from app.config import resolve_sqlite_path, settings

sqlite_path = resolve_sqlite_path(settings.database_url)

engine = create_engine(settings.database_url, echo=False)


def init_db() -> None:
    if sqlite_path is not None:
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
