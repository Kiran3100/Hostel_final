from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError,  EmailStr
from typing import Optional
from email_validator import validate_email, EmailNotValidError
import re


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


# Update the SuperAdminAdminCreateRequest class in app/schemas/super_admin.py

class SuperAdminHostelCreateRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    phone: str = Field(min_length=10, max_length=15)
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v or "@" not in v or "." not in v:
            raise ValueError("Invalid email format")
        # Basic email pattern check
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v.lower().strip()
    
    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate Indian phone number format."""
        if not v:
            raise ValueError("Phone number is required")
        
        # Strip whitespace
        v = v.strip()
        
        # Remove common prefixes and special characters for validation
        # But keep the original for storage? Let's clean it
        cleaned = re.sub(r'[^0-9]', '', v)
        
        # Check length - Indian phone numbers should be exactly 10 digits
        # after removing country code
        if len(cleaned) == 10:
            # Must start with 6,7,8,9 for Indian numbers
            if cleaned[0] not in ['6', '7', '8', '9']:
                raise ValueError("Indian phone number must start with 6, 7, 8, or 9")
            return cleaned
        
        # Handle +91 prefix (11 digits total after removing +91)
        elif len(cleaned) == 12 and cleaned.startswith('91'):
            number_part = cleaned[2:]  # Remove 91
            if len(number_part) == 10 and number_part[0] in ['6', '7', '8', '9']:
                return number_part
        
        # Handle numbers starting with 0
        elif len(cleaned) == 11 and cleaned.startswith('0'):
            number_part = cleaned[1:]  # Remove leading 0
            if len(number_part) == 10 and number_part[0] in ['6', '7', '8', '9']:
                return number_part
        
        # Handle numbers with +91 and spaces/dashes
        elif len(cleaned) > 10:
            # Extract the last 10 digits if they look like a phone number
            if len(cleaned) >= 10:
                last_10 = cleaned[-10:]
                if last_10[0] in ['6', '7', '8', '9']:
                    return last_10
        
        # If we get here, the number is invalid
        raise ValueError(
            "Invalid phone number. Indian phone numbers must be 10 digits "
            "starting with 6, 7, 8, or 9. Format examples: 9876543210, "
            "+919876543210, 09876543210, +91-9876543210"
        )
    
    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 128:
            raise ValueError("Password is too long (max 128 characters)")
        
        # Password strength requirements
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'[0-9]', v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        
        return v
    
    @field_validator("full_name", mode="before")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters")
        if len(v) > 255:
            raise ValueError("Full name is too long")
        return v.strip()


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
    phone: str = Field(min_length=10, max_length=15)  # Allow 10-15 chars after cleaning
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v or "@" not in v or "." not in v:
            raise ValueError("Invalid email format")
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        # Store normalized lowercase version
        return v.lower().strip()
    
    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Phone number is required")
        
        # Strip whitespace
        v = v.strip()
        
        # Remove common prefixes and special characters for validation
        # Keep + for international format detection
        cleaned = re.sub(r'[^0-9+]', '', v)
        
        # Handle +91 prefix - keep it for storage but clean for validation
        has_plus = cleaned.startswith('+')
        if has_plus:
            # Remove + for digit counting
            digits_only = cleaned[1:] if len(cleaned) > 1 else cleaned
        else:
            digits_only = cleaned
        
        # Count only digits
        digit_count = len(re.sub(r'[^0-9]', '', digits_only))
        
        # Validate length
        if digit_count < 10:
            raise ValueError("Phone number must have at least 10 digits")
        if digit_count > 15:
            raise ValueError("Phone number must have at most 15 digits")
        
        # For Indian numbers (10 digits), check that first digit is 6-9
        if digit_count == 10:
            first_digit = digits_only[0] if digits_only else ''
            if first_digit not in ['6', '7', '8', '9']:
                raise ValueError("Indian phone number must start with 6, 7, 8, or 9")
        
        # Store a standardized format (just digits for consistency)
        # This ensures uniqueness checks work properly
        standardized = re.sub(r'[^0-9]', '', cleaned)
        # If it was 10 digits, use as is; if it had +91, keep it as 10 digits only
        if len(standardized) == 12 and standardized.startswith('91'):
            standardized = standardized[2:]  # Remove 91 prefix
        
        # Final validation: should be 10-15 digits now
        if len(standardized) < 10 or len(standardized) > 15:
            raise ValueError(f"Invalid phone number format after cleaning: {standardized}")
        
        return standardized
    
    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        # Password strength requirements
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'[0-9]', v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        
        return v
    
    @field_validator("full_name", mode="before")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters")
        if len(v) > 255:
            raise ValueError("Full name is too long")
        return v.strip()


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
    
class ChangePasswordRequest(BaseModel):
    """Request to change super admin password"""
    old_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_passwords_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("New passwords do not match")
        return self
    
class SuperAdminProfileResponse(TimestampedResponse):
    email: str
    phone: str
    full_name: str
    role: str
    profile_picture_url: str | None = None
    is_email_verified: bool
    is_phone_verified: bool

class SuperAdminProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    phone: str | None = Field(default=None, min_length=8, max_length=30)
    profile_picture_url: str | None = None
    
class ValidatePasswordRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)

class PasswordValidationResponse(BaseModel):
    is_valid: bool
    errors: list[str] = []