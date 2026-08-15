from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Database
from app.integrations.messenger_client import MessengerClient
from app.repositories import (
    AppointmentRepository,
    ConversationRepository,
    FaqRepository,
    MessageRepository,
    PatientRepository,
)
from app.services.booking import BookingService
from app.services.admin_operations import AdminOperationsService
from app.services.chat import ChatService
from app.services.classifier import MessageClassifier
from app.services.faq import FaqService
from app.services.handoff import HandoffService
from app.services.responses import ResponseComposer
from app.services.router import MessageRouter


def get_message_classifier(request: Request) -> MessageClassifier:
    return request.app.state.message_classifier


async def get_database_session(
    request: Request,
) -> AsyncIterator[AsyncSession]:
    database: Database = request.app.state.database

    async with database.create_session() as session:
        yield session


DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session),
]


def create_messenger_client(request: Request) -> MessengerClient:
    settings = request.app.state.settings
    access_token = settings.meta_page_access_token
    return MessengerClient(
        http_client=request.app.state.http_client,
        page_access_token=(
            access_token.get_secret_value()
            if access_token is not None
            else ""
        ),
        graph_base_url=settings.meta_graph_base_url,
        graph_api_version=settings.meta_graph_api_version,
    )


def get_chat_service(
    request: Request,
    session: DatabaseSession,
) -> ChatService:
    return ChatService(
        classifier=get_message_classifier(request),
        router=MessageRouter(),
        conversation_repository=ConversationRepository(session),
        message_repository=MessageRepository(session),
        message_sender=create_messenger_client(request),
        response_composer=ResponseComposer(),
        booking_service=BookingService(
            patient_repository=PatientRepository(session),
            appointment_repository=AppointmentRepository(session),
        ),
        faq_service=FaqService(
            FaqRepository(session),
            knowledge_answerer=request.app.state.rag_service,
        ),
        session=session,
    )


def get_handoff_service(
    request: Request,
    session: DatabaseSession,
) -> HandoffService:
    return HandoffService(
        conversations=ConversationRepository(session),
        messages=MessageRepository(session),
        message_sender=create_messenger_client(request),
        session=session,
    )


def get_admin_operations_service(
    session: DatabaseSession,
) -> AdminOperationsService:
    return AdminOperationsService(
        appointments=AppointmentRepository(session),
        faqs=FaqRepository(session),
        session=session,
    )
