from app.schemas.classification import Intent, MessageClassification
from app.schemas.routing import ChatAction, RoutingDecision


INTENT_ACTIONS: dict[Intent, ChatAction] = {
    Intent.GREETING: ChatAction.SEND_GREETING,
    Intent.BOOK_APPOINTMENT: ChatAction.START_BOOKING,
    Intent.CLINIC_FAQ: ChatAction.ANSWER_FAQ,
    Intent.MEDICAL_QUESTION: ChatAction.HAND_OFF_TO_HUMAN,
    Intent.HUMAN_REQUEST: ChatAction.HAND_OFF_TO_HUMAN,
    Intent.UNKNOWN: ChatAction.SEND_FALLBACK,
}

class MessageRouter:
    def route(
            self,
            classification: MessageClassification
    ) -> RoutingDecision:
        action = INTENT_ACTIONS[classification.intent]

        return RoutingDecision(
            intent=classification.intent,
            action=action
        )

    