import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models import Conversation, ConversationStatus, MessageRole
from app.services.handoff import ConversationStateError, HandoffService


def create_service(
    conversation: Conversation,
) -> tuple[HandoffService, MagicMock, MagicMock, MagicMock, MagicMock]:
    conversations = MagicMock()
    conversations.get_by_id = AsyncMock(return_value=conversation)
    messages = MagicMock()
    messages.create = AsyncMock()
    messages.list_by_conversation = AsyncMock(return_value=[])
    sender = MagicMock()
    sender.send_text = AsyncMock()
    session = MagicMock()
    session.commit = AsyncMock()
    service = HandoffService(conversations, messages, sender, session)
    return service, conversations, messages, sender, session


def test_human_replies_and_saves_history() -> None:
    conversation = Conversation(
        id=uuid4(),
        channel="messenger",
        external_user_id="facebook-user-123",
        status=ConversationStatus.NEEDS_HUMAN,
    )
    service, _, messages, sender, session = create_service(conversation)

    asyncio.run(service.reply(conversation.id, "How can I help you?"))

    sender.send_text.assert_awaited_once_with(
        recipient_id="facebook-user-123",
        text="How can I help you?",
    )
    messages.create.assert_awaited_once_with(
        conversation_id=conversation.id,
        role=MessageRole.HUMAN,
        content="How can I help you?",
    )
    session.commit.assert_awaited_once_with()


def test_rejects_human_reply_for_active_conversation() -> None:
    conversation = Conversation(
        id=uuid4(),
        channel="messenger",
        external_user_id="facebook-user-123",
        status=ConversationStatus.ACTIVE,
    )
    service, _, messages, sender, session = create_service(conversation)

    with pytest.raises(ConversationStateError):
        asyncio.run(service.reply(conversation.id, "Hello"))

    sender.send_text.assert_not_awaited()
    messages.create.assert_not_awaited()
    session.commit.assert_not_awaited()


def test_closes_conversation() -> None:
    conversation = Conversation(
        id=uuid4(),
        channel="messenger",
        external_user_id="facebook-user-123",
        status=ConversationStatus.NEEDS_HUMAN,
    )
    service, _, _, _, session = create_service(conversation)

    asyncio.run(service.close(conversation.id))

    assert conversation.status == ConversationStatus.CLOSED
    session.commit.assert_awaited_once_with()
