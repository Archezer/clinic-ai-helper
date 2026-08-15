from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, ConversationStatus, Message, MessageRole
from app.repositories import ConversationRepository, MessageRepository
from app.services.ports import MessageSender


class ConversationNotFoundError(LookupError):
    """Raised when an operator references an unknown conversation."""


class ConversationStateError(RuntimeError):
    """Raised when an operator action is invalid for the current status."""


class HandoffService:
    def __init__(
        self,
        conversations: ConversationRepository,
        messages: MessageRepository,
        message_sender: MessageSender,
        session: AsyncSession,
    ) -> None:
        self._conversations = conversations
        self._messages = messages
        self._message_sender = message_sender
        self._session = session

    async def list_pending(self) -> list[Conversation]:
        return await self._conversations.list_needing_human()

    async def get_history(self, conversation_id: UUID) -> list[Message]:
        await self._get_conversation(conversation_id)
        return await self._messages.list_by_conversation(conversation_id)

    async def reply(
        self,
        conversation_id: UUID,
        text: str,
    ) -> None:
        conversation = await self._get_conversation(conversation_id)
        if conversation.status != ConversationStatus.NEEDS_HUMAN:
            raise ConversationStateError(
                "Conversation is not waiting for a human"
            )

        await self._message_sender.send_text(
            recipient_id=conversation.external_user_id,
            text=text,
        )
        await self._messages.create(
            conversation_id=conversation.id,
            role=MessageRole.HUMAN,
            content=text,
        )
        await self._session.commit()

    async def close(self, conversation_id: UUID) -> None:
        conversation = await self._get_conversation(conversation_id)
        conversation.status = ConversationStatus.CLOSED
        await self._session.commit()

    async def _get_conversation(
        self,
        conversation_id: UUID,
    ) -> Conversation:
        conversation = await self._conversations.get_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(
                f"Conversation {conversation_id} was not found"
            )
        return conversation
