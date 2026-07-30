"""add HOURLY uppercase to bookingmode enum

Revision ID: 8d3f5a9b1c2e
Revises: 7c26ae672a37
Create Date: 2026-07-30 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '8d3f5a9b1c2e'
down_revision: Union[str, Sequence[str], None] = '7c26ae672a37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add HOURLY (uppercase) to bookingmode enum — SQLAlchemy sends enum names not values."""
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE bookingmode ADD VALUE IF NOT EXISTS 'HOURLY'")


def downgrade() -> None:
    """PostgreSQL does not support removing enum values — no-op."""
    pass
