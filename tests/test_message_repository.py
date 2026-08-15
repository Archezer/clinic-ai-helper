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
        )
    )

    assert isinstance(result, Message)
    assert result.conversation_id == conversation_id
    assert result.role == MessageRole.USER
    assert result.content == "I want to book an appointment"

    session.add.assert_called_once_with(result)
    session.flush.assert_awaited_once_with()