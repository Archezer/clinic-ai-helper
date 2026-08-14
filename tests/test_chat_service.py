import asyncio

from app.schemas.classification import (
    Intent,
    MessageClassification,
)
from app.schemas.routing import ChatAction
from app.services.chat import ChatService
from app.services.router import MessageRouter


class StubClassifier:
    async def classify(
        self,
        message: str,
    ) -> MessageClassification:
        return MessageClassification(
            intent=Intent.MEDICAL_QUESTION,
        )


def test_processes_message() -> None:
    service = ChatService(
        classifier=StubClassifier(),
        router=MessageRouter(),
    )

    decision = asyncio.run(
        service.process_message(
            "Can you recommend a medication?"
        )
    )

    assert decision.intent == Intent.MEDICAL_QUESTION
    assert decision.action == ChatAction.HAND_OFF_TO_HUMAN