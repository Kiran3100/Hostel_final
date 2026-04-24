from datetime import datetime

from pydantic import BaseModel, Field, field_validator



class ApproveBookingRequest(BaseModel):
    bed_id: str


class RejectBookingRequest(BaseModel):
    reason: str | None = None


class SupervisorCreateRequest(BaseModel):
    email: str
    phone: str
    full_name: str
    password: str


class DirectStudentAddRequest(BaseModel):
    full_name: str
    email: str
    phone: str
    password: str
    room_id: str
    bed_id: str
    check_in_date: str
    check_out_date: str
    booking_mode: str = "monthly"


class DirectStudentAddResponse(BaseModel):
    student_id: str
    student_number: str
    user_id: str
    booking_id: str
    booking_number: str
    full_name: str
    email: str
    room_id: str
    bed_id: str
    check_in_date: str

    class Config:
        from_attributes = True


class SupervisorResponse(BaseModel):
    id: str
    email: str
    phone: str
    full_name: str
    role: str
    is_active: bool
    is_email_verified: bool
    is_phone_verified: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid(cls, v):
        return str(v)

    @field_validator("role", mode="before")
    @classmethod
    def coerce_role(cls, v):
        return v.value if hasattr(v, "value") else str(v)

    class Config:
        from_attributes = True


class AdminDashboardResponse(BaseModel):
    hostels: int
    rooms: int
    students: int
    complaints: int
    maintenance_items: int
    payments: int


class SupervisorUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    phone: str | None = Field(default=None, min_length=8, max_length=30)
    email: str | None = Field(default=None, min_length=5, max_length=255)
    is_active: bool | None = None
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is not None:
            if "@" not in v or "." not in v:
                raise ValueError("Invalid email format")
        return v