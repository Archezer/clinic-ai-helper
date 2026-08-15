import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.models import Appointment, AppointmentStatus, FaqEntry, Patient
from app.services.admin_operations import AdminOperationsService


def test_creates_verified_faq() -> None:
    entry = FaqEntry(
        id=uuid4(),
        question="What are the opening hours?",
        answer="Approved answer",
        keywords="hours opening",
    )
    faqs = MagicMock()
    faqs.create = AsyncMock(return_value=entry)
    session = MagicMock()
    session.commit = AsyncMock()
    service = AdminOperationsService(MagicMock(), faqs, session)

    result = asyncio.run(
        service.create_faq(
            "What are the opening hours?",
            "Approved answer",
            "hours opening",
        )
    )

    assert result is entry
    session.commit.assert_awaited_once_with()


def test_lists_appointment_requests_with_patient_contact() -> None:
    appointment = Appointment(
        id=uuid4(),
        patient_id=uuid4(),
        conversation_id=uuid4(),
        requested_time_text="Monday at 10",
        status=AppointmentStatus.REQUESTED,
        created_at=datetime.now(UTC),
    )
    patient = Patient(
        id=appointment.patient_id,
        channel="messenger",
        external_user_id="user-123",
        full_name="Jane Patient",
        phone="+1 555 123 4567",
    )
    appointments = MagicMock()
    appointments.list_requested_with_patients = AsyncMock(
        return_value=[(appointment, patient)],
    )
    service = AdminOperationsService(
        appointments,
        MagicMock(),
        MagicMock(),
    )

    records = asyncio.run(service.list_appointment_requests())

    assert len(records) == 1
    assert records[0].patient_name == "Jane Patient"
    assert records[0].patient_phone == "+1 555 123 4567"
    assert records[0].requested_time_text == "Monday at 10"
