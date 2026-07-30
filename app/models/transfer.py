from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.hostel import Hostel
    from app.models.room import Bed, Room
    from app.models.student import Student
    from app.models.user import User


class TransferType(str, enum.Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"


class TransferStatus(str, enum.Enum):
    PENDING = "pending"
    PENDING_OLD_ADMIN = "pending_old_admin"
    PENDING_NEW_ADMIN = "pending_new_admin"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class StudentTransferRequest(BaseModel):
    __tablename__ = "student_transfer_requests"

    student_id: Mapped[str] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    from_hostel_id: Mapped[str] = mapped_column(
        ForeignKey("hostels.id", ondelete="CASCADE"), index=True
    )
    to_hostel_id: Mapped[str] = mapped_column(
        ForeignKey("hostels.id", ondelete="CASCADE"), index=True
    )
    to_room_id: Mapped[str | None] = mapped_column(
        ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True, index=True
    )
    to_bed_id: Mapped[str | None] = mapped_column(
        ForeignKey("beds.id", ondelete="SET NULL"), nullable=True, index=True
    )
    transfer_type: Mapped[TransferType] = mapped_column(
        Enum(TransferType), index=True
    )
    status: Mapped[TransferStatus] = mapped_column(
        Enum(TransferStatus), default=TransferStatus.PENDING, index=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    old_admin_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    new_admin_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    student: Mapped[Student] = relationship("Student")
    user: Mapped[User] = relationship("User")
    from_hostel: Mapped[Hostel] = relationship("Hostel", foreign_keys=[from_hostel_id])
    to_hostel: Mapped[Hostel] = relationship("Hostel", foreign_keys=[to_hostel_id])
    to_room: Mapped[Room | None] = relationship("Room", foreign_keys=[to_room_id])
    to_bed: Mapped[Bed | None] = relationship("Bed", foreign_keys=[to_bed_id])
