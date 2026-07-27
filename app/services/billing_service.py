# app/services/billing_service.py
"""
BillingService — handles all SaaS subscription billing logic.

Payment flow:
  Hostel Admin → selects plan → backend creates Razorpay order using Super Admin keys
  → Frontend opens Razorpay checkout → payment success
  → Backend verifies signature → activates subscription → records payment → generates invoice
"""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.integrations.razorpay import RazorpayClient
from app.models.billing import BillingPayment, Invoice
from app.models.hostel import AdminHostelMapping, Hostel
from app.models.operations import Subscription
from app.models.plan import Plan, PlanFeature, PlanStatus
from app.schemas.billing import (
    AvailablePlanItem,
    BillingHistoryItem,
    BillingHistoryResponse,
    BillingPlanFeature,
    CreateOrderResponse,
    CurrentPlanResponse,
    InvoiceResponse,
    SelectPlanResponse,
    VerifyPaymentResponse,
)

logger = logging.getLogger(__name__)


class BillingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        # Always use Super Admin Razorpay keys for SaaS subscription payments
        self.razorpay = RazorpayClient()

    # ─── Helpers ──────────────────────────────────────────────────────────────

    async def _resolve_hostel(self, admin_user_id: str, hostel_id: Optional[str] = None) -> Hostel:
        """Get the hostel for this admin. Uses hostel_id if given, else the admin's first hostel."""
        if hostel_id:
            result = await self.session.execute(
                select(Hostel).where(Hostel.id == hostel_id)
            )
            hostel = result.scalar_one_or_none()
            if not hostel:
                raise HTTPException(status_code=404, detail="Hostel not found.")
            return hostel

        # Fallback: first mapped hostel for this admin
        result = await self.session.execute(
            select(AdminHostelMapping)
            .where(AdminHostelMapping.admin_id == admin_user_id)
            .order_by(AdminHostelMapping.created_at)
            .limit(1)
        )
        mapping = result.scalar_one_or_none()
        if not mapping:
            raise HTTPException(status_code=404, detail="No hostel found for this admin.")

        hostel_result = await self.session.execute(
            select(Hostel).where(Hostel.id == mapping.hostel_id)
        )
        hostel = hostel_result.scalar_one_or_none()
        if not hostel:
            raise HTTPException(status_code=404, detail="Hostel not found.")
        return hostel

    async def _load_plan_with_features(self, plan_id: str) -> tuple[Plan, list[PlanFeature]]:
        result = await self.session.execute(select(Plan).where(Plan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found.")

        feat_result = await self.session.execute(
            select(PlanFeature)
            .where(PlanFeature.plan_id == plan.id)
            .order_by(PlanFeature.sort_order)
        )
        features = list(feat_result.scalars().all())
        return plan, features

    def _make_invoice_number(self) -> str:
        now = datetime.now(UTC)
        suffix = str(uuid.uuid4())[:8].upper()
        return f"INV-{now.strftime('%Y%m')}-{suffix}"

    def _generate_invoice_html(
        self,
        invoice_number: str,
        hostel_name: str,
        plan_name: str,
        amount: float,
        currency: str,
        issued_at: datetime,
        gateway_payment_id: Optional[str],
        gateway_order_id: Optional[str],
    ) -> str:
        symbol = "₹" if currency == "INR" else currency
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<style>
  body {{ font-family: Arial, sans-serif; color: #333; margin: 40px; }}
  .header {{ border-bottom: 2px solid #4f46e5; padding-bottom: 12px; margin-bottom: 24px; }}
  .logo {{ font-size: 22px; font-weight: bold; color: #4f46e5; }}
  .subtitle {{ font-size: 13px; color: #888; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
  th, td {{ padding: 10px 12px; border: 1px solid #e5e7eb; font-size: 14px; }}
  th {{ background: #f9fafb; text-align: left; }}
  .total-row td {{ font-weight: bold; background: #f9fafb; }}
  .badge {{ display: inline-block; background: #d1fae5; color: #065f46; padding: 3px 10px; border-radius: 999px; font-size: 12px; }}
  .footer {{ margin-top: 32px; font-size: 12px; color: #aaa; text-align: center; }}
</style>
</head>
<body>
<div class="header">
  <div class="logo">StayEase (Levitica Nestora)</div>
  <div class="subtitle">SaaS Platform Invoice</div>
</div>
<p><strong>Invoice Number:</strong> {invoice_number}</p>
<p><strong>Date:</strong> {issued_at.strftime("%d %b %Y")}</p>
<p><strong>Hostel:</strong> {hostel_name}</p>
<p><strong>Payment ID:</strong> {gateway_payment_id or "—"}</p>
<p><strong>Order ID:</strong> {gateway_order_id or "—"}</p>
<table>
  <thead>
    <tr><th>Description</th><th>Amount</th><th>Status</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>{plan_name} — Subscription Plan</td>
      <td>{symbol}{amount:,.2f}</td>
      <td><span class="badge">Paid</span></td>
    </tr>
    <tr class="total-row">
      <td>Total</td>
      <td colspan="2">{symbol}{amount:,.2f} {currency}</td>
    </tr>
  </tbody>
</table>
<div class="footer">Thank you for using StayEase. For support, contact support@leviticanestora.com</div>
</body>
</html>
"""

    # ─── Public Methods ────────────────────────────────────────────────────────

    async def get_available_plans(self) -> list[AvailablePlanItem]:
        """Return all active plans from DB."""
        result = await self.session.execute(
            select(Plan)
            .where(Plan.status == PlanStatus.ACTIVE)
            .order_by(Plan.price_monthly)
        )
        plans = list(result.scalars().all())

        items = []
        for plan in plans:
            feat_result = await self.session.execute(
                select(PlanFeature)
                .where(PlanFeature.plan_id == plan.id)
                .order_by(PlanFeature.sort_order)
            )
            features = list(feat_result.scalars().all())

            items.append(AvailablePlanItem(
                id=str(plan.id),
                name=plan.name,
                description=plan.description,
                duration_days=plan.duration_days,
                duration_type=plan.duration_type.value,
                price=float(plan.price_monthly),
                price_yearly=float(plan.price_yearly),
                features=[
                    BillingPlanFeature(
                        feature_name=f.feature_name,
                        feature_value=f.feature_value,
                        is_included=f.is_included,
                    )
                    for f in features
                ],
                status=plan.status.value,
            ))
        return items

    async def get_current_subscription(
        self, admin_user_id: str, hostel_id: Optional[str] = None
    ) -> CurrentPlanResponse:
        """Return the active subscription for the admin's hostel."""
        hostel = await self._resolve_hostel(admin_user_id, hostel_id)

        sub_result = await self.session.execute(
            select(Subscription)
            .where(
                Subscription.hostel_id == hostel.id,
                Subscription.status == "active",
            )
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        subscription = sub_result.scalar_one_or_none()

        if not subscription:
            return CurrentPlanResponse(has_subscription=False)

        # Resolve plan name
        plan_name = subscription.tier  # fallback to tier field
        plan_id = None
        amount = float(subscription.price_monthly)
        billing_cycle = f"{(subscription.end_date - subscription.start_date).days}-day cycle"

        if subscription.plan_id:
            plan_result = await self.session.execute(
                select(Plan).where(Plan.id == subscription.plan_id)
            )
            plan = plan_result.scalar_one_or_none()
            if plan:
                plan_name = plan.name
                plan_id = str(plan.id)
                billing_cycle = f"{plan.duration_days}-day cycle"
                amount = float(plan.price_monthly)

        # Last billing payment
        last_payment_date = None
        last_payment_status = None
        pay_result = await self.session.execute(
            select(BillingPayment)
            .where(
                BillingPayment.hostel_id == hostel.id,
                BillingPayment.status == "captured",
            )
            .order_by(BillingPayment.paid_at.desc())
            .limit(1)
        )
        last_payment = pay_result.scalar_one_or_none()
        if last_payment and last_payment.paid_at:
            last_payment_date = last_payment.paid_at.strftime("%d %b %Y")
            last_payment_status = last_payment.status

        return CurrentPlanResponse(
            has_subscription=True,
            subscription_id=str(subscription.id),
            plan_id=plan_id,
            plan_name=plan_name,
            billing_cycle=billing_cycle,
            start_date=subscription.start_date.isoformat(),
            expiry_date=subscription.end_date.isoformat(),
            amount=amount,
            status=subscription.status,
            auto_renew=subscription.auto_renew,
            last_payment_date=last_payment_date,
            last_payment_status=last_payment_status,
        )

    async def select_plan(
        self, plan_id: str, admin_user_id: str, hostel_id: Optional[str] = None
    ) -> SelectPlanResponse:
        """Validate plan and return checkout preview details."""
        plan, features = await self._load_plan_with_features(plan_id)

        if plan.status != PlanStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected plan is not currently available.",
            )

        return SelectPlanResponse(
            plan_id=str(plan.id),
            plan_name=plan.name,
            duration_days=plan.duration_days,
            duration_type=plan.duration_type.value,
            amount_due=float(plan.price_monthly),
            currency="INR",
            features=[
                BillingPlanFeature(
                    feature_name=f.feature_name,
                    feature_value=f.feature_value,
                    is_included=f.is_included,
                )
                for f in features
            ],
        )

    async def create_razorpay_order(
        self, plan_id: str, admin_user_id: str, hostel_id: Optional[str] = None
    ) -> CreateOrderResponse:
        """
        Create a Razorpay order using the Super Admin's Razorpay account.
        Records a pending BillingPayment for tracking.
        """
        hostel = await self._resolve_hostel(admin_user_id, hostel_id)
        plan, _ = await self._load_plan_with_features(plan_id)

        if plan.status != PlanStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Selected plan is not currently available.")

        amount = float(plan.price_monthly)
        receipt = f"sub_{str(hostel.id)[:8]}_{str(plan.id)[:8]}"

        # Create Razorpay order using Super Admin keys
        order = self.razorpay.create_order(
            amount=amount,
            receipt=receipt,
            notes={
                "hostel_id": str(hostel.id),
                "hostel_name": hostel.name,
                "plan_id": str(plan.id),
                "plan_name": plan.name,
                "admin_user_id": admin_user_id,
            },
        )

        # Persist a pending BillingPayment record
        billing_payment = BillingPayment(
            hostel_id=str(hostel.id),
            plan_id=str(plan.id),
            admin_user_id=admin_user_id,
            gateway_order_id=order["id"],
            amount=amount,
            currency="INR",
            payment_provider="razorpay",
            status="pending",
        )
        self.session.add(billing_payment)
        await self.session.commit()
        await self.session.refresh(billing_payment)

        logger.info(
            f"[Billing] Created Razorpay order {order['id']} for hostel {hostel.id}, "
            f"plan {plan.name}, amount ₹{amount}"
        )

        return CreateOrderResponse(
            order_id=order["id"],
            amount=amount,
            currency="INR",
            key_id=order.get("key_id") or self.razorpay.key_id or "",
            plan_name=plan.name,
            billing_payment_id=str(billing_payment.id),
        )

    async def verify_and_activate(
        self,
        billing_payment_id: str,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
        admin_user_id: str,
    ) -> VerifyPaymentResponse:
        """
        1. Verify Razorpay signature
        2. Prevent duplicate processing
        3. Activate subscription
        4. Mark BillingPayment as captured
        5. Generate Invoice
        """
        # Load the pending billing payment
        result = await self.session.execute(
            select(BillingPayment).where(BillingPayment.id == billing_payment_id)
        )
        billing_payment = result.scalar_one_or_none()
        if not billing_payment:
            raise HTTPException(status_code=404, detail="Billing payment record not found.")

        # Duplicate prevention
        if billing_payment.status == "captured":
            logger.warning(f"[Billing] Duplicate payment attempt for {billing_payment_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payment already processed.",
            )

        # Verify Razorpay signature using Super Admin keys
        is_valid = self.razorpay.verify_payment_signature(
            order_id=razorpay_order_id,
            payment_id=razorpay_payment_id,
            signature=razorpay_signature,
        )
        if not is_valid:
            billing_payment.status = "failed"
            billing_payment.failure_reason = "Signature verification failed"
            await self.session.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment signature verification failed.",
            )

        # Load plan
        plan_result = await self.session.execute(
            select(Plan).where(Plan.id == billing_payment.plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found.")

        # Load hostel
        hostel_result = await self.session.execute(
            select(Hostel).where(Hostel.id == billing_payment.hostel_id)
        )
        hostel = hostel_result.scalar_one_or_none()

        try:
            # Deactivate any existing active subscriptions for this hostel
            await self.session.execute(
                Subscription.__table__.update()
                .where(
                    Subscription.__table__.c.hostel_id == str(billing_payment.hostel_id),
                    Subscription.__table__.c.status == "active",
                )
                .values(status="superseded")
            )

            # Create new active subscription
            today = date.today()
            end_date = today + timedelta(days=plan.duration_days)
            subscription = Subscription(
                hostel_id=str(billing_payment.hostel_id),
                plan_id=str(plan.id),
                tier=plan.name,
                price_monthly=float(plan.price_monthly),
                start_date=today,
                end_date=end_date,
                status="active",
                auto_renew=plan.auto_renew_allowed,
            )
            self.session.add(subscription)
            await self.session.flush()

            # Update billing payment
            billing_payment.gateway_payment_id = razorpay_payment_id
            billing_payment.gateway_signature = razorpay_signature
            billing_payment.gateway_order_id = razorpay_order_id
            billing_payment.status = "captured"
            billing_payment.paid_at = datetime.now(UTC)
            billing_payment.subscription_id = str(subscription.id)

            # Generate invoice
            invoice_number = self._make_invoice_number()
            issued_at = datetime.now(UTC)
            invoice_html = self._generate_invoice_html(
                invoice_number=invoice_number,
                hostel_name=hostel.name if hostel else str(billing_payment.hostel_id),
                plan_name=plan.name,
                amount=float(billing_payment.amount),
                currency=billing_payment.currency,
                issued_at=issued_at,
                gateway_payment_id=razorpay_payment_id,
                gateway_order_id=razorpay_order_id,
            )
            invoice = Invoice(
                billing_payment_id=str(billing_payment.id),
                invoice_number=invoice_number,
                invoice_html=invoice_html,
                hostel_name=hostel.name if hostel else str(billing_payment.hostel_id),
                plan_name=plan.name,
                amount=float(billing_payment.amount),
                currency=billing_payment.currency,
                issued_at=issued_at,
            )
            self.session.add(invoice)
            await self.session.commit()
            await self.session.refresh(invoice)

            logger.info(
                f"[Billing] Payment captured: {razorpay_payment_id}, "
                f"subscription activated: {subscription.id}, invoice: {invoice_number}"
            )

            return VerifyPaymentResponse(
                success=True,
                message="Payment verified and subscription activated successfully.",
                subscription_id=str(subscription.id),
                invoice_id=str(invoice.id),
                invoice_number=invoice.invoice_number,
            )

        except Exception as e:
            await self.session.rollback()
            logger.error(f"[Billing] Transaction failed during payment activation: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment was received but subscription activation failed. Contact support.",
            )

    async def get_billing_history(
        self, admin_user_id: str, hostel_id: Optional[str] = None
    ) -> BillingHistoryResponse:
        """Return full payment history for the admin's hostel."""
        hostel = await self._resolve_hostel(admin_user_id, hostel_id)

        result = await self.session.execute(
            select(BillingPayment)
            .where(BillingPayment.hostel_id == hostel.id)
            .order_by(BillingPayment.created_at.desc())
        )
        payments = list(result.scalars().all())

        items = []
        for p in payments:
            plan_name = None
            if p.plan_id:
                plan_res = await self.session.execute(
                    select(Plan).where(Plan.id == p.plan_id)
                )
                plan = plan_res.scalar_one_or_none()
                if plan:
                    plan_name = plan.name

            invoice_id = None
            invoice_number = None
            invoice_url = None
            if p.invoice:
                invoice_id = str(p.invoice.id)
                invoice_number = p.invoice.invoice_number
                invoice_url = p.invoice.invoice_url

            items.append(BillingHistoryItem(
                payment_id=str(p.id),
                order_id=p.gateway_order_id,
                razorpay_payment_id=p.gateway_payment_id,
                plan_name=plan_name,
                amount=float(p.amount),
                currency=p.currency,
                payment_provider=p.payment_provider,
                status=p.status,
                paid_at=p.paid_at.strftime("%d %b %Y") if p.paid_at else None,
                invoice_id=invoice_id,
                invoice_number=invoice_number,
                invoice_url=invoice_url,
            ))

        return BillingHistoryResponse(items=items, total=len(items))

    async def get_invoice(self, invoice_id: str, admin_user_id: str) -> InvoiceResponse:
        """Return invoice details. Validates that the invoice belongs to the admin's hostel."""
        result = await self.session.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        # Authorization check — ensure admin owns this invoice
        pay_result = await self.session.execute(
            select(BillingPayment)
            .where(BillingPayment.id == invoice.billing_payment_id)
        )
        payment = pay_result.scalar_one_or_none()
        if not payment:
            raise HTTPException(status_code=404, detail="Billing payment not found.")

        # Verify admin is mapped to the hostel in this payment
        mapping_result = await self.session.execute(
            select(AdminHostelMapping).where(
                AdminHostelMapping.admin_id == admin_user_id,
                AdminHostelMapping.hostel_id == payment.hostel_id,
            )
        )
        if not mapping_result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Access denied.")

        return InvoiceResponse(
            invoice_id=str(invoice.id),
            invoice_number=invoice.invoice_number,
            hostel_name=invoice.hostel_name,
            plan_name=invoice.plan_name,
            amount=float(invoice.amount),
            currency=invoice.currency,
            issued_at=invoice.issued_at.isoformat(),
            invoice_html=invoice.invoice_html,
            invoice_url=invoice.invoice_url,
        )
