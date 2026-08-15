from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, ConversationStatus


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, conversation: Conversation) -> None:
        self._session.add(conversation)

    async def get_by_id(
            self,
            conversation_id: UUID,
    ) -> Conversation | None:
        return await self._session.get(
            Conversation,
            conversation_id,
        )

    async def get_active_by_external_user(
        self,
        channel: str,
        external_user_id: str,
    ) -> Conversation | None:
        statement = (
            select(Conversation)
            .where(
                Conversation.channel == channel,
                Conversation.external_user_id == external_user_id,
                Conversation.status == ConversationStatus.ACTIVE,
            )
            .order_by(Conversation.updated_at.desc())
            .limit(1)
        )

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def get_or_create_active(
            self,
            channel: str,
            external_user_id: str
    ) -> Conversation:
        conversation = await self.get_active_by_external_user(
            channel=channel,
            external_user_id=external_user_id
        )

        if conversation is not None:
            return conversation

        conversation = Conversation(
            channel=channel,
            external_user_id=external_user_id
        )

        self.add(conversation)
        await self._session.flush()

        return conversation