from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Appointment, AppointmentStatus, Patient


class AppointmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_request(
        self,
        patient_id: UUID,
        conversation_id: UUID,
        requested_time_text: str,
    ) -> Appointment:
        appointment = Appointment(
            patient_id=patient_id,
            conversation_id=conversation_id,
            requested_time_text=requested_time_text,
        )
        self._session.add(appointment)
        await self._session.flush()
        return appointment

    async def get_by_id(self, appointment_id: UUID) -> Appointment | None:
        return await self._session.get(Appointment, appointment_id)

    async def list_requested_with_patients(
        self,
    ) -> list[tuple[Appointment, Patient]]:
        statement = (
            select(Appointment, Patient)
            .join(Patient, Patient.id == Appointment.patient_id)
            .where(Appointment.status == AppointmentStatus.REQUESTED)
            .order_by(Appointment.created_at)
        )
        result = await self._session.execute(statement)
        return list(result.tuples().all())
