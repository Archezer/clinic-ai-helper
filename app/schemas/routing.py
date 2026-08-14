from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.schemas.classification import Intent


class ChatAction(StrEnum):
    SEND_GREETING = 'send_greeting'
    START_BOOKING = "start_booking"
    ANSWER_FAQ = "answer_faq"
    HAND_OFF_TO_HUMAN = "hand_off_to_human"
    SEND_FALLBACK = "send_fallback"

class RoutingDecision(BaseModel):
    model_config = ConfigDict(extra='forbid')

    intent: Intent
    action: ChatAction