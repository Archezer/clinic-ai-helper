from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppointmentStatus, FaqEntry
from app.repositories import AppointmentRepository, FaqRepository


class AppointmentNotFoundError(LookupError):
    """Raised when an appointment request does not exist."""


@dataclass(frozen=True, slots=True)
class AppointmentQueueRecord:
    id: UUID
    patient_id: UUID
    conversation_id: UUID
    patient_name: str | None
    patient_phone: str | None
    requested_time_text: str
    status: AppointmentStatus
    created_at: datetime


class AdminOperationsService:
    def __init__(
        self,
        appointments: AppointmentRepository,
        faqs: FaqRepository,
        session: AsyncSession,
    ) -> None:
        self._appointments = appointments
        self._faqs = faqs
        self._session = session

    async def list_faqs(self) -> list[FaqEntry]:
        return await self._faqs.list_active()

    async def create_faq(
        self,
        question: str,
        answer: str,
        keywords: str,
    ) -> FaqEntry:
        entry = await self._faqs.create(question, answer, keywords)
        await self._session.commit()
        return entry

    async def list_appointment_requests(
        self,
    ) -> list[AppointmentQueueRecord]:
        rows = await self._appointments.list_requested_with_patients()
        return [
            AppointmentQueueRecord(
                id=appointment.id,
                patient_id=appointment.patient_id,
                conversation_id=appointment.conversation_id,
                patient_name=patient.full_name,
                patient_phone=patient.phone,
                requested_time_text=appointment.requested_time_text,
                status=appointment.status,
                created_at=appointment.created_at,
            )
            for appointment, patient in rows
        ]

    async def set_appointment_status(
        self,
        appointment_id: UUID,
        status: AppointmentStatus,
    ) -> None:
        appointment = await self._appointments.get_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError(
                f"Appointment {appointment_id} was not found"
            )
        appointment.status = status
        await self._session.commit()
