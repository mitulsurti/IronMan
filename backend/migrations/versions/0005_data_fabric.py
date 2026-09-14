"""Create provider-independent observation tables."""
from alembic import op
from ironman.db.base import Base
from ironman.data_fabric import models  # noqa: F401

revision = "0005_data_fabric"
down_revision = "0004_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    raise RuntimeError("Data-fabric downgrade is intentionally prohibited")
