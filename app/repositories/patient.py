from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Patient


class PatientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_external_user(
        self,
        channel: str,
        external_user_id: str,
    ) -> Patient | None:
        statement = select(Patient).where(
            Patient.channel == channel,
            Patient.external_user_id == external_user_id,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        channel: str,
        external_user_id: str,
    ) -> Patient:
        patient = await self.get_by_external_user(
            channel=channel,
            external_user_id=external_user_id,
        )
        if patient is not None:
            return patient

        patient = Patient(
            channel=channel,
            external_user_id=external_user_id,
        )
        self._session.add(patient)
        await self._session.flush()
        return patient
