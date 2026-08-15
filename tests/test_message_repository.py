import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.models import Message, MessageRole
from app.repositories import MessageRepository


def test_creates_message() -> None:
    conversation_id = uuid4()
    session = MagicMock()
    session.flush = AsyncMock()
    repository = MessageRepository(session)

    result = asyncio.run(
        repository.create(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content="I want to book an appointment",
            external_message_id="mid.123",
        )
    )

    assert isinstance(result, Message)
    assert result.conversation_id == conversation_id
    assert result.role == MessageRole.USER
    assert result.content == "I want to book an appointment"
    assert result.external_message_id == "mid.123"
    session.add.assert_called_once_with(result)
    session.flush.assert_awaited_once_with()


def test_gets_message_by_external_message_id() -> None:
    message = Message(
        conversation_id=uuid4(),
        role=MessageRole.USER,
        content="Hello",
        external_message_id="mid.123",
    )
    query_result = MagicMock()
    query_result.scalar_one_or_none.return_value = message
    session = MagicMock()
    session.execute = AsyncMock(return_value=query_result)
    repository = MessageRepository(session)

    result = asyncio.run(
        repository.get_by_external_message_id("mid.123")
    )

    assert result is message
    session.execute.assert_awaited_once()
    query_result.scalar_one_or_none.assert_called_once_with()
