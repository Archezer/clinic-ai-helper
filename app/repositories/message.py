from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message, MessageRole


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        external_message_id: str | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            external_message_id=external_message_id,
        )

        self._session.add(message)
        await self._session.flush()

        return message

    async def get_by_external_message_id(
        self,
        external_message_id: str,
    ) -> Message | None:
        statement = select(Message).where(
            Message.external_message_id == external_message_id,
        )
        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def list_by_conversation(
        self,
        conversation_id: UUID,
    ) -> list[Message]:
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at, Message.id)
        )
        result = await self._session.scalars(statement)
        return list(result.all())
