import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.models import Conversation
from app.repositories import ConversationRepository


def test_gets_open_conversation_by_external_user() -> None:
    conversation = Conversation(
        channel="messenger",
        external_user_id="facebook-user-123",
    )
    result = MagicMock()
    result.scalar_one_or_none.return_value = conversation
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)
    repository = ConversationRepository(session)

    found_conversation = asyncio.run(
        repository.get_open_by_external_user(
            channel="messenger",
            external_user_id="facebook-user-123",
        )
    )

    assert found_conversation is conversation
    session.execute.assert_awaited_once()
    result.scalar_one_or_none.assert_called_once_with()


def test_returns_none_when_open_conversation_does_not_exist() -> None:
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)
    repository = ConversationRepository(session)

    found_conversation = asyncio.run(
        repository.get_open_by_external_user(
            channel="messenger",
            external_user_id="unknown-user",
        )
    )

    assert found_conversation is None


def test_returns_existing_open_conversation() -> None:
    conversation = Conversation(
        channel="messenger",
        external_user_id="facebook-user-123",
    )

    session = MagicMock()
    session.flush = AsyncMock()

    repository = ConversationRepository(session)
    repository.get_open_by_external_user = AsyncMock(
        return_value=conversation,
    )

    result = asyncio.run(
        repository.get_or_create_open(
            channel="messenger",
            external_user_id="facebook-user-123",
        )
    )

    assert result is conversation

    repository.get_open_by_external_user.assert_awaited_once_with(
        channel="messenger",
        external_user_id="facebook-user-123",
    )
    session.add.assert_not_called()
    session.flush.assert_not_awaited()


def test_creates_conversation_when_open_one_does_not_exist() -> None:
    session = MagicMock()
    session.flush = AsyncMock()

    repository = ConversationRepository(session)
    repository.get_open_by_external_user = AsyncMock(
        return_value=None,
    )

    result = asyncio.run(
        repository.get_or_create_open(
            channel="messenger",
            external_user_id="new-facebook-user",
        )
    )

    assert isinstance(result, Conversation)
    assert result.channel == "messenger"
    assert result.external_user_id == "new-facebook-user"

    session.add.assert_called_once_with(result)
    session.flush.assert_awaited_once_with()
