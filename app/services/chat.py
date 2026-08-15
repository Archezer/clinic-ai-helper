from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    BookingStage,
    ConversationStatus,
    MessageRole,
)
from app.repositories import (
    ConversationRepository,
    MessageRepository,
)
from app.schemas.routing import ChatAction, RoutingDecision
from app.schemas.classification import Intent
from app.services.booking import BookingService
from app.services.classifier import MessageClassifier
from app.services.exceptions import DuplicateMessageError
from app.services.faq import FaqService
from app.services.ports import MessageSender
from app.services.responses import FAQ_NOT_FOUND_TEXT, ResponseComposer
from app.services.router import MessageRouter


class ChatService:
    def __init__(
        self,
        classifier: MessageClassifier,
        router: MessageRouter,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
        message_sender: MessageSender,
        response_composer: ResponseComposer,
        booking_service: BookingService,
        faq_service: FaqService,
        session: AsyncSession,
    ) -> None:
        self._classifier = classifier
        self._router = router
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._message_sender = message_sender
        self._response_composer = response_composer
        self._booking_service = booking_service
        self._faq_service = faq_service
        self._session = session

    async def process_message(
        self,
        message: str,
        channel: str,
        external_user_id: str,
        external_message_id: str,
    ) -> RoutingDecision:
        existing_message = (
            await self._message_repository.get_by_external_message_id(
                external_message_id,
            )
        )
        if existing_message is not None:
            raise DuplicateMessageError(
                f"Message {external_message_id!r} was already processed"
            )

        conversation = (
            await self._conversation_repository.get_or_create_open(
                channel=channel,
                external_user_id=external_user_id,
            )
        )

        await self._message_repository.create(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=message,
            external_message_id=external_message_id,
        )

        if conversation.status == ConversationStatus.NEEDS_HUMAN:
            await self._session.commit()
            return RoutingDecision(
                intent=Intent.HUMAN_REQUEST,
                action=ChatAction.HAND_OFF_TO_HUMAN,
            )

        classification = await self._classifier.classify(message)
        decision = self._router.route(classification)

        if decision.action == ChatAction.HAND_OFF_TO_HUMAN:
            conversation.status = ConversationStatus.NEEDS_HUMAN
            conversation.booking_stage = BookingStage.IDLE
            response_text = self._response_composer.compose(decision.action)
        elif conversation.booking_stage not in (None, BookingStage.IDLE):
            booking_result = await self._booking_service.continue_flow(
                conversation=conversation,
                channel=channel,
                external_user_id=external_user_id,
                message=message,
            )
            decision = RoutingDecision(
                intent=Intent.BOOK_APPOINTMENT,
                action=ChatAction.START_BOOKING,
            )
            response_text = booking_result.text
        elif decision.action == ChatAction.START_BOOKING:
            booking_result = await self._booking_service.start(
                conversation=conversation,
                channel=channel,
                external_user_id=external_user_id,
            )
            response_text = booking_result.text
        elif decision.action == ChatAction.ANSWER_FAQ:
            faq_answer = await self._faq_service.find_answer(message)
            if faq_answer is None:
                conversation.status = ConversationStatus.NEEDS_HUMAN
                decision = RoutingDecision(
                    intent=Intent.CLINIC_FAQ,
                    action=ChatAction.HAND_OFF_TO_HUMAN,
                )
                response_text = FAQ_NOT_FOUND_TEXT
            else:
                response_text = faq_answer
        else:
            response_text = self._response_composer.compose(decision.action)
        await self._message_sender.send_text(
            recipient_id=external_user_id,
            text=response_text,
        )
        await self._message_repository.create(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=response_text,
        )

        await self._session.commit()

        return decision
