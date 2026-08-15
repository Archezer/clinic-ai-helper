from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Database
from app.services.chat import ChatService
from app.services.classifier import MessageClassifier


def get_message_classifier(request: Request) -> MessageClassifier:
    return request.app.state.message_classifier

def get_chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service

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