from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MessageRole
from app.repositories import (
    ConversationRepository,
    MessageRepository,
)
from app.schemas.routing import RoutingDecision
from app.services.classifier import MessageClassifier
from app.services.router import MessageRouter


class ChatService:
    def __init__(
            self,
            classifier: MessageClassifier,
            router: MessageRouter,
            conversation_repository: ConversationRepository,
            message_repository: MessageRepository,
            session: AsyncSession,
        ) -> None:
        self._classifier = classifier
        self._router = router
        self._conversation_repository = conversation_repository
        self._message_reposytory = message_repository
        self._session = session

    async def process_message(
            self,
            message: str,
            channel: str,
            external_user_id: str,
    ) -> RoutingDecision:
        conversation = (
            await self._conversation_repository.get_or_create_active(
                channel=channel,
                external_user_id=external_user_id
            )
        )

        await self._message_reposytory.create(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=message
        )

        classification = await self._classifier.classify(message)
        decision = self._router.route(classification)

        await self._session.commit()

        return decision