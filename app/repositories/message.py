from uuid import UUID

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
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        self._session.add(message)
        await self._session.flush()

        return message