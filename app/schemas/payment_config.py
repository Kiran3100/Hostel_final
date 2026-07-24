from pydantic import BaseModel, ConfigDict, Field

class HostelPaymentConfigBase(BaseModel):
    razorpay_key_id: str = Field(..., description="Razorpay Key ID (rzp_live_... or rzp_test_...)")
    is_active: bool = Field(default=True, description="Whether online payments are enabled for this hostel")

class HostelPaymentConfigCreate(HostelPaymentConfigBase):
    razorpay_key_secret: str = Field(..., description="Razorpay Key Secret")
    razorpay_webhook_secret: str | None = Field(None, description="Optional Webhook Secret")

class HostelPaymentConfigUpdate(HostelPaymentConfigBase):
    razorpay_key_secret: str | None = Field(None, description="Razorpay Key Secret (leave null to keep existing)")
    razorpay_webhook_secret: str | None = Field(None, description="Optional Webhook Secret")

class HostelPaymentConfigResponse(HostelPaymentConfigBase):
    hostel_id: str
    is_configured: bool = Field(default=True, description="True if a configuration exists")
    
    model_config = ConfigDict(from_attributes=True)
