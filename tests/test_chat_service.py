import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.models import Conversation, MessageRole
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


def test_processes_and_saves_message() -> None:
    conversation = Conversation(
        id=uuid4(),
        channel="messenger",
        external_user_id="facebook-user-123",
    )

    conversation_repository = MagicMock()
    conversation_repository.get_or_create_active = AsyncMock(
        return_value=conversation,
    )

    message_repository = MagicMock()
    message_repository.create = AsyncMock()

    session = MagicMock()
    session.commit = AsyncMock()

    service = ChatService(
        classifier=StubClassifier(),
        router=MessageRouter(),
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        session=session,
    )

    decision = asyncio.run(
        service.process_message(
            message="Can you recommend a medication?",
            channel="messenger",
            external_user_id="facebook-user-123",
        )
    )

    assert decision.intent == Intent.MEDICAL_QUESTION
    assert decision.action == ChatAction.HAND_OFF_TO_HUMAN

    conversation_repository.get_or_create_active.assert_awaited_once_with(
        channel="messenger",
        external_user_id="facebook-user-123",
    )

    message_repository.create.assert_awaited_once_with(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content="Can you recommend a medication?",
    )

    session.commit.assert_awaited_once_with()