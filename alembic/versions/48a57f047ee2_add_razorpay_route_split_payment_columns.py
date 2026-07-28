"""add razorpay route split payment columns

Revision ID: 48a57f047ee2
Revises: f1a2b3c4d5e6
Create Date: 2026-07-28 15:37:43.496215

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48a57f047ee2'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('hostel_payment_configs', sa.Column('razorpay_linked_account_id', sa.String(length=100), nullable=True))
    op.add_column('hostel_payment_configs', sa.Column('platform_fee_percentage', sa.Float(), nullable=False, server_default='0.0'))
    op.alter_column('hostel_payment_configs', 'razorpay_key_id',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)
    op.alter_column('hostel_payment_configs', 'razorpay_key_secret_encrypted',
               existing_type=sa.TEXT(),
               nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('hostel_payment_configs', 'razorpay_key_secret_encrypted',
               existing_type=sa.TEXT(),
               nullable=False)
    op.alter_column('hostel_payment_configs', 'razorpay_key_id',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)
    op.drop_column('hostel_payment_configs', 'platform_fee_percentage')
    op.drop_column('hostel_payment_configs', 'razorpay_linked_account_id')
