from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional


from app.schemas.base import TimestampedResponse


class SuperAdminDashboardResponse(BaseModel):
    # Spec metrics
    total_hostels: int
    pending_approval_count: int
    active_hostels: int
    total_students: int
    total_revenue_month: float
    # Backward-compatible fields used by existing frontend
    hostels: int
    admins: int
    subscriptions: int


class SuperAdminHostelCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=10)
    hostel_type: str
    address_line1: str = Field(min_length=2, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=2, max_length=120)
    state: str = Field(min_length=2, max_length=120)
    country: str = Field(default="India", min_length=2, max_length=120)
    pincode: str = Field(min_length=3, max_length=20)
    latitude: float
    longitude: float
    phone: str = Field(min_length=5, max_length=30)
    email: str = Field(min_length=5, max_length=255)
    website: str | None = Field(default=None, max_length=255)
    is_featured: bool = False
    is_public: bool = True
    rules_and_regulations: str | None = None

    from pydantic import model_validator

    @model_validator(mode="before")
    @classmethod
    def _coerce_empty_strings(cls, values: dict) -> dict:
        for field in ("website", "address_line2", "rules_and_regulations"):
            if values.get(field) == "":
                values[field] = None
        return values


class SuperAdminHostelResponse(TimestampedResponse):
    name: str
    slug: str
    description: str
    hostel_type: str
    status: str
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    country: str
    pincode: str
    latitude: float
    longitude: float
    phone: str
    email: str
    website: str | None = None
    is_featured: bool
    is_public: bool
    rules_and_regulations: str | None = None


class SuperAdminAdminCreateRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    phone: str = Field(min_length=5, max_length=30)
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=255)


class SuperAdminAdminResponse(TimestampedResponse):
    email: str
    phone: str
    full_name: str
    role: str
    is_active: bool
    is_email_verified: bool
    is_phone_verified: bool


class AssignHostelsRequest(BaseModel):
    hostel_ids: list[str] = Field(default_factory=list, min_length=1)


class AssignHostelRequest(BaseModel):
    hostel_id: str
    is_primary: bool = False


class SuperAdminHostelListResponse(BaseModel):
    items: list[SuperAdminHostelResponse]
    total: int
    page: int
    per_page: int


class SuperAdminHostelRejectRequest(BaseModel):
    reason: str


class SuperAdminSubscriptionResponse(TimestampedResponse):
    hostel_id: str
    tier: str
    price_monthly: float
    start_date: date
    end_date: date
    status: str
    auto_renew: bool

# Add to app/schemas/super_admin.py

class SuperAdminSubscriptionCreateRequest(BaseModel):
    """Create a new subscription for a hostel."""
    hostel_id: str = Field(..., description="UUID of the hostel")
    tier: str = Field(..., min_length=2, max_length=50, description="basic, standard, professional, enterprise")
    price_monthly: float = Field(..., ge=0, description="Monthly price in INR")
    start_date: date = Field(..., description="Subscription start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="Subscription end date (YYYY-MM-DD)")
    auto_renew: bool = Field(default=True, description="Auto-renew subscription")
    status: str = Field(default="active", pattern="^(active|expired|cancelled)$", description="Subscription status")

    @model_validator(mode="after")
    def validate_dates(self) -> "SuperAdminSubscriptionCreateRequest":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class SuperAdminSubscriptionUpdateRequest(BaseModel):
    """Update an existing subscription."""
    tier: str | None = Field(default=None, min_length=2, max_length=50)
    price_monthly: float | None = Field(default=None, ge=0)
    start_date: date | None = None
    end_date: date | None = None
    auto_renew: bool | None = None
    status: str | None = Field(default=None, pattern="^(active|expired|cancelled)$")

    @model_validator(mode="after")
    def validate_dates(self) -> "SuperAdminSubscriptionUpdateRequest":
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class SuperAdminSubscriptionDetailResponse(TimestampedResponse):
    """Detailed subscription response."""
    hostel_id: str
    hostel_name: str | None = None
    tier: str
    price_monthly: float
    start_date: date
    end_date: date
    status: str
    auto_renew: bool
    days_remaining: int | None = None