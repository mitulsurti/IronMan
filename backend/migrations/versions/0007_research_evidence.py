"""Create first-class research evidence tables."""
from alembic import op
from ironman.db.base import Base
from ironman.research import evidence  # noqa: F401

revision = "0007_research_evidence"
down_revision = "0006_evidence_boundary"
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    raise RuntimeError("Research evidence downgrade is intentionally prohibited")
