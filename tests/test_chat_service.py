import asyncio
from unittest.mock import AsyncMock, MagicMock, call
from uuid import uuid4

import pytest

from app.models import Conversation, ConversationStatus, MessageRole
from app.schemas.classification import Intent, MessageClassification
from app.schemas.routing import ChatAction
from app.services.chat import ChatService
from app.services.exceptions import DuplicateMessageError, MessageDeliveryError
from app.services.responses import RESPONSE_TEXTS, ResponseComposer
from app.services.router import MessageRouter


class StubClassifier:
    async def classify(self, message: str) -> MessageClassification:
        return MessageClassification(intent=Intent.MEDICAL_QUESTION)


class GreetingClassifier:
    async def classify(self, message: str) -> MessageClassification:
        return MessageClassification(intent=Intent.GREETING)


def create_service(
    classifier: StubClassifier | GreetingClassifier,
    conversation: Conversation,
) -> tuple[
    ChatService,
    MagicMock,
    MagicMock,
    MagicMock,
    MagicMock,
]:
    conversation_repository = MagicMock()
    conversation_repository.get_or_create_open = AsyncMock(
        return_value=conversation,
    )
    message_repository = MagicMock()
    message_repository.get_by_external_message_id = AsyncMock(
        return_value=None,
    )
    message_repository.create = AsyncMock()
    message_sender = MagicMock()
    message_sender.send_text = AsyncMock()
    booking_service = MagicMock()
    faq_service = MagicMock()
    session = MagicMock()
    session.commit = AsyncMock()

    service = ChatService(
        classifier=classifier,
        router=MessageRouter(),
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        message_sender=message_sender,
        response_composer=ResponseComposer(),
        booking_service=booking_service,
        faq_service=faq_service,
        session=session,
    )
    return (
        service,
        conversation_repository,
        message_repository,
        message_sender,
        session,
    )


def test_processes_and_saves_message() -> None:
    conversation = Conversation(
        id=uuid4(),
        channel="messenger",
        external_user_id="facebook-user-123",
    )
    (
        service,
        conversation_repository,
        message_repository,
        message_sender,
        session,
    ) = (
        create_service(StubClassifier(), conversation)
    )

    decision = asyncio.run(
        service.process_message(
            message="Can you recommend a medication?",
            channel="messenger",
            external_user_id="facebook-user-123",
            external_message_id="mid.medical-123",
        )
    )

    assert decision.intent == Intent.MEDICAL_QUESTION
    assert decision.action == ChatAction.HAND_OFF_TO_HUMAN
    conversation_repository.get_or_create_open.assert_awaited_once_with(
        channel="messenger",
        external_user_id="facebook-user-123",
    )
    response_text = RESPONSE_TEXTS[ChatAction.HAND_OFF_TO_HUMAN]
    assert message_repository.create.await_args_list == [
        call(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="Can you recommend a medication?",
            external_message_id="mid.medical-123",
        ),
        call(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=response_text,
        ),
    ]
    message_sender.send_text.assert_awaited_once_with(
        recipient_id="facebook-user-123",
        text=response_text,
    )
    assert conversation.status == ConversationStatus.NEEDS_HUMAN
    session.commit.assert_awaited_once_with()


def test_keeps_active_status_for_non_handoff_action() -> None:
    conversation = Conversation(
        id=uuid4(),
        channel="messenger",
        external_user_id="facebook-user-123",
        status=ConversationStatus.ACTIVE,
    )
    service, _, _, message_sender, session = create_service(
        GreetingClassifier(),
        conversation,
    )

    decision = asyncio.run(
        service.process_message(
            message="Hello",
            channel="messenger",
            external_user_id="facebook-user-123",
            external_message_id="mid.greeting-123",
        )
    )

    assert decision.action == ChatAction.SEND_GREETING
    assert conversation.status == ConversationStatus.ACTIVE
    message_sender.send_text.assert_awaited_once_with(
        recipient_id="facebook-user-123",
        text=RESPONSE_TEXTS[ChatAction.SEND_GREETING],
    )
    session.commit.assert_awaited_once_with()


def test_rejects_duplicate_message_without_side_effects() -> None:
    classifier = MagicMock()
    classifier.classify = AsyncMock()
    conversation_repository = MagicMock()
    conversation_repository.get_or_create_open = AsyncMock()
    message_repository = MagicMock()
    message_repository.get_by_external_message_id = AsyncMock(
        return_value=MagicMock(),
    )
    message_repository.create = AsyncMock()
    message_sender = MagicMock()
    message_sender.send_text = AsyncMock()
    booking_service = MagicMock()
    faq_service = MagicMock()
    session = MagicMock()
    session.commit = AsyncMock()
    service = ChatService(
        classifier=classifier,
        router=MessageRouter(),
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        message_sender=message_sender,
        response_composer=ResponseComposer(),
        booking_service=booking_service,
        faq_service=faq_service,
        session=session,
    )

    with pytest.raises(DuplicateMessageError):
        asyncio.run(
            service.process_message(
                message="Hello again",
                channel="messenger",
                external_user_id="facebook-user-123",
                external_message_id="mid.duplicate-123",
            )
        )

    conversation_repository.get_or_create_open.assert_not_awaited()
    message_repository.create.assert_not_awaited()
    classifier.classify.assert_not_awaited()
    message_sender.send_text.assert_not_awaited()
    session.commit.assert_not_awaited()


def test_does_not_commit_when_message_delivery_fails() -> None:
    conversation = Conversation(
        id=uuid4(),
        channel="messenger",
        external_user_id="facebook-user-123",
        status=ConversationStatus.ACTIVE,
    )
    service, _, message_repository, message_sender, session = (
        create_service(GreetingClassifier(), conversation)
    )
    message_sender.send_text.side_effect = MessageDeliveryError(
        "Messenger is unavailable"
    )

    with pytest.raises(MessageDeliveryError):
        asyncio.run(
            service.process_message(
                message="Hello",
                channel="messenger",
                external_user_id="facebook-user-123",
                external_message_id="mid.failed-delivery-123",
            )
        )

    assert message_repository.create.await_count == 1
    session.commit.assert_not_awaited()


def test_stores_message_without_bot_reply_during_human_handoff() -> None:
    conversation = Conversation(
        id=uuid4(),
        channel="messenger",
        external_user_id="facebook-user-123",
        status=ConversationStatus.NEEDS_HUMAN,
    )
    service, _, message_repository, message_sender, session = (
        create_service(GreetingClassifier(), conversation)
    )

    decision = asyncio.run(
        service.process_message(
            message="I have more information",
            channel="messenger",
            external_user_id="facebook-user-123",
            external_message_id="mid.handoff-followup-123",
        )
    )

    assert decision.action == ChatAction.HAND_OFF_TO_HUMAN
    assert message_repository.create.await_count == 1
    message_sender.send_text.assert_not_awaited()
    session.commit.assert_awaited_once_with()
