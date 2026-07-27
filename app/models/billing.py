"""
Billing models — SaaS subscription payment tracking.

BillingPayment: records each Razorpay payment made by a hostel admin for a subscription plan.
Invoice: stores invoice metadata and PDF content for each payment.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.hostel import Hostel
    from app.models.plan import Plan
    from app.models.operations import Subscription


class BillingPayment(BaseModel):
    """
    Records a SaaS subscription payment made by a Hostel Admin.
    Payments always go to the Super Admin's Razorpay account.
    """
    __tablename__ = "billing_payments"

    hostel_id: Mapped[str] = mapped_column(
        ForeignKey("hostels.id", ondelete="CASCADE"), index=True, nullable=False
    )
    plan_id: Mapped[str | None] = mapped_column(
        ForeignKey("plans.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subscription_id: Mapped[str | None] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    admin_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Razorpay fields
    gateway_order_id: Mapped[str | None] = mapped_column(
        String(120), nullable=True, unique=True, index=True
    )
    gateway_payment_id: Mapped[str | None] = mapped_column(
        String(120), nullable=True, index=True
    )
    gateway_signature: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Payment details
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    payment_provider: Mapped[str] = mapped_column(String(50), default="razorpay", nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    # Status values: pending | captured | failed | refunded

    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    hostel: Mapped["Hostel"] = relationship("Hostel")
    plan: Mapped["Plan | None"] = relationship("Plan")
    subscription: Mapped["Subscription | None"] = relationship("Subscription")
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice", back_populates="billing_payment", uselist=False, cascade="all, delete-orphan"
    )


class Invoice(BaseModel):
    """Invoice for a successful SaaS subscription payment."""
    __tablename__ = "invoices"

    billing_payment_id: Mapped[str] = mapped_column(
        ForeignKey("billing_payments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    invoice_number: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    # Stored as HTML string for PDF generation; also used as the downloadable content
    invoice_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    # URL if stored on cloud storage (S3/Cloudinary); nullable if generated on the fly
    invoice_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Snapshot fields so invoice remains correct even if plan/hostel data changes
    hostel_name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    billing_payment: Mapped["BillingPayment"] = relationship(
        "BillingPayment", back_populates="invoice"
    )
