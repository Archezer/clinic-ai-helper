import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.models import BookingStage, Conversation, Patient
from app.services.booking import BookingService


def test_collects_patient_data_and_creates_appointment_request() -> None:
    patient = Patient(
        id=uuid4(),
        channel="messenger",
        external_user_id="facebook-user-123",
    )
    conversation = Conversation(
        id=uuid4(),
        channel="messenger",
        external_user_id="facebook-user-123",
        booking_stage=BookingStage.IDLE,
    )
    patient_repository = MagicMock()
    patient_repository.get_or_create = AsyncMock(return_value=patient)
    appointment_repository = MagicMock()
    appointment_repository.create_request = AsyncMock()
    service = BookingService(
        patient_repository=patient_repository,
        appointment_repository=appointment_repository,
    )

    start_result = asyncio.run(
        service.start(conversation, "messenger", "facebook-user-123")
    )
    assert conversation.booking_stage == BookingStage.AWAITING_NAME
    assert "full name" in start_result.text

    name_result = asyncio.run(
        service.continue_flow(
            conversation,
            "messenger",
            "facebook-user-123",
            "  Jane   Patient  ",
        )
    )
    assert patient.full_name == "Jane Patient"
    assert conversation.booking_stage == BookingStage.AWAITING_PHONE
    assert "phone" in name_result.text

    invalid_phone_result = asyncio.run(
        service.continue_flow(
            conversation,
            "messenger",
            "facebook-user-123",
            "123",
        )
    )
    assert patient.phone is None
    assert conversation.booking_stage == BookingStage.AWAITING_PHONE
    assert "does not look valid" in invalid_phone_result.text

    asyncio.run(
        service.continue_flow(
            conversation,
            "messenger",
            "facebook-user-123",
            "+1 555 123 4567",
        )
    )
    assert patient.phone == "+1 555 123 4567"
    assert conversation.booking_stage == BookingStage.AWAITING_DATETIME

    completed_result = asyncio.run(
        service.continue_flow(
            conversation,
            "messenger",
            "facebook-user-123",
            "Next Monday at 10:00",
        )
    )
    appointment_repository.create_request.assert_awaited_once_with(
        patient_id=patient.id,
        conversation_id=conversation.id,
        requested_time_text="Next Monday at 10:00",
    )
    assert conversation.booking_stage == BookingStage.IDLE
    assert completed_result.completed is True
    assert "request has been recorded" in completed_result.text


def test_skips_known_patient_fields() -> None:
    patient = Patient(
        id=uuid4(),
        channel="messenger",
        external_user_id="facebook-user-123",
        full_name="Jane Patient",
        phone="+1 555 123 4567",
    )
    conversation = Conversation(
        id=uuid4(),
        channel="messenger",
        external_user_id="facebook-user-123",
        booking_stage=BookingStage.IDLE,
    )
    patient_repository = MagicMock()
    patient_repository.get_or_create = AsyncMock(return_value=patient)
    service = BookingService(
        patient_repository=patient_repository,
        appointment_repository=MagicMock(),
    )

    result = asyncio.run(
        service.start(conversation, "messenger", "facebook-user-123")
    )

    assert conversation.booking_stage == BookingStage.AWAITING_DATETIME
    assert "preferred appointment date" in result.text
