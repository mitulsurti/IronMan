"""Create Phase 3 capital deployment intelligence tables."""
from alembic import op
from ironman.db.base import Base
from ironman.intelligence import models  # noqa: F401

revision = "0004_intelligence"
down_revision = "0003_snapshot_boundary"
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    raise RuntimeError("Phase 3 intelligence downgrade is intentionally prohibited")
