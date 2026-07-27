"""add billing_payments and invoices tables

Revision ID: f1a2b3c4d5e6
Revises: e5f6a7b8c9d0
Create Date: 2026-07-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # billing_payments table
    op.create_table(
        'billing_payments',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('hostel_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('hostels.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('plan_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('plans.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('subscription_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('admin_user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('gateway_order_id', sa.String(120), nullable=True, unique=True, index=True),
        sa.Column('gateway_payment_id', sa.String(120), nullable=True, index=True),
        sa.Column('gateway_signature', sa.String(512), nullable=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, server_default='INR'),
        sa.Column('payment_provider', sa.String(50), nullable=False, server_default='razorpay'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending', index=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_reason', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('billing_payment_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('billing_payments.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('invoice_number', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('invoice_html', sa.Text(), nullable=True),
        sa.Column('invoice_url', sa.String(500), nullable=True),
        sa.Column('hostel_name', sa.String(255), nullable=False),
        sa.Column('plan_name', sa.String(100), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, server_default='INR'),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('invoices')
    op.drop_table('billing_payments')
