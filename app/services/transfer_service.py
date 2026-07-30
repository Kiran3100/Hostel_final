import uuid
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import (
    BedStay,
    BedStayStatus,
    Booking,
    BookingMode,
    BookingStatus,
)
from app.models.hostel import AdminHostelMapping, Hostel
from app.models.payment import Payment, PaymentStatus
from app.models.room import Bed, BedStatus, Room
from app.models.student import Student, StudentStatus
from app.models.transfer import StudentTransferRequest, TransferStatus, TransferType
from app.repositories.transfer_repository import TransferRepository
from app.schemas.transfer import (
    StudentTransferActionRequest,
    StudentTransferCreateRequest,
    StudentTransferResponse,
)


class TransferService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = TransferRepository(session)

    async def _get_admin_hostels(self, admin_id: str) -> set[str]:
        result = await self.session.execute(
            select(AdminHostelMapping.hostel_id).where(
                AdminHostelMapping.admin_id == admin_id
            )
        )
        return set(result.scalars().all())

    async def _has_pending_dues(self, student_id: str) -> bool:
        result = await self.session.execute(
            select(Payment.id).where(
                Payment.student_id == student_id,
                Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.FAILED]),
            )
        )
        return result.scalar_one_or_none() is not None

    async def request_transfer(
        self, *, user_id: str, payload: StudentTransferCreateRequest
    ) -> StudentTransferResponse:
        # 1. Fetch active student profile
        student_res = await self.session.execute(
            select(Student).where(
                Student.user_id == user_id,
                Student.status == StudentStatus.ACTIVE,
            )
        )
        student = student_res.scalar_one_or_none()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active student profile not found.",
            )

        # 2. Check pending dues
        if await self._has_pending_dues(str(student.id)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot request transfer while you have unpaid dues/pending payments. Please clear your dues first.",
            )

        # 3. Check target hostel
        if payload.to_hostel_id == str(student.hostel_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target hostel must be different from your current hostel.",
            )

        to_hostel_res = await self.session.execute(
            select(Hostel).where(Hostel.id == payload.to_hostel_id)
        )
        to_hostel = to_hostel_res.scalar_one_or_none()
        if not to_hostel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target hostel not found.",
            )

        # 4. Check active pending request
        active_req = await self.repository.get_active_transfer_for_student(str(student.id))
        if active_req:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have an active transfer request in progress.",
            )

        # 5. Check if same admin (Internal) vs different admin (External)
        from_admins_res = await self.session.execute(
            select(AdminHostelMapping.admin_id).where(
                AdminHostelMapping.hostel_id == student.hostel_id
            )
        )
        from_admin_ids = set(from_admins_res.scalars().all())

        to_admins_res = await self.session.execute(
            select(AdminHostelMapping.admin_id).where(
                AdminHostelMapping.hostel_id == payload.to_hostel_id
            )
        )
        to_admin_ids = set(to_admins_res.scalars().all())

        if from_admin_ids.intersection(to_admin_ids):
            transfer_type = TransferType.INTERNAL
            initial_status = TransferStatus.PENDING
        else:
            transfer_type = TransferType.EXTERNAL
            initial_status = TransferStatus.PENDING_OLD_ADMIN

        transfer_req = StudentTransferRequest(
            student_id=str(student.id),
            user_id=user_id,
            from_hostel_id=str(student.hostel_id),
            to_hostel_id=payload.to_hostel_id,
            to_room_id=payload.to_room_id,
            to_bed_id=payload.to_bed_id,
            transfer_type=transfer_type,
            status=initial_status,
            reason=payload.reason,
        )

        transfer_req = await self.repository.create_transfer_request(transfer_req)
        await self.session.commit()

        return await self._to_response(transfer_req)

    async def process_transfer_action(
        self, *, admin_id: str, transfer_id: str, payload: StudentTransferActionRequest
    ) -> StudentTransferResponse:
        req = await self.repository.get_transfer_by_id(transfer_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer request not found.",
            )

        admin_hostels = await self._get_admin_hostels(admin_id)

        action = payload.action.lower().strip()

        if action == "reject":
            if req.from_hostel_id not in admin_hostels and req.to_hostel_id not in admin_hostels:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to manage this transfer request.",
                )
            req.status = TransferStatus.REJECTED
            req.rejection_reason = payload.note
            await self.session.commit()
            return await self._to_response(req)

        elif action == "approve":
            target_room_id = payload.to_room_id or req.to_room_id
            target_bed_id = payload.to_bed_id or req.to_bed_id

            if req.transfer_type == TransferType.INTERNAL:
                # Internal transfer: same admin
                if req.from_hostel_id not in admin_hostels and req.to_hostel_id not in admin_hostels:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are not authorized to approve this transfer request.",
                    )
                if not target_room_id or not target_bed_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Target room_id and bed_id are required to complete the transfer.",
                    )
                await self._execute_transfer(
                    req=req, to_room_id=target_room_id, to_bed_id=target_bed_id
                )
                req.status = TransferStatus.COMPLETED
                req.completed_at = datetime.now()
                await self.session.commit()
                return await self._to_response(req)

            else:
                # External transfer: multi-step approval
                if req.status == TransferStatus.PENDING_OLD_ADMIN:
                    if req.from_hostel_id not in admin_hostels:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only the old hostel admin can perform the initial approval.",
                        )
                    req.status = TransferStatus.PENDING_NEW_ADMIN
                    req.old_admin_approved_at = datetime.now()
                    await self.session.commit()
                    return await self._to_response(req)

                elif req.status == TransferStatus.PENDING_NEW_ADMIN:
                    if req.to_hostel_id not in admin_hostels:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only the new hostel admin can complete the final approval.",
                        )
                    if not target_room_id or not target_bed_id:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Target room_id and bed_id are required to complete the transfer.",
                        )
                    req.new_admin_approved_at = datetime.now()
                    await self._execute_transfer(
                        req=req, to_room_id=target_room_id, to_bed_id=target_bed_id
                    )
                    req.status = TransferStatus.COMPLETED
                    req.completed_at = datetime.now()
                    await self.session.commit()
                    return await self._to_response(req)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot approve transfer in status: {req.status}",
                    )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be 'approve' or 'reject'.",
            )

    async def _execute_transfer(
        self, *, req: StudentTransferRequest, to_room_id: str, to_bed_id: str
    ) -> None:
        # Check target bed
        bed_res = await self.session.execute(select(Bed).where(Bed.id == to_bed_id))
        bed = bed_res.scalar_one_or_none()
        if not bed or str(bed.room_id) != to_room_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid target room or bed.",
            )
        if bed.status == BedStatus.OCCUPIED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Target bed is already occupied. Please select an available bed.",
            )

        student_res = await self.session.execute(
            select(Student).where(Student.id == req.student_id)
        )
        student = student_res.scalar_one_or_none()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student record not found.",
            )

        # 1. Close old booking & bed stay
        if student.booking_id:
            old_booking_res = await self.session.execute(
                select(Booking).where(Booking.id == student.booking_id)
            )
            old_booking = old_booking_res.scalar_one_or_none()
            if old_booking:
                old_booking.status = BookingStatus.COMPLETED

        old_bed_res = await self.session.execute(
            select(Bed).where(Bed.id == student.bed_id)
        )
        old_bed = old_bed_res.scalar_one_or_none()
        if old_bed:
            old_bed.status = BedStatus.AVAILABLE

        old_stay_res = await self.session.execute(
            select(BedStay).where(
                BedStay.student_id == student.id,
                BedStay.status == BedStayStatus.ACTIVE,
            )
        )
        old_stay = old_stay_res.scalar_one_or_none()
        if old_stay:
            old_stay.status = BedStayStatus.COMPLETED
            old_stay.end_date = datetime.now()

        # 2. Create new booking in target hostel
        room_res = await self.session.execute(select(Room).where(Room.id == to_room_id))
        room = room_res.scalar_one()

        new_booking_number = f"TR-{uuid.uuid4().hex[:10].upper()}"
        new_booking = Booking(
            booking_number=new_booking_number,
            visitor_id=student.user_id,
            hostel_id=req.to_hostel_id,
            room_id=to_room_id,
            bed_id=to_bed_id,
            booking_mode=BookingMode.MONTHLY,
            status=BookingStatus.CHECKED_IN,
            check_in_date=datetime.now(),
            base_rent_amount=room.monthly_rent,
            security_deposit=room.security_deposit,
            grand_total=room.monthly_rent + room.security_deposit,
            full_name=student.student_number,
        )
        self.session.add(new_booking)
        await self.session.flush()

        # 3. Create new bed stay in target hostel
        new_stay = BedStay(
            booking_id=str(new_booking.id),
            student_id=str(student.id),
            hostel_id=req.to_hostel_id,
            room_id=to_room_id,
            bed_id=to_bed_id,
            start_date=datetime.now(),
            status=BedStayStatus.ACTIVE,
        )
        self.session.add(new_stay)

        # 4. Mark target bed as OCCUPIED
        bed.status = BedStatus.OCCUPIED

        # 5. Update Student profile to point to new hostel, room, bed, and booking
        student.hostel_id = req.to_hostel_id
        student.room_id = to_room_id
        student.bed_id = to_bed_id
        student.booking_id = str(new_booking.id)

        req.to_room_id = to_room_id
        req.to_bed_id = to_bed_id

    async def cancel_transfer(
        self, *, user_id: str, transfer_id: str
    ) -> StudentTransferResponse:
        req = await self.repository.get_transfer_by_id(transfer_id)
        if not req or req.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer request not found.",
            )

        if req.status not in (
            TransferStatus.PENDING,
            TransferStatus.PENDING_OLD_ADMIN,
            TransferStatus.PENDING_NEW_ADMIN,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This transfer request cannot be cancelled.",
            )

        req.status = TransferStatus.CANCELLED
        await self.session.commit()
        return await self._to_response(req)

    async def list_student_transfers(self, user_id: str) -> list[StudentTransferResponse]:
        student_res = await self.session.execute(
            select(Student).where(Student.user_id == user_id)
        )
        student = student_res.scalar_one_or_none()
        if not student:
            return []
        requests = await self.repository.list_transfers_by_student(str(student.id))
        return [await self._to_response(r) for r in requests]

    async def list_hostel_transfers(
        self, admin_id: str, hostel_id: str
    ) -> list[StudentTransferResponse]:
        admin_hostels = await self._get_admin_hostels(admin_id)
        if hostel_id not in admin_hostels:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this hostel.",
            )

        requests = await self.repository.list_transfers_by_hostel(hostel_id)
        return [await self._to_response(r) for r in requests]

    async def _to_response(
        self, req: StudentTransferRequest
    ) -> StudentTransferResponse:
        # Populate nested names for UI convenience
        resp = StudentTransferResponse.model_validate(req)

        from_h = await self.session.get(Hostel, req.from_hostel_id)
        to_h = await self.session.get(Hostel, req.to_hostel_id)
        resp.from_hostel_name = from_h.name if from_h else None
        resp.to_hostel_name = to_h.name if to_h else None

        if req.to_room_id:
            r = await self.session.get(Room, req.to_room_id)
            resp.to_room_number = r.room_number if r else None
        if req.to_bed_id:
            b = await self.session.get(Bed, req.to_bed_id)
            resp.to_bed_number = b.bed_number if b else None

        student = await self.session.get(Student, req.student_id)
        if student and student.user:
            resp.student_name = student.user.full_name

        return resp
