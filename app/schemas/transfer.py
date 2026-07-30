from datetime import datetime
from pydantic import BaseModel, Field
from app.models.transfer import TransferStatus, TransferType
from app.schemas.base import TimestampedResponse


class StudentTransferCreateRequest(BaseModel):
    to_hostel_id: str = Field(..., description="ID of the target hostel to move to")
    to_room_id: str | None = Field(default=None, description="Optional target room ID")
    to_bed_id: str | None = Field(default=None, description="Optional target bed ID")
    reason: str | None = Field(default=None, description="Reason for transfer request")


class StudentTransferActionRequest(BaseModel):
    action: str = Field(..., description="'approve' or 'reject'")
    to_room_id: str | None = Field(default=None, description="Target room ID (required when new admin approves)")
    to_bed_id: str | None = Field(default=None, description="Target bed ID (required when new admin approves)")
    note: str | None = Field(default=None, description="Optional note or rejection reason")


class StudentTransferResponse(TimestampedResponse):
    # id, created_at, updated_at inherited from TimestampedResponse
    # from_attributes=True inherited from APIModel via TimestampedResponse
    student_id: str
    user_id: str
    from_hostel_id: str
    to_hostel_id: str
    to_room_id: str | None = None
    to_bed_id: str | None = None
    transfer_type: TransferType
    status: TransferStatus
    reason: str | None = None
    rejection_reason: str | None = None
    old_admin_approved_at: datetime | None = None
    new_admin_approved_at: datetime | None = None
    completed_at: datetime | None = None

    # UI-convenience fields — populated at service layer
    student_name: str | None = None
    from_hostel_name: str | None = None
    to_hostel_name: str | None = None
    to_room_number: str | None = None
    to_bed_number: str | None = None
