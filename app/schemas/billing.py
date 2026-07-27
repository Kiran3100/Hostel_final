# app/schemas/billing.py
"""
Pydantic schemas for the Billing / Plans module (Hostel Admin SaaS subscriptions).
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ─── Available Plans ──────────────────────────────────────────────────────────

class BillingPlanFeature(BaseModel):
    feature_name: str
    feature_value: Optional[str] = None
    is_included: bool = True


class AvailablePlanItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    duration_days: int
    duration_type: str
    price: float            # price_monthly from Plan model
    price_yearly: float
    features: List[BillingPlanFeature] = []
    status: str

    model_config = {"from_attributes": True}


# ─── Current Subscription ─────────────────────────────────────────────────────

class CurrentPlanResponse(BaseModel):
    """Active subscription details for the hostel."""
    has_subscription: bool
    subscription_id: Optional[str] = None
    plan_id: Optional[str] = None
    plan_name: Optional[str] = None
    billing_cycle: Optional[str] = None   # e.g. "30-day cycle"
    start_date: Optional[str] = None
    expiry_date: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    auto_renew: bool = False
    # Last payment info
    last_payment_date: Optional[str] = None
    last_payment_status: Optional[str] = None


# ─── Plan Selection / Checkout ────────────────────────────────────────────────

class SelectPlanRequest(BaseModel):
    plan_id: str = Field(..., description="ID of the plan to purchase")
    hostel_id: Optional[str] = Field(None, description="Hostel ID (for multi-hostel admins)")


class SelectPlanResponse(BaseModel):
    """Checkout preview — shown before payment."""
    plan_id: str
    plan_name: str
    duration_days: int
    duration_type: str
    amount_due: float
    currency: str = "INR"
    features: List[BillingPlanFeature] = []


# ─── Razorpay Order ───────────────────────────────────────────────────────────

class CreateOrderRequest(BaseModel):
    plan_id: str = Field(..., description="ID of the plan being purchased")
    hostel_id: Optional[str] = Field(None, description="Hostel ID (multi-hostel admins)")


class CreateOrderResponse(BaseModel):
    """Returned to the frontend to open Razorpay checkout."""
    order_id: str           # Razorpay order ID
    amount: float           # Amount in INR
    currency: str = "INR"
    key_id: str             # Super Admin Razorpay Key ID (for frontend checkout init)
    plan_name: str
    billing_payment_id: str # Our internal record ID


# ─── Payment Verification ─────────────────────────────────────────────────────

class VerifyPaymentRequest(BaseModel):
    billing_payment_id: str = Field(..., description="Our internal BillingPayment ID")
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class VerifyPaymentResponse(BaseModel):
    success: bool
    message: str
    subscription_id: Optional[str] = None
    invoice_id: Optional[str] = None
    invoice_number: Optional[str] = None


# ─── Billing History ──────────────────────────────────────────────────────────

class BillingHistoryItem(BaseModel):
    payment_id: str
    order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    plan_name: Optional[str] = None
    amount: float
    currency: str = "INR"
    payment_provider: str
    status: str
    paid_at: Optional[str] = None
    invoice_id: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_url: Optional[str] = None


class BillingHistoryResponse(BaseModel):
    items: List[BillingHistoryItem]
    total: int


# ─── Invoice ──────────────────────────────────────────────────────────────────

class InvoiceResponse(BaseModel):
    invoice_id: str
    invoice_number: str
    hostel_name: str
    plan_name: str
    amount: float
    currency: str
    issued_at: str
    invoice_html: Optional[str] = None
    invoice_url: Optional[str] = None
