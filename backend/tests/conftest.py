from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from ironman.db.base import Base
from ironman.ledger import models  # noqa: F401
from ironman.intelligence import models as intelligence_models  # noqa: F401
from ironman.data_fabric import models as data_fabric_models  # noqa: F401
from ironman.research import evidence as evidence_models  # noqa: F401


@pytest.fixture
def sqlite_session(tmp_path: Path) -> Generator[Session, None, None]:
    engine = create_engine(f"sqlite:///{tmp_path / 'phase2.db'}")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("CREATE TRIGGER ledger_events_immutable_update BEFORE UPDATE ON ledger_events WHEN OLD.posted = 1 BEGIN SELECT RAISE(ABORT, 'posted ledger events are immutable'); END"))
        connection.execute(text("CREATE TRIGGER ledger_events_immutable_delete BEFORE DELETE ON ledger_events WHEN OLD.posted = 1 BEGIN SELECT RAISE(ABORT, 'posted ledger events are immutable'); END"))
        connection.execute(text("CREATE TRIGGER ledger_legs_immutable_update BEFORE UPDATE ON ledger_legs WHEN EXISTS (SELECT 1 FROM ledger_events WHERE id = OLD.event_id AND posted = 1) BEGIN SELECT RAISE(ABORT, 'posted ledger legs are immutable'); END"))
        connection.execute(text("CREATE TRIGGER ledger_legs_immutable_delete BEFORE DELETE ON ledger_legs WHEN EXISTS (SELECT 1 FROM ledger_events WHERE id = OLD.event_id AND posted = 1) BEGIN SELECT RAISE(ABORT, 'posted ledger legs are immutable'); END"))
        connection.execute(text("CREATE TRIGGER portfolio_state_versions_immutable_update BEFORE UPDATE ON portfolio_state_versions BEGIN SELECT RAISE(ABORT, 'portfolio state versions are immutable'); END"))
        connection.execute(text("CREATE TRIGGER portfolio_state_versions_immutable_delete BEFORE DELETE ON portfolio_state_versions BEGIN SELECT RAISE(ABORT, 'portfolio state versions are immutable'); END"))
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as session:
        yield session
        session.rollback()
    engine.dispose()
