"""add hostel payment configs

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    op.create_table('hostel_payment_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('hostel_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('razorpay_key_id', sa.String(length=120), nullable=False),
        sa.Column('razorpay_key_secret_encrypted', sa.Text(), nullable=False),
        sa.Column('razorpay_webhook_secret_encrypted', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['hostel_id'], ['hostels.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_hostel_payment_configs_hostel_id'), 'hostel_payment_configs', ['hostel_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_hostel_payment_configs_hostel_id'), table_name='hostel_payment_configs')
    op.drop_table('hostel_payment_configs')
