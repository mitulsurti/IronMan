import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from ironman.ledger.models import Account, AccountType


def run_alembic(repo_backend: Path, database_url: str, revision: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", revision],
        cwd=repo_backend,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_existing_revision_0002_upgrades_to_head(tmp_path: Path):
    backend = Path(__file__).parents[1]
    database_url = f"sqlite:///{tmp_path / 'upgrade.db'}"
    run_alembic(backend, database_url, "0002_ledger")
    engine = create_engine(database_url)
    with Session(engine) as session:
        session.add(Account(name="existing", account_type=AccountType.BANK, created_at=datetime.now(timezone.utc)))
        session.commit()
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE portfolio_state_versions DROP COLUMN boundary_sequence"))
        connection.execute(text("ALTER TABLE portfolio_state_versions DROP COLUMN boundary_event_id"))
    run_alembic(backend, database_url, "head")
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("portfolio_state_versions")}
    assert {"boundary_sequence", "boundary_event_id"}.issubset(columns)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM accounts WHERE name = 'existing'")).scalar_one() == 1
        trigger_names = {row[0] for row in connection.execute(text("SELECT name FROM sqlite_master WHERE type = 'trigger'"))}
    assert {
        "ledger_legs_immutable_update",
        "ledger_legs_immutable_delete",
        "portfolio_state_versions_immutable_update",
        "portfolio_state_versions_immutable_delete",
    }.issubset(trigger_names)
    engine.dispose()
