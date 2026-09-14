"""Create the empty foundation migration."""

from typing import Sequence, Union

revision: str = "0001_foundation"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No product tables are created in Phase 1."""


def downgrade() -> None:
    """No product tables are created in Phase 1."""
