import re
from dataclasses import dataclass

from app.models import BookingStage, Conversation
from app.repositories import AppointmentRepository, PatientRepository


PHONE_PATTERN = re.compile(r"^\+?[0-9 ()-]{7,30}$")


@dataclass(frozen=True, slots=True)
class BookingResult:
    text: str
    completed: bool = False


class BookingService:
    def __init__(
        self,
        patient_repository: PatientRepository,
        appointment_repository: AppointmentRepository,
    ) -> None:
        self._patients = patient_repository
        self._appointments = appointment_repository

    async def start(
        self,
        conversation: Conversation,
        channel: str,
        external_user_id: str,
    ) -> BookingResult:
        patient = await self._patients.get_or_create(
            channel=channel,
            external_user_id=external_user_id,
        )
        if not patient.full_name:
            conversation.booking_stage = BookingStage.AWAITING_NAME
            return BookingResult("Please provide your full name.")
        if not patient.phone:
            conversation.booking_stage = BookingStage.AWAITING_PHONE
            return BookingResult(
                "Please provide a phone number where the clinic can reach you."
            )

        conversation.booking_stage = BookingStage.AWAITING_DATETIME
        return BookingResult(
            "Please provide your preferred appointment date and time."
        )

    async def continue_flow(
        self,
        conversation: Conversation,
        channel: str,
        external_user_id: str,
        message: str,
    ) -> BookingResult:
        patient = await self._patients.get_or_create(
            channel=channel,
            external_user_id=external_user_id,
        )
        value = " ".join(message.split())

        if conversation.booking_stage == BookingStage.AWAITING_NAME:
            if len(value) < 2:
                return BookingResult("Please provide your full name.")
            patient.full_name = value[:255]
            conversation.booking_stage = BookingStage.AWAITING_PHONE
            return BookingResult(
                "Thank you. Please provide a phone number where the clinic "
                "can reach you."
            )

        if conversation.booking_stage == BookingStage.AWAITING_PHONE:
            digit_count = sum(character.isdigit() for character in value)
            if not PHONE_PATTERN.fullmatch(value) or not 7 <= digit_count <= 15:
                return BookingResult(
                    "That phone number does not look valid. Please enter "
                    "7 to 15 digits, optionally starting with +."
                )
            patient.phone = value
            conversation.booking_stage = BookingStage.AWAITING_DATETIME
            return BookingResult(
                "Please provide your preferred appointment date and time."
            )

        if conversation.booking_stage == BookingStage.AWAITING_DATETIME:
            if len(value) < 3:
                return BookingResult(
                    "Please provide a preferred date and time in plain text."
                )
            await self._appointments.create_request(
                patient_id=patient.id,
                conversation_id=conversation.id,
                requested_time_text=value[:255],
            )
            conversation.booking_stage = BookingStage.IDLE
            return BookingResult(
                "Your appointment request has been recorded. A staff member "
                "will contact you to confirm the date and time.",
                completed=True,
            )

        return await self.start(
            conversation=conversation,
            channel=channel,
            external_user_id=external_user_id,
        )
