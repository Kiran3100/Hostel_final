from pydantic import BaseModel, ConfigDict, Field


class HostelPaymentConfigBase(BaseModel):
    is_active: bool = Field(default=True, description="Whether online payments are enabled for this hostel")


class HostelPaymentConfigCreate(HostelPaymentConfigBase):
    razorpay_key_id: str = Field(..., description="Razorpay Key ID (rzp_live_... or rzp_test_...)")
    razorpay_key_secret: str = Field(..., description="Razorpay Key Secret")
    razorpay_webhook_secret: str | None = Field(None, description="Optional Webhook Secret")


class HostelPaymentConfigUpdate(HostelPaymentConfigBase):
    razorpay_key_id: str | None = Field(None, description="Razorpay Key ID (rzp_live_... or rzp_test_...)")
    razorpay_key_secret: str | None = Field(None, description="Razorpay Key Secret (leave null to keep existing)")
    razorpay_webhook_secret: str | None = Field(None, description="Optional Webhook Secret")
    # Razorpay Route fields (Option 3 — Split Payments)
    razorpay_linked_account_id: str | None = Field(None, description="Razorpay Route Linked Account ID (e.g. acc_xyz123). When set, payments are split automatically.")
    platform_fee_percentage: float | None = Field(None, ge=0, le=100, description="Platform fee % kept by Super Admin (0–100). Rest is transferred to the hostel's linked account.")


class HostelPaymentConfigResponse(HostelPaymentConfigBase):
    hostel_id: str
    razorpay_key_id: str | None = Field(None, description="Razorpay Key ID")
    razorpay_linked_account_id: str | None = Field(None, description="Razorpay Route Linked Account ID (if using split payments)")
    platform_fee_percentage: float = Field(0.0, description="Platform fee percentage")
    is_configured: bool = Field(default=True, description="True if a configuration exists")
    payment_mode: str = Field("direct", description="'direct' = hostel's own keys, 'route' = Razorpay Route split payments")

    model_config = ConfigDict(from_attributes=True)
