# FILE: app/schemas/maintenance.py

from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.schemas.base import APIModel
from typing import Optional

class MaintenanceCreateRequest(BaseModel):
    room_id: str | None = None
    category: str = Field(min_length=2, max_length=100)
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=5)
    priority: str = Field(min_length=2, max_length=50)
    estimated_cost: float | None = None


class MaintenanceUpdateRequest(BaseModel):
    status: str | None = Field(default=None, max_length=50)
    estimated_cost: float | None = None
    actual_cost: float | None = None
    assigned_vendor_name: str | None = None
    vendor_contact: str | None = None
    requires_admin_approval: bool | None = None
    
    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        """Validate status - service layer will check against valid values"""
        if v is None:
            return v
        return v.strip() if isinstance(v, str) else v


class MaintenanceResponse(APIModel):
    id: str
    hostel_id: str
    room_id: str | None = None
    reported_by: str
    category: str
    title: str
    description: str
    priority: str
    status: str
    estimated_cost: float | None = None
    actual_cost: float | None = None
    assigned_vendor_name: str | None = None
    vendor_contact: str | None = None
    requires_admin_approval: bool
    approved_by: str | None = None
    created_at: datetime
    updated_at: datetime