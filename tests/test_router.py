import pytest

from app.schemas.classification import (
    Intent,
    MessageClassification,
)
from app.schemas.routing import ChatAction
from app.services.router import MessageRouter


@pytest.mark.parametrize(
    ("intent", "expected_action"),
    [
        (
            Intent.GREETING,
            ChatAction.SEND_GREETING,
        ),
        (
            Intent.BOOK_APPOINTMENT,
            ChatAction.START_BOOKING,
        ),
        (
            Intent.CLINIC_FAQ,
            ChatAction.ANSWER_FAQ,
        ),
        (
            Intent.MEDICAL_QUESTION,
            ChatAction.HAND_OFF_TO_HUMAN,
        ),
        (
            Intent.HUMAN_REQUEST,
            ChatAction.HAND_OFF_TO_HUMAN,
        ),
        (
            Intent.UNKNOWN,
            ChatAction.SEND_FALLBACK,
        ),
    ],
)
def test_routes_intent_to_expected_action(
    intent: Intent,
    expected_action: ChatAction,
) -> None:
    router = MessageRouter()

    classification = MessageClassification(
        intent=intent,
    )

    decision = router.route(classification)

    assert decision.intent == intent
    assert decision.action == expected_action