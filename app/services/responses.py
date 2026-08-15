from app.schemas.routing import ChatAction


RESPONSE_TEXTS: dict[ChatAction, str] = {
    ChatAction.SEND_GREETING: (
        "Hello! I am the clinic's virtual receptionist. "
        "How can I help you today?"
    ),
    ChatAction.START_BOOKING: (
        "I can help start your appointment request. "
        "Please tell me your preferred date and time."
    ),
    ChatAction.ANSWER_FAQ: (
        "I can help with clinic hours, location, services, fees, "
        "and policies. A staff member can confirm any details "
        "that are not available here yet."
    ),
    ChatAction.HAND_OFF_TO_HUMAN: (
        "I cannot assess symptoms or provide medical advice. "
        "I have forwarded your message for review by a staff member."
    ),
    ChatAction.SEND_FALLBACK: (
        "I am sorry, I did not understand that request. "
        "You can ask about the clinic or request an appointment."
    ),
}

FAQ_NOT_FOUND_TEXT = (
    "I do not have a verified answer to that clinic question yet. "
    "I have forwarded it to a staff member."
)


class ResponseComposer:
    def compose(self, action: ChatAction) -> str:
        return RESPONSE_TEXTS[action]
