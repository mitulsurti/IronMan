"""Create Phase 2 ledger and portfolio-state tables."""
from alembic import op
from sqlalchemy import text

revision = "0002_ledger"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    from ironman.db.base import Base
    from ironman.ledger import models  # noqa: F401
    Base.metadata.create_all(bind=bind)
    if bind.dialect.name == "sqlite":
      bind.execute(text("CREATE TRIGGER ledger_events_immutable_update BEFORE UPDATE ON ledger_events WHEN OLD.posted = 1 BEGIN SELECT RAISE(ABORT, 'posted ledger events are immutable'); END"))
      bind.execute(text("CREATE TRIGGER ledger_events_immutable_delete BEFORE DELETE ON ledger_events WHEN OLD.posted = 1 BEGIN SELECT RAISE(ABORT, 'posted ledger events are immutable'); END"))
      bind.execute(text("CREATE TRIGGER ledger_legs_immutable_update BEFORE UPDATE ON ledger_legs WHEN EXISTS (SELECT 1 FROM ledger_events WHERE id = OLD.event_id AND posted = 1) BEGIN SELECT RAISE(ABORT, 'posted ledger legs are immutable'); END"))
      bind.execute(text("CREATE TRIGGER ledger_legs_immutable_delete BEFORE DELETE ON ledger_legs WHEN EXISTS (SELECT 1 FROM ledger_events WHERE id = OLD.event_id AND posted = 1) BEGIN SELECT RAISE(ABORT, 'posted ledger legs are immutable'); END"))
      bind.execute(text("CREATE TRIGGER portfolio_state_versions_immutable_update BEFORE UPDATE ON portfolio_state_versions BEGIN SELECT RAISE(ABORT, 'portfolio state versions are immutable'); END"))
      bind.execute(text("CREATE TRIGGER portfolio_state_versions_immutable_delete BEFORE DELETE ON portfolio_state_versions BEGIN SELECT RAISE(ABORT, 'portfolio state versions are immutable'); END"))
    elif bind.dialect.name == "postgresql":
        bind.execute(text("""
            CREATE OR REPLACE FUNCTION prevent_posted_ledger_mutation() RETURNS trigger AS $$
            BEGIN
              IF OLD.posted THEN
                RAISE EXCEPTION 'posted ledger events are immutable';
              END IF;
              RETURN OLD;
            END;
            $$ LANGUAGE plpgsql;
        """))
        bind.execute(text("""
            DROP TRIGGER IF EXISTS ledger_events_immutable ON ledger_events;
            CREATE TRIGGER ledger_events_immutable
            BEFORE UPDATE OR DELETE ON ledger_events
            FOR EACH ROW EXECUTE FUNCTION prevent_posted_ledger_mutation();
        """))
        bind.execute(text("""
            CREATE OR REPLACE FUNCTION prevent_posted_ledger_leg_mutation() RETURNS trigger AS $$
            BEGIN
              IF EXISTS (SELECT 1 FROM ledger_events WHERE id = OLD.event_id AND posted) THEN
                RAISE EXCEPTION 'legs of posted ledger events are immutable';
              END IF;
              RETURN OLD;
            END;
            $$ LANGUAGE plpgsql;
        """))
        bind.execute(text("""
            DROP TRIGGER IF EXISTS ledger_legs_immutable ON ledger_legs;
            CREATE TRIGGER ledger_legs_immutable
            BEFORE UPDATE OR DELETE ON ledger_legs
            FOR EACH ROW EXECUTE FUNCTION prevent_posted_ledger_leg_mutation();
        """))


def downgrade() -> None:
    raise RuntimeError("Phase 2 ledger downgrade is intentionally prohibited")
