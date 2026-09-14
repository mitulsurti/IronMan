from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from ironman.config import get_settings


_engine = create_engine(get_settings().database_url, pool_pre_ping=True)


if _engine.dialect.name == "sqlite":
    @event.listens_for(_engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def database_is_healthy() -> bool:
    with _engine.connect() as connection:
        return connection.execute(text("SELECT 1")).scalar_one() == 1
