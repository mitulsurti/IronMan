"""Add ordered PortfolioStateVersion boundary and SQLite protections."""
from alembic import op
from sqlalchemy import inspect, text

revision = "0003_snapshot_boundary"
down_revision = "0002_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("portfolio_state_versions")}
    if "boundary_sequence" not in columns:
        op.add_column("portfolio_state_versions", __import__("sqlalchemy").Column("boundary_sequence", __import__("sqlalchemy").Integer(), nullable=False, server_default="0"))
    if "boundary_event_id" not in columns:
        op.add_column("portfolio_state_versions", __import__("sqlalchemy").Column("boundary_event_id", __import__("sqlalchemy").Uuid(), nullable=True))
    if bind.dialect.name == "sqlite":
        statements = [
            "CREATE TRIGGER IF NOT EXISTS ledger_events_immutable_update BEFORE UPDATE ON ledger_events WHEN OLD.posted = 1 BEGIN SELECT RAISE(ABORT, 'posted ledger events are immutable'); END",
            "CREATE TRIGGER IF NOT EXISTS ledger_events_immutable_delete BEFORE DELETE ON ledger_events WHEN OLD.posted = 1 BEGIN SELECT RAISE(ABORT, 'posted ledger events are immutable'); END",
            "CREATE TRIGGER IF NOT EXISTS ledger_legs_immutable_update BEFORE UPDATE ON ledger_legs WHEN EXISTS (SELECT 1 FROM ledger_events WHERE id = OLD.event_id AND posted = 1) BEGIN SELECT RAISE(ABORT, 'posted ledger legs are immutable'); END",
            "CREATE TRIGGER IF NOT EXISTS ledger_legs_immutable_delete BEFORE DELETE ON ledger_legs WHEN EXISTS (SELECT 1 FROM ledger_events WHERE id = OLD.event_id AND posted = 1) BEGIN SELECT RAISE(ABORT, 'posted ledger legs are immutable'); END",
            "CREATE TRIGGER IF NOT EXISTS portfolio_state_versions_immutable_update BEFORE UPDATE ON portfolio_state_versions BEGIN SELECT RAISE(ABORT, 'portfolio state versions are immutable'); END",
            "CREATE TRIGGER IF NOT EXISTS portfolio_state_versions_immutable_delete BEFORE DELETE ON portfolio_state_versions BEGIN SELECT RAISE(ABORT, 'portfolio state versions are immutable'); END",
        ]
        for statement in statements:
            bind.execute(text(statement))


def downgrade() -> None:
    raise RuntimeError("Phase 2 ledger downgrade is intentionally prohibited")
