"""Create first-class research evidence and claim tables."""
from alembic import op
from ironman.db.base import Base
from ironman.research import evidence  # noqa: F401

revision = "0006_evidence_boundary"
down_revision = "0005_data_fabric"
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    raise RuntimeError("Evidence boundary downgrade is intentionally prohibited")
