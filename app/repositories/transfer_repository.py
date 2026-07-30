from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.transfer import StudentTransferRequest, TransferStatus


class TransferRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_transfer_request(self, req: StudentTransferRequest) -> StudentTransferRequest:
        self.session.add(req)
        await self.session.flush()
        await self.session.refresh(req)
        return req

    async def get_transfer_by_id(self, req_id: str) -> StudentTransferRequest | None:
        result = await self.session.execute(
            select(StudentTransferRequest).where(StudentTransferRequest.id == req_id)
        )
        return result.scalar_one_or_none()

    async def get_active_transfer_for_student(self, student_id: str) -> StudentTransferRequest | None:
        result = await self.session.execute(
            select(StudentTransferRequest).where(
                StudentTransferRequest.student_id == student_id,
                StudentTransferRequest.status.in_([
                    TransferStatus.PENDING,
                    TransferStatus.PENDING_OLD_ADMIN,
                    TransferStatus.PENDING_NEW_ADMIN,
                ])
            )
        )
        return result.scalar_one_or_none()

    async def list_transfers_by_student(self, student_id: str) -> list[StudentTransferRequest]:
        result = await self.session.execute(
            select(StudentTransferRequest)
            .where(StudentTransferRequest.student_id == student_id)
            .order_by(StudentTransferRequest.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_transfers_by_hostel(self, hostel_id: str) -> list[StudentTransferRequest]:
        result = await self.session.execute(
            select(StudentTransferRequest)
            .where(
                or_(
                    StudentTransferRequest.from_hostel_id == hostel_id,
                    StudentTransferRequest.to_hostel_id == hostel_id,
                )
            )
            .order_by(StudentTransferRequest.created_at.desc())
        )
        return list(result.scalars().all())
