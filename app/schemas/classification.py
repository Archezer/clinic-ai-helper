from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Intent(StrEnum):
    GREETING = "greeting"
    BOOK_APPOINTMENT = "book_appointment"
    CLINIC_FAQ = "clinic_faq"
    MEDICAL_QUESTION = "medical_question"
    HUMAN_REQUEST = "human_request"
    UNKNOWN = "unknown"


class MessageClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Intent
