"""revert razorpay route split payments

Revision ID: 7a4ea2e1a94c
Revises: 48a57f047ee2
Create Date: 2026-07-29 12:37:18.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a4ea2e1a94c'
down_revision: Union[str, Sequence[str], None] = '48a57f047ee2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop Route columns
    op.drop_column('hostel_payment_configs', 'platform_fee_percentage')
    op.drop_column('hostel_payment_configs', 'razorpay_linked_account_id')
    
    # 2. Restore non-nullable constraints on direct integration fields
    # Note: We must ensure no null values exist before running this in production.
    # However, since this was just added in dev and not populated, we can safely enforce it.
    op.alter_column('hostel_payment_configs', 'razorpay_key_id',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)
    op.alter_column('hostel_payment_configs', 'razorpay_key_secret_encrypted',
               existing_type=sa.TEXT(),
               nullable=False)


def downgrade() -> None:
    op.alter_column('hostel_payment_configs', 'razorpay_key_secret_encrypted',
               existing_type=sa.TEXT(),
               nullable=True)
    op.alter_column('hostel_payment_configs', 'razorpay_key_id',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)
    op.add_column('hostel_payment_configs', sa.Column('razorpay_linked_account_id', sa.String(length=100), nullable=True))
    op.add_column('hostel_payment_configs', sa.Column('platform_fee_percentage', sa.Float(), nullable=False, server_default='0.0'))
